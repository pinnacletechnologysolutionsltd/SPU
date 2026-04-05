// spu_sdf.h — Layer 7: Rational Distance Field + Anisotropic Distribution
//
// Grounded in two primary sources read verbatim:
//
//   Nguyen (2005) "Space-Efficient Visualisation of Large Hierarchies"
//     Eq 2.1: W(v) = 1 + Σ W(child_i)           — recursive weight
//     Eq 2.2: D(v) = (W(v) / ΣW(siblings)) × A  — wedge angle ratio
//     Here A is the full Spread (rational 1,0) not 360°; no float degrees.
//
//   Olivier (2022) "Dynamic Sketches: Hierarchical modeling of complex
//     and time-evolving scenes"
//     Ch 4.3: Fine-to-Coarse Analysis → Support Structure Hierarchy
//       Strokes cluster into "Fibers" by dominant orientation (anisotropy).
//       Distribution is not uniform — it follows fiber direction.
//     Ch 4.4: Distribution Synthesis: content density ∝ fiber alignment.
//
// SPU-13 translation:
//   "Surface"   = a set of Quadray axes in a Manifold13.
//   "Fiber"     = a dominant IVM axis direction (preferred 60° propagation).
//   "Distance"  = Quadrance Q(P, axis) — exact in Q(√3), no sqrt needed.
//   "Gradient"  = discrete direction toward nearest fiber axis (rational).
//   "Wedge"     = Nguyen ratio expressed as RationalSurd, not degrees.
//   "Aniso prop"= Olivier: propagate harder along fiber than across it.
//
// No floating point. No division. No sqrt. All arithmetic in Q(√3).
//
// Layer dependencies: spu_surd.h → spu_quadray.h → spu_ivm.h →
//                     spu_physics.h → spu_hex_hierarchy.h

#pragma once
#include "spu_quadray.h"
#include "spu_ivm.h"
#include "spu_hex_hierarchy.h"

// ── Quadrance distance from a point P to an IVM axis A ─────────────────────
// Returns Q(P-A) = (P-A)·(P-A) in Q(√3).  No sqrt.  Exact.
inline RationalSurd sdf_q(const Quadray& P, const Quadray& A) {
    return (P - A).quadrance();
}

// ── Find the nearest axis in a manifold by minimum Quadrance ───────────────
// Returns axis index [0..12].  Ties broken by lower index.
inline int sdf_nearest(const Quadray& P, const Manifold13& m) {
    int    best_idx = 0;
    RationalSurd best_q = sdf_q(P, m.qr[0]);

    for (int i = 1; i < Manifold13::AXES; i++) {
        RationalSurd q = sdf_q(P, m.qr[i]);
        if (rs_lt(q, best_q)) {
            best_q   = q;
            best_idx = i;
        }
    }
    return best_idx;
}

// ── Discrete rational gradient ∇f(P) ───────────────────────────────────────
// Returns a QuadrayVector pointing from P toward the nearest manifold axis.
// In Q(√3) there is no normalisation — the caller uses it for direction only.
// Per Olivier ch4: the gradient is the "fiber direction" — dominant aniso axis.
inline Quadray sdf_grad(const Quadray& P, const Manifold13& m) {
    int nearest = sdf_nearest(P, m);
    return m.qr[nearest] - P;
}

// ── Nguyen Eq 2.2 — Rational Wedge ratio ───────────────────────────────────
// D(v) = W_i / W_total  (replaces the 360° angle with a unit Spread ratio)
// Returns the fraction of the manifold "wedge" this node should own.
// Both arguments are RationalSurd weights from sum_weight() / sdf_q().
// No float. No division: returned as numerator + denominator pair.
struct WedgeRatio {
    RationalSurd numer;  // W_i
    RationalSurd denom;  // W_total
    // Scale a Q(√3) value by this ratio: result = (val * numer) — caller
    // multiplies numer and interprets as "proportional to W_i / W_total".
    // True division is never needed: hardware uses the ratio for comparison.
    bool dominates(const WedgeRatio& other) const {
        // numer/denom > other.numer/other.denom
        // ↔ numer * other.denom > other.numer * denom
        RationalSurd lhs = numer * other.denom;
        RationalSurd rhs = other.numer * denom;
        return rs_lt(rhs, lhs);
    }
};

inline WedgeRatio sdf_wedge_ratio(const RationalSurd& w_i,
                                   const RationalSurd& w_total) {
    return { w_i, w_total };
}

// ── Olivier fiber bias: alignment via Quadrance distance ───────────────────
// Aligned = impact direction and cell axis are close in IVM Quadray space.
// We measure this as sdf_q(impact_dir, cell_pos) — small Q = close = aligned.
// Threshold: Q < Q(impact_dir)/2  ("within half-distance of itself")
// This avoids the spread(A,A)≠0 issue (Quadray metric tensor is not diagonal).
struct FiberBias {
    RationalSurd q_dist;    // sdf_q(impact_dir, cell_pos)
    RationalSurd q_self;    // sdf_q(impact_dir, QR_ZERO) = impact quadrance
    // Aligned if Q_dist * 2 < Q_self  (closer than half self-distance)
    bool is_aligned() const {
        RationalSurd two_d = q_dist + q_dist;
        return rs_lt(two_d, q_self);
    }
};

inline FiberBias sdf_fiber_bias(const Quadray& impact_dir,
                                 const Quadray& cell_pos) {
    return {
        sdf_q(impact_dir, cell_pos),
        impact_dir.quadrance()  // Q of impact vector from origin
    };
}

// ── Anisotropic propagation (Olivier ch4 distribution synthesis) ────────────
//
// Like hex_propagate() but directional:
//   - Cells whose axis is aligned with impact_dir (low Spread) receive full
//     pressure (no extra attenuation) — they are "in the fiber."
//   - Cells perpendicular to impact_dir (high Spread) get an extra ANNE
//     halving each hop, matching Olivier's anisotropic density falloff.
//
// impact_q    : initial pressure magnitude (RationalSurd)
// impact_dir  : normalised direction of the hit (Quadray)
// max_hops    : BFS depth (default 3 to reach meso-level of HexHierarchy)
//
inline void sdf_aniso_propagate(HexHierarchy& h,
                                 uint16_t       origin_idx,
                                 const RationalSurd& impact_q,
                                 const Quadray&      impact_dir,
                                 uint8_t max_hops = 3) {
    if (origin_idx >= h.count) return;
    if (impact_q.is_zero()) return;

    struct Entry { uint16_t idx; uint8_t hops; RationalSurd pressure; };
    Entry    queue[HEX_MAX_NODES];
    bool     visited[HEX_MAX_NODES] = {};
    uint16_t head = 0, tail = 0;

    queue[tail++] = { origin_idx, 0, impact_q };
    visited[origin_idx] = true;

    while (head != tail) {
        Entry e = queue[head++];
        HexCell& cell = h.pool[e.idx];

        if (!e.pressure.is_zero()) {
            cell.pressure = cell.pressure + e.pressure;
            hex_reweight(h, e.idx);
        }

        if (e.hops >= max_hops) continue;

        for (int i = 0; i < cell.child_count; i++) {
            uint16_t ci = cell.children[i];
            if (ci >= h.count || visited[ci]) continue;
            visited[ci] = true;

            // Compute fiber alignment for this child
            FiberBias bias = sdf_fiber_bias(impact_dir, h.pool[ci].position);

            // Attenuate: aligned cells keep full pressure; cross-fiber halved
            RationalSurd p = e.pressure;
            p.p >>= 1;   // base ANNE per hop (isotropic component)
            p.q >>= 1;
            if (!bias.is_aligned()) {
                // Extra halving for off-fiber cells (Olivier anisotropy)
                p.p >>= 1;
                p.q >>= 1;
            }

            if (!p.is_zero())
                queue[tail++] = { ci, static_cast<uint8_t>(e.hops + 1), p };
        }
    }
}

// ── Davis Gate snap: does the gradient conflict with manifold stability? ─────
// Returns true if a Henosis pulse is needed.
// Conflict condition: grad · manifold_vec_sum ≠ zero
//   (the gradient is pulling against the laminar state)
// Uses dot product in Q(√3) — exact integer arithmetic.
inline bool sdf_snap(const Quadray& grad, const Manifold13& m) {
    Quadray vec_sum = manifold_vec_sum(m);
    // dot = Σ (grad.component_i * vec_sum.component_i) in Q(√3)
    RationalSurd dot = grad.dot(vec_sum);
    return !(dot == RationalSurd(0, 0));
}

// ── Nearest-axis SDF evaluation for all 13 axes ────────────────────────────
// Returns the minimum Quadrance from P to any manifold axis.
// This is the "rational SDF" value for point P.
inline RationalSurd sdf_min_q(const Quadray& P, const Manifold13& m) {
    return sdf_q(P, m.qr[sdf_nearest(P, m)]);
}

// ── Wedge-weighted manifold partition ──────────────────────────────────────
// Assigns each of the 13 axes a WedgeRatio based on its Quadrance weight
// relative to the total manifold weight (Nguyen Eq 2.2 for the whole VE).
// Results written into out[13].
inline void sdf_wedge_partition(const Manifold13& m, WedgeRatio out[13]) {
    // Compute total weight: Σ Q(axis) for all 13 axes
    RationalSurd total(0, 0);
    for (int i = 0; i < Manifold13::AXES; i++)
        total = total + m.qr[i].quadrance();

    for (int i = 0; i < Manifold13::AXES; i++)
        out[i] = sdf_wedge_ratio(m.qr[i].quadrance(), total);
}
