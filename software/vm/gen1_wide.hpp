// gen1_wide.hpp — exact 192-bit arithmetic for the gen1-surd profile (SPU-GEN1-SIM-IMPL-0).
// Unsigned 64-bit limbs only: no signed overflow, no __int128, no narrowing UB.
// Signed values are sign + magnitude. Width 192 covers every Gen-1 SMUL intermediate:
// |a*c + 3*b*e| < 2^130 and d*f < 2^128 (contract §7.3).
#ifndef SPU_GEN1_WIDE_HPP
#define SPU_GEN1_WIDE_HPP
#include <cstdint>

namespace gen1 {

struct U192 { uint64_t w[3]; };            // little-endian limbs
struct S192 { bool neg; U192 mag; };       // neg is false for zero

inline U192 u192(uint64_t v) { return U192{{v, 0, 0}}; }
inline bool is_zero(const U192& x) { return (x.w[0] | x.w[1] | x.w[2]) == 0; }

inline int cmp(const U192& x, const U192& y) {
    for (int i = 2; i >= 0; --i)
        if (x.w[i] != y.w[i]) return x.w[i] < y.w[i] ? -1 : 1;
    return 0;
}

inline U192 add(const U192& x, const U192& y) {        // caller guarantees no 192-bit overflow
    U192 r{}; uint64_t carry = 0;
    for (int i = 0; i < 3; ++i) {
        uint64_t s = x.w[i] + y.w[i];
        uint64_t c1 = s < x.w[i];
        r.w[i] = s + carry;
        carry = c1 | (r.w[i] < s);
    }
    return r;
}

inline U192 sub(const U192& x, const U192& y) {        // requires x >= y
    U192 r{}; uint64_t borrow = 0;
    for (int i = 0; i < 3; ++i) {
        uint64_t d = x.w[i] - y.w[i];
        uint64_t b1 = x.w[i] < y.w[i];
        r.w[i] = d - borrow;
        borrow = b1 | (d < borrow);
    }
    return r;
}

inline U192 mul64(uint64_t x, uint64_t y) {            // full 64x64 -> 128 via 32-bit halves
    const uint64_t m = 0xffffffffULL;
    uint64_t xl = x & m, xh = x >> 32, yl = y & m, yh = y >> 32;
    uint64_t ll = xl * yl, lh = xl * yh, hl = xh * yl, hh = xh * yh;
    uint64_t mid = (ll >> 32) + (lh & m) + (hl & m);
    uint64_t lo = (ll & m) | (mid << 32);
    uint64_t hi = hh + (lh >> 32) + (hl >> 32) + (mid >> 32);
    return U192{{lo, hi, 0}};
}

inline U192 shl1(const U192& x) {
    return U192{{x.w[0] << 1, (x.w[1] << 1) | (x.w[0] >> 63), (x.w[2] << 1) | (x.w[1] >> 63)}};
}

// Exact restoring division: q = x / y, r = x % y (y != 0). Bit-serial, mirrors surd_exact_quotient.
inline void divmod(const U192& x, const U192& y, U192& q, U192& r) {
    q = U192{{0, 0, 0}}; r = U192{{0, 0, 0}};
    for (int bit = 191; bit >= 0; --bit) {
        r = shl1(r);
        r.w[0] |= (x.w[bit / 64] >> (bit % 64)) & 1ULL;
        if (cmp(r, y) >= 0) { r = sub(r, y); q.w[bit / 64] |= 1ULL << (bit % 64); }
    }
}

inline U192 gcd(U192 x, U192 y) {                       // Euclid; gcd(0, y) = y
    while (!is_zero(y)) { U192 q, r; divmod(x, y, q, r); x = y; y = r; }
    return x;
}

// Two's-complement 64-bit bits -> sign/magnitude (INT64_MIN handled without UB).
inline S192 from_i64_bits(uint64_t bits) {
    bool n = (bits >> 63) != 0;
    return S192{n, u192(n ? (~bits + 1) : bits)};
}

inline S192 smul(const S192& x, const S192& y) {        // operands have one-limb magnitudes
    U192 m = mul64(x.mag.w[0], y.mag.w[0]);
    return S192{!is_zero(m) && (x.neg != y.neg), m};
}

inline S192 sadd(const S192& x, const S192& y) {
    if (x.neg == y.neg) return S192{x.neg, add(x.mag, y.mag)};
    int c = cmp(x.mag, y.mag);
    if (c == 0) return S192{false, u192(0)};
    return c > 0 ? S192{x.neg, sub(x.mag, y.mag)} : S192{y.neg, sub(y.mag, x.mag)};
}

inline bool fits_s64(const S192& x) {                   // -2^63 <= x <= 2^63 - 1
    if (x.mag.w[1] | x.mag.w[2]) return false;
    return x.neg ? x.mag.w[0] <= (1ULL << 63) : x.mag.w[0] <= ((1ULL << 63) - 1);
}

inline bool fits_u64_nonzero(const U192& x) { return (x.w[1] | x.w[2]) == 0 && x.w[0] != 0; }

inline uint64_t to_i64_bits(const S192& x) {            // requires fits_s64(x)
    return x.neg ? (~x.mag.w[0] + 1) : x.mag.w[0];
}

}  // namespace gen1
#endif
