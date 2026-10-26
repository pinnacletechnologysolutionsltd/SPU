# SGN-1 third software increment: independent BFS and local routing probe

Date: 2026-10-13. Status: COMPLETE for isolated routing increment;
focused qualification PASS, repository/software regression COMPLETE (exit 0).
Roles: command-first draft; halt-and-flag implementation; independent audit.

## Focused commands

```bash
python3 software/tests/test_sgn1_geometry_oracle.py
python3 software/tests/test_sgn1_symmetry_oracle.py
python3 software/tests/test_sgn1_routing_oracle.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/sgn1 software/tests/test_sgn1_routing_oracle.py spu_strategy/contract_sgn1_routing_oracle_increment_2026-10-13.md docs/SGN1_RESEARCH_SPECIFICATION.md
```

After the symmetry regression has exactly one COMPLETE marker, launch the
following single repository/software regression attempt. Do not run full suites
concurrently because they share generated test artifacts. If the preceding
regression fails or times out, retain its result and review before launch.

```bash
tools/run_detached_job.sh \
  --output build/sgn1/routing_oracle_20261013/regression_01 \
  --timeout 1800 --notify-desktop -- bash -c 'set -e
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py'
```

One attempt, 1,800 seconds; no automatic retry or timeout extension. Inspect the
terminal marker in a later invocation. No production RTL, kernel or build flow
changes; FPGA synthesis is inapplicable. Explicit Python commands provide scope
coverage; an empty TB_FILTER run does not.

## Scope and frozen semantics

Add `software/research/sgn1/routing_oracle.py` (BFS and path checker),
`software/research/sgn1/local_routing.py` (metric and stateless port selection),
and `software/tests/test_sgn1_routing_oracle.py` (bounded-graph probe).
No tick scheduler, packet queues, wavefront, AOR or hardware work is included.
This increment tests a stateless local route, not deterministic packet delivery.

BFS uses the independent squared-distance graph; it imports neither the routing
metric nor port selector. The selector receives only an exact FCC displacement
and available ordered basis pairs; it receives no graph, BFS table or destination
ID. Validate strict integer types and FCC parity before arithmetic. Validate all
available pairs, reject duplicates, then use lexicographic port order.

Use h=max(abs(dx),abs(dy),abs(dz),(abs(dx)+abs(dy)+abs(dz))/2), with exact integer
division in this software probe. Self arrival returns no port; otherwise select
the first legal port strictly reducing h. No improving port raises ROUTE_STALL
with the displacement and available ports. Never substitute global search.

Check all 169/3,969 ordered pairs including self. Compare h with independent BFS
distance, inspect every non-destination current/target pair for a legal improving
hop, then check complete paths for endpoints, legal edges, no repeats and BFS
hop count. All paths remain within their bounded graph. Repeat-run hashes cover
the canonical all-pair path catalogue, not timing text.

Negative controls: wrong endpoints, missing observations, illegal edges, duplicate
nodes, longer legal paths, malformed input, removed improving ports and a wrong
metric. Retain named rejection reasons and first counterexamples. Removing all
improving ports must produce ROUTE_STALL even when BFS on the original graph
could find a path. A positive-profile stall halts for review without expectation
changes. Matching tested profiles proves no universal routing theorem.

## Evidence and next step

Retain source/plan hashes, all-pair paths, summaries and negative-control examples
under `build/sgn1/routing_oracle_20261013/focused_01/`, with seeds 0,1,17.
Repository checks remain pending until their detached terminal result exists.
Packet scheduling remains a separately reviewed next increment.

Focused results: 169/3,969 ordered pairs, 144/3,100 boundary non-self cases,
zero stalls and graph diameters 2/6. All 16 geometry/symmetry/routing tests pass
under each of seeds 0,1,17; route/action hashes match. Eleven negative-control
counterexamples and the canonical all-pair paths are retained. No packet-service,
queue, contention, wavefront or distributed algebra acceptance is implied.

The initial test fixture incorrectly expected radius-2 diameter 4. Independent
BFS returned 6; opposite corners have displacement (4,4,4), whose metric is 6.
The fixture was flagged and corrected to 6; routing and acceptance rules were
unchanged. Retain this preparation error separately from any routing counterexample.

The sole terminal marker in `build/sgn1/routing_oracle_20261013/regression_01/`
is COMPLETE. `result.json` records exit 0 and duration 927 seconds against the
1,800-second limit. All commands in the frozen regression sequence succeeded.
