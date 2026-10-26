# Offline Surd CPU kernel analysis

```bash
python3 software/tests/test_surd_cpu_trace_analysis.py
python3 software/experiments/surd_cpu_trace_analysis.py --help
python3 software/experiments/surd_cpu_trace_analysis.py --runtime-log build/spu_surd_register/main_cpu_integration_20261007/focused_01/cpu/runtime.log --reference-records build/spu_surd_register/main_cpu_integration_20261007/focused_01/cpu/reference_records.json --output build/spu_surd_register/software_preparation_20261007/analysis_01/kernel_analysis.json
```

The last command was executed on 2026-10-07 and extracted 128 retained groups.
Its output refuses overwrite. For a future completed run, substitute its
`runtime.log` and `reference_records.json` and select a fresh output filename.
The extractor executes no simulation, synthesis, or hardware commands.

Before interpreting a detached run, require exactly one of `COMPLETE`,
`FAILED`, or `TIMEOUT` in its evidence directory. The retained `focused_01`
run has `COMPLETE`, exit 0, and a 391-second duration in `result.json`.
Do not interpret an active build from intermediate logs. An extraction result
does not change the job's terminal outcome.

## Trace interface

The producer is
[`spu13_core_surd_tasks.vh`](../hardware/tests/spu13/spu13_core_surd_tasks.vh).
Each `INS` row contains decimal group, opcode, boundary tag, instruction cycles,
normalization cycles, alignment cycles, product/check cycles, rescue requests,
all normalizer starts, readiness stalls, and retirement status. `GROUP` supplies
group and elapsed cycles. Group -1 contains directed diagnostics and is
excluded from retained kernel accounting.

The report includes per-group and per-chain-length cycle counts, counts for all
eight Surd instructions, tuple transfer counts and cycles, phase work, rescue
requests, normalizer starts, failure counts, and successful tagged `SNORM`
reductions. Expected scheduled reductions are eight per chain joint: four
components at each forward and inverse boundary. A mismatch is reported rather
than hidden. Chain names, indices, and lengths come from the reference records;
input SHA-256 digests bind each report to its exact log and metadata bytes.

Alignment cycles count phase 1/2 occupancy, not GCD iterations or quotient
operations. Product/check cycles count phases 3/4; normalization cycles count
phases 5/6. These are measured simulator cycles. Normalizer starts include
scheduled and rescue work; rescue requests must not be added to those starts
as a second workload count. Readiness stalls count polling iterations and are
not an additional term in total cycles. Issuer/control cycles are elapsed group
cycles minus the sum of instruction cycles. Reset/boot precedes group timing.

Kernel transfers include inverse coefficient generation, six-slice loads and
readbacks, cached inverse reloads, and scheduled reductions; see the
[`schedule`](../software/experiments/surd_cpu_kernel_schedule.py). Retained
joint coefficients have zero radical components. Directed radical diagnostics
do not establish a radical-heavy kernel performance result.

## Verification and limits

Four fixture tests pass, covering known totals, failed reductions, missing PASS,
malformed/truncated/duplicate groups, inconsistent cycles, input hashes, and
output refusal. Every common measured counter in the 128 extracted groups
matches the retained `cpu/results.json` report. The extractor leaves the
existing test runner and arithmetic oracle unchanged.

`runtime_pass_marker` records only the producer's literal PASS line. Counters
cannot establish exact tuple readback agreement, destination preservation,
fallback execution, mapped topology, hardware timing, speedup, instruction
elimination, or energy. The report labels exact agreement and fallback
observability accordingly. Review the producer's oracle, assertions, source
provenance, and complete job evidence separately. Physical claims require a
specific entry in the [hardware evidence ledger](hardware_evidence.md).

Related preparation:

* [Oracle review](SURD_CPU_ORACLE_REVIEW_2026-10-07.md), including remaining RTL verification gaps.
* [Integer baseline capabilities](../spu_strategy/spec_surd_integer_baseline_capabilities_2026-10-07.md).
* [T1I offline milestone review](GPU_T1I_OFFLINE_PREPARATION_2026-10-07.md), preserving T1H H1 HOLD and T1G rollback.
* [Short progress article](blog/exact_surd_progress_2026-10-07.md).
