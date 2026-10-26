# Contract: opt-in unshared robotics kernel

Date: 2026-10-06 (Pacific/Auckland)  
Status: ACTIVE — software-only opt-in implementation.

## Commands

```bash
timeout --signal=KILL 60s python3 software/tests/test_rational_robotics_unshared.py
git diff --check -- software/lib/rational_robotics_unshared.py software/tests/test_rational_robotics_unshared.py spu_strategy/contract_rational_robotics_unshared_2026-10-06.md
```

## Scope

Add `software/lib/rational_robotics_unshared.py` with public
`apply_joint_pair(vector, joint) -> (forward, recovered)`. This is an explicit
opt-in API. Preserve `software/lib/rational_robotics.py` as the unchanged
reference and default for existing robotics calls. Add one focused test file.
No timing campaign, default dispatch change, native code, hardware, RTL, ISA,
UART, firmware, or new dependencies.

## Semantics

Represent each Q3 coefficient pair as its own `(a,b,d)` with `d>0`, where the
value is `(a+b*sqrt(3))/d`. Do not align all seven input denominators to a shared
scale. Defer canonicalization until materializing the eight output Q3 values.
Use the maintained forward circulant equations and determinant-one adjugate
recovery exactly. Do not divide by a determinant or reject singular joints;
match `apply_joint` and `apply_inverse_joint` behavior, including outside the
unit-determinant closure domain.

The return values are the same two `QuadrayQ` objects produced by calling the
maintained reference forward and inverse functions in sequence. Use exact
`Fraction` values only. This work makes no speed claim.

## Verification and boundaries

The focused test compares against the unchanged reference on catalog fixtures
and a deterministic broader set including nonzero Surd coefficients in both
vectors and joints, unequal denominators, zero, and singular joints. Assert
closure only for declared determinant-one joints; otherwise require exact
reference equality. Run the scoped repository gates required by `AGENTS.md`
before treating the new API as verified. Existing C1 and repository-gate
artifacts remain immutable and are referenced, not rewritten.
