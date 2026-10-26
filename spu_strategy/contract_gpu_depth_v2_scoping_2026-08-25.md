**Roles:**
- **Spec Author:** Claude (architecture + oracle prototype)
- **Halt-and-Flag Implementer:** unassigned (RTL not yet authorized — see §5)
- **Integration Auditor:** `bash tools/verify_repo.sh`

---

# Engineering Contract: GPU Depth-v2 (Affine-Interpolated Depth) — Scoping
**Date:** 2026-08-25
**Contract ID:** `contract_gpu_depth_v2_scoping_2026-08-25.md`
**Status:** DRAFT

## 0. Why this exists
Per [[spu13-gpu-rasterizer-audit-2026-08-24]] and
`contract_gpu_reciprocal_scoping_2026-08-25.md`'s addendum 3b: rather
than choosing the reciprocal's `OUT_FRAC_BITS` and denominator range in
the abstract, scope the smallest real consumer first. Depth-v2 is that
consumer — affine-interpolated per-pixel depth, one setup-time
reciprocal per triangle, no per-pixel multiply or divide. This
supersedes flat depth-v1 (a single depth value per triangle) as the
next real step, without yet touching perspective-correct texture
mapping's harder per-pixel reciprocal.

## 1. Objective & Scoped Files
* **Prototype (built this session, software-only, no hardware claim):**
  - `software/lib/gpu_depth_v2_oracle.py` — independent bit-exact model:
    vertex→edge coefficients (self-checked against the sum-of-edges=2×area
    identity, not assumed) → full reciprocal of the triangle-area
    denominator (normalize incl. real truncation → LUT → 1 NR iteration →
    denormalize) → setup-time `A_z,B_z,C_z` → pure incremental per-pixel
    accumulation, same shape as `spu_edge_stepper.v`.
* **Target files if/when RTL is authorized (NOT yet in scope):**
  - `hardware/rtl/gpu/spu_attr_stepper.v` (Lithic, ≤150 lines — same
    accumulator shape as `spu_edge_stepper.v` but outputs a value, not
    a boolean)
  - a small setup block computing `A_z,B_z,C_z` from the dot products and
    `spu_reciprocal_core.v` (itself still unauthorized, see the
    reciprocal contract)

## 2. Finding: the reciprocal contract's "exact shift" claim needed a correction
`contract_gpu_reciprocal_scoping_2026-08-25.md` §2 point 1 said the
normalize/denormalize shifts are exact. That's true for denormalizing
the *result*, but normalizing a wide denominator (confirmed up to ~25
bits for 640×480) down to the 16-bit LUT mantissa is a real
right-shift-and-truncate — it discards low bits of the actual
denominator, an error source the earlier 16-bit-mantissa-only sweep
didn't cover.

**Exhaustive worst-case characterization** (every mantissa value, worst-
case truncated bits, per denominator width 16–25 bits):

| denominator width | max rel error | effective correct bits |
|---|---|---|
| 16 bits | 3.11e-5 | 15.0 |
| 17–24 bits | 2.3–3.0e-5 | 15.0–15.4 |
| 25 bits | 3.01e-5 | 15.0 |

**Good news the numbers show, contrary to a naive hand-estimate:**
truncation does not meaningfully degrade precision across the full 16–25
bit range — it stays pinned at ~15 correct bits throughout, matching the
core's own isolated characterization. The 256-entry/1-NR design holds up
end-to-end, not just in the idealized case.

## 3. depth-v2 simulation results
Three representative triangles (screen-corner, thin sliver, near-
degenerate), 16-bit vertex depths (0–65535 range), full pipeline
including the real ~25-bit denominator and setup-time-only reciprocal,
per-pixel path verified to use **only** incremental add + a final shift
(no per-pixel multiply, no per-pixel divide — confirmed by construction
in `simulate_depth_raster()`, not just claimed):

| case | max depth error (16-bit units) | worst pixel |
|---|---|---|
| screen-corner | 1.73 | (592, 30) |
| thin sliver | 1.20 | (609, 27) |
| near-degenerate | 1.28 | (632, 5) |

**Interpretation:** sub-2-unit absolute error out of a 65536-range depth
buffer — good enough for depth ordering except when two surfaces are
already within ~2 units of each other (the same near-coincident/
"z-fighting" case that affects reference float32 GPU pipelines too, not
a defect specific to this design).

**Real cost surfaced, not hidden:** the setup-stage fixed-point
intermediates need wide registers — `frac_bits` (the final right-shift
amount) came out to 33–34 bits in these cases, meaning `A_z/B_z/C_z`
need on the order of 40+ bit registers. This is consistent with, not
worse than, the existing RPLU/Padé infrastructure's own wide
accumulators (`pade_eval_4_4.v` already carries 128–192-bit
intermediates) — not a new category of cost, but a real one to budget
for, not hand-waved.

## 4. Resolves reciprocal contract §4 open items
- **Precision target:** `OUT_FRAC_BITS=15` (the already-characterized
  256-entry/1-NR design) is sufficient for affine depth interpolation —
  confirmed by this consumer, not assumed. No redesign of the reciprocal
  core needed for this consumer.
- **Input range:** confirmed 16–25 bit denominators all hold ~15 correct
  bits; the normalize stage's shift-amount register needs to cover at
  least a 9-bit shift range (25−16) for 640×480.
- **Iteration count:** still 1 — no evidence surfaced here that a second
  NR iteration would change the depth-ordering outcome.

## 4b. Hardware resource accounting (2026-08-25 addendum — real measured data, not a paper estimate)
Grounded against `docs/hardware_evidence.md` §3.6g (Tang 25K GW5A-25A =
23,040 LUT4 total, measured 2026-08-15/16 — this citation is for the
*existing* spins measured there, not a claim about depth-v2 or the
reciprocal, which are unmeasured and unimplemented):

- **`series_stream_probe` hit 70,390 LUT4 = 305% over capacity from a
  single combinational M31 multiplier.** Recorded remedy: "a sequential
  variant or a Gowin DSP wrapper." This is a proven failure mode in this
  exact repo/toolchain, not a hypothetical risk.
- **Every Tang-25K spin using multiply-heavy fixed-point math reports 0
  DSP used** (SOM-SIDECAR: 0 DSP/14,068 LUT4 on Tang vs. 44 DSP/8,013
  LUT on the same design's A7 100T build; RPLU2 arith probe: 6,282
  LUT4=27% on Tang). The Gowin/nextpnr-himbaechel flow this project uses
  is not inferring hardened multiplier primitives for these designs on
  Tang 25K. RPLU2PADE on A7 100T (Xilinx, DSP48 inference works): 72
  DSP, only 34% LUT — comfortable.

**Consequence for depth-v2's setup path** (~14 multiplies: 3 dot
products × 3 terms + 2 NR + 3 final scale by `inv_denom`): implementing
this as a fully-combinational chain — the same shape as
`rplu_poly_step.v`'s `USE_LOCAL_POLY=1` path — targeting Tang 25K would
risk the exact failure mode `series_stream_probe` already hit. The
setup-time-only timing budget (§3b of the reciprocal contract) makes a
**shared, sequential multiplier** (the FSM shape `pade_eval_4_4.v`
already uses in its non-`USE_LOCAL_POLY` path, reusing one multiplier
across all ~14 operations over ~14+ cycles) the correct choice on Tang
25K — not a nice-to-have, a capacity requirement given the proven
history. Targeting A7 100T instead, where DSP inference already works
for this project's RPLU2PADE spin, is the other real option.

**Gap closed 2026-08-25** — see `contract_gpu_raster_synth_probe_2026-08-25.md`.
The coverage path (`spu_edge_stepper.v`/`spu_raster_unit.v`/
`spu_dual_raster.v`, driven by real `spu_video_timing.v` scan) measured
at **1,317/23,040 LUT4 = 5.7% on Tang 25K**, routes clean, 109.82 MHz max.
Zero DSP used — expected, since the coverage path is pure incremental
add with no multiply, so this says nothing about the reciprocal/depth-v2
multiplier logic's own DSP-inference odds. **21,723 LUT4 (94.3%) of
headroom exists** before depth-v2/reciprocal logic is added — comfortable
room even if the sequential-multiplier discipline from §4b isn't
followed perfectly, though it should still be followed given the proven
`series_stream_probe` failure mode.

## 5. Stop Conditions
- **RTL implementation is still NOT authorized** — this is a scoping/
  characterization pass. Both this contract and the reciprocal contract
  it depends on must move to RTL together, since depth-v2's per-pixel
  accumulator only exists to consume the reciprocal core's output.
- Perspective-correct texture mapping (genuine per-pixel reciprocal, not
  setup-time) is explicitly OUT of scope here — its own contract, once
  depth-v2 exists and works.
- If a future RTL parity run shows error outside the envelope in §2/§3,
  HALT and flag — do not silently widen registers or add iterations to
  paper over it.

Related: [[spu13-gpu-rasterizer-audit-2026-08-24]],
`contract_gpu_reciprocal_scoping_2026-08-25.md`.
