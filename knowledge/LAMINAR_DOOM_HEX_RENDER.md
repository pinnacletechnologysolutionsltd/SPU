# Laminar-Doom: Hex-Hierarchy Render Graph and Engine Mapping

**References:**
- Arlinghaus, S.L. "Geometric Visualization of Hexagonal Hierarchies: Animation
  and Virtual Reality" (Solstice: An Electronic Journal of Geography and
  Mathematics)
- Arlinghaus, S.L. *Spatial Mathematics: Theory and Practice Through Mapping*
- See also: `ARLINGHAUS_SPATIAL_SYNTHESIS.md`

---

## 1. Core Insight: The Render Graph IS the Davis Hierarchy

Traditional render graphs (Unreal, Unity SRP, Vulkan frame graphs) organise
passes as a DAG to minimise barriers and state transitions. In Laminar-Doom,
the DAG structure is not separate from the physics — it *is* the hex
hierarchy. The same `ΣABCD == 0` laminar check that enforces physics
stability also determines:

- Which cells are stable (culled from tension passes)
- Which cells are undergoing Henosis (need a spread-shading update pass)
- Which cells have cubic leaks (trigger LOD fracture / destructible geometry
  pass)

The render graph is driven by the physics state. No separate culling system.
No separate LOD manager. One hierarchy, one stability check, three outcomes.

```
HexHierarchy state → Render pass selection
  LAMINAR      → skip tension pass, use cached colour
  HENOSIS      → enqueue SpreadShading pass for this cell + neighbours
  CUBIC-LEAK   → enqueue FractureGeometry pass, propagate to parent
```

---

## 2. HexCell Data Structure (C++)

The fundamental node of the hierarchy. Designed to map directly onto the
`Manifold13` register file and `DavisGasket` struct from `spu_physics.h`.

```cpp
// spu_hex_hierarchy.h — Hex-hierarchy spatial engine for Laminar-Doom

#pragma once
#include "spu_quadray.h"
#include "spu_physics.h"

// IVM neighbourhood: hex center + 6 equidistant neighbours = 7 cells.
// At the cuboctahedral level (LOD 2), this is 12 vertices + center = 13
// — matching the SPU-13 Manifold axis count exactly.
constexpr int HEX_CHILD_COUNT = 7;   // micro/meso
constexpr int CUBO_CHILD_COUNT = 13; // macro (full cuboctahedron)

enum class HexState : uint8_t {
    LAMINAR     = 0,  // ΣABCD == 0, stable
    HENOSIS     = 1,  // ΣABCD != 0, recovery in progress
    CUBIC_LEAK  = 2,  // recovery failed, fracture propagating
    RECOVERED   = 3,  // post-Henosis, returning to laminar
};

struct HexCell {
    Quadray       center;            // IVM position in Q(√3)⁴
    RationalSurd  edge_len;          // Pell Octave level: (2,1)^n · unity
    int           lod_level;         // 0=micro, 1=meso, 2=macro
    DavisGasket   gasket;            // local τ, K, C = τ/K
    RationalSurd  davis_sum;         // ΣABCD for this cell
    HexState      state;
    HexCell*      parent;            // null at root
    HexCell*      children[13];      // up to 13 (macro) or 7 (meso/micro)
    int           child_count;

    bool is_laminar()    const { return state == HexState::LAMINAR; }
    bool needs_render()  const { return state != HexState::LAMINAR; }
};

// The full hierarchy root — one per environmental macro-region
struct HexHierarchy {
    HexCell* root;
    int      max_depth;      // typically 3: macro→meso→micro
    int      total_cells;

    // Tick: update all gaskets bottom-up, propagate leaks upward
    void tick();

    // Query: return all cells within Quadrance radius of point p
    // Exact — uses Quadrance comparison, no sqrt
    void query_radius(const Quadray& p, const RationalSurd& q_radius,
                      HexCell** results, int& count) const;

    // Render hint: fill 'dirty' list with cells needing pass updates
    void collect_dirty(HexCell** dirty, int& count) const;
};
```

**Why `edge_len` uses the Pell Octave:**
The Pell recurrence `a_{n+1} = 2a_n + b_n`, `b_{n+1} = a_n + b_n` generates
the exact scale progression for hex-net LOD without ever leaving Q(√3). Each
LOD level is a Pell step:

| LOD | edge_len (p,q) | Real value approx |
|-----|---------------|-------------------|
| 0   | (1, 0)        | 1.0 (micro)       |
| 1   | (2, 1)        | 3.73 (meso)       |
| 2   | (7, 4)        | 13.93 (macro)     |
| 3   | (26, 15)      | 51.98 (env chunk) |

Scale ratios stay rational. No floating-point LOD transitions.

---

## 3. Render Graph Pass Structure

```
Frame N:
  ┌─ Pass 1: HexHierarchyUpdate (Compute)
  │   Dispatch: one workgroup per macro-cell
  │   Threads:  one thread per meso-cell (7 per macro)
  │   Work:     update DavisGasket, compute ΣABCD, set HexState
  │   Output:   dirty cell list (SSBO)
  │
  ├─ Pass 2: TensionPropagation (Compute)
  │   Input:    dirty cell list
  │   Work:     propagate CUBIC_LEAK upward; trigger HENOSIS on neighbours
  │   Output:   updated HexState per cell
  │
  ├─ Pass 3: SpreadShading (Compute → Texture)
  │   Input:    cells with state != LAMINAR
  │   Work:     map Davis Ratio C to colour via rational colour ramp
  │             (see ARLINGHAUS_SPATIAL_SYNTHESIS.md §4 for thresholds)
  │             Uses SPR_MUL spread shading — integer multiply only
  │   Output:   tension overlay texture
  │
  ├─ Pass 4: FractureGeometry (Compute → Geometry)
  │   Input:    cells with state == CUBIC_LEAK
  │   Work:     generate fracture quads/tris along lattice bond axes
  │             break bond at Quadray neighbour offset
  │   Output:   dynamic geometry buffer
  │
  └─ Pass 5: HexRasterize (Graphics)
      Input:    geometry buffer + tension overlay
      Work:     HAL_Native_Hex scanout or Cartesian projection
                Rational barycentric interpolation per hex cell
      Output:   framebuffer
```

Passes 1–4 are compute only. Pass 5 is the only graphics pass. On the
RX 550 this is a natural fit — AMD's RDNA compute queue handles passes 1–4
while the graphics queue handles pass 5 asynchronously.

---

## 4. Engine Mapping: Hex World vs. Cubic Scene Graph

### Classical approach (cubic)
```
SceneNode (transform: 4×4 float matrix)
  ├── MeshNode
  ├── LightNode
  └── PhysicsBody (AABB in float coords)
```
Every transform accumulates float error. LOD boundaries are arbitrary.
Collision queries use square Euclidean distance (requires sqrt).

### Laminar-Doom hex approach
```
HexCell (center: Quadray, edge_len: RationalSurd, gasket: DavisGasket)
  ├── geometry: bond list (Quadray offsets, exact)
  ├── material: tension: RationalSurd, fracture_threshold: RationalSurd
  └── children: HexCell[7 or 13]
```
No float matrices. No sqrt in collision. LOD boundaries at Pell Octave
steps. Fracture along lattice bonds — not arbitrary axis-aligned splits.

### Compatibility layer
For legacy Cartesian output (monitor display, Vulkan swapchain):

```cpp
// Project Quadray → XYZ float (display only — math stays rational)
glm::vec3 quadray_to_xyz(const Quadray& q) {
    // IVM basis: e1=(1,-1,0,0), e2=(0,1,-1,0), e3=(0,0,1,-1) in Cartesian
    // This conversion is the ONLY float operation in the pipeline.
    float a = q.a.to_float(), b = q.b.to_float(),
          c = q.c.to_float(), d = q.d.to_float();
    return { a-b, b-c, c-d };
}
```

One float conversion per vertex, at the boundary to the display HAL.
All physics, collision, and LOD logic upstream of this stays exact.

---

## 5. Animated Propagation: Debug Visualisation

Arlinghaus's VR/animation work focused on *watching hierarchies evolve* as
a way to understand spatial structure. In Laminar-Doom this becomes a first-
class debug feature:

**Davis ripple visualisation:**
When an impact seeds a micro-cell CUBIC_LEAK, the propagation through the
hierarchy is animated:
1. Micro-cell: flashes RED (CUBIC_LEAK)
2. Meso-parent: turns YELLOW (HENOSIS) for N frames
3. If recovered: fades to CYAN then GREEN
4. If not recovered: macro-parent turns RED (cascade failure = chunk break)

The animation timing is Fibonacci-gated (same as the hardware dispatch):
frames at 8, 13, 21 ticks. This is not a visual trick — it is the actual
Henosis recovery window expressed as screen frames.

```cpp
// Visualisation tick — maps to Fibonacci pulse
void davis_ripple_tick(HexHierarchy* h, int frame) {
    bool phi8  = (frame % 8  == 0);
    bool phi13 = (frame % 13 == 0);
    bool phi21 = (frame % 21 == 0);

    if (phi8)  h->tick();              // micro-cell gasket update
    if (phi13) h->propagate_meso();    // meso aggregation
    if (phi21) h->propagate_macro();   // macro decision: Henosis or fracture
}
```

---

## 6. Integration with SPU-13 Hardware (Future)

When the GW5A-LV25 arrives, the hex-hierarchy update pass (Pass 1 above)
moves from compute shader to FPGA:

| Software (now)        | Hardware (FPGA)                     |
|-----------------------|-------------------------------------|
| `HexHierarchy::tick()`| SPU-13 TDM ALU, 13-axis manifold    |
| `DavisGasket::tick()` | `davis_gate_dsp.v`                  |
| `henosis_pulse()`     | Henosis soft-recovery pulse (RTL)   |
| Fibonacci dispatch    | `spu_sierpinski_clk.v` 61.44 kHz    |
| Davis Ratio → colour  | Whisper PWI telemetry → RP2040      |

The software hex-hierarchy is the emulator of the hardware pipeline. When the
board is programmed, the FPGA handles passes 1–2 and streams results to the
GPU via Whisper/Artery. Passes 3–5 stay on GPU.

---

## 7. Immediate Action Items

1. **`spu_hex_hierarchy.h`** — implement `HexCell`, `HexHierarchy::tick()`,
   `query_radius()` (depends on `spu_quadray.h`, `spu_physics.h`)
2. **Davis ripple demo** — extend `davis_monitor/main.cpp` with ASCII
   hex-grid visualisation of propagation
3. **Compute shader prototype** — single Vulkan compute pass for
   `HexHierarchyUpdate` on RX 550 (or Metal on macOS)

---

*CC0 1.0 Universal.*
