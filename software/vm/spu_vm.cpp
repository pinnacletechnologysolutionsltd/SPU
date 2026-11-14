// spu_vm.cpp — SPU-13 Sovereign Virtual Machine (C++17)
// Partial canonical ISA implementation; see docs/isa/ISA_CONFORMANCE_2026-10-10.md.
//
// Q(√3) arithmetic: all values are (a + b·√3), a,b ∈ int32_t.
// No floating point. checked signed128 intermediates; ROTC rounds nearest.
//
// Supported ISA: LD ADD SUB MUL ROT LOG JMP SNAP HALT CALL RET QREAD
//                QADD QSUB QROT ROTC QNORM QLOAD QLDI QLOG DELTA SPREAD HEX
//                EQUIL IDNT JINV ANNE NOP
//
// Build: c++ -std=c++17 -O2 -Wall -o spu_vm spu_vm.cpp

// === Platform detection ===
#ifdef __AVX2__
// AVX2: 4×int32 Quadray batch — VPMADD / VPMULLD
// TODO: implement when benchmarking on Ryzen / Haswell
// Sandy Bridge (i5-2500) has AVX1 but NOT AVX2 integer ops — scalar path used.
#endif
#ifdef __ARM_NEON__
// NEON: 4×int32 — vmulq_s32 / vmlaq_s32
// TODO: implement for Apple M2/M3 target
#endif

#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <cassert>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <cctype>
#include <climits>
#include <numeric>
#include <tuple>
#include "gen1_cli.hpp"   // explicit gen1-surd profile (SPU-GEN1-SIM-IMPL-0)
#include "psurd_cli.hpp"  // EXPERIMENTAL programmable-surd profile (SPU-V03-SIM-0)
#include <stdexcept>
#include "checked_math.h"
#include "../common/include/spu_gram_spread.h"

// SPREAD mathematics (research/sim_cap1_spread/GRAM_V1_CONTRACT.md); fixed at construction.
enum class MetricSemantics { LegacyDot, GramV1 };

// ============================================================================
// RationalSurd — element of Q(√3): value = a + b·√3
// NOTE: uses int32_t, wider than the hardware's int16_t on-wire format.
// Parity is restricted to values and intermediates that fit these widths.
// For the hardware packed format (int16_t a,b) see SynergeticsMath.hpp.
// ============================================================================

struct RationalSurd {
    int32_t a, b;      // a + b·√3
    int32_t pell_step; // -1 = not Pell-tracked; ≥0 = total ROT count from (1,0)

    RationalSurd(int32_t a_ = 0, int32_t b_ = 0, int32_t ps = -1)
        : a(a_), b(b_), pell_step(ps) {}

    RationalSurd operator+(const RationalSurd& o) const {
        return RationalSurd(checked_i32(Wide(a) + o.a), checked_i32(Wide(b) + o.b));
    }
    RationalSurd operator-(const RationalSurd& o) const {
        return RationalSurd(checked_i32(Wide(a) - o.a), checked_i32(Wide(b) - o.b));
    }
    // (a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3
    RationalSurd operator*(const RationalSurd& o) const {
        Wide na = Wide(a) * o.a + 3 * Wide(b) * o.b;
        Wide nb = Wide(a) * o.b + Wide(b) * o.a;
        return RationalSurd(checked_i32(na), checked_i32(nb));
    }
    RationalSurd operator-() const { return RationalSurd(checked_i32(-Wide(a)), checked_i32(-Wide(b))); }

    bool operator==(const RationalSurd& o) const { return a == o.a && b == o.b; }

    // Q = a² − 3b²  (Davis Gate check: >0 = laminar/stable)
    Wide quadrance() const {
        return Wide(a) * a - 3 * Wide(b) * b;
    }
    bool is_laminar() const { return quadrance() > 0; }
    bool is_zero()    const { return a == 0 && b == 0; }

    // Davis Ratio: a/b as string (exact, no float)
    std::string davis_c() const {
        if (b == 0) return (a != 0) ? "inf" : "0/0";
        int64_t g = std::gcd(std::abs(int64_t(a)), std::abs(int64_t(b)));
        if (g == 0) g = 1;
        return std::to_string(a/g) + "/" + std::to_string(b/g);
    }

    std::string repr() const {
        if (b == 0) return std::to_string(a);
        if (b < 0) return "(" + std::to_string(a) + " - " + std::to_string(-int64_t(b)) + "·√3)";
        return "(" + std::to_string(a) + " + " + std::to_string(b) + "·√3)";
    }
};

// ============================================================================
// Pell Orbit table — all 8 fundamental-domain entries fit in int16
// Used by rotate_phi() for exact orbit tracking without overflow.
// Pell sequence: rⁿ where r = (2+√3), norm a²-3b²=1 for all entries.
// ============================================================================

static const int32_t PELL_ORBIT[8][2] = {
    {1, 0}, {2, 1}, {7, 4}, {26, 15},
    {97, 56}, {362, 209}, {1351, 780}, {5042, 2911}
};

// Phi-Rotor: multiply by unit element (2 + 1·√3).
// If pell_step is tracked, advances within the Pell Octave representation
// (stored mantissa cycles through orbit[0..7], octave counter increments).
RationalSurd rotate_phi(const RationalSurd& s) {
    if (s.pell_step >= 0) {
        int32_t new_step = checked_i32(Wide(s.pell_step) + 1);
        int32_t idx = new_step % 8;
        return RationalSurd(PELL_ORBIT[idx][0], PELL_ORBIT[idx][1], new_step);
    }
    // Fallback: full field multiply for non-Pell-tracked surds
    RationalSurd r = s * RationalSurd(2, 1);
    return RationalSurd(r.a, r.b, -1);
}

// ============================================================================
// Exact Q(√3) ordering — no floats, pure integer case analysis
// Returns true iff s1 < s2
// ============================================================================

bool rs_lt(const RationalSurd& s1, const RationalSurd& s2) {
    Wide da = Wide(s1.a) - s2.a;
    Wide db = Wide(s1.b) - s2.b;
    if (da == 0 && db == 0) return false;
    if (da <= 0 && db <= 0) return true;    // both terms negative
    if (da >= 0 && db >= 0) return false;   // both terms positive
    if (da < 0 && db > 0) return 3*db*db < da*da;  // |da| > |db|√3 ?
    return da*da < 3*db*db;                 // da>0, db<0
}

RationalSurd rs_min(const RationalSurd& a, const RationalSurd& b,
                    const RationalSurd& c, const RationalSurd& d) {
    RationalSurd m = a;
    if (rs_lt(b, m)) m = b;
    if (rs_lt(c, m)) m = c;
    if (rs_lt(d, m)) m = d;
    return m;
}

static int32_t sign_extend8(uint32_t x) {
    x &= 0xFFu;
    return (x & 0x80u) ? (int32_t)(x | 0xFFFFFF00u) : (int32_t)x;
}

// ============================================================================
// QuadrayVector — 4-axis IVM tetrahedral coordinates in Q(√3)⁴
// Canonical form: min component = 0 (subtract min from all)
// ============================================================================

struct QuadrayVector {
    RationalSurd a, b, c, d;

    QuadrayVector() : a(0,0), b(0,0), c(0,0), d(0,0) {}
    QuadrayVector(RationalSurd a_, RationalSurd b_,
                  RationalSurd c_, RationalSurd d_)
        : a(a_), b(b_), c(c_), d(d_) {}

    QuadrayVector operator+(const QuadrayVector& o) const {
        return QuadrayVector(a+o.a, b+o.b, c+o.c, d+o.d);
    }

    QuadrayVector operator-(const QuadrayVector& o) const {
        return QuadrayVector(a-o.a, b-o.b, c-o.c, d-o.d);
    }

    // Normalize: subtract min component from all axes (canonical IVM form)
    QuadrayVector normalize() const {
        RationalSurd m = rs_min(a, b, c, d);
        return QuadrayVector(a-m, b-m, c-m, d-m);
    }

    // Apply Pell rotor to each component, then normalize
    QuadrayVector rotate() const {
        QuadrayVector r(rotate_phi(a), rotate_phi(b),
                        rotate_phi(c), rotate_phi(d));
        return r.normalize();
    }

    // IVM quadrance: Σᵢ<ⱼ (cᵢ−cⱼ)² for all 6 pairs
    RationalSurd quadrance() const {
        const RationalSurd comps[4] = {a, b, c, d};
        RationalSurd q(0, 0);
        for (int i = 0; i < 4; i++)
            for (int j = i+1; j < 4; j++) {
                RationalSurd diff = comps[i] - comps[j];
                q = q + diff * diff;
            }
        return q;
    }

    // Euclidean dot product: Σ aᵢ·bᵢ
    RationalSurd dot(const QuadrayVector& o) const {
        return a*o.a + b*o.b + c*o.c + d*o.d;
    }

    // Wildberger spread — returns (numerator, denominator) exact rational pair
    std::pair<RationalSurd,RationalSurd> spread(const QuadrayVector& o) const {
        RationalSurd pp = quadrance();
        RationalSurd qq = o.quadrance();
        RationalSurd pq = dot(o);
        RationalSurd denom = pp * qq;
        RationalSurd numer = denom - pq * pq;
        return {numer, denom};
    }

    // Project to axial hex grid: (q_hex, r_hex) using integer (a-field) parts
    std::pair<int32_t,int32_t> hex_project() const {
        QuadrayVector norm = normalize();
        int32_t d_offset = norm.d.a;
        return {checked_i32(Wide(norm.a.a) - d_offset), checked_i32(Wide(norm.b.a) - d_offset)};
    }

    bool is_zero() const {
        return a.is_zero() && b.is_zero() && c.is_zero() && d.is_zero();
    }

    std::string repr() const {
        return "[" + a.repr() + ", " + b.repr() + ", "
             + c.repr() + ", " + d.repr() + "]";
    }
};

// ============================================================================
// Opcode table
// ============================================================================

static const std::unordered_map<std::string,uint8_t> OPCODES = {
    {"LD",0x00},{"ADD",0x01},{"SUB",0x02},{"MUL",0x03},{"ROT",0x04},
    {"LOG",0x05},{"JMP",0x06},{"SNAP",0x07},{"HALT",0x08},
    {"QADD",0x10},{"QROT",0x11},{"QNORM",0x12},{"QLOAD",0x13},{"QLOG",0x14},
    {"SPREAD",0x15},{"HEX",0x16},{"QSUB",0x1B},{"ROTC",0x1C},{"QLDI",0x1D},{"DELTA",0x1E},
    {"EQUIL",0x17},{"IDNT",0x18},{"JINV",0x19},{"ANNE",0x1A},
    {"CALL",0x20},{"RET",0x21},{"QREAD",0x22},
    {"NOP",0xFF},
};

static const std::unordered_map<uint8_t,std::string> OPNAMES = [](){
    std::unordered_map<uint8_t,std::string> m;
    for (auto& kv : OPCODES) m[kv.second] = kv.first;
    return m;
}();

// ============================================================================
// Assembler — two-pass, matches Python spu_vm.py v1.2
// ============================================================================

static std::string str_toupper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return std::toupper(c); });
    return s;
}

// Tokenize, stripping comments and commas
static std::vector<std::string> tokenize(const std::string& line) {
    std::string clean;
    for (char c : line) {
        if (c == ';') break;
        clean += (c == ',') ? ' ' : c;
    }
    std::istringstream ss(clean);
    std::vector<std::string> parts;
    std::string tok;
    while (ss >> tok) parts.push_back(tok);
    return parts;
}

#include "assembly_operands.h"

static uint64_t assemble_line(const std::vector<std::string>& parts,
                               int line_no,
                               const std::unordered_map<std::string,int>& labels) {
    if (parts.empty()) return (uint64_t)-1;
    std::string mnemonic = str_toupper(parts[0]);
    if (mnemonic.back() == ':') return (uint64_t)-1;
    if (mnemonic == "COND")
        throw std::runtime_error("COND has no canonical encoding; legacy sources require explicit migration");
    auto it = OPCODES.find(mnemonic);
    if (it == OPCODES.end()) {
        throw std::runtime_error("unsupported mnemonic '" + mnemonic + "' at line " + std::to_string(line_no));
    }
    validate_operands(parts, labels);
    uint8_t opcode = it->second;
    if ((mnemonic == "ADD" || mnemonic == "SUB" || mnemonic == "MUL") && parts.size() != 3)
        throw std::runtime_error(mnemonic + " requires Rd, Rs (in-place)");
    uint8_t  r1 = 0, r2 = 0;
    uint16_t p1_a = 0, p1_b = 0;

    auto parse_reg_index = [](const std::string& raw) -> uint8_t {
        std::string arg = str_toupper(raw);
        if (arg.substr(0,2) == "QR") return (uint8_t)(std::stoi(arg.substr(2)) & 0xFF);
        if (arg[0] == 'R') return (uint8_t)(std::stoi(arg.substr(1)) & 0xFF);
        return (uint8_t)(operand_integer(raw) & 0xFF);
    };

    auto parse_qr_index = [](const std::string& raw) -> uint8_t {
        std::string arg = str_toupper(raw);
        if (arg.substr(0,2) != "QR")
            throw std::runtime_error("expected QR register");
        return (uint8_t)(std::stoi(arg.substr(2)) & 0xFF);
    };

    if (mnemonic == "QREAD") {
        if (parts.size() != 3)
            throw std::runtime_error("QREAD requires QRd, QRs");
        r1 = parse_qr_index(parts[1]);
        r2 = parse_qr_index(parts[2]);
        return (uint64_t(opcode)<<56) | (uint64_t(r1)<<48) | (uint64_t(r2)<<40);
    }

    if (mnemonic == "QSUB") {
        if (parts.size() < 3) {
            std::cerr << "  ASM error line " << line_no
                      << ": QSUB requires QRd, QRs or QRd, QRa, QRb\n";
            return (uint64_t)-1;
        }
        try {
            r1 = parse_qr_index(parts[1]);
            if (parts.size() > 3) {
                r2 = parse_qr_index(parts[2]);
                p1_b = parse_qr_index(parts[3]);
            } else {
                r2 = r1;
                p1_b = parse_qr_index(parts[2]);
            }
        } catch (const std::exception& e) {
            std::cerr << "  ASM error line " << line_no << ": " << e.what() << "\n";
            return (uint64_t)-1;
        }
        return ((uint64_t)opcode << 56)
             | ((uint64_t)r1    << 48)
             | ((uint64_t)r2    << 40)
             | ((uint64_t)p1_a  << 24)
             | ((uint64_t)p1_b  <<  8);
    }

    if (mnemonic == "ROTC") {
        if (parts.size() < 4) {
            std::cerr << "  ASM error line " << line_no
                      << ": ROTC requires QRd, QRs, angle\n";
            return (uint64_t)-1;
        }
        r1 = parse_qr_index(parts[1]);
        r2 = parse_qr_index(parts[2]);
        p1_a = (uint16_t)(operand_integer(parts[3]) & 0xFF);
        return ((uint64_t)opcode << 56)
             | ((uint64_t)r1    << 48)
             | ((uint64_t)r2    << 40)
             | ((uint64_t)p1_a  << 24)
             | ((uint64_t)p1_b  <<  8);
    }

    if (mnemonic == "QLDI") {
        if (parts.size() < 6) {
            std::cerr << "  ASM error line " << line_no
                      << ": QLDI requires QRd, A, B, C, D\n";
            return (uint64_t)-1;
        }
        r1 = parse_qr_index(parts[1]);
        uint8_t a = (uint8_t)(operand_integer(parts[2]) & 0xFF);
        uint8_t b = (uint8_t)(operand_integer(parts[3]) & 0xFF);
        uint8_t c = (uint8_t)(operand_integer(parts[4]) & 0xFF);
        uint8_t d = (uint8_t)(operand_integer(parts[5]) & 0xFF);
        p1_a = (uint16_t)(((uint16_t)a << 8) | b);
        p1_b = (uint16_t)(((uint16_t)c << 8) | d);
        return ((uint64_t)opcode << 56)
             | ((uint64_t)r1    << 48)
             | ((uint64_t)r2    << 40)
             | ((uint64_t)p1_a  << 24)
             | ((uint64_t)p1_b  <<  8);
    }

    if (mnemonic == "DELTA") {
        if (parts.size() < 5) {
            std::cerr << "  ASM error line " << line_no
                      << ": DELTA requires QRd, Q1, Q2, steps\n";
            return (uint64_t)-1;
        }
        r1 = parse_qr_index(parts[1]);
        p1_a = (uint16_t)(operand_integer(parts[2]) & 0xFFFF);
        p1_b = (uint16_t)(operand_integer(parts[3]) & 0xFFFF);
        r2 = (uint8_t)(operand_integer(parts[4]) & 0xFF);
        return ((uint64_t)opcode << 56)
             | ((uint64_t)r1    << 48)
             | ((uint64_t)r2    << 40)
             | ((uint64_t)p1_a  << 24)
             | ((uint64_t)p1_b  <<  8);
    }

    auto parse_arg = [&](const std::string& raw, bool is_first) {
        std::string arg = str_toupper(raw);
        if (arg.substr(0,2) == "QR") {
            uint8_t idx = parse_reg_index(raw);
            if (is_first) r1 = idx; else r2 = idx;
        } else if (arg[0] == 'R') {
            uint8_t idx = parse_reg_index(raw);
            if (is_first) r1 = idx; else r2 = idx;
        } else {
            auto lit = labels.find(arg);
            if (lit != labels.end()) {
                p1_a = (uint16_t)(lit->second & 0xFFFF);
            } else {
                p1_a = (uint16_t)(operand_integer(raw) & 0xFFFF);
            }
        }
    };

    if (parts.size() > 1) parse_arg(parts[1], true);
    if (parts.size() > 2) parse_arg(parts[2], false);
    if (parts.size() > 3) {
        // Third operand: QR index → p1_b; immediate → p1_b (e.g. LD R0, 2, 1)
        std::string arg = str_toupper(parts[3]);
        if (arg.substr(0,2) == "QR") {
            p1_b = (uint16_t)(std::stoi(arg.substr(2)) & 0xFFFF);
        } else if (arg[0] == 'R') {
            p1_b = (uint16_t)(std::stoi(arg.substr(1)) & 0xFFFF);
        } else {
            int32_t v = operand_integer(parts[3]);
            p1_b = (uint16_t)(v & 0xFFFF);
        }
    }

    uint64_t word = ((uint64_t)opcode << 56)
                  | ((uint64_t)r1    << 48)
                  | ((uint64_t)r2    << 40)
                  | ((uint64_t)p1_a  << 24)
                  | ((uint64_t)p1_b  <<  8);
    return word;
}

std::vector<uint64_t> assemble_source(const std::string& source) {
    std::istringstream iss(source);
    std::string line;
    std::unordered_map<std::string,int> labels;
    std::vector<std::string> raw_lines;

    // Pass 1: collect labels
    int addr = 0;
    while (std::getline(iss, line)) {
        raw_lines.push_back(line);
        auto parts = tokenize(line);
        if (parts.empty()) continue;
        std::string t = str_toupper(parts[0]);
        if (t == "COND")
            throw std::runtime_error("COND has no canonical encoding; legacy sources require explicit migration");
        if (!t.empty() && t.back() == ':') {
            labels[t.substr(0, t.size()-1)] = addr;
        } else if (OPCODES.count(t)) {
            addr++;
        }
    }

    // Pass 2: emit
    std::vector<uint64_t> words;
    int line_no = 0;
    for (auto& ln : raw_lines) {
        line_no++;
        auto parts = tokenize(ln);
        if (parts.empty()) continue;
        std::string t = str_toupper(parts[0]);
        if (t == "COND")
            throw std::runtime_error("COND has no canonical encoding; legacy sources require explicit migration");
        if (t.empty() || t.back() == ':') continue;
        if (!OPCODES.count(t))
            throw std::runtime_error("unsupported mnemonic '" + t + "'");
        uint64_t w = assemble_line(parts, line_no, labels);
        if (w != (uint64_t)-1) words.push_back(w);
    }
    return words;
}

// ============================================================================
// SPUCore — interpreter
// ============================================================================

static const int NUM_REGS = 26;

class SPUCore {
public:
    RationalSurd regs[NUM_REGS];
    QuadrayVector qregs[13];
    std::vector<int> call_stack;
    int pc = 0;
    std::vector<uint64_t> program;
    int step_count = 0;
    int max_steps;
    bool verbose;
    bool proof;
    bool halted = false;
    bool step_limit_reached = false;
    int snap_failures = 0;
    std::string fault_kind;

private:
    MetricSemantics metric_semantics_;  // fixed at construction; no setter
public:
    MetricSemantics metric_semantics() const { return metric_semantics_; }

    SPUCore(int ms = 256, bool v = true, bool p = false,
            MetricSemantics m = MetricSemantics::LegacyDot)
        : max_steps(ms), verbose(v), proof(p), metric_semantics_(m) {
        for (int i = 0; i < NUM_REGS; i++) regs[i] = RationalSurd(0,0);
    }

    void load(const std::vector<uint64_t>& words) {
        program = words;
        pc = 0; halted = false; step_limit_reached = false;
        step_count = 0; fault_kind.clear();
        if (verbose)
            std::cout << "  SPU-VM: " << words.size() << " words loaded.\n";
    }

    struct Decoded { uint8_t opcode, r1, r2; int32_t p1_a, p1_b; };

    Decoded decode(uint64_t word) const {
        Decoded d;
        d.opcode = (word >> 56) & 0xFF;
        d.r1     = (word >> 48) & 0xFF;
        d.r2     = (word >> 40) & 0xFF;
        uint32_t pa = (word >> 24) & 0xFFFF;
        uint32_t pb = (word >>  8) & 0xFFFF;
        // Sign-extend 16-bit
        d.p1_a = (pa & 0x8000) ? (int32_t)(pa | 0xFFFF0000u) : (int32_t)pa;
        d.p1_b = (pb & 0x8000) ? (int32_t)(pb | 0xFFFF0000u) : (int32_t)pb;
        return d;
    }

    std::string q_proof(const RationalSurd& r, const std::string& label = "") const {
        Wide q = r.quadrance();
        std::string stable = q > 0 ? "✓ laminar" : (q == 0 ? "∅ zero" : "✗ CUBIC");
        std::string s = label.empty() ? "  " : ("  " + label + "  ");
        s += "Q(" + r.repr() + ") = " + std::to_string(r.a) + "² - 3·"
           + std::to_string(r.b) + "² = "
           + std::to_string((int64_t)r.a*r.a) + " - "
           + wide_string(3*Wide(r.b)*r.b) + " = "
           + wide_string(q) + "  " + stable;
        return s;
    }

    std::string reg_str(int idx) const {
        const RationalSurd& r = regs[idx];
        Wide q = r.quadrance();
        std::string stable = q > 0 ? "✓" : (q == 0 ? "∅" : "✗");
        return "R" + std::to_string(idx) + "=" + r.repr()
             + " Q=" + wide_string(q)
             + " " + stable
             + " C=" + r.davis_c();
    }

    std::string qreg_str(int idx) const {
        const QuadrayVector& qr = qregs[idx];
        RationalSurd q = qr.quadrance();
        auto [hx, hy] = qr.hex_project();
        return "QR" + std::to_string(idx) + "=" + qr.repr()
             + " Q=" + q.repr()
             + " hex=(" + std::to_string(hx) + "," + std::to_string(hy) + ")";
    }

    bool step() {
        RationalSurd saved_regs[NUM_REGS];
        QuadrayVector saved_qregs[13];
        std::copy(std::begin(regs), std::end(regs), saved_regs);
        std::copy(std::begin(qregs), std::end(qregs), saved_qregs);
        auto saved_stack = call_stack;
        int saved_pc = pc, saved_steps = step_count, saved_snap = snap_failures;
        try { return execute_step(); }
        catch (const VmFault& fault) {
            std::copy(std::begin(saved_regs), std::end(saved_regs), regs);
            std::copy(std::begin(saved_qregs), std::end(saved_qregs), qregs);
            call_stack = saved_stack;
            pc = saved_pc; step_count = saved_steps; snap_failures = saved_snap;
            halted = true; fault_kind = fault.kind;
            throw;
        }
    }

    bool execute_step() {
        if (halted || pc < 0 || pc >= (int)program.size()) {
            halted = true;
            return false;
        }

        uint64_t word = program[pc];
        Decoded d = decode(word);
        // Scalar storage must never be indexed out of bounds; QR wrapping stays.
        switch (d.opcode) {
        case 0x00: case 0x04: case 0x05: case 0x19: case 0x15: case 0x16:
            if (d.r1 >= NUM_REGS) throw VmFault("INVALID_REGISTER", "invalid scalar destination");
            break;
        case 0x01: case 0x02: case 0x03:
            if (d.r1 >= NUM_REGS || d.r2 >= NUM_REGS)
                throw VmFault("INVALID_REGISTER", "invalid scalar operand");
            break;
        }
        int next_pc = pc + 1;

        // Build immediate; seed pell_step=0 when loading (1,0)
        RationalSurd imm(d.p1_a, d.p1_b,
                         (d.p1_a == 1 && d.p1_b == 0) ? 0 : -1);

        switch (d.opcode) {

        // ── Scalar Q(√3) arithmetic ─────────────────────────────────────
        case 0x00: { // LD
            regs[d.r1] = imm;
            if (verbose) std::cout << "  [" << std::to_string(pc) << "] LD    R"
                                   << (int)d.r1 << " ← " << imm.repr() << "\n";
            if (proof) std::cout << "         " << q_proof(imm, "R" + std::to_string(d.r1) + ":") << "\n";
            break;
        }
        case 0x01: { // ADD
            RationalSurd prev = regs[d.r1];
            regs[d.r1] = regs[d.r1] + regs[d.r2];
            if (verbose) std::cout << "  [" << pc << "] ADD   R" << (int)d.r1
                                   << " + R" << (int)d.r2 << " → " << regs[d.r1].repr() << "\n";
            if (proof) std::cout << "         (" << prev.a << "+" << prev.b << "·√3)"
                                 << " + (" << regs[d.r2].a << "+" << regs[d.r2].b << "·√3)"
                                 << "  →  a=" << prev.a << "+" << regs[d.r2].a
                                 << "=" << regs[d.r1].a
                                 << "  b=" << prev.b << "+" << regs[d.r2].b
                                 << "=" << regs[d.r1].b << "\n";
            break;
        }
        case 0x02: { // SUB
            RationalSurd prev = regs[d.r1];
            regs[d.r1] = regs[d.r1] - regs[d.r2];
            if (verbose) std::cout << "  [" << pc << "] SUB  R" << (int)d.r1
                                   << " - R" << (int)d.r2 << " → " << regs[d.r1].repr() << "\n";
            if (proof) std::cout << "         (" << prev.a << "+" << prev.b << "·√3)"
                                 << " - (" << regs[d.r2].a << "+" << regs[d.r2].b << "·√3)"
                                 << "  →  a=" << regs[d.r1].a << "  b=" << regs[d.r1].b << "\n";
            break;
        }
        case 0x03: { // MUL
            RationalSurd prev = regs[d.r1], rhs = regs[d.r2];
            regs[d.r1] = prev * rhs;
            if (verbose) std::cout << "  [" << pc << "] MUL  R" << (int)d.r1
                                   << " × R" << (int)d.r2 << " → " << regs[d.r1].repr() << "\n";
            if (proof) {
                Wide ra = Wide(prev.a) * rhs.a + 3*Wide(prev.b)*rhs.b;
                Wide rb = Wide(prev.a) * rhs.b + Wide(prev.b)*rhs.a;
                std::cout << "         (" << prev.a << "+" << prev.b << "·√3)"
                          << " × (" << rhs.a << "+" << rhs.b << "·√3)\n"
                          << "         a=" << (int64_t)prev.a<<"·"<<rhs.a
                          << "+3·"<<prev.b<<"·"<<rhs.b<<"="<<wide_string(ra)<<"\n"
                          << "         b="<<prev.a<<"·"<<rhs.b
                          <<"+"<<prev.b<<"·"<<rhs.a<<"="<<wide_string(rb)<<"\n"
                          << "         " << q_proof(regs[d.r1]) << "\n";
            }
            break;
        }
        case 0x04: { // ROT
            RationalSurd prev = regs[d.r1];
            regs[d.r1] = rotate_phi(prev);
            if (verbose) {
                std::string oct_info;
                if (regs[d.r1].pell_step >= 0) {
                    int oct = regs[d.r1].pell_step / 8;
                    int st  = regs[d.r1].pell_step % 8;
                    oct_info = "  [oct=" + std::to_string(oct)
                             + ", step=" + std::to_string(st)
                             + ", total=r^" + std::to_string(regs[d.r1].pell_step) + "]";
                }
                std::cout << "  [" << pc << "] ROT  R" << (int)d.r1 << ": "
                          << prev.repr() << " → " << regs[d.r1].repr() << oct_info << "\n";
            }
            if (proof) {
                Wide na = 2*Wide(prev.a) + 3*Wide(prev.b);
                Wide nb = Wide(prev.a) + 2*Wide(prev.b);
                std::cout << "         Pell step: (2+√3) × (" << prev.a << "+" << prev.b << "·√3)\n"
                          << "         a=2·"<<prev.a<<"+3·"<<prev.b<<"="<<wide_string(na)<<"\n"
                          << "         b="<<prev.a<<"+2·"<<prev.b<<"="<<wide_string(nb)<<"\n"
                          << "         " << q_proof(regs[d.r1]) << "\n";
            }
            break;
        }
        case 0x05: { // LOG
            std::string msg = reg_str(d.r1);
            std::cout << "  [" << pc << "] LOG  " << msg << "\n";
            break;
        }
        case 0x06: { // JMP
            int target = (int)(uint16_t)d.p1_a;
            if (verbose) std::cout << "  [" << pc << "] JMP  → " << target << "\n";
            next_pc = target;
            break;
        }
        case 0x07: { // SNAP
            std::vector<int> failures;
            for (int i = 0; i < NUM_REGS; i++) {
                if (!regs[i].is_zero() && !regs[i].is_laminar())
                    failures.push_back(i);
            }
            if (!failures.empty()) {
                snap_failures++;
                std::cout << "  [" << pc << "] SNAP ✗ CUBIC LEAK — unstable regs: {";
                for (int i = 0; i < (int)failures.size(); i++) {
                    if (i) std::cout << ", ";
                    std::cout << failures[i];
                }
                std::cout << "}\n";
                if (proof) for (int i : failures)
                    std::cout << "         " << q_proof(regs[i], "R"+std::to_string(i)+":") << "\n";
            } else if (verbose) {
                std::string oct_summary;
                for (int i = 0; i < NUM_REGS; i++) {
                    if (!regs[i].is_zero() && regs[i].pell_step >= 0) {
                        if (!oct_summary.empty()) oct_summary += ", ";
                        int oct = regs[i].pell_step / 8;
                        int st  = regs[i].pell_step % 8;
                        oct_summary += "R" + std::to_string(i)
                                     + "=r^" + std::to_string(regs[i].pell_step)
                                     + "(oct=" + std::to_string(oct)
                                     + ",s=" + std::to_string(st) + ")";
                    }
                }
                std::cout << "  [" << pc << "] SNAP ✓ Manifold stable";
                if (!oct_summary.empty()) std::cout << "  " << oct_summary;
                std::cout << "\n";
                if (proof) for (int i = 0; i < NUM_REGS; i++)
                    if (!regs[i].is_zero())
                        std::cout << "         " << q_proof(regs[i], "R"+std::to_string(i)+":") << "\n";
            }
            break;
        }
        // ── Control flow ────────────────────────────────────────────────
        case 0x20: { // CALL
            call_stack.push_back(next_pc);
            next_pc = (int)(uint16_t)d.p1_a;
            if (verbose) std::cout << "  [" << pc << "] CALL → " << next_pc
                                   << "  (ret=" << call_stack.back() << ")\n";
            break;
        }
        case 0x21: { // RET
            if (!call_stack.empty()) {
                next_pc = call_stack.back();
                call_stack.pop_back();
                if (verbose) std::cout << "  [" << pc << "] RET  → " << next_pc << "\n";
            } else {
                if (verbose) std::cout << "  [" << pc << "] RET  (empty stack — halting)\n";
                halted = true;
            }
            break;
        }
        // ── Quadray IVM operations ───────────────────────────────────────
        case 0x13: { // QLOAD
            int base = d.r2;
            QuadrayVector qv(
                regs[(base+0) % NUM_REGS], regs[(base+1) % NUM_REGS],
                regs[(base+2) % NUM_REGS], regs[(base+3) % NUM_REGS]);
            qregs[d.r1 % 13] = qv;
            if (verbose) std::cout << "  [" << pc << "] QLOAD QR" << (int)(d.r1%13)
                                   << " ← R" << base << "..R" << (base+3)
                                   << " = " << qv.repr() << "\n";
            break;
        }
        case 0x1D: { // QLDI
            uint16_t pa = (uint16_t)d.p1_a;
            uint16_t pb = (uint16_t)d.p1_b;
            int32_t A = sign_extend8(pa >> 8);
            int32_t B = sign_extend8(pa);
            int32_t C = sign_extend8(pb >> 8);
            int32_t D = sign_extend8(pb);
            int n = d.r1 % 13;
            qregs[n] = QuadrayVector(
                RationalSurd(A, 0), RationalSurd(B, 0),
                RationalSurd(C, 0), RationalSurd(D, 0));
            if (verbose) std::cout << "  [" << pc << "] QLDI QR" << n
                                   << " ← (" << A << "," << B << ","
                                   << C << "," << D << ") → "
                                   << qregs[n].repr() << "\n";
            break;
        }
        case 0x1E: { // DELTA
            uint16_t Q1 = (uint16_t)d.p1_a;
            uint16_t Q2 = (uint16_t)d.p1_b;
            int steps = d.r2 > 0 ? d.r2 : 4;
            int n = d.r1 % 13;
            int32_t q_sum = (int32_t)Q1 + (int32_t)Q2;
            Wide rhs_sq = 4 * Wide(Q1) * Q2;

            for (int k = 0; k <= steps; k++) {
                Wide rhs = (4 * Wide(Q1) * Q2 * (steps - k)) / steps;
                if (k == steps) rhs_sq = rhs;
            }

            qregs[n] = QuadrayVector(
                RationalSurd(q_sum, 0),
                RationalSurd(checked_i32(rhs_sq), 0),
                RationalSurd(steps, 0),
                RationalSurd(0, 0));
            if (verbose) std::cout << "  [" << pc << "] DELTA QR" << n
                                   << " Q1=" << Q1 << " Q2=" << Q2
                                   << " steps=" << steps
                                   << " → q_sum=" << q_sum
                                   << " rhs²=" << wide_string(rhs_sq) << "/" << steps << "\n";
            break;
        }
        case 0x10: { // QADD
            int dd = d.r1 % 13, s = d.r2 % 13;
            qregs[dd] = qregs[dd] + qregs[s];
            if (verbose) std::cout << "  [" << pc << "] QADD QR" << dd
                                   << " + QR" << s << " → " << qregs[dd].repr() << "\n";
            break;
        }
        case 0x1B: { // QSUB
            int dd = d.r1 % 13;
            int a = d.r2 % 13;
            int b = ((uint16_t)d.p1_b) % 13;
            qregs[dd] = qregs[a] - qregs[b];
            if (verbose) std::cout << "  [" << pc << "] QSUB QR" << dd
                                   << " ← QR" << a << " - QR" << b
                                   << " → " << qregs[dd].repr() << "\n";
            break;
        }
        case 0x11: { // QROT
            int n = d.r1 % 13;
            qregs[n] = qregs[n].rotate();
            if (verbose) {
                auto [hx,hy] = qregs[n].hex_project();
                std::cout << "  [" << pc << "] QROT QR" << n
                          << " → " << qregs[n].repr()
                          << "  hex=(" << hx << "," << hy << ")\n";
            }
            break;
        }
        case 0x1C: { // ROTC
            struct RotcCoeff {
                int32_t fa, fb, ga, gb, ha, hb, denom;
            };
            static const std::unordered_map<int, RotcCoeff> ROTC_TABLE = {
                {0, { 1, 0,  0, 0,  0, 0, 1}},
                {1, { 2, 0,  2, 0, -1, 0, 3}},
                {2, { 0, 0,  1, 0,  0, 0, 1}},
                {3, {-1, 0,  2, 0,  2, 0, 3}},
                {4, { 2, 0, -1, 0,  2, 0, 3}},
                {5, { 0, 0,  0, 0,  1, 0, 1}},
            };

            int angle = ((uint16_t)d.p1_a) & 0x3F;
            auto it_rotc = ROTC_TABLE.find(angle);
            if (it_rotc == ROTC_TABLE.end()) {
                halted = true;
                throw VmFault("UNSUPPORTED", "unsupported C++ ROTC angle " + std::to_string(angle));
            }

            int dd = d.r1 % 13;
            int s = d.r2 % 13;
            const RotcCoeff& rc = it_rotc->second;
            const QuadrayVector& src = qregs[s];
            auto component = [&](int f, int h, int g) {
                return RationalSurd(
                    checked_i32(nearest_div(Wide(f)*src.b.a + Wide(h)*src.c.a + Wide(g)*src.d.a, rc.denom)),
                    checked_i32(nearest_div(Wide(f)*src.b.b + Wide(h)*src.c.b + Wide(g)*src.d.b, rc.denom)));
            };
            auto rb = component(rc.fa, rc.ha, rc.ga);
            auto rc_value = component(rc.ga, rc.fa, rc.ha);
            auto rd = component(rc.ha, rc.ga, rc.fa);
            qregs[dd] = QuadrayVector(src.a, rb, rc_value, rd);

            if (verbose) {
                static const char* names[6] = {
                    "identity", "thirds period-6", "P5 forward",
                    "thirds period-2", "thirds period-6 inverse", "P5 inverse"
                };
                std::cout << "  [" << pc << "] ROTC QR" << dd
                          << " ← QR" << s << " @" << names[angle]
                          << " → " << qregs[dd].repr() << "\n";
            }
            break;
        }
        case 0x22: { // QREAD: basic QR copy; C++ has no IROTC tags
            qregs[d.r1 % 13] = qregs[d.r2 % 13];
            break;
        }
        case 0x12: { // QNORM
            int n = d.r1 % 13;
            qregs[n] = qregs[n].normalize();
            if (verbose) std::cout << "  [" << pc << "] QNORM QR" << n
                                   << " → " << qregs[n].repr() << "\n";
            break;
        }
        case 0x14: { // QLOG
            int n = d.r1 % 13;
            std::cout << "  [" << pc << "] QLOG " << qreg_str(n) << "\n";
            break;
        }
        // ── Geometry output ──────────────────────────────────────────────
        case 0x15: { // SPREAD
            int qa = d.r2 % 13;
            int qb = (int)(uint16_t)d.p1_b % 13;
            RationalSurd numer, denom;
            if (metric_semantics() == MetricSemantics::GramV1) {
                int32_t v[4][2], w[4][2];
                const RationalSurd* vc[4] = {&qregs[qa].a, &qregs[qa].b, &qregs[qa].c, &qregs[qa].d};
                const RationalSurd* wc[4] = {&qregs[qb].a, &qregs[qb].b, &qregs[qb].c, &qregs[qb].d};
                for (int i = 0; i < 4; i++) {
                    v[i][0] = vc[i]->a; v[i][1] = vc[i]->b;
                    w[i][0] = wc[i]->a; w[i][1] = wc[i]->b;
                }
                gram::Result g = gram::spread(v, w);
                if (g.status == gram::Status::Degenerate)
                    throw VmFault("DEGENERATE_METRIC", "gram_v1 SPREAD operand has zero Gram quadrance");
                if (g.status == gram::Status::Overflow)
                    throw VmFault("OVERFLOW", "gram_v1 SPREAD result outside signed32 coefficients");
                numer = RationalSurd(g.n[0], g.n[1]);
                denom = RationalSurd(g.d[0], g.d[1]);
            } else {
                std::tie(numer, denom) = qregs[qa].spread(qregs[qb]);
            }
            regs[d.r1] = numer;
            regs[(d.r1+1) % NUM_REGS] = denom;
            if (verbose) std::cout << "  [" << pc << "] SPREAD QR" << qa
                                   << "∧QR" << qb << " → " << numer.repr()
                                   << "/" << denom.repr()
                                   << "  (→ R" << (int)d.r1 << "/R"
                                   << (int)((d.r1+1)%NUM_REGS) << ")\n";
            if (proof && metric_semantics() == MetricSemantics::GramV1) {
                int32_t v[4][2], w[4][2];
                const RationalSurd* vc[4] = {&qregs[qa].a, &qregs[qa].b, &qregs[qa].c, &qregs[qa].d};
                const RationalSurd* wc[4] = {&qregs[qb].a, &qregs[qb].b, &qregs[qb].c, &qregs[qb].d};
                for (int i = 0; i < 4; i++) { v[i][0] = vc[i]->a; v[i][1] = vc[i]->b; w[i][0] = wc[i]->a; w[i][1] = wc[i]->b; }
                gram::Gram3 g = gram::gram3(v, w);
                std::cout << "         B(v,v)=(" << wide_string(g.vv[0]) << "," << wide_string(g.vv[1]) << ")"
                          << " B(w,w)=(" << wide_string(g.ww[0]) << "," << wide_string(g.ww[1]) << ")"
                          << " B(v,w)=(" << wide_string(g.vw[0]) << "," << wide_string(g.vw[1]) << ")\n";
            }
            if (proof) std::cout << "         exact spread numerator=" << numer.repr()
                                 << " denominator=" << denom.repr() << "\n";

            break;
        }
        case 0x16: { // HEX
            int n = d.r2 % 13;
            auto [hq, hr] = qregs[n].hex_project();
            regs[d.r1] = RationalSurd(hq, 0);
            regs[(d.r1+1) % NUM_REGS] = RationalSurd(hr, 0);
            if (verbose) std::cout << "  [" << pc << "] HEX  QR" << n
                                   << " → pixel (" << hq << ", " << hr << ")"
                                   << "  (→ R" << (int)d.r1 << ", R"
                                   << (int)((d.r1+1)%NUM_REGS) << ")\n";
            break;
        }
        // ── v1.2 Vector Equilibrium + Janus layer ───────────────────────
        case 0x17: { // EQUIL
            std::vector<int> active;
            for (int i = 0; i < 13; i++)
                if (!qregs[i].is_zero()) active.push_back(i);
            int64_t sum_hx = 0, sum_hy = 0;
            for (int i : active) {
                auto [hx,hy] = qregs[i].hex_project();
                sum_hx += hx; sum_hy += hy;
            }
            bool balanced = (sum_hx == 0 && sum_hy == 0);
            if (balanced) {
                if (verbose) std::cout << "  [" << pc
                    << "] EQUIL ✓ Vector Equilibrium — hex sum=(0,0)"
                    << "  (" << active.size() << " active axes)\n";
            } else {
                snap_failures++;
                std::cout << "  [" << pc
                    << "] EQUIL ✗ MANIFOLD TENSION — hex residual=("
                    << sum_hx << "," << sum_hy << ")"
                    << "  (" << active.size() << " active axes)\n";
            }
            if (proof && !active.empty()) {
                std::cout << "         Active QR axes: {";
                for (int i = 0; i < (int)active.size(); i++) {
                    if (i) std::cout << ",";
                    std::cout << active[i];
                }
                std::cout << "}\n";
                for (int i : active) {
                    auto [hx,hy] = qregs[i].hex_project();
                    std::cout << "           QR" << i << ": " << qregs[i].repr()
                              << "  hex=(" << (hx>=0?"+":"") << hx
                              << "," << (hy>=0?"+":"") << hy << ")\n";
                }
                std::cout << "         Σ hex = (" << (sum_hx>=0?"+":"") << sum_hx
                          << "," << (sum_hy>=0?"+":"") << sum_hy << ")"
                          << "  VE condition → " << (balanced?"PASS":"FAIL") << "\n";
            }
            break;
        }
        case 0x18: { // IDNT
            int n = d.r1 % 13;
            QuadrayVector prev = qregs[n];
            qregs[n] = QuadrayVector(RationalSurd(1,0), RationalSurd(0,0),
                                     RationalSurd(0,0), RationalSurd(0,0));
            if (verbose) std::cout << "  [" << pc << "] IDNT QR" << n
                                   << " → [1,0,0,0]  (was " << prev.repr() << ")\n";
            if (proof) std::cout << "         Identity reset: canonical IVM origin vector.\n"
                                 << "         In Quadray space (1,0,0,0) is the +A tetrahedral vertex.\n";
            break;
        }
        case 0x19: { // JINV
            RationalSurd prev = regs[d.r1];
            regs[d.r1] = RationalSurd(prev.a, checked_i32(-Wide(prev.b)), prev.pell_step);
            if (verbose) std::cout << "  [" << pc << "] JINV R" << (int)d.r1
                                   << ": " << prev.repr() << " → " << regs[d.r1].repr() << "\n";
            if (proof) std::cout << "         Janus flip: b-component sign inverted.\n"
                                 << "         " << prev.a << "+" << prev.b << "·√3"
                                 << "  →  " << prev.a << "+" << -int64_t(prev.b) << "·√3\n"
                                 << "         " << q_proof(regs[d.r1]) << "\n";
            break;
        }
        case 0x1A: { // ANNE
            int n = d.r1 % 13;
            QuadrayVector prev = qregs[n];
            RationalSurd comps[4] = {
                RationalSurd(prev.a.a >> 1, prev.a.b >> 1),
                RationalSurd(prev.b.a >> 1, prev.b.b >> 1),
                RationalSurd(prev.c.a >> 1, prev.c.b >> 1),
                RationalSurd(prev.d.a >> 1, prev.d.b >> 1),
            };
            qregs[n] = QuadrayVector(comps[0],comps[1],comps[2],comps[3]).normalize();
            if (verbose) std::cout << "  [" << pc << "] ANNE QR" << n
                                   << ": " << prev.repr() << " → " << qregs[n].repr() << "\n";
            if (proof) {
                std::cout << "         Anneal step: each component >> 1 (halved toward VE zero-point).\n";
                const RationalSurd* oc[4] = {&prev.a,&prev.b,&prev.c,&prev.d};
                for (int i = 0; i < 4; i++)
                    std::cout << "         axis[" << i << "]: (" << oc[i]->a << ","
                              << oc[i]->b << ") → (" << (oc[i]->a>>1) << ","
                              << (oc[i]->b>>1) << ")\n";
            }
            break;
        }
        case 0x08: // HALT
            halted = true;
            break;
        case 0xFF: // NOP
            if (verbose) std::cout << "  [" << pc << "] NOP\n";
            break;
        default:
            halted = true;
            throw VmFault("UNSUPPORTED", "unsupported canonical opcode " + std::to_string(d.opcode));
        }

        pc = next_pc;
        step_count++;

        if (!halted && step_count >= max_steps) {
            if (verbose)
                std::cout << "\n  SPU-VM: max_steps (" << max_steps << ") reached. Halting.\n";
            step_limit_reached = true;
            halted = true;
            return false;
        }
        return !halted;
    }

    void run() { while (step()) {} }

    void dump_registers() const {
        std::cout << "\n  ── Scalar Registers ───────────────────────────────────────\n";
        bool any_scalar = false;
        for (int i = 0; i < NUM_REGS; i++) {
            if (!regs[i].is_zero()) {
                std::cout << "  " << const_cast<SPUCore*>(this)->reg_str(i) << "\n";
                any_scalar = true;
            }
        }
        if (!any_scalar) std::cout << "  (all zero)\n";

        std::cout << "\n  ── Quadray Registers (IVM Axes) ───────────────────────────\n";
        bool any_quad = false;
        for (int i = 0; i < 13; i++) {
            if (!qregs[i].is_zero()) {
                std::cout << "  " << const_cast<SPUCore*>(this)->qreg_str(i) << "\n";
                any_quad = true;
            }
        }
        if (!any_quad) std::cout << "  (all zero)\n";

        std::cout << "\n  ── PC=" << pc << "  steps=" << step_count
                  << "  snap_failures=" << snap_failures
                  << "  call_depth=" << call_stack.size() << "\n\n";
    }
};

// ============================================================================
// main()
// ============================================================================

int main(int argc, char** argv) {
    // Profile selection: absent = unchanged legacy behaviour; never ignored when present.
    std::vector<char*> profile_argv;
    int profile_status = psurd::dispatch(argc, argv);   // claims only --profile programmable-surd
    if (profile_status >= 0) return profile_status;
    profile_status = gen1::dispatch(argc, argv, profile_argv);
    if (profile_status >= 0) return profile_status;

    std::string source_file;
    std::string bin_file;
    int max_steps = 256;
    bool quiet = false;
    bool proof = false;
    MetricSemantics metric = MetricSemantics::LegacyDot;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--quiet") { quiet = true; }
        else if (arg.rfind("--metric-semantics=", 0) == 0) {
            std::string v = arg.substr(19);
            if (v == "legacy_dot") metric = MetricSemantics::LegacyDot;
            else if (v == "gram_v1") metric = MetricSemantics::GramV1;
            else { std::cerr << "Error: --metric-semantics must be legacy_dot or gram_v1.\n"; return 1; }
        }
        else if (arg == "--proof") { proof = true; }
        else if (arg == "--bin" && i+1 < argc) { bin_file = argv[++i]; }
        else if (arg == "--steps") {
            if (i + 1 >= argc) {
                std::cerr << "Error: --steps requires a positive integer.\n";
                return 1;
            }
            try {
                std::string limit = argv[++i];
                std::size_t consumed = 0;
                max_steps = std::stoi(limit, &consumed);
                if (consumed != limit.size())
                    throw std::invalid_argument("trailing characters");
            }
            catch (const std::exception&) {
                std::cerr << "Error: --steps requires a positive integer.\n";
                return 1;
            }
        }
        else if (arg[0] != '-') { source_file = arg; }
    }

    if (max_steps <= 0) {
        std::cerr << "Error: --steps requires a positive integer.\n";
        return 1;
    }

    std::string target = bin_file.empty() ? source_file : bin_file;
    if (target.empty()) {
        std::cerr << "Usage: spu_vm [--bin FILE] [--steps N] [--quiet] [--proof] [--metric-semantics=legacy_dot|gram_v1] <file.sas|file.bin>\n";
        return 1;
    }

    bool verbose = !quiet;
    SPUCore core(max_steps, verbose, proof, metric);
    std::vector<uint64_t> words;

    bool is_bin = !bin_file.empty()
               || (target.size() >= 4 && target.substr(target.size()-4) == ".bin");

    if (is_bin) {
        std::ifstream f(target, std::ios::binary);
        if (!f) { std::cerr << "Error: cannot open " << target << "\n"; return 1; }
        uint8_t buf[8];
        while (f.read((char*)buf, 8)) {
            uint64_t w = 0;
            for (int i = 0; i < 8; i++) w = (w << 8) | buf[i];
            words.push_back(w);
        }
        std::cout << "\n  SPU-13 Sovereign VM  |  " << target << "  |  binary\n";
    } else {
        std::ifstream f(target);
        if (!f) { std::cerr << "Error: cannot open " << target << "\n"; return 1; }
        std::string src((std::istreambuf_iterator<char>(f)),
                         std::istreambuf_iterator<char>());
        try { words = assemble_source(src); }
        catch (const std::runtime_error& error) {
            std::cerr << "Assembly rejected: " << error.what() << "\n";
            return 1;
        }
        if (words.empty()) {
            std::cerr << "Error: no instructions assembled.\n";
            return 1;
        }
        std::cout << "\n  SPU-13 Sovereign VM  |  " << target
                  << "  |  " << words.size() << " words\n";
    }

    std::cout << "  ──────────────────────────────────────────────────────────\n";
    core.load(words);
    try { core.run(); }
    catch (const std::runtime_error& error) {
        std::cerr << "Execution rejected: " << error.what() << "\n";
        return 1;
    }
    core.dump_registers();

    if (core.snap_failures) {
        std::cout << "  ⚠  " << core.snap_failures
                  << " SNAP failure(s) — cubic leak detected\n";
        if (core.step_limit_reached)
            std::cerr << "Execution stopped at the --steps budget before HALT.\n";
        return 2;
    }
    if (core.step_limit_reached) {
        std::cerr << "Execution stopped at the --steps budget before HALT.\n";
        return 3;
    }
    std::cout << "  ✓  Execution complete — manifold laminar\n";
    return 0;
}
