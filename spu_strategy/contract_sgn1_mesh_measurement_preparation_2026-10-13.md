# SGN-1 isolated mesh adapter and measurement preparation

Date: 2026-10-13. Status: PREPARED / NOT EXECUTED.
Owner authorizes source and contract preparation only. Adapter tests and the
comparison campaign remain HOLD. Scheduler qualification remains CLOSED PASS;
Phase A remains OPEN. Surd CPU physical qualification retains priority.

## Review commands: authorized now

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/sgn1_mesh spu_strategy/contract_sgn1_mesh_measurement_preparation_2026-10-13.md docs/SGN1_RESEARCH_SPECIFICATION.md
sha256sum build/sgn1/mesh_cost_20261013/preparation_01/source_manifest.json
```

Parse prepared Python with `ast.parse` without importing or executing it.
Verify all snapshot digests against the qualified reference manifest.
Record static review separately from functional verification: syntax validity
does not establish routing, conservation, serialization or measurement correctness.

## Scope and source boundaries

Candidate source: [software/research/sgn1_mesh](../software/research/sgn1_mesh/).
Exact file hashes are frozen in
`build/sgn1/mesh_cost_20261013/preparation_01/source_manifest.json`.
Do not change the original FCC implementation, its snapshot, parent contract or
fixture plan. The qualified manifest SHA256 remains
`2ffbb5a8db811b2c804285a151c6c9158adfd631b701b950381be46113bbdce5`.

| Boundary | Prepared modules | Rule |
|---|---|---|
| Candidate mesh execution | topology, service, simulator | Local Manhattan selector, lexicographic six ports; no BFS/table lookup |
| Independent mesh oracle | oracle, checker_reference, trace_checker | Literal frozen coordinates, pairwise axis adjacency, BFS, independent dict transitions; no candidate imports |
| Frozen shared helpers | reference | Hash-bound immutable Packet, Node storage/snapshot, input validation and Accounting only for mesh |
| Common costs | wire, metrics | Same packet/storage model for both checked backends |
| Future execution | preflight, comparison, campaign | Fail on first error; no retry or reference mutation |

Frozen FCC trace checker and fixture enumerator are used for retained FCC
records and input labels, never to select a mesh port or perform mesh service.
The mesh checker shares qualified generic identity conservation, not the
candidate transition logic. This is independent implementation checking, not
a formal proof or a wholly independent packet protocol.

## Freeze the comparison profile

Use exactly the original endpoint mapping: FCC_R2 and 7×3×3 mesh, 63 nodes.
Retain 3,969 ordered pair cases and four FCC_R2 traffic fixtures: 3,973 cases
per node order/hash seed. Use forward/reverse node orders and seeds 0, 1, 17.
Keep every injection ID, tick, ordinal, endpoint and payload unchanged.
The prepared mesh tick cap is 4,096 per case; exhaustion fails with a retained
counterexample, never changes the routing expectation or silently extends the cap.

Retain one service per node per tick, old inbox prefix before arrivals before
host injections, arrivals sorted by ingress/packet key, host injections by ordinal,
alternating inbox/fanout preference, next-tick arrival, one packet per directed
link per tick, and unbounded queues. Wavefront first visits add once and create
all-port pending tasks; fanout occurs on later service ticks. Duplicates consume
service without adding again. Stop at the earliest complete drain.

Use retained qualified FCC traces instead of rerunning or modifying the FCC
backend. Verify each full decompressed stream against
`c7f965b888ec647198beb4fa7ec7c7885311ab8a2f5d43f1191b4d9aebc128c6`.
Recheck every selected FCC trace and every newly generated mesh trace.
Require equal final accumulator arrays, deliveries and first visits, with
separate topology-specific trace hashes. Require all six mesh and cost hashes
to match within their respective backend/model. No cross-topology trace equality.

## Common logical serialization and state model

Candidate model: 119 bits padded to 15 big-endian bytes; bit 119 is zero.
From high to low: kind1, source6, sequence32, signed two's-complement payload64,
target6, sender6, egress4. Low-bit offsets are 118, 112, 80, 16, 10, 4, 0.
Source/target IDs are 0–62. Absent target/sender use 63; absent egress uses 15.
Wavefronts require absent target and either absent sender/egress together or
valid sender and topology port. Unicasts require target and zero sender/egress.
Reject bools, out-of-range integers, invalid tags, padding, lengths and reserved
ports. No truncation. Debug paths and JSON are excluded instrumentation.

Live node bits: 64 accumulator + 1 preference + 120 per inbox packet + 124
per packet-plus-port pending task + 38 per source/sequence seen entry.
Validate signed64 accumulators at both observation boundaries. Report global
node-state peak, individual node peaks and in-flight packet bits separately;
do not sum independent peaks as if simultaneous. Exclude allocator, pointer,
queue-capacity-counter and Python-object overhead. This is prospective logical
state accounting, not a realizable memory budget or finite-buffer model.

## Measurement definitions and evidence levels

| Level | Measurements | Interpretation |
|---|---|---|
| A mathematical | Nodes, links, degrees, diameter, BFS distance | FCC240/mesh138 undirected links; maximum degree12/6; diameter6/10 |
| B simulated/modelled | Messages, bytes, latencies, queues, state | Workload-specific synchronous software observations |
| C physical | LUTs, congestion, Fmax, power, wire length | UNMEASURED; separate future contract |

Each committed transmission is one link message and 15 modeled bytes. Report
host injections separately. Updates are unicast deliveries plus first visits;
report messages/update as numerator/denominator, including a possible zero
denominator. Per-link use counts transmissions/occupied ticks and drain ticks;
absent entries mean zero use. Do not infer steady-state throughput.

Delivery latency is service tick minus injection tick plus one. Wavefront
completion is the last first visit under the same convention. Drain ticks
include all duplicate consumption. Report each separately; no undefined
workload critical-path claim. Self-delivery takes one tick.

Count per-node contention when both pre-service inbox and pending are nonempty.
Count waiting-item ticks from post-service inbox and pending occupancy separately.
Report service classes and per-node/global queue peaks. Normalization operations
are zero for these integer-addition fixtures. Host sorting comparisons are
implementation costs, not wire cost. Retained-FCC versus new-mesh processing
time is not a valid host speed comparison and will not be reported as one.

This is equal nodes/per-node service/per-link capacity, not equal total links
or physical wiring budget. Keep FCC's 102 extra links visible. Accept either
topology's result; there is no FCC superiority gate.

## Negative controls and future commands: NOT authorized now

Prepared preflight covers independent all-pair routing, adjacency, diameter,
wavefront labels 276 sends/214 suppressions, next-tick delivery, admission order,
node-order repeatability, literal header offsets, storage arithmetic and bounds.
Mutations cover tick order, hidden link drop, accumulator corruption, wrong
service, service-count corruption, early termination, same-tick fanout, missing
seen update, wrong preference, duplicate arithmetic and missing observation.
Range controls cover bool/source63, sequence overflow, signed64 bounds, absent
fields, invalid ports, padding and malformed lengths. These are NOT RUN.

After a separate owner authorization, the exact proposed single campaign is:

```bash
tools/run_detached_job.sh --output build/sgn1/mesh_cost_20261013/qualification_01 --timeout 3000 --notify-desktop -- python3 -m software.research.sgn1_mesh.campaign build/sgn1/mesh_cost_20261013/qualification_01/artifacts
```

Proposed budget: one attempt, 3,000-second wall timeout, 3,000-second cumulative
budget, zero retries. This budget is NOT owner-authorized. The driver runs
preflight and comparison under each seed, then repository, ROTC/IROTC and math
gates. No synthesis: no RTL or hardware build behavior changes in this scope.
Retain mesh traces, paired costs and hashes under the new job directory.
After LAUNCHED, end the turn; later interpret exactly one terminal marker.
Failure, timeout, source drift or counterexample halts the campaign and requires
review. No substitute mapping, longer timeout or retry is implicitly authorized.

This preparation closes no functional gate. Comparison acceptance also does
not automatically close Phase A or authorize AOR, finite buffers, RTL or FPGA.
