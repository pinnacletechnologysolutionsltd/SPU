// spu_manifold_types_test.cpp — Tests for spu_manifold_types.h
// Covers: WNode leaf/branch, sum_weight (Nguyen Eq 2.1), WeightedManifold
// construction, wm_tier, pressure API, bram_promote, jitterbug_to, wm_tick.

#include <cstdio>
#include <cstdint>
#include "spu_surd.h"
#include "spu_quadray.h"
#include "spu_ivm.h"
#include "spu_physics.h"
#include "spu_manifold_types.h"

static int g_pass = 0;
static int g_fail = 0;

#define ASSERT(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { printf("FAIL: %s (line %d)\n", msg, __LINE__); g_fail++; } \
} while(0)

#define ASSERT_EQ(got, want, msg) do { \
    if ((got) == (want)) { g_pass++; } \
    else { printf("FAIL: %s  got=%d want=%d (line %d)\n", \
                  msg, (int)(got), (int)(want), __LINE__); g_fail++; } \
} while(0)

int main() {
    // ── 1. WNode leaf ─────────────────────────────────────────────────────
    // QR_A = (1,0,0,0), quadrance = (3,0) [each pair diff = 1+1+1+1 = sum of 6 pairs of (1,0)²]
    // Quadray quadrance: Σᵢ<ⱼ (cᵢ-cⱼ)² = (1-0)²×3 = (3,0)
    {
        WNode leaf = wn_leaf(QR_A);
        ASSERT_EQ((int)leaf.weight.p, 3, "leaf QR_A weight.p = Q(QR_A)=3");
        ASSERT_EQ((int)leaf.weight.q, 0, "leaf QR_A weight.q = 0");
        ASSERT_EQ((int)leaf.child_count, 0, "leaf has no children");
    }

    // QR_ZERO = (0,0,0,0), quadrance = (0,0)
    {
        WNode leaf = wn_leaf(QR_ZERO);
        ASSERT(leaf.weight.is_zero(), "leaf QR_ZERO weight = 0");
    }

    // ── 2. sum_weight (Nguyen Eq 2.1) ────────────────────────────────────
    // sum_weight of a leaf = its self_quad (no children)
    {
        WNode a = wn_leaf(QR_A);
        WNode b = wn_leaf(QR_B);
        RationalSurd wa = sum_weight(a);
        RationalSurd wb = sum_weight(b);
        // QR_A and QR_B have same quadrance by symmetry
        ASSERT(wa == wb, "sum_weight QR_A == sum_weight QR_B (symmetry)");
        ASSERT_EQ((int)wa.p, 3, "sum_weight QR_A = (3,0)");
    }

    // sum_weight of branch = self + sum of children
    // Build: root → [leafA, leafB]
    {
        WNode la = wn_leaf(QR_A);
        WNode lb = wn_leaf(QR_B);
        const WNode* kids[2] = {&la, &lb};
        WNode branch = wn_branch(kids, 2, QR_C);
        // branch.self_quad = Q(QR_C) = 3
        // branch.weight = 3 + sum_weight(la) + sum_weight(lb) = 3 + 3 + 3 = 9
        RationalSurd w = sum_weight(branch);
        ASSERT_EQ((int)w.p, 9, "sum_weight 2-child branch = 3+3+3=9");
        ASSERT_EQ((int)w.q, 0, "sum_weight branch q = 0");
    }

    // 3-level deep chain: root → mid → leaf
    {
        WNode leaf = wn_leaf(QR_A);         // w = 3
        const WNode* mk[1] = {&leaf};
        WNode mid  = wn_branch(mk, 1, QR_B); // w = 3(self) + 3(leaf) = 6
        const WNode* rk[1] = {&mid};
        WNode root = wn_branch(rk, 1, QR_C); // w = 3(self) + 6(mid)  = 9
        ASSERT_EQ((int)sum_weight(root).p, 9, "sum_weight 3-level chain = 9");
    }

    // ── 3. wn_from_manifold + sum over all 13 axes ────────────────────────
    {
        Manifold13 m = Manifold13::ivm_full();
        WNode leaves[13];
        wn_from_manifold(m, leaves);
        // QR[0] = QR_A, Q=3. QR[1..12] = IVM_CUBE_12 (Q=8 each after Henosis zeroing)
        // Actually with ivm_full, QR[0]=QR_A has Q=3; QR[1..12]=IVM_CUBE_12 have Q=8
        // Total = 3 + 12×8 = 99
        RationalSurd total(0,0);
        for (int i = 0; i < 13; i++) total = total + sum_weight(leaves[i]);
        ASSERT_EQ((int)total.p, 99, "sum_weight over ivm_full = 3+12×8=99");
    }

    // ── 4. WeightedManifold construction ─────────────────────────────────
    {
        WeightedManifold wm = wm_ivm_full(8, 0);
        ASSERT_EQ((int)wm.static_weight.p, 8, "wm static_weight.p = 8");
        ASSERT(wm.pressure.is_zero(),          "wm pressure starts at 0");
        ASSERT_EQ((int)wm.js.phase, 0,         "wm jitterbug starts at phase 0");
        ASSERT_EQ((int)wm.pressure_decay_interval, 8, "wm decay interval default 8");

        // effective_weight = static_weight + 0 = (8,0)
        RationalSurd eff = wm_effective_weight(wm);
        ASSERT_EQ((int)eff.p, 8, "wm effective_weight = static when pressure=0");
    }

    // ── 5. wm_tier ────────────────────────────────────────────────────────
    // ivm_full laminar_weight = 99.  BRAM18 threshold: 4×eff ≥ 99  → eff ≥ 25
    // With static=8: 4×8=32 ≥ 99? No. 13×8=104 ≥ 99? Yes → SDRAM
    {
        WeightedManifold wm = wm_ivm_full(8, 0);
        BramTier t = wm_tier(wm);
        ASSERT(t == BramTier::SDRAM, "wm_tier(static=8) = SDRAM (13×8=104≥99)");
    }
    // With static=25: 4×25=100 ≥ 99 → BRAM18
    {
        WeightedManifold wm = wm_ivm_full(25, 0);
        BramTier t = wm_tier(wm);
        ASSERT(t == BramTier::BRAM18, "wm_tier(static=25) = BRAM18 (4×25=100≥99)");
    }
    // With static=1: 4×1=4 < 99, 13×1=13 < 99 → PSRAM
    {
        WeightedManifold wm = wm_ivm_full(1, 0);
        BramTier t = wm_tier(wm);
        ASSERT(t == BramTier::PSRAM, "wm_tier(static=1) = PSRAM");
    }

    // ── 6. Pressure API ───────────────────────────────────────────────────
    // Start PSRAM, add pressure to push to SDRAM
    {
        WeightedManifold wm = wm_ivm_full(1, 0);
        ASSERT(wm_tier(wm) == BramTier::PSRAM, "pre-pressure: PSRAM");
        // Add pressure=8: eff=9; 13×9=117 ≥ 99 → SDRAM
        wm_pressure_add(wm, RationalSurd(8, 0));
        ASSERT_EQ((int)wm.pressure.p, 8, "pressure accumulates");
        ASSERT(wm_tier(wm) == BramTier::SDRAM, "post-pressure(8): SDRAM");
        ASSERT_EQ((int)wm.stable_ticks, 0, "stable_ticks reset on pressure");
    }

    // Pressure decay: stable_ticks reaches interval → pressure halves
    {
        WeightedManifold wm = wm_ivm_full(1, 0, 3);  // decay every 3 stable ticks
        wm_pressure_add(wm, RationalSurd(8, 0));
        ASSERT_EQ((int)wm.pressure.p, 8, "pressure=8 before decay");
        // 3 decay ticks → should halve
        for (int i = 0; i < 3; i++) wm_pressure_decay_tick(wm);
        ASSERT_EQ((int)wm.pressure.p, 4, "pressure halved after 3 stable ticks");
        // 3 more → halve again
        for (int i = 0; i < 3; i++) wm_pressure_decay_tick(wm);
        ASSERT_EQ((int)wm.pressure.p, 2, "pressure halved again");
    }

    // ── 7. bram_promote ───────────────────────────────────────────────────
    {
        WeightedManifold before = wm_ivm_full(1, 0);
        WeightedManifold after  = before;
        // Impact of quadrance=8 → eff=9 → SDRAM (promoted from PSRAM)
        bool promoted = bram_promote(before, after, RationalSurd(8, 0));
        ASSERT(promoted, "bram_promote: PSRAM→SDRAM returns true");
        // No promotion if already at same tier
        WeightedManifold b2 = wm_ivm_full(25, 0);  // already BRAM18
        WeightedManifold a2 = b2;
        bool same = bram_promote(b2, a2, RationalSurd(1, 0));
        ASSERT(!same, "bram_promote: no promotion from BRAM18");
    }

    // ── 8. jitterbug_to ───────────────────────────────────────────────────
    {
        WeightedManifold wm = wm_ivm_full(8, 0);
        ASSERT_EQ((int)wm.js.phase, 0, "Jitterbug starts at VE (phase 0)");
        int steps = jitterbug_to(wm, JbTarget::OCTAHEDRON);
        ASSERT_EQ((int)wm.js.phase, 4, "jitterbug_to OCTAHEDRON → phase 4");
        ASSERT_EQ(steps, 4, "jitterbug_to OCTAHEDRON takes 4 steps");
        // Already at target → 0 steps
        steps = jitterbug_to(wm, JbTarget::OCTAHEDRON);
        ASSERT_EQ(steps, 0, "jitterbug_to already at target → 0 steps");
        // Full cycle back to VE
        steps = jitterbug_to(wm, JbTarget::VE);
        ASSERT_EQ((int)wm.js.phase, 0, "jitterbug_to VE wraps back to phase 0");
        ASSERT_EQ(steps, 4, "jitterbug_to VE from OCTAHEDRON takes 4 steps");
    }
    // ICOSAHEDRON = phase 2
    {
        WeightedManifold wm = wm_ivm_full(8, 0);
        jitterbug_to(wm, JbTarget::ICOSAHEDRON);
        ASSERT_EQ((int)wm.js.phase, 2, "jitterbug_to ICOSAHEDRON → phase 2");
    }

    // ── 9. wm_tick integration ────────────────────────────────────────────
    {
        WeightedManifold wm = wm_ivm_full(8, 0);
        // Cycle 0: not phi8 → no Henosis, just gasket check
        PhysicsFrame f = wm_tick(wm, 0);
        ASSERT_EQ((int)f.cycle, 0, "wm_tick cycle 0");
        // Cycle 21: phi21 gate — Jitterbug steps + possible recovery
        f = wm_tick(wm, 21);
        ASSERT_EQ((int)f.gate, (int)FibGate::PHI21, "wm_tick cycle 21 = PHI21 gate");
        // Pressure stays 0 (no external impact)
        ASSERT(wm.pressure.is_zero(), "wm pressure 0 with no impact added");
    }
    // Pressure survives leak ticks, decays on stable ticks
    {
        WeightedManifold wm = wm_ivm_full(8, 0, 4);
        wm_pressure_add(wm, RationalSurd(16, 0));
        // Run 4 stable ticks manually
        for (int i = 0; i < 4; i++) wm_pressure_decay_tick(wm);
        ASSERT_EQ((int)wm.pressure.p, 8, "pressure 16→8 after one decay period");
    }

    // ── Result ────────────────────────────────────────────────────────────
    if (g_fail == 0)
        printf("PASS\n");
    else
        printf("FAIL (%d failures / %d total)\n", g_fail, g_pass + g_fail);

    return g_fail > 0 ? 1 : 0;
}
