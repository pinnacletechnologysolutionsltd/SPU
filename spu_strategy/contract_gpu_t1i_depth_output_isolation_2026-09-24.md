# Engineering Contract: T1i Depth Output Isolation

**Date:** 2026-09-24<br>
**Contract ID:** `GPU-T1I-DEPTH-OUTPUT-ISOLATION-2026-09-24`<br>
**Revision:** 0<br>
**Status:** `STOPPED / INCONCLUSIVE; Scene-A coverage and winner-ID diagnostics were clean; U/V artifact and history shift remained`<br>
**Owner:** John Curley

## 1. Objective

Test whether the visible ghosting is associated with coverage, combinational
depth-winner output, or settling after a registered output boundary. This is
an experimental diagnostic tranche only. It does not authorize a production
RTL correction or change the T1i interpolation claim.

Use the exact T1i Scene A fixture for each of three diagnostic images:

1. coverage-only white output;
2. combinational winner-ID colour;
3. winner-ID colour registered on `clk_pixel`, with sync and active delayed
   by the matching additional cycle.

The visual comparison is limited to this exact scene and hardware setup.

## 2. Q0 source review

The existing T1i data path has clocked raster/depth steppers, followed by a
combinational `spu_depth_compare4` winner reduction and combinational RGB
selection. `hal_vga` gates RGB with `active` but does not register it. The
current `hsync_d`, `vsync_d`, and `active_d` registers already align timing
with the accumulator pipeline by one cycle. There is no output register after
the four-way winner/RGB logic.

The registered experiment must therefore add exactly one output cycle and
delay the already-delayed sync/active by one matching cycle. A synchronous
pixel oracle can prove this alignment; it cannot prove the absence of
sub-cycle analog-visible glitches. Existing route timing at 35.23 MHz against
the 25 MHz clock target does not establish that an unregistered combinational
RGB path is free of short output hazards.

**Q0 result:** PASS. The three images are a bounded discriminator for the
owner's combinational-settling hypothesis. The result can support or weaken
that hypothesis but cannot identify the physical ghosting cause alone.

## 3. Frozen inputs and compatibility

* Use only frozen T1i Scene A:
  `fixtures/gpu_t1i_scene_a_wire_175b.hex`, 175 bytes including `A5`, wire
  SHA-256 `8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9`.
* Preserve all T1i interpolation, coverage, depth arithmetic, winner priority,
  scene activation, UART framing, packet length, and pacing behavior.
* Preserve the existing `T1I_UV_DIAG` selector and all earlier profile defaults.
* The T1i-HW H1 status remains **HOLD — ghosting visible**. No prior photo,
  hardware observation, or Q3 repository result is rewritten.
* No logic-analyzer capture, unrelated renderer refactor, FIFO, or transport
  change is authorized.

## 4. Compile-time diagnostic modes

Add `T1I_DEPTH_DIAG=0|1|2|3`, default `0`, to the GPU top, Artix wrapper,
and build script. Legal nonzero values require `T1I_UV_SCENE=1`,
`FOUR_PRIMITIVE_SCENE=1`, `GPU_T1D_UART=1`, `GPUVGA`, and T1h/T1i U/V
visualization selectors disabled. Reject all illegal combinations.

| Value | Output |
|---:|---|
| 0 | Existing T1i normal RGB path; unchanged default behavior |
| 1 | `4'hF` on all RGB channels when any armed coverage bit is set; black otherwise. Do not consult the depth winner. |
| 2 | Combinational selected winner ID: 0 red, 1 green, 2 blue, 3 yellow; black when winner invalid. |
| 3 | Register selected winner valid, winner ID, and resulting fixed RGB on `clk_pixel`; black when invalid. Delay current delayed `hsync`, `vsync`, and `active` by one more cycle before `hal_vga`. |

Use distinct artifact tags:

```text
T1I_DEPTH_COVERAGE_B1_S1      -> T1I_DEPTH_DIAG=1
T1I_DEPTH_WINNER_B1_S1        -> T1I_DEPTH_DIAG=2
T1I_DEPTH_WINNER_REG_B1_S1    -> T1I_DEPTH_DIAG=3
```

All builds use the same device, frequency, scene fixture, base compile-time
profile, seed, and constraints. Only the diagnostic mode and artifact tag may
differ. The registered mode must delay VGA sync/active with the RGB result;
do not change the timing generator or accumulator steps.

## 5. Q1 implementation and verification

Implement only the selector, the three diagnostic mappings, profile guards,
focused simulation coverage, and the three artifact build tags.

The focused regression shall use frozen Scene A and check:

* coverage-only output equals the OR of all four armed coverage bits and is
  independent of depth/winner;
* combinational winner colours match the four-way winner ID and validity;
* registered winner colour, valid, sync, and active equal the corresponding
  combinational signals delayed by exactly one pixel clock;
* the normal T1i profile with diagnostic value zero retains existing RGB;
* no colour appears for invalid pixels in any mode.

These are sampled-cycle simulation checks. They do not assert anything about
sub-cycle pin glitches.

**Q1 result (2026-09-24): PASS.** Implemented `T1I_DEPTH_DIAG`, the coverage,
combinational-winner, and registered-winner output modes, profile guards, and
three artifact tags. The registered mode captures valid, ID, RGB, sync, and
active together and drives VGA with the matching additional cycle. The
focused test checked every sampled cycle over two frames for all four modes,
rejected an illegal profile, exercised all four winner IDs, and verified the
one-cycle alignment. It passed alongside the T1h attribute test, T1g pacing
test, T1f profile and four-way oracle, loader boundary test, and scene-banking
suite (876 checks). `git diff --check` and the build-script syntax check
passed. The T1i 32,000-pixel interpolation oracle was not rerun.

Run:

```bash
python3 software/tests/test_gpu_t1i_depth_output.py
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1h_attribute.py
python3 software/tests/test_gpu_t1g_pacing.py
git diff --check
bash -n hardware/boards/artix7/build_a7.sh
```

Do not rerun the full repository gate. T1i Q3 remains FAILED on its previously
recorded unrelated T1D transaction timeout.

## 6. B1 — Three-image campaign

Build the three modes with:

```bash
A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
T1H_SCALAR_SCENE=0 T1H_SCALAR_DIAG=0 T1I_UV_SCENE=1 T1I_UV_DIAG=0 \
T1I_DEPTH_DIAG=<1|2|3> A7_ARTIFACT_TAG=<matching-tag> \
bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

For each image, record a detached-job terminal result, bitstream hash,
resource use, routed timing, source status, and tool versions. Program each
exact image and send Scene A with the existing T1i pacing. Record the visible
shape and whether ghosting is present.

Interpretation:

* ghosting in mode 1 means it remains with coverage-only output;
* clean mode 1 but ghosting in mode 2 localizes the artifact to winner/depth
  selection or its immediate output mux;
* ghosting in mode 2 but clean mode 3 supports a combinational output-settling
  hypothesis, provided sync/active alignment passes the focused regression.

These observations are diagnostic evidence, not a production fix and not
proof of the cause at analog-pin timescale. Do not promote mode 3 to the
production profile under this contract.

### Frozen build-attempt budget — awaiting owner authorization

Authorized maximum: **3 builds**, each with a **3600-second timeout**, and a
**10,800-second cumulative campaign budget**. The owner authorized these
exact time bounds on 2026-09-24. Each launched detached job
consumes one attempt regardless of outcome. Do not launch any of the three
builds beyond this budget. Do not extend or replace a failed, timed-out, or
unavailable attempt under this contract.

**Attempt 1:** coverage-only, `T1I_DEPTH_DIAG=1`,
`T1I_DEPTH_COVERAGE_B1_S1`. Detached unit
`spu-gpu_t1i_depth_output_20260924_coverage_01-20260923T214105Z-451380`;
evidence directory `build/gpu_t1i_depth_output_20260924_coverage_01`.
Terminal result: `COMPLETE`, exit 0, duration 1474 seconds. The tagged
bitstream was generated.

**Attempt 2:** combinational winner-ID palette, `T1I_DEPTH_DIAG=2`,
`T1I_DEPTH_WINNER_B1_S1`. Detached unit
`spu-gpu_t1i_depth_output_20260924_winner_01-20260923T220836Z-455072`;
evidence directory `build/gpu_t1i_depth_output_20260924_winner_01`.
Terminal result: `COMPLETE`, exit 0, duration 1460 seconds. The tagged
bitstream was generated.

**Attempt 3:** registered winner-ID palette, `T1I_DEPTH_DIAG=3`,
`T1I_DEPTH_WINNER_REG_B1_S1`. Detached unit
`spu-gpu_t1i_depth_output_20260924_winner_reg_01-20260923T223503Z-457923`;
evidence directory `build/gpu_t1i_depth_output_20260924_winner_reg_01`.
Terminal result: `COMPLETE`, exit 0, duration 1357 seconds. The tagged
bitstream was generated. This consumed the campaign's final authorized build
slot.

## 7. H1 — Physical diagnostic sequence

The board was detected as XC7A100 (`idcode 0x3631093`). The coverage-only
image `build/spu_a7_100t_GPUVGA_T1I_DEPTH_COVERAGE_B1_S1.bit` (SHA-256
`68b96455e09470e8beea08ee570447f5a01034e11bb37fe8290e68440937b358`) was
loaded to SRAM with `openFPGALoader -c dirtyJtag --freq 1000000`; the captured
completion reported `Load SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`.
The frozen Scene A packet was sent at 115200 8N1 through `/dev/ttyUSB0`,
175 bytes, `tcdrain` complete. Transcript:
`build/gpu_t1i_depth_output_20260924_coverage_01/h1_scene_a.json`.
Operator assessment: **coverage-only scene appears clean; no ghost line
observed**. This is one mode's observation only and does not isolate the
cause. The combinational winner-ID image
`build/spu_a7_100t_GPUVGA_T1I_DEPTH_WINNER_B1_S1.bit` (SHA-256
`81a7eb05a5be7839fd3261db430fbf6dc0c9a6df7d879ee5b4fb3059f9bf03a2`) was
loaded successfully to SRAM (`Load SRAM 100%`, `isc_done 1`, `init 1`,
`done 1`). Scene A was sent, 175 bytes, `tcdrain` complete; transcript:
`build/gpu_t1i_depth_output_20260924_winner_01/h1_scene_a.json`. Operator
Operator assessment of combinational winner-ID mode: **no ghost line
observed**. Load and send evidence are captured; continue with registered
winner-ID mode. The registered image
`build/spu_a7_100t_GPUVGA_T1I_DEPTH_WINNER_REG_B1_S1.bit` (SHA-256
`393d5cabbfce24ffd7920cfa318a1866930e90e57f0969bfa10823629ca46aea`) was
loaded successfully to SRAM (`Load SRAM 100%`, `isc_done 1`, `init 1`,
`done 1`). Scene A was sent, 175 bytes, `tcdrain` complete; transcript:
`build/gpu_t1i_depth_output_20260924_winner_reg_01/h1_scene_a.json`. Operator
assessment of registered winner-ID mode: **no ghost line observed**.

Photos supplied by the operator:

* Coverage-only: `IMG_1744.jpeg`, SHA-256
  `35b632147c331e0bc9511fca7b18c883d8bb73c47ffd196403ae57bf2e280824`, copied
  to `build/gpu_t1i_depth_output_20260924_coverage_01/IMG_1744.jpeg`.
* Combinational winner ID: `IMG_1745.jpeg`, SHA-256
  `511d633345806959e9a822195473528c864660f77a9bd780b6d3e2f3bf6cab1b`, copied
  to `build/gpu_t1i_depth_output_20260924_winner_01/IMG_1745.jpeg`.
* Registered winner ID: `IMG_1746.jpeg`, SHA-256
  `4e3aea84ad7516123e85ab93ccd3d4d37c24d03d0b500e149955e825d68dc89f`, copied
  to `build/gpu_t1i_depth_output_20260924_winner_reg_01/IMG_1746.jpeg`.
  The operator identifies the small scattered flecks in these images as
  likely fly marks and dust on the old garage monitor; they are not the
  geometry-following ghost-line artifact under investigation.

**H1 result:** Scene A produced no visible ghost line in coverage-only,
combinational winner-ID, or registered winner-ID mode. The planned diagnostic
discriminator therefore did not reproduce the original T1i U/V-image artifact
and does not isolate its cause. In particular, these observations do not
support claiming that registering the winner output removed the artifact.
Keep the original T1i
physical H1 classification on hold until the artifact is reproduced or
otherwise resolved with comparable evidence.

## 8. H2 — Original T1i U/V A/B/C/A replay

Owner-directed follow-up: replay the exact frozen sequence on the original
T1i U/V diagnostic image, freshly programmed, and observe after each scene:
`A -> B -> C -> A`. This adds no RTL or build and changes no fixtures. Pause
between packets for operator visual assessment/photo; each sender invocation
uses the frozen fixtures and pacing.

The board was detected as XC7A100 (`idcode 0x3631093`). Original image
`build/spu_a7_100t_GPUVGA_T1I_UV_DIAG_B1_S1.bit`, SHA-256
`ccfa2b883a5ee1e30da52afdfa7b122a4a288e64b1730ecc59df788d1ad5b92e`, was
freshly loaded to SRAM; programming completed with `Load SRAM 100%`,
`isc_done 1`, `init 1`, and `done 1`. Frozen Scene A was sent at 115200 8N1,
175 bytes, `tcdrain` complete. Transcript:
`build/gpu_t1i_uv_abca_replay_20260924_01/scene_a.json`. Operator assessment:
**no ghost line; small artifact above the image**. This is recorded separately
from the prior detached fragment/dotted extension. Frozen Scene B was then
sent at 115200 8N1, 175 bytes, `tcdrain` complete. Transcript:
`build/gpu_t1i_uv_abca_replay_20260924_01/scene_b.json`. Await operator
assessment: the supplied `IMG_1747.jpeg` shows a detached red fragment above
the triangle, distinct from the monitor flecks and resembling the fragment in
the earlier U/V image. Photo SHA-256
`9f910b634bbfd341b1285ddb56019ebc4be3d58bc224c81ff77402aceb030c15`; copied
to `build/gpu_t1i_uv_abca_replay_20260924_01/IMG_1747_scene_b.jpeg`. Frozen
Scene C was then sent at 115200 8N1, 175 bytes, `tcdrain` complete. Transcript:
`build/gpu_t1i_uv_abca_replay_20260924_01/scene_c.json`. Await operator
assessment: supplied `IMG_1748.jpeg` shows separated colored regions above and
beside the lower triangles, including a detached red region. Photo SHA-256
`7bc46ac58cdad18f91ed7d3cb1b63a7272c1efc1966977e6d6380e596a24663b`; copied
to `build/gpu_t1i_uv_abca_replay_20260924_01/IMG_1748_scene_c.jpeg`. This is
visually distinct from the likely monitor flecks; its relation to expected C
geometry or the reported artifact remains to be classified. The final frozen
Scene A was then sent at 115200 8N1, 175 bytes, `tcdrain` complete. Transcript:
`build/gpu_t1i_uv_abca_replay_20260924_01/scene_a_return.json`. Await
operator assessment/photo to determine whether the display returns to the
initial A appearance. The operator supplied two further images after the
replay and confirmed their labels: `IMG_1749.jpeg` is initial A and
`IMG_1750.jpeg` is return A. `IMG_1749.jpeg` (SHA-256
`67b703153fcc21d82cb3cad2219e55512cb500cd3f0b4473d6d26ae8c4f3c5d8`) appears
to show a yellow-left/green-right triangle with a detached red fragment above.
`IMG_1750.jpeg` (SHA-256
`985119120eb94284b4ddd22b0bcd7c27b47c900fdcc6c4c1ced22ae8bcbfe238`) appears
to show a red-left/green-right triangle with a similar detached red fragment.
Both are archived in `build/gpu_t1i_uv_abca_replay_20260924_01/`. The
confirmed comparison is a left-region change from yellow to red while the
right region remains green after A -> B -> C -> A. This confirms a
history-dependent physical output discrepancy consistent with the suspected
U/V state handoff. The T1i independent simulation test already checks all
32,000 pixels across A/B/C/A and requires exact return-A equality; it passes.
RTL/sample-cycle simulation therefore disagrees with the physical photos, and
the responsible state or output path is not yet identified.

**UART boundary check (2026-09-24):** `python3
software/tests/test_gpu_t1i_uv.py` passed again (32,000 full-frame pixel
oracle checks); it injects decoded bytes directly and does not instantiate
`spu_uart_rx`. A full-GPU 115200-waveform variant exceeded the test's 60-second
simulation timeout and was discarded without a result. The narrower
`python3 software/tests/test_gpu_t1i_uv_uart_loader.py` passed in 5.45 seconds:
all 700 bytes for A/B/C/A decoded with zero frame errors, each 174-byte payload
reconstructed exactly, and each bank activated only at the requested boundary.
This reduces suspicion on UART decode and loader assembly in simulation but
does not explain the physical A-return color change.

## 9. H3 — Recheck depth winner identity across A/B/C/A

Use the already-built combinational winner-ID image; no new build or RTL edit
is authorized. Replay the frozen A/B/C/A packets with the same pacing and
compare the winner-color pattern in initial A and return A. A changed pattern
would implicate coverage/depth-winner state; an identical pattern alongside
the original U/V color change would localize the discrepancy downstream to
the U/V attribute or diagnostic path. Pause for operator observation/photo
after each activation.

Image: `build/spu_a7_100t_GPUVGA_T1I_DEPTH_WINNER_B1_S1.bit`, SHA-256
`81a7eb05a5be7839fd3261db430fbf6dc0c9a6df7d879ee5b4fb3059f9bf03a2`.
The image was freshly loaded to SRAM; completion reported `Load SRAM 100%`,
`isc_done 1`, `init 1`, and `done 1`. Initial Scene A was sent, 175 bytes,
`tcdrain` complete; transcript:
`build/gpu_t1i_depth_winner_abca_20260924_01/scene_a_initial.json`. Await
operator assessment of initial A: **red, green, blue, and yellow winner
regions; no ghosting or artifacts**. Frozen Scene B was then sent, 175 bytes,
`tcdrain` complete; transcript:
`build/gpu_t1i_depth_winner_abca_20260924_01/scene_b.json`. Await observation
or photo before sending C.

## 10. Stop conditions

* Any diagnostic requiring a change to coverage, depth arithmetic, winner
  priority, interpolation, scene activation, or packet semantics: HALT.
* Registered mode with one-cycle misalignment in RGB/sync/active simulation:
  HALT and correct only the diagnostic pipeline before B1.
* A build timeout, failure, or unavailable result consumes its campaign slot.
* No conclusion about the ghosting cause from one mode alone.
* No production fix or T1j work based solely on this isolation campaign.

## 11. Final classification

The planned diagnostic comparisons were stopped before a complete H3
A/B/C/A replay. The Scene-A coverage-only, combinational winner-ID, and
registered winner-ID displays were reported clean, while the original T1i
U/V diagnostic still showed the detached red artifact and the broad
history-dependent return-A color change. This isolation tranche is therefore
**STOPPED / INCONCLUSIVE**: it did not identify a coverage or winner-ID fault
and does not justify a raster/depth correction. The subsequent registered
U/V and post-winner-output-register findings are recorded in their own
contracts and in the hardware evidence ledger.
