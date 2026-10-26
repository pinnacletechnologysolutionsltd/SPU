# SGN-1 first software increment: independent geometry oracle

Date: 2026-10-13. Status: COMPLETE for isolated geometry-oracle increment;
focused checks PASS, detached repository/software gates COMPLETE (exit 0).
Roles: spec author scopes; implementer reviews domain/edges; auditor checks evidence.

## Commands

```bash
python3 software/tests/test_sgn1_geometry_oracle.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/sgn1 software/tests/test_sgn1_geometry_oracle.py docs/SGN1_RESEARCH_SPECIFICATION.md docs/README.md spu_strategy/contract_sgn1_geometry_oracle_increment_2026-10-13.md
```

Run the required repository/software regression gates as one detached job:

```bash
tools/run_detached_job.sh \
  --output build/sgn1/geometry_oracle_20261013/regression_01 \
  --timeout 1800 --notify-desktop -- bash -c 'set -e
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py'
```

One regression attempt, external limit 1,800 seconds; no automatic retry.
Only a later invocation may interpret its terminal marker. No hardware build
flow or production arithmetic kernel changes; FPGA synthesis is not applicable
to this host-only geometry oracle. TB_FILTER cannot exercise this Python test;
use the explicit focused command above, without claiming an empty RTL run as coverage.

## Authorization and scope

The owner's 2026-10-13 instruction to start software oracles supersedes the
documentation HOLD for this isolated first increment. Preserve the earlier
[Phase A contract](contract_sgn1_phase_a_2026-10-12.md) and fixture-plan statuses
as historical preparation; this increment does not ratify scheduling or traffic.

New source files are `software/research/sgn1/{__init__,literals,geometry,graph_oracle}.py`
and `software/tests/test_sgn1_geometry_oracle.py`. Keep oracle modules separate
from future implementation and from production SPU arithmetic, VM and hardware.
No router, packet simulator, stencil, hierarchy, RTL, CPU integration or FPGA
campaign is included. No bounded-width claim or performance comparison is included.

## Reviewed invariants and checks

Use literal node profiles, pairwise squared-distance-two adjacency and literal
port fixtures. The graph oracle must not import Quadray conversions or neighbour
generation. Validate container, length, exact integer types and parity in that order.
Use arbitrary-precision integer coordinates; reject invalid images rather than round.

Focused checks cover the 19 prepared domain rows; strict container/coefficient
subclasses and rejection precedence; 625 small Quadray tuples checked against
an independently evaluated unscaled basis sum; Cartesian enumeration of both
literal profiles; 36/240 undirected edges; boundary/interior degrees; connectivity;
inverse lifts and common offsets through ±10^100; all 12 literal directed ports
and reverses. Graph mutation controls exercise node reordering, adjacency length,
removed edges, self edges and neighbour reordering, retaining named counterexamples.

Any failed fixture or escaped negative control halts this increment. Focused
oracle qualification is not acceptance of the future graph generator or network.
All seven end-to-end Phase A simulator gates remain NOT RUN.

## Evidence and next increments

Focused outputs, source hashes and the prepared plan hash are retained under
`build/sgn1/geometry_oracle_20261013/focused_01/`. Repository-wide audit findings
remain separate from focused acceptance. Do not infer a clean repository result.

The sole terminal marker in `build/sgn1/geometry_oracle_20261013/regression_01/`
is COMPLETE; `result.json` records exit 0 and duration 953 seconds against the
1,800-second limit. All commands in the frozen regression sequence succeeded.
This establishes the repository/software regression result, not resolution of
the separately recorded documentation-audit findings or network acceptance.

Next: independently check the 24 permutations and 576 compositions. Then build
BFS reference distances and verify the improving-hop rule across both bounded
graphs, retaining boundary stalls unchanged. Review these before packet scheduling.
