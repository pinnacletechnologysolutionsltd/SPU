# Engineering Contract: Surd batch and shared-scale C1

Date: 2026-10-06 (Pacific/Auckland)
Status: ACTIVE — C0 resolved; C1 scope amended and timing campaign frozen.

## 1. Inspect the existing C0 job first

```bash
systemctl --user show spu-c0-cpu-20261006-gates-01 --property=ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,ExecMainStartTimestamp,ExecMainExitTimestamp
journalctl --user -u spu-c0-cpu-20261006-gates-01 --no-pager -n 40
ls -la build/spu_lossless_reduction/c0_cpu_20261005/gates_01
```

Interpret only a supported durable terminal result. Missing terminal evidence
means UNAVAILABLE, never FAILED. Preserve the existing unit, journal, logs and
all command failures; never duplicate the job or reopen C0's repair budget.
Continue independent source inspection, fixture compatibility and implementation
while C0 is unavailable. Resolve C0 before additional mandatory gates.

## 2. Preserve scope and reference semantics

Modify only `software/experiments/spu_surd_batch_c1.py`,
`software/experiments/spu_surd_batch_c1_run.py`,
`software/tests/test_spu_surd_batch_c1.py`, this contract and generated evidence
under `build/spu_lossless_reduction/c1_surd_batch_20261006/`.
Use standard library only. Preserve production arithmetic, R0/R1/C0, RTL, ISA,
UART, firmware and hardware. hardware_operations=0;
device_equivalence_tested=false. Do not run synthesis under C1.
Owner amendment: use a second runner module, both modules <=150 lines;
keep arithmetic/tracing in the adapter and measurement/reporting in the runner.
Timing and repair budgets remain unchanged.

Use unchanged C0 decoding and forward/inverse kernel. The maintained kernel
uses unbounded Fraction coefficient pairs, without rounding or finite-width
overflow. Its circulant inverse assumes determinant one and computes the
adjugate without dividing or rejecting singular input. Preserve that behavior.
Use an independent Fraction matrix calculation as the algebra reference.
Reject zero norm only for the separate general algebra division fixtures;
the retained kernel does not require Surd division.

Inventory explicit retained robotics seeds by path and fixture index. Include
compatible literal native-thirds fixtures, the maintained sample and P5 sequence,
the exact six-step root, and the demo's decoded integer seed. Deduplicate ordered
28-integer inputs including joint coefficients. Retain source hashes and exact
expected results. Exclude generated range sweeps as synthetic and VM finite-width
workloads as a different reference semantic. Record these exclusions explicitly.
Freeze inputs.json and its SHA256 before timing; do not invent distributions.

## 3. Implement and falsify candidates

Model (a,b,d) as (a+b*sqrt(3))/d, with d positive after validation.
Normalize signs, canonicalize by gcd(abs(a),abs(b),d), and represent zero as
(0,0,1). Add with lcm alignment; multiply with both ac+3be and ae+bc.
Retain the common denominator explicitly and reconstruct original inputs.
Compare eager and output-boundary normalization over one bounded forward/inverse
segment. Preserve all pair and batch order. AoS and SoA use scalar Python
operations; do not claim vectorization. Count preprocessing, scale metadata,
normalization and materialization in appropriate end-to-end paths.

Require original reconstruction, batch/scalar and AoS/SoA equality, and separate
maintained-kernel/algebra equivalence. Test unequal denominators, mixed input
signs, zero/cancellation, large nonzero-b growth and zero division independently.
Retain discarded-scale and narrow-intermediate overflow negative controls.
Stop timing a mismatching candidate; retain FAIL or SEMANTICS_DIFFERENT.

Observe signed two's-complement widths including zero and negative endpoints;
count operations, gcd/lcm/division and checked-width wide fallbacks. Observations
are not proofs. Derive conservative bounds over every intermediate before
proposing specialization. Do not infer faster Python execution from small ints.

## 4. Freeze timing and budget before execution

Use batch sizes 1,16,64 by deterministic cycling through frozen inputs. Record
distinct and repeated inputs per batch. Use perf_counter_ns, five trials,
100 repetitions and three equal warmups per path. Keep correctness and output
digests outside timed loops. Record integer totals without overhead subtraction.
Measure baseline kernel, decode-once execution, layout conversion execution,
and complete shared-scale normalization/materialization separately. Include an
end-to-end path for every excluded construction cost. Freeze exact experiment
commands and width bounds before any timing. Use the frozen plan for these paths:
baseline; aos_kernel; soa_kernel; decode_once_aos; layout_once_soa;
aos_e2e; soa_e2e; shared_eager_kernel; shared_boundary_kernel;
shared_eager_e2e; shared_boundary_e2e; checked8_e2e; checked16_e2e; checked32_e2e.
The plan contains all 42 exact argv vectors, one per size/path. Each is one
initial execution with the unchanged 60-second timeout. Encode input streams
before timings; end-to-end paths begin from the same pre-encoded C0 stream.
Encoding is a storage preparation cost, outside this arithmetic comparison.
Kernel paths use prepared arrays; end-to-end paths decode and construct them on
each repetition. Decode-once/layout-once paths construct once per trial and reuse
for100 executions. All paths include output normalization/materialization.
Checked paths include full trace/overflow-predicate overhead; they are software
models, never a native narrow-register performance claim.

```bash
timeout --signal=KILL 60s python3 software/experiments/spu_surd_batch_c1_run.py --out build/spu_lossless_reduction/c1_surd_batch_20261006/timings_01/64_shared_boundary_e2e --plan build/spu_lossless_reduction/c1_surd_batch_20261006/timing_plan_01/plan.json --batch-size 64 --path shared_boundary_e2e
tools/run_detached_job.sh --output build/spu_lossless_reduction/c1_surd_batch_20261006/campaign_01 --timeout 2700 --unit spu-c1-surd-20261006-timing-01 --notify-desktop -- python3 build/spu_lossless_reduction/c1_surd_batch_20261006/timing_plan_01/run_campaign.py
```

The first command is an example member of the frozen campaign, not a second
execution. Launch the campaign once. The external campaign orchestrator/command
recorder may create processes; the experimental runner may not. Sum of per-command
limits2520 seconds, outer limit2700 seconds including evidence overhead. On
TIMEOUT preserve evidence and do not extend limits or automatically retry.

Enforce `timeout --signal=KILL 60s` separately for focused tests and each
experiment command. One initial execution per command, at most two prospective
C1 repairs in fresh paths; preserve failed logs and revised hashes. Refuse
existing evidence output directories. Runner creates no child processes.

## 5. Required checks and closeout

After C0 resolution, record exact commands, limits, hashes, logs and terminal
markers for these focused checks:

```bash
timeout --signal=KILL 60s python3 software/tests/test_spu_surd_batch_c1.py
timeout --signal=KILL 60s python3 software/tests/test_rational_robotics.py
git diff --check -- software/experiments/spu_surd_batch_c1.py software/tests/test_spu_surd_batch_c1.py spu_strategy/contract_spu_surd_batch_c1_2026-10-06.md
```

Compile sources in memory. Record repository-required gates separately and
resolve their applicability before completion; this contract does not waive
AGENTS.md. Use detached execution for work exceeding 60 seconds and end the turn
after LAUNCHED. Do not poll solely for completion or infer a result from logs.
Preserve C0's durable overall FAILED marker and its repo/triage TIMEOUT outcomes.
Do not reuse C0's passing gates as verification of new C1 sources. The exhausted
C0 gate attempts and unchanged owner budgets do not authorize another expensive
attempt against the unresolved repository/triage gate. Report this repository
verification gap separately from C1 software correctness; no full-gate PASS.

Deliver a self-contained packet of sources, references, frozen inputs/contract,
hashes, correctness, sizes, integer timings, exclusions and failure history.
Report Python object memory NOT_MEASURED unless measured consistently.
PASS denotes correctness only. Recommend integration only with measured
end-to-end benefit after metadata, normalization, conversion and fallback costs.
No physical, power or native-throughput conclusions; follow-on ISA work is separate.
