// psurd_arith.hpp — Q(sqrt3) arithmetic for the EXPERIMENTAL programmable-surd profile (SPU-V03-SIM-0).
// Specification: docs/design/SPU_V03_CONTRACT_CANDIDATE.md (image revision 0x03), §5 and §6.
// SMUL reuses the frozen Gen-1 model unchanged (identical rules). SADD/SSUB/SNORM/sign are new here.
#ifndef SPU_PSURD_ARITH_HPP
#define SPU_PSURD_ARITH_HPP
#include "gen1_surd.hpp"

namespace psurd {

using gen1::S192;
using gen1::Tuple;
using gen1::U192;

// Raw (A, B, D): commit raw if it fits, else divide by gcd(|A|,|B|,D) and commit if that fits,
// else OVERFLOW (out untouched). A = B = 0 normalizes to (0, 0, 1). Same rule as gen1::smul.
inline gen1::Status commit(S192 A, S192 B, U192 D, Tuple& out) {
    using namespace gen1;
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

inline S192 neg(S192 x) { if (!gen1::is_zero(x.mag)) x.neg = !x.neg; return x; }

// Draft §4: g = gcd(d, f), u = f/g, v = d/g; raw (a*u +- c*v, b*u +- e*v, d*u).
inline gen1::Status add_sub(const Tuple& x, const Tuple& y, bool subtract, Tuple& out) {
    using namespace gen1;
    U192 g = gcd(u192(x.d), u192(y.d)), u, v, r;
    divmod(u192(y.d), g, u, r);
    divmod(u192(x.d), g, v, r);
    S192 U{false, u}, V{false, v};
    S192 cv = smul(from_i64_bits(y.a), V), ev = smul(from_i64_bits(y.b), V);
    if (subtract) { cv = neg(cv); ev = neg(ev); }
    S192 A = sadd(smul(from_i64_bits(x.a), U), cv);
    S192 B = sadd(smul(from_i64_bits(x.b), U), ev);
    return commit(A, B, mul64(x.d, u.w[0]), out);
}

// SNORM: divide by gcd(|a|,|b|,d); zero becomes (0,0,1). Always fits for committed operands.
inline gen1::Status norm(const Tuple& x, Tuple& out) {
    using namespace gen1;
    S192 A = from_i64_bits(x.a), B = from_i64_bits(x.b);
    U192 D = u192(x.d);
    if (is_zero(A.mag) && is_zero(B.mag)) { out = Tuple{0, 0, 1}; return OK; }
    U192 g = gcd(gcd(A.mag, B.mag), D), q, r;
    divmod(A.mag, g, q, r); A.mag = q;
    divmod(B.mag, g, q, r); B.mag = q;
    divmod(D, g, q, r); D = q;
    return commit(A, B, D, out);
}

// Draft §5.1: sign of a + b*sqrt3 (d > 0). Opposite signs: compare a^2 with 3b^2 (< 2^128, exact).
inline int sign(const Tuple& x) {
    using namespace gen1;
    S192 a = from_i64_bits(x.a), b = from_i64_bits(x.b);
    bool az = is_zero(a.mag), bz = is_zero(b.mag);
    if (az && bz) return 0;
    if (bz || (!az && a.neg == b.neg)) return a.neg ? -1 : 1;
    if (az) return b.neg ? -1 : 1;
    U192 aa = mul64(a.mag.w[0], a.mag.w[0]), bb = mul64(b.mag.w[0], b.mag.w[0]);
    int c = cmp(aa, add(add(bb, bb), bb));   // a^2 != 3b^2 for nonzero integers (sqrt3 irrational)
    return (c > 0) ? (a.neg ? -1 : 1) : (b.neg ? -1 : 1);
}

}  // namespace psurd
#endif
