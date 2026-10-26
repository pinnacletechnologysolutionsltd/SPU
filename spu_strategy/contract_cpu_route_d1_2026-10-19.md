# CPU ROUTE-D1: bounded router observability

Date: 2026-10-19. Status: **CORRECTED DRAFT; implementation authorization pending**.

Spec author: Codex. Implementer and auditor: unassigned; distinct functional
reviews are required, not additional agents. No native source is changed by
this packet. No new CPU campaign is authorized. D1-R1 through D1-R5 are addressed in this
corrected preparation packet; the original draft and controlling review remain
byte-for-byte preserved in `cpu_route_d1_20261019/original_pre_corrections/`.

## 1. Freeze and inspect before implementation

```bash
python3 spu_strategy/cpu_route_d1_20261019/check_packet.py
git diff --check -- spu_strategy/contract_cpu_route_d1_2026-10-19.md spu_strategy/cpu_route_d1_20261019
```

Use `cpu_route_d1_20261019/source_manifest.json` as the source identity pin.
Use the retained `forward_search_analysis_20261019/REVIEW.md` and
`analysis.json` as controlling evidence, not an inferred performance baseline.
The old campaign ended with three TIMEOUT markers and exactly 10,800 seconds.
Standalone arithmetic evidence stands; integrated CPU routing is unresolved;
25 MHz is unqualified. The design has not been proved unable to fit.

The observations contain 338/328/279 distinct active names, each seen once per
attempt, with three names recurring across attempts. Slot totals cannot rank
calls. The dispersed 132-input-port recurring net is a hypothesis candidate,
not an established bottleneck. No second completed iteration or wire-ownership
trace exists. Do not optimize a search policy on this evidence.

## 2. Proposed exact source edit surface

Copy only the pinned candidate source into a new `build/` preparation directory
after implementation authorization. Do not edit retained inputs, installed
OSS CAD Suite/openXC7 binaries, RTL, databases, placement, constraints, or
campaign scripts. Keep the legacy progress instrumentation unchanged. Add
ROUTE-D1 under `SPU_ROUTE_D1`; a build without that define must retain the
baseline source behavior. A defined build with no D1 output path must perform
no D1 allocations, clock reads, output, or RNG calls.

All paths below are relative to that future source copy. Implement helpers as
single-purpose files, each 50–150 lines; split any helper exceeding 150 lines.
Do not implement a general telemetry framework.

| File | Exact proposed edit / call site |
| --- | --- |
| `common/router2.cc` | Include `spu_route_d1.h`; add a private D1 recorder to `Router2`. No changes to `WireScore`, `QueuedWire::Greater`, RNG, neighbor iteration, scores, visitation, limits, routing queues, bounding boxes, ownership, or delay computations. |
| `common/router2.cc::setup_nets` | After driver/sink resolution and before workers start, build immutable identity tables in sorted net order. Store the native user-index mapping explicitly. Wire names are dictionary references, never reconstructed from JSON port order. |
| `common/router2.cc::route_arc` | Create exactly one call scope at function entry; tag each existing return in it carrying the original `is_mt` and `is_bb` arguments, net/user identity and iteration. Record the *existing* result at each original return without evaluating it twice. Destructor emits END only for normal return; unwinding produces ABORT with exception status. |
| `common/router2.cc::route_xilinx_const` | Create a separate constant-search call type for each sink search, using the actual sink identity; never silently include it in ordinary arc totals. Parent constant-net invocation gets a separate span, not duplicate pop accounting. |
| `common/router2.cc` backward queues | Count a pop exactly where the existing `front()` is removed in each of the two backward-search loops. Sample peak immediately after every push, including initial push. Count every return path, empty queue, and bounded-search exit. |
| `common/router2.cc` forward queue | Count each existing `pop()` once. Update peak after initial and neighbor pushes. Trace only values already computed, at POP, enqueue/first-discovery, visited rejection and final result; never call a scoring function or RNG again for logging. |
| `common/router2.cc::update_congestion` | After worker join, capture occupancy in the existing wire scan alongside the existing totals. Record old/new historical cost around its existing update; do not perform another update. Do not traverse `bound_nets` concurrently with worker mutations. |
| `common/router2.cc::operator()` iteration body | After `update_congestion`, statistics, optional `bind_and_check_all`, and construction of `failed_nets`/next queue, commit ITERATION_END and its ownership snapshot. Test diagnostic-stop requests only at the safe boundaries below. Route-complete processing takes priority if its existing conditions are satisfied. |
| `common/router2.cc` test-only probes | Under `SPU_ROUTE_D1_FIXTURE` only, expose the existing score/comparator methods to the small native fixture context; record their returned bits. Add identical bounded decision/RNG capture to baseline and candidate fixture builds. No probe or capture in CPU builds. |
| `common/spu_route_d1.h` | Immutable configuration, disabled guard, typed result enums and scope interfaces only. |
| `common/spu_route_d1_identity.h` | Collision-free string dictionary, explicit net/driver/sink identity mapping and escaping. |
| `common/spu_route_d1_call.h` | Local counters, monotonic timestamps, BEGIN/END/ABORT and nested-span accounting. |
| `common/spu_route_d1_live.h` | Fixed active-call slots, atomic heartbeat publication and bounded unfinished-call snapshots. |
| `common/spu_route_d1_trace.h` | Fixed selected-call buffers and trace-cap accounting. |
| `common/spu_route_d1_writer.h` | Bounded record serialization, preallocated buffers, checked writes and rolling file digests. |
| `common/spu_route_d1_congestion.h` | Quiescent occupancy/ownership snapshots and coordinate histograms. |
| `common/spu_route_d1_limits.h` | Byte/memory/time accounting and diagnostic-stop reasons. |

Do not add an algorithm repair. If an anchor or signature differs from the pin,
HALT with a minimal correction proposal. Do not silently transplant to another
backend revision.

## 3. Observation and accounting contract

Use the normative `cpu_route_d1_20261019/SCHEMA.md` V1 framing, fields and
checkpoint semantics. Use `allocation.json` for simultaneous capacities and
pre-admission export reservations. Use `binary_schema.json` as the exact V1 packed little-endian wire layout:
256-byte frames, 32-byte header, 224-byte payload, explicit field offsets and
zero padding, CRC-32/ISO-HDLC on payload and header, sequential frame IDs and
SHA-256 chained COMMIT records. Reject unknown versions/types/enums, nonzero
reserved bytes, invalid sizes, gaps, reordering and corrupt commits.
`binary_golden.json` freezes one layout vector for all fourteen record types
and a committed accounting stream. `schema_codec.py` and `check_binary.py`
validate reference framing/accounting and corruption controls only; native
implementation qualification remains NOT RUN. DICT entries are bounded UTF8
chunks with full string identity. JSON export is exactly one lowercase hex
string per complete frame per line: 515 bytes, hence 771 bytes for native plus
reserved export. Typed decoded views stream without creating extra disk files.
Every frame reserves its complete export cost before admission; metadata and
non-frame artifacts are also charged. This encoding preserves full-width bits.
Reject unknown versions. Include build/source/config/database/placed-input SHA-256,
seed, target clock, platform, thread count and monotonic-clock identity.
IDs are dictionary indexes backed by full strings, not truncated hashes.
Counter overflow, unresolved identity, duplicate END or malformed output fails
diagnostic qualification.

**Call key:** `(run_id, worker_id, worker_sequence)` with monotonically
increasing worker sequence. Stable comparison key: full net name, driver cell,
driver port, source wire name, sink cell, sink port, sink wire name, search kind,
iteration, ordinal for this endpoint in that iteration, and routing mode
`bounded_mt`, `bounded_serial`, `unbounded_serial`, or `constant_backward`.
Undriven/absent endpoints are explicit null plus reason. Parent spans and actual
search calls are different record types. Parallel order is not assumed stable.

BEGIN precedes work and contains identity, net/arc bounding boxes and context.
END contains elapsed steady-clock nanoseconds, exclusive pop counts, exact
forward/backward queue peaks, result and exit reason, attempted/skipped sink
status, start/end times, trace coverage and counter publication sequence.
Preserve `ARC_SUCCESS`, `ARC_RETRY_WITHOUT_BB`, `ARC_FATAL` distinctly. A bounded
failure followed by an unbounded retry creates two linked calls. Constant calls
have their own result vocabulary. Parent elapsed time includes child time;
parent pop totals do not duplicate child counters.

Rank completed search calls by elapsed time and separately by forward/backward
pops; group by full stable endpoint and net. Report all completed calls, total
and max time, counts, mode/result distributions and iteration. Do not infer
per-net work from legacy slots. Report elapsed as wall time, not CPU time;
overlapping call wall times may exceed process wall time.

Preallocate nine worker identities maximum including the serial role, each with
four nesting slots (36 total); reject a larger configuration before routing.
Reserve terminal record storage and output allowance before admitting BEGIN.
Use local counters and all-atomic coherent sequence publication; a reader gets
three retries then emits SNAPSHOT_UNAVAILABLE, never mixed fields.

`durability.json` controls live/write/fsync semantics. Per-call
published_sequence is a heartbeat ordinal; written_sequence is the ordinal
whose snapshot completed write(2); fsync_confirmed_sequence is the ordinal
covered by a COMMIT for which fsync returned success. These are separate from
global frame/COMMIT sequences. Enforce fsync-confirmed <= written <= published.
Userspace flush or a readable valid CRC does not establish fsync durability.

Read steady clock at entry, exit and every 256 aggregate pops. Publish both
counters after either direction accumulates 4096 unpublished pops, or at the
first clock check seeing >=100 ms since publication. The 4095 residual bound
applies at completed pop-hook boundaries, not an interrupted publication or
an older durable checkpoint. Record observed age; slow pops, blocking and
scheduling prevent a hard 100 ms freshness guarantee.

Every 250 ms the writer emits explicit UNFINISHED snapshots, writes a chained
COMMIT, fsyncs the event file and only then publishes acknowledgment. A later
ACK describes that earlier confirmed COMMIT, never itself. Fsync directory
creation before claiming durable file identity. Charge all writes/fsync/stalls
to budgets. Recover written-consistent and fsync-confirmed prefixes separately.

An unmatched BEGIN after termination becomes UNFINISHED_TERMINATED. Preserve
its last confirmed lower bound, or label written-only/NO_DURABLE_COUNTERS.
Extra work is unknown/unbounded (UINT64_MAX), unless another retained checkpoint
bounds it; never apply the 4095 residual bound to the last disk record. Lost
BEGINs or partial/uncommitted tails also imply an unknown count of calls, not
just a known unfinished list. No synthesized END or route success. Add a
killed-helper case with three publications after the last fsync-confirmed commit.

## 4. Congestion and selected state traces

WIRE/OWNER records encode the full occupied set; derive and verify coordinate
histograms from them. AGGREGATE.status marks failed-net identities separately
from cost ranking. Each finished iteration records total distinct occupied wires, total owner-wire
incidences (the existing `total_wire_use`), overused wire count and summed
`max(owner_count-1,0)`, failed net identities, current/historical congestion
weights, per-coordinate occupancy histogram and full overused-wire list.
For every occupied wire emit native wire identity, notional `(x,y)` from
`PerWireData`, coordinate-definition tag, owner net identities, owner arc-use
counts, driving pip identity, reservation/unavailable flags and historical
cost. Distinct owners determine occupancy, not arc-use count. Notional wire
coordinates are not BEL coordinates or a claim about physical wire extent.
Commit snapshot only after all records, totals and checksum reconcile. A partial
snapshot is explicitly incomplete; never count it as a finished congestion
iteration. Compare exact owned-resource sets and owner identities as well as
totals; equal totals alone do not establish equivalent congestion states.

Select at most eight calls from a frozen allowlist of exact endpoint keys,
optionally matching any sink of a named net, then choose lowest native user
index before workers start. Pin selected iteration/ordinal/mode. No adaptive
selection based on runtime, scheduling or RNG. Include the three recurring net
names from the analysis in the *candidate* selector input; resolve endpoints
from native setup, not JSON ordering. Fail if a required selector is unresolved.

**Search-state definition:** `(call key, direction, wire identity, incoming pip,
cost float32 bits, togo float32 bits, delay native bits, randtag, visited bit,
predecessor pip, bounding-mode/box, congestion-epoch)`. Queue occurrence has a
separate local event ordinal. Resource-equivalence projection is
`(stable endpoint, mode, box, epoch, direction, wire)`; repeated resource visits
are not automatically equivalent scored states. Full recorded-state equality requires
all listed fields, including context; it does not establish equality of untraced
concurrent ownership changes. Never describe a matching projection as a full
global-router-state recurrence. Across epochs compare only labelled projections.

Record POP, PUSH, VISITED_REJECT and RESULT for selected calls with these fields
where valid; unavailable fields are tagged, not zero-filled. Track per-call
push/pop/reject counts and forward/backward unique-wire and repeated-wire
counts for selected calls using fixed-cap maps. Track duplicate full states
only within the retained prefix; if the map or trace cap is hit, mark coverage
`PREFIX_ONLY` with exact truncation event ordinal. Never claim unseen repeats
absent. Preserve real score bit patterns, tie tags and native pip enumeration.
No use of the exact-arithmetic RTL rule to change existing host float scoring.

## 5. Frozen resource limits and failure semantics

`limits.json`, `resources.json` and `acceptance.json` are normative together.
`resources.json` allocates exactly 64 MiB across identity16, trace16, state maps8,
writer8, scratch8, stack/TLS4, active/END2 and metadata2 MiB. No fallback malloc.
The 256 MiB diagnostic-output ceiling is global across the entire fixture job,
including native captures, routed graphs, FASM, logs, exports and metadata.
Build objects/binaries/source copies are reported implementation inputs, not
diagnostic output; build logs remain charged. Category ceilings stay
32/64/128/24/8 MiB. Native records reserve 771 bytes including export; external
artifact reservations are explicit in resources.json. Refuse oversized
identities or reservations before work; never silently drop or roll output.
Cap exhaustion is nonacceptance even when an existing graph remains legal.
Count ceilings do not promise storage capacity: two call frames alone allow
at most 43,520 calls under the 64 MiB call category before live/aggregate records.
A future 50,000-call trigger can therefore be preempted by a cap stop; neither
the cap nor trigger is changed without separate authorization.

| Resource | Ceiling / action |
| --- | --- |
| All D1 durable output including exported JSON | 256 MiB; reserve 4 MiB for terminal metadata; no rollover or overwrite |
| Identity dictionaries / call records / congestion / traces | 32 / 64 / 128 / 24 MiB respectively; remaining 8 MiB terminal/index allowance |
| Additional native diagnostic resident allocation | 64 MiB, including all buffers, tables, active slots and writer stack; enforce tracked allocations, cross-check peak RSS in fixtures |
| Completed calls | 100,000 globally; pre-reserve capacity for nine workers × four nested active calls; request stop before starting another when remaining capacity equals reservation |
| Selected trace | 8 calls × 8192 events, at most 256 bytes/event; fixed maps ≤4096 wire entries/call, included in 64 MiB |
| Congestion | At most 2 committed iterations, 2,000,000 occupied wires/iteration, 4,000,000 ownership incidences/iteration; actual byte cap wins |
| Writer | One thread; 250 ms flush; maximum 1 MiB record chunk; no unbounded backlog; full buffer requests diagnostic stop, never drops an END silently |
| D1 self-accounted native time | ≤10 s summed over the fixture job, ≤2 s per snapshot, ≤50 ms synchronous flush/stall; check at bounded chunks, request stop on excess |
| Fixture incremental overhead | For every seed/comparison: median paired relative increase ≤5% AND median paired absolute increase ≤100 ms; paired peak RSS median and maximum positive delta ≤64 MiB |
| Later CPU overhead acceptance | Report timed-hook totals over the entire completed diagnostic interval, ≤1% of its elapsed and ≤10 s; actual CPU slowdown remains UNMEASURED without a separately authorized paired baseline |

Self-time measures timed hook blocks, publication, snapshot and writer activity,
summed across threads. Inline scalar pop/peak updates cannot be isolated exactly
without timing every operation; their cost is covered by paired fixture overhead
measurements, not mislabelled as measured CPU self-time. Report this exclusion.
The whole completed diagnostic interval runs from enabled recorder initialization
through final diagnostic flush; it is not a startup-prefix test. Retain excursions.
Allocation tracking and paired peak RSS are separate acceptance gates. Every cap,
I/O or time breach is non-accepting, even if the trace is otherwise quiet.
Host scheduling and
filesystem stalls prevent a strict instantaneous wall-time guarantee. Measure
overruns and mark `BUDGET_BREACH`; never represent these ceilings as hard-real-
time guarantees. External frozen wall-clock deadline is the hard execution cap.
Queue peaks are exact, not sampled; constant-cost local updates only, with
batched clocks. If the overhead acceptance cannot be met, HALT and revise the
instrumentation contract; do not relax caps silently.

`acceptance.json` freezes the complete ledger: tracked allocation, measured
paired runtime and ru_maxrss deltas, global output/reservations, timed self-time
with exclusions, deadlines and correctness. Native processes are sequential.
Measure elapsed from immediately before spawn through wait using the same
wrapper/affinity for both arms; use fresh-child wait4 ru_maxrss converted from
Linux KiB to bytes. Keep all raw samples, exclusions and observed breaches.
No missing row, unexpected cap stop, IO error, required trace truncation or
incomplete native fixture execution can receive ACCEPT. Predeclared negative
helper tests pass only by verifying the expected child rejection under smaller
injected limits; this never waives a real shared job ceiling or excuses a
native equivalence/timing breach. Their actual resource use remains charged. Counters may mark optional selected trace
prefix coverage, but acceptance tests must exercise their required scope.

Resource exhaustion sets `DIAGNOSTIC_CAP` and returns a distinct non-success
diagnostic status at the next safe boundary, preserving existing choices up to
that boundary. Safe boundaries: between calls, after joined MT phase, or after
iteration completion. Never cancel a search mid-mutation. A long call can exceed
a requested stop; only the external deadline can kill it. This is diagnostic
lifecycle control, not a routing heuristic. An output error disables success
claims and requests `DIAGNOSTIC_IO_ERROR`; continue only until a safe stop.

Reserve one terminal slot per admitted in-flight call before BEGIN. If the
writer queue fills, retain END in that reserved slot, refuse new calls at the
next safe boundary and drain there. Never block indefinitely or overwrite an
unwritten terminal record. External termination still has the durable-tail
limitations in §3.

## 6. Prepared fixtures and future implementation commands

`fixtures.json` freezes accounting, corruption, native graph equivalence,
unfinished-call and congestion cases. It is a test specification, not a claim
that native fixtures passed. `weighted_graph.json` separately specifies the
small search-policy comparison. `check_packet.py` validates this preparation
packet only; it neither builds nor invokes the router.

Following implementation authorization, add the preparation scripts listed in
`commands.json` under `tools/cpu_route_d1/` and its explicit audit adapter.
They are proposed interfaces, not implemented or authorized executables.

`commands.json` is the frozen argument-vector manifest. It defines four builds:

| Build | CMAKE_CXX_FLAGS definitions (all explicit) |
| --- | --- |
| decision_baseline | SPU_CONSTANT_GUARD_PROBE, SPU_NATIVE_ROUTE_DIAGNOSTICS, SPU_ROUTE_D1_FIXTURE |
| decision_candidate | Same three plus SPU_ROUTE_D1 |
| timing_baseline | SPU_CONSTANT_GUARD_PROBE, SPU_NATIVE_ROUTE_DIAGNOSTICS |
| timing_candidate | Same two plus SPU_ROUTE_D1 |

Baseline and candidate decision capture must use identical test-only hooks,
existing RNG return values, ordered per-worker push/pop/result events and exact
score bits. No added RNG calls. Compare graphs and decisions to disabled,
no-trace and selected-trace candidate modes. Timing builds omit decision
capture and omit post-route graph/native/FASM serialization in both arms;
D1 observations remain included. Decision-build graph/audit acceptance is a
prerequisite for timing admission. The small-fixture selected endpoint is
frozen in runtime_config.json; failure to exercise it is nonacceptance. Only the no-define and candidate macro differ for a given build pair.
The weighted-graph reopening variant is confined to fixture code.

Each variant has complete configure/build argv, absolute binary path, native
fixture argv for seeds1/2 and runtime modes, clean environment, CPU0 affinity
and audit argv. No arbitrary argument overrides. The sole substitution is a
six-digit unique sample_id in output paths; it cannot change inputs or flags.
The input allowlist pins the single small placed fixture, constraints, chipdb
and hooks; exact paths and hashes must both match. CPU JSON is absent and must
be refused. Compiler/runtime dependency files and dependency trees are pinned.
Require resolved dependencies to match those pins; unexpected configure/link
resolution halts. Do not run old campaign drivers: they contain CPU launches.

Retain one warmup pair and nine measured pairs for each of five explicit
comparisons at each seed: disabled/baseline, no-trace/baseline,
selected-trace/baseline, no-trace/disabled and selected-trace/disabled. This is
10 groups ×20 fresh-process invocations =200 invocations, one per sample.
Warmup AB, measured pair0 AB then BA alternating; exclude warmup only. Each
sample has a 15-second cap and each group a shared 100-second cap. All overhead
groups share 1000 seconds. Builds/preparation, accounting/corruption,
weighted-graph, equivalence/audits have caps600/100/60/40 seconds, respectively.
The global 1800-second deadline includes all phases and setup: earliest deadline
wins. These caps bound work, not guarantee completion at worst-case sample
runtimes. Incomplete groups or a missed deadline are nonaccepting; never extend,
resample or retry to obtain a pass. Both original median thresholds remain.

Frozen future entry points (NOT authorized or executed):

```bash
python3 tools/cpu_route_d1/prepare.py --packet spu_strategy/cpu_route_d1_20261019 --output build/cpu_route_d1/implementation_01
tools/run_detached_job.sh --output build/cpu_route_d1/fixture_gate_01 --timeout 1800 --notify-desktop -- bash tools/cpu_route_d1/run_fixture_gates.sh --packet spu_strategy/cpu_route_d1_20261019 --preparation build/cpu_route_d1/implementation_01
```

Before launch, pin all implemented scripts and expanded command arguments in a
new implementation_manifest.json; pin built executable hashes before any native
fixture invocation. Refuse absent/mismatched manifests. New directories only,
no installs or overwrites. Job budget: one fixture job,1800 seconds,no retry.
After LAUNCHED record unit/evidence and end turn. Native fixture qualification,
implementation review and implementation authorization remain pending; CPU,
FPGA synthesis and board work remain excluded. No repository-wide verification
claim follows from preparation checks.

## 7. Later integrated CPU diagnostic stopping conditions

No executable CPU launch command is supplied or authorized. Require a separate
owner-approved manifest with maximum attempts, per-attempt wall timeout,
cumulative wall budget, exact executable/input hashes, seed, thread count and
new output path. An authorization boolean alone is insufficient. The old budget
cannot be reused. D1 defaults remain off without the explicit diagnostic config.

In that later manifest freeze earliest applicable stopping reason:

1. **Complete route:** original router termination, zero unresolved overuse,
   successful architecture binding, then independent endpoint/ownership/
   completeness, preservation and FASM checks. Native exit alone is insufficient.
   Do not generate/program a bitstream. Timing remains separately unqualified.
2. **Two finished congestion iterations:** after second complete committed
   snapshot and existing binding checks at the iteration boundary, stop with
   `TWO_ITERATIONS`, publish absolute and fractional changes in overused wires,
   summed overuse, unresolved owners, and exact state-set comparison.
3. **Bounded diagnostic attribution:** request safe stop at 50,000 completed
   calls or 250,000,000 aggregate forward pops since D1 start, whichever first.
   Commit at least 1000 completed calls with exact per-call totals and identities,
   a ranked report plus explicit unfinished coverage. If fewer are available,
   mark `INSUFFICIENT_ATTRIBUTION`, not diagnostic success. Total-call capacity
   100,000 is a separate hard storage guard, not the review trigger.
4. **Caps/deadline/error:** stop as specified in §5 or at the separately frozen
   external deadline; preserve partial records and terminal classification.

No trigger extends another. A completed route outranks a simultaneous diagnostic
trigger only if original complete-route conditions actually hold. Diagnostic
stops must not emit COMPLETE/route-success. Detached exit codes: 0 only after
full requested route/audits; 20 diagnostic review stop, 21 invalid diagnostics,
22 budget breach; external 124 TIMEOUT. Record diagnostic reason separately from
the detached runner's FAILED/nonzero marker. None qualifies 25 MHz.

## 8. Review acceptance and authorization boundary

Approve source edit surface, schema, fixtures, budgets and commands separately
from a CPU campaign. This draft authorizes only packet preparation/validation.
Do not compile native code, route fixtures, launch CPU routing, alter search
policy, synthesize, install tools, touch boards, or consume physical qualification
budgets under this preparation. Mark unrun claims NOT RUN.

HALT if coherent unfinished snapshots, complete accounting within fixed memory,
safe quiescent congestion capture, or transparent caps cannot be implemented.
Propose the smallest contract correction; do not silently weaken observations.

## 9. Corrected preparation review ledger

R1–R5 are incorporated as preparation requirements, not native PASS evidence.
Review `SCHEMA.md`, `allocation.json`, `command_matrix.json` and fixtures.json
together. The historical IMPLEMENTATION_REVIEW.md remains unchanged. Native
qualification, overhead, graph equality and policy probes remain **NOT RUN**.
No source edits, fixture launch, integrated routing or 25 MHz claim is authorized.

## 9. Correction traceability and preparation validation

Controlling review: `cpu_route_d1_20261019/IMPLEMENTATION_REVIEW.md`, preserved
unchanged. R1 maps to commands.json; R2 to fixtures.json and command phase caps;
R3 to binary_schema.json, binary_golden.json and resources.json; R4 to
durability.json; R5 to acceptance.json. Original files and their checksums are
in original_pre_corrections/preservation_manifest.json. The weighted_graph.json
proposal and production source pins are unchanged.

```bash
python3 spu_strategy/cpu_route_d1_20261019/check_packet.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_cpu_route_d1_2026-10-19.md spu_strategy/cpu_route_d1_20261019
```

`preparation.diff` is an exact unified diff against the preserved original
packet; new files appear as additions. `preparation_diff_manifest.json` pins
original/current byte identities; validation_results.json records offline
checks. Native router edits, compilation, fixture launch, CPU work, synthesis
and board work require future explicit authorization. No such authorization
is inferred from accepting these preparation corrections.
