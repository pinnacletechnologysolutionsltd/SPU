# Engineering Contract: GPU T1r Q1 Focused-Gate Recovery v2

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-PALETTE-PAIR-Q1-RECOVERY-V2-2026-10-01`  
**Status:** DRAFT — fresh focused-gate execution NOT AUTHORIZED  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** exact T1r Python/RTL oracle and compatibility checks

## 0. Purpose and execution boundary

This contract replaces only the focused-test procedure in [Q1 recovery v1](contract_gpu_t1r_palette_pair_q1_recovery_2026-10-01.md). It does not revise T1r RTL semantics, source identity, packet layout, the earlier failed campaign record, or the stop conditions. It does not authorize repository verification, synthesis, route, FPGA programming, UART traffic, or visual observation.

Use `python3 software/tests/test_gpu_t1r_palette_pair.py` as the sole T1r focused invocation. That test compiles the exact `spu_gpu_t1r_palette_pair_tb` against its declared RTL inputs, runs it with Icarus/VVP, and checks the independent Python scene, packet, palette, lane-coverage, and profile oracles. The T1r focused scope has no required C++ oracle; the twelve C++ tests printed during recovery v1 were unrelated post-filter work from `run_all_tests.py` and are not part of this gate.

## 1. Historical evidence and current state

Preserve these prior outcomes without upgrading them:

| Evidence | Result | Use in v2 |
|---|---|---|
| Original T1r direct oracle | PASS | Historical only; execute once fresh below |
| Original filtered triage | TIMEOUT / exit 124 at 600 s | Infrastructure-inconclusive; original attempt consumed |
| First T1p compatibility invocation | FAIL at pixel `(10,10)` | Original invocation consumed |
| Post-failure T1p correction rerun | PASS | Diagnostic only; cannot replace the consumed invocation |
| Recovery v1 direct T1r oracle | PASS | Diagnostic only; execute once fresh below |
| Recovery v1 selected T1r Verilog bench | PASS | Diagnostic only; it ran inside an incomplete runner command |
| Recovery v1 twelve C++ tests | PASS | Out of scope for T1r focused acceptance |
| Recovery v1 filtered runner command | Interrupted at 300 s, exit 130 | Incomplete; generator phase was active; not a pass |

The T1r Verilog bench passed before the recovery v1 runner continued into twelve C++ tests and then the unrelated generator phase. `TB_FILTER` narrows Verilog testbench discovery only; do not use `run_all_tests.py` for this focused gate. Keep the runner correction and its hash solely as historical evidence: [diff](../build/gpu/t1r_palette_pair_20261001/recovery_01/t1r_filter_correction.diff), [corrected runner hash](../build/gpu/t1r_palette_pair_20261001/recovery_01/run_all_tests.py.sha256), and [interrupted run record](../build/gpu/t1r_palette_pair_20261001/recovery_01/focused_campaign_status.md).

## 2. Frozen source identity

Use the exact implementation, RTL, testbench, oracle, helper, fixture, and T1o/T1p/T1q compatibility source hashes from §1 of [Q1 recovery v1](contract_gpu_t1r_palette_pair_q1_recovery_2026-10-01.md). The `run_all_tests.py` pre-recovery hash there describes the old runner. The post-correction hash `d1f5a3c4cf11013af16ca64fffc6d79c9fe8b44f43af7a1d07dafa65608586e5` and its diff are historical evidence only; neither runner version is an input to a v2 test invocation.

Before the first command, recompute every implementation and test input hash in recovery v1 §1, excluding `run_all_tests.py`. Save the command output as `build/gpu/t1r_palette_pair_20261001/recovery_v2/source_hashes.txt`. Halt before testing if any hash differs. Do not modify source files under this contract.

## 3. Fresh focused campaign

Run the following four commands once each, in order. Each command has a 300-second wall-clock maximum; cumulative campaign budget is 1,200 seconds. These Python checks have previously completed below 60 seconds, so run them as bounded foreground commands. Each `timeout` result of 124, nonzero exit, missing output, or source-hash mismatch consumes its slot and halts the campaign.

```bash
timeout 300s python3 software/tests/test_gpu_t1r_palette_pair.py
timeout 300s python3 software/tests/test_gpu_t1q_truth_table.py
timeout 300s python3 software/tests/test_gpu_t1p_predicate_bits.py
timeout 300s python3 software/tests/test_gpu_t1o_per_primitive_material.py
```

For each invocation, preserve the exact command, start and end UTC times, exit code, stdout, stderr, and the source-hash manifest in `build/gpu/t1r_palette_pair_20261001/recovery_v2/`. Require each command to print its expected `PASS` record and exit 0. Do not retry, substitute commands, increase a timeout, or continue to a later command after a failed or unavailable result.

The first invocation is the complete T1r functional gate: its Verilog bench must pass, and its independent Python checks must confirm the 186-byte packet layout, four-lane false/true palette outcomes, all lane/predicate coverage, invalid-byte rejection and recovery, and incompatible-profile rejection. The following three invocations are unchanged compatibility gates; run them only after the complete T1r Python command exits 0.

## 4. Acceptance and downstream boundary

The recovery v2 focused gate passes only if all four fresh commands complete with exit 0 on the frozen source state. A passing T1r subtest inside a longer command does not qualify if the Python command itself is incomplete or nonzero.

After a complete focused-gate pass, report the evidence and request a separate owner decision before any downstream work. The repository gate, mandatory Padé synthesis, T1r route, hardware interface actions, and silicon observations remain locked. If any command fails, times out, or becomes unavailable, mark the campaign HALTED and do not infer a semantic T1r failure from infrastructure-only outcomes.

| Evidence claim | Recovery v2 starting state |
|---|---|
| T1r RTL functional oracle | Historical PASS; fresh result NOT RUN |
| Filtered `run_all_tests.py` invocation | Excluded from this focused gate |
| Fresh T1q/T1p/T1o compatibility | NOT RUN |
| Repository gate | NOT RUN; not authorized here |
| Synthesis/place-and-route | NOT RUN; not authorized here |
| Hardware/interface/silicon evidence | NOT RUN; not authorized here |
