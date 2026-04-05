// spu_manifold_types.h — Weighted Manifold declarations for Lithic-L
// Layer 5.5: sits between the ISA encoding (spu_lithic_l.h) and user programs.
//
// Answers the static/dynamic weight question:
//   STATIC  — compile-time Nguyen W(v) tree, pre-calculated by the
//             compiler/constexpr and baked into the boot Weight-Map that
//             the SPU-13 inhales.  Determines BRAM tier assignment.
//   DYNAMIC — runtime `pressure` field scales the static weight each tick,
//             letting the Davis gasket promote hot data to faster memory
//             automatically.  Implements "Heave" (bram_promote()).
//
// Both are first-class: static weight is the *gravity*, pressure is the
// *current direction of that gravity*.
//
// Nguyen Eq 2.1 (translated):
//   W(v) = axis_quadrance(v) + Σ W(child_i)
//   — quadrance replaces the node-count in the original, giving semantic
//     density instead of structural size.
//
// Usage:
//   #include "spu_manifold_types.h"
//
//   // Build a weighted tree at compile time:
//   constexpr WNode leaf  = wn_leaf(QR_A);          // weight = Q(QR_A)
//   constexpr WNode trunk = wn_branch(leaf, leaf);   // weight = sum of children
//
//   // At runtime, apply pressure and decide tier:
//   WeightedManifold wm = wm_ivm_full(8);            // static_weight=8
//   wm_pressure_tick(&wm, impact_quadrance);          // dynamic update
//   BramTier tier = wm_tier(&wm);                     // live BRAM decision

#ifndef SPU_MANIFOLD_TYPES_H
#define SPU_MANIFOLD_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include "spu_surd.h"
#include "spu_quadray.h"
#include "spu_ivm.h"
#include "spu_physics.h"

// ── WNode: compile-time weight tree ───────────────────────────────────────
// A node in Nguyen's W(v) = 1 + ΣW(children) tree, translated to
// Q(√3): W(v) = quadrance(axis) + Σ W(children).
// Stored as a RationalSurd so the tree weight stays in the field.
// Max WNODE_CHILDREN per node — keeps the struct literal-constructible.
#define WNODE_CHILDREN 13  // one per SPU-13 axis

struct WNode {
    RationalSurd      weight      = {};
    RationalSurd      self_quad   = {};
    uint32_t          child_count = 0;
    const WNode*      children[WNODE_CHILDREN] = {};
};

// Leaf node: weight = quadrance of the Quadray axis.
constexpr WNode wn_leaf(const Quadray& axis) {
    RationalSurd q = axis.quadrance();
    WNode n;
    n.weight      = q;
    n.self_quad   = q;
    n.child_count = 0;
    for (int i = 0; i < WNODE_CHILDREN; i++) n.children[i] = nullptr;
    return n;
}

// sum_weight: Nguyen Eq 2.1 — W(v) = self_quad + ΣW(child_i)
// Returns the total weight of a subtree rooted at `n`.
// This IS the `sum_weight` operator — first-class in Lithic-L.
inline RationalSurd sum_weight(const WNode& n) {
    RationalSurd total = n.self_quad;
    for (uint32_t i = 0; i < n.child_count && n.children[i]; i++)
        total = total + sum_weight(*n.children[i]);
    return total;
}

// Branch node: weight = self_quad + sum of all child weights.
// Children are passed as a flat array of pointers.
inline WNode wn_branch(const WNode* const* kids, uint32_t nkids,
                        const Quadray& self_axis) {
    WNode n;
    n.self_quad   = self_axis.quadrance();
    n.child_count = (nkids < WNODE_CHILDREN) ? nkids : WNODE_CHILDREN;
    RationalSurd total = n.self_quad;
    for (uint32_t i = 0; i < n.child_count; i++) {
        n.children[i] = kids[i];
        total = total + sum_weight(*kids[i]);
    }
    n.weight = total;
    for (uint32_t i = n.child_count; i < WNODE_CHILDREN; i++)
        n.children[i] = nullptr;
    return n;
}

// Convenience: build a 13-leaf WTree from an IVM Manifold13 (one leaf per axis).
// Returns a WNode array of 13 leaves — caller stores them.
inline void wn_from_manifold(const Manifold13& m, WNode out[13]) {
    for (int i = 0; i < 13; i++)
        out[i] = wn_leaf(m.qr[i]);
}

// ── WeightedManifold: runtime pressure-modulated manifold ─────────────────
// Extends Manifold13 with a static weight floor and a dynamic pressure
// accumulator.  Together they drive live BRAM tier decisions.
struct WeightedManifold {
    Manifold13   m;               // 13-axis IVM manifold (positions)
    DavisGasket  g;               // Davis gasket (tension τ, K)
    JitterbugState js;            // Jitterbug phase

    // Static weight (pre-calculated Nguyen tree sum).
    // Set at construction. Determines the base BRAM tier.
    RationalSurd static_weight;

    // Dynamic pressure accumulator.
    // Each pressure_tick() adds impact quadrance; decays (>>1) on stable tick.
    // Acts as a runtime multiplier: effective_weight = static_weight + pressure.
    RationalSurd pressure;

    // Pressure decay counter: halve pressure every N stable ticks.
    uint32_t     stable_ticks;
    uint32_t     pressure_decay_interval;  // default 8 (phi_8 gate)
};

// Construct a WeightedManifold from ivm_full() + a static weight scalar.
inline WeightedManifold wm_ivm_full(int32_t static_weight_p,
                                     int32_t static_weight_q = 0,
                                     uint32_t decay_interval   = 8) {
    WeightedManifold wm;
    wm.m                    = Manifold13::ivm_full();
    wm.g.tau                = RationalSurd(0, 0);
    wm.g.K                  = RationalSurd(1, 0);
    wm.g.henosis_count      = 0;
    wm.g.tick_count         = 0;
    wm.g.leak               = false;
    wm.js.phase             = 0;
    wm.static_weight        = RationalSurd(static_weight_p, static_weight_q);
    wm.pressure             = RationalSurd(0, 0);
    wm.stable_ticks         = 0;
    wm.pressure_decay_interval = decay_interval;
    return wm;
}

// effective_weight: static_weight + pressure
// This is the live Nguyen weight used by bram_tier() at runtime.
inline RationalSurd wm_effective_weight(const WeightedManifold& wm) {
    return wm.static_weight + wm.pressure;
}

// wm_tier: compute BRAM tier from effective weight + manifold laminar_weight.
// Mirrors bram_tier() in spu_ivm.h but uses effective_weight as the numerator.
//   BRAM18  if  4 × eff ≥ lw   (top 25% of manifold weight)
//   SDRAM   if 13 × eff ≥ lw   (top ~8%)
//   PSRAM   otherwise
inline BramTier wm_tier(const WeightedManifold& wm) {
    RationalSurd lw  = laminar_weight(wm.m);
    RationalSurd eff = wm_effective_weight(wm);
    // 4 × eff ≥ lw  ↔  4*eff.p ≥ lw.p (both non-negative, q==0 for whole weights)
    // Use rs_lt: BRAM18 if NOT (4*eff < lw)
    RationalSurd eff4 = RationalSurd(eff.p * 4, eff.q * 4);
    if (!rs_lt(eff4, lw)) return BramTier::BRAM18;
    RationalSurd eff13 = RationalSurd(eff.p * 13, eff.q * 13);
    if (!rs_lt(eff13, lw)) return BramTier::SDRAM;
    return BramTier::PSRAM;
}

// ── Pressure API ──────────────────────────────────────────────────────────
// "Heave": add impact quadrance to pressure accumulator.
// Call this when an external event (collision, priority change) hits the node.
// The hardware "Heaves" the data into faster memory if tier promotes.
inline void wm_pressure_add(WeightedManifold& wm, const RationalSurd& impact_q) {
    wm.pressure = wm.pressure + impact_q;
    wm.stable_ticks = 0;  // reset decay counter on new pressure
}

// Decay: halve pressure each stable (non-leak) tick at the decay interval.
// Mirrors Henosis ANNE halving — same >>1 mechanic, applied to pressure.
inline void wm_pressure_decay_tick(WeightedManifold& wm) {
    if (wm.pressure.is_zero()) return;
    wm.stable_ticks++;
    if (wm.stable_ticks >= wm.pressure_decay_interval) {
        wm.pressure.p >>= 1;
        wm.pressure.q >>= 1;
        wm.stable_ticks = 0;
    }
}

// bram_promote: check if pressure has raised tier; returns true if promoted.
// In hardware, this would trigger a DMA copy to faster memory.
inline bool bram_promote(const WeightedManifold& wm_before,
                          WeightedManifold& wm_after,
                          const RationalSurd& impact_q) {
    BramTier before = wm_tier(wm_before);
    wm_pressure_add(wm_after, impact_q);
    BramTier after  = wm_tier(wm_after);
    return (int)after < (int)before;  // lower enum = faster tier
}

// ── Jitterbug shorthand ───────────────────────────────────────────────────
// jitterbug_to(): advance Jitterbug to a named phase target.
// Named phases from the Pell octave:
//   0 = VE (Vector Equilibrium)    2 = Icosahedron crossover
//   4 = Octahedron                 6 = return crossing
enum class JbTarget : uint8_t {
    VE          = 0,
    ICOSAHEDRON = 2,
    OCTAHEDRON  = 4,
    RETURN      = 6,
};

// Advance Jitterbug to target phase (stepping forward modulo 8).
// Returns number of steps taken (0 if already at target).
inline int jitterbug_to(WeightedManifold& wm, JbTarget target) {
    int steps = 0;
    uint8_t t = static_cast<uint8_t>(target);
    while (wm.js.phase != t && steps < 8) {
        jitterbug_step(wm.js, true);
        steps++;
    }
    return steps;
}

// ── Physics integration ───────────────────────────────────────────────────
// wm_tick: full physics frame for a WeightedManifold.
// Runs gasket_tick, Henosis recovery, Jitterbug advance, pressure decay.
inline PhysicsFrame wm_tick(WeightedManifold& wm, uint32_t cycle) {
    PhysicsFrame f = physics_tick(wm.g, wm.m, wm.js, cycle);
    if (!f.had_leak)
        wm_pressure_decay_tick(wm);
    else
        wm.stable_ticks = 0;  // pressure holds on leak, resets on recovery
    return f;
}

// ── Weight-Map emission ───────────────────────────────────────────────────
// wm_print: print the weight map for this WeightedManifold to stdout.
// This is the "Inhale" debug view — what the SPU-13 boots with.
inline void wm_print(const WeightedManifold& wm) {
    printf("WeightedManifold state:\n");
    printf("  static_weight  : (%d, %d√3)\n",
           (int)wm.static_weight.p, (int)wm.static_weight.q);
    printf("  pressure       : (%d, %d√3)\n",
           (int)wm.pressure.p, (int)wm.pressure.q);
    printf("  effective      : (%d, %d√3)\n",
           (int)wm_effective_weight(wm).p,
           (int)wm_effective_weight(wm).q);
    printf("  Jitterbug phase: %u/7\n", (unsigned)wm.js.phase);

    const char* tier_name[] = {"BRAM18", "SDRAM", "PSRAM"};
    BramTier t = wm_tier(wm);
    printf("  BRAM tier      : %s\n",
           (int)t < 3 ? tier_name[(int)t] : "?");

    printf("  Axis weights (sum_weight on WNodes):\n");
    WNode leaves[13];
    wn_from_manifold(wm.m, leaves);
    RationalSurd total(0, 0);
    for (int i = 0; i < 13; i++) {
        RationalSurd w = sum_weight(leaves[i]);
        total = total + w;
        printf("    QR[%2d] Q=(%3d,%3d√3)  W=(%3d,%3d√3)\n",
               i, (int)wm.m.qr[i].quadrance().p,
               (int)wm.m.qr[i].quadrance().q,
               (int)w.p, (int)w.q);
    }
    printf("  Total manifold weight: (%d, %d√3)\n",
           (int)total.p, (int)total.q);
}

#endif // SPU_MANIFOLD_TYPES_H
