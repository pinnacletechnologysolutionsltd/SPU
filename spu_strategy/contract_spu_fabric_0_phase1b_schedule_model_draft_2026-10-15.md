# SPU-FABRIC-0 Phase 1B Schedule Model Draft

**Date:** 2026-10-15
**Status:** DRAFT — OWNER REVIEW REQUIRED; NO EVALUATION AUTHORIZED HERE
**Parents:** `contract_spu_fabric_0_2026-10-15.md`; `contract_spu_fabric_0_phase1b_timing_addendum_2026-10-15.md`
**Frozen input:** `fixtures/spu_fabric_0/manifest.json` and its three trace files

## 1. Preservation and Commands

Do not modify the Phase 0/Phase 1A contracts, source locks, manifest, or trace
files. Do not run a scheduler, RTL simulation, synthesis, FPGA tool, or hardware
operation under this draft.

No execution command is authorized by this draft. The Phase 1B evaluator
command, output directory, attempt count, timeout, cumulative budget, and retry
policy belong in the later Phase 1B execution contract.

## 2. Cycle and Completion Convention

Use rising-edge indices. An operation accepted at edge `n` and completed at
edge `n+k` has latency `k` cycles. A one-cycle micro-operation issued during
`[n,n+1)` makes its result available at edge `n+1`; dependent work may issue
no earlier than the following interval. A response latency includes offered
arrival to externally visible completion, including ingress backpressure,
arbitration, and resource stalls.

At each edge, first retire completed operations and release their execution
contexts, then dequeue at most one already-enqueued operation per ready
client, then enqueue that edge's offered operation if ingress has capacity.
An arrival enqueued at edge `n` is first eligible for acceptance at `n+1`.
When a queue is full after the dequeue step, hold the offered operation and
count producer backpressure; never shift its immutable offered cycle. For
ordinary stateful clients, do not accept a replacement operation on the edge
that its previous operation retires; its next acceptance may occur at the
following edge. D4 is the sole exception, with its edge ordering and
one-cycle acceptance interval defined below.

### D4 dedicated path

The frozen `spu_d4_reflection_unit.v` is combinational and has no registered
stages or handshake. For the scheduler model, use this explicit wrapper
convention for every candidate:

- Accept and capture inputs at edge `n`.
- Evaluate the combinational D4 function during `[n,n+1)`.
- At edge `n+1`, sample and retire the previous operation's output first, then
  capture the next operation's inputs on that same edge. The old input was
  held stable through the sampling edge; the new input becomes active only
  after capture. This D4-only same-edge retire/accept rule is the explicit
  exception to the ordinary-client rule above.
- Occupy the modeled D4 path for one interval, with initiation interval 1:
  consecutive operations may be accepted on consecutive edges, at most one
  per cycle on the independent D4 path.
- Model one abstract input/output boundary for accounting only. This is not a
  claim that the frozen RTL contains those registers or meets a clock period.

## 3. Frozen Arithmetic Micro-Operations

The following model makes the candidate resource maps executable without
claiming that B or C already exists in RTL.

### Product operations

- Each product lane has one-cycle latency and initiation interval 1.
- Products are full precision. Surd operands retain the source signedness:
  `aa`, `bb`, `ab`, and `ba` are signed products; `dd` is unsigned.
- SOM operands are signed 17-bit deltas; each square is a full-precision,
  nonnegative product. No narrowing or wrap is permitted.
- A product result is available to dependent work at the following edge.

### Surd operation graph

For operands `(a,b,d,c,e,f)`, issue five independent products:
`aa=a*c`, `bb=b*e`, `ab=a*e`, `ba=b*c`, and `dd=d*f`.
Then compute `three_bb = bb + (bb << 1)`, `raw_a = aa + three_bb`, and
`raw_b = ab + ba`. The `dd` product is the raw denominator. Preserve the
source RTL widths and signed/unsigned fit tests. Only after all raw values and
fit status are available may normalization start.

### SOM operation graph

For each of four nodes and four features, issue `p_square=dp*dp` and
`q_square=dq*dq`, giving 32 products per query. For each feature compute
`three_q = q_square + (q_square << 1)` and
`feature_q = p_square + three_q`. Sum the four `feature_q` values for each
node and select the lowest-index minimum using strict `<`. The reduction
width, unsigned interpretation, and tie rule must match the frozen SOM RTL
and oracle.

## 4. Candidate Resource Schedules

### A — Dedicated reference

- Surd uses the frozen `surd_smul_unit` with `W=32/64, LANES=5`, connected to
  the frozen normalizer handshake. Intrinsic Surd timing is accepted-start to
  `done`, including normalization and return handshake. From the FSM, a
  zero-denominator request asserts `done` on its accepting edge (0-cycle
  edge-to-edge latency); an ordinary product captures its five products on
  the accepting edge and completes on the following `FINAL` edge (1 cycle)
  when normalization is not requested. When normalization is requested,
  completion is the exact normalizer handshake latency plus the FSM wait/return
  edges; derive per input from the RTL timing oracle, not from product count.
- SOM uses the frozen four-node/four-feature sequential-scan behavior. Derive
  accepted start at edge `n`, scans nodes at `n+1` through `n+4`, and asserts
  `done` at `n+4` (4-cycle latency). The `S_DONE` edge at `n+5` returns to
  idle but cannot accept a new request; earliest next acceptance is `n+6`,
  giving a 6-cycle initiation interval.
- D4 uses §2's abstract one-interval interface convention.
- Independent family units may operate concurrently. Preserve per-client
  operation order; no global arbiter is added.

### B — One shared product lane and one shared binary add lane

- Use one product lane and one add lane. Each has latency 1 and initiation
  interval 1. The add lane is a binary add operation, not a fused multioperand
  instruction; shifts by one are wiring and consume no add issue slot.
- The add lane is 130 bits to cover the signed Surd raw sums; SOM values are
  zero-extended and treated as unsigned. Preserve the exact Surd and SOM
  arithmetic contracts.
- Surd uses the five products and three dependent additions in §3. SOM uses
  the 32 products, two additions per feature, three additions to reduce the
  four feature values per node, and the dedicated strict-`<` winner path.
- Product and add resources arbitrate independently, work-conserving
  round-robin over `surd_w32`, `surd_w64`, and `som`, initially pointing at
  `surd_w32`. Each pointer advances to the client after the last grant; no
  grant leaves that pointer unchanged. A client may issue at
  most one micro-operation to a given resource per cycle.
- Use fixed per-client topological priority when more than one micro-operation
  is ready: Surd products `aa, bb, ab, ba, dd`; Surd additions
  `three_bb, raw_a, raw_b`; SOM products by ascending node, feature, then
  `p_square, q_square`; SOM additions by ascending node, feature, then
  `three_q, feature_q`, followed by node-reduction additions in ascending
  operand index. A newly ready dependent operation waits until the next cycle.
- Keep Surd normalization/control and SOM comparison/tie logic dedicated.

### C — Two shared product lanes with dedicated reduction paths

**Proposed schedule amendment — C2 width-specific Surd reducers; review pending.**
The parent contract does not prescribe a shared or width-specific Surd final
reducer. This schedule freezes Candidate C as C2: one dedicated W32 Surd
final-reduction path and one dedicated W64 Surd final-reduction path. They
are independent resources, each with one-cycle latency and initiation
interval 1. They may accept reductions concurrently when each width's own
products are ready. There is no cross-width reducer arbitration, no implicit
sharing with either product lane, and no additional context or queue beyond
the storage already charged to Candidate C. The shared product lanes remain
shared across W32 Surd, W64 Surd, and SOM as specified below. This is a
scheduling-model choice, not a physical area or timing claim. A shared-reducer
C1 variant requires a separately frozen sensitivity study.

For all candidates, model W32 and W64 Surd normalization/control as
independently parameterized dedicated paths, one per width, consistent with
the two frozen RTL configurations. They do not arbitrate with each other or
with SOM/product resources. Count both paths and their state in later physical
costing; do not model a free shared normalizer.

- Use two product lanes, each with latency 1 and initiation interval 1.
- Arbitrate work-conserving round-robin over the three product clients. In one
  cycle select at most two distinct ready clients: the first grant uses lane
  0, the next distinct-client grant uses lane 1. Advance the pointer to the
  client after the last grant; no grant leaves it unchanged. If only one
  client is ready, the second lane is idle; do not issue two micro-operations
  from one client in the same cycle.
- Within a client, select the lowest-priority-rank ready product from the
  fixed order in §4.B. A lane's result becomes available at the next edge.
- W32 and W64 Surd each use the five products in §3 and their own dedicated
  final-reduction path, which computes `raw_a` and `raw_b` together once that
  operation's required products are ready. A width's reduction may issue in
  the first interval whose starting edge follows availability of all five
  products; both raw outputs and fit status become available at the ending
  edge of that one-cycle stage. The W32 and W64 reducers can issue in the same
  interval. Each Surd context stays allocated through any normalizer
  start/return handshake and final status retirement. Normalization/control
  remains on that width's dedicated normalizer/control path; it is not
  silently included in the final-reduction resource.
- SOM uses the 32 products in §3 and a dedicated one-node-per-cycle reduction
  and strict-`<` winner path. A node may be reduced only after all eight of
  its square products are available. Its stage may issue in the first interval
  whose starting edge follows availability of all eight products for the next
  node in ascending node order. That one-cycle stage computes the four-feature
  total, compares it with the current best, and makes the updated best state
  available at the ending edge. A later node cannot bypass an earlier node
  that is not ready. Preserve lowest-index tie behavior.

For B and C, an accepted operation owns one bounded execution context per
client until retirement. That context is not an extra request queue. A client
cannot accept its next source-ordered operation until its current operation
retires. The four-entry external ingress queue per client and zero additional
candidate request-queue entries remain as frozen in the Phase 1A manifest.
Record context/result storage for later physical costing; do not treat it as
free hardware. Independent product and add resources may issue for the same
client in one cycle when both micro-operations are ready; a dependency result
created at edge `n` cannot feed another operation until interval
`[n,n+1)`.

For A, B, and C, if the raw Surd result requests normalization, assert the
dedicated normalizer start during the interval after raw-ready and let the
normalizer accept it at the following edge. The multiply operation retires at
the first later edge that observes the normalizer's valid result. Include both
start and return handshakes exactly once; do not overlap or double-count the
normalizer's internal GCD and parallel quotient stages.

For Candidate B's dedicated SOM winner path, process node totals in node-index
order with one 64-bit unsigned strict-`<` comparison per cycle, including node
0 against the initialized maximum value. The first node initializes the
winner; equal values retain the lower index. Candidate C performs its
one-node reduction and corresponding winner comparison in the same dedicated
one-cycle node stage.

### Candidate C stage availability and retirement

Product-lane issue during interval `[n,n+1)` makes a square/product available
at edge `n+1`. Candidate C's Surd final-reduction stage and SOM node stage may
not consume that result until an interval beginning at or after that edge.
The Surd reduction is a single one-cycle stage with both raw outputs produced
together. The SOM reduction path has one stage and one node result per cycle;
it starts with node 0, then advances in node order when the next node's eight
products are available. Stage availability is distinct from operation
retirement: the context is released only when the specified final response is
retired, including Surd normalization where requested.

## 5. Qualification Required Before Evaluation

1. Independently derive the remaining A Surd normalization timing from the
   frozen RTL semantics. Report
   a proved/derived full-domain upper bound separately from the maximum over
   the Phase 1A fixtures. Include the normalizer's `MAX_ITER` guard, both GCD
   phases, parallel quotient engines, start/done handshakes, and early invalid
   completion. Do not infer a general bound from fixture maxima.
2. Derive A's SOM latency/reaccept interval and confirm the D4 module remains
   combinational. The D4 wrapper convention is a model boundary, not a physical
   timing result.
3. Validate representative intrinsic Surd timing cases independently of the
   scheduler evaluator. If this requires substantial RTL characterization,
   define a separate bounded verification allocation before running it.
4. Confirm the B/C DAGs preserve all source-defined outputs and status
   semantics. These are modeled candidate schedules, not RTL or physical
   measurements.
5. Freeze the timing tables, DAG/config hashes, exact evaluator command,
   output directory, and owner-approved attempt/timeout/cumulative budget in
   the Phase 1B execution contract. Halt on any unqualified timing or
   unresolved schedule rule.
