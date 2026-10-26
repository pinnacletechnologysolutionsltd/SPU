// spu13_arch.h — SPU-13 Architecture v1.0 behavioral simulator
//
// Twin-register file, temporal ops (OFFR/CNFM/PHSLK/INVJ),
// geometric ops (SPRD/ROTR/CROSS/DOT/TNSR), quadrance arithmetic,
// RPLU material table simulation, phase-lock ratio comparator.
//
// Matches software/spu13_arch_sim.py exactly for cross-validation.
//
// CC0 1.0 Universal.

#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <vector>

// ═════════════════════════════════════════════════════════════════════════════
// Opcode Constants (matching spu_isa_defines.vh and spu13_arch_sim.py)
// ═════════════════════════════════════════════════════════════════════════════

// System
constexpr uint8_t OP_NOP     = 0x00;
constexpr uint8_t OP_HALT    = 0x01;
constexpr uint8_t OP_SYNC    = 0x02;

// Data movement
constexpr uint8_t OP_LOAD    = 0x10;
constexpr uint8_t OP_STORE   = 0x11;
constexpr uint8_t OP_MOV     = 0x12;
constexpr uint8_t OP_MOVI    = 0x13;
constexpr uint8_t OP_LDO     = 0x14;
constexpr uint8_t OP_LDC     = 0x15;

// Quadrance arithmetic
constexpr uint8_t OP_QADD    = 0x20;
constexpr uint8_t OP_QSUB    = 0x21;
constexpr uint8_t OP_QMUL    = 0x22;
constexpr uint8_t OP_QDIV    = 0x23;
constexpr uint8_t OP_QNORM   = 0x24;
constexpr uint8_t OP_QCMP    = 0x25;

// Geometric
constexpr uint8_t OP_SPRD    = 0x30;
constexpr uint8_t OP_ROTR    = 0x31;
constexpr uint8_t OP_CROSS   = 0x32;
constexpr uint8_t OP_DOT     = 0x33;
constexpr uint8_t OP_TNSR    = 0x34;
constexpr uint8_t OP_PROJ    = 0x35;

// Temporal
constexpr uint8_t OP_OFFR    = 0x40;
constexpr uint8_t OP_CNFM    = 0x41;
constexpr uint8_t OP_PHSLK   = 0x42;
constexpr uint8_t OP_INVJ    = 0x43;
constexpr uint8_t OP_PHSTA   = 0x44;
constexpr uint8_t OP_PHCLR   = 0x45;

// RPLU
constexpr uint8_t OP_RCFG    = 0x50;
constexpr uint8_t OP_RREAD   = 0x51;
constexpr uint8_t OP_RLOAD   = 0x52;
constexpr uint8_t OP_RDISSOC = 0x53;

// Flow control
constexpr uint8_t OP_CMP     = 0x60;
constexpr uint8_t OP_JMP     = 0x61;
constexpr uint8_t OP_JZ      = 0x62;
constexpr uint8_t OP_JNZ     = 0x63;
constexpr uint8_t OP_JC      = 0x64;
constexpr uint8_t OP_JNC     = 0x65;
constexpr uint8_t OP_CALL    = 0x66;
constexpr uint8_t OP_RET     = 0x67;

// Telemetry
constexpr uint8_t OP_MFOLD   = 0x70;
constexpr uint8_t OP_STAT    = 0x71;
constexpr uint8_t OP_SCALE   = 0x72;
constexpr uint8_t OP_QR      = 0x73;
constexpr uint8_t OP_HEX     = 0x74;
constexpr uint8_t OP_SENT    = 0x75;

// Special registers
constexpr int REG_ZERO         = 0;
constexpr int REG_PC           = 1;
constexpr int REG_FLAGS        = 2;
constexpr int REG_MANIFOLD_PTR = 3;
constexpr int REG_SCALE_PTR    = 4;
constexpr int REG_CHORD_IN     = 5;
constexpr int REG_CHORD_OUT    = 6;
constexpr int REG_QUAD_OUT     = 7;

// Flag bits
constexpr int FLAG_ZERO     = 0;
constexpr int FLAG_COHERENT = 1;
constexpr int FLAG_SCALE_OVF = 2;
constexpr int FLAG_FIFO_FULL = 3;


// ═════════════════════════════════════════════════════════════════════════════
// Core Types
// ═════════════════════════════════════════════════════════════════════════════

struct Rational {
    int64_t num;
    int64_t den;

    Rational(int64_t n = 0, int64_t d = 1) : num(n), den(d) {
        if (den < 0) { num = -num; den = -den; }
    }

    Rational& normalize() {
        if (num == 0) { den = 1; return *this; }
        if (den < 0) { num = -num; den = -den; }
        int64_t g = gcd(std::llabs(num), std::llabs(den));
        if (g > 1) { num /= g; den /= g; }
        return *this;
    }

    static int64_t gcd(int64_t a, int64_t b) {
        while (b) { int64_t t = b; b = a % b; a = t; }
        return a;
    }

    Rational operator+(const Rational& o) const {
        return Rational(num * o.den + o.num * den, den * o.den).normalize();
    }
    Rational operator-(const Rational& o) const {
        return Rational(num * o.den - o.num * den, den * o.den).normalize();
    }
    Rational operator*(const Rational& o) const {
        return Rational(num * o.num, den * o.den).normalize();
    }
    Rational operator/(const Rational& o) const {
        return Rational(num * o.den, den * o.num).normalize();
    }
    bool operator==(const Rational& o) const {
        return num * o.den == o.num * den;
    }
    bool operator!=(const Rational& o) const { return !(*this == o); }
    Rational operator-() const { return Rational(-num, den); }

    int32_t to_q12() const {
        if (den == 0) return num > 0 ? 0x7FFFFFFF : -0x80000000;
        return int32_t((num << 12) / den);
    }

    void print() const {
        if (den == 1) printf("%lld", (long long)num);
        else printf("%lld/%lld", (long long)num, (long long)den);
    }
};


struct Quadray {
    int32_t a, b, c, d;  // Q12 fixed-point components

    Quadray(int32_t a_=0, int32_t b_=0, int32_t c_=0, int32_t d_=0)
        : a(a_), b(b_), c(c_), d(d_) {}

    Quadray operator+(const Quadray& o) const {
        return { a+o.a, b+o.b, c+o.c, d+o.d };
    }
    Quadray operator-(const Quadray& o) const {
        return { a-o.a, b-o.b, c-o.c, d-o.d };
    }
    Quadray operator-() const {
        return { -a, -b, -c, -d };
    }
    bool operator==(const Quadray& o) const {
        return a==o.a && b==o.b && c==o.c && d==o.d;
    }

    // Quadrance: Q = a² + b² + c² + d² (Q12 scale)
    int64_t quadrance() const {
        int64_t aa = int64_t(a)*a;
        int64_t bb = int64_t(b)*b;
        int64_t cc = int64_t(c)*c;
        int64_t dd = int64_t(d)*d;
        return aa + bb + cc + dd;
    }

    // Scale by 4 (tensor M = 4I)
    Quadray tensor_M() const {
        return { a*4, b*4, c*4, d*4 };
    }

    // Cross product (returns orthogonal complement)
    Quadray cross(const Quadray& o) const {
        return {
            b*o.c - c*o.b,  // a
            c*o.a - a*o.c,  // b
            a*o.b - b*o.a,  // c
            0               // d
        };
    }

    void print() const {
        printf("[%d,%d,%d,%d]", a, b, c, d);
    }
};


// ═════════════════════════════════════════════════════════════════════════════
// Twin-Register File
// ═════════════════════════════════════════════════════════════════════════════

struct TwinReg {
    Quadray O;  // Offer slot
    Quadray C;  // Confirmation slot
};


// ═════════════════════════════════════════════════════════════════════════════
// Instruction Word Pack/Unpack (64-bit, matches spu_isa_defines.vh)
// ═════════════════════════════════════════════════════════════════════════════

inline uint8_t  field_u8(uint64_t w, int hi, int lo) { return (w >> lo) & ((1u << (hi-lo+1)) - 1); }
inline int32_t  field_s10(uint64_t w, int hi, int lo) { int32_t v = (w >> lo) & 0x3FF; return (v & 0x200) ? v - 0x400 : v; }
inline int64_t  field_s51(uint64_t w, int hi, int lo) { int64_t v = (w >> lo) & 0x7FFFFFFFFFFFF; return (v & 0x4000000000000) ? v - 0x8000000000000 : v; }

inline uint64_t pack_R(uint8_t op, uint8_t d=0, uint8_t a=0, uint8_t b=0, uint64_t resv=0) {
    return (uint64_t(op)<<56) | (uint64_t(d&0x1F)<<51) | (uint64_t(a&0x1F)<<46) | (uint64_t(b&0x1F)<<41) | (resv & 0x1FFFFFFFFFF);
}

inline uint64_t pack_L(uint8_t op, uint8_t d=0, uint8_t base=0, int16_t offset=0, uint64_t resv=0) {
    return (uint64_t(op)<<56) | (uint64_t(d&0x1F)<<51) | (uint64_t(base&0x1F)<<46) | ((uint64_t(offset)&0x3FF)<<36) | (resv & 0xFFFFFFFFF);
}

inline uint64_t pack_I(uint8_t op, uint8_t d=0, uint64_t imm=0) {
    return (uint64_t(op)<<56) | (uint64_t(d&0x1F)<<51) | (imm & 0x7FFFFFFFFFFFF);
}

inline uint64_t pack_U(uint8_t op, uint8_t d=0, uint8_t s=0, uint8_t cond=0, uint64_t resv=0) {
    return (uint64_t(op)<<56) | (uint64_t(d&0x1F)<<51) | (uint64_t(s&0x1F)<<46) | (uint64_t(cond&0x3)<<44) | (resv & 0xFFFFFFFFFFF);
}

inline uint64_t pack_B(uint8_t op, int64_t offset=0, uint8_t flags=0) {
    return (uint64_t(op)<<56) | (uint64_t(flags&0x1F)<<51) | (uint64_t(offset) & 0x7FFFFFFFFFFFF);
}

inline uint64_t pack_X(uint8_t op, uint64_t resv=0) {
    return (uint64_t(op)<<56) | (resv & 0xFFFFFFFFFFFFFF);
}

// Decode: returns (opcode, dest/offset, srcA/flags, srcB/cond)
struct DecodedInst {
    uint8_t opcode;
    uint8_t dest;
    uint8_t srcA;
    uint8_t srcB;
    int16_t offset;
    uint64_t imm;
    uint8_t cond;
    uint8_t flags;
};

inline DecodedInst decode(uint64_t w) {
    DecodedInst d;
    d.opcode = field_u8(w, 63, 56);
    d.dest   = field_u8(w, 55, 51);
    d.srcA   = field_u8(w, 50, 46);
    d.srcB   = field_u8(w, 45, 41);
    d.offset = field_s10(w, 45, 36);
    d.imm    = w & 0x7FFFFFFFFFFFF;
    d.cond   = field_u8(w, 45, 44);
    d.flags  = field_u8(w, 55, 51);
    return d;
}

inline const char* opcode_name(uint8_t op) {
    switch (op) {
        case OP_NOP: return "NOP"; case OP_HALT: return "HALT"; case OP_SYNC: return "SYNC";
        case OP_LOAD: return "LOAD"; case OP_STORE: return "STORE"; case OP_MOV: return "MOV";
        case OP_MOVI: return "MOVI"; case OP_LDO: return "LDO"; case OP_LDC: return "LDC";
        case OP_QADD: return "QADD"; case OP_QSUB: return "QSUB"; case OP_QMUL: return "QMUL";
        case OP_QDIV: return "QDIV"; case OP_QNORM: return "QNORM"; case OP_QCMP: return "QCMP";
        case OP_SPRD: return "SPRD"; case OP_ROTR: return "ROTR"; case OP_CROSS: return "CROSS";
        case OP_DOT: return "DOT"; case OP_TNSR: return "TNSR"; case OP_PROJ: return "PROJ";
        case OP_OFFR: return "OFFR"; case OP_CNFM: return "CNFM"; case OP_PHSLK: return "PHSLK";
        case OP_INVJ: return "INVJ"; case OP_PHSTA: return "PHSTA"; case OP_PHCLR: return "PHCLR";
        case OP_RCFG: return "RCFG"; case OP_RREAD: return "RREAD"; case OP_RLOAD: return "RLOAD";
        case OP_RDISSOC: return "RDISSOC";
        case OP_CMP: return "CMP"; case OP_JMP: return "JMP"; case OP_JZ: return "JZ";
        case OP_JNZ: return "JNZ"; case OP_JC: return "JC"; case OP_JNC: return "JNC";
        case OP_CALL: return "CALL"; case OP_RET: return "RET";
        case OP_MFOLD: return "MFOLD"; case OP_STAT: return "STAT"; case OP_SCALE: return "SCALE";
        case OP_QR: return "QR"; case OP_HEX: return "HEX"; case OP_SENT: return "SENT";
        default: return "???";
    }
}


// ═════════════════════════════════════════════════════════════════════════════
// RPLU Material Table
// ═════════════════════════════════════════════════════════════════════════════

struct RPLUTable {
    // params: (a_q16, re_q16, De_q16) per material[0..7]
    struct Params { int32_t a, re, de; };
    Params params[8] = {
        {0x00010000, 0x00080000, 0x00000200},  // 0=carbon
        {0x00008000, 0x00060000, 0x00000300},  // 1=iron
        {0x00010000, 0x00070000, 0x00000250},  // 2=aluminum
        {0x00009000, 0x00050000, 0x00000350},  // 3=silicon
        {0x0000A000, 0x00065000, 0x00000280},  // 4=titanium
        {0x00008000, 0x00055000, 0x00000320},  // 5=nickel
        {0x0000C000, 0x00060000, 0x00000200},  // 6=copper
        {0x0000D000, 0x00070000, 0x00000400},  // 7=tungsten
    };
    // vnorm: 1024 entries per material
    int32_t vnorm[8][1024];
    // dissoc: 1024 entries per material
    uint8_t dissoc[8][1024];

    RPLUTable() {
        for (int m = 0; m < 8; m++) {
            for (int i = 0; i < 1024; i++) {
                vnorm[m][i] = 0x00010000;
                dissoc[m][i] = (i < 100) ? 1 : 0;
            }
        }
    }

    Params read_params(int material, int addr) {
        return params[material & 7];
    }

    int32_t read_vnorm(int material, int addr) {
        return vnorm[material & 7][addr & 0x3FF];
    }

    uint8_t read_dissoc(int material, int addr) {
        return dissoc[material & 7][addr & 0x3FF];
    }

    // RATIO_CMP: cross-multiplication comparison
    int ratio_cmp(int64_t acc_num, int64_t acc_den, int64_t p2, int64_t q2) {
        int64_t left = acc_num * q2;
        int64_t right = acc_den * p2;
        if (left < right) return -1;
        if (left > right) return 1;
        return 0;
    }
};


// ═════════════════════════════════════════════════════════════════════════════
// SPU-13 Core Simulator
// ═════════════════════════════════════════════════════════════════════════════

struct SPU13Core {
    TwinReg R[32];          // Twin-register file
    uint64_t FLAGS;          // Flags register
    uint64_t PC;             // Program counter
    int MANIFOLD_PTR;        // Manifold read pointer
    int SCALE_PTR;           // Scale table index
    Quadray CHORD_IN;        // Incoming chord
    Quadray CHORD_OUT;       // Outgoing chord
    Rational QUAD_OUT;       // Quadrance output

    std::vector<uint64_t> program;
    std::vector<uint64_t> call_stack;
    bool halted;
    int steps;
    int max_steps;
    bool verbose;
    bool trace;

    RPLUTable rplu;

    // Telemetry
    struct {
        bool manifold_valid;
        uint8_t manifold_bytes[32];
        uint16_t dissonance;
        uint8_t flags;
    } telemetry;

    SPU13Core(bool v=false, bool t=false)
        : FLAGS(0), PC(0), MANIFOLD_PTR(0), SCALE_PTR(0),
          QUAD_OUT(0,1), halted(false), steps(0), max_steps(10000),
          verbose(v), trace(t) {
        // Init all registers to zero
        for (int i = 0; i < 32; i++) {
            R[i].O = Quadray(0,0,0,0);
            R[i].C = Quadray(0,0,0,0);
        }
        memset(&telemetry, 0, sizeof(telemetry));
    }

    void flag_set(int bit, bool val=true) {
        if (val) FLAGS |= (1ull << bit);
        else FLAGS &= ~(1ull << bit);
    }
    bool flag_test(int bit) const {
        return (FLAGS >> bit) & 1;
    }

    Quadray int_to_quad(uint64_t val) {
        return Quadray(int32_t(val), 0, 0, 0);
    }

    void load(const std::vector<uint64_t>& prog) {
        program = prog;
        PC = 0;
        halted = false;
        steps = 0;
        call_stack.clear();
        FLAGS = 0;
        if (verbose) printf("  SPU-13: %zu instructions loaded.\n", prog.size());
    }

    bool step() {
        if (halted || PC >= program.size()) {
            halted = true;
            return false;
        }

        steps++;
        if (steps > max_steps) { halted = true; return false; }

        uint64_t word = program[PC];
        auto d = decode(word);
        uint64_t next_pc = PC + 1;

        if (trace) {
            printf("[%04llu] %-8s R%d R%d R%d",
                   (unsigned long long)PC, opcode_name(d.opcode),
                   d.dest, d.srcA, d.srcB);
        }

        switch (d.opcode) {
            case OP_NOP: break;

            case OP_HALT:
                halted = true;
                if (verbose) printf("\n  HALT");
                break;

            case OP_LOAD: {
                int32_t val = d.offset;
                R[d.dest].O = int_to_quad(uint64_t(val & 0x3FF));
                break;
            }

            case OP_MOV:
                R[d.dest].O = R[d.srcA].O;
                break;

            case OP_MOVI:
                R[d.dest].O = int_to_quad(d.imm);
                break;

            case OP_LDO:
                R[d.dest].O = int_to_quad(uint64_t(d.offset & 0x3FF));
                break;

            case OP_LDC:
                R[d.dest].C = int_to_quad(uint64_t(d.offset & 0x3FF));
                break;

            // ── Temporal ops ──

            case OP_OFFR: {
                int material = d.srcA & 0xF;
                int addr = d.srcB;
                auto p = rplu.read_params(material, addr);
                R[d.dest].O = Quadray(p.a, p.re, p.de, 0);
                if (trace) printf("  OFFR mat=%d[%d]", material, addr);
                break;
            }

            case OP_CNFM: {
                int material = d.srcA & 0xF;
                int addr = d.srcB;
                auto p = rplu.read_params(material, addr);
                R[d.dest].C = Quadray(p.a, p.re, p.de, 0);
                if (trace) printf("  CNFM mat=%d[%d]", material, addr);
                break;
            }

            case OP_PHSLK: {
                int64_t q_offer = R[d.srcA].O.quadrance();
                int64_t q_confirm = R[d.srcB].C.quadrance();
                bool coherent = (q_offer == q_confirm);
                if (coherent) {
                    auto o = R[d.srcA].O;
                    auto c = R[d.srcB].C;
                    R[d.dest].O = Quadray(o.a + c.a, o.b + c.b, o.c + c.c, o.d + c.d);
                    flag_set(FLAG_COHERENT, true);
                    if (trace) printf("  PHSLK ✅ LOCK");
                } else {
                    flag_set(FLAG_COHERENT, false);
                    if (trace) printf("  PHSLK ❌ no lock (%lld vs %lld)",
                                      (long long)q_offer, (long long)q_confirm);
                }
                break;
            }

            case OP_INVJ:
                R[d.dest].O = -R[d.srcA].O;
                if (trace) printf("  INVJ ✓");
                break;

            case OP_PHSTA:
                R[d.dest].O = int_to_quad(flag_test(FLAG_COHERENT) ? 1 : 0);
                break;

            case OP_PHCLR:
                flag_set(FLAG_COHERENT, false);
                break;

            // ── Quadrance arithmetic ──

            case OP_QADD: {
                int64_t qa = R[d.srcA].O.quadrance();
                int64_t qb = R[d.srcB].O.quadrance();
                QUAD_OUT = Rational(qa + qb, 1);
                R[d.dest].O = int_to_quad(uint64_t(QUAD_OUT.to_q12()));
                break;
            }

            case OP_QMUL: {
                int64_t qa = R[d.srcA].O.quadrance();
                int64_t qb = R[d.srcB].O.quadrance();
                QUAD_OUT = Rational(qa * qb, 1);
                R[d.dest].O = int_to_quad(uint64_t(QUAD_OUT.to_q12()));
                break;
            }

            case OP_QCMP: {
                int64_t qa = R[d.srcA].O.quadrance();
                int64_t qb = R[d.srcB].O.quadrance();
                flag_set(FLAG_ZERO, qa == qb);
                flag_set(FLAG_COHERENT, qa >= qb);
                break;
            }

            case OP_QNORM:
                R[d.dest].O = R[d.srcA].O;
                break;

            // ── Geometric ops ──

            case OP_SPRD: {
                int64_t q1 = R[d.srcA].O.quadrance();
                int64_t q2 = R[d.srcB].O.quadrance();
                int64_t qmin = (q1 < q2) ? q1 : q2;
                R[d.dest].O = int_to_quad(uint64_t(qmin));
                break;
            }

            case OP_ROTR:
                R[d.dest].O = R[d.srcB].O;
                break;

            case OP_CROSS:
                R[d.dest].O = R[d.srcA].O.cross(R[d.srcB].O);
                break;

            case OP_DOT: {
                auto& a = R[d.srcA].O;
                auto& b = R[d.srcB].O;
                int64_t dot = int64_t(a.a)*b.a + int64_t(a.b)*b.b +
                              int64_t(a.c)*b.c + int64_t(a.d)*b.d;
                R[d.dest].O = int_to_quad(uint64_t(dot));
                break;
            }

            case OP_TNSR:
                R[d.dest].O = R[d.srcA].O.tensor_M();
                break;

            // ── Flow control ──

            case OP_JMP:
                next_pc = PC + field_s51(word, 50, 0);
                break;

            case OP_JZ:
                if (flag_test(FLAG_ZERO)) next_pc = PC + field_s51(word, 50, 0);
                break;

            case OP_JNZ:
                if (!flag_test(FLAG_ZERO)) next_pc = PC + field_s51(word, 50, 0);
                break;

            case OP_JC:
                if (flag_test(FLAG_COHERENT)) next_pc = PC + field_s51(word, 50, 0);
                break;

            case OP_JNC:
                if (!flag_test(FLAG_COHERENT)) next_pc = PC + field_s51(word, 50, 0);
                break;

            case OP_CALL:
                call_stack.push_back(PC + 1);
                next_pc = PC + field_s51(word, 50, 0);
                break;

            case OP_RET:
                if (!call_stack.empty()) {
                    next_pc = call_stack.back();
                    call_stack.pop_back();
                }
                break;

            // ── Telemetry ──

            case OP_MFOLD:
                telemetry.manifold_valid = true;
                memset(telemetry.manifold_bytes, 'M', 32);
                if (trace) printf("  MFOLD → 32B");
                break;

            case OP_STAT:
                telemetry.dissonance = uint16_t(FLAGS & 0xFFFF);
                telemetry.flags = uint8_t((FLAGS >> 16) & 0xFF);
                if (trace) printf("  STAT → flags=0x%02llX", (unsigned long long)FLAGS);
                break;

            case OP_HEX:
                if (trace) printf("  HEX");
                break;

            default:
                if (verbose) printf("\n  WARN: unimplemented opcode 0x%02X", d.opcode);
                break;
        }

        PC = next_pc;
        return true;
    }

    void run() {
        while (!halted) {
            if (PC >= program.size()) { halted = true; break; }
            step();
        }
        if (verbose) {
            printf("\n  Done: %d steps, FLAGS=0x%04llX\n",
                   steps, (unsigned long long)FLAGS);
        }
    }
};
