# Engineering Contract: T1h Ghost Vertex-Line Isolation

**Date:** 2026-09-23<br>
**Contract ID:** `GPU-T1H-GHOST-VERTEX-LINE-2026-09-23`<br>
**Revision:** 0<br>
**Status:** `STOPPED — Q2 INCONCLUSIVE; OWNER DECLINED FURTHER LOGIC CAPTURE`<br>
**Owner:** John Curley

## 1. Objective

Determine whether the purple line following the left triangle edge in the T1h
scalar diagnostic originates in digital raster/scalar logic, FPGA output
timing, or the external VGA conversion/display path. Keep T1h H1 on hold until
the artifact is explained or the owner explicitly accepts it as a documented
physical limitation.

The symptom is called the **ghost vertex-line** in this contract. It is the
purple shimmer photographed along the triangle's left edge and reported to
follow the scene geometry. This name does not assert a raster-coverage cause.

## 2. Immutable evidence

| Evidence | Frozen result |
|---|---|
| T1h diagnostic image | `build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit`, SHA-256 `ec600abe73e847f0846bff5429813cc6913a343b235e215cab5298ebb5d126dd` |
| Physical observation | Operator saw the black/white scalar pattern change A→B→C→A; purple shimmer remained aligned with the triangle edge |
| Photo | `build/t1h_gpu_attributes_20260923/h1_scalar_threshold_photo.jpeg`, SHA-256 `a0afe136711a6acd02cd91c000b9c394663f6fbebb161b5dba7a3f06a07c757d` |
| Simulation edge audit | 572 lower-vertex samples across A/B/C/A; all twelve lane edge values, coverage, winner, scalar and final VGA RGB matched independent checks |
| Physical logic-analyzer capture | `build/t1h_gpu_attributes_20260923/rgb_pin_capture_01/vga_rgb_hsync.sr`, SHA-256 `41f35997cbf7882d467643bf6df3f87d6aebaf500ba03b1f379bab3a257177bb` |
| Capture limitation | Requested 1,000,000 samples at 48 MHz; FX2 returned 10,240 samples (0.213 ms, about 6.7 scan lines). D0–D2 remained black and D3 toggled as hsync. Capture did not include the triangle edge and is inconclusive for the symptom. |

The current T1h regression checks all 32,000 active simulation pixels against
the scalar/depth oracle. The focused edge region additionally compares the
final VGA outputs. No physical RGB frame capture exists.

## 3. Scope and files

### 3.1 Authorized work

* Read-only inspection of T1h scalar visualization, raster coverage, VGA
  blanking/timing, board constraints and measured J10 wiring.
* Simulation assertions that check final RGB and sync alignment over the full
  tested frame, if the pre-execution review finds the existing assertions do
  not already cover that boundary.
* One bounded physical observation using the already-qualified diagnostic
  image, after the capture method can target the line containing the artifact.
* Record the resulting classification and evidence in this contract and
  `docs/hardware_evidence.md`.

### 3.2 Prohibited without a revised contract

* Production raster, scalar, depth, activation, UART or VGA RTL changes.
* A new bitstream build or FPGA reprogramming.
* Changes to T1h fixtures, scene geometry, monitor, VGA cable or resistor
  harness during the baseline capture.
* Repeated blind FX2 captures. The first capture request returned only 10,240
  samples; another attempt requires a method that places the capture window
  over the geometry edge.
* Closing H1 as PASS based only on the expected scene change or the existing
  simulation result.

Target source files are read-only for this contract. The only authorized file
updates are this contract, the T1h simulation test if a missing assertion is
found, and the H1 classification in `docs/hardware_evidence.md`.

## 4. Q0 — Source and evidence audit

Run these commands before making any source or fixture change:

```bash
sed -n '700,755p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '1,120p' hardware/rtl/hal/hal_vga.v
sed -n '1,120p' hardware/rtl/gpu/spu_video_timing.v
sed -n '1,90p' hardware/boards/artix7/spu_a7_gpu_vga.xdc
python3 software/tests/test_gpu_t1h_attribute.py
```

Q0 findings:

* In `T1H_SCALAR_DIAG=1`, one `scalar_gray` signal drives red, green and blue.
  Invalid scalar pixels map to zero.
* `hal_vga` gates each channel with the same delayed `active_d` signal. The
  color and sync path share the existing one-cycle alignment correction.
* The T1h simulation checks exact scalar-derived RGB over all 32,000 active
  pixels. Its 572-point lower-vertex audit also checks final VGA RGB, with
  black required outside coverage.
* The exact board mapping is J10-1/G8 red, J10-2/G7 green, J10-3/G5 blue,
  J10-4/D5 hsync, and J10-10/E5 vsync. J10-5 or J10-11 is ground. The pins
  are tapped at the board header, before the three 270-ohm VGA resistors.
* The short analyzer capture contains only a blank fragment. It cannot
  distinguish a geometry-edge fault from output, harness, monitor, or camera
  behavior.

**Depth-winner follow-up (2026-09-23; simulation/oracle only):** Scene A's four
primitives have identical edge coefficients and therefore exactly coextensive
coverage. Their depth planes meet on an internal vertex-to-vertex seam. The
independent oracle finds 117 covered pixels with a minimum-depth tie. At
`(40,41)`, depth values are `[60,60,58,58]`; lanes 2 and 3 tie and the fixed
lower-ID rule selects lane 2. Adjacent `(39,41)` and `(41,41)` select lanes 2
and 3 respectively. At `(40,40)` all four depths tie and lane 0 wins. The
expanded regression scans two consecutive A frames and matches all 40,000
active pixels against the oracle, with 715 edge samples; the winner seam does
not change between those simulated frames. This supports a depth-winner seam
as the source of the sharp black/white boundary, but not temporal RTL
z-fighting. It does not explain the purple physical fringe.

**Q0 result:** PASS for source and simulation boundary review; physical cause
remains undetermined. The ordinary logic capture cannot yet target the edge.

## 5. Q1 — Full-frame simulation output audit

Extend `software/tests/test_gpu_t1h_attribute.py` with a continuous assertion
that final `vga_r/g/b` follow the delayed `active_d` gate and final
`vga_hsync/vsync` follow `hsync_d/vsync_d` on every simulated pixel clock,
including blanking and UART/activation intervals. Keep the independent
per-pixel oracle over scene A's lower vertex, the left edge, the first row
below the vertex, and all four A/B/C/A active frames. Do not alter production
RTL.

Run:

```bash
python3 software/tests/test_gpu_t1h_attribute.py
git diff --check
```

Pass criteria:

* Each diagnostic RGB channel equals the independent scalar-oracle grayscale
  value for every active sample; the three channels are equal.
* Final RGB follows the delayed active gate at every simulated cycle, so
  blanking and uncovered output is black.
* Final hsync/vsync follow the documented delayed timing nets at every cycle.
* Every lane's coverage and the selected depth winner match the edge/depth
  oracle at all added edge samples.

If any criterion fails, HALT. Create a separate correction contract before
changing production RTL. If all pass, proceed to Q2; do not claim the physical
artifact has been explained.

**Q1 result (2026-09-23):** the continuous final-output checks and the
32,000-pixel A/B/C/A oracle regression pass. The 572 focused edge samples
continue to match the edge, coverage, winner, scalar and VGA-output oracles.
This confirms the RTL simulation path and does not classify the physical
shimmer. `git diff --check` passed.

## 6. Q2 — Physical edge capture

Use the existing `T1H_DIAG_B1_S1` image and the current VGA harness. Probe
J10-1 through J10-4 with a 3.3 V-compatible analyzer, common ground at J10-5
or J10-11, and leave the monitor connected. Confirm the channel mapping before
capture: D0=red, D1=green, D2=blue, D3=hsync. Do not probe J10-6 or J10-12;
they are 3.3 V.

The capture method must either capture a full active frame at a sample rate
sufficient to resolve the RGB transition, or trigger a targeted active
scanline containing the ghost edge. The capture must include the geometry edge
and at least two pixels on both sides of it. A free-running capture that
contains only blank rows is not evidence and shall not be repeated unchanged.

Record the exact command, instrument identity, sample rate, sample count,
channel-to-pin map, capture hash, scene identity and operator observation.
For each captured edge sample, compare D0/D1/D2 values and their transition
positions relative to the oracle-predicted grayscale edge:

* If the digital RGB pins diverge or their transitions differ at the edge,
  classify the result as an FPGA output/timing or board-pin-path issue. Stop;
  do not patch raster coverage based on that result.
* If the digital RGB pins remain equal and match the oracle across the edge,
  classify the RTL raster/scalar and FPGA digital RGB outputs as exonerated for
  that capture. The remaining cause is downstream of J10: resistor network,
  VGA cable/connector, monitor sampling/scaling, or camera capture.
* If the capture does not include the edge or the analyzer underfills its
  requested window, classify Q2 as INCONCLUSIVE and stop. Do not infer cause
  from hsync-only or blank-region data.

No new hardware or purchase is authorized by this contract. If the available
FX2 analyzer cannot make the required targeted capture, record the limitation
and return with the smallest additional-observability proposal. Do not make
repeated attempts against the same underfilled capture gate without an
owner-approved attempt count, per-attempt timeout and total budget.

## 7. Q3 — Classification and H1 gate

Update the classification only after Q1 and a conclusive Q2 result:

| Q1 | Q2 | Required disposition |
|---|---|---|
| Fail | Any | H1 HOLD; draft a production correction contract if RTL is implicated |
| Pass | Digital RGB mismatch | H1 HOLD; isolate FPGA output or board-pin timing in a separate correction contract |
| Pass | Digital RGB matches oracle at edge | Record downstream VGA/display cause; H1 remains HOLD until owner accepts the visible artifact or an authorized hardware remedy removes it |
| Pass | Inconclusive capture | H1 HOLD; no RTL change and no silicon cause claim |

The current T1h H1 status remains **HOLD — ghost vertex-line unresolved**.

**Owner direction (2026-09-23):** stop further logic-analyzer captures and
move to the next graphics tranche. This closes this isolation effort as
inconclusive; it does not accept the artifact, resolve its cause, or change
T1h H1 from HOLD. Subsequent depth analysis is read-only and simulation-only;
no further physical capture is authorized by this contract.

## 8. Stop conditions

* Stop on any unexpected board reset, loss of sync, USB disconnect or wiring
  anomaly. Follow `docs/BENCH_ELECTRICAL_SAFETY.md` before further probing.
* Stop if a capture misses the edge or returns fewer samples than requested.
* Stop before any production RTL edit, bitstream build or FPGA reprogramming;
  those actions require a separate, reviewed correction contract.
* Do not claim the ghost vertex-line is a rasterizer bug, monitor artifact or
  camera artifact without a discriminating observation.
