# Engineering Contract: G3 rational paired-state isometries
Date: 2026-10-17
Status: ACTIVE — owner authorized separate mathematical/software tranche
Roles: current agent performs specification, implementation and audit sequentially.

## Commands and scope
1. Create `research/exact_geometry/isometries.py`, `test_isometries.py`,
   `g3_demo.py` and `G3.md`; update package README historical status.
2. Use B with rows (1,1,-1,-1), (1,-1,1,-1), (1,-1,-1,1).
   Define P=11^T/4, G=B^T B, T(R)=B^T R B/4+P.
3. Freeze R=((3/5,-4/5,0),(4/5,3/5,0),(0,0,1)); H=diag(1,-1,1).
   Define U(o,c)=(T(R)o,T(R)c), J(o,c)=(T(H)o,T(H)c).
4. Check exact identities T^T G T=G, inverse T(R^T), gauge preservation,
   J^2=I and J U J=U^-1. Check Cartesian bridge independently.
5. Check a frozen node network and a sequence R,R^T,R^2 preserves all pair
   distances and displacement Gram values. Include inconsistent constraints.
6. Run `python3 -m unittest discover -s research/exact_geometry -p 'test_*.py' -v`.
7. Run `python3 -m research.exact_geometry.g3_demo`.
8. Run `git diff --check -- research/exact_geometry spu_strategy/contract_exact_geometry_g3_2026-10-17.md`.
9. Launch `bash research/exact_geometry/check_repo.sh` through the detached
   runner, new output directory, timeout 1800 seconds, one attempt, then end turn.

## Pre-execution review and acceptance
Flag: metric identity alone does not establish full-space invertibility because
G is singular. Correction: freeze gauge action to identity with P and explicitly
verify the two-sided inverse. The canonical state space is the rational
zero-sum subspace; full matrices also act invertibly on redundant coordinates.

Accept exact matrix identities, 200 seeded paired rational states, frozen
near-degenerate family and network checks, and negative controls: pair swap
is involutive but fails time reversal; unequal component isometries can destroy
Gram-zero; a singular gauge projection satisfies metric preservation but has
no full-space inverse. Nonzero network residuals must remain nonzero.

No RTL, opcode, GPU or simulator changes. No new physics, speedup, novelty,
generic constraint-network solver, or guarantee for noncommuting schedules.
Hardware realization and performance NOT RUN. Halt on contradictions or test
failures; report counterexamples rather than silently changing the model.
