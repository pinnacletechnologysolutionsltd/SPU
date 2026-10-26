**Roles:**
- **Spec Author / Implementer / Auditor:** Claude (single-pass — no new
  arithmetic logic is authored here, only a measurement wrapper around
  already-testbench-verified modules; see §2)

---

# Engineering Contract: GPU Rasterizer Coverage — Tang 25K Synthesis Probe
**Date:** 2026-08-25
**Contract ID:** `contract_gpu_raster_synth_probe_2026-08-25.md`
**Status:** COMPLETE — measured 2026-08-25

## RESULT
`bash build_25k_spu13_gpu_raster_probe.sh` — Yosys synth + nextpnr-himbaechel
place/route + gowin_pack all completed clean, no congestion, no timing fail:

| Resource | Used | Total | % |
|---|---|---|---|
| LUT4 | 1,317 | 23,040 | **5.7%** |
| ALU | 538 | 17,280 | 3.1% |
| DFF | 674 | 23,040 | 2.9% |
| MULTALU27X18 / MULTADDALU12X12 (DSP) | 0 | 28 each | 0% |

Max frequency (final reported line, per
[[nextpnr-fmax-estimate-vs-final]]'s take-the-last-line rule): **109.82 MHz**,
comfortably passing the 12 MHz test constraint and the real 25 MHz pixel
clock target. Bitstream packaged (`build/tang_primer_25k_spu13_gpu_raster_probe.fs`)
but **not flashed** — this is a synthesis/PNR area measurement, not a
silicon claim; no `docs/hardware_evidence.md` entry is warranted.

**Zero DSP usage is expected here, not a red flag**: the coverage path
(`spu_edge_stepper.v`) is pure incremental add, no multiply at all — this
number says nothing about how the reciprocal/depth-v2 multiplier logic
(§4b of the depth-v2 contract) will fare on DSP inference; that remains
untested.

**Headroom for depth-v2 + reciprocal:** 23,040 − 1,317 = **21,723 LUT4
free (94.3%)** on top of this baseline before hitting Tang 25K capacity.

## 0. Why this exists
`contract_gpu_depth_v2_scoping_2026-08-25.md` §4b identified that the
GPU rasterizer coverage path has never been synthesized to any FPGA
target — no `docs/SPIN_CATALOG.md` entry, no `board_build_manifest.json`
target. That measurement is the actual prerequisite before any go/no-go
on depth-v2/reciprocal RTL, which both remain explicitly halted. This
contract scopes and runs that one measurement.

## 1. Objective & Scoped Files
* **New files (probe wrapper + build plumbing only — no new arithmetic):**
  - `hardware/boards/tang_primer_25k/spu13_tang25k_gpu_raster_probe.v`
  - `hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_gpu_raster_probe.ys`
  - `build_25k_spu13_gpu_raster_probe.sh`
* **Existing RTL measured, unmodified:**
  - `hardware/rtl/gpu/spu_edge_stepper.v`, `spu_raster_unit.v`,
    `spu_dual_raster.v`, `spu_video_timing.v` — all testbench-verified
    2026-08-24 (`50a19c4`, `8293451`), never resynthesized here.

## 2. Scope boundary (why this isn't gated the way depth-v2/reciprocal are)
- No new arithmetic, no new module beyond wiring/aggregation. The probe
  only needs to (a) drive `step_x/step_y` realistically (reuse
  `spu_video_timing.v` — already used this way in `spu_gpu_top.v`), (b)
  feed the raster units non-constant edge coefficients so Yosys can't
  constant-fold the accumulator logic away and under-report LUT usage,
  and (c) fan pixel output into the 3 available LEDs so it isn't
  optimized out as dead code.
- **Explicitly excluded:** `spu_gpu_top.v`'s HDMI/TMDS HAL and PLL. Those
  are a separate, unrelated cost center — mixing them in would confound
  the coverage-path measurement this step exists to get.
- **This produces a synthesis/place-route LUT count, not a silicon
  claim.** No `openFPGALoader` step, no board bring-up. Per CLAUDE.md's
  Silicon Claims Discipline, the result is reportable as
  `testbench-verified` (functional, from 2026-08-24) `+ synthesizable at
  N% Tang 25K capacity` — never "verified in silicon" without a
  `docs/hardware_evidence.md` entry from an actual board run.

## 3. Anti-optimization design (so the number is trustworthy)
- Edge coefficients for both triangle units are derived from a
  free-running frame counter (XOR/shift-mixed, not a static literal),
  reloaded via `setup0`/`setup1` pulses every N frames — prevents Yosys
  from treating `a/b/c` as compile-time constants and folding the
  incremental accumulators into fixed-stride counters.
- `step_x`/`step_y` come from the real `spu_video_timing.v` scan, not a
  synthetic toggle, matching actual usage.
- Pixel output (`pixel_r/g/b` from both raster paths) is XOR-folded into
  a shift register sampled onto `led[2:0]` — keeps the whole datapath
  live from input to a real output pin.

## 4. Verification Commands
```bash
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_gpu_raster_probe.ys
nextpnr-himbaechel --device GW5A-LV25MG121NES --vopt family=GW5A-25A \
    --vopt sspi_as_gpio --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_gpu_raster_probe.json \
    --write build/spu13_gpu_raster_probe_pnr.json \
    --log build/spu13_gpu_raster_probe_nextpnr.log --freq 12
```
Report the LUT4 count from the nextpnr log against the established
23,040 LUT4 Tang 25K capacity (`docs/hardware_evidence.md` §3.6g).

## 5. Stop Conditions
- If the coverage path alone already consumes an unreasonable share of
  23,040 LUT4 (e.g. approaching the 96%+ congestion band `six_step_probe`
  hit), HALT and flag before treating depth-v2/reciprocal as viable on
  Tang 25K at all — that would mean A7 100T is the only realistic target
  regardless of the reciprocal's own cost.
- Do not add this probe to `board_build_manifest.json` / claim regression
  coverage without discussing scope with John first — it is a one-off
  measurement, not yet a maintained regression target.
