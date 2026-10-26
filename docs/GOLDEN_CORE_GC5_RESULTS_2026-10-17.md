# Golden Core GC-5 — oriented edge-turn results

**Status:** PASS within the frozen finite software experiment

**Date:** 2026-10-17

**Hardware / ISA:** unchanged; no hardware qualification

## Result

On the frozen exact icosahedron, the vertex stars define 12 oriented 5-cycles.
The orientation is selected by the positive exact sign of
`det(v, n[k], n[k+1])`. These cycles induce left- and right-turn permutations
on the 60 directed edges, giving a state space of dimension 60 over
`Q(√5)`.

The exact operator identities hold for all 120 GC-4 symmetries:

- each of the 60 determinant-`+1` maps commutes with both turn operators;
- each of the 60 determinant-`−1` maps exchanges the left and right operators.

For `F_(a,b) = a T_L + b T_R`, equal weights therefore have all 120 maps as
internal symmetries. For the tested unequal exact weights, 60 of the 120 GC-4
spatial maps are internal symmetries; this does not classify every possible
linear symmetry of the operator. All 120 maps remain covariant when
orientation-reversing transport exchanges the weights. The profiles were
`(a,b)=(1,1)` and `(3+√5, 1−√5)` in `Q(√5)`. Since `1−√5 < 0`, the unequal
profile is a signed linear operator, not a transition-probability rule.

This locates the tested asymmetry in the weighted evolution law. The substrate
itself remains the same achiral, unlabelled icosahedron from GC-4. The result
does not demonstrate emergent trajectories, useful computation, physical
chirality, or hardware advantage.

## Evidence

`software/golden_core/oriented_edge_turns.py` constructs the local link cycles
and directed-edge permutations using exact `Q(√5)` arithmetic. The independent
test oracle finds each oriented link by exhaustive enumeration of candidate
cyclic orders and exact determinant signs. Verification checks the operator
identities for every symmetry as permutation identities, weighted covariance
on exact field-valued states, and the weighted action on every basis state for
a proper-map representative and an orientation-reversing representative.

The negative control reverses the link cycle at vertex 0 only. It causes 110 of
120 expected covariance checks to fail, so the orientation convention is
detectable by the test suite.

The complete 60 directed-edge list, 12 link cycles, and left/right
permutations are frozen in
`fixtures/golden_core_gc5_oriented_edge_turns.json`, SHA-256
`ccce31465559743ec255ce18d4ce2ef3334331bb04e5798301e2744440d52d13`.

## Reproduction

```sh
python3 software/tests/test_golden_core_gc5.py
python3 software/tests/test_golden_core_gc4.py
```

The construction is limited to this finite oriented edge model. It is not a
vertex-state cellular automaton, a temporal simulation, or a specification for
SPU instructions.
