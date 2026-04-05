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
