# Engineering Contract: S2-P exact affine projection and observability
Date: 2026-10-17
Status: ACTIVE — owner authorized bounded software experiment alongside S1
Roles: current agent performs specification, implementation and audit sequentially.

## Scope and commands
1. Create only `research/symbolic_projection/` and this contract. Keep S1 separate.
2. Implement exact rational row reduction and affine families over Q^n.
   Frozen objects store canonical origin/basis or explicit empty family.
   Support dimensions 1..8, at most 64 matrix rows, 4096-bit coefficients.
3. Transform/project by matrix image, reducing dependent image directions.
   Observe via exact intersection with A*x=y; retain empty/unique/family status.
4. Test closure only for surjective P and square T on the same domain;
   use rank([P;PT])=rank(P), equivalent to ker(P) invariance.
5. Construct O_k=[P;PT;...;PT^(k-1)] with 1<=k<=8 and <=64 rows;
   recover initial states by observing the full affine state space.
6. Run `python3 -m unittest discover -s research/symbolic_projection -p 'test_*.py' -v`.
7. Run `python3 -m research.symbolic_projection.demo`.
8. Run `git diff --check -- research/symbolic_projection spu_strategy/contract_symbolic_s2p_2026-10-17.md`.
9. Launch `bash research/symbolic_projection/check_repo.sh` detached, one attempt,
   timeout 3600 seconds including S1 prerequisite wait, new output directory;
   end turn at launch. Linux waits for exactly one S1 terminal marker and starts
   the gate only after COMPLETE/exit 0; avoid concurrent shared regressions.

## Acceptance
P1 canonical equivalent families, empty/singleton distinctions, immutability.
P2 exact reversible transformation and inverse round-trip.
P3 rank reduction under projection without sampling; dimension cannot increase.
P4 T1 closes, T2 fails with a frozen indistinguishable-state counterexample.
P5 T1 rank3, T2 two observations rank4; exact witness recovery and inconsistent
observations; a 5D cyclic map exposes two hidden coordinates in successive steps.
P6 composition versus stepping on families and stacked measurement constraints.
Reject floats, dimension mismatch, non-surjective closure projection and budgets.

## Boundaries and pre-review
S1 currently has no terminal marker: result unavailable, not failed or passed.
Independent S2-P work does not change or restart that job.
Uncertainty means a set over Q, not a probability distribution. Dimension of
an observed image can increase after evolution but not exceed internal family
dimension. No E8/surds, learning, RTL, opcodes or general nonlinear solver.
No claims of new observability mathematics. Resource bounds are software guards,
not hard host isolation. Halt on contradictions or failing tests.
