# T1p H1 Integration Debt: T1d Repeatability Timeout Triage

**Date:** 2026-09-29  
**Status:** COMPLETE — ISOLATED PASSES AND RENEWED REPOSITORY GATE PASS  
**Roles:** Spec Author / Halt-and-Flag Implementer / Integration Auditor

## 1. Runbook

Inspect the consumed H1 gate and run one isolated phase-0 T1d diagnostic:

```bash
cat build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_01/result.json
python3 -m py_compile tools/triage_t1d_repeatability_runtime.py
tools/run_detached_job.sh \
  --output build/gpu/t1p_t1d_timeout_triage_20260929/isolated_phase0/run_01 \
  --timeout 180 --notify-desktop -- \
  python3 tools/triage_t1d_repeatability_runtime.py \
  --phase 0 --reset 0 --run-timeout 150
```

After `LAUNCHED`, end the agent turn. Interpret only `COMPLETE`, `FAILED`, or
`TIMEOUT` together with `result.json` in a later session. Do not relaunch
because a log is quiet or a session ended.

## 2. Frozen budget and stop rules

The owner requested isolated runtime diagnosis before any renewed repository
gate. Freeze a maximum of three isolated runs, each with a 180-second external
timeout and a 150-second `vvp` timeout, for a 540-second cumulative campaign
budget. Run 01 consumes one slot once launched. Further runs, if needed for
repeatability, must use new `run_02` and `run_03` evidence directories and the
same exact command except the output path. Do not increase either timeout or
the attempt count within this campaign.

If compilation fails, `vvp` reports `FAIL`, exits nonzero, or omits the PASS
verdict, stop the campaign and investigate semantics. If `vvp` times out at
150 seconds, stop; do not label it a 60-second budget issue. If the test
passes, record compile and `vvp` wall times before deciding whether more
samples are needed. Do not launch a renewed full repository gate until the
cause and any corrective edit have been reviewed and a separate gate budget
has been frozen.

## 3. Exact test scope

The H1 `tools/verify_repo.sh` attempt at
`build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_01/` ended `FAILED`,
exit 1, after 1,004 seconds. Hygiene and citation checks passed. The single
Verilog timeout was `spu_t1d_repeatability_diag_tb.v` at its 60-second
per-test cap; `run_all_tests.py` reported 236 passes and two failure counts.
The same bench passed in the earlier D4 P0 and P1 repository gates.

`tools/triage_t1d_repeatability_runtime.py` compiles the dedicated T1d D1
source list with `GPU_T1D_DIAG` and `GPU_T1D_UART` defined, plus
`spu_depth_compare4.v`, which the repository runner discovers from the GPU
directory. The phase-0/reset-0 run matches the bench's default plusargs used
by the repository runner. It reports compilation time, `vvp` wall time, exit
code, and the bench verdict. The script is under 100 lines.

Run 01 was consumed but failed during harness elaboration, before `vvp`:
the copied list omitted `spu_depth_compare4.v`. This was a triage-tool setup
error, not a semantic result or measured runtime. The source was added, and
`python3 tools/triage_t1d_repeatability_runtime.py --compile-only` now passes
in 0.199 seconds. The unchanged three-attempt campaign had two slots
remaining at that point. Run 02 used the same phase/reset and timeout settings
and completed successfully: compile 0.080 seconds; `vvp` 55.506 seconds; D1
semantic PASS; detached result `COMPLETE`, exit 0, duration 55 seconds. Run
01's compile setup failure and run 02's near-cap PASS do not establish
consistent runtime. Run 03 used the exact same phase/reset and timeout
settings and completed successfully: compile 0.083 seconds; `vvp` 50.722
seconds; D1 semantic PASS; detached result `COMPLETE`, exit 0, duration 51
seconds.

Across the two valid isolated samples, D1 passed at 55.506 and 50.722
seconds. The H1 repository run exceeded its 60-second cap once. Classify this
as insufficient runner headroom under full-suite load, with no semantic
regression observed in the bounded samples. `run_all_tests.py` now gives this
bench a 90-second cap, retaining 30 seconds of headroom over the slowest
measured isolated run.

After `py_compile` and `git diff --check`, freeze one renewed repository-gate
attempt, 1,800 seconds per attempt and cumulative. Run:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

The attempt is consumed on any outcome. Do not retry or increase its timeout
without renewed owner authorization. Interpret only the durable terminal
marker and `result.json` in a later session.

This test diagnoses the T1d regression gate timeout only. It does not modify
T1p RTL or its SRAM, UART, or visual evidence. A passing isolated run does
not itself make the failed H1 repository gate complete.

**Renewed gate result (2026-09-29): COMPLETE, exit 0.** The durable result
at `build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/result.json`
records 937 seconds. The corrected 90-second T1d test passed;
`run_all_tests.py` reported 237 passes and zero failures. This closes the
T1p post-transport repository integration debt.

## 4. Evidence decision

| Observation | Classification | Next action |
|---|---|---|
| Semantic PASS, `vvp` near or above 60 seconds | Test-specific runner budget debt | Retain measured test-specific headroom and verify in the renewed gate |
| Semantic PASS, `vvp` clearly below 60 seconds | Runtime variability or contention | Record bounded samples; inspect host load and runner differences |
| Simulation reports `FAIL`, nonzero exit, or no PASS verdict after successful compile | Possible regression | Halt and investigate the failing assertion or wait state |
| Isolated 150-second simulation timeout | Unresolved hang or severe slowdown | Halt; do not increase caps without new authorization |

**Evidence boundary:** T1p's route/timing, SRAM load, CH340 transport, and
operator-observed enlarged-scene return-A pass remain separate claims. Exact
physical pixel comparison remains unmeasured, and configuration flash was
not written.
