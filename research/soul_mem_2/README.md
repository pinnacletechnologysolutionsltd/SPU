# SOUL-MEM-2

Authorized deterministic comparison; [contract and clarifications](CONTRACT.md).
No prior Soul implementation code is reused. Python 3.10+ standard library only.

## Registered design

Separate `calibrate.py` uses eight unique synthetic keys and never imports the
registered scenarios. The maximum complete policy-state size after 2, 4 and 8
calibration records defines small 239, medium 431 and large 815 byte budgets;
`evidence/calibration.json` records all samples. The registered scenarios are
in `scenarios.py`, scoring and controls in `evaluate.py`, support semantics in
`support.py`, and policy code in `memory.py`. Their pre-run hashes and budget
file are `evidence/registration.sha256`. The same scenario observations, in
order, and same queries go to all policies for each budget. Expected answers
remain evaluator-only.

Canonical state is UTF-8 JSON, sorted keys, compact separators, ASCII escapes;
its exact byte count includes every field of the policy's decision state. Common
code and fixed budget configuration are excluded. The memory state is the only
persistent agent data; stream and outcome logs belong to the evaluator and are
never read by the policies. If empty state exceeds the budget, report
`INFEASIBLE_BUDGET`. Each observation is an atomic transaction: after applying
revocation and/or insertion, enforce the budget by oldest-record eviction,
rebuild the index, and verify the complete resulting state. The rejected or
discarded records, including their content, are evaluator logs, not a retrieval
channel. Revocation deletes the target before optional retention of a tombstone,
so an evicted tombstone cannot resurrect a retained target. IDs in the fixture
are unique; out-of-order duplicate IDs are outside scope.

- M0 stores up to three latest candidates per key, then evicts globally oldest
  candidates if required. It retains alternatives, source IDs and epochs.
- M1 keeps an append-oriented archive including revocation tombstones and evicts
  oldest records on overflow. Current beliefs are reconstructed on query.
- M2 keeps an archive, a per-key index and a summary of latest fact IDs. All are
  budgeted. Every update rebuilds the index and summary; oldest archive records
  are evicted until the full representation fits. Every query first validates
  the complete index and then retrieves the indexed key. The query uses indexed
  candidates, including for current and historical questions; the stored summary
  is included in cost but is not used for a shortcut.

All policies apply the same rule: select the retained matching fact with the
highest epoch and then strength; conflicting equally ranked values are unknown.
Historical queries restrict the epoch. Losing a record can lead to a wrong or
unknown answer; the evaluator reports both. The support checker is separately
implemented and receives only available records and cited IDs. It checks exact
direct propositions or two explicit transitive premises with a declared rule;
missing premises or rule are UNKNOWN and mismatching propositions UNSUPPORTED.
This does not validate source truth, completeness, or absence of a better
unretained fact. Registered answers use the direct rule; the transitive rule is
exercised by a control, not a learned inference.

Recorded occupancy is exact canonical size after every update. The transient
field is the serialized size of the candidate working state before eviction,
not actual peak Python memory or an allocation measurement; queries similarly
report an estimate. Each decision starts from the serialized policy state, and
intermediate query data are discarded. The `ops` counters count specified record
visits and index operations, including M2's validation scan, and index rebuilding
visits on ingestion. They do not count all Python operations or give timings.
Logical bytes include the serialized records visited plus index information;
index validation bytes and visits are explicitly included. Archive visits in
`visits` are retrieval visits; M2's separate `validation_visits` must also be
included when comparing total history inspected. M0 visits are candidate reads,
not archive reads. Per-update snapshots expose retained records, discarded
records and index contents. `not_recoverable_ids` compares stream IDs with the
final state; dropped revocation tombstones and invalidated facts are included,
so consult each event's reason before interpreting the list.

## Reproduction

Run from repository root. Each command is bounded to 30 seconds and 1 GiB virtual
address space. Supply fresh scratch paths: outputs are overwritten.

```bash
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_2/calibrate.py /tmp/soul-mem2-cal-repro.json'
diff -u research/soul_mem_2/evidence/calibration.json /tmp/soul-mem2-cal-repro.json
sha256sum -c research/soul_mem_2/evidence/registration.sha256
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_2/test_experiment.py'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_2/evaluate.py /tmp/soul-mem2-repro1'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_2/evaluate.py /tmp/soul-mem2-repro2'
diff -r /tmp/soul-mem2-repro1 /tmp/soul-mem2-repro2
```
