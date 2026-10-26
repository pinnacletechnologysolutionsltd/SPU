# D4-MEM-1 Canonical Associative Memory Comparison

```bash
python3 -m unittest software.tests.test_d4_mem1 -v
python3 -m software.research.d4_symmetry.mem1 --output build/research/d4_mem1/eval_03/result.json
git diff --check -- software/research/d4_symmetry software/tests/test_d4_mem1.py spu_strategy/contract_d4_mem1_2026-10-14.md
```

Date: 2026-10-14. Status: ACTIVE — bounded software-only comparison.
No hardware, Soul-0 evaluator, or product-performance claim is authorized.
`eval_01/result.json` and `eval_02/result.json` are preliminary executions:
the first omitted augmented action-transform preparation counts, and the
second did not report payload and action correctness independently. They are
preserved as emitted and superseded by `eval_03/result.json`.

## Objective

Compare four exact memory strategies for the same finite D4 orbit workload:
raw exact-key memory, explicit symmetry augmentation, canonical orbit memory
with witnesses, and a competent group-aware query-time orbit scan. Use the
existing `W(D4)` and D4-SYM-0 interfaces. This evaluates retrieval mechanics,
not learning quality or a realistic sensor task.

## Frozen workload and semantics

- `D4` means the rank-four root system; use all 192 even signed permutations.
- Training representatives: generic `(1,2,4,7)` and stabilizer-bearing
  `(1,1,2,2)`. Associate each with a distinct invariant payload and use the
  representative itself as the equivariant action.
- Query every distinct orbit member for both representatives, repeat each
  representative query once, and query non-equivalent `(1,2,4,8)` as a miss.
- Use exact integer vectors and the D4-SYM-0 lexicographic key and
  deterministic witness conventions. A valid action must be fixed by the
  input stabilizer after canonicalization. The workload includes orbit sizes
  192 and 48 respectively; compute and assert these before evaluation.
- Raw memory stores only the two observed representatives and probes exact
  vector keys. Augmented memory materializes every distinct transformed input
  and transforms its action during preparation. Canonical memory stores one
  canonical key per association and reconstructs actions from the witness.
  Group-aware memory stores only representatives, scans all 192 transforms
  per query, and checks all matches so stabilizer ambiguity is explicit.
- Every strategy receives the same two training associations and the same
  symmetry definition. Do not add transformed observations to the raw or
  query-time group-aware training set.

## Frozen accounting

- Count exact vector transformations, key comparisons/probes, witness/group
  candidates, and action transformations separately. Report preparation cost
  separately from query cost and report both total and per-query operation
  counts. Define each counter in the result metadata.
- Report serialized association bytes as canonical UTF-8 JSON bytes with
  sorted keys and compact separators. This is a portable serialization
  measure, not Python heap size or hardware storage usage.
- Report query count, hits, misses, payload correctness, and exact action
  reconstruction. A valid result requires no false alias for the
  non-equivalent query and correct retrieval for every supported orbit member.
- Do not combine these measures into a composite score. Do not claim a general
  compression, latency, energy, or computational advantage from this finite
  deterministic workload.

## Required verification and stop conditions

1. Verify the generic and stabilizer orbit sizes are exactly 192 and 48.
2. Verify all strategies receive identical source associations and query
   records; raw exact-key misses on unseen orientations are expected behavior.
3. Verify augmented, canonical, and group-aware strategies return exact
   payloads and actions on every supported orbit query; verify all strategies
   miss the non-equivalent query.
4. Verify canonical and group-aware action results are independent of witness
   choice for the stabilizer-bearing representative. Reject an inconsistent
   action in a negative test.
5. Record deterministic operation counters, serialized bytes, source and
   query counts, and the scope limitation in the result artifact.
6. Refuse to overwrite the output file. Keep D4-SYM-0 and all Soul-0 evidence
   immutable. No RTL, FPGA, or hardware operation is in scope.

## Interpretation boundary

This is a controlled finite-workload comparison of exact memory strategies.
It does not establish held-out task generalization, equal-budget superiority,
learning, practical compression, or hardware efficiency. If canonical memory
uses fewer serialized bytes but more query operations, report both results
without selecting a winner. Further workload or budget changes require a new
contract.
