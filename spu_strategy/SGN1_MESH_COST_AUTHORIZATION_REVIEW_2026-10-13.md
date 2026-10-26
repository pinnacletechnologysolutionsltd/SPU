# SGN-1 mesh/cost authorization review

Date: 2026-10-13. Status: REVIEW PREPARED; execution NOT AUTHORIZED.
Scheduler gate CLOSED PASS; Phase A OPEN. No new campaign is launched.

Later owner decision: isolated adapter and measurement-contract preparation is
authorized. The [prepared candidate](contract_sgn1_mesh_measurement_preparation_2026-10-13.md)
freezes that source/model proposal. Its tests and campaign remain NOT RUN;
the execution HOLD and requirement for a separate owner-approved budget remain.

## Review commands

```bash
python3 -m json.tool build/sgn1/scheduler_20261013/qualification_01/result.json > /dev/null
python3 -m json.tool build/sgn1/scheduler_20261013/qualification_01/artifacts/result.json > /dev/null
sha256sum build/sgn1/scheduler_20261013/qualification_preparation_01/source_manifest.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/SGN1_MESH_COST_AUTHORIZATION_REVIEW_2026-10-13.md docs/SGN1_RESEARCH_SPECIFICATION.md
```

The sole scheduler terminal marker is COMPLETE, exit 0, duration 1,142 seconds.
Its source snapshot, traces and sixteen control types remain the frozen reference.
The [comparison preparation](contract_sgn1_mesh_cost_preparation_2026-10-13.md)
is a measurement proposal, not implementation or execution authority.

## Preserve the qualified implementation

Frozen snapshot: `build/sgn1/scheduler_20261013/qualification_preparation_01/snapshot/`.
Manifest SHA256: `2ffbb5a8db811b2c804285a151c6c9158adfd631b701b950381be46113bbdce5`.
Retain the original fixture plan, whose SHA256 is
`289c2860aca4ea4607151e181da3995b2adda2e7e88b5816104bd9cde97bac8b`.
Verify snapshot files against the manifest before any comparison.

Review flag: the existing service and commit code imports FCC ordered basis
pairs and the FCC selector directly. It is not a generic mesh scheduler.
Supplying mesh links would violate the port interface and routing domain.
Minimal proposed correction: a separate mesh adapter in an isolated comparison
package, with independent mesh adjacency/BFS and dict-based tick checking.
Do not edit, monkeypatch or silently generalize the frozen FCC implementation.
Freeze exact adapter source paths and checker boundaries before coding it.

Use the frozen FCC backend for FCC observations. Qualify the mesh adapter's
admission, alternating service, first-visit/fanout separation, duplicate cost,
next-tick commit and termination against the same reviewed protocol.
Require identical application labels, not identical traces between topologies.
Within each backend, compare traces across the same node orders/hash seeds.
Do not equate reproducibility of these deterministic runs with cross-device proof.

## Structural controls, derived before comparison

| Property | FCC_R2 | 7×3×3 nearest-axis mesh |
|---|---:|---:|
| Nodes | 63 | 63 |
| Undirected links | 240 | 138 |
| Directed links | 480 | 276 |
| Maximum degree | 12 | 6 |
| Graph diameter | 6 | 10 |

FCC counts/diameter are retained geometry/routing results. Mesh links follow
6×3×3 + 7×2×3 + 7×3×2 = 138; its diameter is 6+2+2 = 10.
These are structural expectations, not a new mesh simulation result.
FCC has 102 additional undirected links. This is an equal-node/per-service/
per-link-capacity comparison, not an equal-total-link or physical wiring budget.

With the frozen all-port wavefront rule, each first-visited node creates one
task per present port. After complete connected-graph propagation, the expected
link-message counts are therefore 480 versus 276 and duplicate consumptions
418 versus 214. These are analytic labels to check, not measured mesh outcomes.
Do not assume fewer unicast hops imply less broadcast traffic or shorter drain time.

Use all 3,969 pairs and the four FCC_R2 traffic fixtures with unchanged endpoint
IDs, ticks and payloads under the plan's frozen lexicographic mapping. Report
both coordinate assignments: identical IDs do not preserve neighbourhoods.
Do not select a new mapping after observing costs. The two existing scheduling
checkpoint fixtures belong to FCC_R1; use them to check service semantics, not
as literal mesh node/port expectations.

## Measurement definitions to resolve before authorization

Adopt or revise the proposed common 119-bit/15-byte serialization explicitly.
If adopted, require encode/decode and range controls before any byte result:
signed64 payload, unsigned32 sequence, reserved absent-field codes, malformed
types, header corruption and no truncation. All current literal payload/sequence
labels fit; that does not cover arbitrary unbounded simulator inputs.
Exclude debug paths and JSON snapshots from modeled traffic and logical state.

One proposed live-state model is 64 accumulator bits + 1 preference bit per node,
120 bits per queued packet, 124 per packet-plus-port fanout task and 38 per seen
source/sequence pair. Report in-flight packet bits separately. Validate all
modeled accumulator ranges. Queue pointers, allocators and capacity counters are
excluded overheads, so this is not a complete FPGA storage estimate.

Define waiting-item ticks from post-service queued occupancy; report inbox and
fanout separately. Count simultaneous inbox/fanout contention and service classes.
Report injection-to-delivery, last first-visit application, and drain makespan
separately, using the preparation packet's tick conventions. Retain per-link
traffic, update counts, service operations, normalization count and host costs.
Normalization is zero for this integer-addition workload, not for future AOR work.

Freeze structural interconnect proxies separately from a physical cost model.
Without placement/layout and technology assumptions, wire length, FPGA routing
congestion, timing, power and energy remain unmeasured. No physical-cost PASS
follows from the structural table or modeled bytes.

## Authorization readiness

Not launch-ready: the separate mesh adapter, independent checker, selected byte/
storage model, negative-control schedule, source identities, exact qualification
commands and owner-authorized attempt/time budget are not yet frozen.
Do not infer any implementation or campaign authorization from this review.
Keep acceptance about correctness and fair accounting; impose no FCC superiority
threshold. Audit remaining Phase A requirements after comparison qualification
before declaring closeout. Surd CPU physical work retains its priority.
