# AOR × FPRA P0 — independent reference-derivation preparation

2026-10-23. **Preparation complete; execution readiness BLOCKED.** No numerical
fixtures or executable reference have been generated. This packet does not
authorize implementation or launch. Revision 3 is frozen by identity, not by a
filesystem permission change. Do not edit the reviewed specification.

## Frozen inputs

- [Specification](PREPARATION.md): SHA-256
  `8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb`.
- [Independent PASS](REVISION3_SPEC_REVIEW.md): SHA-256
  `8c1bfacc61e9612ed9e0aa786b484f4ff9fb502ef31932d52338dbc333db077b`.
- Launcher `tools/run_detached_job.sh`: SHA-256
  `52dedd350c9356482d6c4d19cb496dd543b337f69e34bf5f9de9e39e8701d065`.
- Worker `tools/run_detached_job_worker.sh`: SHA-256
  `bf2f299a1c8a4b6feb693e3b4c2357d4785fd850fb66575e7df3becf7d2196c4`.

Predecessors and reviews remain evidence. A later identity difference stops
launch; it does not authorize repinning. QCG-0, X2, Vivado and closed SOM work
are unaffected.

## Proposed independent implementation

Use Python standard-library integers only, in the following new, isolated files
under `research/aor_fpra_p0/reference/`. These files do not exist yet:

| File | Responsibility |
|---|---|
| `derive.py` | Bounded entry point, ordered case enumeration, manifest and writer |
| `pell.py` | Signed coefficient recurrence and independent product/norm checks |
| `semantics.py` | Public version/snapshot/receipt transition oracle |
| `accounting.py` | Declarative primitive schedule replay, work and live-slot ledger |
| `controls.py` | Literal control stimuli and deliberate-fault checker |

An independent reference author must implement these without candidate imports,
shared arithmetic/cache helpers or copied candidate traces. There is no candidate
implementation in this packet. Source review must enumerate imports and pin all
five files before execution GO. Small single-purpose helpers may be split only
within this responsibility list; do not introduce a general dependency engine.

Coefficient oracle: start with the identity pair and apply the specification's
signed recurrence for each event. For each observation, compute the product from
the two independently maintained source pairs using the general coefficient
product and compare it with a separately recurrent product state. Check all three
norms directly, and equality by coefficient comparison as a cross-check against
exponent equality. Do not use the candidate-style power ladder to establish
coefficient truth. Isolated EXPAND references use signed recurrence as truth.

Accounting oracle: replay the frozen arm-specific ladder/STEP schedule against
that independent truth. It may model the prescribed ladder to count operations,
but its values cannot certify themselves: compare them to the recurrence oracle.
Keep semantic truth, modeled arm work and actual derivation/checker work in
separate ledgers. Do not present reference runtime as candidate performance.

## Coverage and outputs

Enumerate nominal cases in arm A,B,C,D order, then rho 1,8,64. Reset independently
for each case. Preserve the 64-event tape: twelve cases, 768 STEP applications
and 292 observation batches. Then enumerate controls 1–20 for each arm: eighty
reset microcases, at most 66 API/kernel requests each. No extra workload, cadence,
randomness, fault variants or numerical tuning.

For every request record the exact coefficients when observable, logical
exponents, public versions/snapshots, status/code/stage, complete receipt and
changed flag where applicable. Record cache keys, alias/hit/miss/invalidations,
ladder extent, installations and pre/post committed-state identities. Public
observations must match across arms; private cache behavior need not match
across representations. A/B and C/D schedule equivalence is a valid outcome.

Derive counts per request, phase, case and arm for every specification counter,
ENTER and BYTE32, plus denial events and diagnostic charges separately. Include
retained/live peaks, alias inventory, serialization bytes and discarded work.
Use the exact READ/COPY schedule, including failure-path releases. Each count
must trace to a specification operation and stable stage path, not a candidate
trace. Preserve compact per-request counts and a digest of the primitive stream;
save the first-denied/failed event and its immediately preceding event. Do not
save an unbounded primitive trace.

For controls 14–19 derive the exact first refusal, attempted/charged work and
unchanged committed state; for every other control derive exact output, receipt,
cache and count expectations. Controls 12–13 test powering only for C/D and
expanded maintenance for A/B. Controls 11/19 remain isolated helper cases.
Do not infer algorithm-specific first-refusal equality from public equivalence.

Deliberate faults are exactly those registered in controls 1–6 and 20. For each,
preserve the intended injection point, altered record and checker rejection
reason. A wrong coefficient, Boolean, receipt, stale cache or invalid proof must
not pass as a legitimate resource refusal. Controls 7–19 also require their
registered semantic/cache/refusal checks. Missing detection is FAIL, never repair
the expected answer to accommodate a fault.

Output files: `manifest.json`, `nominal.json`, `controls.json`, `accounting.json`,
`faults.json`, `summary.json`. Manifest binds every file SHA-256, all inputs,
implementation/executable identities, command/argv, git HEAD and dirty boundary.
Large integers use signed decimal strings, no floating point. Freeze JSON field
order, compact UTF-8 serialization and newline policy in the implementation
review before counting SERIAL/BYTE32; do not silently select an encoding during
derivation. Record modeled observation bytes separately from evidence JSON bytes.

## Proposed bounded allowance and enforcement

Request one invocation, 60 seconds externally enforced, 1 GiB address-space
hard/soft limit, zero retries. No subprocesses from the reference, network,
devices, installation, candidate execution or hardware access. All six outputs
combined <=4 MiB, each <=2 MiB; private serialization <=64 KiB. Retain the
specification's 512 scalar-slot/64 pair modeled-case bounds, case work cap
100,000 and invocation cap 4,000,000. Actual independent validation work is
charged separately but consumes the same allowance; never add a free oracle
budget. Count/release cases sequentially; invocation totals persist across resets.

The reference owns pre-allocation modeled bounds, pre-event work reservation,
pre-write byte checks and aggregate JSON enforcement. Streaming aggregation
avoids retaining all primitive events. Child RLIMIT_FSIZE is 4 MiB; this is a
per-file limit, not an aggregate quota. Allow <=4 MiB each stdout/stderr and
<=4 MiB provenance/terminal files: <=16 MiB evidence total, checked after terminal
completion. The reviewed worker owns the external deadline and notification.
Its termination grace is not accepted computation time. Preserve elapsed time,
RSS, limit receipts and cleanup timing separately.

This finite operation envelope makes a small derivation plausible, but does not
prove Python completion within 60 seconds or ledger capacity. No timing trial
is authorized. A cap, timeout or incomplete output yields HOLD/incomplete
derivation; no split, budget enlargement or retry. A reference inconsistency is
FAIL and must be preserved. COMPLETE/exit zero alone does not certify fixtures.

## Exact proposed launch procedure — NOT executable or authorized yet

After reference source review, freeze its SHA-256 manifest, executable paths and
versions, serialization schema and complete argv. Recheck every pinned file,
imports, git/dirty boundary, executable callability, user-manager availability,
limit enforcement and absence of the exclusive destination. If any check fails,
do not launch or consume a slot. No training or candidate qualification is a
preflight check.

Proposed command, to be reviewed and pinned after the missing files exist:

```bash
tools/run_detached_job.sh \
  --output build/aor_fpra_p0/reference_derivation_01 \
  --timeout 60 --notify-desktop -- \
  /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- \
  /usr/bin/python3 -I research/aor_fpra_p0/reference/derive.py \
  --spec research/aor_fpra_p0/PREPARATION.md \
  --spec-sha256 8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb \
  --output build/aor_fpra_p0/reference_derivation_01/fixtures
```

The entry point must support isolated-mode imports explicitly, assert inherited
limits before mathematical work, and create only its new `fixtures` child.
The launcher creates the parent exclusively. After LAUNCHED record unit/path and
end the turn. Later inspection requires exactly one COMPLETE/FAILED/TIMEOUT;
then obtain independent acceptance of the saved fixtures and ledgers without
rerunning derivation. Do not launch a candidate as part of acceptance.

## Remaining blockers

1. Reference implementation is absent; no source hashes or inspectable counting
   implementation exist. Separate reference-only implementation permission is
   needed; this preparation supplies no candidate implementation permission.
2. Before literal counts, freeze the concrete request encodings/fault payloads,
   tag/ID/key representation and observation serialization/field inventory
   required by Revision 3. These determine K, COPY, storage and BYTE32 counts.
   Resolve only these literal encodings, without changing registered stimuli or
   semantics; flag any choice that would require changing frozen Revision 3.
3. Independently review the source schedule, oracle separation, output bounds,
   enforcement and final command; pin executable identities and ensure the
   reference-plus-checker work fits the unchanged allowance by static analysis.

No launch-ready identity can honestly be supplied before these gates. Numerical
fixture generation and all candidate implementation/execution remain HOLD.
