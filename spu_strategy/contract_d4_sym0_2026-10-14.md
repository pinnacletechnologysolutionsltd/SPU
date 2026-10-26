# D4-SYM-0 Exact Symmetry and Canonical Memory Addressing

```bash
python3 -m unittest software.tests.test_d4_sym0 -v
python3 -m software.research.d4_symmetry.demo --output build/research/d4_sym0/demo_01/result.json
git diff --check -- software/research/d4_symmetry software/tests/test_d4_sym0.py spu_strategy/contract_d4_sym0_2026-10-14.md
```

Date: 2026-10-14. Status: ACTIVE — bounded software-only reference.
No hardware, FPGA, Soul-0 evaluator, or performance advantage claim is authorized.

## Objective and scope

Implement a small exact software interface for the rank-four root system
`D4` and its 192-element Weyl group `W(D4)`. Establish canonical orbit keys,
deterministic transformation witnesses, invariant associative addressing,
and orientation-sensitive action reconstruction. Keep this work independent
of Soul-0's arithmetic/adaptation state and of the pending Soul-0 experiment.

Existing D4 evidence is immutable and reusable: the exact bounded chamber
oracle in `software/tests/d4_canonical_exact.py`, its exhaustive P0 checks,
and the conventional even-signed-permutation descriptors in
`software/research/lattice_comparison/d4.py`. Do not change those files or
restate their prior result as a new D4-SYM-0 result.

New files:

- `software/research/d4_symmetry/__init__.py`
- `software/research/d4_symmetry/canonical.py`
- `software/research/d4_symmetry/memory.py`
- `software/research/d4_symmetry/demo.py`
- `software/tests/test_d4_sym0.py`
- `spu_strategy/contract_d4_sym0_2026-10-14.md`

## Frozen conventions

- `D4` means the rank-four root system; its Weyl group has order 192. It does
  not mean the eight-element dihedral group of a square.
- A group element is the existing descriptor `(permutation, even_sign_bits)`.
  The action is `y[i] = (-1)**bits[i] * x[permutation[i]]`.
- Composition `compose(left,right)` applies `right` first, then `left`.
- Enumerate all 192 descriptors and sort lexicographically by permutation
  tuple, then sign-bit tuple. This fixes witness ties.
- Accept four-component integer vectors, including vectors outside the
  bounded D4 lattice used by prior P0 research. Reject malformed vectors.
- Define `C(x)` as the lexicographically smallest signed integer vector in
  `{g*x | g in W(D4)}`. Return the first sorted descriptor `g_x` with
  `g_x*x=C(x)`. This lexicographic orbit key is intentionally distinct from
  the prior P0 closed-chamber key.
- For an observed orientation-sensitive action `a_x`, store canonical action
  `a_c = g_x*a_x`. On lookup at `y`, reconstruct `a_y = g_y^-1*a_c`.
- Before storing an action, require every `h` satisfying `h*C(x)=C(x)` to
  also satisfy `h*a_c=a_c`. Reject actions that fail this stabilizer check.
- An invariant payload may be associated with a canonical key. Repeated
  equivalent observations with a different payload are rejected; this is a
  negative control for tasks where the proposed symmetry is invalid.

## Required verification

1. Verify 192 unique group elements, identity, closure, and two-sided inverses.
   Check the composition/action law on the frozen sample vectors.
2. On `D4_B={x in Z^4 : -4<=x_i<=4, sum(x) even}`, containing 3,281 states,
   check that every group transform receives the same canonical key. For each
   state, verify chamber-independent witness reconstruction `g_x^-1*C(x)=x`.
3. Train one memory association on a generic orbit representative and query
   all distinct transforms without adding them. Verify invariant payload
   retrieval and equivariant action reconstruction for all 192 queries.
4. Demonstrate canonical addressing reduces 192 distinct raw keys in the
   generic orbit of `(1,2,4,7)` to one canonical key. Report this as a
   bounded orbit count, not a general compression or task-performance claim.
5. Reject a conflicting non-invariant payload for two symmetry-related inputs.
   Reject a canonical action that is not fixed by the input's stabilizer.
6. Keep all arithmetic integer and deterministic. Record group size, orbit
   size, canonical candidate evaluations, witness, and memory entry count.
   Do not claim elapsed-time or hardware efficiency from these checks.

## Boundaries and next experiment

This reference establishes exact transformations and address behavior only.
It does not establish learned transfer on held-out tasks, equal-budget memory
advantage, generalization, cost advantage, E8 suitability, or native SPU
implementation. Those questions belong to a separately frozen D4-MEM-1
comparison of raw memory, symmetry augmentation, and canonical memory, with
task-valid and task-invalid symmetries, full inference cost, and exact action
reconstruction.

The Soul-0 arithmetic study remains frozen and unlaunched until its separate
owner authorization is recorded. D4-SYM-0 must not modify Soul-0 files or
consume its run budget.
