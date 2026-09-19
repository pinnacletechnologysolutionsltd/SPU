# Engineering Contract: Wukong GPU Prepared-State Cost

**Date:** 2026-09-13
**Contract ID:** `contract_wukong_gpu_prepared_cost_2026-09-13.md`
**Status:** COMPLETE — D, tool-flow failure before synthesis/P&R

**Roles:**
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** unassigned
- **Integration Auditor:** `bash tools/verify_repo.sh` + owner

## 1. Objective and terminal boundary

Measure the incremental post-route resource and timing cost of T1c prepared
scene banking on the Wukong XC7A100T at the frozen 25 MHz pixel-clock target.
Build one matched control (`PS0`) and one matched candidate (`PS1`) from the
same source tree, seed, constraints, stimulus, and toolchain.

Stop after synthesis/P&R evidence and a written comparison. Do not pack or
load a bitstream. Do not operate hardware. Do not edit the T1c data path.

## 2. Pre-execution halt findings

1. `synth_a7_gpu_vga.ys` omits `spu_scene_loader.v`,
   `spu_scene_unpack.v`, and `spu_prepared_scene_control.v`. An unmodified
   build cannot elaborate current `spu_gpu_top.v`.
2. The board top uses the default `PREPARED_SCENE=0`. An ordinary GPUVGA build
   therefore cannot measure T1c.
3. A constant-inactive scene ingress permits synthesis to remove the banking
   path. Both builds require the same retained, dynamic, pixel-clocked
   synthesis stimulus.
4. `build_a7.sh` currently emits one canonical GPUVGA artifact name. The two
   builds require distinct `_PS0_S1` and `_PS1_S1` names before either runs.

If any correction requires functional edits to `hardware/rtl/gpu/spu_gpu_top.v`
or the three T1c modules, HALT and request a revised contract.

## 3. Scoped files

Modify only:

- `hardware/boards/artix7/spu_a7_gpu_vga_top.v`
- `hardware/boards/artix7/synth_a7_gpu_vga.ys`
- `hardware/boards/artix7/build_a7.sh`
- `software/tests/test_gpu_top_integration.py` only if its explicit source
  manifest must follow the synthesis manifest
- `docs/WUKONG_GPU_CHECKPOINT_2026-09-11.md` after terminal evidence exists
- this contract, status and terminal evidence only

Do not modify `hardware/rtl/gpu/spu_gpu_top.v`, `spu_scene_loader.v`,
`spu_scene_unpack.v`, `spu_prepared_scene_control.v`, arithmetic RTL, XDC,
scene constants, clocks, reset logic, VGA outputs, or tests' expected pixels.

## 4. Literal implementation

1. Add the three missing T1c source paths to `synth_a7_gpu_vga.ys`.
2. Add board-top parameters `PREPARED_SCENE=0` and `COST_STIMULUS=0`. Pass
   `PREPARED_SCENE` literally to `spu_gpu_top`.
3. Under `generate if (COST_STIMULUS)`, add one 9-bit nonzero-seeded,
   pixel-clocked synthesis-stimulus register in the board top. Mark the
   register `(* keep *)`. Drive `scene_rx_byte` from bits `[7:0]` and
   `scene_rx_valid` from bit `[8]`; drive both to zero when the generate block
   is absent. The register and update logic must be identical and retained in
   PS0 and PS1. Do not connect it to a physical pin or output. Canonical builds
   with the environment selector unset must retain neither the stimulus nor
   prepared-scene logic.
4. Add optional `GPU_PREPARED_SCENE=0|1` validation to `build_a7.sh`. Reject
   any explicit value for every spin except GPUVGA. Unset means the canonical
   build, `PREPARED_SCENE=0`, `COST_STIMULUS=0`, with no artifact suffix.
5. For an explicit GPUVGA selector, apply `chparam -set PREPARED_SCENE` and
   `chparam -set COST_STIMULUS 1` before synthesis. Suffix every JSON, P&R,
   timing, metric, and potential bitstream path with
   `_PS${GPU_PREPARED_SCENE}_S${A7_SEED}`. Do not overwrite the canonical
   `spu_a7_100t_GPUVGA.*` artifacts.
6. Keep `A7_SEED=1`, `A7_FREQ=25`, XC7A100T, the existing GPUVGA XDC, and all
   other build selectors identical across PS0 and PS1.
7. Add a `synth_pnr` step which runs only `synth && pnr`; it must not call
   `pack`. Confirm the build log prints the prepared selector and exact
   artifact path.

## 5. Acceptance and classifications

Record for both PS0 and PS1: Yosys cell counts, `SLICE_LUTX`, `SLICE_FFX`,
DSP48E1, BRAM, routed Fmax, worst setup path/slack when emitted, seed, source
commit, dirty state, and routed JSON/FASM SHA-256. Compute absolute and
percentage PS1-minus-PS0 deltas.

- **A — PASS:** both runs exit 0, PS1 retains the T1c hierarchy/state, and PS1
  routed Fmax is at least 25.00 MHz.
- **B — COST PASS / TIMING FAIL:** both runs exit 0 and retain T1c, but PS1
  routed Fmax is below 25.00 MHz.
- **C — INVALID COMPARISON:** selectors, seed, constraints, source identity,
  stimulus, or toolchain differ; or PS1 does not retain T1c state.
- **D — TOOL FAILURE:** synthesis or P&R exits nonzero for an infrastructure
  or tool reason without an RTL acceptance result.
- **E — REPOSITORY FAILURE:** focused or repository verification fails.

No classification licenses bitstream loading or a silicon claim.

## 6. Commands and frozen campaign budget

Run the focused check in the foreground; HALT on nonzero:

```bash
python3 software/tests/test_gpu_top_integration.py
```

Then launch exactly one detached job per agent turn, in this order, and end
the turn after `LAUNCHED`. Proceed only when the prior job has exactly one
terminal marker and it is `COMPLETE`.

```bash
tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_cost_20260913/verify_repo_01 \
  --timeout 3600 --notify-desktop -- bash tools/verify_repo.sh

tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_cost_20260913/ps0_seed1_01 \
  --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 \
  GPU_PREPARED_SCENE=0 bash hardware/boards/artix7/build_a7.sh 100t gpuvga synth_pnr

tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_cost_20260913/ps1_seed1_01 \
  --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 \
  GPU_PREPARED_SCENE=1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga synth_pnr
```

Frozen budget: one repository attempt plus two build attempts, maximum three
launched jobs, per-attempt timeouts as above, cumulative timeout 18,000
seconds. Every launch consumes its slot. Do not rerun, change seed, extend a
timeout, repair a failed gate, substitute a tool, or load hardware without a
new owner authorization.

## 7. Mandatory stop conditions

- HALT on any pre-execution contradiction, unrelated dirty-file overlap,
  source-manifest mismatch, artifact collision, verification failure, missing
  terminal marker, timeout, or nonzero build exit.
- HALT if PS0 retains prepared-state logic or PS1 loses it; do not report a
  numeric delta from an invalid comparison.
- Do not call either result silicon-verified. Label it synthesis/P&R evidence.

## 8. Terminal result — 2026-09-13

The repository job completed with exit 0: 230 PASS / 0 FAIL. The PS0 job then
failed with exit 1 after one second, before synthesis or P&R. The synthesis
manifest's terminal `hierarchy -top spu_a7_gpu_vga_top` removed the
unparameterized `spu_gpu_top`; the subsequent PS0 `chparam` re-derived the
board top and could no longer resolve its `spu_gpu_top` instance.

Classification: **D — TOOL FAILURE**. No resource or timing comparison exists.
PS1 was not launched. Two of the three frozen job slots were consumed; the
unused slot is not authorization for a repair or substitute run.

Evidence:
`build/wukong_gpu_prepared_cost_20260913/ps0_seed1_01/result.json`.

Minimal proposed correction, not applied: remove the manifest's premature
`hierarchy` pass and let `build_a7.sh` apply parameters before its single final
hierarchy/synthesis pass. Any correction and new PS0/PS1 campaign require a
new owner authorization and newly frozen budget.

## Historical reconciliation — superseded by 2026-09-19 retry

The terminal D result above remains preserved as the original campaign outcome.
Under the separately authorized contract
`contract_wukong_gpu_prepared_cost_2026-09-19.md`, the corrected flow completed
one repository gate and matched PS0/PS1 synthesis/P&R:

- repository gate: `230 PASS / 0 FAIL`;
- PS0: 9,306 cells, 7,900 routed LUTs, 2,428 routed FFs, 45.46 MHz
  `clk_pixel`;
- PS1: 15,941 cells, 12,903 routed LUTs, 3,799 routed FFs, 43.44 MHz
  `clk_pixel`;
- both runs passed the 25 MHz constraint and retained the intended T1c
  hierarchy.

This later result is classification **A — PASS**, post-route evidence only.
It does not rewrite or invalidate the original D result and does not constitute
silicon verification.
