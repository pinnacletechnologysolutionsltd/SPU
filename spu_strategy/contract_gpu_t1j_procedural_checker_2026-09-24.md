# Engineering Contract: T1j Procedural Checker Material

**Date:** 2026-09-24  
**Contract ID:** `GPU-T1J-PROCEDURAL-CHECKER-2026-09-24`  
**Status:** `TIMING FORENSICS COMPLETE; SIMULATION PIPELINE CANDIDATE PASS; PRODUCTION Q2 PENDING`  
**Owner:** John Curley

## 1. Objective

Prove that the GPU can generate deterministic fragment color from its existing
depth-winner-selected, interpolated `(u,v)` coordinates, without texture
storage, framebuffer, or sampled image data.

The sole material function is a two-color checker:

```text
if !fragment_valid:
    RGB = black
else:
    checker = selected_u[12] XOR selected_v[12]
    checker == 0 -> RGB = black
    checker == 1 -> RGB = white
```

`RGB` is 12-bit RGB444: black is `12'h000`, white is `12'hFFF`.
`T1J_CHECKER_BIT=12` is frozen for the whole tranche. It is not a run-time or
build-time tuning parameter.

## 2. Q0 source review and checker-bit selection

The frozen T1i A/B/C wire fixtures are unchanged. Their hex-file SHA-256
values are:

| Scene | Fixture | SHA-256 |
|---|---|---|
| A | `fixtures/gpu_t1i_scene_a_wire_175b.hex` | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` |
| B | `fixtures/gpu_t1i_scene_b_wire_175b.hex` | `49484804bf798a4de6c4389c615eacfc3b42115d67a3b5d60c311b0c432d9fc9` |
| C | `fixtures/gpu_t1i_scene_c_wire_175b.hex` | `628f1efd61c1c23f52d72d6908d4ccbacc27289687b8c18c6ab5c01d91b5ccba` |

The existing independent T1i oracle was run over all 640x480 active pixels,
computing coverage, depth winner, then independently interpolated U/V before
evaluating candidate checker bits. The visible geometry lies entirely within
the 80x100 upper-left region. At bit 12 the oracle predicts:

| Scene | Covered pixels | U range | V range | Black | White |
|---|---:|---:|---:|---:|---:|
| A | 2441 | 2879–39566 | 667–25452 | 703 | 1738 |
| B | 924 | 2047–47102 | 1023–29695 | 477 | 447 |
| C | 2441 | 3903–40590 | 4763–29548 | 1588 | 853 |

Both colors occur in all four winning lanes in every scene. Each scene has
thousands of covered pixels, while the bit-12 pattern has broad connected
regions and several large cells. Across the complete frames, A differs from B
at 1801 checker-RGB pixel positions and from C at 1833; an oracle return to A is exactly
pixel-identical. These ranges and counts freeze `T1J_CHECKER_BIT=12`.

**Q0 count correction (2026-09-24):** the initial draft recorded checker
differences of 2700 and 2384. The production Q2 run and an independent recount
of the frozen depth/U/V/checker oracle establish the correct RGB deltas as
1801 (A/B) and 1833 (A/C). The checker rule and selected bit remain unchanged.
The initial production attempt consumed its one-run budget and completed all
1,228,800 pixel comparisons without an oracle mismatch, but failed the stale
delta assertion. The owner authorized one corrected 600-second production
replay on 2026-09-24.

Source review confirms that `fragment_u` and `fragment_v` are produced by two
independent T1i attribute paths with the same `raster_primitive_id` and
`raster_primitive_valid`. The final display mux is downstream of those
winner-selected values, and `GPU_POST_WINNER_REG` is downstream of the final
RGB mux with hsync/vsync/active on the same stage. The checker can be added as
one compile-time branch in this path without changing interpolation, depth,
coverage, activation, or transport.

**Q0 result: PASS. Q1 implementation is authorized within this contract.**

## 3. Frozen profile and signal order

Add `T1J_PROC_SHADE=0|1`, default `0`.

`T1J_PROC_SHADE=1` requires:

```text
PREPARED_SCENE=1
FOUR_PRIMITIVE_SCENE=1
T1I_UV_SCENE=1
T1H_SCALAR_SCENE=0
T1H_SCALAR_DIAG=0
T1I_UV_DIAG=0
T1I_UV_REG_DIAG=0
T1I_DEPTH_DIAG=0
```

`GPU_POST_WINNER_REG` is legal with T1j. The physical T1j profile shall set
`GPU_POST_WINNER_REG=1`; it registers final procedural RGB and aligned
hsync/vsync/active together. The ordinary T1i profile remains unchanged when
`T1J_PROC_SHADE=0`. The build profile must reject any T1j/diagnostic conflict
and tag the physical image distinctly.

The frozen signal order is:

```text
coverage -> depth winner -> winner-selected U/V -> T1j checker
          -> final RGB mux -> GPU_POST_WINNER_REG -> VGA/HDMI
```

## 4. Invariants and exclusions

* The shader consumes only winner-selected U, V, and their existing valid
  state. It does not consume primitive ID, depth value, screen position,
  scene ID, or any separate coordinate source.
* If either selected coordinate is invalid, output black. Every uncovered
  active pixel is black.
* Do not change U/V setup, coefficients, fractional shifts, accumulators,
  depth comparisons, winner priority, coverage, scene activation, UART,
  loader, host pacing, or A/B/C fixtures.
* No texture lookup, texture RAM, framebuffer, sampled image data, division,
  floating point, shader framework, or new top-level port.
* The small detached red physical artifact remains a separate unresolved
  observation. T1j makes no claim to explain or fix it.
* T1i's unrelated full-repository timeout remains documented gate debt. This
  contract does not waive or rerun that gate.

## 5. Q1 implementation and focused qualification

1. Add the default-off selector and elaboration/build guards in
   `spu_gpu_top.v`, the Artix wrapper, and `build_a7.sh`.
2. Add only the bit-12 checker branch after T1i winner-selected U/V and before
   the existing final RGB mux. Keep `GPU_POST_WINNER_REG` as the final
   color/sync boundary.
3. Add an independent Python checker oracle that decodes each frozen fixture,
   computes coverage and depth winner first, interpolates U/V for that winner,
   then computes the expected checker. It must not use RTL-selected U/V as
   its expected input.
4. Verify disabled T1j preserves T1i RGB behavior; reject illegal profiles;
   check reset/invalid black; and check exact one-cycle procedural RGB plus
   hsync/vsync/active alignment with the output register enabled.
5. Do not regenerate or edit fixtures.

## 6. Q2 production-timing oracle

Run frozen `A -> B -> C -> A` at production 640x480 timing. Compare all
640x480 active pixels in each first post-activation frame against the
independent depth/U/V/checker oracle: 1,228,800 frame-pixel comparisons total.
This includes every uncovered pixel, which must be black. Assert:

* all covered colors match the oracle and all invalid pixels are black;
* all four primitive lanes win pixels and both checker colors occur in every
  scene;
* B and C differ from A at the corrected Q0-frozen 1801 and 1833 pixel positions,
  respectively;
* return A is pixel-identical to initial A;
* the registered RGB/sync/active tuple has exactly one cycle of alignment.

The initial Q2 attempt failed only because the original frozen delta counts
were wrong. The corrected owner-authorized replay completed with exactly one
`COMPLETE` marker in 246 seconds; all 1,228,800 pixels matched the independent
oracle. Evidence is in
`build/gpu/t1j_q2_20260924/run_02/`. Do not rerun the full repository gate;
the pre-existing T1i timeout remains separate and recorded.

## 7. B1/H1 boundary

After Q2 passes, B1 is one fresh Artix image with `T1J_PROC_SHADE=1` and
`GPU_POST_WINNER_REG=1`; it uses the existing frozen A/B/C packets and host
pacing. The owner directed continuation on 2026-09-25. Freeze one build
attempt, 3600 seconds per attempt, and 3600 seconds total campaign budget.
Launch it detached with desktop notification using:

```bash
env A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
    T1H_SCALAR_SCENE=0 T1H_SCALAR_DIAG=0 T1I_UV_SCENE=1 \
    T1I_UV_DIAG=0 T1I_UV_REG_DIAG=0 T1I_DEPTH_DIAG=0 \
    T1J_PROC_SHADE=1 GPU_POST_WINNER_REG=1 \
    A7_ARTIFACT_TAG=T1J_PROC_CHECKER_B1_S1 \
    bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

Evidence directory: `build/gpu/t1j_b1_20260925/run_01/`. If the one attempt
fails, times out, or becomes unavailable, stop; a second build requires a
new owner-authorized budget.

**B1 result (2026-09-25):** The detached build command completed with exit 0
in 1144 seconds and produced
`build/spu_a7_100t_GPUVGA_T1J_PROC_CHECKER_B1_S1.bit` (SHA-256
`101fb8088afd283b244500e68a7a727ab0fffb363d78b4c0fc63a07406f5f17c`).
However, nextpnr's final routed result reports `clk_pixel=21.56 MHz`, below
the required 25 MHz, and explicitly prints `ERROR: Max frequency ... FAIL at
25.00 MHz`. Therefore B1 is **FAIL** for timing qualification; the emitted
bitstream is not qualified and must not be loaded for H1. The detached job's
`COMPLETE` marker records only that the build script exited zero; it does not
override the routed timing failure. The one-build/3600-second budget is
consumed. Any timing correction or additional build requires a revised
contract and new owner-authorized budget.

**Timing forensics (read-only, 2026-09-25):** Yosys logs show both
`T1J_PROC_SHADE=1` and `GPU_POST_WINNER_REG=1` propagated to the Artix top and
GPU. The routed endpoint is the D input of
`u_gpu.post_winner_output_register.u_pixel_output_register`; the register is
present and enabled. The startpoint is the Q output of
`u_gpu.prepared_quad_raster.u_rast4.u0.u_e2`, an edge-function accumulator
register. The reported path proceeds through edge comparison and coverage,
the four-way depth comparison, primitive-ID routing, the selected V attribute
path, `fragment_v[12]`, checker/color logic, and `display_b[0]` into that
output-register endpoint. Its report totals 6.9 ns logic and 39.5 ns routing.

The checker RTL is one-bit logic: a one-bit XOR of `fragment_u[12]` and
`fragment_v[12]`, masked by valid, replicated to RGB. It adds no wide
arithmetic. T1j versus the closest T1i registered-output build changes
resources by only -2 LUTs (39327 versus 39329), 0 flip-flops (15346 each),
0 CARRY4 (1190 each), 0 DSP48E1 (6 each), and 0 BRAM. The timing difference
is 21.56 versus 24.18 MHz; the reported routing component differs by 4.8 ns
while logic differs by 0.2 ns. The prior 35.23 MHz result was the unregistered
T1i U/V diagnostic and is not an equivalent timing baseline. The T1i
registered-output build also missed the 25 MHz target, although its bitstream
was previously loaded for physical observation.

The build script's zero exit status reflects nextpnr's process status; it does
not gate the final log-backed Fmax. Its `COMPLETE` marker therefore did not
represent timing qualification.

**Authorized simulation-only correction:** register winner-selected U/V,
valid, hsync, vsync, and active together before the T1j checker, then retain
`GPU_POST_WINNER_REG` after final RGB. This splits the edge/depth/winner/U/V
route from the checker/output route, preserves one-pixel-per-clock throughput,
and adds one aligned pixel of latency. The independent oracle and A/B/C/A
pixel stream must remain identical after sync/active alignment. Do not change
depth, winner identity, U/V arithmetic, checker semantics, scene state,
transport, fixtures, or legacy profiles. No additional build is authorized
by the consumed original B1 budget.

**Pipeline candidate implementation (2026-09-25):** the T1j branch now
registers the selected 56-bit U and V values, combined validity, and
hsync/vsync/active before evaluating the frozen bit-12 checker. The existing
`GPU_POST_WINNER_REG` remains after the final procedural RGB. The directed
pixel-test harness aligns its oracle coordinates through this extra stage.
The reduced 80x100 A/B/C/A run passes 32,000 pixels, including independent
oracle RGB, all four lanes and both colors per scene, invalid black, reset,
exact sync/active alignment, and return-A equality. T1i U/V, T1h attribute,
T1g pacing, and T1i depth-output regressions also pass. No interpolation,
depth, winner, scene, loader, transport, fixture, or legacy-profile logic was
changed.

Run one production 640x480 A/B/C/A replay for this new RTL candidate through
the detached runner, with a 600-second limit and desktop notification. Use
`build/gpu/t1j_q2_20260925/pipeline_run_01/`; stop on any failure. The owner
also authorized one fresh 3600-second Artix build after the diagnosed cause
and correction are documented. Freeze its cumulative budget at 3600 seconds,
to be launched only after production Q2 passes, under
`build/gpu/t1j_b1_timing_fix_20260925/run_01/`. This separate correction
campaign does not restore the consumed original B1 build slot.
H1 replays A/B/C/A and records operator/photo evidence that the broad checker
pattern changes for B and C and returns to A. Physical evidence supports only
that the expected checker pattern was observed; exact per-pixel correctness
remains the simulation/oracle claim.

**Timing-correction B1 (2026-09-25): PASS.** The detached build completed
with exit 0 in 1239 seconds at
`build/gpu/t1j_b1_timing_fix_20260925/run_01/` (unit
`spu-run_01-20260925T083932Z-571056`). The source commit was
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`; the source tree was dirty, with
the build-time status preserved beside the result. Routed `clk_pixel` Fmax is
27.82 MHz against the 25 MHz constraint. Metrics are in
`build/metrics/artix7_100t_GPUVGA_T1J_PROC_CHECKER_B1_S1.md`. The qualified
artifact is `build/spu_a7_100t_GPUVGA_T1J_PROC_CHECKER_B1_S1.bit`, SHA-256
`a2e7eaa2a5a4997d7e6ac416e82b6e07d72489c1ecbf08a84b00b638e3576526`.

**H1 execution (2026-09-25): HOLD — operator result incomplete.** The board
was detected as XC7A100 (`idcode 0x3631093`). The exact qualified image loaded
to SRAM with `Load SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`. The frozen
T1i A/B/C/A sequence was sent over `/dev/ttyUSB0` at 115200 8N1. All four
175-byte writes completed `tcdrain`; start-to-start gaps were 3011.43,
3011.49, and 3011.40 ms, above the frozen 20 ms minimum. Transcript:
`build/gpu/t1j_h1_20260925/uart_sequence.json`.

The operator first reported “image unstable or artifact visible,” then
described “a series of broken triangles with edges clipped.” The operator
confirms that `IMG_1760.jpeg` shows final A and that B/C visibly changed.
In a follow-up on 2026-09-26, the operator confirmed that the black/white
checker cells themselves changed for B/C and that final A matched initial A.
The photo (SHA-256
`2b5b38765d4c14d68c77f673c7ecd90b1fdec661594acdeeb56d3b6199cb1a11`)
shows several pale triangle-shaped regions. Their apparent gaps are not enough
to classify this as raster clipping: black checker cells and uncovered pixels
both render black, so checker cells can blend into the black background. The
photo alone does not distinguish those cases or prove exact checker pixels.

**H1 classification:** **PASS (operator-observed, visual-only)** for the
bounded A/B/C/A demonstration: checker cells changed for B and C, then final A
matched initial A. This does not establish exact checker pixels on hardware.
Record the silhouette as **apparent discontinuities, cause unclassified**;
black-cell/background aliasing is a plausible explanation. The next
discriminator is a two-visible-color checker mapping (checker zero to blue,
checker one to white, uncovered to black) with the same raster, U/V, depth,
winner, and checker rule. A complete two-color silhouette would support the
aliasing explanation; remaining missing pieces would justify reopening
coverage/output investigation. The earlier detached red artifact remains a
separate unresolved observation. No raster RTL correction is justified by
the current evidence.

**Integration-gate follow-up (2026-09-26):** the detached repository gate
`build/docs_evidence_levels_20260925/repo_gate/` ended `FAILED` (exit 1): 236
passed and 2 reported failures. The underlying GPU failure was
`test_gpu_t1i_uv.py` elaborating T1j-only hierarchical taps inside a procedural
`if (PROC)` even when the T1i profile had `PROC=0`. The testbench now aliases
those taps inside a compile-time `generate if (PROC)`; no GPU RTL changed.
`python3 software/tests/test_gpu_t1i_uv.py` passes all 32,000 pixel checks
after the correction. The full repository gate has not been rerun, so its
status remains unverified after this fix.

## 8. Stop conditions

* Any need to alter interpolation, depth/winner state, coverage, activation,
  loader, transport, or fixtures: HALT and revise the contract.
* Any T1j-off RGB change, invalid-pixel color, oracle mismatch, or sync/RGB
  register misalignment: HALT before B1.
* Any legal profile combination affecting a legacy profile: HALT and correct
  the compile-time guard.
* Do not interpret the T1i full-repository timeout as a T1j failure or as
  resolved gate debt.
