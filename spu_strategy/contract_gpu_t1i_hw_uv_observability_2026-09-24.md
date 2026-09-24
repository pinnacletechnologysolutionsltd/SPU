# Engineering Contract: T1i-HW Interpolated U/V Physical Observability

**Date:** 2026-09-24<br>
**Contract ID:** `GPU-T1I-HW-UV-OBSERVABILITY-2026-09-24`<br>
**Revision:** 0<br>
**Status:** `Q0–Q1 PASS; B1 PASS; H1 HOLD — GHOSTING VISIBLE`<br>
**Owner:** John Curley

## 1. Objective

Answer the question:

> Does the simulation-qualified T1i interpolated `(u,v)` output produce the
> expected broad physical colour regions when observed through a dedicated
> compile-time diagnostic display mode on the Wukong Artix-7 VGA path?

This is a hardware observability tranche for the existing T1i interpolation
and scene-activation implementation. It does not requalify exact per-pixel
interpolation on silicon. Exact U/V values and winner selection remain
simulation-qualified by T1i's independent oracle.

T1i remains classified as:

* interpolation/oracle: simulation-qualified;
* loader/profile checks: passed;
* Q3 full repository gate: failed because of the recorded unrelated
  `spu_t1d_board_transaction_tb.v` timeout;
* FPGA build and physical U/V evidence: none before this tranche.

The T1h purple edge fringe remains unresolved. This tranche does not
investigate or claim to resolve it.

## 2. Frozen T1i baseline

The T1i source snapshot and fixture bytes are frozen by the SHA-256 values
below. Q1 may add only the diagnostic selector, post-winner display mapping,
build-profile guards, and the tests and documentation required by this
contract. It shall not change T1i geometry, interpolation arithmetic,
coefficient preparation, depth winner selection, activation, UART loading, or
the frozen fixtures.

### 2.1 Source snapshot

| File | SHA-256 |
|---|---|
| `hardware/rtl/gpu/spu_gpu_top.v` | `61b6097eebf90784aa04cbe31a9dddc41c095524d4672c75c05ca1cb7a948e21` |
| `hardware/rtl/gpu/spu_scene_profile_unpack.v` | `96c02f34d0ef40f148d23e7a4a8b08d10110a87784b7742e60ebe5aa2b4b5ccc` |
| `hardware/rtl/gpu/spu_scene_loader.v` | `0b3f43443da1835889945923936dbc346074e834bb6e7acef394c2fca7ef0dca` |
| `hardware/rtl/gpu/spu_scene_unpack.v` | `8801576124865a597b231a3e73fde828ce06b18af320d2bd75fbcbb1ea593cdc` |
| `hardware/rtl/gpu/spu_prepared_scene_control4.v` | `cc2e6007894987d3064d5791c91b827de2f977740a86a544785ef02358de1567` |
| `hardware/rtl/gpu/spu_depth_dispatch4.v` | `99ea3441ec39bfd973f9de6aa5adbcfb0e018ffd4baa01f54cb5ae9a847acf97` |
| `hardware/rtl/gpu/spu_prepared_scalar_attribute4.v` | `8443f4d61ecad7d1e56be402c043493cc1cd0542608ce99a164d6f5b087fdf25` |
| `hardware/rtl/gpu/spu_depth_math.v` | `e86d84244e1c2352ef86b6188d63be820a4a81c34ad23864f696cf1e9f3492bd` |
| `hardware/rtl/gpu/spu_attr_stepper.v` | `7e6daa88abd61ba5587b3e98ad9d127d88b6fefbd259d1f784b2ddf0eb218b74` |
| `hardware/rtl/gpu/spu_depth_compare4.v` | `5ffb83c57abdb6a802e14550b2bb87fb986f75f1f43db5f6cb2d535cbcc3a46c` |
| `hardware/rtl/gpu/spu_quad_raster.v` | `386414cc2d301a942a542d22f353daae292379b87e794a75b9533473ac1877b6` |
| `hardware/rtl/gpu/spu_raster_unit.v` | `4e7674635363fd317f337a3ee1f7aec419f2d737459dabb3bfd4e5983d8f13bf` |
| `hardware/rtl/gpu/spu_edge_stepper.v` | `cd6d2d7bd6b73fde5d848e806b8a6a4be911c5760ecf63bea84497902560ee9d` |
| `hardware/rtl/gpu/spu_reciprocal_core.v` | `9f49e386f4bf04b200097c4bb3c82f1af42ef3decebafae081dd49d1a4749306` |
| `hardware/rtl/gpu/spu_shared_mult35.v` | `6f95ae24f276af6437ce9d91152e6babec314a1de2e8a669697530cbae764bf5` |
| `hardware/boards/artix7/spu_a7_gpu_vga_top.v` | `03fc76477250242ccc7c6913bb18ef1cd2b8353db965ce0d63bbf7ed0c427915` |
| `hardware/boards/artix7/build_a7.sh` | `e9225ec03ff1db7011943a82a945514fadddfd8f33129a6d11da3ff8b70de6a3` |
| `hardware/boards/artix7/synth_a7_gpu_vga.ys` | `adcd61f8ce2c9410b39e4a988cffec201d1b766177fa1e30154a6a23e58b8365` |
| `software/tests/test_gpu_t1i_uv.py` | `70ebde3049c22155f6e5a560a3cee95b33c4128ad6fa304539c18480e77b116c` |
| `tools/generate_gpu_t1i_uv_scenes.py` | `cace478d1cba6be6bd3e10d52ee4661297d70404054725c2bcfe4c23eea6dd92` |

### 2.2 Frozen fixture identities

Fixture files are immutable generated outputs. Do not regenerate or edit them
in this tranche.

| Scene | Wire transaction SHA-256 | Hex fixture SHA-256 | Decoded payload SHA-256 |
|---|---|---|---|
| A | `8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9` | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` | `25a21419cffd7055d8cbdd9730fba8bd1e5b210215ce87047b33ad39ac0c4ae2` |
| B | `f71ec97d18c37cdae7067accbc3b0100bad3689d4fcbc856f55efc11207525d1` | `49484804bf798a4de6c4389c615eacfc3b42115d67a3b5d60c311b0c432d9fc9` | `016191716775c000020fa03c802e7001af19b30f6d9b1f2fecccf0569ae35716` |
| C | `604fea47bee07549e28212b87bb5da18dbe6b72d32412ed57bddb6decb8cb89d` | `628f1efd61c1c23f52d72d6908d4ccbacc27289687b8c18c6ab5c01d91b5ccba` | `aa8b607e5504f823c2dae97092d12a21fae1bf4d13487616355ee6b3c0ff229e` |

The physical sequence is `A → B → C → A`, using the existing T1i 175-byte
wire transactions and the T1g/T1i characterized host pacing. No packet or
transport change is in scope.

## 3. Frozen diagnostic semantics

Add one compile-time selector:

```text
T1I_UV_DIAG=0|1, default 0
```

Value `1` is legal only with `T1I_UV_SCENE=1`,
`FOUR_PRIMITIVE_SCENE=1`, `GPU_T1D_UART=1`, the `GPUVGA` Artix profile, and
both T1h selectors disabled. Reject illegal combinations at build/elaboration
time. The default-zero build retains normal RGB rendering and all legacy
profile behavior.

The diagnostic taps the already selected, post-depth-winner fragment values.
It does not feed back into interpolation or raster state. For a valid selected
fragment:

```text
R[3:0] = {4{selected_u[14]}}
G[3:0] = {4{selected_v[14]}}
B[3:0] = 4'b0000
```

If the pixel is uncovered or either coordinate-valid bit is low, RGB is
black. Assert that U and V valid bits agree. The Artix VGA wrapper exposes
only each channel's most significant bit, so physical RGB is exactly
`(U[14], V[14], 0)`: black, red, green, or yellow. This yields broad regions
with a clear two-coordinate signature and avoids relying on camera capture of
subtle grayscale levels.

For the frozen small-frame oracle, use `(u,v)` threshold `0x4000`. Expected
representative physical classes include:

| Scene | Pixel `(x,y)` | Expected class |
|---|---:|---|
| A | `(10,10)` | black |
| A | `(41,10)` | red |
| A | `(41,41)` | green |
| B | `(16,50)` | yellow |
| C | `(30,49)` | yellow |

The operator observation is limited to seeing the diagnostic U/V colour
regions change for B and C and return for A, with uncovered background black.
It is not evidence of exact physical per-pixel U/V correctness.

## 4. Invariants and hard constraints

* No changes to T1i U/V coefficients, fixed-point semantics, interpolation,
  depth winner, activation, loader, wire format, pacing, or fixtures.
* Diagnostic output uses both selected coordinates after the existing depth
  winner and is strictly gated by coverage/validity.
* No new top-level ports, runtime selector, framebuffer, texture, procedural
  material, or extra render pipeline stage.
* No changes to T1f/T1g/T1h default profiles or their fixtures.
* No speculative fix or claim concerning the T1h purple fringe.
* No T1j checker/grid shading in this tranche.
* T1i Q3 remains `FAILED` as recorded. No rerun of the full repository gate
  is authorized by this contract; a new bounded attempt budget requires owner
  authorization. Do not describe the prior Q3 as waived or green.

## 5. Q0 — Source and observability review

The following read-only source checks confirmed the existing T1i selected U/V
signals, existing T1h post-winner diagnostic branch, compile-time profile
guards, and one-bit-per-channel Artix output:

```bash
rg -n "T1I_UV|fragment_[uv]|T1H_SCALAR_DIAG" hardware/rtl/gpu/spu_gpu_top.v hardware/boards/artix7/spu_a7_gpu_vga_top.v hardware/boards/artix7/build_a7.sh
sed -n '780,800p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '250,262p' hardware/boards/artix7/spu_a7_gpu_vga_top.v
```

**Q0 result:** PASS. The diagnostic can be placed after winner-selected U/V
without changing their interpolation or winner path. The Artix wrapper's
single-bit channel outputs require broad binary bands; the frozen mapping
above supplies those directly. T1i source and fixture identities are frozen
in §2. Q1 remains unstarted until owner approval.

## 6. Q1 — Diagnostic implementation and simulation

After approval, implement only the following:

1. Add `T1I_UV_DIAG` to the GPU top, Artix wrapper, and build script with the
   legal profile combinations in §3. Use a new artifact tag
   `T1I_UV_DIAG_B1_S1`; preserve `T1I_SIM_S0` and all existing tags.
2. Add the post-winner colour mapping in §3. Keep the selector default zero
   and keep top-level ports unchanged.
3. Add a focused regression that falsifiably checks valid U/V threshold bits,
   black invalid pixels, valid-bit agreement, all four colour classes where
   present, and unchanged normal RGB when diagnostics are disabled.
4. Run the frozen T1i oracle and T1h/T1g/T1f profile, oracle, and loader
   regressions. Run `git diff --check` and `bash -n
   hardware/boards/artix7/build_a7.sh`.
5. Record resource utilization and timing from the fresh Artix build. HALT if
   the diagnostic prevents the existing timing target or exceeds the frozen
   board resource budget; do not optimize or alter the datapath under this
   contract.

No new T1i fixture is required. No full repository gate is run under this
contract while the prior Q3 timeout remains unresolved and no bounded retry
budget has been authorized.

**Q1 result (2026-09-24): PASS.** Added `T1I_UV_DIAG` defaulting to zero,
profile guards in the GPU top and Artix build flow, and post-winner binary
U/V-to-RGB mapping. The T1i regression now executes diagnostic-off and
diagnostic-on elaborations. Across all 32,000 A/B/C/A pixels, diagnostic-on
checks the exact U/V threshold mapping and black invalid output; all four
covered colour classes occur, B and C differ from A, and the second A matches
the first A at every sampled pixel. Diagnostic-off checks display RGB equals
the normal raster RGB for every sampled pixel. An illegal diagnostic-only
profile is rejected at elaboration.

Passed regressions:

```text
software/tests/test_gpu_t1i_uv.py                    PASS (32,000 oracle pixels; diag on/off)
software/tests/test_gpu_t1h_attribute.py              PASS (40,000 pixels; 715 focused edge samples)
software/tests/test_gpu_t1g_pacing.py                 PASS (five phase cases)
spu_scene_loader_profiles_tb.v                       PASS (63/126/150/174 exact and boundaries)
spu_t1f_profile_tb.v                                 PASS (199 checks)
spu_t1f_top_oracle_tb.v                              PASS (four-way oracle)
spu_prepared_scene_banking_tb.v                      PASS (876 checks)
git diff --check                                     PASS
bash -n hardware/boards/artix7/build_a7.sh           PASS
```

No interpolation, scene, loader, fixture, or pacing source changed. The
pre-existing T1i Q3 full repository result remains FAILED and was not retried.

## 7. B1 — Fresh Artix image

Build the diagnostic profile from the frozen T1i source plus only the Q1
diagnostic delta:

```bash
A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
T1H_SCALAR_SCENE=0 T1H_SCALAR_DIAG=0 T1I_UV_SCENE=1 T1I_UV_DIAG=1 \
A7_ARTIFACT_TAG=T1I_UV_DIAG_B1_S1 \
bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

**B1 job:** unit
`spu-gpu_t1i_hw_uv_diag_20260924_b1_01-20260923T201345Z-382055`; evidence
directory `build/gpu_t1i_hw_uv_diag_20260924_b1_01`. Exactly one terminal
marker, `COMPLETE`, is present; `result.json` records exit 0 after 1445
seconds.

Record the exact source revision/dirty state, bitstream SHA-256, tool versions,
resource use, timing result, and build logs. B1 PASS means the exact diagnostic
image was built and passed its synthesis/place-and-route timing and resource
checks. It does not mean U/V has been observed physically.

**B1 result (2026-09-24): PASS.** Source commit was
`8ea3bc2abeaff97dac5b01ed558ee96008788340`; the dirty source inventory and
tool versions are preserved in the detached evidence directory above. The
Artix-7 100T bitstream is
`build/spu_a7_100t_GPUVGA_T1I_UV_DIAG_B1_S1.bit`, SHA-256
`ccfa2b883a5ee1e30da52afdfa7b122a4a288e64b1730ecc59df788d1ad5b92e`. The
nextpnr log reports 39,335/126,800 LUTs (31%), 15,331/126,800 flip-flops
(12%), 1,190/15,850 CARRY4 (7%), 6/240 DSP48E1 (2%), and no block RAM. The
final routed `clk_pixel` maximum frequency is 35.23 MHz, passing the 25 MHz
target. Build and routed logs are in the evidence directory and the adjacent
named nextpnr artifact.

## 8. H1 — Physical observation

Only after B1 PASS:

1. Program the exact B1 bitstream and record its SHA-256.
2. Confirm a stable VGA baseline with the diagnostic enabled.
3. Send frozen T1i scenes `A → B → C → A` with existing 20 ms post-payload
   pacing; do not send another packet while the host delay is active.
4. Observe the broad black/red/green/yellow U/V regions. Confirm the pattern
   changes for B and C and returns to A. Capture an operator note and photo if
   available, identifying the image and sequence.
5. If the pattern is absent, unstable, or inconsistent with the broad oracle
   distinctions, record H1 as FAIL/INCONCLUSIVE and stop. Do not change
   interpolation or coverage logic under this contract.

H1 PASS supports only the statement: **“The T1i diagnostic U/V colour pattern
was physically observed changing across the frozen A/B/C/A sequence.”** Exact
per-pixel U/V correctness remains simulation evidence. The T1h purple fringe
is recorded separately and is not silently cleared by this observation.

The bounded sender is `tools/send_gpu_t1i_sequence.py`; it validates all three
frozen wire-transaction hashes, writes 175-byte packets at 115200 8N1, waits
20 ms after `tcdrain` (the actual sequence uses a 3-second scene dwell), and
writes a timestamped transcript. The Wukong JTAG chain was detected as
XC7A100 (`idcode 0x3631093`) before programming.

**H1 transport record (2026-09-24):** The exact B1 image was loaded with
`openFPGALoader -c dirtyJtag --freq 1000000`; result was `Load SRAM 100%`,
`isc_done 1`, `init 1`, `done 1`. Sender:
`tools/send_gpu_t1i_sequence.py`, SHA-256
`c227b38053cea29ea6c109aa91e986d0cad4c207284a6b5d561f030fc7455d74`.
Transcript: `build/gpu_t1i_hw_uv_diag_20260924_b1_01/h1_abca.json`, SHA-256
`e4f24c71c1748eaa55dd6a0ee8f25435ff81dd586310df35f1cf4eb055d93e60`. All
four frozen 175-byte writes completed `tcdrain`; measured start-to-start gaps
were 3011.583114 ms, 3011.703550 ms, and 3011.457002 ms. The operator supplied
`IMG_1743.jpeg`, copied to
`build/gpu_t1i_hw_uv_diag_20260924_b1_01/IMG_1743.jpeg` (SHA-256
`e31a002fc5f77d2876505e31c5e61bf2f202e07d227f27815024ff93985b1f51`). The
photo shows broad red/green diagnostic regions and yellow edge pixels, plus a
detached red fragment and a dotted green line above the main shape. The
operator reports that ghosting lines remain. This does not identify their
cause. H1 is **HOLD**; the sent sequence and photo do not prove captured
per-pixel U/V correctness or confirm every scene transition by themselves.
No interpolation or coverage correction is indicated by this evidence.

## 9. Stop conditions

* Any changed T1i baseline/fixture hash: HALT and restore/re-freeze through an
  explicit contract revision.
* Any change to interpolation, winner, activation, loader or pacing needed to
  make the diagnostic visible: HALT and propose a separate contract.
* U/V-valid disagreement, invalid-pixel colour leakage, or diagnostic-off RGB
  change: HALT B1 and fix only within the diagnostic boundary.
* Build timing/resource failure: HALT; no datapath redesign is authorized.
* Any full repository gate retry request must specify maximum attempts,
  per-attempt timeout, and cumulative budget before launch.
* Do not proceed to T1j based on B1 alone; H1 observation and the simulation
  oracle remain distinct evidence claims.
