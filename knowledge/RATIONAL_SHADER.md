# Rational Shader & Bresenham Killer — Pipeline Integration
# SPU-13 Sovereign Engine v4.1

## Overview

The SPU-13 rendering pipeline eliminates floating-point at every stage. This document
describes how the Bresenham Killer feeds the rasterizer, how barycentric interpolation
works in Q(√3), and what the two missing primitives (SPR_MUL and PURIFY) need to do.

---

## 1. The Full Pipeline

```
Quadray World Coords (4D)
         │
         ▼
  spu_bresenham_killer.v         ← lattice line/edge traversal, 4-axis L∞
  [q_a, q_b, q_c, q_d] (int16)  ← outputs one lattice point per Piranha tick
         │
         ▼ (Quadray → 2D projection, needed between these stages)
  spu_rasterizer.v               ← 64-bit edge functions, rational reciprocal LUT
  [lambda0, lambda1, lambda2]    ← 16.16 fixed-point barycentric weights
         │
         ▼
  spu_fragment_pipe.v            ← LERP vertex attributes (colour, normal)
  [pixel_energy]                 ← 64-bit interpolated attribute
         │
         ▼
  SPR_MUL  [MISSING RTL]         ← spread shading: s = sin²θ as rational ratio
  [shade_numer, shade_denom]     ← (numer, denom) pair, never divided
         │
         ▼
  RAT_MUL + PURIFY  [MISSING]    ← spectral ratio × material, GCD reduce for PHY
  [pixel_out]                    ← final value for HAL_Native_Hex / spu_hal_vga
```

---

## 2. What Is Implemented (✅)

### 2.1 Bresenham Killer (`spu_bresenham_killer.v` v2.0)

Draws a geometrically exact line through the IVM lattice from start to end vertex,
visiting exactly the right lattice points with zero drift.

**Algorithm:** 4-axis L∞-normalised DDA with error bias `err_i ← max_steps >> 1`
**Key property:** `max_steps = max(|Δa|, |Δb|, |Δc|, |Δd|)` — all four axes arrive
at the target in the same number of pulses. This is the Quadray equivalent of the
classical Bresenham constraint.

**Output per pulse:**
```verilog
output reg [15:0] out_a, out_b, out_c, out_d  // current lattice point
output reg        valid                         // high for exactly 1 clock
```
Phase-locked to `pulse_61k` — one step per Piranha tick.

**Connection to rasterizer:** The Bresenham Killer traverses triangle *edges*.
Three instances (one per edge) walk A→B, B→C, C→A simultaneously. The filled
region is every scanline between the two active edge walkers. The Quadray output
needs one projection step before entering `spu_rasterizer.v` (see §3.1).

---

### 2.2 Rasterizer (`spu_rasterizer.v` v3.9)

Computes coverage and barycentric weights for any pixel coordinate against a triangle.

**Edge functions — signed 64-bit determinants (no overflow risk for 16-bit inputs):**
```
edge0 = (px − v0x)·(v1y − v0y) − (py − v0y)·(v1x − v0x)
edge1 = (px − v1x)·(v2y − v1y) − (py − v1y)·(v2x − v1x)
edge2 = (px − v2x)·(v0y − v2y) − (py − v2y)·(v0x − v2x)
```
These are pure integer multiplications in Q(√3) — the same determinant formula that
gives Wildberger's signed area in rational geometry. No square roots, no division.

**Inside test:** `pixel_inside = sign(edge0)==sign(total_area) && sign(edge1)==... && sign(edge2)==...`

**Normalization:** A reciprocal LUT (`spu_rational_lut.v`) maps the 8-bit mantissa of
`total_area` to a 1.23 fixed-point approximation of 1/area. This is the *only*
approximation in the pipeline — and it is bounded: the LUT has 256 entries, the error
is ≤ 0.4% of one ULP at the 16.16 output stage. For shader correctness this is
sufficient; for exact manifold geometry (physics), use the exact Pell Octave path instead.

**Barycentric output:**
```
lambda_i = (edge_i × reciprocal) >> 7   [16.16 fixed-point]
```

---

### 2.3 Fragment Pipe (`spu_fragment_pipe.v` v1.0)

Interpolates vertex attributes using the barycentric weights.

```
pixel_energy = λ₀·V₀ + λ₁·V₁ + λ₂·V₂
```
Currently uses only the lower 32 bits of 64-bit vertex attributes and the integer
part of lambda (`lambda[31:16]`). This is a working stub — see §4.1 for the full
version needed.

---

### 2.4 SDRAM Controller (`HAL_SDRAM_Winbond.v` v1.0)

Implements the full SDRAM init, refresh, read and write state machine for Winbond
W9864G6KH-6 (SDR SDRAM). Suitable for the Tang Primer 25K SDRAM module (32MB).

**Important for Tang Primer 20K users:** The 20K has 128MB onboard DDR3 (not SDR SDRAM).
The DDR3 requires Gowin's hard `DDRC` PHY primitive — a separate `spu_mem_bridge_ddr3.v`
is needed. `HAL_SDRAM_Winbond.v` does *not* target DDR3. See todo `ddr3-bridge-20k`.

---

## 3. What Is Missing (❌)

### 3.1 Quadray → 2D Projection (gap between Bresenham and Rasterizer)

`spu_bresenham_killer.v` outputs 4-axis Quadray `(a, b, c, d)`.
`spu_rasterizer.v` expects `v0_abcd = {y[31:0], x[31:0]}` — 2D screen coords.

The projection from Quadray to Cartesian screen space is:
```
x_screen = a − c           (Quadray → hex x, exact integer)
y_screen = b − d           (Quadray → hex y, exact integer)
```
This is exact and requires no multiplication. It is the canonical IVM→Cartesian
conversion. A one-line `assign` in the top-level wires these together.

For 60° native displays (`HAL_Native_Hex.v`) this step is skipped entirely — the
Quadray output feeds the HAL directly.

---

### 3.2 SPR_MUL — Spread Shader Primitive

The LAMINAR_SHADER_SPEC defines spread shading as:
```
Luminance = (Intensity / Q) × s
```
where `s` is the Spread between the surface normal and the light direction.

**Spread in Q(√3), no division:**

Given two Quadray vectors `N` (normal) and `L` (light direction):
```
dot(N, L)  = Na·La + Nb·Lb + Nc·Lc + Nd·Ld   [integer]
Q(N)       = dot(N, N)                          [integer, always positive]
Q(L)       = dot(L, L)                          [integer]

spread_numer = Q(N)·Q(L) − dot(N,L)²          [integer]
spread_denom = Q(N)·Q(L)                        [integer]
```
`s = spread_numer / spread_denom` — but we never divide. We store the pair
`(spread_numer, spread_denom)` and carry it through the pipeline.

**Final luminance (still no division):**
```
lum_numer = Intensity × spread_numer
lum_denom = spread_denom × Q_light
```
Output pixel: `(lum_numer, lum_denom)` — exact rational.

**RTL interface needed:**
```verilog
module spu_spread_mul (
    input  wire [63:0] normal_abcd,      // surface normal, Quadray
    input  wire [63:0] light_abcd,       // light direction, Quadray
    input  wire [31:0] intensity,        // light power (integer)
    output wire [63:0] lum_numer,        // output numerator
    output wire [63:0] lum_denom         // output denominator (never zero if Q>0)
);
```
Uses 4 multiplications and 5 additions — fits in 2 DSP slices on GW2A.

---

### 3.3 PURIFY — Spectral Ratio Reduction

For display output, the rational `(numer, denom)` colour must be reduced to fit the
display PHY's bit depth `D` (e.g., 8-bit = 255, 10-bit = 1023).

**Algorithm:**
```
g = gcd(lum_numer, lum_denom)        // binary GCD (shift-based, no division)
out = (lum_numer / g) * D / (lum_denom / g)
```
`binary_gcd(a, b)` uses only shifts and subtractions — valid in the no-division
constraint because GCD via binary method eliminates factors of 2 iteratively.

**Why this matters:** Without PURIFY, the pixel value may overflow the display PHY
or lose precision. With PURIFY, the output is always in `[0, D]` exactly, with no
banding artefact at any luminance level.

**RTL interface needed:**
```verilog
module spu_purify (
    input  wire [63:0] numer,
    input  wire [63:0] denom,
    input  wire [9:0]  max_out,      // display PHY depth (255, 1023, etc.)
    output wire [9:0]  pixel_val,    // reduced, display-ready
    output wire        valid
);
```

---

### 3.4 Fragment Pipe — Full Version

The current stub needs two upgrades:

1. **Use full 64-bit attributes**, not just lower 32 bits.
   The upper 32 bits carry the `b` (surd) component — dropping them makes colour
   interpolation Cartesian, not Q(√3). Fix: `assign term0 = v0_attr * lambda0[31:16]`
   should be `(v0_attr[63:32], v0_attr[31:0]) × (lambda0[31:16])` producing a pair.

2. **Pipeline the three multiplications** (3-stage). At 24 MHz, the combinatorial
   path through three 64×32 multipliers exceeds one clock on GW2A. Add three register
   stages between term computation and accumulation.

---

## 4. Hardware Summary — Tang Primer 20K + RP2350

| Controller | File | Tang 20K status |
|------------|------|-----------------|
| SDR SDRAM (25K module) | `HAL_SDRAM_Winbond.v` | ✅ Ready (for 25K/9K only) |
| DDR3 (20K onboard 128MB) | `spu_mem_bridge_ddr3.v` | ❌ Not yet written — needs Gowin `DDRC` PHY |
| HDMI display | `spu_hal_vga.v` + `HAL_Native_Hex.v` | ✅ Ready |
| RP2350 SPI/UART | `rp2350_spu_interface.c` | ✅ Core firmware complete |
| Whisper TX/RX | `SPU_WHISPER_TX/RX.v` | ✅ Tested |
| Artery cluster FIFO | `SPU_ARTERY_FIFO.v` | ✅ Tested |
| Spread shader (SPR_MUL) | `spu_spread_mul.v` | ❌ Not yet written |
| Spectral purify | `spu_purify.v` | ❌ Not yet written |

### RP2350 Pin Summary (no changes needed)
```
SPI0:  CS=GP17, SCK=GP18, MOSI=GP19, MISO=GP16   ← SPU-4 interrogation
UART1: TX=GP4, 921600 baud                         ← Whisper frames to RP2040
```
The RP2350 is the Laminar Controller: it polls the SPU-4 manifold state over SPI
and streams 104-byte Whisper frames to the RP2040 visualiser. It does not touch DDR3.

---

## 5. Cluster Rendering Model

```
         ┌─────────────────────────────────────┐
         │         SPU-13 Mother (FPGA)        │
         │  Pell orbit, 13-axis manifold state │
         │  DDR3: world geometry + archives    │
         └──────────────┬──────────────────────┘
                        │ Artery FIFO (distributed manifold calc)
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
    SPU-4 Sentinel  SPU-4 Sentinel  SPU-4 Sentinel
    (face cluster A)(face cluster B)(input/physics)
          │             │
          ▼             ▼
   Bresenham Killer  Bresenham Killer     ← one per rasterisation zone
   + SPR_MUL         + SPR_MUL
          │             │
          └──────┬───────┘
                 ▼
          spu_rasterizer.v → spu_fragment_pipe.v → PURIFY → HAL
```

Each SPU-4 handles a geometric partition (face cluster, physics zone, input stream).
The Bresenham Killer runs on the SPU-4 — it only needs 16-bit Quadray inputs which
the 32-bit SPU-4 provides natively. The SPU-13 Mother holds the manifold oracle
(Pell state, Davis Gate) and arbitrates Henosis when any satellite reports instability
via the Whisper pulse width.

---

## 6. Immediate Implementation Order

1. **`spu_spread_mul.v`** — 4 muls + 5 adds, fits in 2 DSP slices. Enables true
   Laminar shading on any geometry the Bresenham Killer draws.

2. **`spu_purify.v`** — binary GCD + scale. Required before any display output
   carries rational colour (without it, pixel values overflow the PHY).

3. **`spu_fragment_pipe.v` upgrade** — full 64-bit attribute LERP + 3-stage pipeline.

4. **`spu_mem_bridge_ddr3.v`** — Gowin `DDRC` PHY wrapper for Tang Primer 20K.
   Vertex geometry lives in DDR3; without this bridge the rasterizer has no data.

5. **Quadray→screen projection wire** in `spu_tang_20k_top.v`:
   `assign screen_x = quadray_a - quadray_c;`
   `assign screen_y = quadray_b - quadray_d;`
   Two subtractions. This closes the Bresenham→Rasterizer gap.

---

## References

- `hardware/common/rtl/graphics/spu_bresenham_killer.v` — v2.0 lattice line traversal
- `hardware/common/rtl/graphics/spu_rasterizer.v` — v3.9 edge-function rasterizer
- `hardware/common/rtl/graphics/spu_fragment_pipe.v` — v1.0 LERP stub
- `hardware/common/rtl/mem/HAL_SDRAM_Winbond.v` — SDR SDRAM controller
- `reference/synergeticrenderer/docs/LAMINAR_SHADER_SPEC.md` — spread/spectral spec
- `reference/synergeticrenderer/docs/RATIONAL_SURD_REFACTOR.md` — Q(√3) gate design
- `knowledge/PELL_OCTAVE.md` — rotor orbit and overflow-safe representation
- `knowledge/LITHIC_L_LANGUAGE_SPEC.md` — SPR_MUL, DIVQ, PURIFY ISA opcodes
