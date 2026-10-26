# Engineering Contract: exact paired-boundary closure pilot
Date: 2026-10-17
Status: ACTIVE; software-only continuation authorized by owner
Roles: current agent performs specification, implementation and audit sequentially.

## Commands and scoped files
1. Create `research/exact_geometry/closure.py`, `test_closure.py`, and
   `closure_demo.py`; append results and semantics to the package README.
2. Solve p+t*u=q+s*v over rational canonical Quadray coordinates with closed
   segment [0,1] or ray [0,infinity) parameter domains. Reject zero directions.
3. Return no solution, a unique exact witness, or an explicit one-parameter
   family. For a family report t in [lo,hi], s=(t-offset)/scale, x=p+t*u;
   hi=None denotes no finite upper bound. Never interpret Gram-zero as closure.
4. Run `python3 -m unittest discover -s research/exact_geometry -p 'test_*.py' -v`.
5. Run `python3 -m research.exact_geometry.closure_demo`.
6. Run `git diff --check -- research/exact_geometry spu_strategy/contract_exact_geometry_closure_2026-10-17.md`.
7. Launch `bash research/exact_geometry/check_repo.sh` with detached runner,
   timeout 1800 seconds, one attempt. End turn on launch; no automatic retry.

## Acceptance and boundaries
Check exact residuals, gauge invariance, swapped boundary classification,
independent Cartesian intersection baseline, known singleton/empty/family
cases, rational endpoints, and near-degenerate unique solutions.
Pre-review: nonzero directions make the family parameterization injective;
closed interval singleton must be classified unique, not a family.
No RTL, ISA, GPU, simulator, G3 evolution or physical claims. Hardware gates
are inapplicable to this independent Python package. Halt on failed checks or
specification contradictions. Prior tranche gate: COMPLETE/exit 0, 244 PASS,
0 FAIL in build/exact_geometry/g1_g2_20261017_01.
