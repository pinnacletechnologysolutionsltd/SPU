**Roles:**
- **Spec Author:** Claude (architecture + oracle prototype)
- **Halt-and-Flag Implementer:** unassigned (RTL not yet authorized — see §5)
- **Integration Auditor:** `bash tools/verify_repo.sh`

---

# Engineering Contract: GPU Reciprocal Unit (Scoping)
**Date:** 2026-08-25
**Contract ID:** `contract_gpu_reciprocal_scoping_2026-08-25.md`
**Status:** DRAFT

## 0. Why this exists
Per [[spu13-gpu-rasterizer-audit-2026-08-24]]: current rasterizer
coverage (`spu_edge_stepper.v`) needs no division. A flat depth-v1 (one
depth value per triangle) also needs none. Real per-pixel depth/texture
interpolation does — the barycentric weights are the three edge-function
values divided by their sum (twice the triangle's signed area). The
shipped RPLU/Padé reciprocal (`rplu_thimble_pade.v`) is confirmed
A31-field-specific (routes through "an A31 inverter"), not reusable
here. `pade_eval_4_4.v` in `hardware/rtl/gpu/` uses a bare Verilog `/`
but is **not instantiated anywhere** — dead code, and would violate
AGENTS.md §3.1 (no division in RTL) if it were live. This contract
scopes a generic, multiply-only fixed-point reciprocal core instead.

## 1. Objective & Scoped Files
* **Prototype (built this session, software-only, no hardware claim):**
  - `software/lib/gpu_reciprocal_oracle.py` — independent bit-exact
    model: normalize → LUT initial estimate → 1 Newton-Raphson iteration
    → denormalize. No `/` operator in the modeled runtime path (the LUT
    generator uses a float divide, generation-time only, same convention
    as `tools/generate_pade_44.py`).
* **Target files to create if/when RTL is authorized (NOT yet in scope):**
  - `hardware/rtl/gpu/spu_reciprocal_core.v` (Lithic, ≤150 lines)
  - `hardware/tests/gpu/spu_reciprocal_core_tb.v`
* **Existing domain evidence used to size this:**
  - `hardware/rtl/gpu/spu_edge_stepper.v`: edge coefficients `a,b` are
    16-bit signed, accumulator `f` is 32-bit signed. Confirms the real
    denominator (twice triangle area) is bounded to roughly 25 bits for
    a 640×480 screen, not the full 32-bit range.

## 2. Architecture (no division; core arithmetic is multiply-only)
1. **Normalize:** find the denominator's leading-1 bit position (a
   priority encoder / leading-one detector — real combinational logic,
   not free; for the ~25-bit domain from §1 this is a small tree, but
   it's on the critical path if done in one cycle and should be sized/
   pipelined deliberately, not assumed away) and barrel-shift so that
   bit lands at a fixed position, producing a fixed-width mantissa. The
   *shift itself* is exact (no rounding), so only the mantissa-domain
   core below needs error characterization — but the leading-one
   detector is a real piece of hardware this contract has not yet sized.
2. **LUT initial estimate:** table-bits index (top bits below the
   implicit leading 1) into a ROM of precomputed reciprocal estimates,
   one per bucket midpoint.
3. **One Newton-Raphson refinement:** `y1 = y0 * (2 - d*y0)`, pure
   multiply/subtract/shift, fixed point throughout.
4. **Denormalize:** barrel-shift the result back (exact).

**Correction from initial draft:** step 3 is NOT a drop-in reuse of
`rplu_poly_step.v`. That module is a single multiply-then-*add*-a-
coefficient MAC (`(acc_in*x_q32)>>>32 + coef_q32`, one multiply per
step). The NR update needs two sequential multiplies (`d*y0`, then
`y0*err`) with a subtraction-from-a-constant between them — a different
dataflow, even though both ultimately bottom out in the same primitive
building blocks (a fixed-point multiplier and an adder/subtractor). A
future implementer should budget for a purpose-built 2-multiply NR
datapath, not assume `rplu_poly_step.v` slots in unmodified.

## 3. Exhaustive characterization (software oracle, run 2026-08-25)
16-bit mantissa domain (`d` in `[2**15, 2**16)`), exhaustive sweep — every
value, not sampled, per [[bench-evidence-discipline]]:

| LUT index bits | ROM entries | max abs error (ULP) | max rel error | effective correct bits |
|---|---|---|---|---|
| 4 | 16 | 61.00 | 9.3e-4 | ~10.1 |
| 6 | 64 | 4.75 | 7.4e-5 | ~13.7 |
| **8** | **256** | **1.20** | **3.1e-5** | **~15.0** |
| 10 | 1024 | 1.01 | 3.1e-5 | ~15.0 |

**8-bit index (256×16-bit ROM ≈ 4 Kbit) + 1 NR iteration already
saturates the 15-bit output word's own precision ceiling** — going to
1024 entries buys nothing, the bottleneck becomes the output format, not
the algorithm. This is a cheap, small design point (well inside Tang
25K's already-tight budget, see [[tang25k-capacity-ceiling]]) — no need
to spend more LUT area than 256 entries for this precision target.

The ROM's contents are generated once by `build_lut()` (a Python float
divide, generation-time only) and then frozen — every row above comes
from the exhaustive sweep exercising those *frozen* integer constants
through `reciprocal_core()`, which never calls `/`. The float divide
never appears in the hardware or runtime path; it is exactly the
`generate_pade_44.py`-style convention, not an exception to the no-
division rule.

## 3b. Consumer shape changes the timing budget (2026-08-25 addendum)
This reciprocal is shared infrastructure for the eventual interpolated
rasterizer, not a texture-specific feature — don't design its interface
around one consumer prematurely. But the two candidate consumers have
very different area/timing implications for §2 point 1's leading-one
detector:

- **Affine interpolation:** the denominator (`F0+F1+F2`, twice the
  triangle's signed area) is constant across the whole triangle. Its
  reciprocal is computed **once at triangle setup**, then every pixel's
  barycentric weight is `w_i = F_i * inv_denom` — a multiply against
  arithmetic already present (the edge-function values), not a divide.
  The leading-one detector therefore does NOT need to be in the
  per-pixel critical path for this consumer — it can take several
  cycles during the same setup phase that already computes edge
  coefficients.
- **Perspective-correct interpolation:** genuinely needs one reciprocal
  *per pixel* — but only one, at the end: interpolate `attribute/w` and
  `1/w` linearly (cheap incremental adds, same shape as
  `spu_edge_stepper.v`'s accumulator), then a single reciprocal-and-
  multiply per pixel recovers the true attribute. Not an open-ended
  per-pixel cost, but a real one, unlike the affine case.

**Recommended next concrete step (not yet started):** scope a minimal
"depth-v2: affine-interpolated depth" consumer — the smallest real step
up from flat depth-v1 that still only needs the cheap, setup-time
reciprocal, not perspective-correct's harder per-pixel budget. That
consumer would pin down the actual denominator range and required
output precision against a real use case, resolving §4's open items
with evidence instead of guessing them in the abstract. Perspective-
correct texture mapping would be its own later contract once affine
interpolation exists and works.

## 4. Open decisions — RESOLVED 2026-08-25 by `contract_gpu_depth_v2_scoping_2026-08-25.md`
- [x] **What precision does the actual consumer need?** depth-v2
  (affine-interpolated depth) confirmed as the first consumer;
  `OUT_FRAC_BITS=15` is sufficient — sub-2-unit error out of a 65536
  depth range across representative triangles. Texture/perspective-
  correct interpolation remains a separate, later question (harder,
  genuine per-pixel reciprocal — see addendum 3b).
- [x] **Full input range.** Confirmed 16–25 bit denominators (640×480
  screen) all hold ~15 correct bits end-to-end, INCLUDING the real
  mantissa-truncation error the normalize stage introduces that this
  contract's original "exact shift" framing missed — see depth-v2 §2
  for the correction and the exhaustive worst-case sweep across that
  range.
- [x] **Iteration count.** Still 1 — depth-v2 surfaced no evidence a
  second iteration would change the depth-ordering outcome.

RTL is still NOT authorized (see §5) — depth-v2's own contract flags a
new, previously-unbudgeted cost (40+ bit intermediate registers for
`A_z/B_z/C_z`) that should factor into any future go/no-go, not just
the precision questions this section originally blocked on.

## 5. Stop Conditions
- **RTL implementation is NOT authorized by this contract** — it is a
  scoping/characterization pass only. Halt before writing
  `spu_reciprocal_core.v` until §4's open decisions are resolved.
- If a future oracle-vs-RTL parity run (once RTL exists) shows an error
  outside this characterized envelope, HALT and flag — do not silently
  add iterations or widen the LUT to paper over it.
