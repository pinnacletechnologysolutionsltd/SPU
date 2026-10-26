# Engineering Contract: Wukong GPU Prepared-State Cost Retry

**Date:** 2026-09-19  
**Contract ID:** `contract_wukong_gpu_prepared_cost_2026-09-19.md`  
**Status:** COMPLETE — A, post-route cost/timing pass

## 1. Objective and boundary

Measure the incremental post-route resource and timing cost of T1c prepared
scene banking on the Wukong XC7A100T at the frozen 25 MHz pixel-clock target.
Build one matched control (`PS0`) and one matched candidate (`PS1`) from the
same source tree, seed, constraints, stimulus, and toolchain.

Stop after repository verification plus synthesis/P&R evidence and a written
comparison. Do not pack or load a bitstream. Do not operate hardware. Do not
edit the T1c data path.

## 2. Authorized source state

The worktree already contains the minimal flow correction from the terminal
2026-09-13 campaign:

1. the GPU synthesis manifest includes the three T1c scene modules and does
   not run a premature `hierarchy` pass;
2. `build_a7.sh` applies `PREPARED_SCENE` and `COST_STIMULUS` before the final
   hierarchy/elaboration pass; and
3. PS0 and PS1 artifact names are suffixed with `_PS${selector}_S${seed}`.

The focused integration check passed before this campaign:

```text
115198 active pixels checked; 0 mismatches
```

Do not make unrelated edits or repair failures under this contract.

## 3. Frozen comparison

| Item | Value |
|---|---|
| Device | XC7A100T |
| Clock target | 25 MHz |
| Seed | 1 |
| Control | `GPU_PREPARED_SCENE=0` |
| Candidate | `GPU_PREPARED_SCENE=1` |
| Stimulus | `COST_STIMULUS=1` for both explicit selectors |
| Build step | `synth_pnr` only |
| Hardware | prohibited |
| Bitstream packing | prohibited |

Record for both runs: Yosys cell counts, LUT, FF, DSP48E1, BRAM, routed Fmax,
worst setup path/slack when emitted, seed, source commit, dirty state, and
routed JSON/FASM SHA-256. Compute absolute and percentage PS1-minus-PS0
deltas.

## 4. Acceptance classifications

- **A — PASS:** both runs exit 0, PS1 retains T1c state, and PS1 routed Fmax
  is at least 25.00 MHz.
- **B — COST PASS / TIMING FAIL:** both runs exit 0 and retain T1c, but PS1
  routed Fmax is below 25.00 MHz.
- **C — INVALID COMPARISON:** selectors, seed, constraints, source identity,
  stimulus, or toolchain differ, or PS1 does not retain T1c state.
- **D — TOOL FAILURE:** synthesis or P&R exits nonzero without an RTL
  acceptance result.
- **E — REPOSITORY FAILURE:** focused or repository verification fails.

No classification licenses bitstream loading or a silicon claim.

## 5. Commands and frozen budget

The focused check has already passed. Launch exactly one detached job at a time
in this order. Do not launch the next job until the previous job has exactly
one terminal marker and it is `COMPLETE`.

```bash
tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_cost_20260919/verify_repo_01 \
  --timeout 3600 --notify-desktop -- bash tools/verify_repo.sh

tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_cost_20260919/ps0_seed1_01 \
  --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 \
  GPU_PREPARED_SCENE=0 bash hardware/boards/artix7/build_a7.sh 100t gpuvga synth_pnr

tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_cost_20260919/ps1_seed1_01 \
  --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 \
  GPU_PREPARED_SCENE=1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga synth_pnr
```

Budget: one repository attempt plus two build attempts; maximum three launched
jobs; per-attempt timeouts as above; cumulative timeout 18,000 seconds. Every
launch consumes its slot. Do not rerun, change seed, extend a timeout, repair a
failed gate, substitute a tool, or load hardware without renewed authorization.

## 6. Terminal evidence — 2026-09-19

The repository gate completed `230 PASS / 0 FAIL`. The focused GPU integration
check completed with `115198 active pixels checked` and `0 mismatches`. Both
post-route builds completed with exit 0 at the same commit (`e62c7e3`), device,
seed, 25 MHz constraint, and toolchain.

| Metric | PS0 | PS1 | Delta PS1-PS0 | Relative delta |
|---|---:|---:|---:|---:|
| Yosys cells | 9,306 | 15,941 | +6,635 | +71.3% |
| Routed `SLICE_LUTX` | 7,900 | 12,903 | +5,003 | +63.3% |
| Routed `SLICE_FFX` | 2,428 | 3,799 | +1,371 | +56.5% |
| DSP48E1 | 2 | 2 | 0 | 0.0% |
| BRAM | 0 | 0 | 0 | 0.0% |
| `clk_pixel` Fmax | 45.46 MHz | 43.44 MHz | -2.02 MHz | -4.4% |

Both routed clocks passed the 25 MHz constraint. PS1 retained
`spu_prepared_scene_control` and `spu_scene_loader` in the synthesized
hierarchy.

Classification: **A — PASS**. This is simulation and synthesis/P&R evidence
only; it is not silicon verification and does not authorize bitstream loading
or hardware operation.

Artifacts:

- PS0 metrics: `build/metrics/artix7_100t_GPUVGA_PS0_S1.json`
- PS1 metrics: `build/metrics/artix7_100t_GPUVGA_PS1_S1.json`
- PS0 routed JSON SHA-256:
  `9d7c908b4c4664153975d6a80e49417b40614de5ae1aa7b8e2449e7b08258222`
- PS1 routed JSON SHA-256:
  `c76ed3b5eff7290d9afde4cd29a26136582e4f0610d6a048d4458019fb11a4a3`
