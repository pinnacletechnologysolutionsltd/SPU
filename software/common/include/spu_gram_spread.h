// gram_v1 SPREAD: exact Gram-consistent spread with final-only int32 range checks.
// research/sim_cap1_spread/GRAM_V1_CONTRACT.md. B(v,w) = 4*sum(v_i w_i) - (sum v_i)(sum w_i).
//   N = B(v,v)B(w,w) - B(v,w)^2,  D = B(v,v)B(w,w)   (unreduced, in Q(sqrt3))
// For int32 lanes every intermediate is < 2^148 in magnitude, so signed 256-bit two's
// complement (add, sub, truncating mul, compare) is exact. No intermediate is ever refused.
#pragma once
#include <cstdint>

namespace gram {

struct I256 {
    uint64_t w[4];  // little-endian two's complement
    static I256 from_i64(int64_t v) {
        I256 r; r.w[0] = (uint64_t)v;
        uint64_t ext = v < 0 ? ~0ull : 0ull;
        r.w[1] = r.w[2] = r.w[3] = ext;
        return r;
    }
    bool neg() const { return (w[3] >> 63) != 0; }
    bool zero() const { return !(w[0] | w[1] | w[2] | w[3]); }
};
inline I256 add(const I256& a, const I256& b) {
    I256 r; unsigned __int128 c = 0;
    for (int i = 0; i < 4; i++) { c += (unsigned __int128)a.w[i] + b.w[i]; r.w[i] = (uint64_t)c; c >>= 64; }
    return r;
}
inline I256 negate(const I256& a) {
    I256 n, one = I256::from_i64(1);
    for (int i = 0; i < 4; i++) n.w[i] = ~a.w[i];
    return add(n, one);
}
inline I256 sub(const I256& a, const I256& b) { return add(a, negate(b)); }
inline I256 mul(const I256& a, const I256& b) {  // low 256 bits; exact when the true product fits
    I256 r = {{0, 0, 0, 0}};
    for (int i = 0; i < 4; i++) {
        unsigned __int128 carry = 0;
        for (int j = 0; i + j < 4; j++) {
            carry += (unsigned __int128)a.w[i] * b.w[j] + r.w[i + j];
            r.w[i + j] = (uint64_t)carry; carry >>= 64;
        }
    }
    return r;
}
// True iff the value lies in [INT32_MIN, INT32_MAX]; stores it in out.
inline bool to_i32(const I256& a, int32_t& out) {
    uint64_t ext = a.neg() ? ~0ull : 0ull;
    if (a.w[1] != ext || a.w[2] != ext || a.w[3] != ext) return false;
    int64_t v = (int64_t)a.w[0];
    if ((v < 0) != a.neg() || v < INT32_MIN || v > INT32_MAX) return false;
    out = (int32_t)v;
    return true;
}

struct Surd { I256 p, q; };
inline Surd sadd(const Surd& a, const Surd& b) { return {add(a.p, b.p), add(a.q, b.q)}; }
inline Surd ssub(const Surd& a, const Surd& b) { return {sub(a.p, b.p), sub(a.q, b.q)}; }
inline Surd smul(const Surd& a, const Surd& b) {  // (p1+q1 s)(p2+q2 s), s^2 = 3
    I256 three = I256::from_i64(3);
    return {add(mul(a.p, b.p), mul(three, mul(a.q, b.q))), add(mul(a.p, b.q), mul(a.q, b.p))};
}
inline bool szero(const Surd& a) { return a.p.zero() && a.q.zero(); }

// v[i] = {p, q} lanes of the four Quadray components.
inline Surd bilinear(const int32_t v[4][2], const int32_t w[4][2]) {
    Surd dot = {I256::from_i64(0), I256::from_i64(0)}, sv = dot, sw = dot;
    for (int i = 0; i < 4; i++) {
        Surd x = {I256::from_i64(v[i][0]), I256::from_i64(v[i][1])};
        Surd y = {I256::from_i64(w[i][0]), I256::from_i64(w[i][1])};
        dot = sadd(dot, smul(x, y)); sv = sadd(sv, x); sw = sadd(sw, y);
    }
    Surd four = {I256::from_i64(4), I256::from_i64(0)};
    return ssub(smul(four, dot), smul(sv, sw));
}

// B values for proof output; |B coefficient| < 2^70 so each fits __int128 exactly.
inline bool to_i128(const I256& a, __int128& out) {
    uint64_t ext = a.neg() ? ~0ull : 0ull;
    if (a.w[2] != ext || a.w[3] != ext || ((a.w[1] >> 63) != 0) != a.neg()) return false;
    out = (__int128)(((unsigned __int128)a.w[1] << 64) | a.w[0]);
    return true;
}
struct Gram3 { __int128 vv[2], ww[2], vw[2]; };
inline Gram3 gram3(const int32_t v[4][2], const int32_t w[4][2]) {
    Surd s[3] = {bilinear(v, v), bilinear(w, w), bilinear(v, w)};
    Gram3 g = {};
    __int128* d[3] = {g.vv, g.ww, g.vw};
    for (int i = 0; i < 3; i++) { to_i128(s[i].p, d[i][0]); to_i128(s[i].q, d[i][1]); }
    return g;
}

enum class Status { Ok, Degenerate, Overflow };
struct Result { Status status; int32_t n[2], d[2]; };

inline Result spread(const int32_t v[4][2], const int32_t w[4][2]) {
    Result r = {Status::Ok, {0, 0}, {0, 0}};
    Surd bvv = bilinear(v, v), bww = bilinear(w, w), bvw = bilinear(v, w);
    if (szero(bvv) || szero(bww)) { r.status = Status::Degenerate; return r; }
    Surd den = smul(bvv, bww), num = ssub(den, smul(bvw, bvw));
    if (!to_i32(num.p, r.n[0]) || !to_i32(num.q, r.n[1]) ||
        !to_i32(den.p, r.d[0]) || !to_i32(den.q, r.d[1])) {
        r.status = Status::Overflow; r.n[0] = r.n[1] = r.d[0] = r.d[1] = 0;
    }
    return r;
}

}  // namespace gram
