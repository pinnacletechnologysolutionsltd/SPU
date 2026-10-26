# SGN-1: Synergetic Geometric Network research specification

Date: 2026-10-13. Status: FROZEN DOCUMENTATION MILESTONE;
isolated geometry/routing oracles and scheduler implementation subsequently
authorized. Serialized predecessor regressions and bounded FCC scheduler
qualification passed. Phase A mesh/cost comparison remains open; Phase B/C remain proposed.

The [first software increment](../spu_strategy/contract_sgn1_geometry_oracle_increment_2026-10-13.md)
records the owner's later authorization, isolated source scope and focused
oracle checks. It does not ratify the synchronous packet protocol.

The [second software increment](../spu_strategy/contract_sgn1_symmetry_oracle_increment_2026-10-13.md)
checks all 24 transformations and 576 compositions against an independent
Cartesian reference on both profiles. Focused checks and broader regression
pass. These are geometry/action checks, not packet-network acceptance.

The [third software increment](../spu_strategy/contract_sgn1_routing_oracle_increment_2026-10-13.md)
checks stateless local paths against independent BFS for all 4,138 ordered pairs.
Focused checks pass with zero positive-profile stalls, including boundaries.
Repository checks pass; bounded tick-based delivery subsequently qualified below.
The [fourth software increment](../spu_strategy/contract_sgn1_scheduler_implementation_2026-10-13.md)
subsequently implements synchronous unicast/wavefront service. Its seven short
preflight tests pass; full fixture/all-pair/hash-seed qualification subsequently passed below.
The [bounded scheduler qualification](../spu_strategy/contract_sgn1_scheduler_qualification_2026-10-13.md)
uses a frozen source snapshot, 4,148 cases per order/seed and sixteen controls.
Its artifact PASS and sole COMPLETE marker (exit 0) establish acceptance of
24,888 FCC case executions under the tested node orders/seeds and sixteen
negative-control types. The mesh/cost comparison is outside this tranche.
The [mesh/cost authorization review](../spu_strategy/SGN1_MESH_COST_AUTHORIZATION_REVIEW_2026-10-13.md)
preserves the frozen scheduler, identifies the separate mesh-adapter requirement,
and records structural controls and measurement choices. No comparison campaign
is authorized or launched by that review.

The later [isolated mesh preparation](../spu_strategy/contract_sgn1_mesh_measurement_preparation_2026-10-13.md)
records owner-authorized source preparation, checker boundaries, logical packet/
state models and a proposed single-attempt budget. Sources are prepared; adapter
tests and the comparison campaign remain NOT RUN and execution remains HOLD.

The [algebraic–geometric machine direction](ALGEBRAIC_GEOMETRIC_MACHINE_RESEARCH_DIRECTION.md)
records the proposed AOR/SGN synthesis and five later research gates without
authorizing unified-machine implementation.

## Documentation review commands

Run from the repository root; these commands review documents, not experiments.

```bash
python3 -m json.tool spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/SGN1_RESEARCH_SPECIFICATION.md docs/README.md
```

## Research question and scope

Can a computing network exploit the same geometric relationships that its
processing elements calculate? The first proposed test asks whether exact
Quadray displacements and tetrahedral transformations can select neighbour
ports and permute communication operations in a deterministic network.

Prepare an isolated Python simulator before considering standalone RTL or FPGA
work. Keep the integrated Surd CPU as the immediate hardware priority and the
Surd register paper as a parallel writing priority. This note authorizes only
documentation preparation; it neither starts a simulator nor ratifies a campaign.

The [Phase A contract](../spu_strategy/contract_sgn1_phase_a_2026-10-12.md)
and [fixture plan](../spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json)
contain the detailed proposed protocol. Their corrected coordinate domain is
ratified; scheduling, traffic, implementation and execution remain on HOLD.
This summary adds no executable semantics or contract ratification.

## Phase A: exact geometric correspondence

Use the FCC lattice V={(x,y,z) in Z^3: x+y+z is even}. Its nearest-neighbour
displacements are the 12 permutations of (±1,±1,0), with independent signs.
Use the bounded graphs G_R=V intersect [-R,R]^3 for R=1 and R=2, containing
13 and 63 nodes respectively. Boundary nodes have fewer than 12 neighbours;
absent ports are absent edges, with no wraparound.

Set E=((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)). A Quadray tuple q maps to
D(q)/2, where D(q)=sum(q_i E_i). Require four actual integers and sum(q_i)
divisible by four. Even total alone is insufficient: q=(1,1,0,0) maps to
(1,0,0), outside V. Common offsets preserve displacement. Port (i,j) has
displacement (E_i-E_j)/2 and reverse port (j,i); order ports lexicographically.
All conversion and state arithmetic uses exact, arbitrary-precision integers.

| Label | Proposed check | Independent acceptance reference |
|---|---|---|
| SGN-A1 | Construct both bounded FCC graphs | Literal Cartesian nodes and squared-distance-two adjacency |
| SGN-A2 | Map all 12 ordered basis pairs to ports | Literal displacement fixtures; inverse and reverse-port checks |
| SGN-A3 | Apply all 24 tetrahedral basis permutations | Node/edge bijection, fixed port permutation, all 576 compositions |
| SGN-A4 | Route using local destination displacement | Independent BFS for every ordered pair, including self-delivery |
| SGN-A5 | Propagate wavefronts and exact local additions synchronously | Independent component traversal, sums, service checkpoints and conservation |

The local router selects the first available port that strictly reduces
h=max(|dx|,|dy|,|dz|,(|dx|+|dy|+|dz|)/2). It cannot consult BFS tables;
absence of an improving port is ROUTE_STALL. Shortest-path agreement is tested
on the declared graphs, with no universal topology claim.
Check legal improving hops at boundaries in both profiles. Retain any local
minimum as a first counterexample and halt for review; do not change the routing
rule or acceptance expectations during execution.

Graph symmetry requires adjacency and port correspondence. A fixed routing
tie-break can break path equivariance; transformed traffic must still deliver
correctly, but identical transformed paths are not required.

Use the contract's proposed synchronous phases: preserve inbox prefixes,
order arrivals and injections, service one inbox item or one fanout task per
node per tick, then commit transmissions for arrival next tick. First wavefront
visits add the payload once and enqueue fanout; duplicates consume service
without adding again. Queues are unbounded and peak storage is reported.

Neighbour stencils need separately reviewed update equations, boundary rules
and literal expected results before inclusion in SGN-A5. They are not part
of the current wavefront/addition acceptance profile.

## Acceptance and falsification

Require all seven proposed gates: valid graph construction, 12/12 reversible
port mappings, symmetry-preserving permutations, deterministic delivery,
independent shortest-path agreement, identical repeated traces, and no loss
or duplication. All remain NOT RUN. Retain canonical traces and repeat under
PYTHONHASHSEED=0,1,17; repeatability alone does not establish correctness.

Require conservation at tick boundaries and exact application totals. Inject
invalid coordinate parity, missing/reversed ports, a removed edge, corrupted
destinations, duplicate delivery, hidden drops and a wrong accumulator. Each
negative control must produce a named checker failure and first counterexample.
Missing required observations mean UNVERIFIED. A simulation tick-limit result
is non-delivery; external wall-clock TIMEOUT is an infrastructure outcome.

## Later phases and comparison controls

| Phase | Labels | Reviewable scope before execution |
|---|---|---|
| B | SGN-B1/B2/B3 | 2D mesh, FCC, Sierpiński and hybrid definitions; contention and multiscale reductions |
| C | SGN-C1 | One exact Quadray workload through conventional SPU and SGN software backends |
| C | SGN-C2/C3 | Bounded arithmetic, standalone processing network RTL, then device-specific FPGA qualification |

These labels organize research; they are not ratified contracts. The existing
Phase A comparator is a 63-node 7×3×3 nearest-axis mesh. The proposed Phase B
2D mesh is a separate comparator requiring its own frozen graph and mapping.
Freeze traffic, endpoint mapping, service/link capacities and workload semantics.
Report degree, edge count, diameter, hops, latency ticks, queue peaks, link
utilization, service operations, host runtime and preprocessing cost.

Separate equal node/link-budget comparisons from equal estimated wiring-budget
comparisons. Define physical layout and the wire-cost model before claiming
wiring benefits; hops and squared geometric distances are not physical wire
length or power measurements. Phase A unbounded queues establish no finite-buffer
deadlock or backpressure guarantee. No superiority threshold is imposed.

## Review handoff and evidence boundary

Before implementation, review and ratify scheduling and fixture identities,
freeze isolated source scope, oracle/checker commands and short preflight, then
authorize a bounded campaign with attempt count and wall-clock budgets.
Standalone RTL, synthesis, routing, board observation and CPU integration each
need their own gates. Preserve existing PSS-1/PSS-1R evidence and CPU routing HOLD.

Use this note for an initial technical discussion with PARC: seek critique of
the correspondence tests, synchronous scheduling and comparison controls.
SGN-1 has bounded FCC scheduler qualification with repository/software gates
passed. Mesh/cost comparison, synthesis, interface and silicon results remain
unavailable. Existing
Pell, AOR-1 and Artix-7 artifacts are background with their own evidence limits,
not SGN validation. Cite any hardware observation through the
[hardware evidence ledger](hardware_evidence.md).

Owner review froze this documentation milestone on 2026-10-13, then authorized
the isolated software-oracle increments and scheduler implementation linked above.
Full qualification remains subject to the Phase A review handoff and the agreed
serialized regression order. Repository-wide documentation audit
findings are recorded separately in
`build/sgn1/documentation_milestone_20261013/`; they do not establish a clean
repository-wide result. Physical SPU-13 implementation remains the next priority.
