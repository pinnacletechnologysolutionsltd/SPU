# Laminar UI Manager — Sovereign Desktop Architecture

## Core Concept

In a "Cubic" OS, a window is a fixed rectangle (x, y, w, h).
In a **Laminar OS**, a window is a **Rational Wedge** of the total system weight.

The desktop IS the Vector Equilibrium (VE). Every visible element is a Quadray
sector. The window manager is the Davis Gate.

## The LaminarNode Tree (mapped to Manifold13)

Nguyen's `W(v) = 1 + Σ W(child_i)` maps directly to our Q(√3) implementation:

```cpp
// Nguyen (Cubic bridge — uint64, approximate):
uint64_t calculateTotalWeight() {
    uint64_t total = self_weight;
    for (auto child : children) total += child->calculateTotalWeight();
    return total;
}

// Laminar (Q(√3) — exact, zero-drift, already in spu_ivm.h):
RationalSurd laminar_weight(const Manifold13& m);
// axis_weight(qr[i]) = qr[i].quadrance() — the "truth" of one sector
```

The LaminarNode tree IS the Manifold13. Each child is a QR[i] axis.
The recursive sum is laminar_weight(). No rewrite needed — it's done.

## The Elastic Desktop

| Concept | Implementation |
|---------|---------------|
| Active window (focused process) | QR[i] with highest axis_weight → largest wedge_fraction → BRAM18 tier |
| Background app | Low axis_weight → SDRAM/PSRAM tier → wedge collapses toward nucleus |
| Window edge snap | Pell Octave boundary — edges are always RationalSurd values, never sub-pixel |
| Window resize | Recompute wedge_fraction(m, i) after updating QR[i] — O(13) exact |
| Multi-window balance | Davis Gate ΣABCD == 0 check → VE equilibrium across all windows |

## The Inhale UI Protocol

The SPU-13 only needs the `Total Weight` of a branch to decide rendering priority:

```
if (wedge_fraction(m, i).numer > RENDER_THRESHOLD)
    render_full(window_i);        // BRAM18 tier — deferred rendering
else
    render_shim(window_i);        // PSRAM tier — skeleton only
```

`RENDER_THRESHOLD` is a RationalSurd comparison (rs_lt) — zero float, zero drift.
This is **hardware-level semantic zooming**: the ALU only "exhales" pixels for
branches with enough weight to be visible.

## The 60° Advantage

### Natural Grouping
Apps cluster in Hex-Cells, not folder trees. The hex-hierarchy (Arlinghaus)
provides the spatial index; the weight tree provides the priority index.
Both share the same Q(√3) coordinate system.

### Flow-Based Navigation  
No "click and drag in straight lines." Navigation follows weight gradients —
you flow toward high-weight sectors (currently active manifold state) and
away from low-weight (background). This is the skate "line": finding the natural
path through the weight landscape.

### Jitterbug Work/Leisure Mode

The Jitterbug transformation IS the work/leisure toggle:

```
Work mode  → VE expanded (cuboctahedron)
              all 12 axes active, full laminar_weight, large wedges
              implemented by jitterbug_step(m, 0)  — phase = 0

Leisure mode → Octahedron contracted
               6 axes active, weight halved, wedges contracted
               implemented by jitterbug_step(m, t) — phase = max
```

The Davis Gate monitors this transition. If ΣABCD ≠ 0 during transition
(cubic leak — the app is "fighting" the mode switch), Henosis fires and
the transition pauses until manifold tension resolves.

## Window Types

| Type | Geometry | Use case |
|------|----------|----------|
| **Rectangular Shim** | Standard (x,y,w,h) | Legacy app compatibility — runs inside a wedge container |
| **Simplex Window** | 60° Laminar Manifold | Native SPU-13 app — interface IS the manifold sector |
| **Hex Tile** | IVM_FACE_6 projection | Hex-hierarchy LOD panel — scales with Pell zoom |

Both types can coexist. The Shim is a `bram_tier(wf) == PSRAM` window with a
rectangular clipping region inside the rational wedge container.

## Implementation Path

1. `spu_ivm.h` (done): `laminar_weight()`, `wedge_fraction()`, `bram_tier()` — the engine
2. `spu_physics.h` (next): `jitterbug_step()` — work/leisure transition
3. `software/demos/davis_monitor/` — first visible demo of weight table + tier map
4. Later: `LaminarWindowManager` class — wraps Manifold13, maps to screen coords via hex_project()

## The Sovereign Question

Simplex-Windows are the target. Rectangular Shims are the compatibility bridge.

The migration path for a developer:
1. Start: rectangular app runs inside a wedge container (Shim)
2. Adopt: app exposes `laminar_weight()` hook → becomes weight-aware
3. Native: app IS a Manifold13 sector — interface geometry is the data geometry

## Connection to Hardware

On the Tang 25K:
- `bram_tier()` determines synthesis-time memory placement
- High-weight sectors mapped to BRAM18 (1-cycle, synchronous)
- Low-weight sectors mapped to SDRAM (8-cycle burst)
- The `wedge_fraction()` ratio IS the register bit-depth allocation for the 832-bit bus

The UI and the hardware speak the same language.

## References
- Nguyen, Q.V. — Space-Efficient Visualisation of Large Hierarchies (SpaceTree)
- Arlinghaus, S.L. — Hexagonal Hierarchies, Geometric Visualization
- Fuller, R.B. — Synergetics: Vector Equilibrium, Jitterbug Transformation
- Wildberger, N.J. — Rational Trigonometry: Spread, Quadrance
