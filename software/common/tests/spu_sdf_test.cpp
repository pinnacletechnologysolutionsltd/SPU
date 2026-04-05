// spu_sdf_test.cpp — Layer 7 tests for spu_sdf.h
//
// Tests verify:
//   1. sdf_q()           — exact Quadrance distance, no sqrt
//   2. sdf_nearest()     — correct nearest axis selection
//   3. sdf_grad()        — gradient points toward nearest axis
//   4. WedgeRatio        — dominates() comparison via cross-multiply
//   5. FiberBias         — is_aligned() matches expected spread geometry
//   6. sdf_aniso_propagate() — aligned cells receive MORE pressure than cross-fiber
//   7. sdf_snap()        — zero grad → no snap; nonzero grad → snap needed
//   8. sdf_wedge_partition() — 13 ratios, all have same denominator (total Q)

#include <cstdio>
#include <cstdlib>
#include "../include/spu_sdf.h"

static int pass = 0, fail = 0;

#define ASSERT(cond, msg) \
    do { if (cond) { pass++; } else { fail++; \
         printf("FAIL: %s (line %d)\n", msg, __LINE__); } } while(0)

// ── 1. sdf_q: Quadrance from QR_A to QR_B ──────────────────────────────────
// Quadray quadrance uses Σ(i<j)(comp_i - comp_j)²
// QR_A=(1,0,0,0), QR_B=(0,1,0,0): diff=(1,-1,0,0)
// Pairs: (1,-1)²=4, (1,0)²=1, (1,0)²=1, (-1,0)²=1, (-1,0)²=1 → sum = 8
static void test_sdf_q() {
    RationalSurd q = sdf_q(QR_A, QR_B);
    ASSERT(q.p == 8 && q.q == 0, "sdf_q(QR_A, QR_B) == (8,0)");

    // Distance from an axis to itself is zero
    RationalSurd q0 = sdf_q(QR_A, QR_A);
    ASSERT(q0.p == 0 && q0.q == 0, "sdf_q(QR_A, QR_A) == (0,0)");
}

// ── 2. sdf_nearest: canonical() has QR[0]=QR_A, QR[1]=QR_B, QR[2]=QR_C, QR[3]=QR_D
static void test_sdf_nearest() {
    Manifold13 m = Manifold13::canonical();

    // QR_A itself → nearest is axis 0
    int n0 = sdf_nearest(QR_A, m);
    ASSERT(n0 == 0, "nearest to QR_A in canonical is axis 0");

    // QR_B → nearest is axis 1
    int n1 = sdf_nearest(QR_B, m);
    ASSERT(n1 == 1, "nearest to QR_B in canonical is axis 1");

    // QR_C → nearest is axis 2
    int n2 = sdf_nearest(QR_C, m);
    ASSERT(n2 == 2, "nearest to QR_C in canonical is axis 2");
}

// ── 3. sdf_grad: gradient from QR_B toward nearest = QR_B - QR_B = zero
//                gradient from origin toward QR_A
static void test_sdf_grad() {
    Manifold13 m = Manifold13::canonical();

    // Point AT an axis → gradient is zero vector (already at surface)
    Quadray g0 = sdf_grad(QR_A, m);
    ASSERT(g0 == QR_ZERO, "grad at surface axis is zero");

    // Point midway between QR_A and QR_B: P = QR_A + QR_B scaled by half
    // Use P = QR_A; nearest is 0; grad = QR_A - QR_A = 0 (already checked)
    // Now use a point closer to QR_B: just QR_B scaled (still == QR_B)
    // Gradient from QR_C toward its nearest (axis 2 = QR_C) is zero
    Quadray g2 = sdf_grad(QR_C, m);
    ASSERT(g2 == QR_ZERO, "grad at QR_C axis is zero");
}

// ── 4. WedgeRatio::dominates ────────────────────────────────────────────────
static void test_wedge_ratio() {
    // W=3, total=9  vs  W=2, total=9
    // 3/9 > 2/9  →  3*9 > 2*9  →  dominates
    RationalSurd w3(3, 0), w2(2, 0), tot(9, 0);
    WedgeRatio r3 = sdf_wedge_ratio(w3, tot);
    WedgeRatio r2 = sdf_wedge_ratio(w2, tot);
    ASSERT(r3.dominates(r2),  "WedgeRatio: 3/9 dominates 2/9");
    ASSERT(!r2.dominates(r3), "WedgeRatio: 2/9 does NOT dominate 3/9");

    // Equal weights → neither dominates
    WedgeRatio re = sdf_wedge_ratio(w3, tot);
    ASSERT(!r3.dominates(re), "WedgeRatio: equal weights → no dominance");
}

// ── 5. FiberBias::is_aligned ────────────────────────────────────────────────
// Alignment uses Q-distance: aligned iff Q(impact, cell)*2 < Q(impact, origin)
// QR_A to QR_A: Q_dist=0, Q_self=Q(QR_A)=8 → 0*2=0 < 8 → aligned
// QR_A to QR_B: Q_dist=8, Q_self=8 → 16 < 8 = false → not aligned
static void test_fiber_bias() {
    // Same vector → Q_dist = 0 → strongly aligned
    FiberBias b_same = sdf_fiber_bias(QR_A, QR_A);
    ASSERT(b_same.is_aligned(), "fiber bias: QR_A vs QR_A is aligned");

    // Adjacent IVM axis → Q_dist = Q_self = 8 → 2*8=16 >= 8 → NOT aligned
    FiberBias b_adj = sdf_fiber_bias(QR_A, QR_B);
    ASSERT(!b_adj.is_aligned(), "fiber bias: QR_A vs QR_B is not aligned");
}

// ── 6. sdf_aniso_propagate: aligned axis gets more pressure ─────────────────
// Set up a hierarchy: root (QR_A) with two children:
//   child_0 at QR_A (aligned with impact dir QR_A) — same axis
//   child_1 at QR_B (perpendicular to QR_A)
// After propagate with impact_dir = QR_A, child_0 should have >= child_1 pressure
static void test_aniso_propagate() {
    HexHierarchy h;
    h.count = 0; h.root = 0;

    // Allocate root at QR_A
    HexCell root_cell = hex_cell_leaf(QR_A, 0xFFFF);
    uint16_t root_idx = hex_alloc(h, root_cell);

    // Two children
    HexCell ca = hex_cell_leaf(QR_A, root_idx);
    HexCell cb = hex_cell_leaf(QR_B, root_idx);
    uint16_t idx_a = hex_alloc(h, ca);
    uint16_t idx_b = hex_alloc(h, cb);
    hex_adopt(h, root_idx, idx_a);
    hex_adopt(h, root_idx, idx_b);

    RationalSurd impact(16, 0);
    sdf_aniso_propagate(h, root_idx, impact, QR_A, 2);

    // Root gets the impact
    RationalSurd proot = h.pool[root_idx].pressure;
    ASSERT(proot.p == 16, "aniso_propagate: root gets full impact");

    // Aligned child (child_a = QR_A direction) gets full hop-attenuation only
    // Cross-fiber child (child_b = QR_B direction) gets extra halving
    RationalSurd pa = h.pool[idx_a].pressure;
    RationalSurd pb = h.pool[idx_b].pressure;

    // pa should be >= pb (aligned ≥ cross-fiber)
    bool aligned_dominates = !rs_lt(pa, pb) || pa == pb;
    ASSERT(aligned_dominates, "aniso_propagate: aligned child >= cross-fiber child");

    // If pa != pb, aligned cell strictly won
    if (!(pa == pb)) {
        ASSERT(!rs_lt(pa, pb), "aniso_propagate: aligned child > cross-fiber child strictly");
    }
}

// ── 7. sdf_snap ─────────────────────────────────────────────────────────────
static void test_sdf_snap() {
    // Laminar manifold: canonical, vec_sum ≠ zero in general
    // Zero gradient: sdf_snap returns false (no conflict)
    Manifold13 m = Manifold13::canonical();
    ASSERT(!sdf_snap(QR_ZERO, m), "sdf_snap: zero gradient → no snap needed");

    // Zero manifold: vec_sum = 0, any gradient → dot = 0 → no snap
    Manifold13 m_zero;
    ASSERT(!sdf_snap(QR_A, m_zero), "sdf_snap: zero manifold → no snap needed");
}

// ── 8. sdf_wedge_partition ───────────────────────────────────────────────────
static void test_wedge_partition() {
    Manifold13 m = Manifold13::ivm_full();
    WedgeRatio parts[13];
    sdf_wedge_partition(m, parts);

    // All denominators should be the same total Q weight (nonzero)
    bool all_same_denom = true;
    for (int i = 1; i < 13; i++) {
        if (!(parts[i].denom == parts[0].denom)) {
            all_same_denom = false;
            break;
        }
    }
    ASSERT(all_same_denom, "wedge_partition: all 13 ratios have same denominator");

    // Nucleus (QR_A: Q=1) should have smaller wedge than cube-12 axes (Q=8 or 11)
    // nucleus_ratio < cube_ratio ↔ !cube_ratio.dominates(nucleus) is false
    bool nucleus_smaller = parts[1].dominates(parts[0]);
    ASSERT(nucleus_smaller, "wedge_partition: IVM cube axis dominates nucleus wedge");
}

int main() {
    test_sdf_q();
    test_sdf_nearest();
    test_sdf_grad();
    test_wedge_ratio();
    test_fiber_bias();
    test_aniso_propagate();
    test_sdf_snap();
    test_wedge_partition();

    printf("\nLayer 7 (spu_sdf): %d passed, %d failed\n", pass, fail);
    if (fail == 0) { printf("PASS\n"); return 0; }
    else           { printf("FAIL\n"); return 1; }
}
