# Engineering Contract: T1l Pre-Winner Pipeline Partition

**Date:** 2026-09-27  
**Contract ID:** `GPU-T1L-PIPELINE-PARTITION-2026-09-27`  
**Status:** `Q1 PASS; B1 PASS; H1 PASS (broad return-A repeatability); U-stripe visibility INCONCLUSIVE; T1l CLOSED`  
**Owner:** John Curley

## 1. Objective

Test whether registering a same-pixel tuple from all four raster lanes before
depth reduction isolates the recurrent activation/winner/U-V path enough to
justify a future Artix attempt. Preserve one pixel per clock after pipeline
fill. The source and simulation tranche has been followed by an owner-authorized
build and bounded physical observation. The exhausted earlier T1l material-op
build campaign was not reopened; the later pipeline-partition image and its
evidence are recorded below.

The target claim is limited to the frozen T1l U-stripe profile
(`T1L_MATERIAL_OP=3`) and its independent production A/B/C/A oracle.

## 2. Source review and proposed boundary

The failed route starts at frame/activation control, passes fractional-bit
readout and per-lane depth values, then crosses the serial four-way depth
reduction and winner-ID-controlled U/V selection before ending at
`fragment_u[12]`. The material predicate is downstream of the already
registered selected U/V tuple and is not on that critical path.

Add an opt-in `T1L_PIPELINE_PARTITION=1` profile boundary:

```text
per-lane coverage + depth + U + V
                + hsync/vsync/active
                    -> REGISTER
registered four-lane tuple
                    -> depth winner and matching U/V selection
                    -> existing registered selected-U/V/material path
                    -> existing GPU_POST_WINNER_REG and display
```

The first register must capture every field for the same input pixel. Carry
coverage, signed 56-bit depth, signed 56-bit U and V for each lane, and
hsync/vsync/active. The data/control tuple is approximately 679 bits per pixel
before any validity or generation tags. Do not register only winner ID: the
attribute steppers advance on the same pixel edge, so a delayed ID can select
the next pixel's U/V unless the corresponding lane values are held too.

## 3. Frozen invariants

* `T1L_PIPELINE_PARTITION=0` remains the default and preserves all existing
  T1f–T1l profiles exactly.
* Value `1` is legal only with prepared four-primitive T1i U/V scenes,
  `T1L_MATERIAL_OP=3`, and `GPU_POST_WINNER_REG=1`.
* Keep geometry, coverage equations, depth coefficients and comparisons,
  winner tie priority, U/V interpolation, activation/generation handoff,
  loader, fixtures, pacing, U-stripe predicate, and post-winner output
  register semantics unchanged.
* The new tuple boundary adds one pipeline cycle and preserves one-pixel-per-
  clock throughput. Delay hsync/vsync/active and valid with the exact same
  number of cycles as the pixel tuple.
* No fixture regeneration, RGB/diagnostic redesign, buffering, or material
  semantics changes.

If the lane values cannot be exposed without changing their numerical
semantics, halt and record the interface issue before broad refactoring.

## 4. Q1 simulation qualification

1. Add the default-off compile-time selector and profile guards.
2. Expose the four existing lane U/V stepper outputs to the top-level pipeline
   boundary without adding duplicate interpolation arithmetic.
3. Register the complete four-lane coverage/depth/U/V tuple and video controls.
4. Perform depth reduction from the registered tuple, select U/V from the same
   tuple, then feed the existing U-stripe and post-winner output stages.
5. Extend the independent oracle to model the added cycle and check every
   production-timing pixel over A→B→C→A (1,228,800 pixels). Check exact return-A
   equality, every lane winning, invalid-black behavior, first pixel after
   activation, and pixel-to-sync/active alignment.
6. Verify selector-off compatibility and run the focused T1i/T1j/T1k/T1l,
   depth, banking, and scene-pacing regressions.
7. Record synthesis-relevant register count as a structural estimate only;
   do not label it as FPGA resource or timing evidence.

Exact focused commands:

```bash
python3 software/tests/test_gpu_t1l_material_ops.py
python3 software/tests/test_gpu_t1l_material_ops.py --production
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1j_checker.py
python3 software/tests/test_gpu_t1k_grid.py
python3 software/tests/test_gpu_t1h_attribute.py
python3 software/tests/test_gpu_t1g_pacing.py
python3 software/tests/test_gpu_t1i_depth_output.py
```

The production oracle command must use the detached runner with a new evidence
directory and a frozen 600-second timeout. Do not run synthesis as part of Q1.

### Q1 completion

The implementation and direct testbench selector are complete. The full
production command completed through the detached runner with `COMPLETE`, exit
0, and reported:

```text
PASS: T1l independent production 640x480 A/B/C/A U-stripe oracle (1228800 pixels)
```

The focused default-profile T1l, T1i U/V, T1g pacing, T1j, T1k, T1h, and T1i
depth-output regressions passed. The selector remains default-off. The Artix
build flow now propagates `T1L_PIPELINE_PARTITION` and accepts only the new
seed-1 `T1L_PIPELINE_PARTITION_B1_S1` tag with `T1L_MATERIAL_OP=3`, the prepared
four-lane scene, and `GPU_POST_WINNER_REG=1`.

## 5. B1/H1 boundary

The owner authorized one Artix build attempt with a 3,600-second timeout and
3,600-second cumulative budget. The exact detached command was:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1l_pipeline_partition_20260927/b1_s1_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_MATERIAL_OP=3 T1L_PIPELINE_PARTITION=1 \
      GPU_POST_WINNER_REG=1 A7_ARTIFACT_TAG=T1L_PIPELINE_PARTITION_B1_S1 \
      bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

The attempt is consumed regardless of completion, failure, timeout, or build
flow error. Qualification requires final routed `clk_pixel` Fmax >= 25.00 MHz;
a zero exit code or `COMPLETE` marker alone is insufficient. On a miss, retain
the candidate and reports, do not flash, and stop before any correction or
rebuild. On a pass, only that exact image is eligible for the scoped T1l H1
visual check. No scene, material, interpolation, winner, activation, loader,
fixture, pacing, or post-winner-register semantics may change.

### B1 result

The detached job completed with exit 0 (`COMPLETE`) in 959 seconds. The final
routed report gives `clk_pixel = 40.03 MHz`, above the frozen 25.00 MHz gate;
the earlier placement estimate is not used. The exact image is
`build/spu_a7_100t_GPUVGA_T1L_PIPELINE_PARTITION_B1_S1.bit`, SHA-256
`79c9de8fab4a9c40bbc3be845b0a4d2c124279b0704acd76d18aa85e52fe7040`. The
Yosys command record confirms `T1L_PIPELINE_PARTITION=1` was elaborated.
Detached evidence is in
`build/gpu/t1l_pipeline_partition_20260927/b1_s1_01`; post-route metrics are
in `build/metrics/artix7_100t_GPUVGA_T1L_PIPELINE_PARTITION_B1_S1.md`.
This establishes build and timing evidence. The bounded H1 result is recorded
in §6.

## 6. Evidence status

| Evidence dimension | Status |
|---|---|
| Structural validation | Source review and profile propagation PASS |
| Functional simulation | PASS, production A/B/C/A oracle: 1,228,800 pixels |
| Synthesis / place-and-route | B1 PASS; routed `clk_pixel` 40.03 MHz |
| Interface validation | Production sync/active and partition alignment checks PASS |
| Silicon observation | Broad return-A repeatability PASS; physical U-stripe visibility/correspondence INCONCLUSIVE |

### H1 physical observation and closeout

The exact B1 image above was loaded to the Wukong Artix-7. `openFPGALoader`
completed the SRAM load and reported `isc_done=1`, `init=1`, and `done=1`.
The prepared-scene image displayed output after the frozen 175-byte scenes
were sent over `/dev/ttyUSB0` at 115200 8N1. The latest A/B/C/A transmission
record is `build/gpu/t1l_pipeline_partition_20260927/h1_repeat_sequence.json`.

Archived photos are in `docs/bench_captures/t1l_h1_2026-09-27/`:

| Photo | State | SHA-256 |
|---|---|---|
| `IMG_1769.jpeg` | Initial A | `f7332e14ea6a3784ee81d66600afb9c5317956e8b636ec15d796dd835dbfd23c` |
| `IMG_1770.jpeg` | B | `51c7823992c7eb8b8cde266e158b659eac4afd2526aba53ee511e1edcb2fc152` |
| `IMG_1771.jpeg` | Return A | `87e788d2c8f891cd6af847611f1b84a71955876b57c91b65c39dce37cd0cff12` |

Scene C was operator-observed but not photographed; it looked similar to
initial A. The operator also reported that return A and initial A looked
slightly different. Photo comparison shows the same two broad white regions;
the apparent differences are consistent with framing and brightness and do
not establish a changed large-scale pattern.

> **Return-A broad-pattern repeatability: PASS at operator/photo-comparison
> level.** The same two broad white regions are present in the initial and
> return-A captures; differences appear attributable to framing/brightness
> rather than a changed large-scale material pattern.

> **Physical U-stripe visibility/correspondence: INCONCLUSIVE.** The photos do
> not resolve the internal stripe structure clearly enough to claim that the
> expected U-stripe bands themselves were visibly confirmed.

Exact A/B/C/A return equality remains the independent simulation-oracle
claim, not a physical per-pixel claim. No RTL change, packet investigation, or
additional build/replay is justified by this H1 result. T1l is closed at this
evidence boundary.
