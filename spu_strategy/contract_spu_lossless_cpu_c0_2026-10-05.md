# Engineering Contract: SPU lossless CPU storage experiment C0

Date: 2026-10-05  
Status: ACTIVE — authorized Python host experiment; gates pending.

## 1. Execute frozen commands

```bash
timeout --signal=KILL 60s python3 software/tests/test_spu_lossless_cpu_c0.py
timeout --signal=KILL 60s python3 software/experiments/spu_lossless_cpu_c0_run.py --out build/spu_lossless_reduction/c0_cpu_20261005/run_01 --preflight /tmp/spu_c0_preflight_20261005.json
timeout --signal=KILL 60s python3 software/tests/test_rational_robotics.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/experiments/spu_lossless_cpu_c0.py software/experiments/spu_lossless_cpu_c0_timing.py software/experiments/spu_lossless_cpu_c0_run.py software/tests/test_spu_lossless_cpu_c0.py spu_strategy/contract_spu_lossless_cpu_c0_2026-10-05.md
```

Record exact commands, return codes, integer runtime and terminal status in
fresh evidence directories under `build/spu_lossless_reduction/c0_cpu_20261005/`.
Use an external command recorder; the experimental runner creates no child
processes. Compile new sources in memory and inspect their whitespace without
writing bytecode. Preserve existing sources, dirty changes and prior evidence.
No production arithmetic, RTL, ISA, UART, hardware, synthesis-flow, scheduler
or dependency changes. No physical execution. Keep runtime modules <=150 lines.

Do not silently waive repository gates. The owner-supplied AGENTS instructions
require the full verification commands before completion. Preserve their status
separately from C0 correctness. Run long required jobs with the detached runner
and end the turn after LAUNCHED; do not poll solely for completion. Synthesis,
if required by that policy, is verification only, never device execution or a
C0 performance measurement. Do not edit gate policy under this contract.

## 2. Retained workload and reference

Use `software/lib/rational_robotics.py:sample_robot_vector()` and
`joint_60(axis_id=3)`, maintained by
`software/tests/test_rational_robotics.py`. Select this one vector and joint
because they expose reusable rational inputs and existing Fraction-string
serialization without GPU tooling. Invoke the unchanged `apply_joint`, then
unchanged `apply_inverse_joint` as one kernel execution.

Flatten a,b,c,d,f,g,h in order, storing each p numerator, p denominator,
q numerator, q denominator: 28 signed int64 integers. Preserve every scale;
reject nonpositive or noncanonical denominators, unsupported integer values,
counts and axes. Do not manufacture common factors. Use the maintained first
`six_step_kinematics_trace` frame, inverse closure and an independent direct
Fraction fixture as expected outputs. This kernel intentionally uses unbounded
Python integers and Fraction: no native finite-width behavior is claimed.

Record HEAD, dirty status and input/source hashes. Read the R1 closeout before
reuse. Preserve R0 run_02 tested hashes and run_03 reporting-only ancestry;
record the present R0 test hash separately. Do not rewrite prior reports or
claim a reporting revision reran tests. Input/source changes invalidate frozen
preflight; stop before timing.

## 3. Complete representations

Prefix every representation with `43 30 00 03 01` (C0/schema0/axis3/one block).
Use R1 tags 0=fixed-int64, 2=R0-packed, 3=uint64-factor-plus-R0-packed.
These retain their uint32 element count, width bytes and padding. There is one
ordered block, so no offsets/index table are required. Factors reconstruct all
original numerator and denominator integers before Fraction objects or kernel
calls; no arithmetic runs on reduced values. Reject unsupported factors.

Automatic selection constructs all three candidates, takes minimum complete
byte length, and breaks ties by numeric tag (0,2,3). It adds no selector tag:
the chosen stream's mode tag identifies the representation. Independently
calculate lengths from integer widths, framing, count, padding and factor.
Use fixed fallback even when packing expands.

Also report the existing logical input serialization from
`quadray_to_trace_value` and `q3_to_trace_value`: compact ASCII JSON retaining
vector/joint dictionaries and Fraction strings, tag4 and uint32 payload length,
plus the same prefix. This is a declared serialization of the maintained
representation, not an existing CPU binary/wire format. Compare complete bytes
against this JSON and int64 independently; report raw sizes separately. Never
compare Python object sizes against serialized bytes. Retained decoded storage
contains original 28 integers and Fraction/Q3 objects, not compressed working
memory. No claim about actual Python object footprint.

## 4. Falsifiable correctness and timing

Require exact input reconstruction, order, workload outputs and maintained
kernel error behavior for every representation. Reuse R0 exhaustive/seeded,
boundary, malformed-stream and factor tests without its subprocess CLI tests
or GPU geometry campaign. Include every C0 truncation, tag/count/width/padding
corruption, invalid denominator, deterministic tie and a validly framed changed
coefficient which must fail output equivalence. Refuse an existing output.
Any mismatch stops timing and records FAIL; no speed or compression threshold.

Freeze five trials, 100 repetitions and three warmups per measurement path.
Use `perf_counter_ns`; store integer totals/medians, operation counts and exact
integer numerator/denominator ratios without overhead subtraction. Preconstruct
encoded streams before decode/kernel timing. Consume checksums and compare
outputs outside each measured interval. Measure each representation, including
maintained JSON, for decode-once + one kernel, decode-once +100 kernels,
decode-anew +100 kernels, and encoding100 alone. Include automatic candidate
construction and selection in encoding. Original decoded-input baselines run
one and100 unchanged kernels. Python overhead is included; no native/silicon,
throughput, bandwidth, power or device equivalence inference.

## 5. Budget, evidence and decisions

One initial focused correctness command and experiment command, each with
`timeout --signal=KILL 60s`; up to two prospective software repair/check cycles
in fresh paths, never automatic retry. Retain failures and freeze revised hashes.
Never extend these limits. TIMEOUT or unavailable retained inputs is a terminal
informative result; do not substitute synthetic workload data.

Write deterministic correctness/provenance/sizes separately from timing in
`results.json`; include hardware_operations=0 and device_equivalence_tested=false.
Retain inputs, complete streams, frozen source copies, contract, preflight,
command logs and a self-contained review packet. Report storage and end-to-end
improvement for each reuse mode independently. Retain experimental status;
any integration needs a separately scoped authorization supported by benefit.
