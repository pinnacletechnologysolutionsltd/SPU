// spu_ivm_test.cpp — Unit tests for spu_ivm.h (IVM 13-axis manifold + Nguyen weight)
//
// CC0 1.0 Universal.

#include "spu_ivm.h"
#include <cstdio>

static int failures = 0;

#define CHECK(label, cond) do { \
    if (!(cond)) { printf("  FAIL: %s\n", label); failures++; } \
} while(0)

#define CHECK_SURD(label, got, want) do { \
    RationalSurd _g=(got), _w=(want); \
    if (_g != _w) { \
        printf("  FAIL: %s  got (%d,%d) want (%d,%d)\n", label, _g.p,_g.q,_w.p,_w.q); \
        failures++; \
    } \
} while(0)

int main() {

    // ── Manifold13 construction ────────────────────────────────────────── //
    {
        Manifold13 zero;
        bool all_zero = true;
        for (int i = 0; i < 13; i++)
            if (!zero.qr[i].is_zero()) { all_zero = false; break; }
        CHECK("default: all axes zero", all_zero);
    }

    // Canonical: QR[0..3] = tetrahedral basis, rest zero
    Manifold13 mc = Manifold13::canonical();
    CHECK("canonical: QR[0] == QR_A", mc.qr[0] == QR_A);
    CHECK("canonical: QR[1] == QR_B", mc.qr[1] == QR_B);
    CHECK("canonical: QR[4] == zero", mc.qr[4].is_zero());

    // IVM full: nucleus + 12 cube neighbours
    Manifold13 mf = Manifold13::ivm_full();
    CHECK("ivm_full: QR[0] == QR_A", mf.qr[0] == QR_A);
    for (int i = 0; i < 12; i++)
        if (mf.qr[i+1] != IVM_CUBE_12[i]) {
            printf("  FAIL: ivm_full QR[%d] mismatch\n", i+1);
            failures++;
        }

    // ── manifold_quad_sum ──────────────────────────────────────────────── //
    // Zero manifold: sum = 0
    {
        Manifold13 zero;
        CHECK_SURD("quad_sum: zero manifold", manifold_quad_sum(zero), SURD_ZERO);
    }
    // Canonical: QR[0..3] each have quadrance 3, rest 0 → total 12
    CHECK_SURD("quad_sum: canonical = (12,0)", manifold_quad_sum(mc), RationalSurd(12,0));
    // IVM full: QR[0] Q=3, QR[1..12] each Q=8 → total = 3 + 12*8 = 99
    CHECK_SURD("quad_sum: ivm_full = (99,0)", manifold_quad_sum(mf), RationalSurd(99,0));

    // ── manifold_vec_sum ──────────────────────────────────────────────── //
    // Zero manifold: vector sum = zero vector
    {
        Manifold13 zero;
        CHECK("vec_sum: zero manifold", manifold_vec_sum(zero).is_zero());
    }
    // Single axis QR_A: sum = QR_A
    {
        Manifold13 m;
        m.qr[0] = QR_A;
        CHECK("vec_sum: single A", manifold_vec_sum(m) == QR_A);
    }

    // ── is_cubic_leak ──────────────────────────────────────────────────── //
    CHECK("no leak: zero manifold", !is_cubic_leak(Manifold13{}));
    // QR_A alone → non-zero sum → cubic leak
    {
        Manifold13 m;
        m.qr[0] = QR_A;
        CHECK("cubic leak: single axis", is_cubic_leak(m));
    }
    // QR_A + (-QR_A) should cancel → no leak
    {
        Manifold13 m;
        m.qr[0] = QR_A;
        m.qr[1] = Quadray{ {-1,0},{0,0},{0,0},{0,0} };  // -QR_A (not canonical)
        // vec_sum = QR_A + (-QR_A) = zero
        CHECK("no leak: A + (-A)", !is_cubic_leak(m));
    }

    // ── Nguyen weight: axis_weight ─────────────────────────────────────── //
    // axis_weight = quadrance of the Quadray
    CHECK_SURD("axis_weight: QR_A = 3", axis_weight(QR_A), RationalSurd(3,0));
    CHECK_SURD("axis_weight: QR_ZERO = 0", axis_weight(QR_ZERO), SURD_ZERO);
    CHECK_SURD("axis_weight: CUBE[0] = 8", axis_weight(IVM_CUBE_12[0]), RationalSurd(8,0));

    // ── laminar_weight ─────────────────────────────────────────────────── //
    CHECK_SURD("laminar_weight: zero manifold = 0",
        laminar_weight(Manifold13{}), SURD_ZERO);
    CHECK_SURD("laminar_weight: canonical = 12",
        laminar_weight(mc), RationalSurd(12,0));
    CHECK_SURD("laminar_weight: ivm_full = 99",
        laminar_weight(mf), RationalSurd(99,0));

    // ── wedge_fraction ─────────────────────────────────────────────────── //
    // Canonical manifold: total=12, each active axis weight=3
    {
        WeightFraction wf = wedge_fraction(mc, 0);  // QR[0] = QR_A, W=3
        CHECK_SURD("wedge: numer = 3", wf.numer, RationalSurd(3,0));
        CHECK_SURD("wedge: denom = 12", wf.denom, RationalSurd(12,0));
        CHECK("wedge: not zero weight", !wf.is_zero_weight());
        CHECK("wedge: not full weight", !wf.is_full_weight());
    }
    // Zero axis → zero weight fraction
    {
        WeightFraction wf = wedge_fraction(mc, 4);  // QR[4] = zero
        CHECK("wedge: zero axis is_zero_weight", wf.is_zero_weight());
    }
    // Single-axis manifold → full weight
    {
        Manifold13 m;
        m.qr[0] = QR_A;
        WeightFraction wf = wedge_fraction(m, 0);
        CHECK("wedge: single axis is_full_weight", wf.is_full_weight());
    }

    // ── bram_tier ──────────────────────────────────────────────────────── //
    // Zero weight → PSRAM
    {
        WeightFraction z { SURD_ZERO, RationalSurd(12,0) };
        CHECK("tier: zero → PSRAM", bram_tier(z) == BramTier::PSRAM);
    }
    // Weight 3/12 = 1/4 → exactly on BRAM18 threshold → BRAM18 (>= 1/4)
    {
        WeightFraction wf { RationalSurd(3,0), RationalSurd(12,0) };
        CHECK("tier: 3/12 → BRAM18", bram_tier(wf) == BramTier::BRAM18);
    }
    // Weight 4/12 = 1/3 → BRAM18
    {
        WeightFraction wf { RationalSurd(4,0), RationalSurd(12,0) };
        CHECK("tier: 4/12 → BRAM18", bram_tier(wf) == BramTier::BRAM18);
    }
    // Weight 1/13 of total (IVM full, one axis Q=8, total Q=99)
    // 8/99: 4*8=32, 32 < 99 → not BRAM18. 13*8=104, 104 > 99 → SDRAM
    {
        WeightFraction wf { RationalSurd(8,0), RationalSurd(99,0) };
        CHECK("tier: 8/99 → SDRAM", bram_tier(wf) == BramTier::SDRAM);
    }
    // Very small weight → PSRAM
    {
        WeightFraction wf { RationalSurd(1,0), RationalSurd(1000,0) };
        CHECK("tier: 1/1000 → PSRAM", bram_tier(wf) == BramTier::PSRAM);
    }

    // ── Pell zoom ──────────────────────────────────────────────────────── //
    // Pell scale levels: 0=(1,0), 1=(2,1), 2=(7,4), 3=(26,15)
    CHECK_SURD("pell_zoom: level 0", pell_zoom_scale(0), RationalSurd(1,0));
    CHECK_SURD("pell_zoom: level 1", pell_zoom_scale(1), RationalSurd(2,1));
    CHECK_SURD("pell_zoom: level 2", pell_zoom_scale(2), RationalSurd(7,4));
    CHECK_SURD("pell_zoom: level 3", pell_zoom_scale(3), RationalSurd(26,15));

    // Pell zoom level 0 = identity transform
    {
        Manifold13 zoomed = manifold_pell_zoom(mc, 0);
        bool same = true;
        for (int i = 0; i < 13; i++)
            if (zoomed.qr[i] != mc.qr[i].normalize()) { same = false; break; }
        CHECK("pell_zoom: level 0 = identity", same);
    }
    // Pell zoom preserves laminar_weight ratio between axes (weights scale equally)
    {
        // At zoom 1: each axis scaled by (2,1). Quadrance of QR_A after pell_rotate:
        // scale QR_A=(1,0,0,0) by (2,1) → (2,1,0,0,0,0,0,0). Q = 3*(2,1)*(2,1) = ...
        // Actually: q.scale(s).quadrance() = q.quadrance() * s * s
        // Q(QR_A) = 3, scale (2,1): Q = 3 * (2,1)*(2,1) = 3*(7,4) = (21,12)
        Manifold13 z1 = manifold_pell_zoom(mc, 1);
        // QR[0] after scale+normalize: (2,1,0,0,0,0,0,0)
        CHECK("pell_zoom: QR[0] scaled",
            z1.qr[0] == QR_A.scale(RationalSurd(2,1)).normalize());
    }

    // ── davis_ratio_product ────────────────────────────────────────────── //
    {
        RationalSurd tau {8,0}, K {1,0};
        CHECK_SURD("davis_ratio: 8*1 = 8", davis_ratio_product(tau, K), RationalSurd(8,0));
        RationalSurd tau2 {2,1}, K2 {2,1};
        // (2,1)*(2,1) = (4+3, 4+2) = (7,4)
        CHECK_SURD("davis_ratio: (2,1)*(2,1) = (7,4)",
            davis_ratio_product(tau2, K2), RationalSurd(7,4));
    }

    // ── Result ────────────────────────────────────────────────────────────//
    if (failures == 0) {
        printf("PASS\n");
        return 0;
    }
    printf("FAIL (%d failures)\n", failures);
    return 1;
}
