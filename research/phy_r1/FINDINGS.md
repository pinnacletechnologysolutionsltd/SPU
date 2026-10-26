# PHY-R1 — Relational (metric-state) tensegrity

2026-10-20. Class A host-only experiment (AGENTS.md §4.3,
[execution policy](../../spu_strategy/RESEARCH_EXECUTION_POLICY.md)), selected by
the owner and following [DESIGN_PAUSED.md](DESIGN_PAUSED.md).
**Status: COMPLETE** within its static, exact, canonical-fixture scope (owner
review 2026-10-20). **Result: CONFIRMED within the canonical fixture.** A metric
state admits a continuous family of balanced, non-congruent configurations. The
integer-coordinate representation reaches only congruent copies. This shows
geometric admissibility only; physical reachability through cables is not
established (that is PHY-R2's question). 5 field and 7 PHY-R1 test groups
passed, exit 0, 4.1 s total. No RTL, CPU/GPU, simulator or evidence change was made.

```bash
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/phy_r1/test_field.py && python3 -I research/phy_r1/test_phy_r1.py'
```

Limits: 60 s wall time, 1 GiB address space, no network or installation, no outputs
beyond stdout. Arithmetic is exact (`Fraction`, Q(√d)), with no floating point.

## Files

| File | Role |
|---|---|
| `field.py` | Q(√d) arithmetic, exact square-root test, LDLᵀ rank/PSD, nullspace, determinant |
| `fixture.py` | Bridge to the existing oracle (`make_tensegrity_six_strut`, `verify_balance`); self-stress; super-stability |
| `model.py` | Metric state machine: immutable handles, refusals, dependency-checked certificate reuse (SSM-6 semantics), Cholesky materialisation per field |
| `reference.py` | Independent coordinate-free checks from pairwise quadrances and the documented 2:−3 stress |
| `test_field.py`, `test_phy_r1.py` | Tests |

## Field-helper validation (done first)

The pre-run review of `field.py` found three defects in code that had never been
executed. All were fixed before any experiment used it:

1. **Silent cross-field mixing.** `1(d=2) + √3` returned 1+√2. Now rationals convert explicitly and two different surd fields raise an error.
2. **Non-canonical d = 1 elements.** These are now normalised, and square d values are rejected.
3. **Float inverse.** `nullspace_rank` computed `1/int`. It now uses `Fraction`.

Tests cover square-root representability in Q, Q(√3) and Q(√5), including negative
inputs and non-squares. They cover rank and PSD on positive, singular, indefinite,
zero-diagonal and Q(√3) examples. They cover nullspace correctness, integer input
and the determinant against cofactor expansion.

## Results

**Reference.** The fixture has 30 members. The unique self-stress (nullspace
dimension 1) is cables 1 and struts −3/2, i.e. 2:−3. The stress matrix Ω is PSD
with nullity 4 = d+1, and the conic condition holds, so the reference is
**super-stable**. Both the independent check and the existing oracle report BALANCED.

**Metric perturbations.** State = X₀ plus M = AᵀA with unit diagonal; the struts are
axis-aligned, so their quadrance of 16 is preserved.

| Metric (off-diagonals) | Admitted | Independent check | Non-congruent | Materialisable in Q / Q(√3) / Q(√5) | Oracle |
|---|---|---|---|---|---|
| m₁₂ = 3/5 | yes | balanced | yes | yes / yes / yes | BALANCED (Q and Q(√5)) |
| m₁₂ = 1/2 | yes | balanced | yes | no / **yes** / no | not checkable (needs √3) |
| m₁₂ = 2/3 | yes | balanced | yes | no / no / **yes** | BALANCED (Q(φ)) |
| (1/3, 1/4, 1/5) | yes | balanced | yes | no / no / no | not checkable |

"Balanced" means all of the following hold:
- The configuration is realisable in 3D: the centred Gram matrix is PSD with rank 3.
- It is in equilibrium: ΩGΩ = 0.
- Every strut has quadrance 16.
- Every cable has positive quadrance.
- The struts are disjoint. Non-coplanar pairs are checked by Cayley–Menger volume; the three coplanar pairs are parallel and their separation is checked from polarised quadrances.

Non-congruence is proved by the pairwise-quadrance multiset differing from the reference.
Where coordinates materialise, they reproduce every metric quadrance exactly.

**Bounded sweep.** For off-diagonals in {−½, −¼, 0, ¼, ½}³, 121 of 125 metrics are PD and
admitted. All 121 are balanced, and they fall into at least 14 congruence classes.
The multiset distinguishes classes, so 14 is a lower bound.

**Restoration.** Setting M = I publishes a *new* handle whose geometry equals the
reference. The earlier handle keeps its own geometry. Certificates are not inherited
without an explicit REUSE.

**Refusals, each leaving the state unchanged.** Not positive-definite (m₁₂ = 6/5). Singular
(m₁₂ = 1, a flattened shape). Strut length changed (M₀₀ = 9/8). Coefficient bound (2³² denominator).
Not symmetric.

**Non-affine controls.** Rigidly translating one strut, by (1,0,0) or (0,0,1), keeps every strut length.
In both cases:
- REUSE refuses with DEPENDENCY_CHANGED.
- A mutant that carries the certificates anyway is caught: the independent check finds no equilibrium.
- The oracle does not report BALANCED. For the (1,0,0) move it reports STRUT_INTERSECTION first.

**Integer-coordinate reach.** An integer A with unit-norm columns has every column equal
to ±eₖ. Of the 216 such column triples, 48 are invertible, and each gives M = I, i.e. a
congruent copy. Enumeration and proof agree.

## Interpretation and claim boundary

- **Mechanism.** Equilibrium is preserved by any invertible linear map:
  Ω(X Aᵀ) = (ΩX)Aᵀ = 0 for the same stress. The strut-length constraint selects
  M = AᵀA with unit diagonal, a 3-parameter family. Super-stability adds that each
  admitted image is prestress-stable. That conclusion rests on Connelly's theorem
  (super-stability is invariant under non-singular affine maps). It was checked here
  on the reference only, not re-derived per state. Admissibility, by contrast, was
  **not** inherited from the reference: every admitted state was independently
  re-checked for realisability, equilibrium, strut lengths, cable tautness and strut
  disjointness. The non-affine strut-translation controls, including the mutant
  certificate carry, are retained as evidence that reuse does not accept every
  geometrically plausible edit.
- **Static only.** The results cover exact static equilibrium and admissibility, plus
  prestress stability via the cited theorem. This is not dynamic stability: there are no
  masses, damping or time-stepping. It is not real-world actuation: the force-density
  model has no constitutive law, so cable rest lengths that would realise each
  shape are not computed. It is not balancing control. The affine family implies
  cable-length (tendon) actuation, which is the option the 2026-09-04 contract deferred.
- **Earlier hypotheses stay falsified.** Single-strut octahedral rotation
  (2026-09-04) and paired-strut Option A (`8f3922e`) tested *rigid strut rotations*
  in a different actuation space. This experiment does not reach new states through
  those primitives, and it does not reclassify them. It identifies a different
  reachable family.
- **What "the integer approach did not reach" means precisely.** Integer coordinates
  admit only congruent copies under strut-preserving linear maps. Rational coordinates are
  *not* so limited: m₁₂ = 3/5 materialises in Q. So the representational boundary is
  field-dependent, not metric versus coordinates in general.

## Field-representability limits

Materialisation uses one Cholesky factor A. An `OUT_OF_FIELD` refusal means that
route needs a square root outside Q(√d). It does **not** prove that no coordinates
exist in that field: any QA with Q orthogonal also works, and existence of a rational
A is a quadratic-form question (Hasse–Minkowski). The relational state, quadrances,
equilibrium check and certificates never need coordinates. The oracle can only
confirm states that materialise in Q or Q(φ).

## Failed hypotheses and corrections during the run

- The first independent disjointness check (Cayley–Menger volume ≠ 0 only) rejected the
  reference. Three strut pairs are parallel, hence coplanar, so a zero volume is not
  evidence of contact. A parallel-separation test from polarised quadrances was added.
  Non-parallel coplanar pairs remain uncertified.
- The three `field.py` defects above.
- No experimental expectation was changed after observing results. The tests assert
  the values observed in one exploratory run, all of which match the design's predictions.

## Smallest next mathematical question

Within the admitted metric family, which configurations are **reachable by cable
rest-length changes under a specified constitutive law**? Equivalently: for linear
springs with t = k(ℓ − ℓ₀), which (M, ℓ₀) pairs satisfy equilibrium, and does that
map stay exact? It need not, because ℓ = √Q; a force-density or quadrance-based law
would keep it exact. This is the first point where physics, rather than geometry,
enters, and it decides whether the family is actuatable as well as admissible.
