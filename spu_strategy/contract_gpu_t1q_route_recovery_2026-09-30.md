# Engineering Contract: T1q Artix-7 Route Recovery

**Date:** 2026-09-30  
**Contract ID:** `GPU-T1Q-ROUTE-RECOVERY-2026-09-30`  
**Status:** `COMPLETE; ROUTE/PACK/TIMING PASS; SUSPEND ACCOUNTING VERIFIED`  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `tools/verify_repo.sh` plus owner evidence review

## 0. Objective and boundary

Run one renewed seed-1 Artix-7 100T place-and-route/pack attempt for the
existing default-off T1q four-bit truth-table material profile. Make no RTL,
test, fixture, board-profile, or build-script changes under this contract.
Do not program FPGA SRAM or flash, transmit UART packets, or make visual or
silicon claims.

The first route attempt was launched at
`build/gpu/t1q_truth_table_20260929/build_seed1/run_01/` and then stopped
before a durable terminal marker was written. Its outcome is unavailable and
its frozen attempt slot is consumed. This recovery contract defines one new
attempt. The T1q repository gate and mandatory Padé build have separately
completed with exit 0. The T1d triage and renewed T1p repository gate are
complete as recorded in
`spu_strategy/contract_gpu_t1p_t1d_timeout_triage_2026-09-29.md`.

## 1. Halt-and-flag review

The interrupted build left two generated files at the build script's fixed
artifact paths. The recovery build will overwrite those paths, so preserve
their exact bytes into the first attempt's evidence directory before launch.
Do not infer route completion, route failure, timing, or pack status from
these partial files or their logs.

The Q1 source and profile are unchanged from the first launch. Freeze the
route-relevant source bytes by the SHA-256 values below. Stop if any value
differs during preflight; request a new source review before changing the
configuration or regenerating artifacts.

| File | SHA-256 |
|---|---|
| `hardware/rtl/gpu/spu_gpu_top.v` | `ecdce615c9d3ffda7c1aa75ff0905ae6a4a9941adac9896676e3ac6adb38eee8` |
| `hardware/rtl/gpu/spu_scene_loader.v` | `6d4e142d015bf000d656058ca86b13677fb4849b1c1eebe6f675e219d68e2711` |
| `hardware/rtl/gpu/spu_material_op_select4.v` | `0fadfdc7b6a0ba2b64a820097c3b7edfe4835a52b5087da6d9dcb1e151a0341f` |
| `hardware/rtl/gpu/spu_material_predicate_select4.v` | `115c9685c544f8a37f3ee4ae3dedac8202b2a8f6463fb7178cac7efadddae19c` |
| `hardware/boards/artix7/spu_a7_gpu_vga_top.v` | `a2e7a27b792defd2dbc21aab9b2438b5d58c71eff80c2f1fb22e681e69c6f57f` |
| `hardware/boards/artix7/build_a7.sh` | `354ebffdd920b6028aff32ab60e5c8a00469d0c3de226036bb5cd3aabe55cc61` |
| `hardware/boards/artix7/synth_a7_gpu_vga.ys` | `4483f3d6e34e307c15bb6c0b9624edfb3399c962c5cca76f5b80a1a37966a7c2` |
| `hardware/boards/artix7/spu_a7_vga.xdc` | `cf29830aa15f48919b142e761258883f9c8fbdf1c772b609db40c13be6fe0fbb` |
| `hardware/boards/artix7/spu_a7_vga_fix.xdc` | `df7301f9418b3d29116a9e2dcfd5ab2c040457ff11ccf5c4a398d3c3d5cd344e` |

## 2. Preconditions and exact recovery budget

Before launch, run from the repository root:

```bash
cat build/gpu/t1q_truth_table_20260929/repo_gate/run_01/result.json
cat build/gpu/t1q_truth_table_20260929/pade_synthesis/run_01/result.json
cat build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_02/result.json
cat build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_03/result.json
cat build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/result.json
test -f build/gpu/t1q_truth_table_20260929/repo_gate/run_01/COMPLETE && test ! -e build/gpu/t1q_truth_table_20260929/repo_gate/run_01/FAILED && test ! -e build/gpu/t1q_truth_table_20260929/repo_gate/run_01/TIMEOUT
test -f build/gpu/t1q_truth_table_20260929/pade_synthesis/run_01/COMPLETE && test ! -e build/gpu/t1q_truth_table_20260929/pade_synthesis/run_01/FAILED && test ! -e build/gpu/t1q_truth_table_20260929/pade_synthesis/run_01/TIMEOUT
test -f build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_02/COMPLETE && test ! -e build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_02/FAILED && test ! -e build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_02/TIMEOUT
test -f build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_03/COMPLETE && test ! -e build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_03/FAILED && test ! -e build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_03/TIMEOUT
test -f build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/COMPLETE && test ! -e build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/FAILED && test ! -e build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/TIMEOUT
sha256sum hardware/rtl/gpu/spu_gpu_top.v hardware/rtl/gpu/spu_scene_loader.v hardware/rtl/gpu/spu_material_op_select4.v hardware/rtl/gpu/spu_material_predicate_select4.v hardware/boards/artix7/spu_a7_gpu_vga_top.v hardware/boards/artix7/build_a7.sh hardware/boards/artix7/synth_a7_gpu_vga.ys hardware/boards/artix7/spu_a7_vga.xdc hardware/boards/artix7/spu_a7_vga_fix.xdc
git diff --check
test ! -e build/gpu/t1q_truth_table_20260929/build_seed1/run_02
test ! -e build/gpu/t1q_truth_table_20260929/build_seed1/run_01/pre_retry_spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json
test ! -e build/gpu/t1q_truth_table_20260929/build_seed1/run_01/pre_retry_spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json.nextpnr.log
test ! -e build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json.pnr.json
test ! -e build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json.timing_report.json
test ! -e build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit
test ! -e build/metrics/artix7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json
test ! -e build/metrics/artix7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.md
```

Require the five listed repository and T1d/T1p prerequisite runs to have
exactly one durable `COMPLETE` marker and `result.json` exit code 0. Require
every source hash above to match. Require the new evidence path and all
listed generated output paths to be absent. Stop on any failed precondition.

The recovery budget was exactly one launch, with a 1,800-second per-attempt
timeout and 1,800-second cumulative campaign budget. The attempt is consumed
on this outcome. No further route attempt or timeout increase is included.

Before the build, preserve the two files that would otherwise be overwritten:

```bash
cp build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json build/gpu/t1q_truth_table_20260929/build_seed1/run_01/pre_retry_spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json
cp build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json.nextpnr.log build/gpu/t1q_truth_table_20260929/build_seed1/run_01/pre_retry_spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json.nextpnr.log
sha256sum build/gpu/t1q_truth_table_20260929/build_seed1/run_01/pre_retry_spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json build/gpu/t1q_truth_table_20260929/build_seed1/run_01/pre_retry_spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json.nextpnr.log
```

Require the copied hashes to equal `006901ac62f41d4cc97dbaf7c3e7a867151eff6ff70ff570695a6427b6650aa5` and
`6c4462bf6d530f3dbe940addea6d2bc06e28de08d1a20ee480aba38a9dfee4ac`,
respectively. Do not remove or alter the original generated files before the
recovery attempt.

## 3. Frozen route configuration

Launch exactly once after owner authorization of this contract's recovery
budget:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1q_truth_table_20260929/build_seed1/run_02 \
  --timeout 1800 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 \
    FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
    T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
    T1O_PER_PRIMITIVE_MATERIAL=0 T1P_PER_PRIMITIVE_PREDICATES=0 \
    T1Q_TRUTH_TABLE_MATERIAL=1 A7_ARTIFACT_TAG=T1Q_TRUTH_TABLE_MATERIAL_Q1 \
    bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
```

After `LAUNCHED`, record the unit and evidence directory and end the agent
turn. Do not poll or wait for deterministic build completion in that turn.

## 4. Result interpretation and stop rules

In a later session, inspect the evidence only when exactly one of
`COMPLETE`, `FAILED`, or `TIMEOUT` exists, paired with `result.json`.
No marker means the result is unavailable. Never infer a result from logs,
elapsed time, or process state.

For `COMPLETE`, require exit code 0, the generated bitstream, and
`build/metrics/artix7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json` with
`fmax.clk_pixel.status` equal to `PASS` and `fmax.clk_pixel.achieved_mhz` at
least 25.00. Report synthesis, route/pack, and timing as separate evidence
claims. For `FAILED`, `TIMEOUT`, a missing required artifact, or pixel Fmax
below 25.00 MHz, stop. Do not retry or change the profile under this budget.

This contract makes no FPGA SRAM, configuration flash, UART, visual, or
silicon claim. Any such step requires a separate contract and budget.

## 5. Recovery result and suspend accounting

The sole recovery attempt at
`build/gpu/t1q_truth_table_20260929/build_seed1/run_02/` has exactly one
terminal marker, `COMPLETE`. `result.json` records exit 0, configured timeout
1,800 seconds, and `duration_seconds=39754`. The generated bitstream exists
at `build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit`. Post-route
metrics report `clk_pixel=36.92 MHz`, status `PASS`, against 25.00 MHz.

The 39,754-second timestamp duration includes system suspend. The detached
worker records `started_epoch` and `ended_epoch` with `date +%s` in
`tools/run_detached_job_worker.sh`; that subtraction includes the suspended
interval. The system journal records the run starting at 2026-09-30 10:05:37
NZST, `user.slice` frozen for suspend at 10:18:44, and thawed at 21:05:22.
The detached service completed at 21:08:11. Systemd reports 15m57.803s of
service wall time and 18m14.870s CPU time. The suspend gap was 10h46m38s;
active service wall time remained below the 1,800-second limit. The command
returned exit 0 rather than timeout status 124.

Classification: T1q seed-1 route, pack, and pixel-clock gate PASS on the
recorded source/profile. The result's `duration_seconds` is suspend-inflated
and is not the active service runtime. This finding is recorded separately
in `docs/DETACHED_JOB_SUSPEND_ACCOUNTING_2026-09-30.md`. It does not imply
SRAM programming, configuration flash, UART, visual, or silicon evidence.
