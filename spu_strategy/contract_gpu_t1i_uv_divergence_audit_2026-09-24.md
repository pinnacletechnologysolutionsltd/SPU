# Engineering Contract: T1i U/V RTL–Silicon Divergence Audit

**Date:** 2026-09-24<br>
**Contract ID:** `GPU-T1I-UV-DIVERGENCE-AUDIT-2026-09-24`<br>
**Revision:** 1<br>
**Status:** `Q0–Q3 SIM/SOURCE PASS; REGISTERED-U/V H1 OBSERVED; RETURN-A BROAD REGIONS REPORTED MATCH; SMALL ARTIFACT UNRESOLVED`
**Owner:** John Curley

## Roles

* **Spec Author:** Codex
* **Halt-and-Flag Implementer:** Codex
* **Integration Auditor:** `run_all_tests.py` scoped checks; owner reviews physical evidence

## 1. Objective and frozen evidence

Diagnose the confirmed physical difference between initial Scene A and return
Scene A on the original T1i U/V diagnostic image. The initial A photo shows a
yellow left region; after A -> B -> C -> A the return-A photo shows that region
red while the right region remains green. The operator confirmed photo order.
Do not infer the specific faulty state yet.

Frozen baseline:

* Original T1i U/V image:
  `build/spu_a7_100t_GPUVGA_T1I_UV_DIAG_B1_S1.bit`, SHA-256
  `ccfa2b883a5ee1e30da52afdfa7b122a4a288e64b1730ecc59df788d1ad5b92e`.
* A/B/C fixtures and their hashes are frozen by
  `tools/send_gpu_t1i_sequence.py`.
* Coverage-only, winner-ID, and registered winner-ID Scene-A photos showed no
  geometry-following ghost line. Their original three-build campaign is
  exhausted; this contract authorizes no rebuild until a separate owner budget
  is recorded.
* `test_gpu_t1i_uv.py` passes 32,000 full-frame checks at 80x100 timing and
  verifies identical return-A pixels. It drives decoded bytes directly.
* `test_gpu_t1i_uv_uart_loader.py` passes all 700 UART bytes and exact A/B/C/A
  loader payloads. This does not run the full GPU behind bit-level UART input.

## 2. Scope and invariants

Q1 may strengthen the existing U/V activation audit to observe, for every
lane, both U and V `A/B/C` coefficients, `frac_bits`, candidate/result
generation and readiness at activation. It shall also check the stepper's
captured `a_r`, `b_r`, and `acc` re-anchor state and compare the first-A tuple
with return-A.

Q2 adds a production 640x480 timing A/B/C/A simulation that checks the
geometry-relevant region and compares initial A with return A. Keep the frozen
fixtures and arithmetic unchanged. Do not repeat the full repository gate;
its previously recorded unrelated T1D timeout remains unchanged.

Q3 may add only a compile-time U/V output diagnostic selector. It shall
register the actual depth-winner-selected U, V, valid, sync, and active signals
as one aligned stage, then map registered `U[14]` to red and `V[14]` to green
(blue zero). It may not register only winner ID and call that U/V-path
coverage.

No production interpolation, depth, winner, activation, UART loader, pacing,
or fixture changes are authorized by this contract. Preserve existing
top-level ports and all legacy profiles. Any production correction requires a
separate reviewed amendment after a falsifiable defect is isolated.

## 3. Ordered work

1. Strengthen the 80x100 activation test to compare complete U/V committed
   tuples and accumulator re-anchor state for A/B/C/A.
2. Run `python3 software/tests/test_gpu_t1i_uv.py` and
   `python3 software/tests/test_gpu_t1i_uv_uart_loader.py`.
3. Add and run `python3 software/tests/test_gpu_t1i_uv_production_timing.py`
   using 640x480 timing, frozen packets, and selected oracle samples. If it
   exceeds 60 seconds, run it only through `tools/run_detached_job.sh` with a
   new build-directory child and a frozen timeout.
4. Implement the compile-time registered U/V diagnostic and focused alignment
   regression only after Q1/Q2 source review. Do not build it yet.
5. Before any FPGA build, record a new owner-authorized attempt count,
   per-attempt timeout, and cumulative budget. The prior 3-build allowance is
   fully consumed.
6. After that authorization, program the exact diagnostic image and replay
   A/B/C/A, pausing for an operator photo after each scene.

## 4. Focused verification commands

```bash
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1i_uv_uart_loader.py
python3 software/tests/test_gpu_t1i_uv_production_timing.py
git diff --check
```

Do not run `bash tools/verify_repo.sh` in this tranche unless the owner
explicitly reopens T1i Q3; its earlier timeout remains unchanged.

## 5. Recorded results

* Q1: PASS. `test_gpu_t1i_uv.py` checks all four lanes' complete active U/V
  coefficient tuples and fractional widths, generation-matched readiness,
  accumulator `a_r`/`b_r`/`acc` activation anchors, and exact initial-A versus
  return-A tuple and pixel equality. The existing independent 80x100 oracle
  remains at 32,000 checked pixels.
* Q2: PASS. Detached run
  `build/gpu_t1i_uv_divergence_audit_20260924/prod_timing_run_01` has exactly
  one terminal marker, `COMPLETE`, exit 0, duration 271 seconds, and reports
  production 640x480 A/B/C/A timing with 32,000 top-left ROI samples matching
  the independent U/V oracle.
* Q3: PASS at source/test level. `T1I_UV_REG_DIAG` registers selected 56-bit U
  and V, shared validity, active, and sync; focused simulation checks the
  binary RGB mapping and the aligned one-cycle output timing. The Artix build
  selector is defined but has not been synthesized or programmed.
* No production interpolation, depth, coverage, winner, activation, UART, or
  fixture semantics were changed. The T1i physical return-A discrepancy
  remains unresolved because the registered U/V diagnostic has not yet been
  built and observed on hardware.
* The prior three-build allowance remains exhausted. Any further FPGA build
  must use the fresh bounded budget recorded in §6.

## 6. Owner-authorized hardware budget

The owner authorized a fresh maximum of two Artix builds, each capped at 3600
seconds, for a cumulative campaign maximum of 7200 seconds. Build 1 is the
frozen `T1I_UV_REG_DIAG` profile below. Build 2 is contingency-only for a
procedural/build-flow correction inside this diagnostic boundary and cannot
change interpolation, arithmetic, winner selection, activation, scene bytes,
pacing, or production semantics. Do not spend Build 2 if Build 1 produces a
valid registered-U/V bitstream.

Build 1 profile:

```text
A7_FREQ=25
GPU_T1D_UART=1
FOUR_PRIMITIVE_SCENE=1
T1H_SCALAR_SCENE=0
T1H_SCALAR_DIAG=0
T1I_UV_SCENE=1
T1I_UV_DIAG=1
T1I_UV_REG_DIAG=1
T1I_DEPTH_DIAG=0
A7_ARTIFACT_TAG=T1I_UV_REG_DIAG_B1_S1
bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

Detached evidence destination:
`build/gpu_t1i_uv_divergence_hw_20260924/build_01`

Build 1 terminal record: unit
`spu-build_01-20260924T033048Z-489836`; exactly one terminal marker,
`COMPLETE`; exit 0; duration 1390 seconds. The artifact is
`build/spu_a7_100t_GPUVGA_T1I_UV_REG_DIAG_B1_S1.bit`, SHA-256
`3bd663e65db659ddfa7dcc4b71082c1a490927ccf4d1994cf07d14f2aaeed376`.
The build log confirms the frozen selector value `T1I_UV_REG_DIAG=1`.

The exact artifact was loaded to SRAM with
`openFPGALoader -c dirtyJtag --freq 1000000`; the load reached 100%, and the
completion reported `isc_done 1`, `init 1`, and `done 1`. The initial frozen
Scene A packet was sent at 115200 8N1, 175 bytes, with `tcdrain` complete.
Transcript: `build/gpu_t1i_uv_divergence_hw_20260924/build_01/h1_scene_a_initial.json`.
Operator observation for initial A: **red left region, green right region,
small red artifact above the image**. This is the comparison baseline for
return A. The observation was recorded before B was sent.
Frozen Scene B was then sent at 115200 8N1, 175 bytes, with `tcdrain`
complete. Transcript:
`build/gpu_t1i_uv_divergence_hw_20260924/build_01/h1_scene_b.json`.
The operator referred to the photo as `IMG_1952.jpeg`; the image appeared in
the workspace as `IMG_1752.jpeg`, SHA-256
`d761b93eee76ade1847a66b4c8d729df339ea51f8cc04372e2daeef491cdcc6d`, and was
archived as
`build/gpu_t1i_uv_divergence_hw_20260924/build_01/scene_b_operator_capture.jpeg`.
It shows red and green regions, a yellow overlap at the left triangle, and
the small red artifact above. Frozen Scene C was then sent at 115200 8N1,
175 bytes, with `tcdrain` complete. Transcript:
`build/gpu_t1i_uv_divergence_hw_20260924/build_01/h1_scene_c.json`.
The Scene C photo `IMG_1754.jpeg`, SHA-256
`b4370196f7ab2c861f8cecde72c94fe068ac1a8578ae2d79225f73a6613144f6`, is
archived as
`build/gpu_t1i_uv_divergence_hw_20260924/build_01/scene_c_operator_capture.jpeg`.
It shows a broad yellow-left/green-right triangle with a red region above.
Scene C was recorded before sending return A; compare the final capture to the
initial-A baseline before classifying the physical discriminator.
Frozen return Scene A was sent at 115200 8N1, 175 bytes, with `tcdrain`
complete. Transcript:
`build/gpu_t1i_uv_divergence_hw_20260924/build_01/h1_scene_a_return.json`.
The operator reports that the small artifact remains visible on return A and
that the broad regions appear to match initial A (red left, green right).
This is operator-observed evidence; there is no return-A photo in this
record. The large-region history-dependent color change seen on the original
combinational U/V image was not reproduced with the registered-U/V image.
This supports output settling/alignment as a contributor to that
history-dependent color discrepancy. It does not explain or eliminate the
small red artifact, whose cause remains unresolved.

**H1 classification:** registered U/V physical replay PASS at the limited
operator-observation level for A/B/C scene changes and broad return-A color
repeatability. The small artifact remains physically visible, so the visual
artifact investigation is not closed. No production interpolation or raster
correction is authorized by this result. Build 1 produced a valid image, so
do not consume contingency Build 2 merely for repetition.

## 7. Interpretation

* A mismatch in committed U/V tuples or re-anchor state localizes a digital
  activation-state defect; stop before any production correction.
* Identical tuples but a production-timing oracle mismatch localizes a
  raster/phase interaction; stop before changing interpolation arithmetic.
* Identical tuples and clean production-timing pixels, followed by a clean
  registered U/V hardware replay, supports an output-settling/alignment cause.
* A persistent registered U/V physical return-A mismatch with clean
  simulation remains unresolved; it does not authorize a speculative
  production fix.

## 8. Stop conditions

* Any need to change arithmetic, coverage, winner priority, scene bytes,
  packet size, activation policy, or legacy profile behavior: HALT and revise
  scope before editing RTL.
* Any selector/profile combination that can affect non-diagnostic builds:
  HALT and correct the guard.
* Any build launch without the fresh owner-authorized budget: HALT.
