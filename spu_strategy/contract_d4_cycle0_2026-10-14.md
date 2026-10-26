# D4-CYCLE-0 Exact Transformation-Cycle Consistency

```bash
python3 -m unittest software.tests.test_d4_cycle0 -v
python3 -m software.research.d4_symmetry.cycle_demo --output build/research/d4_cycle0/demo_01/result.json
git diff --check -- software/research/d4_symmetry software/tests/test_d4_cycle0.py spu_strategy/contract_d4_cycle0_2026-10-14.md
```

Date: 2026-10-14. Status: ACTIVE — bounded software-only mathematical
reference. No hardware, Soul-1 integration, performance, or localization
claim is authorized.

## Objective and scope

Implement immutable runtime-validated types for exact rank-four `D4` state,
`W(D4)` group elements, frame identifiers, witnesses, orbit keys, and directed
relation edges. Define edge transforms as mappings from source-frame
coordinates to target-frame coordinates. Compose edges only when adjacent
frame identifiers match. Evaluate exact ordered cycle products in the
existing descriptor convention where `compose(left, right)` applies right
first and then left.

Keep D4-SYM-0, D4-MEM-1, Soul-0, and existing mathematical evidence
unchanged. Do not implement automatic graph-cycle enumeration, anomaly
localization, learned relationships, non-D4 groups, or hardware support.

## Frozen fixtures

1. **Consistent graph:** Four typed frames with deterministic hidden
   `W(D4)` frame assignments. Derive both directed edges for every unordered
   pair using `q_target * inverse(q_source)`. Check the frozen seven simple
   cycles (four triangles and three distinct quadrilaterals); each product
   must equal the identity.
2. **Corrupted graph:** Replace one undirected pair's forward label with a
   distinct valid group element and set its reverse edge to the exact inverse.
   Check that cycles using that pair disagree with expected identity and the
   triangle that excludes it remains identity. Report the union of edges in
   disagreeing cycles as candidates only; do not assert unique localization.
3. **Prescribed nontrivial holonomy:** Build a three-edge cycle whose first
   two transforms are identity and whose final transform is a fixed nonidentity
   element. Verify the exact reported product equals that element and passes
   when that product is the declared expectation. Verify it fails an identity
   expectation. A nonidentity product is not inherently an error.

The fixture constants, frame assignments, cycle order, corrupted edge, and
prescribed holonomy must be literal and deterministic in the test source.

## Required verification

- Verify all 192 unique group elements, inverses, and closure for typed
  `GroupElementD4` values.
- Verify invalid descriptors, malformed state dimensions, empty frame IDs,
  frame-discontinuous paths, and non-closed paths are rejected.
- Verify all consistent fixture cycles have identity products; corruption
  detection matches the declared affected/unaffected loops; the nontrivial
  cycle reports exactly its prescribed product.
- Verify composition ordering with an independently calculated action on a
  frozen vector, not only descriptor equality.
- Run the focused test and deterministic demo. Demo refuses overwrite and
  reports cycle products, expected products, status, candidate-edge set, and
  scope disclaimer. No elapsed-time benchmark is in scope.

## Interpretation boundary

This establishes exact finite-group composition and checks against explicitly
declared cycle expectations. It does not prove that arbitrary real-world
cycles should be identity, identify a unique faulty edge, establish source
trust, or show machine reasoning. Nonidentity holonomy is accepted when it is
the declared expectation. D4-MEM-1 remains the separate primary quantitative
symmetry study; no D4-MEM-1 result is modified or consumed here.
