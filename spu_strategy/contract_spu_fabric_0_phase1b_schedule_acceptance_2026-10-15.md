# SPU-FABRIC-0 Phase 1B Schedule Acceptance Amendment

**Date:** 2026-10-15
**Status:** ACCEPTED FOR SOFTWARE SCHEDULER PREPARATION; EVALUATION HELD
**Parent schedule draft:** `contract_spu_fabric_0_phase1b_schedule_model_draft_2026-10-15.md`
**Parent schedule SHA-256:** `9409b5e2a7c60516647c36ba11e0d12c3a6658311d71a196745902326de3366a`
**Parents:** `contract_spu_fabric_0_2026-10-15.md`; `contract_spu_fabric_0_phase1b_timing_addendum_2026-10-15.md`

## 1. Accepted schedule choices

Accept the schedule draft's resource DAGs and edge conventions for use in
preparing the Phase 1B software experiment, subject to the clarifications in
this amendment. This acceptance does not authorize the frozen-trace scheduler
campaign, RTL changes, synthesis, placement/routing, FPGA programming, or board
operations.

Candidate C is C2: two shared product lanes; one dedicated W32 Surd final
reducer; one dedicated W64 Surd final reducer; separate W32 and W64
normalizer/control paths; and a dedicated SOM node-reduction/winner path.
Candidate B retains one shared product lane, one shared binary add lane, and
dedicated normalization and SOM winner paths. Candidate A retains the frozen
dedicated operators. These are modeled resource assignments only; physical
cost is unmeasured.

D4 uses the draft's sole same-edge replacement exception: output retirement
occurs before input capture on the same edge, giving a one-cycle service
latency and initiation interval one. Every other client cannot accept a
replacement on its prior operation's retirement edge.

## 2. Service schedule versus contention

Candidate service timing means the latency of one operation under its
candidate resource map when no other client competes for shared resources. It
is derived from the frozen micro-operation DAG and frozen intrinsic timing
table and is recorded before campaign evaluation.

The scheduler computes contention-dependent issue delays, queueing,
backpressure, response latency, and retirement from the immutable offered
traces. Do not precompute or freeze those response times. Cross-client
arbitration is deterministic and fixed by the schedule draft; it is part of
the scheduler mechanics, not an adjustable candidate parameter.

## 3. Evidence boundary

The selected Candidate A RTL timing checks are separately reported in
`build/spu_fabric/fabric_0_phase1b_rtl_timing_retry_20261015/artifacts/result.json`.
They confirm only the ten selected cases recorded there. Full-domain timing
bounds remain source-derived. Candidate B/C timings remain software schedule
models; no RTL or physical result is implied.

The Phase 1A manifest and three compressed traces are immutable inputs. Any
hash mismatch halts preparation or evaluation rather than regenerating them.
