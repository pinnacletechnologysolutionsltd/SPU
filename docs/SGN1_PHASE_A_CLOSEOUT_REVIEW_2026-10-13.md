# SGN-1 Phase A closeout review

Date: 2026-10-13. Status: REVIEW PREPARED; owner closeout decision pending.
Qualified software evidence supports all seven positive gates in the declared
Phase A profile. No Phase B campaign is authorized or launched by this review.

The later [owner decision record](SGN1_PHASE_A_OWNER_DECISION_RECORD_2026-10-13.md)
distinguishes original acceptance evidence from supplemental diagnostics and
records the owner's explicit Phase B deferral until the Surd CPU implementation
path passes carry-cluster legality, integrated routing and routed 25 MHz review.

## Evidence review commands

```bash
python3 -m json.tool build/sgn1/phase_a_closeout_20261013/review_01/review_result.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/SGN1_PHASE_A_CLOSEOUT_REVIEW_2026-10-13.md docs/README.md
```

The preserved review scripts perform bounded evidence inspection and checker
mutations on retained traces. They do not run positive scheduler cases or
launch another campaign. `review.py` refuses to overwrite its result; inspect
the existing record rather than rerunning that exact output path.

## Frozen identity and durable qualification

| Evidence | Identity / terminal result |
|---|---|
| Parent Phase A contract | SHA256 `ebdf883e6afa9d53ac3eaf29272a86eec6f1a15e4c9f84b4592925260a29bf96` |
| Fixture plan | SHA256 `289c2860aca4ea4607151e181da3995b2adda2e7e88b5816104bd9cde97bac8b` |
| Qualified FCC source manifest | SHA256 `2ffbb5a8db811b2c804285a151c6c9158adfd631b701b950381be46113bbdce5` |
| Mesh preparation manifest | SHA256 `0f2affef74148e0308571d533c823f38aad2337fbebed5478d5f0a064cb3aa1b` |
| Geometry/symmetry/routing regressions | Each has sole COMPLETE marker, exit 0 |
| FCC scheduler qualification | Sole COMPLETE, exit 0; 1,142 seconds; 24,888 executions |
| Mesh/cost qualification | Sole COMPLETE, exit 0; attempt 1; 1,500 seconds; 23,838 mesh executions plus 23,838 FCC trace rechecks |

The [source and evidence review record](../build/sgn1/phase_a_closeout_20261013/review_01/review_result.json)
checks all prepared source/document hashes and every FCC snapshot file against
their manifests. Original source and evidence remain unchanged.
The [owner authorization](../build/sgn1/mesh_cost_20261013/authorization_01/authorization.json)
superseded the preparation HOLD and one-attempt proposal: maximum three
3,000-second attempts, 9,000 seconds cumulative, scoped repairs permitted.
One slot was used successfully. No repair, second attempt or third attempt
was needed; remaining slots are not an instruction to repeat a passing campaign.

## Seven acceptance gates

| Gate | Supporting evidence | Scope |
|---|---|---|
| Valid FCC graph construction | Geometry focused tests and COMPLETE regression | R1:13 nodes/36 links; R2:63 nodes/240 links |
| 12 reversible direction/port mappings | Literal directions, inverse lift and reverse checks | Corrected integer Quadray domain; boundary ports absent |
| Symmetry-preserving permutations | Symmetry focused report and COMPLETE regression | All 24 basis permutations, 576 compositions, both graphs |
| Deterministic packet delivery | Qualified full-tick FCC checker and mesh checker | Fresh states, all pairs and declared concurrent fixtures |
| Independent shortest-path agreement | Routing focused report, BFS and mesh preflight | FCC4,138 ordered pairs; mesh3,969; includes self-delivery and boundaries |
| Identical repeated traces | Six FCC hashes and six mesh/cost hashes | Forward/reverse node orders; seeds0,1,17 |
| No unexplained loss/duplication | Per-identity conservation, exact sums and negative controls | Tick boundaries, unique unicast delivery and defined wavefront suppression |

These are tested finite-profile properties, not proofs for arbitrary graphs,
faults, schedules, queue capacities or sizes. Full pair coverage includes
transformed endpoint labels, but lexicographic route tie-breaking is not
claimed to be path-equivariant under tetrahedral transformations.

SGN-A5 covers exact additions and wavefront propagation with independent
component traversal and service checkpoints. Neighbour stencils were explicitly
excluded pending reviewed equations and boundary rules; they are not completed
by this result. The unified AOR/SGN gates remain separate and NOT RUN.

## Reproducibility and control diagnostics

| Canonical decompressed stream | SHA256, equal across all six runs |
|---|---|
| Full retained FCC trace | `c7f965b888ec647198beb4fa7ec7c7885311ab8a2f5d43f1191b4d9aebc128c6` |
| Mesh trace | `f42c61f7e0182e6c6a578d1d00b088e070d6e490b2b1f7a72e5b71e01ae73119` |
| Paired logical costs | `294a50ee2440bb00b7cf45586f6729dbe016c29d37ab6c6bf2b2d6f09d647236` |

The closeout audit independently recomputes all six mesh trace hashes and
all six cost hashes from gzip contents. The qualification itself binds each
full FCC stream and independently rechecks the selected records. Each run
contains 3,969 pairs plus four fixtures: 3,973×2×3=23,838 comparisons.
Identical cross-topology traces are neither required nor expected.

FCC qualification retains sixteen named negative-control types and their
first counterexamples under every seed. Geometry, symmetry and routing have
their own domain/fault rejection evidence. Mesh preflight ran seven tests under
each seed, including eleven checker mutations, wire bounds and storage controls.
Its campaign log retained test success but no per-mutation diagnostics.

The supplemental closeout record fills that diagnostic gap by mutating retained
unicast and wavefront traces and requiring the exact expected checker reason
for each of the eleven controls. It stores each first counterexample and trace
identity. These are post-qualification diagnostics, not retroactively claimed
original campaign logs. No simulator executes in this supplement; the checker
is the unchanged qualified source. This review is not a separate human or
independent implementation of that checker.

## Measurements and interpretation

| Workload | FCC messages | Mesh messages | FCC drain ticks | Mesh drain ticks |
|---|---:|---:|---:|---:|
| Many-to-one | 120 | 192 | 63 | 63 |
| Crossing | 240 | 384 | 27 | 20 |
| Burst | 292 | 288 | 14 | 16 |
| Wavefront | 480 | 276 | 46 | 37 |

Across all isolated pairs, FCC sends10,848 messages and mesh16,128. Wavefront
duplicate suppressions are418/214. Those counts also follow independently
from directed adjacency and reached-node coverage under the all-port protocol.
Fewer point-to-point hops do not determine concurrent drain time: report the
observed scheduler outcome without attributing a causal breakdown that was
not separately measured. Endpoint-ID mapping and injection schedules stay fixed.

FCC has240 undirected links versus138 for mesh, maximum degree12/6 and
diameter6/10. This is equal nodes/per-node service/per-link capacity; total
link resources and estimated wiring budgets are not matched.

The packet model has119 meaningful bits and120 serialized bits: fifteen bytes
with zero padding. Bounds and absent-field codes are validated before costs
are accepted. Every reviewed message costs fifteen modeled bytes. This is
logical serialization, not FPGA traffic or a realizable hardware interface.

Storage counts65 bits per node plus120 per inbox packet,124 per pending task
and38 per seen entry, with signed64 accumulator checks. Simultaneous global
node-state peaks, individual node peaks and in-flight peaks are separate.
Allocator, queue pointer and capacity-counter overhead is excluded. Debug
paths/JSON are excluded. Normalization count is zero for integer additions.
Historical FCC versus newly executed mesh host speed is not compared.

## Closeout recommendation and exclusions

Recommend owner/independent review acceptance of Phase A for this bounded
software profile, subject to accepting the explicit supplemental diagnostics.
Keep the [frozen specification](SGN1_RESEARCH_SPECIFICATION.md), contracts and
preparation manifests intact; this note supplies the later status instead of
rewriting hash-bound historical HOLD/NOT RUN statements.

Qualified: exact geometry, port/symmetry correspondence, bounded routing,
deterministic scheduling, conservation and workload-dependent logical costs.
Unqualified: physical wiring, area, congestion, power, frequency, finite
hardware buffers, FPGA network implementation, AOR transport or CPU integration.
Unbounded queues prove neither deadlock freedom nor backpressure behavior.

Phase B remains proposed. Freeze new topology/workload/layout definitions,
equal-resource comparison rules, technology assumptions, independent cost
models and its own authorization before execution. A cost model is not a
physical measurement. Surd CPU backend qualification retains first priority.
Existing unrelated documentation-audit findings remain separately recorded;
no clean repository-wide documentation result is claimed.
