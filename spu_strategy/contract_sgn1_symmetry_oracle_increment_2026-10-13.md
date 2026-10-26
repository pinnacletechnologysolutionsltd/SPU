# SGN-1 second software increment: symmetry correspondence

Date: 2026-10-13. Status: COMPLETE for isolated symmetry increment;
focused checks PASS, repository/software gates COMPLETE (exit 0).
Roles: draft, halt-and-flag, audit.

## Commands and single regression budget

```bash
python3 software/tests/test_sgn1_geometry_oracle.py
python3 software/tests/test_sgn1_symmetry_oracle.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/sgn1 software/tests/test_sgn1_symmetry_oracle.py spu_strategy/contract_sgn1_symmetry_oracle_increment_2026-10-13.md docs/SGN1_RESEARCH_SPECIFICATION.md
```

```bash
tools/run_detached_job.sh \
  --output build/sgn1/symmetry_oracle_20261013/regression_01 \
  --timeout 1800 --notify-desktop -- bash -c 'set -e
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py'
```

One attempt, 1,800 seconds, no automatic retry. Launch only after focused checks.
Inspect its single terminal marker in a later invocation. No production kernel,
RTL or hardware build changes; FPGA synthesis is inapplicable. TB_FILTER cannot
exercise these Python tests; use the explicit scoped commands above.

## Scope and pre-execution review

Add `software/research/sgn1/symmetry_oracle.py`,
`software/research/sgn1/symmetry_action.py` and
`software/tests/test_sgn1_symmetry_oracle.py`. Preserve geometry-oracle evidence.
The owner's instruction to continue authorizes this next isolated software step.
No router, packet scheduler, AOR bridge, finite-width or hardware work is included.

For sigma mapping old basis index to new basis index, assign q'[sigma(i)]=q[i].
Composition means apply sigma then tau: combined(i)=tau(sigma(i)). Retain both
orientation-preserving and orientation-reversing symmetries, 12 of each.

Use independent Cartesian signed-coordinate permutations as the reference:
all six axis permutations times four sign choices with sign product +1.
They preserve the four literal tetrahedral basis vertices and the bounded cubes.
Derive the corresponding basis permutation from the Cartesian action on those
vertices, not from Quadray conversion. This reference must not import geometry
conversion or the basis-action implementation.

Compare all 24 Quadray actions against this reference on every node, boundary
edge and directed port in both profiles. Require bijections, adjacency,
inverse composition and all 576 pair compositions on every node and port.
Verify strict domain rejection and offset equivalence. Check wrong node action,
wrong/reversed port action and mislabelled symmetry with named first counterexamples.
No identical routing-path claim is implied by graph equivariance.

Halt on a mismatch or escaped negative control; do not weaken expected mappings.
This qualifies geometry/group correspondence in host software, not communication
execution or network efficiency. All packet-simulator acceptance gates remain NOT RUN.

## Evidence and next step

Retain source/fixture hashes and focused outputs under
`build/sgn1/symmetry_oracle_20261013/focused_01/`, including seeds 0,1,17.
Require identical canonical action-catalogue hashes across these runs, independently
of timing text. Record repository/audit results separately.
Next: independent BFS and bounded-graph improving-hop checks before scheduling.

The sole terminal marker in `build/sgn1/symmetry_oracle_20261013/regression_01/`
is COMPLETE. `result.json` records exit 0 and duration 927 seconds against the
1,800-second limit. Every command in the frozen regression sequence succeeded.
This qualifies the repository/software gates, not physical or packet-network
acceptance or resolution of separately recorded documentation-audit findings.
