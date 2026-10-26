# SGN-1 Phase A mesh/cost comparison: preparation

Date: 2026-10-13. Status: DRAFT; no implementation or campaign launched.
Entry gate: scheduler qualification job must have exactly one COMPLETE marker
and exit 0. Preserve artifact PASS separately until that terminal result exists.

## Review commands

```bash
python3 -m json.tool build/sgn1/scheduler_20261013/qualification_01/artifacts/result.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_sgn1_mesh_cost_preparation_2026-10-13.md
```

These inspect the artifact and documentation only; the first command does not
establish campaign success. Freeze source scope, serialization, negative controls,
runnable commands and a bounded execution budget before comparison qualification.
No additional campaign may launch while the scheduler job remains pending.

## Matched workloads and topology boundary

Use the original fixture plan's 63-node FCC_R2 and 7×3×3 nearest-axis mesh,
with its exact endpoint-ID mapping. Freeze all-pair, many-to-one, crossing,
burst and wavefront injections, integer payloads, ticks, ordinals and outcomes.
Keep the scheduler's one-service allowance, alternating inbox/fanout preference,
next-tick arrival, one-packet directed-link capacity and unbounded queues identical.
Mesh ports are lexicographic Cartesian displacements; reverse negates displacement.
Use local Manhattan-improving mesh routing and independent BFS, without global
tables in either tested router. Define an independent mesh adjacency oracle.

No 2D mesh or hierarchy is included. Report actual edge counts, degree distribution,
diameter, endpoint coordinates and mapping. This compares equal nodes and equal
per-node/per-link capacity; it is not an equal total-link or equal wire-budget test.
The additional links in FCC must remain visible in every comparative summary.
No superiority threshold is an acceptance gate; a mesh win is a valid result.

## Required communication and service measurements

| Quantity | Proposed definition to freeze before execution |
|---|---|
| Link messages | Every committed transmission counts once; report host injections separately |
| Updates | Delivered unicasts plus wavefront first visits; duplicate suppressions are not updates |
| Messages/update | Link messages divided by updates, retained as numerator/denominator |
| Delivery latency | Destination service tick minus injection tick plus one; self-delivery is one tick |
| Wavefront latency | Last first-visit tick minus root-injection tick plus one |
| Drain makespan | Last serviced/committed tick plus one, including duplicate suppression |
| Contention | Per-node inbox and pending-fanout occupancy, waiting-item ticks and service-class counts |
| Link use | Per-directed-link transmissions and occupied ticks; no steady-state throughput extrapolation |
| Storage | Separate per-node/global queue peaks, pending tasks, seen entries and accumulator state |

Report communication span and application completion separately from draining
the duplicate traffic. Do not call path hops a workload's critical path without
defining its dependencies. Reuse deterministic canonical traces and conservation
checks; retain independent expected sums for both endpoint mappings.

## Bytes and storage model: proposed, not a physical interface

Before comparing bytes, freeze one common logical packet serialization for both
topologies. Proposed fields: kind 1 bit, source 6, sequence 32, signed payload 64,
destination 6, wavefront sender 6 and egress 4: 119 bits, padded to 15 bytes.
Reserve destination/sender 63 for absent values and egress 15 for absent ports.
Validate every encoded field; reject out-of-profile input instead of truncating.
This model covers the frozen finite fixtures, not every unbounded simulator value.

Count 15 modeled bytes per link message only if that serialization is adopted
and checked independently. Exclude debug paths, JSON keys and trace snapshots;
those are host instrumentation, not transmitted message fields. Record this as
modeled logical traffic, never measured FPGA wire traffic.

Propose live logical-state bits from encoded queued packets, packet-plus-port
fanout tasks, source/sequence seen entries, signed64 accumulators and service
preferences. Freeze range checks and counting rules before using that model.
Allocator overhead, pointers and Python process memory are separate host costs;
unbounded queues do not specify a synthesizable storage budget.

The integer-addition workload performs no algebraic normalization. Report that
operation count as zero in both models; do not extrapolate to AOR/Surd workloads.
Charge address/port selection, validation and preprocessing separately where
measured. A node-ID packet with topology-dependent coordinate lookup does not
establish the hardware cost of geometric addressing.

## Physical cost and closeout limits

Report edge count, maximum degree, adjacency entries and common packet width as
structural routing-cost proxies. Estimated wire length requires a separately
frozen placement/layout and wire-cost model. Device routing congestion, timing,
energy, FPGA resources and physical wire length remain unmeasured here.

Preserve the scheduler qualification evidence and existing Surd CPU priority.
After comparison acceptance, audit every original Phase A requirement before
closeout; these proposed measurements alone do not close Phase A or authorize RTL.
