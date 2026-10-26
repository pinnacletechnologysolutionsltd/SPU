# FIELD-0: intrinsic metric vs Surd representation

Status: software-only mathematical audit, 2026-10-23. Not hardware qualification, not exhaustive
architectural coverage, not a measured distribution of renderer/CPU operations.

Reproduce: `python3 software/tests/test_field0_intrinsic_metric.py` (9 checks, exact Fractions).
Not in `run_all_tests.py`; integrate in a separate test-maintenance pass.

## Classification (representative operations only)

| Class | Operations shown |
|---|---|
| Intrinsically integer/rational | A2 quadrance, inner product, spread (basis spread 3/4); A2 60-degree rotation `[[0,-1],[1,1]]` (R^T G R = G, R^6 = I; exactly 12 integer isometries); Quadray Gram (3 on diagonal, -1 off) and quadrance; 24 cube rotations as signed Quadray permutations; 60-degree rotation about a body diagonal (denominator 3) |
| Rational with extra state / other basis | Non-lattice A2 rotations z/zbar (e.g. z=2+zeta, denominator 7: denominators grow); 3-4-5 rotation is Cartesian-rational but A2-irrational |
| Needs an extension | One basis exposing both lattice-native (60 deg) and Cartesian-native (90 deg, 3-4-5) rotations |

Caveat: "only /3 tagging" is NOT established. Rational rotations and projective transforms
introduce other denominators; general transforms may need an extension or explicit refusal.

## SIM-CAP1 compatibility item: `QuadrayVector.rotate()` (software/spu_vm.py)

Docstring claims "Quadrance is preserved". Counterexample (exact):
`QuadrayVector(RS(3),RS(1),RS(0),RS(0)).rotate()` -> quadrance 24 becomes 168+96*sqrt3 = 24*(7+4*sqrt3).

Cause: the field norm N(2+sqrt3) = 2^2 - 3*1^2 = 1 is not the Euclidean scale factor; multiplying
every component by u scales Euclidean quadrance by u^2 = 7+4*sqrt3. Pell multiplication preserves the
indefinite form x^2-3y^2, not a positive-definite metric.

Already identified by METRIC-VAL-1 (`spu_strategy/metric_val_1/REPRODUCERS/val_d_transforms.py`,
`rotate_is_dilation_not_isometry`); FIELD-0 reproduces it independently, pinned in
`test_pell_rotor_is_integer_but_not_euclidean`. Simulator behavior unchanged pending the SIM-CAP1 decision.
