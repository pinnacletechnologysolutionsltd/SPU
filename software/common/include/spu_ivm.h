// spu_ivm.h — IVM 13-axis Manifold geometry for the SPU-13 software stack
//
// The Manifold13 struct holds the 13 Quadray register axes that form the
// SPU-13 Sovereign Cortex. The 13 axes correspond to the 12 IVM nearest-
// neighbour directions (cuboctahedral / Vector Equilibrium) plus the central
// nucleus axis QR[0].
//
// Core predicates:
//   manifold_sum()    — Σ of all 13 Quadray quadrances (Total Quadrance)
//   is_cubic_leak()   — true if manifold_sum != 0 (Henosis needed)
//   laminar_weight()  — Nguyen-style recursive weight as Σ axis_weight(i)
//   wedge_fraction()  — W(QR[i]) / W(manifold) — exact rational partition
//   davis_ratio()     — C = τ / K, integer multiply only (no division)
//
// Nguyen weight mapping (see knowledge/NGUYEN_WEIGHT_PARTITIONING.md):
//   axis_weight(q)    = q.quadrance()          — "truth density" of one axis
//   laminar_weight(m) = Σᵢ axis_weight(QR[i]) — total manifold weight
//   wedge_fraction(m,i) = (W(QR[i]), W(total)) — drives BRAM tier + hex LOD
//
// No floating point. No division. No branches in arithmetic.
// CC0 1.0 Universal.

#pragma once
#include "spu_quadray.h"

// ── Manifold13 ────────────────────────────────────────────────────────────── //

struct Manifold13 {
    static constexpr int AXES = 13;
    Quadray qr[AXES];  // QR[0] = nucleus, QR[1..12] = cuboctahedral axes

    // Default-init: all axes at zero.
    Manifold13() = default;

    // Initialise to IVM canonical basis: QR[0]=(1,0,0,0), QR[1..3]=(0,1,0,0)
    // etc., remaining axes at zero.
    static Manifold13 canonical() {
        Manifold13 m;
        m.qr[0]  = QR_A;
        m.qr[1]  = QR_B;
        m.qr[2]  = QR_C;
        m.qr[3]  = QR_D;
        // QR[4..12] remain zero
        return m;
    }

    // Initialise from the 12 IVM_CUBE_12 neighbours + nucleus at QR_A.
    static Manifold13 ivm_full() {
        Manifold13 m;
        m.qr[0] = QR_A;
        for (int i = 0; i < 12; i++)
            m.qr[i + 1] = IVM_CUBE_12[i];
        return m;
    }
};

// ── Manifold predicates ───────────────────────────────────────────────────── //

// Sum of all 13 Quadray quadrances. In a perfectly laminar manifold this is
// the "total field tension" — zero only if all axes are at the origin.
// Used as the raw Davis Leak detector before thresholding.
inline RationalSurd manifold_quad_sum(const Manifold13& m) {
    RationalSurd s;
    for (int i = 0; i < Manifold13::AXES; i++)
        s = s + m.qr[i].quadrance();
    return s;
}

// Sum of all 13 Quadray vectors (component-wise). In a balanced VE manifold
// this should equal the zero vector (after normalisation).
inline Quadray manifold_vec_sum(const Manifold13& m) {
    Quadray s;
    for (int i = 0; i < Manifold13::AXES; i++)
        s = s + m.qr[i];
    return s;
}

// Cubic Leak: true if the vector sum of the manifold is non-zero.
// Corresponds to ΣABCD ≠ 0 in the Davis Law gasket.
// A laminar manifold has zero vector sum (all tensions cancel).
inline bool is_cubic_leak(const Manifold13& m) {
    return !manifold_vec_sum(m).is_zero();
}

// Davis Ratio: C = τ / K (manifold tension / stiffness).
// τ and K are provided externally (computed by the physics layer).
// Returns τ * K as a RationalSurd — the "product form" avoids division.
// To compare two ratios τ₁/K₁ vs τ₂/K₂: cross-multiply τ₁*K₂ vs τ₂*K₁.
inline RationalSurd davis_ratio_product(const RationalSurd& tau,
                                         const RationalSurd& K) {
    return tau * K;
}

// ── Nguyen Weight Partitioning ────────────────────────────────────────────── //
// See knowledge/NGUYEN_WEIGHT_PARTITIONING.md for full derivation.

// Weight of a single axis: its Quadray quadrance (truth density).
inline RationalSurd axis_weight(const Quadray& q) {
    return q.quadrance();
}

// Total manifold weight: Σ axis_weight(QR[i]) for all 13 axes.
// This is the "Heartbeat" scalar — drives BRAM tier + hex-hierarchy LOD.
inline RationalSurd laminar_weight(const Manifold13& m) {
    RationalSurd w;
    for (int i = 0; i < Manifold13::AXES; i++)
        w = w + axis_weight(m.qr[i]);
    return w;
}

// Wedge fraction for axis i: (W(QR[i]), W(manifold)).
// Exact rational partition — no float, no atan2.
// Use rs_lt(numer * total_denom, other_numer * numer_denom) to compare.
struct WeightFraction {
    RationalSurd numer;   // W(QR[i])
    RationalSurd denom;   // W(manifold) — total weight
    bool is_zero_weight() const { return numer.is_zero(); }
    bool is_full_weight() const { return numer == denom; }
};

inline WeightFraction wedge_fraction(const Manifold13& m, int axis_i) {
    return { axis_weight(m.qr[axis_i]), laminar_weight(m) };
}

// BRAM tier classification based on wedge fraction.
// Thresholds (in units of 1/13 of total weight):
//   BRAM18 : weight > 1/4 of total  (high-weight axis — on-chip)
//   SDRAM  : weight > 1/13 of total (mid-weight — burst cached)
//   PSRAM  : weight ≤ 1/13 of total (low-weight or zero — background)
// Comparison is exact: uses rs_lt on cross-multiplied RationalSurds.
enum class BramTier { BRAM18, SDRAM, PSRAM };

inline BramTier bram_tier(const WeightFraction& wf) {
    if (wf.denom.is_zero() || wf.is_zero_weight())
        return BramTier::PSRAM;
    // numer/denom > 1/4  ↔  4*numer > denom
    RationalSurd four_numer = wf.numer * RationalSurd(4, 0);
    if (!rs_lt(four_numer, wf.denom))   // 4*n >= d  →  n/d >= 1/4
        return BramTier::BRAM18;
    // numer/denom > 1/13  ↔  13*numer > denom
    RationalSurd thirteen_numer = wf.numer * RationalSurd(13, 0);
    if (!rs_lt(thirteen_numer, wf.denom))
        return BramTier::SDRAM;
    return BramTier::PSRAM;
}

// ── Pell Zoom (semantic zoom via Pell Octave snapping) ────────────────────── //
// Replaces Nguyen's transcendental distortion with discrete Pell steps.
// Returns the Pell orbit element at the given zoom level n.
// level 0 = (1,0), 1 = (2,1), 2 = (7,4), 3 = (26,15), 4 = (97,56)...
inline RationalSurd pell_zoom_scale(int level) {
    RationalSurd s { 1, 0 };
    for (int i = 0; i < level; i++)
        s = s.pell_next();
    return s;
}

// Apply Pell zoom to a manifold: scale all axes by pell_orbit[level].
inline Manifold13 manifold_pell_zoom(const Manifold13& m, int level) {
    RationalSurd scale = pell_zoom_scale(level);
    Manifold13 out;
    for (int i = 0; i < Manifold13::AXES; i++)
        out.qr[i] = m.qr[i].scale(scale).normalize();
    return out;
}

// ── Display helpers ───────────────────────────────────────────────────────── //

inline const char* bram_tier_name(BramTier t) {
    switch (t) {
        case BramTier::BRAM18: return "BRAM18";
        case BramTier::SDRAM:  return "SDRAM ";
        case BramTier::PSRAM:  return "PSRAM ";
    }
    return "?";
}

// Print a summary weight table for the manifold.
inline void print_weight_table(const Manifold13& m) {
    RationalSurd total = laminar_weight(m);
    printf("Axis  Quadrance    Weight         Tier\n");
    printf("----  -----------  -------------  ------\n");
    for (int i = 0; i < Manifold13::AXES; i++) {
        WeightFraction wf = wedge_fraction(m, i);
        BramTier tier = bram_tier(wf);
        printf(" %2d   (%4d,%4d)   (%4d,%4d)/%s(%4d,%4d)   %s\n",
               i,
               m.qr[i].quadrance().p, m.qr[i].quadrance().q,
               wf.numer.p, wf.numer.q,
               wf.denom.is_zero() ? " " : "/",
               wf.denom.p, wf.denom.q,
               bram_tier_name(tier));
    }
    printf("Total weight: (%d, %d)\n", total.p, total.q);
    printf("Cubic leak:   %s\n", is_cubic_leak(m) ? "YES (Henosis needed)" : "no");
}
