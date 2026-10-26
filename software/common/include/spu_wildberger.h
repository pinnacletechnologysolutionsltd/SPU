// spu_wildberger.h — Layer 8: Wildberger Rational Geometry Laws
//
// Implements core laws from N.J. Wildberger's Universal Geometry,
// adapted for the SPU-13 Q(√3) arithmetic field:
//
//   1. Triple Quad Formula — collinearity check (degenerate triangle)
//      (Q1+Q2+Q3)² = 2(Q1²+Q2²+Q3²)
//      True iff three points are collinear (zero-area triangle).
//      No product term. Used as a zero-epsilon occlusion gate.
//
//   2. Triple Quad Tangency — mutually tangent circles (Descartes variant)
//      (Q1+Q2+Q3)² = 2(Q1²+Q2²+Q3²) + 4·Q1·Q2·Q3
//      DISTINCT from the collinearity formula. Used for tangent-sphere tests.
//
//   3. Spread Law — rational refraction (replaces Snell's Law)
//      Q1/s1 = Q2/s2 = Q3/s3
//      Relates the Quadrances and Spreads of a rational triangle.
//      No sine, no arcsin, no transcendental approximation.
//
//   4. Rational Fresnel — reflection/refraction ratio
//      Replaces the classical Fresnel equations (which require cos θ) with
//      pure Spread arithmetic: R = (s_in - s_out)² / (s_in + s_out)²
//
// All inputs and outputs are exact in Q(√3).  No division.  No sqrt.
// Equality tests use cross-multiplication to avoid rational division:
//   a/b == c/d  ↔  a·d == b·c   (exact integer identity)
//
// Hardware correspondence:
//   triple_quad_check()  → TRIPLE_QUAD opcode → davis_gate collinearity path
//   spread_law_ratio()   → SPREAD_LAW opcode  → spu_spread_mul.v DSP path
//   rational_fresnel()   → FRESNEL opcode     → spu_fragment_pipe.v
//
// Layer dependencies: spu_surd.h → spu_quadray.h
//
// References:
//   Wildberger, N.J. "Divine Proportions: Rational Trigonometry to
//     Universal Geometry." Wild Egg, 2005.
//     §3.3 Triple Quad Formula, §5.2 Spread Law, §8 Conics.
//
// CC0 1.0 Universal.

#pragma once
#include "spu_quadray.h"

// ── 1. Triple Quad Formula — Collinearity ────────────────────────────────────
//
// Three points A, B, C with pairwise Quadrances Q1=Q(A,B), Q2=Q(B,C), Q3=Q(A,C)
// are COLLINEAR if and only if:
//   (Q1 + Q2 + Q3)² = 2·(Q1² + Q2² + Q3²)
//
// This is the degenerate-triangle condition: the "area" of the triangle is zero.
// Derivation: collinearity means √Q1 + √Q2 = √Q3 (or a permutation). Squaring
// twice and eliminating the square roots yields the pure-algebraic identity above.
//
// No product term Q1·Q2·Q3 appears here. That term belongs to the
// tangent-circles formula (triple_quad_tangent, below).
//
// Typical usage: shadow / occlusion gate. Q(eye,edge), Q(edge,light), Q(eye,light)
// satisfying this identity means the edge perfectly lies on the line eye→light.
//
// All arithmetic in Q(√3). No float. No epsilon. No sqrt.

inline bool triple_quad_check(const RationalSurd& Q1,
                               const RationalSurd& Q2,
                               const RationalSurd& Q3)
{
    RationalSurd sum    = Q1 + Q2 + Q3;
    RationalSurd lhs    = sum * sum;
    RationalSurd sum_sq = Q1*Q1 + Q2*Q2 + Q3*Q3;
    RationalSurd rhs    = RationalSurd{2,0} * sum_sq;
    return lhs == rhs;
}

// ── Triple Quad Tangency (Descartes / tangent circles) ────────────────────────
//
// Three circles with Quadrances Q1, Q2, Q3 (squared radii) are mutually tangent
// if and only if:
//   (Q1 + Q2 + Q3)² = 2·(Q1² + Q2² + Q3²) + 4·Q1·Q2·Q3
//
// This is a DISTINCT law from the collinearity check above.
// Applications: tangent-sphere intersection tests in the SDF layer.

inline bool triple_quad_tangent(const RationalSurd& Q1,
                                 const RationalSurd& Q2,
                                 const RationalSurd& Q3)
{
    RationalSurd sum    = Q1 + Q2 + Q3;
    RationalSurd lhs    = sum * sum;
    RationalSurd sum_sq = Q1*Q1 + Q2*Q2 + Q3*Q3;
    RationalSurd prod   = Q1 * Q2 * Q3;
    RationalSurd rhs    = RationalSurd{2,0} * sum_sq + RationalSurd{4,0} * prod;
    return lhs == rhs;
}

// Convenience: compute the three Quadrances from three Quadray points A, B, C
// and run the Triple Quad check.
//   Q1 = Q(A, B), Q2 = Q(B, C), Q3 = Q(A, C)
// Collinear means the "middle" point B lies between A and C on the same line.
inline bool triple_quad_collinear(const Quadray& A,
                                   const Quadray& B,
                                   const Quadray& C)
{
    RationalSurd Q1 = (A - B).quadrance();
    RationalSurd Q2 = (B - C).quadrance();
    RationalSurd Q3 = (A - C).quadrance();
    return triple_quad_check(Q1, Q2, Q3);
}

// ── 2. Spread Law ─────────────────────────────────────────────────────────────
//
// The Spread Law for a triangle with sides Q1, Q2, Q3 (Quadrances) and
// opposite spreads s1, s2, s3:
//   Q1/s1 = Q2/s2 = Q3/s3
//
// This is the rational counterpart of the Sine Rule: a/sin A = b/sin B = c/sin C
// with the key difference that no transcendental function is needed.
//
// SPU-13 application: rational refraction / Snell's Law replacement.
//   Given:  Q_in  — incoming ray quadrance
//           s_in  — spread at the surface for incoming ray (rational)
//           s_out — spread at the surface for outgoing ray (rational)
//   Solve for Q_out = Q_in · s_out / s_in  using cross-multiply (no division).
//
// Because we avoid division, the result is returned as a (numerator, denom)
// pair so the caller can choose to reduce or compare without ever dividing.

struct SpreadRatio {
    RationalSurd numer;   // Q_in  * s_out
    RationalSurd denom;   // s_in  (multiply this into downstream expressions)

    // Equality check without division: a/b == c/d ↔ a·d == b·c
    bool equals(const SpreadRatio& o) const {
        return (numer * o.denom) == (o.numer * denom);
    }

    // Check if ratio equals a simple integer n/1
    bool equals_int(int32_t n) const {
        return numer == denom * RationalSurd{n, 0};
    }
};

// Given incoming Quadrance Q_in and the two Spreads, compute the outgoing
// Quadrance as Q_in · s_out / s_in  (returned in ratio form).
inline SpreadRatio spread_law_refract(const RationalSurd& Q_in,
                                       const RationalSurd& s_in,
                                       const RationalSurd& s_out)
{
    // Q_out / 1 = Q_in · (s_out / s_in)
    // Ratio form: numer = Q_in * s_out,  denom = s_in
    return { Q_in * s_out, s_in };
}

// Verify that three (Q, s) pairs satisfy the Spread Law:
//   Q1·s2 == Q2·s1  and  Q2·s3 == Q3·s2
// (cross-multiplication avoids division completely)
inline bool spread_law_check(const RationalSurd& Q1, const RationalSurd& s1,
                               const RationalSurd& Q2, const RationalSurd& s2,
                               const RationalSurd& Q3, const RationalSurd& s3)
{
    return (Q1 * s2 == Q2 * s1) && (Q2 * s3 == Q3 * s2);
}

// ── 3. Rational Fresnel ───────────────────────────────────────────────────────
//
// Classical Fresnel equations use cos(θ) — transcendental, irrational.
// Rational Fresnel replaces θ with Spread s = sin²(θ) and uses the identity:
//   Reflectance R_s = (s_i - s_t)² / (s_i + s_t)²
//                   = (n_i·s_t - n_t·s_i)² / (n_i·s_t + n_t·s_i)²
//
// In the SPU-13 (no division):
//   R_numer = (s_in - s_out)²
//   R_denom = (s_in + s_out)²
//   T_numer = 4 · s_in · s_out              (= R_denom - R_numer)
//   T_denom = (s_in + s_out)²
//
//   Verify energy conservation: R_numer + T_numer == R_denom  (exact identity)
//
// Returns the (reflectance, transmittance) ratio pair. No float. No sqrt.

struct FresnelRatio {
    RationalSurd R_numer;  // reflected energy numerator
    RationalSurd T_numer;  // transmitted energy numerator
    RationalSurd denom;    // shared denominator = (s_in + s_out)²

    // Energy conservation: R + T == denom (exact identity)
    bool conserved() const {
        return (R_numer + T_numer) == denom;
    }
};

inline FresnelRatio rational_fresnel(const RationalSurd& s_in,
                                      const RationalSurd& s_out)
{
    RationalSurd diff   = s_in - s_out;
    RationalSurd sum_s  = s_in + s_out;
    RationalSurd R_num  = diff  * diff;          // (s_in - s_out)²
    RationalSurd denom  = sum_s * sum_s;          // (s_in + s_out)²
    RationalSurd T_num  = RationalSurd{4,0} * s_in * s_out;  // 4·s_in·s_out
    return { R_num, T_num, denom };
}

// ── IVM convenience: canonical Spread constants ───────────────────────────────
//
// In the 60° IVM lattice, adjacent tetrahedral axes subtend a spread of 3/4.
// These are rational constants — not approximations.
//
// Spread  0   → s = 0      collinear (0°)
// Spread 3/4  → s = 3/4   — 60° tetrahedral edge (IVM standard)
// Spread  1   → s = 1     — right angle (90°)
//
// For triple_spread_law_check pass numerators with common denom d=4:
//   s = 3/4 → s_n=3, d=4
//   s = 1/4 → s_n=1, d=4
//   s = 1   → s_n=4, d=4

constexpr RationalSurd WB_S_ZERO        = {0, 0};
constexpr RationalSurd WB_S_TETRAHEDRAL = {3, 0};   // numerator for 3/4 spread; use denom d=4
constexpr RationalSurd WB_S_DENOM_60    = {4, 0};   // common denominator for 60° IVM spreads
constexpr RationalSurd WB_S_RIGHT       = {1, 0};   // spread = 1 (90°); or numerator 4 with d=4

// ── 4. Triple Spread Law ──────────────────────────────────────────────────────
//
// The Triple Spread Law is the Spread counterpart of the Triple Quad Formula.
// For three angles (spreads) s1, s2, s3 consistent with a rational triangle:
//   (s1 + s2 + s3)² = 2(s1² + s2² + s3²) + 4·s1·s2·s3
//
// Because the SPU-13 avoids division, spreads are represented as integer
// NUMERATORS s1_n, s2_n, s3_n over a common denominator d:  si = si_n / d.
//
// Substituting and clearing d³:
//   d · (s1_n + s2_n + s3_n)²  =  2d · (s1_n² + s2_n² + s3_n²) + 4 · s1_n · s2_n · s3_n
//
// This is exact, integer-only, and division-free. The d cancels asymmetrically
// because the product term is cubic while the squared terms are quadratic.
//
// Physical meaning (Fresnel / optical link):
//   s1 = spread of incident ray to surface normal
//   s2 = spread of reflected ray to surface normal  (= s1 by reflection law)
//   s3 = spread of transmitted (refracted) ray to surface normal
//
// IVM examples (common denominator d=4):
//   Equilateral 60°:         s1=s2=s3=3  (3/4 each)        → holds ✓
//   Degenerate (flat edge):  s1=3, s2=3, s3=0               → holds ✓
//   Optical glass-air:       s1=3, s2=1, s3=4  (3/4,1/4,1) → holds ✓
//
// Hardware: TRIPLE_SPREAD opcode → spu_fragment_pipe.v Fresnel gate.
// Reference: Wildberger, Divine Proportions §8.3 "Triple Spread Formula".

inline bool triple_spread_law_check(const RationalSurd& s1_n,
                                     const RationalSurd& s2_n,
                                     const RationalSurd& s3_n,
                                     const RationalSurd& d)
{
    RationalSurd sum    = s1_n + s2_n + s3_n;
    RationalSurd lhs    = d * sum * sum;
    RationalSurd sum_sq = s1_n*s1_n + s2_n*s2_n + s3_n*s3_n;
    RationalSurd prod   = s1_n * s2_n * s3_n;
    RationalSurd rhs    = RationalSurd{2,0} * d * sum_sq + RationalSurd{4,0} * prod;
    return lhs == rhs;
}

// Convenience: unit denominator (d=1). Spreads are integers / Q(√3) values.
// Holds for degenerate cases like (s, s, 0).
inline bool triple_spread_law_check_unit(const RationalSurd& s1,
                                          const RationalSurd& s2,
                                          const RationalSurd& s3)
{
    return triple_spread_law_check(s1, s2, s3, RationalSurd{1,0});
}
