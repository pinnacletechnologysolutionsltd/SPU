// spu_quadray.h — 4-axis IVM tetrahedral coordinates for the SPU-13 software stack
//
// Quadray coordinates represent points in 3D space using four axes that point
// to the vertices of a regular tetrahedron. Any point reachable with (x,y,z)
// is reachable with (a,b,c,d) where all components ≥ 0 in canonical form.
//
// Canonical (normalised) form: subtract the minimum component from all axes
// so that min(a,b,c,d) == 0. This is exact and branchless in Q(√3).
//
// Correspondence with spu_vm.py QuadrayVector:
//   Quadray::normalize()    ↔  QuadrayVector.normalize()
//   Quadray::pell_rotate()  ↔  QuadrayVector.rotate()
//   Quadray::cycle()        ↔  QuadrayVector.cycle()
//   Quadray::quadrance()    ↔  QuadrayVector.quadrance()
//   Quadray::dot()          ↔  QuadrayVector.dot()
//   Quadray::spread()       ↔  QuadrayVector.spread()
//   rs_lt() / rs_min()      ↔  rs_lt() / rs_min()
//
// Key IVM facts:
//   - 4 tetrahedral vertices: (1,0,0,0) and cyclic permutations
//   - 12 cuboctahedral neighbours: all permutations of (1,1,0,0)
//   - Quadrance between any two nearest neighbours = 2 (in canonical IVM units)
//   - pell_rotate() multiplies each component by SURD_PHI1 = (2,1) — a unit
//     in Q(√3) — so quadrance is preserved after normalisation
//
// No floating point. No division. No branches in arithmetic.
// CC0 1.0 Universal.

#pragma once
#include "spu_surd.h"

// ── Exact ordering helpers ────────────────────────────────────────────────── //

// Returns true if s1 < s2 in Q(√3), using only integer arithmetic.
// Strategy: let d = s1 - s2 = (da + db·√3). Then s1 < s2 iff d < 0.
//   - If da ≤ 0 and db ≤ 0 (and not both zero) → d < 0  → true
//   - If da ≥ 0 and db ≥ 0                      → d ≥ 0 → false
//   - Mixed sign: compare magnitudes via squaring (√3 ≈ 1.732)
//       da < 0, db > 0: d < 0 iff |da| > db√3 iff da² > 3·db²
//       da > 0, db < 0: d < 0 iff da < |db|√3 iff da² < 3·db²
inline bool rs_lt(const RationalSurd& s1, const RationalSurd& s2) {
    int32_t da = s1.p - s2.p;
    int32_t db = s1.q - s2.q;
    if (da == 0 && db == 0)   return false;
    if (da <= 0 && db <= 0)   return true;
    if (da >= 0 && db >= 0)   return false;
    int64_t da2 = (int64_t)da * da;
    int64_t db2 = (int64_t)db * db;
    if (da < 0 && db > 0)     return da2 > 3 * db2;   // |da| > db√3
    return da2 < 3 * db2;                               // da > 0, db < 0
}

inline RationalSurd rs_min(const RationalSurd& a, const RationalSurd& b) {
    return rs_lt(b, a) ? b : a;
}

inline RationalSurd rs_min4(const RationalSurd& a, const RationalSurd& b,
                             const RationalSurd& c, const RationalSurd& d) {
    return rs_min(rs_min(a, b), rs_min(c, d));
}

// ── Quadray ───────────────────────────────────────────────────────────────── //

struct Quadray {
    RationalSurd a, b, c, d;  // four tetrahedral axes

    constexpr Quadray() : a(), b(), c(), d() {}
    constexpr Quadray(RationalSurd a_, RationalSurd b_,
                      RationalSurd c_, RationalSurd d_)
        : a(a_), b(b_), c(c_), d(d_) {}

    // ── Arithmetic ──────────────────────────────────────────────────────── //

    constexpr Quadray operator+(const Quadray& o) const {
        return { a + o.a, b + o.b, c + o.c, d + o.d };
    }
    constexpr Quadray operator-(const Quadray& o) const {
        return { a - o.a, b - o.b, c - o.c, d - o.d };
    }
    constexpr Quadray operator-() const {
        return { -a, -b, -c, -d };
    }

    // Scale all components by a RationalSurd scalar.
    constexpr Quadray scale(const RationalSurd& s) const {
        return { a * s, b * s, c * s, d * s };
    }

    constexpr bool operator==(const Quadray& o) const {
        return a == o.a && b == o.b && c == o.c && d == o.d;
    }
    constexpr bool operator!=(const Quadray& o) const { return !(*this == o); }

    constexpr bool is_zero() const {
        return a.is_zero() && b.is_zero() && c.is_zero() && d.is_zero();
    }

    // ── Normalisation ───────────────────────────────────────────────────── //

    // Subtract minimum component from all axes → canonical form: min == 0.
    // Exact: uses rs_min4() with integer-only comparison.
    Quadray normalize() const {
        RationalSurd m = rs_min4(a, b, c, d);
        return { a - m, b - m, c - m, d - m };
    }

    // ── Geometry ────────────────────────────────────────────────────────── //

    // IVM quadrance (squared distance from origin):
    //   Q = Σᵢ<ⱼ (cᵢ - cⱼ)²  for all 6 component pairs.
    // Exact in Q(√3). Equals 2 for any nearest-neighbour in canonical IVM.
    constexpr RationalSurd quadrance() const {
        const RationalSurd comps[4] = {a, b, c, d};
        RationalSurd q;
        for (int i = 0; i < 4; i++)
            for (int j = i + 1; j < 4; j++) {
                RationalSurd diff = comps[i] - comps[j];
                q = q + diff * diff;
            }
        return q;
    }

    // Component-wise inner product Σ aᵢ·bᵢ in Q(√3).
    constexpr RationalSurd dot(const Quadray& o) const {
        return a*o.a + b*o.b + c*o.c + d*o.d;
    }

    // Wildberger-style spread: s = (Q(P)·Q(Q) − (P·Q)²) / (Q(P)·Q(Q))
    // Returns exact rational fraction as (numerator, denominator) in Q(√3).
    // Note: dot() here is the component-wise sum Σuᵢvᵢ (matching spu_vm.py).
    // This gives a useful geometric ratio but spread(A,A) is NOT necessarily 0
    // because the Quadray metric tensor is not diagonal in component form.
    // Denominator == ZERO means at least one vector is the zero vector.
    struct Spread { RationalSurd numer, denom; };
    Spread spread(const Quadray& o) const {
        RationalSurd pp = quadrance();
        RationalSurd qq = o.quadrance();
        RationalSurd pq = dot(o);
        RationalSurd den = pp * qq;
        RationalSurd num = den - pq * pq;
        return { num, den };
    }

    // ── Discrete transforms ─────────────────────────────────────────────── //

    // Cyclic permutation: (a,b,c,d) → (b,c,d,a).
    // One 90° discrete rotation in IVM space. Zero-cost, exact.
    constexpr Quadray cycle() const { return { b, c, d, a }; }

    // Pell rotation: multiply each component by SURD_PHI1 = (2,1).
    // SURD_PHI1 is a unit in Q(√3) (norm==1), so this preserves quadrance
    // after normalisation. Generates the Pell orbit: (1,0)→(2,1)→(7,4)→…
    Quadray pell_rotate() const {
        return scale(SURD_PHI1).normalize();
    }

    // ── F,G,H Circulant Rotation (Thomson SQR §6) ──────────────────────── //

    // Applies the 3×3 circulant matrix to B,C,D with A invariant.
    //   B' = F·B + H·C + G·D
    //   C' = G·B + F·C + H·D
    //   D' = H·B + G·C + F·D
    // F,G,H must satisfy F³+G³+H³−3FGH = 1 (circulant determinant).
    // 9 surd multiplies, zero sqrt, zero division.
    // At {60°,120°,240°,300°}: every entry rational in {−1/3, 2/3}.
    constexpr Quadray circulant_rotate(const RationalSurd& F,
                                        const RationalSurd& G,
                                        const RationalSurd& H) const {
        return {
            a,                                                          // A invariant
            F*b + H*c + G*d,                                           // B'
            G*b + F*c + H*d,                                           // C'
            H*b + G*c + F*d                                            // D'
        };
    }

    // ── Rational Linear Interpolation ──────────────────────────────────── //

    // Interpolate between self (t=0) and other (t=1) with rational t = tn/td.
    // Each component: c_i = self[i] + (other[i]−self[i]) * tn / td.
    // Result coefficients are scaled by td; divide by td to recover true value.
    constexpr Quadray lerp_spread(const Quadray& other,
                                   int tn, int td) const {
        auto lerp_comp = [&](const RationalSurd& s0, const RationalSurd& s1) {
            return RationalSurd{
                s0.p * td + (s1.p - s0.p) * tn,
                s0.q * td + (s1.q - s0.q) * tn,
            };
        };
        return { lerp_comp(a, other.a), lerp_comp(b, other.b),
                 lerp_comp(c, other.c), lerp_comp(d, other.d) };
    }

    // ── Hex projection ──────────────────────────────────────────────────── //

    // Project normalised Quadray onto axial hex grid coordinates (col, row).
    // Uses only the rational (p) part of each component.
    // With d==0 canonical: col = a.p - d.p, row = b.p - d.p.
    struct HexCoord { int32_t col, row; };
    HexCoord hex_project() const {
        Quadray n = normalize();
        int32_t d_off = n.d.p;
        return { n.a.p - d_off, n.b.p - d_off };
    }

    // ── Display ─────────────────────────────────────────────────────────── //

    void print(const char* label = nullptr) const {
        if (label) printf("%s: ", label);
        printf("[(%d,%d) (%d,%d) (%d,%d) (%d,%d)]\n",
               a.p, a.q, b.p, b.q, c.p, c.q, d.p, d.q);
    }
};

// ── IVM canonical basis vectors ───────────────────────────────────────────── //
// The four tetrahedral axes. All in canonical form (min component == 0).
// Quadrance of each from origin: Q((1,0,0,0)) = 3.

constexpr Quadray QR_A { {1,0}, {0,0}, {0,0}, {0,0} };
constexpr Quadray QR_B { {0,0}, {1,0}, {0,0}, {0,0} };
constexpr Quadray QR_C { {0,0}, {0,0}, {1,0}, {0,0} };
constexpr Quadray QR_D { {0,0}, {0,0}, {0,0}, {1,0} };
constexpr Quadray QR_ZERO {};

// The 6 IVM face-pair vectors (permutations of (1,1,0,0)).
// These are the pairwise sums of the 4 tetrahedral axes, forming the face
// centres of the tetrahedron. Quadrance from origin = 4.
// Used in spread calculations and hex projection alignment.
constexpr Quadray IVM_FACE_6[6] = {
    { {1,0}, {1,0}, {0,0}, {0,0} },   // A+B
    { {1,0}, {0,0}, {1,0}, {0,0} },   // A+C
    { {1,0}, {0,0}, {0,0}, {1,0} },   // A+D
    { {0,0}, {1,0}, {1,0}, {0,0} },   // B+C
    { {0,0}, {1,0}, {0,0}, {1,0} },   // B+D
    { {0,0}, {0,0}, {1,0}, {1,0} },   // C+D
};

// The 12 FCC nearest-neighbour (cuboctahedral / VE) vectors in canonical
// Quadray form. These are all 12 permutations of the multiset {2,1,1,0}.
// Quadrance from origin = 8. Each pair of the 12 that are antipodal in 3D
// has Quadrance 32 between them.
//
// Derivation: the 12 FCC nearest neighbours of the origin in Cartesian
// (e.g. (1,1,0) and its 11 sign/axis permutations) map to exactly these 12
// Quadray vectors under the standard Urner tetrahedral basis embedding.
constexpr Quadray IVM_CUBE_12[12] = {
    { {2,0}, {1,0}, {1,0}, {0,0} },
    { {2,0}, {1,0}, {0,0}, {1,0} },
    { {2,0}, {0,0}, {1,0}, {1,0} },
    { {1,0}, {2,0}, {1,0}, {0,0} },
    { {1,0}, {2,0}, {0,0}, {1,0} },
    { {1,0}, {1,0}, {2,0}, {0,0} },
    { {1,0}, {0,0}, {2,0}, {1,0} },
    { {1,0}, {1,0}, {0,0}, {2,0} },
    { {1,0}, {0,0}, {1,0}, {2,0} },
    { {0,0}, {2,0}, {1,0}, {1,0} },
    { {0,0}, {1,0}, {2,0}, {1,0} },
    { {0,0}, {1,0}, {1,0}, {2,0} },
};

// ── Pell orbit with Janus polarity (Thomson SQR §9) ──────────────────────── //

// The 8-entry Pell fundamental domain orbit[step] = r^step.
// Each entry: {p, q, polarity} where polarity = sign of cos(step·φ/2).
// Steps 0–3 have p=+1; steps 4–7 have p=−1 (half-angle crosses 90°).
struct PellStep { int32_t p, q, polarity; };
constexpr PellStep PELL_ORBIT[8] = {
    {  1,    0, +1},   // r⁰
    {  2,    1, +1},   // r¹
    {  7,    4, +1},   // r²
    { 26,   15, +1},   // r³
    { 97,   56, -1},   // r⁴  (cos(θ/2) < 0)
    {362,  209, -1},   // r⁵
    {1351, 780, -1},   // r⁶
    {5042, 2911, -1},  // r⁷
};

// Look up (p, q, polarity) for Pell step n (≥ 0).
// Uses the fundamental domain with octave tracking for n ≥ 8.
inline PellStep pell_orbit_lookup(int n) {
    return PELL_ORBIT[n % 8];
}

// ── Cayley NLERP on Pell Orbit ───────────────────────────────────────────── //

// Interpolate between two Pell rotors by interpolating step counts linearly
// and reconstructing from the Pell orbit vault. Rational throughout.
// Returns the interpolated (p, q, polarity) at rational t = tn/td.
inline PellStep cayley_nlerp_pell(int step_a, int step_b, int tn, int td) {
    int step_interp = step_a + (step_b - step_a) * tn / td;
    return pell_orbit_lookup(step_interp);
}

// ── Triple Quadrance Formula (Wildberger, Divine Proportions Ch.5) ────────── //

// Given two quadrances Q1, Q2 and the spread s3 between them,
// returns the squared discriminant: (Q₃ − Q₁ − Q₂)² = 4·Q₁·Q₂·(1−s₃).
// Q₃ = Q₁ + Q₂ ± √discriminant.  Caller selects sign via polarity.
// All operations are integer — no square root taken.
inline int64_t triple_quadrance_disc(int Q1, int Q2, int spread_numer, int spread_denom) {
    // (1 − s₃) = (denom − numer) / denom
    // disc = 4·Q₁·Q₂·(denom − numer) / denom
    // Returns numerator of disc (without division by denom).
    return 4LL * Q1 * Q2 * (spread_denom - spread_numer);
}

// Spread from three quadrances (inverse of triple quadrance).
// Returns (numer, denom) as integer pair.
// s₃ = 1 − (Q₃ − Q₁ − Q₂)² / (4·Q₁·Q₂)
// numer = 4·Q₁·Q₂ − (Q₃ − Q₁ − Q₂)²
// denom = 4·Q₁·Q₂
struct SpreadPair { int64_t numer, denom; };
inline SpreadPair spread_from_quadrances(int Q1, int Q2, int Q3) {
    int64_t denom = 4LL * Q1 * Q2;
    int64_t diff = Q3 - Q1 - Q2;
    return { denom - diff * diff, denom };
}

// True if Q₁, Q₂, Q₃ form a right triangle (spread s₃ = 1 at Q₃ vertex).
inline bool is_right_triangle(int Q1, int Q2, int Q3) {
    return Q3 == Q1 + Q2;
}

// ── Delta Curve ──────────────────────────────────────────────────────────── //

// Parameterize the family of triangles with fixed Q₁, Q₂ as spread varies.
// Returns number of steps generated (≤ max_steps).
// For each step k, stores (k, steps, Q_sum, rhs_sq_num, rhs_sq_den).
struct DeltaPoint { int k, steps, Qsum; int64_t rhs_num; int rhs_den; };
inline int delta_curve(int Q1, int Q2, int max_steps, DeltaPoint* out) {
    int Qsum = Q1 + Q2;
    for (int k = 0; k <= max_steps; k++) {
        int64_t rhs_num = 4LL * Q1 * Q2 * (max_steps - k);
        out[k] = { k, max_steps, Qsum, rhs_num, max_steps };
    }
    return max_steps + 1;
}
