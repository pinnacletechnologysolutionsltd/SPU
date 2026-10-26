# Engineering Contract: Exact geometry G1/G2
Date: 2026-10-17
Status: ACTIVE — software tranche authorized by owner

## Roles and scope
Spec author, implementer, auditor: current agent, sequentially.
Create only `research/exact_geometry/` and this contract. Preserve existing work.

## Commands and invariants
1. Implement `oracle.py`: arbitrary-precision Fraction coordinates; reject floats;
   canonicalize gauge by subtracting mean; use G=4I-11^T.
2. Implement `predicates.py`: signed Cartesian tetrahedral orientation and exact
   closed ray/segment intersection, including parallel overlap and skew cases.
   Reject zero directions explicitly. Gram-zero means dependence only.
3. Implement an independent Cartesian baseline using cross products.
4. Run `python3 -m unittest discover -s research/exact_geometry -p 'test_*.py' -v`.
5. Run `python3 -m research.exact_geometry.compare`.
6. Run `git diff --check -- research/exact_geometry spu_strategy/contract_exact_geometry_g1_g2_2026-10-17.md`.
7. Launch `bash tools/verify_repo.sh` with the detached runner, timeout 1800 seconds,
   one attempt; record terminal status in a later invocation. No automatic retry.

## Acceptance
G1: exact metric agrees with independent Cartesian dot, gauge invariance,
zero and rational controls. G2: collinear/noncollinear controls and frozen
N=1,10,10^3,10^12,10^50 give Gram 48 and normalized 3/[4(N²+N+1)].
Track A: baseline agreement on deterministic rational cases; signed orientation;
intersection controls for crossing, skew, parallel disjoint, overlap, endpoints,
and opposing rays. Report software costs separately from correctness.

## Boundaries and stop conditions
No opcode, RTL, rasterizer or simulator changes. No physical interpretation.
No G3-G5 implementation. No claim of GPU speedup from Python timings.
Halt on contradictions or failing checks; report counterexamples.
Hardware synthesis/interface/silicon dimensions: NOT RUN, out of scope.
