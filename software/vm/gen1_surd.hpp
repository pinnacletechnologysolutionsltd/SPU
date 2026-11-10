// gen1_surd.hpp — architectural model of the frozen Gen-1 Surd CPU (SPU-GEN1-SIM-IMPL-0).
// Authority: docs/GEN1_ARCHITECTURAL_CONTRACT.md (dev/next 5948d8d5). Architecture-level, not
// cycle-accurate. Only the four contract §5 patterns execute; every other word faults at fetch.
#ifndef SPU_GEN1_SURD_HPP
#define SPU_GEN1_SURD_HPP
#include "gen1_wide.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace gen1 {

enum Status { OK = 0, INVALID = 1, OVERFLOW = 2 };   // ENGINE_FAULT (3) unreachable in exact arithmetic

struct Tuple { uint64_t a, b, d; };                  // a, b: two's-complement bits; d unsigned

struct Run {                                         // architectural result + diagnostics
    bool fault = false;
    int pc = 0;
    uint8_t mask = 0;
    std::array<uint32_t, 6> result{};
    std::vector<std::array<int, 2>> retires;         // diagnostic: (pc, status)
    std::string cause;                               // diagnostic: "", fetch_reject, retire_status
    bool s0_init = false;                            // diagnostic
    Tuple s0{0, 0, 1};                               // diagnostic (reset value, contract §6)
    std::array<uint8_t, 33> frame{};                 // architectural: the only hardware-visible output
};

// Contract §5 / cpu_fetch_1b.v:26-28.
inline bool accepted(uint64_t w) {
    unsigned op = unsigned(w >> 56), r1 = unsigned((w >> 48) & 0xff), r2 = unsigned((w >> 40) & 0xff);
    if (op == 0x70) return r1 == 0 && r2 < 6 && (w & 0xff) == 0;
    if (op == 0x72) return r1 == 0 && r2 < 6 && (w & ((1ULL << 40) - 1)) == 0;
    return w == 0x7100000000000000ULL || w == 0x7300000000000000ULL;
}

inline uint32_t slice_of(const Tuple& t, unsigned s) {
    uint64_t v = s < 2 ? t.a : s < 4 ? t.b : t.d;
    return uint32_t(s % 2 ? v >> 32 : v & 0xffffffffULL);
}

// Contract §7.3: raw product; commit raw if it fits, else normalize by gcd; else OVERFLOW.
inline Status smul(const Tuple& x, const Tuple& y, Tuple& out) {
    S192 a = from_i64_bits(x.a), b = from_i64_bits(x.b), c = from_i64_bits(y.a), e = from_i64_bits(y.b);
    S192 be = smul(b, e);
    S192 A = sadd(smul(a, c), S192{be.neg, add(add(be.mag, be.mag), be.mag)});
    S192 B = sadd(smul(a, e), smul(b, c));
    U192 D = mul64(x.d, y.d);
    if (!(fits_s64(A) && fits_s64(B) && fits_u64_nonzero(D))) {
        if (is_zero(A.mag) && is_zero(B.mag)) { A = S192{false, u192(0)}; B = A; D = u192(1); }
        else {
            U192 g = gcd(gcd(A.mag, B.mag), D), q, r;
            divmod(A.mag, g, q, r); A.mag = q;
            divmod(B.mag, g, q, r); B.mag = q;
            divmod(D, g, q, r); D = q;
        }
        if (!(fits_s64(A) && fits_s64(B) && fits_u64_nonzero(D))) return OVERFLOW;
    }
    out = Tuple{to_i64_bits(A), to_i64_bits(B), D.w[0]};
    return OK;
}

inline uint32_t crc32(const uint8_t* p, size_t n) {   // ISO-HDLC, as board_top.v:19-21
    uint32_t c = 0xffffffffu;
    for (size_t i = 0; i < n; ++i) {
        c ^= p[i];
        for (int k = 0; k < 8; ++k) c = (c & 1u) ? (c >> 1) ^ 0xedb88320u : (c >> 1);
    }
    return ~c;
}

inline void build_frame(Run& r) {                     // contract §9 / board_top.v:24-32
    r.frame = {0xA5, 0x01, uint8_t(r.fault ? 0x02 : 0x01), uint8_t(r.mask & 0x3f), uint8_t(r.pc & 0x0f)};
    for (int s = 0; s < 6; ++s) {
        uint32_t v = (r.mask >> s) & 1u ? r.result[s] : 0u;
        for (int k = 0; k < 4; ++k) r.frame[5 + 4 * s + k] = uint8_t(v >> (8 * k));
    }
    uint32_t c = crc32(r.frame.data(), 29);
    for (int k = 0; k < 4; ++k) r.frame[29 + k] = uint8_t(c >> (8 * k));
}

// Contract §3-§8: reset, then words 0..13 in order; HALT at PC 14; FAULT is terminal.
inline Run execute(const std::array<uint64_t, 16>& rom) {
    Run r;
    std::array<uint32_t, 6> staging{};
    uint8_t received = 0;
    for (int pc = 0; pc < 14; ++pc) {
        r.pc = pc;
        uint64_t w = rom[pc];
        if (!accepted(w)) { r.fault = true; r.cause = "fetch_reject"; build_frame(r); return r; }
        unsigned op = unsigned(w >> 56), s = unsigned((w >> 40) & 0xff);
        Status st = OK;
        if (op == 0x70) { staging[s] = uint32_t((w >> 8) & 0xffffffffULL); received |= uint8_t(1u << s); }
        else if (op == 0x71) {
            uint64_t d = uint64_t(staging[4]) | (uint64_t(staging[5]) << 32);
            if (received == 0x3f && d != 0) {
                r.s0 = Tuple{uint64_t(staging[0]) | (uint64_t(staging[1]) << 32),
                             uint64_t(staging[2]) | (uint64_t(staging[3]) << 32), d};
                r.s0_init = true;
            } else st = INVALID;
            staging = {}; received = 0;               // cleared on every SLD (spu13_surd_load.v:17)
        } else if (op == 0x73) {
            Tuple out{};
            st = r.s0_init ? smul(r.s0, r.s0, out) : INVALID;
            if (st == OK) r.s0 = out;                 // refusal preserves S0
        } else {                                      // 0x72 SRD
            if (!r.s0_init) st = INVALID;
            else { r.result[s] = slice_of(r.s0, s); r.mask |= uint8_t(1u << s); }
        }
        r.retires.push_back({pc, int(st)});
        if (st != OK) { r.fault = true; r.cause = "retire_status"; build_frame(r); return r; }
    }
    r.pc = 14;
    build_frame(r);
    return r;
}

}  // namespace gen1
#endif
