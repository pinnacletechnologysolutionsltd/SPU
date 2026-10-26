# SPU-FABRIC-0 Phase 1B Scheduler Execution Contract

**Date:** 2026-10-15
**Contract ID:** `contract_spu_fabric_0_phase1b_scheduler_2026-10-15.md`
**Status:** DRAFT — READY FOR OWNER REVIEW; SCHEDULER EXECUTION NOT AUTHORIZED
**Parents:** Phase 0 contract, Phase 1A contract, accepted timing and schedule amendments

## 1. Objective and boundary

Compare the frozen Candidate A dedicated, Candidate B shared, and Candidate C
C2 hybrid schedules on each unchanged Phase 1A trace. This is a deterministic
software schedule model. It does not execute arithmetic RTL, the detached-job
worker, synthesis, place-and-route, FPGA programming, or board I/O.

The model tracks readiness and dependencies in each accepted operation's
micro-operation DAG. At completion it binds the operation to its immutable
Phase 1A oracle digest. It does not recompute candidate arithmetic values.
Oracle correctness is inherited from the frozen Phase 1A fixture checks; this
campaign measures the declared schedule and contention model only.

Candidate C is C2: two shared product lanes, separate W32/W64 Surd final
reducers, separate W32/W64 normalization/control paths, and the dedicated SOM
reduction path. The D4 one-cycle, initiation-interval-one wrapper is the only
same-edge retire/accept exception. These accepted choices are recorded in
`contract_spu_fabric_0_phase1b_schedule_acceptance_2026-10-15.md` and derive
from the full DAGs in
`contract_spu_fabric_0_phase1b_schedule_model_draft_2026-10-15.md`.

## 2. Frozen input identities

The evaluator must refuse any identity or schema mismatch. It consumes only:

| Input | SHA-256 |
|---|---|
| `fixtures/spu_fabric_0/manifest.json` | `24e7e35204baa8ee1e44a1cb09f788073a2bf721045190acb2a120ad1081ca13` |
| `fixtures/spu_fabric_0/traces/isolated.jsonl.gz` | `18585af72c7f65b4767e0526890424e56218af9eb20a6dbf90d943bf30c8a440` |
| `fixtures/spu_fabric_0/traces/burst_synthetic.jsonl.gz` | `4db6e7458794b4a36f07d2cfd29a135f4301fb1a9e46ec73f77dc7f5b1060067` |
| `fixtures/spu_fabric_0/traces/steady_synthetic.jsonl.gz` | `64359fdf2079299bbc1bfe95fe1b439f601084be288b62c9ace234dd5c4f3844` |
| `fixtures/spu_fabric_0/phase1b_timing_table.json` | `cccf933d1302da0cc658b03bb1cfa9ee33bd28047c882722d02d28237b392fab` |
| `fixtures/spu_fabric_0/phase1b_candidate_service_table.json` | `411ae0f8067a404667f570d0fc92481ef503cc1bb7cd8bdc15df9ddeefd9004d` |
| `software/experiments/spu_fabric_0_timing_reference.py` | `80b753da559a19b4a3fc3dada6829806846b74449513040bc52adfdc516a603d` |

The intrinsic timing table contains the 654 source-derived Surd latencies,
eight source-derived A SOM latencies, and the D4 wrapper convention. Its
full-domain W32/W64 bounds are 343/663 cycles; fixture maxima are 237/467.
The isolated candidate service table records accepted-to-completion cycles
with no competing client: A uses the qualified intrinsic values, B/C use the
frozen micro-operation schedules, and D4 uses one cycle. During evaluation,
the candidate table is a lower-bound check; the scheduler computes contention
and response latency. It must not replace contention with the isolated
service values.

The schedule inputs are pinned by the accepted amendment and source hashes:

| File | SHA-256 |
|---|---|
| `spu_strategy/contract_spu_fabric_0_2026-10-15.md` | `491670afb91600878e15955c5ea8ae9d508637e8f236e234bf4574fbd9169b80` |
| `spu_strategy/contract_spu_fabric_0_phase1a_2026-10-15.md` | `3ac47fd49990bb9b09cce0baca7511abc978d1eb1cdf96ff056455c788bad81d` |
| `spu_strategy/contract_spu_fabric_0_phase1b_schedule_model_draft_2026-10-15.md` | `9409b5e2a7c60516647c36ba11e0d12c3a6658311d71a196745902326de3366a` |
| `spu_strategy/contract_spu_fabric_0_phase1b_schedule_acceptance_2026-10-15.md` | `66e7430f55fa17fe3f2f9b8c6413c72c273e14fefb957218714731862ac2e763` |
| `spu_strategy/contract_spu_fabric_0_phase1b_cycle_qualification_2026-10-15.md` | `e08a7220775e80fd4b22beab2955bf2de0d32990da20f7efda013e45a9f3b589` |
| `spu_strategy/contract_spu_fabric_0_phase1b_timing_addendum_2026-10-15.md` | `b3ab7bad6ad9c048f0d1d8bcfe9c5ac932e6822061513b844de8380f2a5fc51b` |
| `spu_strategy/contract_spu_fabric_0_phase1b_timing_qualification_2026-10-15.md` | `7900885ab3be8e338cfb8a8e08223967e21002c3beb81b223f55b3ae7e463e2d` |
| `spu_strategy/contract_spu_fabric_0_phase1b_rtl_timing_retry_2026-10-15.md` | `5f834a2a3cef98442cb61394db706e980ee6822e06f3eb70ecc351e92667de60` |
| Selected RTL timing result | `build/spu_fabric/fabric_0_phase1b_rtl_timing_retry_20261015/artifacts/result.json`, SHA-256 `5a31c266ccdaa47a25bd5346e3a19911152c2140a37f829de868c8362402bf54` |

## 3. Evaluator and tool identities

Pin all files that determine validation, scheduling, results, or execution:

| File | SHA-256 |
|---|---|
| `software/experiments/spu_fabric_0_scheduler.py` | `8bdde50321b11300a5d6d5aa827628ab34885ecb11fe97962bebdda784bada11` |
| `software/experiments/spu_fabric_0_scheduler_engine.py` | `a5762cbcddd8c8f9232a477fca99350a2c4e36e75bbc80eda479d02dc74eec3a` |
| `software/experiments/spu_fabric_0_scheduler_ops.py` | `cf81e4652408a961f7bdb1ca15fd363c0f9fd787ba58cd34512245853274e6ef` |
| `software/experiments/spu_fabric_0_scheduler_accept.py` | `d9c64b39d1466f4b59618c689c7cbd3c0024bce02c900c531d34eab520ac72b2` |
| `software/experiments/spu_fabric_0_scheduler_resources.py` | `59dd8ba4ff051c70fb2ea3b24e9699284173b2a1d1cd1518790031b99bf58fba` |
| `software/experiments/spu_fabric_0_scheduler_report.py` | `f94f9fa9b0f930abf24c34df02d1db9ab3a2e5f41ac41f07e80e901a92edb7b3` |
| `software/experiments/spu_fabric_0_scheduler_io.py` | `c384541fb8d3c2dd7defcc37a65bf2df7302e7656c2a6733e927b44594a2404a` |
| `software/experiments/spu_fabric_0_scheduler_preflight.py` | `d8822c045a2c7f10c55438e28e0e179d63a67b6e0ed19ea08ee5261641ce70fc` |
| `software/experiments/spu_fabric_0_prepare_timing_table.py` | `b42a3f6b1067a52d739f1b2a5a8d0cc1130870ec54214ef9278eeefba5d7dcd2` |
| `software/experiments/spu_fabric_0_prepare_service_table.py` | `14210c45ba7aa8d4d0d99220c064dae47aac78d15160308eab526b3a0d1e3564` |
| `software/tests/test_spu_fabric_0_scheduler_mechanics.py` | `13cde070165dfaba390c8cb0fcac9516e2e15b1c02d60077efb5f9672827ac6a` |
| `tools/run_detached_job.sh` | `52dedd350c9356482d6c4d19cb496dd543b337f69e34bf5f9de9e39e8701d065` |
| `tools/run_detached_job_worker.sh` | `bf2f299a1c8a4b6feb693e3b4c2357d4785fd850fb66575e7df3becf7d2196c4` |

Python runtime: `Python 3.14.8`. Any changed pinned identity is a pre-execution
HALT; do not regenerate traces or timing tables automatically.

## 4. Scheduler semantics and measurements

Use the cycle ordering in the accepted schedule: retire first; dequeue at most
one eligible, already-enqueued request per ready client; then enqueue at most
one newly offered request per client. An offer that cannot enter the four-entry
ingress queue remains producer-held at its original offered cycle. Each
candidate has one active execution context per client and no additional
candidate request queue. Source order and predecessor dependencies are
preserved; a dependent request cannot start before all predecessor operations
complete.

Candidate B has one product lane and one binary add lane with independent
round-robin arbitration. Candidate C has two product lanes and may select two
distinct ready clients per cycle; it cannot issue two operations from one
client in one cycle. Its W32/W64 reducers and normalizers are independent.
D4 is outside shared arbitration. The arbitration pointers start at
`surd_w32`; fixed within-client DAG priority is the order in the accepted
schedule. A newly produced value is usable from the next edge. Candidate B/C
normalization begins after raw-result readiness and uses the frozen intrinsic
normalizer tail exactly once.

Drain all offered, accepted, and queued operations after the final release.
Each profile has a hard watchdog at 1,000,000 cycles after its last offered
cycle. Missing completion by that bound is a failed evaluation. No operation
may be dropped, reordered within a client, or silently rescheduled to a new
offered cycle.

For each profile and client, report:

- Offered, accepted, and completed operation counts.
- Offered throughput = offered count / inclusive first-to-last offered-cycle span.
- Completed throughput = completed count / inclusive first-offer-to-last-completion span.
- Queue wait = accepted edge minus original offered cycle.
- Response latency = completion edge minus original offered cycle.
- Producer backpressure cycles, maximum and cumulative ingress occupancy.
- Product, add, reducer, normalizer, SOM scan/compare, and D4 busy cycles and
  modeled utilization fractions.
- Arbitration stalls, accepted/completed operation-ID set checks, and the
  frozen expected-result digest. The evaluator publishes the aggregate digest
  rather than a 288,794-entry completion log.

Candidate C must achieve at least 90% of Candidate A's completed throughput
for each of the four clients in each of the three profiles. Report this as a
separate modeled throughput gate. A failed throughput gate is a valid negative
architecture result: the evaluation may complete successfully while the
Candidate C architecture gate reports `FAIL`. No software result establishes
DSP/LUT/FF/BRAM savings, Fmax, physical timing, or routability. Phase 1B must
not claim those quantities.

## 5. Mechanics qualification already performed

The exact focused command is:

```bash
python3 software/tests/test_spu_fabric_0_scheduler_mechanics.py
```

It passed seven hand-derived artificial cases covering D4 replacement at the
one-cycle interval, simultaneous arrivals and product contention, two-lane
issue with independent W32/W64 reducers, ingress saturation and drain,
Candidate A normalization delay, isolated B/C DAG service cycles,
candidate-specific normalization tails, and D4 completion beside slower
arithmetic. These fixtures do not load or schedule the frozen campaign.

The non-scheduling identity command is:

```bash
python3 software/experiments/spu_fabric_0_scheduler.py --preflight
```

It passed for all three frozen traces: 288,794 records and unique operation
IDs per profile, with manifest, trace, expected-value, timing-table, and
candidate-service-table identities matching. It does not execute Candidate A,
B, or C schedules.

## 6. Proposed bounded execution allocation

This is a proposed budget and requires explicit owner authorization before
launch:

- Maximum attempts: 1.
- Per-attempt timeout: 600 seconds.
- Cumulative campaign budget: 600 seconds.
- Automatic retries or timeout extensions: none.
- Execution method: detached runner with notification attempt.
- Scheduler output: `build/spu_fabric/fabric_0_phase1b_scheduler_20261015/artifacts/`.
- Runner evidence: `build/spu_fabric/fabric_0_phase1b_scheduler_20261015/runner/`.
- Failure artifacts, if the evaluator starts: sibling `artifacts.failed/`.
- Temporary staging, if interrupted: sibling `artifacts.staging/`; it is not a
  successful result.

Before launch, rerun the preflight command, recheck every pinned SHA-256, and
verify that `runner/`, `artifacts/`, `artifacts.failed/`, and
`artifacts.staging/` are absent. The exact detached command is:

```bash
tools/run_detached_job.sh \
  --output build/spu_fabric/fabric_0_phase1b_scheduler_20261015/runner \
  --timeout 600 \
  --notify-desktop \
  -- python3 software/experiments/spu_fabric_0_scheduler.py \
    --output-dir build/spu_fabric/fabric_0_phase1b_scheduler_20261015/artifacts
```

Any launched attempt consumes the one attempt and all 600 seconds of campaign
authorization, whether it completes, fails, times out, or becomes unavailable.
Interpret only exactly one detached-runner terminal marker. Do not relaunch,
extend the timeout, change any input, or substitute a different command
without renewed owner authorization.

## 7. Stop conditions and evidence meaning

Halt on any pinned hash mismatch, malformed or incomplete input, trace-order
or dependency violation, timing-table mismatch, service below its frozen
isolated bound, candidate digest disagreement, missing completion, deadlock,
watchdog expiry, output publication failure, or duplicate terminal marker.
The evaluator writes through a private staging directory, publishes the
completed result atomically, and preserves a failed result under
`artifacts.failed/`; it refuses any pre-existing destination.

`COMPLETE` with exit 0 means the schedule comparison ran and its evidence
passed evaluator integrity checks. The `candidate_c_throughput_gate` is a
separate architecture result and may be `FAIL`. A timeout is an infrastructure
outcome. RTL timing confirmation remains limited to the ten selected cases;
the full-domain bounds remain source-derived, and all candidate B/C timing and
resource results remain software models.

**Authorization state:** none for the 600-second scheduler attempt. The prior
Phase 1B authorization does not override this execution budget gate.
