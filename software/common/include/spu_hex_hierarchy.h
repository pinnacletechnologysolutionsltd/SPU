// spu_hex_hierarchy.h — Arlinghaus Hexagonal Hierarchy for SPU-13
// Layer 6 of the Q(√3) software stack.
//
// Implements nested hexagonal cell structures for:
//   • Spatial partitioning (render graph tile-based culling)
//   • Pressure wave propagation (Laminar-Doom destructible environments)
//   • Weight-based LOD (Nguyen W(v) drives micro→macro aggregation)
//
// Architecture:
//   HexCell  — single node: IVM Quadray position + Nguyen weight + children
//   HexHierarchy — 6-neighbour hex lattice, recursively nested
//
// Arlinghaus connection:
//   Micro-cells  (depth 0): individual tetra bonds  — Q = 3 or 8
//   Meso-cells   (depth 1): local hex cluster of 7  — W = 7 × micro
//   Macro-cells  (depth 2): 7 meso clusters         — W = 7 × meso
//   Each level aggregates via sum_weight() (Nguyen Eq 2.1).
//
// All coordinates are in Q(√3) Quadray. No float. No sqrt.
//
// Usage:
//   #include "spu_hex_hierarchy.h"
//
//   HexHierarchy h = hex_hierarchy_ivm();   // seed from ivm_full()
//   hex_propagate(&h, origin, impact_q);    // pressure wave
//   hex_cull(&h, frustum_center, q_radius, out, &n); // frustum query

#ifndef SPU_HEX_HIERARCHY_H
#define SPU_HEX_HIERARCHY_H

#include <stdint.h>
#include <stddef.h>
#include "spu_surd.h"
#include "spu_quadray.h"
#include "spu_ivm.h"
#include "spu_manifold_types.h"

// ── Hex lattice constants ──────────────────────────────────────────────────
// Maximum children per HexCell: 6 neighbours + 1 nucleus = 7.
// This is the IVM hex cluster: one centre + six face-vectors.
// Matches Arlinghaus's "7-cell" central-place hex unit.
#define HEX_CHILDREN 7
#define HEX_MAX_DEPTH 4   // max hierarchy levels (micro→meso→macro→sovereign)
#define HEX_MAX_NODES 512 // flat pool size for static allocation (no heap)

// ── HexCell ────────────────────────────────────────────────────────────────
// One node in the hex hierarchy tree.
// position  : IVM Quadray of this cell's nucleus
// weight    : Nguyen W(v) for this subtree
// pressure  : dynamic impact accumulator (Heave mechanic)
// depth     : 0 = leaf (micro), 1 = meso, 2 = macro, 3 = sovereign
// children  : indices into the flat HexHierarchy pool (0 = empty slot)
// parent    : index of parent cell (0xFFFF = root)
struct HexCell {
    Quadray      position;
    RationalSurd weight;
    RationalSurd pressure;
    uint8_t      depth;
    uint8_t      child_count;
    uint16_t     parent;
    uint16_t     children[HEX_CHILDREN];
};

// Initialise a leaf HexCell at a given Quadray position.
inline HexCell hex_cell_leaf(const Quadray& pos, uint16_t parent_idx = 0xFFFF) {
    HexCell c;
    c.position    = pos;
    c.weight      = pos.quadrance();   // W(leaf) = axis quadrance
    c.pressure    = RationalSurd(0, 0);
    c.depth       = 0;
    c.child_count = 0;
    c.parent      = parent_idx;
    for (int i = 0; i < HEX_CHILDREN; i++) c.children[i] = 0;
    return c;
}

// ── HexHierarchy ──────────────────────────────────────────────────────────
// Flat pool of HexCells.  Index 0 is always the root (sovereign nucleus).
// Add cells via hex_alloc(); build links via hex_adopt().
struct HexHierarchy {
    HexCell  pool[HEX_MAX_NODES];
    uint16_t count;   // number of allocated cells
    uint16_t root;    // index of root cell (always 0)
};

// Allocate a new HexCell into the pool.  Returns its index.
// Returns 0xFFFF on overflow (caller should check).
inline uint16_t hex_alloc(HexHierarchy& h, const HexCell& cell) {
    if (h.count >= HEX_MAX_NODES) return 0xFFFF;
    uint16_t idx = h.count++;
    h.pool[idx]  = cell;
    return idx;
}

// Link a child to a parent (adds to parent's children[], updates depth).
inline bool hex_adopt(HexHierarchy& h, uint16_t parent_idx, uint16_t child_idx) {
    if (parent_idx >= h.count || child_idx >= h.count) return false;
    HexCell& parent = h.pool[parent_idx];
    HexCell& child  = h.pool[child_idx];
    if (parent.child_count >= HEX_CHILDREN) return false;
    parent.children[parent.child_count++] = child_idx;
    child.parent = parent_idx;
    child.depth  = parent.depth + 1;
    return true;
}

// ── IVM seed: build a 2-level hierarchy from ivm_full() ────────────────────
// Level 0 (root): QR[0] = nucleus (QR_A), depth 0
// Level 1 (leaves): QR[1..12] = IVM_CUBE_12, depth 1
// Produces a 13-node tree mirroring the SPU-13 hardware axis map.
inline HexHierarchy hex_hierarchy_ivm() {
    HexHierarchy h;
    h.count = 0;
    h.root  = 0;

    // Root = nucleus
    HexCell root = hex_cell_leaf(QR_A, 0xFFFF);
    root.depth = 0;
    uint16_t root_idx = hex_alloc(h, root);

    // Leaves = 12 IVM_CUBE_12 neighbours (grouped into 2 rings of 6 each)
    for (int i = 0; i < 12; i++) {
        HexCell leaf = hex_cell_leaf(IVM_CUBE_12[i], root_idx);
        uint16_t idx = hex_alloc(h, leaf);
        if (idx != 0xFFFF)
            hex_adopt(h, root_idx, idx);
    }

    // Recompute root weight = self_quad + Σ children.weight
    RationalSurd total = h.pool[root_idx].weight;
    for (int i = 0; i < h.pool[root_idx].child_count; i++) {
        uint16_t ci = h.pool[root_idx].children[i];
        total = total + h.pool[ci].weight;
    }
    h.pool[root_idx].weight = total;

    return h;
}

// ── Weight recalculation ──────────────────────────────────────────────────
// Recompute W(v) bottom-up for a cell and all its ancestors.
// Must be called after modifying a leaf's position or pressure.
inline void hex_reweight(HexHierarchy& h, uint16_t idx) {
    if (idx >= h.count) return;
    HexCell& cell = h.pool[idx];

    // Recompute this cell's weight = self_quad + Σ children weights
    RationalSurd w = cell.position.quadrance() + cell.pressure;
    for (int i = 0; i < cell.child_count; i++) {
        uint16_t ci = cell.children[i];
        if (ci < h.count) w = w + h.pool[ci].weight;
    }
    cell.weight = w;

    // Propagate up to parent
    if (cell.parent != 0xFFFF)
        hex_reweight(h, cell.parent);
}

// ── Pressure propagation (Arlinghaus wave) ────────────────────────────────
// Apply an impact at `origin_idx` and propagate outward to all cells
// within `max_hops` neighbourhood distance.
// Each hop attenuates pressure by halving (>>1) — the ANNE mechanic.
inline void hex_propagate(HexHierarchy& h, uint16_t origin_idx,
                           const RationalSurd& impact_q,
                           uint8_t max_hops = 2) {
    if (origin_idx >= h.count) return;
    if (impact_q.is_zero()) return;

    // BFS with hop counter — no heap: fixed-size queue
    struct Entry { uint16_t idx; uint8_t hops; };
    Entry queue[HEX_MAX_NODES];
    bool  visited[HEX_MAX_NODES] = {};
    uint16_t head = 0, tail = 0;

    queue[tail++] = {origin_idx, 0};
    visited[origin_idx] = true;

    while (head != tail) {
        Entry e = queue[head++];
        HexCell& cell = h.pool[e.idx];

        // Attenuate: each hop halves the pressure (>>1)
        RationalSurd p = impact_q;
        for (uint8_t hop = 0; hop < e.hops; hop++) {
            p.p >>= 1;
            p.q >>= 1;
        }
        if (!p.is_zero()) {
            cell.pressure = cell.pressure + p;
            hex_reweight(h, e.idx);
        }

        if (e.hops >= max_hops) continue;

        // Enqueue children
        for (int i = 0; i < cell.child_count; i++) {
            uint16_t ci = cell.children[i];
            if (ci < h.count && !visited[ci]) {
                visited[ci] = true;
                queue[tail++] = {ci, uint8_t(e.hops + 1)};
            }
        }
        // Enqueue parent (wave propagates up the hierarchy too)
        if (cell.parent != 0xFFFF && !visited[cell.parent]) {
            visited[cell.parent] = true;
            queue[tail++] = {cell.parent, uint8_t(e.hops + 1)};
        }
    }
}

// ── Pressure decay ────────────────────────────────────────────────────────
// Halve pressure on all cells (call at phi_8 gate intervals).
inline void hex_pressure_decay(HexHierarchy& h) {
    for (uint16_t i = 0; i < h.count; i++) {
        if (!h.pool[i].pressure.is_zero()) {
            h.pool[i].pressure.p >>= 1;
            h.pool[i].pressure.q >>= 1;
            // Reweight only if pressure actually changed
            if (h.pool[i].pressure.is_zero())
                hex_reweight(h, i);
        }
    }
}

// ── Frustum / radius query (hex_cull) ─────────────────────────────────────
// Find all cells within quadrance radius `q_radius` of `center`.
// Writes their indices into `out[0..out_cap-1]`, sets *out_count.
// Uses exact Q(√3) quadrance comparison — no float.
inline void hex_cull(const HexHierarchy& h, const Quadray& center,
                      const RationalSurd& q_radius,
                      uint16_t* out, size_t* out_count, size_t out_cap) {
    *out_count = 0;
    for (uint16_t i = 0; i < h.count && *out_count < out_cap; i++) {
        Quadray diff = h.pool[i].position - center;
        RationalSurd q = diff.quadrance();
        if (!rs_lt(q_radius, q)) {  // q ≤ q_radius
            out[(*out_count)++] = i;
        }
    }
}

// ── BRAM tier for a cell ──────────────────────────────────────────────────
// Determine which memory tier a cell belongs to based on its effective
// weight (Nguyen weight + pressure) vs the total hierarchy weight.
inline BramTier hex_cell_tier(const HexHierarchy& h, uint16_t idx) {
    if (idx >= h.count) return BramTier::PSRAM;
    RationalSurd eff  = h.pool[idx].weight + h.pool[idx].pressure;
    RationalSurd root_w = h.pool[h.root].weight;
    if (root_w.is_zero()) return BramTier::PSRAM;

    // 4 × eff ≥ root_w → BRAM18
    RationalSurd eff4{eff.p * 4, eff.q * 4};
    if (!rs_lt(eff4, root_w)) return BramTier::BRAM18;
    RationalSurd eff13{eff.p * 13, eff.q * 13};
    if (!rs_lt(eff13, root_w)) return BramTier::SDRAM;
    return BramTier::PSRAM;
}

// ── Print helpers ──────────────────────────────────────────────────────────
inline void hex_print_cell(const HexHierarchy& h, uint16_t idx, int indent = 0) {
    if (idx >= h.count) return;
    const HexCell& c = h.pool[idx];
    const char* tier_name[] = {"BRAM18", "SDRAM ", "PSRAM "};
    BramTier t = hex_cell_tier(h, idx);
    for (int i = 0; i < indent; i++) printf("  ");
    printf("[%3u] depth=%u  W=(%3d,%d√3)  P=(%3d,%d√3)  %s  children=%u\n",
           (unsigned)idx, (unsigned)c.depth,
           (int)c.weight.p,   (int)c.weight.q,
           (int)c.pressure.p, (int)c.pressure.q,
           (int)t < 3 ? tier_name[(int)t] : "???",
           (unsigned)c.child_count);
    for (int i = 0; i < c.child_count; i++)
        hex_print_cell(h, c.children[i], indent + 1);
}

inline void hex_print(const HexHierarchy& h) {
    printf("HexHierarchy: %u cells\n", (unsigned)h.count);
    hex_print_cell(h, h.root, 0);
}

#endif // SPU_HEX_HIERARCHY_H
