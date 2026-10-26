# SGN-1 Phase A: exact geometric communication computer

Status: DOMAIN RATIFIED / HOLD FOR SCHEDULING AND EXECUTION REVIEW.
Contract ID: `contract_sgn1_phase_a_2026-10-12.md`.
Roles: spec author drafts; implementer checks edge cases; auditor validates independent evidence.

## Review commands (authorized preparation only)

```bash
python3 -m json.tool spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json
git diff --check -- spu_strategy/contract_sgn1_phase_a_2026-10-12.md spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json
```

No simulator implementation or experiment launch is authorized by this draft.
Freeze runnable implementation/experiment commands in a subsequent reviewed packet.

## Scope

Implement later in an isolated software project, independent of production SPU modules.
Phase A covers FCC graph construction, Quadray port mapping, tetrahedral symmetries,
local unicast routing, exact node-state updates, wavefront propagation and contention.
Use arbitrary-precision integer arithmetic; no finite-width or hardware parity claim.
Exclude Sierpinski hierarchy, Surd/REGEN/AOR changes, CPU integration, RTL and boards.

## Mandatory domain correction

Let E=((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)) and D(q)=sum(q_i E_i).
Physical nodes satisfy integer x,y,z and even x+y+z.
For integer q, D(q)/2 belongs to this FCC lattice iff sum(q_i) is divisible by four.
Counterexample to an even-total condition: q=(1,1,0,0) gives (1,0,0).
Even individual coefficients are also insufficient: q=(2,0,0,0) gives (1,1,1).
Require four actual integers (reject bool and malformed tuples) and sum(q_i) mod 4=0.
Common-offset equivalence q~q+(c,c,c,c) preserves displacement and the domain.
Optional nonnegative canonicalization subtracts min(q); it is not a new ISA encoding.
Inverse lift of an FCC node is q=(x+y+z,x-y-z,-x+y-z,-x-y+z)/2.
All components are integers, sum(q)=0, and D(q)/2=(x,y,z).
The corrected domain is ratified; do not silently round invalid images.
Validate container type, then length four, then actual-integer coefficients, then parity.
Only built-in list/tuple containers and exact integer coefficients are supported; bool,
float, string and null coefficients are malformed, even when numerically coercible.
The fixture plan specifies literal inputs and the first applicable rejection reason.

## Graph and port semantics

Use G_R={v in [-R,R]^3: sum(v) even}; radii 1 and 2 are initial profiles.
Ports are the 12 ordered pairs (i,j), i!=j, ordered lexicographically.
Port displacement is (E_i-E_j)/2; reverse port is (j,i).
Missing boundary neighbours are absent ports, never wraparound connections.
Oracle graph uses literal integer nodes and squared-distance-two adjacency,
not implementation neighbour-generation or Quadray conversion functions.
Graph radius 1 has 13 nodes; radius 2 has 63 nodes.
The radius-1 graph is a future small RTL candidate, not a demonstrated FPGA fit.

## Symmetry contract

For every permutation sigma of four basis indices, define q'_sigma(i)=q_i.
Map port (i,j) to (sigma(i),sigma(j)); induce node action through the inverse lift.
Test all 24 permutations on every node and edge, including boundaries.
Require bijection, adjacency preservation, inverse composition and fixed port permutation.
Test all 24x24 compositions; do not infer this from repeated identity checks.
Graph symmetry does not imply route-choice symmetry: a fixed tie-break breaks equivariance.
Require deterministic delivery after transformation, not identical transformed paths.

## Local routing and independent reference

A router receives only current position, exact destination displacement and available ports.
It must not consult BFS tables or a global shortest-path map.
For delta=(dx,dy,dz), define h=max(abs(dx),abs(dy),abs(dz),sum(abs(delta))/2).
The final division is exact for FCC displacements; implementation may use integer shift.
Choose the first available port whose displacement strictly reduces h.
An absent improving port is ROUTE_STALL; never silently fall back to global search.
Verify all ordered source/target pairs, including self-delivery, for each frozen graph.
Compare legal paths, destination and hop count with independent BFS.
Shortest-path agreement is scoped to these graphs; no universal topology theorem is claimed.

## Processing and synchronous execution

Each node starts with accumulator zero, empty inbox, empty pending-fanout FIFO,
empty wavefront seen set and next-service preference INBOX. Node IDs are lexicographic
Cartesian positions. All ticks begin at zero; host injections are visible in that tick.

Apply these phases in order at every tick:

1. Preserve the entire existing inbox prefix. Append prior-link arrivals sorted by
   receiver ingress-port index, then packet key. Append host injections after those
   arrivals, sorted by globally unique nonnegative injection ordinal.
2. Choose at most one service per node. If inbox and pending fanout are both nonempty,
   use next-service preference. If only one is nonempty, service that class.
   After service, prefer the opposite class next; an idle tick leaves preference intact.
3. An inbox unicast either delivers locally and adds its payload once, or forwards
   through the first improving port. Each action consumes the full service allowance.
   Self-delivery also consumes one service. Transit never updates application state.
4. A first-visit wavefront inbox item immediately marks its ID seen, adds payload once,
   and appends one fanout task per available outgoing port in lexicographic order.
   Include the ingress/reverse port. Preserve older fanout tasks ahead of new ones.
   This consumes the whole service tick: the first transmission cannot share it.
5. A seen wavefront inbox item is suppressed without application update or fanout.
   Suppression consumes the full inbox service allowance and changes the preference.
   Seen is updated on service, never admission; queued copies are not pre-suppressed.
6. A fanout service pops one oldest task and sends one copy on its recorded port.
   Fanout and inbox service share the same allowance; no node sends two packets.
7. Commit all transmissions after all nodes have serviced. They arrive at tick t+1.
   Node iteration order must not affect admission, service or application outcomes.

Unicast IDs are (source-node ID, source sequence), unique within each trace.
Wavefront IDs are (origin-node ID, broadcast sequence), also unique within each trace.
Use integer packet keys (kind, origin, sequence, sender, egress-port index):
unicast (0,source,sequence,0,0); injected wavefront (1,origin,sequence,-1,-1);
transmitted wavefront (1,origin,sequence,sender,egress-index).
Reverse egress pair to obtain receiver ingress index. This gives a total admission order.
Mesh ports use lexicographic Cartesian displacement order and reverse displacement.

Each directed link carries at most one packet per tick; queues are unbounded.
Record peak inbox and pending-fanout storage, seen-set size and admission sorting cost.
No finite-buffer deadlock, flow-control or backpressure claim is implied.
At post-commit tick boundaries, injected unicasts equal delivered plus inbox plus
in-flight unicasts. Check unique delivery separately.
For wavefront physical copies, require injected roots plus created fanout tasks equal
inbox copies plus pending fanout plus in-flight copies plus first-visit consumptions
plus duplicate suppressions. Sending moves a task to in-flight; it creates no new copy.
Stop after all injections are admitted and inboxes, fanout and links are empty.
A simulation tick limit is a non-delivery result, distinct from wall-clock TIMEOUT.

## Wavefront and contention fixtures

The fixture plan records literal admission-order and wavefront-service checkpoints.
First-visit application and first transmission occupy separate ticks; pending fanout
and ordinary inbox items alternate when both remain nonempty. A duplicate consumes
service even if another fanout task is waiting. Check queue prefixes as well as sums.
Independent component traversal supplies reached nodes and local sums.
Wavefront arrival ticks need not equal BFS levels under serialized fanout.
Freeze many-to-one, crossing and burst injections by endpoint ID, tick and payload.
All-pair cases use fresh state per ordered pair, including self-delivery.
Expected accumulators are preparation labels, not evidence of simulator execution.
Record inbox admission, selected service, preference, fanout, seen, application update,
send, delivery and suppression events in canonical node-ID/event-order traces.
Compare repeated runs with PYTHONHASHSEED=0,1,17; never rely on set iteration order.

## Baselines and cost boundary

BFS is the correctness oracle, not a matched hardware-performance comparator.
Compare 63-node FCC with a 7x3x3 nearest-axis mesh using one-item router service,
one-packet directed-link capacity and the same endpoint-ID traffic and injection ticks.
The fixture plan freezes endpoint-ID mapping by lexicographic coordinate order in each
graph. Report differing degree, edge count, diameter and layout.
Equal node/link capacity does not mean equal interconnect budget; report all extra links.
Report hops, latency ticks, queue peak, service operations, preprocessing and host runtime.
Do not equate hop count or squared geometric lengths with physical wire length or power.
No performance-superiority acceptance threshold is imposed on this feasibility experiment.

## Negative controls and acceptance

Reject invalid Quadray parity, missing/reversed ports, a removed legal edge,
corrupted destination, duplicate delivery, hidden drop and a deliberately wrong accumulator.
Every injected fault must have a named checker reason and retained first counterexample.
Missing required observations yield UNVERIFIED, never partial PASS.
Unsupported domains are separate from implementation mismatches.
Positive acceptance requires topology, 12-port bijection, symmetries, all-pair routing,
wavefront outcomes, contention conservation and trace repeatability in declared profiles.

## Promotion and budget gates

Next: ratify proposed tick semantics and prepared traffic labels, authorize isolated implementation,
freeze fixtures/oracle identities and short preflight, then approve a bounded experiment.
No attempt count, runtime or cumulative execution budget is authorized by this draft.
Standalone RTL follows software acceptance under its own bounded-arithmetic contract.
FPGA synthesis/routing/board evidence requires separate authorization and legal timing.
CPU integration and custom physical-fabric/ASIC exploration remain separate future work.
Preserve PSS-1/PSS-1R evidence and the Artix-7 CPU routing HOLD.
