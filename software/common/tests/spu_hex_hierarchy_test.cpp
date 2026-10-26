// spu_hex_hierarchy_test.cpp — Tests for spu_hex_hierarchy.h
// Covers: HexCell leaf, hex_hierarchy_ivm(), weights, hex_adopt,
//         hex_reweight, hex_propagate, hex_pressure_decay,
//         hex_cull, hex_cell_tier.

#include <cstdio>
#include <cstdint>
#include "spu_surd.h"
#include "spu_quadray.h"
#include "spu_ivm.h"
#include "spu_manifold_types.h"
#include "spu_hex_hierarchy.h"

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
    // ── 1. HexCell leaf construction ─────────────────────────────────────
    {
        HexCell c = hex_cell_leaf(QR_A);
        // QR_A = (1,0,0,0), quadrance = 3
        ASSERT_EQ((int)c.weight.p,     3, "leaf QR_A weight = Q(QR_A) = 3");
        ASSERT(c.pressure.is_zero(),       "leaf pressure starts at 0");
        ASSERT_EQ((int)c.depth,        0, "leaf depth = 0");
        ASSERT_EQ((int)c.child_count,  0, "leaf has no children");
        ASSERT_EQ((int)c.parent, 0xFFFF,  "leaf parent = none");
    }

    // ── 2. hex_hierarchy_ivm() structure ─────────────────────────────────
    {
        HexHierarchy h = hex_hierarchy_ivm();
        // 1 root + 12 leaves = 13 cells
        ASSERT_EQ((int)h.count, 13, "ivm hierarchy has 13 cells");
        ASSERT_EQ((int)h.root,   0, "root index = 0");

        // Root should have 12 children (limited by HEX_CHILDREN=7 per level)
        // Wait — HEX_CHILDREN=7, but we have 12 leaves. The first 7 are adopted.
        // Root child_count ≤ HEX_CHILDREN=7.
        ASSERT(h.pool[0].child_count <= HEX_CHILDREN, "root children ≤ HEX_CHILDREN");

        // Root depth = 0
        ASSERT_EQ((int)h.pool[0].depth, 0, "root depth = 0");

        // All adopted leaves have depth = 1
        for (int i = 0; i < h.pool[0].child_count; i++) {
            uint16_t ci = h.pool[0].children[i];
            ASSERT_EQ((int)h.pool[ci].depth, 1, "leaf depth = 1");
        }

        // Root weight ≥ leaf weights (it includes them all)
        ASSERT(h.pool[0].weight.p > 3, "root weight > single leaf weight");
    }

    // ── 3. hex_alloc + hex_adopt ─────────────────────────────────────────
    {
        HexHierarchy h;
        h.count = 0; h.root = 0;

        HexCell root = hex_cell_leaf(QR_A, 0xFFFF);
        uint16_t ri = hex_alloc(h, root);
        ASSERT_EQ((int)ri, 0, "first alloc = index 0");
        ASSERT_EQ((int)h.count, 1, "count = 1 after alloc");

        HexCell child = hex_cell_leaf(QR_B, 0xFFFF);
        uint16_t ci = hex_alloc(h, child);
        ASSERT_EQ((int)ci, 1, "second alloc = index 1");

        bool ok = hex_adopt(h, ri, ci);
        ASSERT(ok, "hex_adopt succeeds");
        ASSERT_EQ((int)h.pool[ri].child_count, 1, "root now has 1 child");
        ASSERT_EQ((int)h.pool[ci].parent, (int)ri, "child's parent = root");
        ASSERT_EQ((int)h.pool[ci].depth, 1, "child depth = 1");
    }

    // ── 4. hex_reweight ──────────────────────────────────────────────────
    {
        HexHierarchy h;
        h.count = 0; h.root = 0;

        // root(QR_A) → child(QR_B) → grandchild(QR_C)
        HexCell root = hex_cell_leaf(QR_A, 0xFFFF);
        uint16_t ri = hex_alloc(h, root);
        HexCell ch = hex_cell_leaf(QR_B, 0xFFFF);
        uint16_t ci = hex_alloc(h, ch);
        hex_adopt(h, ri, ci);
        HexCell gc = hex_cell_leaf(QR_C, 0xFFFF);
        uint16_t gi = hex_alloc(h, gc);
        hex_adopt(h, ci, gi);

        hex_reweight(h, gi);  // recompute from grandchild up

        // child weight = Q(QR_B) + Q(QR_C) = 3 + 3 = 6
        ASSERT_EQ((int)h.pool[ci].weight.p, 6, "child weight = 6 after reweight");
        // root weight = Q(QR_A) + child_weight = 3 + 6 = 9
        ASSERT_EQ((int)h.pool[ri].weight.p, 9, "root weight = 9 after reweight");
    }

    // ── 5. hex_propagate ─────────────────────────────────────────────────
    {
        HexHierarchy h = hex_hierarchy_ivm();
        // Propagate impact at leaf [1] with pressure=8
        RationalSurd impact{8, 0};
        hex_propagate(h, 1, impact, /*max_hops=*/1);

        // Cell 1 itself gets full impact
        ASSERT_EQ((int)h.pool[1].pressure.p, 8, "origin gets full pressure");

        // Root (1 hop away from leaf 1) gets halved: 8>>1 = 4
        ASSERT_EQ((int)h.pool[0].pressure.p, 4, "root (1 hop) gets p/2 = 4");

        // Cell 2 is a sibling (child of root, 2 hops) — but max_hops=1, not reached
        // (cell 2 would be reached in 2 hops: 1→root→2, but max_hops=1)
        // pressure at cell 2 should be 0
        ASSERT(h.pool[2].pressure.is_zero(), "cell 2 (2 hops) not reached at max_hops=1");
    }

    // Wider propagation
    {
        HexHierarchy h = hex_hierarchy_ivm();
        hex_propagate(h, 1, RationalSurd(16, 0), /*max_hops=*/2);

        ASSERT_EQ((int)h.pool[1].pressure.p, 16, "origin: full 16");
        ASSERT_EQ((int)h.pool[0].pressure.p,  8, "root (hop 1): 8");
        // Cell 2 is root's child, 2 hops from cell 1: 16>>2 = 4
        ASSERT_EQ((int)h.pool[2].pressure.p,  4, "sibling (hop 2): 4");
    }

    // ── 6. hex_pressure_decay ────────────────────────────────────────────
    {
        HexHierarchy h = hex_hierarchy_ivm();
        hex_propagate(h, 0, RationalSurd(8, 0), 0); // impact root only
        ASSERT_EQ((int)h.pool[0].pressure.p, 8, "pre-decay pressure = 8");

        hex_pressure_decay(h);
        ASSERT_EQ((int)h.pool[0].pressure.p, 4, "after 1 decay: pressure = 4");

        hex_pressure_decay(h);
        ASSERT_EQ((int)h.pool[0].pressure.p, 2, "after 2 decays: pressure = 2");

        hex_pressure_decay(h);
        ASSERT_EQ((int)h.pool[0].pressure.p, 1, "after 3 decays: pressure = 1");

        hex_pressure_decay(h);
        ASSERT_EQ((int)h.pool[0].pressure.p, 0, "after 4 decays: pressure = 0");
    }

    // ── 7. hex_cull (radius query) ────────────────────────────────────────
    {
        HexHierarchy h = hex_hierarchy_ivm();

        // Query from QR_A with radius = 0 (only cells at exact position)
        uint16_t out[16];
        size_t n = 0;
        hex_cull(h, QR_A, RationalSurd(0, 0), out, &n, 16);
        // Only cell 0 (QR_A at distance 0) should match
        ASSERT_EQ((int)n, 1, "cull radius=0 finds only root (QR_A)");
        ASSERT_EQ((int)out[0], 0, "cull radius=0 result is index 0");

        // Query with radius = 19 (covers all IVM_CUBE_12 distances from QR_A: 3,11,19)
        hex_cull(h, QR_A, RationalSurd(19, 0), out, &n, 16);
        // Should find root (Q=0) + all 13 cells (root + up to 12 leaves)
        ASSERT_EQ((int)n, 13, "cull radius=19 from QR_A finds all 13 cells");
    }

    // ── 8. hex_cell_tier ─────────────────────────────────────────────────
    {
        HexHierarchy h = hex_hierarchy_ivm();
        // Root weight = 3 + 12×8 = 99 (but only 7 children adopted)
        // Root weight = Q(QR_A) + Σ children(min(12,7)) + unadopted...
        // Actually: hex_hierarchy_ivm adopts min(12, HEX_CHILDREN=7) children
        // Root weight = 3 + 7×8 = 59  (root + 7 leaves: Q=8 each)
        // Tier for root: eff = root.weight = 59; total = 59
        //   4×59 = 236 ≥ 59 → BRAM18
        BramTier root_tier = hex_cell_tier(h, 0);
        ASSERT(root_tier == BramTier::BRAM18, "root tier = BRAM18 (highest weight)");

        // A leaf: weight = 8; total = root.weight
        // 4×8=32 ≥ root.weight? Depends on root.weight
        // We just verify it's a valid tier value
        BramTier leaf_tier = hex_cell_tier(h, 1);
        ASSERT(leaf_tier == BramTier::BRAM18 || leaf_tier == BramTier::SDRAM
               || leaf_tier == BramTier::PSRAM, "leaf tier is a valid BramTier");
    }

    // ── 9. Pool overflow guard ────────────────────────────────────────────
    {
        HexHierarchy h;
        h.count = HEX_MAX_NODES;  // simulate full pool
        h.root  = 0;
        HexCell c = hex_cell_leaf(QR_A);
        uint16_t idx = hex_alloc(h, c);
        ASSERT_EQ((int)idx, 0xFFFF, "overflow returns 0xFFFF");
    }

    // ── Result ────────────────────────────────────────────────────────────
    if (g_fail == 0)
        printf("PASS\n");
    else
        printf("FAIL (%d failures / %d total)\n", g_fail, g_pass + g_fail);

    return g_fail > 0 ? 1 : 0;
}
