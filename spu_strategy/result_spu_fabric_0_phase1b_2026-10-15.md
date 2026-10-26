# SPU-FABRIC-0 Phase 1B Scheduler Result

**Date:** 2026-10-15
**Disposition:** CLOSED — EXECUTION COMPLETE — INTEGRITY PASS — C2 THROUGHPUT GATE FAIL
**Scope:** Frozen software scheduling models only; no RTL, synthesis, FPGA, or board operation.

## Result

The one authorized detached attempt completed with exit code 0 in 264 seconds.
Exactly one terminal marker, `COMPLETE`, is present. The evaluator result has
`status: PASS`; this means the declared schedule comparison and evidence
integrity checks completed. Candidate C2 separately failed its frozen
requirement to retain at least 90% of Candidate A's completed throughput for
each client in each profile.

| C2 completed throughput / A | Isolated | Burst | Steady | 90% gate |
|---|---:|---:|---:|---|
| W32 Surd | 97.35% | 97.34% | 97.38% | Pass |
| W64 Surd | 98.64% | 98.63% | 98.65% | Pass |
| D4 | 100.00% | 100.00% | 100.00% | Pass |
| SOM | **15.02%** | **14.24%** | **21.53%** | **Fail** |

The Candidate C2 gate fails solely on SOM, in all three profiles. Candidate B
also retains the Surd and D4 throughputs closely, but its SOM retention is
lower: 10.17% isolated, 9.49% burst, and 14.39% steady.

| SOM model metric | Isolated A / B / C2 | Burst A / B / C2 | Steady A / B / C2 |
|---|---:|---:|---:|
| Maximum response latency (cycles) | 33 / 395 / 265 | 33 / 424 / 280 | 5 / 374 / 231 |
| Producer backpressure cycles | 11 / 146 / 98 | 11 / 181 / 113 | 0 / 142 / 71 |

All nine profile/candidate runs accounted for 288,794 offered, accepted, and
completed operations. The completed expected-result digest was identical in
all runs (`ef8b3111325ed675fe108e853edfcf1fef0418486ae46962a2a8c0b82545ed85`).
Frozen trace and timing input hashes match the execution contract. The full
machine-readable results are preserved in the build evidence directory.

## What the counters say about C2

In the declared C2 model, two product lanes may serve two distinct clients in
one cycle, but at most one operation from any single client may issue that
cycle. Each SOM job has 32 independent product micro-operations (four nodes,
four features, and two products per feature). Therefore, one SOM job cannot
use both lanes for those products in the same cycle. This is a model property,
not a physical RTL finding.

The resource counters are consistent with poor use of the second lane on
these traces: it is busy for only 53 cycles in isolated, 64 in burst, and 66
in steady, while lane 0 is busy for 3,443, 3,432, and 3,430 cycles
respectively. C2 records 32 SOM node-reducer busy cycles in each profile.
SOM product-arbitration stalls are 0 reported in isolated and 15 in each of
burst and steady. Thus, the large SOM latency penalty is not explained by the
recorded arbitration-stall count alone. The one-operation-per-client issue
limit and serial per-client progress are credible contributors; this model
does not isolate their causal shares from one another.

Candidate A's separate SOM scan path completes the fixture much faster under
the same offered trace. Candidate C2 retains 97–99% of A's Surd throughput,
so the model does not show a uniform penalty across clients. Candidate B's
still lower SOM throughput supports investigating how SOM product parallelism
interacts with sharing, but neither model establishes physical resource cost.

## Interpretation and limits

- The frozen C2 schedule is rejected by its predeclared SOM throughput gate.
- The experiment supports exact result-digest agreement and complete operation
  accounting for the declared A/B/C software models.
- Surd throughput retention is favorable within this model and these traces.
- The counters identify a plausible issue-parallelism bottleneck; they do not
  prove that the same bottleneck or ratios will occur in hardware.
- No DSP/LUT/FF/BRAM savings, clock rate, energy, physical timing, or integrated
  CPU/GPU feasibility was measured.

Do not amend C2 or reinterpret its gate after observing this result. A
dedicated SOM product path (C3), same-client multi-issue (C4), or a comparison
of both would be a new architecture study requiring its own frozen contract,
resource accounting, mechanics qualification, and authorization. This result
does not authorize that work or any RTL/FPGA evaluation.

## Evidence

- Execution contract: `contract_spu_fabric_0_phase1b_scheduler_2026-10-15.md`
- Command: `python3 software/experiments/spu_fabric_0_scheduler.py --output-dir build/spu_fabric/fabric_0_phase1b_scheduler_20261015/artifacts`
- Detached runner: `build/spu_fabric/fabric_0_phase1b_scheduler_20261015/runner/`
- Machine-readable result: `build/spu_fabric/fabric_0_phase1b_scheduler_20261015/artifacts/result.json`
- Result SHA-256: `33667c0839b057fe33a17857101838034614bbe59b19b50aa2fa3f2e1922c8bd`
- Runner result SHA-256: `1e4526762f63b1de6a9634d970c7115caea2cdacdea1c6e016a1fbaac92f730c`
- Repository revision recorded at launch: `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`
