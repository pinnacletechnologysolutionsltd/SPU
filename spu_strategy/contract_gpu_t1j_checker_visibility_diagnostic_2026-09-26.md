# Engineering Contract: T1j Checker Visibility Diagnostic

**Date:** 2026-09-26  
**Contract ID:** `GPU-T1J-CHECKER-VIS-2026-09-26`  
**Status:** `Q0 PASS; Q1 PRODUCTION-TIMING SIMULATION PASS; B1 PASS; H1 PASS (OPERATOR-OBSERVED)`  
**Owner:** John Curley

## 1. Objective

Distinguish black T1j checker cells from uncovered black background on the
physical display. The photo's apparent gaps are unclassified; they are not
evidence of raster clipping because both cases currently render black.

## 2. Frozen diagnostic mapping

Preserve the T1j checker predicate exactly:

```text
checker = selected_u_q[12] XOR selected_v_q[12]
covered = selected_uv_valid_q

if !covered:             RGB = black (0, 0, 0)
else if !checker:         RGB = blue  (0, 0, F)
else:                    RGB = white (F, F, F)
```

Use the existing registered winner-selected U/V and validity tuple. Preserve
all sync and active signals at their current stages. Blue distinguishes a
covered black-checker cell from uncovered background while retaining white
checker cells. This selector changes only diagnostic RGB mapping.

## 3. Q0 source boundary

Add default-off compile-time selector `T1J_CHECKER_VIS_DIAG=0|1`. When enabled,
require `T1J_PROC_SHADE=1`, prepared four-primitive T1i U/V scene, and
`GPU_POST_WINNER_REG=1`; exclude T1k and all existing diagnostic profiles.
The ordinary T1j black/white profile and every legacy profile remain
unchanged when the selector is zero.

Do not change coverage, depth comparison, winner identity, U/V interpolation,
checker-bit selection, scene activation, UART transport, pacing, A/B/C
fixtures, or either register boundary. No interpolation or raster correction
is authorized or indicated by this diagnostic.

**Q0 result: PASS.** The mapping adds only a color code for the two existing
checker states and preserves invalid black, so it separates the two visual
cases at issue without changing raster semantics.

## 4. Q1 simulation qualification

Implement only the compile-time color selector, its legal profile guards,
independent-oracle assertions, and focused documentation. Reuse the frozen
T1i A/B/C/A scenes and T1j oracle. Check every production 640x480 pixel:

* covered checker-zero pixels are blue;
* covered checker-one pixels are white;
* uncovered pixels are black;
* A/B/C/A color maps agree with the independent depth/U/V oracle;
* initial A and return A are identical;
* the T1j U/V register and post-winner RGB/control alignment are unchanged;
* selector-off T1j output remains bit-identical to its existing black/white
  checker behavior.

No synthesis, FPGA build, or board programming is included in Q1. After Q1
passes, the physical observation requires a separately frozen bounded build
budget and the exact qualified bitstream.

## 5. Q1 result and B1 boundary

The reduced 80x100 A/B/C/A oracle passed 32,000 pixels. The production
640x480 A/B/C/A oracle then passed 1,228,800 pixels using the detached run
`build/gpu/t1j_checker_visibility_q1_20260926/production_oracle/` (exit 0,
252 seconds). The T1j, T1k reduced-oracle, and T1i regression commands also
passed after adding the selector. `git diff --check` and
`bash -n hardware/boards/artix7/build_a7.sh` pass.

Prepared B1 profile:

```bash
A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
T1J_PROC_SHADE=1 T1J_CHECKER_VIS_DIAG=1 GPU_POST_WINNER_REG=1 \
A7_ARTIFACT_TAG=T1J_CHECKER_VIS_DIAG_B1_S1 \
bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

The owner authorized a maximum one-build B1 campaign with a 3600-second
per-build timeout and 3600-second cumulative limit. The first attempt
`build/gpu/t1j_checker_visibility_b1_20260926/run_01/` failed in one second:
the launch command omitted all profile environment variables. The detached
runner records only the command after `--`; shell assignments before the
runner are not forwarded to the worker. Its command record therefore shows a
default GPUVGA profile, and no timing result or qualified artifact was
produced. It consumed its authorized slot. The owner then authorized one
additional attempt under a renewed 3600-second budget.

If the owner renews one B1 attempt, pass profile variables as arguments to
`env` after `--`, for example:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1j_checker_visibility_b1_retry_20260926/run_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
      T1J_PROC_SHADE=1 T1J_CHECKER_VIS_DIAG=1 GPU_POST_WINNER_REG=1 \
      A7_ARTIFACT_TAG=T1J_CHECKER_VIS_DIAG_B1_S1 \
      bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

**B1 result:** The corrected retry
`build/gpu/t1j_checker_visibility_b1_retry_20260926/run_01/` completed with
exit 0 in 987 seconds. Routed `clk_pixel` Fmax is 25.94 MHz against the
25.00 MHz constraint. Metrics:
`build/metrics/artix7_100t_GPUVGA_T1J_CHECKER_VIS_DIAG_B1_S1.md`.
Bitstream:
`build/spu_a7_100t_GPUVGA_T1J_CHECKER_VIS_DIAG_B1_S1.bit`, SHA-256
`5c7ea46db4eb3ec8080f45ad33fa6f113a10cd783b382a604654483ad50a0127`.
This is a timing-qualified build. The exact image was subsequently loaded to
the Artix-7 board with `openFPGALoader -c dirtyJtag --freq 1000000`; it
reported `Load SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`. The frozen
T1i A/B/C/A fixtures were then sent over `/dev/ttyUSB0` at 115200 8N1. Each
175-byte write completed `tcdrain`; the three start-to-start gaps were
3011.60, 3011.48, and 3011.52 ms. Transcript:
`build/gpu/t1j_checker_visibility_h1_20260926/uart_sequence.json`.
The operator uploaded `IMG_1767.jpeg` (SHA-256
`ae2da46bd6a321aaece3a5ea5b491060c4b6c7e62671ed393a6d26d9bd8f6e89`). It
shows blue and white regions filling the triangle-shaped scene against a
black background, without the apparent silhouette gaps in the previous
black/white image. No detached colored fragment is apparent in this capture.

**H1 classification:** **PASS (operator-observed, visual-only)** for the
two-visible-color diagnostic: covered checker states appear blue and white,
and the combined silhouette appears filled against black. This supports
the prior apparent clipping as a visualization artifact: covered fragments
in the black checker state were indistinguishable from the black background
in the original black/white display. The two-visible-color checker preserves
the complete triangle silhouette and shows those regions as procedurally
shaded cells rather than clipped raster coverage. Exact physical pixel
correctness remains a simulation/oracle claim. The small detached red artifact
remains a separate unresolved observation.

## 6. Evidence interpretation

* Continuous blue and white regions forming the full triangle support
  checker-cell/background aliasing as the explanation for the apparent gaps.
* Missing regions in this diagnostic remain ambiguous between coverage and
  output gating and justify a focused follow-up.
* Any blue or white pixels outside the expected covered oracle region are a
  separate output artifact.

The earlier small detached red artifact remains separate and unresolved.
