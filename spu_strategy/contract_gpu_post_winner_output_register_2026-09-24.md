# Engineering Contract: T1i Post-Winner Output Register

**Date:** 2026-09-24<br>
**Contract ID:** `GPU-POST-WINNER-OUTPUT-REGISTER-2026-09-24`<br>
**Status:** `Q0–Q2 PASS; B1 PASS; H1 PASS (operator-observed); small artifact unresolved`<br>
**Owner:** John Curley

## Roles

* **Spec Author:** Codex
* **Halt-and-Flag Implementer:** Codex
* **Integration Auditor:** focused GPU tests and owner review of physical evidence

## 1. Objective

Add one compile-time controlled register boundary after the existing final
post-winner RGB mux. Delay RGB, hsync, vsync, and active together by one
`clk_pixel` edge. Use the boundary for the prepared four-primitive T1i path and
as the output stage available to the later T1j procedural material path.

This change addresses the broad history-dependent color instability supported
by the registered-U/V physical replay. It does not claim to explain or remove
the small detached red artifact. That artifact remains a separate open
hardware observation in `docs/hardware_evidence.md` §3.15.

## 2. Q0 source review and fixed boundary

The source path is `coverage/depth winner -> existing RGB/diagnostic mux ->
hal_vga and hal_hdmi`. The T1i registered-U/V diagnostic already demonstrates
that an aligned register stage can be added without changing U/V arithmetic,
winner selection, activation, or scene loading. The production stage belongs
after `display_r/g/b` selection so any T1j fragment color function is also
settled before the video outputs.

Q0 review finds no need to alter arithmetic or raster state. Freeze these
rules:

* Add `GPU_POST_WINNER_REG=0` as a compile-time parameter. Default zero keeps
  every existing profile cycle-for-cycle unchanged.
* The selector is legal only with `PREPARED_SCENE=1`,
  `FOUR_PRIMITIVE_SCENE=1`, `T1I_UV_SCENE=1`, `T1H_SCALAR_SCENE=0`, and
  `T1I_UV_REG_DIAG=0`. `T1I_UV_DIAG` may be either value; the physical
  diagnostic build uses it at 1 to observe the final registered RGB.
* When enabled, register all four-bit RGB channels and hsync/vsync/active on
  the same rising edge of `clk_pixel`, with asynchronous active-low reset to
  zero. Feed both VGA and HDMI from this aligned output tuple.
* Do not change top-level ports, raster/depth/U/V/scalar arithmetic, winner
  priority, scene activation, UART, packet format, pacing, or fixtures.
* Do not enable the existing `T1I_UV_REG_DIAG` at the same time; that mode
  registers U/V upstream and would add a second output stage.

## 3. Scoped files

* `hardware/rtl/gpu/spu_gpu_top.v`
* `hardware/rtl/gpu/spu_pixel_output_register.v` (new, single-purpose stage)
* `hardware/boards/artix7/spu_a7_gpu_vga_top.v`
* `hardware/boards/artix7/synth_a7_gpu_vga.ys`
* `hardware/boards/artix7/synth_a7_gpu_vga_t1d.ys`
* `hardware/boards/artix7/synth_a7_gpu_vga_t1d_diag.ys`
* `hardware/boards/artix7/build_a7.sh`
* `software/tests/test_gpu_t1i_uv.py`
* `software/tests/test_gpu_t1i_uv_production_timing.py`
* `spu_strategy/contract_gpu_post_winner_output_register_2026-09-24.md`
* `docs/hardware_evidence.md`

No fixture files may be regenerated or modified.

## 4. Ordered implementation and verification

1. Add the Lithic output-register module and guarded compile-time selector.
2. Add a falsifiable test for the enabled selector: compare registered RGB and
   hsync/vsync/active to their pre-edge values at every sampled pixel; check
   reset values, the disabled combinational profile, illegal profile
   rejection, and mutual exclusion with `T1I_UV_REG_DIAG`.
3. Run:

   ```bash
   python3 software/tests/test_gpu_t1i_uv.py
   python3 software/tests/test_gpu_t1i_uv_uart_loader.py
   python3 software/tests/test_gpu_t1i_depth_output.py
   python3 software/tests/test_gpu_t1i_uv_production_timing.py
   bash -n hardware/boards/artix7/build_a7.sh
   git diff --check
   ```

   The 640x480 production-timing test is expected to exceed 60 seconds. Run
   it through one detached job with a 600-second wall-clock limit and desktop
   notification; output directory:
   `build/gpu_post_winner_output_register_20260924/prod_timing_run_01`.
   Do not poll that deterministic job in the launching turn.

4. Do not rerun `bash tools/verify_repo.sh`; the earlier T1i full repository
   gate remains timed out in the unrelated T1D transaction test.
5. Do not synthesize or program this production selector under the exhausted
   T1i divergence build budget. After Q1/Q2 source and simulation checks pass,
   record a separate owner-authorized bounded hardware budget before B1.
6. A future B1 diagnostic profile shall use
   `GPU_POST_WINNER_REG=1`, `T1I_UV_SCENE=1`, `T1I_UV_DIAG=1`,
   `T1I_UV_REG_DIAG=0`, and a unique artifact tag. Physical A/B/C/A evidence
   must compare initial and return A and separately report the detached red
   artifact. Build authorization and physical replay are not implied by this
   contract.

## 5. Recorded Q1 result and Q2 run

Q1 implementation and focused tests pass. `test_gpu_t1i_uv.py` passes the
existing 32,000-pixel oracle and return-A tuple checks with the output stage
disabled; it also passes registered-U/V diagnostics and both enabled
post-winner variants (normal RGB and T1i U/V diagnostic RGB). Enabled-mode
samples check RGB, sync, active, and reset alignment against their pre-edge
inputs. Illegal selector profiles and coexistence with the upstream
registered-U/V mode fail elaboration as required. The UART loader and depth
diagnostic regressions pass. `bash -n hardware/boards/artix7/build_a7.sh`,
Python bytecode compilation, and `git diff --check` pass.

Q2 production 640x480 A/B/C/A oracle test is launched with `OUT_REG=1`,
32,000 top-left ROI samples, and a 600-second detached timeout. Interpret its
result only from exactly one terminal marker. No FPGA build has been launched
for this contract.

## 6. Acceptance criteria

* With the selector disabled, existing T1i RGB and sync/active behavior are
  unchanged.
* With the selector enabled, every registered RGB tuple corresponds to the
  immediately preceding combinational display tuple, and hsync/vsync/active
  have exactly the same one-cycle delay.
* The enabled production-timing A/B/C/A simulation retains exact oracle
  agreement for 32,000 ROI samples and exact initial-A/return-A equality.
* No claim is made that this change fixes the small detached red artifact.
  The artifact stays open unless separate evidence resolves it.

## 7. Stop conditions

* Any need to change coverage, depth/U/V arithmetic, winner selection, scene
  state, loader, pacing, or fixture semantics: HALT and revise the contract.
* Any mismatch in RGB/sync/active cycle alignment or any disabled-profile
  output change: HALT before build authorization.
* Any selector combination that can affect legacy profiles: HALT and correct
  the guard.
* Do not consume the unused second build from the completed T1i divergence
  campaign. A new hardware build needs a separate owner-authorized budget.

## 8. Q2 result and owner-authorized hardware campaign

The detached production-timing replay completed successfully:

* Evidence directory:
  `build/gpu_post_winner_output_register_20260924/prod_timing_run_01`
* Systemd unit:
  `spu-prod_timing_run_01-20260924T061957Z-510430`
* Terminal result: exactly one `COMPLETE` marker, exit code 0.
* Result: `PASS: T1i production 640x480 A/B/C/A timing; 32,000 ROI samples
  match the independent U/V oracle`.

The owner conditionally authorized a fresh bounded hardware campaign, and the
Q2 pass satisfies that condition. Freeze the campaign at a maximum of two
Artix builds, 3600 seconds per build and 7200 seconds cumulative. Build 1 is
the exact registered post-winner diagnostic profile below. Build 2 is
contingency-only for a procedural or build-flow correction within this
contract; do not spend it if Build 1 succeeds. Do not reuse the unused build
slot from the separate T1i divergence campaign.

Build 1 command and profile:

```bash
env A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
    T1H_SCALAR_SCENE=0 T1H_SCALAR_DIAG=0 T1I_UV_SCENE=1 \
    T1I_UV_DIAG=1 T1I_UV_REG_DIAG=0 T1I_DEPTH_DIAG=0 \
    GPU_POST_WINNER_REG=1 \
    A7_ARTIFACT_TAG=T1I_POST_WINNER_REG_DIAG_B1_S1 \
    bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

Run it through `tools/run_detached_job.sh` with output directory
`build/gpu_post_winner_output_register_20260924/build_01`, timeout 3600
seconds, and `--notify-desktop`. After launch, record the unit and evidence
directory and end the turn without polling. Interpret its result only from a
single terminal marker. A valid successful Build 1 is the only image to
program; it authorizes the frozen physical A/B/C/A replay and ordinary
T1f/T1g-style RGB sanity observation. Physical acceptance requires initial
and return A to have the same broad color regions and the ordinary RGB image
to remain visually sane. Report the small detached red artifact separately;
this tranche does not claim to resolve it.

## 9. B1 and H1 result

B1 completed successfully in 1626 seconds with exactly one `COMPLETE` marker
(exit code 0) in
`build/gpu_post_winner_output_register_20260924/build_01`. The build used
source commit `8ea3bc2abeaff97dac5b01ed558ee96008788340`; the dirty source
snapshot is retained in that evidence directory. Bitstream:
`build/spu_a7_100t_GPUVGA_T1I_POST_WINNER_REG_DIAG_B1_S1.bit`, SHA-256
`f782a18ad2ee78928ddae05eb341094655815180fdd019ea3826a07610925640`.

The image loaded to the board and reported `Load SRAM 100%`, `isc_done 1`,
`init 1`, and `done 1`. The frozen 175-byte T1i A, B, C, A packets were sent
at 115200 8N1 through `/dev/ttyUSB0`; all four per-scene transcripts in the
evidence directory record complete writes and `tcdrain`.

**Operator observations:** initial A was a red-left/green-right triangle with
a small red artifact above it. B was reported identical to the referenced
`IMT_1748.jpeg`. C was yellow-left/green-right, with a red triangle artifact
above. Return A matched initial A in its broad red-left/green-right regions.
The small red artifact remained visible throughout. No photos were supplied
for this replay, so these are operator observations rather than captured-pixel
evidence.

For ordinary RGB sanity, the already-qualified T1g bitstream was loaded from
`build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit`
(SHA-256
`e16dc6992c60de99d9d5f9d5a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`).
Its frozen 127-byte T1f Scene A packet was sent and the operator reported a
normal triangle with no phantom vertices. This reused an existing qualified
image and consumed no additional build slot.

**Classification:** B1 PASS. H1 PASS for the bounded operator-observed claim
that the registered post-winner diagnostic changes across A/B/C and returns
to the same broad A regions, and for ordinary T1g RGB visual sanity. The
broad history-dependent color shift was not reproduced with the post-winner
register. The detached red artifact remains unresolved and is explicitly
outside this pass. This is not exact physical pixel proof. The second build
slot remains unused. The broad output-settling issue is closed sufficiently
to proceed to the next procedural-shading tranche; do not claim the small
artifact is solved.
