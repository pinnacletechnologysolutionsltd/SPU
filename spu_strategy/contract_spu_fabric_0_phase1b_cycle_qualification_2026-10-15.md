# SPU-FABRIC-0 Phase 1B Cycle-Convention Qualification

**Date:** 2026-10-15
**Status:** SOURCE-DERIVED QUALIFICATION PACKET — REVIEW PENDING; SCHEDULER HELD
**Parent model:** `contract_spu_fabric_0_phase1b_schedule_model_draft_2026-10-15.md`
**Frozen workload input:** `fixtures/spu_fabric_0/manifest.json` and
`fixtures/spu_fabric_0/traces/isolated.jsonl.gz`
**Purpose:** Resolve edge-level A timing and Candidate C stage availability
before any Phase 1B scheduler evaluation.

## 1. Scope and evidence boundary

This packet records hand-derived edge traces from the frozen RTL and the
declared B/C abstract resource model. It does not run or qualify the Phase 1B
scheduler, does not change the Phase 1A fixtures, and does not establish
synthesis, clock, area, or FPGA results. B and C traces below are model
examples, not RTL measurements.

The frozen RTL source identities used for this derivation are:

| Source | SHA-256 |
| --- | --- |
| `hardware/rtl/math/surd_smul_unit.v` | `0cebd08aec2cd9ea6603ae655b9a15d65d9651eca958e1935137bd6deb04fdaa` |
| `hardware/rtl/math/surd_normalize_unit.v` | `4d43e03f3745326a3f7d26fcf7a34219c8bc0ba1a4826a568eb3c74ab82291fa` |
| `hardware/rtl/math/surd_binary_gcd3.v` | `e994552b50f34017b176d91303ac6c85774748d64d4014755d0979d6fcd3097c` |
| `hardware/rtl/math/surd_exact_quotient.v` | `2a78246d9ab13d439ee0be88b57dd58029d1d5ed0e77fcd61d1bac4837fd15cd` |
| `hardware/rtl/core/spu4/spu4_som_edge.v` | `9dbea0aed255b7738d40390d0abc2c627117de449e038422e85c9faed492ac95` |
| `hardware/rtl/core/spu4/spu4_som_edge_wrapper.v` | `5bcb8b832338e2fb8b900e5fb8e94fbc107462094594e1b4d57b1fd3815b28f2` |
| `hardware/rtl/math/spu_d4_reflection_unit.v` | `5dbf69f431285a7bb55657d65bfd909c30efa981890ca42f766f13fde88425e8` |

The frozen isolated trace SHA-256 is
`18585af72c7f65b4767e0526890424e56218af9eb20a6dbf90d943bf30c8a440`.
The selected normalized Surd record is
`surd_w32:min_negation_overflow`, operands
`[-2147483648, 0, 1, -1, 0, 1]`, with `raw=[2147483648,0,1]`,
`request_normalization=true`, `invalid=false`, and `overflow=true`.

## 2. Edge convention

Edge `n` is the rising edge that accepts the operation. Signals assigned by
nonblocking assignments at an edge are visible during the following interval.
An output asserted by the RTL on edge `n` is an architectural completion at
edge `n`, not one cycle later. A one-cycle abstract B/C micro-operation issued
in interval `[n,n+1)` makes its result available at edge `n+1`.

## 3. Candidate A Surd timing

### A1. Invalid denominator

Use frozen record `surd_w32:zero_denominator_a` (or
`surd_w32:zero_denominator_b`). Its denominator input `d` or `f` is zero.

| Edge | RTL state/action | Observable result |
| --- | --- | --- |
| `n` | `IDLE` sees `start` and `d_in == 0 || f_in == 0`; it remains `IDLE` | `done=1`, `invalid=1`, no raw result is asserted by the trace contract |
| `n+1` | `IDLE` can accept the next request | Earliest next acceptance |

The operation latency is zero edge-to-edge cycles; it still consumes one
acceptance event. No second request can also be accepted on edge `n`.

### A2. Normalization-required frozen fixture

For `surd_w32:min_negation_overflow`, W=32 and N=2W+2=66. The signed raw
numerator is `+2^31`, which does not fit signed 32-bit output; raw denominator
is 1, so the normalizer reduces by gcd 1 and reports overflow. This fixture
does not depend on a guessed wrapped result.

| Edge | SMUL / normalizer / subunit action |
| --- | --- |
| `n` | SMUL accepts and captures all five `LANES=5` products; state becomes `FINAL`. |
| `n+1` | SMUL `FINAL` sees `raw_fits=0`, enters `WAIT_NORM`; `norm_req` is high after this edge. |
| `n+2` | Normalizer accepts `start`, captures raw values, raises `gcd_start`; state becomes `WAIT_GCD`. |
| `n+3` | GCD accepts `gcd_start`, enters `INIT_AB`. |
| `n+4` | GCD `INIT_AB` sees the second numerator is zero and moves the denominator into the second GCD phase. |
| `n+5` | GCD `INIT_GD` sees an even numerator and odd denominator; enters `LOOP_GD`. |
| `n+6` through `n+36` | `LOOP_GD` shifts the even numerator right once per edge: 31 shifts from `2^31` to 1. |
| `n+37` | GCD sees equal operands and asserts `gcd_done`. |
| `n+38` | Normalizer observes `gcd_done`, raises `quotient_start`. |
| `n+39` | All three quotient engines accept the common start. |
| `n+40` through `n+105` | Each quotient engine performs exactly N=66 restoring iterations; `*_done` is asserted at `n+105`. |
| `n+106` | Normalizer observes all quotient completions and asserts `valid`/`done`, with `fits_W=0`. |
| `n+107` | SMUL `WAIT_NORM` observes `norm_valid`, asserts `done` and `overflow`, and retires. |

Thus the fixture's intrinsic SMUL latency is **107 cycles** from accepting
edge to completion edge. The next request can be accepted no earlier than
`n+108` because `n+107` is the retirement edge. This is one hand-derived
fixture result, not a full-domain worst-case bound or a fixture-set maximum.

### A3. Non-normalized ordinary request

For any valid W=32/64 `LANES=5` operation with `raw_fits=1`:

| Edge | Action |
| --- | --- |
| `n` | Accept; all products captured and state becomes `FINAL`. |
| `n+1` | `FINAL` copies the raw result, asserts `done`, and returns to `IDLE`. |
| `n+2` | Earliest next acceptance under the no-retire-edge-reaccept convention. |

This confirms the edge-to-edge one-cycle completion and does not change the
established normalizer handshake.

## 4. Candidate A SOM and D4 conventions

The SPU-4 wrapper instantiates four features. For one accepted SOM query:

| Edge | Action |
| --- | --- |
| `n` | `S_IDLE` accepts `start`, initializes `node_idx=0`, enters `S_SCAN`. |
| `n+1` | Scan node 0. |
| `n+2` | Scan node 1. |
| `n+3` | Scan node 2. |
| `n+4` | Scan node 3, assert `done` and `bmu_valid`, enter `S_DONE`. |
| `n+5` | `S_DONE` returns to `S_IDLE`; no acceptance on this edge. |
| `n+6` | Earliest next acceptance. |

The accepted-start to done latency is 4 cycles and the reaccept interval is 6
cycles.

`spu_d4_reflection_unit.v` contains only combinational assignments and has no
clock, state, or handshake. Under the explicit common wrapper convention in
the model, A/B/C all accept/capture at edge `n`, sample the result at `n+1`,
and complete at `n+1`. At edge `n+1`, the old result is sampled and retired
before the next D4 input is captured. D4 is the sole same-edge retire/accept
exception to the ordinary-client rule; its modeled initiation interval is one
cycle. This is an accounting convention, not a physical timing qualification
of D4 logic. For an invalid signed-16 reflection, compare the invalid status
only; output bits remain unspecified under the frozen D4 result-definedness
policy.

For consecutive D4 requests, accept request 0 at edge `k`, retire its output
and accept request 1 at edge `k+1`, then retire request 1 at edge `k+2`. This
is the explicit wrapper exception that gives D4 an initiation interval of one;
it does not change the ordinary-client no-reaccept-on-retirement-edge rule.

## 5. B and C concurrent Surd/SOM micro-operation traces

These traces use simultaneous context acceptance at edge 0, initial product
arbitration pointer `surd_w32`, and one ready Surd W32 client plus one ready
SOM client. Product results become available at the ending edge of their
issue interval. D4 is on its independent path.

### B: one shared product lane

The cursor advances round-robin across ready clients; the sole Surd context
issues its next fixed-order product and SOM issues products in node/feature,
`p_square` then `q_square` order.

| Interval | Product-lane grant | Available edge |
| --- | --- | --- |
| `[0,1)` | Surd `aa` | 1 |
| `[1,2)` | SOM node0/feature0 `p_square` | 2 |
| `[2,3)` | Surd `bb` | 3 |
| `[3,4)` | SOM node0/feature0 `q_square` | 4 |
| `[4,5)` | Surd `ab` | 5 |
| `[5,6)` | SOM node0/feature1 `p_square` | 6 |
| `[6,7)` | Surd `ba` | 7 |
| `[7,8)` | SOM node0/feature1 `q_square` | 8 |
| `[8,9)` | Surd `dd` | 9 |
| `[9,10)` | SOM node0/feature2 `p_square` | 10 |

The B add lane is separately arbitrated. The following hand trace applies
its own initial pointer `surd_w32`, round-robin rule, and fixed topological
priority to the operations that become ready in this example.

| Interval | Add-lane grant | Reason / result availability |
| --- | --- | --- |
| `[3,4)` | Surd `three_bb` | `bb` available at edge 3; result at edge 4 |
| `[4,5)` | SOM n0/f0 `three_q` | Surd raw_a and SOM three_q are ready; add pointer scans from w64 and grants SOM; result at edge 5 |
| `[5,6)` | Surd `raw_a` | Highest-priority ready Surd addition; result at edge 6 |
| `[6,7)` | SOM n0/f0 `feature_q` | Both p-square and three_q are available; result at edge 7 |
| `[7,8)` | Surd `raw_b` | `ab` and `ba` are both available at edge 7; result at edge 8 |
| `[8,9)` | SOM n0/f1 `three_q` | q-square available at edge 8; result at edge 9 |
| `[9,10)` | SOM n0/f1 `feature_q` | Its p-square and three_q are available; result at edge 10 |
| `[10,11)` | SOM node0 reduction add 0 | Feature 0 and 1 totals are available; result at edge 11 |
| `[11,12)` | SOM n0/f2 `three_q` | q-square available at edge 11; result at edge 12 |
| `[12,13)` | SOM n0/f2 `feature_q` | Inputs are available; result at edge 13 |
| `[13,14)` | SOM n0/f3 `three_q` | Its q-square is available; feature 2 total also enables a node reduction, but fixed priority selects `three_q`; result at edge 14 |
| `[14,15)` | SOM n0/f3 `feature_q` | Its p-square and three_q are available; result at edge 15 |
| `[15,16)` | SOM node0 reduction add 1 | Prior partial sum and feature 2 total are available; result at edge 16 |
| `[16,17)` | SOM node0 reduction add 2 | Prior partial sum and feature 3 total are available; node0 total at edge 17 |

This makes explicit that `raw_a` cannot issue until the interval after
`three_bb` is available, while `raw_b` waits for both `ab` and `ba` at edge 7.
It also exercises the fixed priority between SOM feature construction and
node reduction when both are ready at edge 13. The additions overlap
independent product-lane work, and newly created results do not feed another
addition in the same interval.

### C: two shared product lanes and dedicated reductions

The rule grants at most one operation to each distinct ready client in an
interval. While both clients have products ready, W32 Surd is granted lane 0
and SOM lane 1. Once Surd's five products are exhausted, SOM receives only one
grant per interval; the second product lane idles because a client cannot
issue two products in one interval.

| Interval | Lane 0 | Lane 1 | Relevant result availability |
| --- | --- | --- | --- |
| `[0,1)` | Surd `aa` | SOM n0/f0 `p_square` | Both at edge 1 |
| `[1,2)` | Surd `bb` | SOM n0/f0 `q_square` | Both at edge 2 |
| `[2,3)` | Surd `ab` | SOM n0/f1 `p_square` | Both at edge 3 |
| `[3,4)` | Surd `ba` | SOM n0/f1 `q_square` | Both at edge 4 |
| `[4,5)` | Surd `dd` | SOM n0/f2 `p_square` | Both at edge 5 |
| `[5,6)` | SOM n0/f2 `q_square` | — | q-square at edge 6; Surd reduction issued in this interval and raw tuple ready at edge 6 |
| `[6,7)` | SOM n0/f3 `p_square` | — | p-square at edge 7 |
| `[7,8)` | SOM n0/f3 `q_square` | — | All n0 squares ready at edge 8 |
| `[8,9)` | SOM n1/f0 `p_square` | — | n0 reduction/winner stage also issues; node0 total/best available at edge 9 |
| `[9,10)` | SOM n1/f0 `q_square` | — | n1 products continue |
| `[16,17)` | SOM n2/f0 `p_square` | — | n1 reduction/winner stage issues; result at edge 17 |

For clarity, SOM node1's last square is issued in `[15,16)`, so all eight
node1 products are available at edge 16 and its reduction stage may issue in
`[16,17)`, concurrently with the node2 product shown in the table. The node1
total and updated winner state are available at edge 17. Node2's eight
products issue in `[16,24)` and its reduction stage may issue in `[24,25)`.

The Surd raw reduction stage begins at `[5,6)` because all five products are
available at edge 5, and its two raw outputs and fit result appear together
at edge 6. The Surd context remains allocated through normalization if
requested. This resolves when C reduction may begin, when outputs become
available, and why SOM reductions do not begin before all eight node products
are ready.

## 6. Queue-full offered-arrival trace

For one client with a four-entry ingress queue, suppose its execution context
is busy and four already-enqueued requests occupy the queue before edge `k`.
Request 5 has immutable `offered_cycle=k`.

| Edge | Context/queue action | Request 5 |
| --- | --- | --- |
| `k` | Context busy, no dequeue; queue remains full | Held; count one backpressure cycle |
| `k+1` | Prior operation retires. The no-retire-edge-reaccept rule prohibits dequeue/acceptance on this same edge; queue remains full | Held; count a second backpressure cycle |
| `k+2` | Context is ready; dequeue one pre-existing request for acceptance, then enqueue the held request into the freed queue slot | Accepted from ingress without changing `offered_cycle=k` |

No request is dropped, retimestamped, or accepted on the prior operation's
retirement edge.

## 7. Findings and remaining gates

The hand derivations resolve the reviewed schedule questions:

1. Candidate A invalid denominator completion is on its accepting edge;
   valid raw-fit completion is one cycle later; the normalization fixture
   completion is 107 cycles after acceptance, with both normalizer handshakes
   counted once.
2. Candidate A four-node/four-feature SOM is 4 cycles to `done`, with
   6-cycle reaccept interval.
3. D4 has no RTL cycle latency; the wrapper model has one interval of latency,
   initiation interval one, and an explicit retire-then-accept edge exception.
4. Candidate C reduction issue/availability and context retirement boundaries
   are explicit.
5. The queue-full case preserves immutable offered time and counts backpressure
   without same-edge reacceptance.

The full-domain GCD bound and maxima over the frozen Surd fixtures are recorded
in `contract_spu_fabric_0_phase1b_timing_qualification_2026-10-15.md`; that
source-derived timing packet remains review pending and is not an RTL timing
measurement. Candidate C's schedule draft now proposes C2: separate W32/W64
Surd final reducers, each one-cycle with initiation interval 1 and no
cross-width arbitration. This proposal remains pending independent review and
freeze; it is not a physical resource claim. Complete B/C schedule/config
hashes and the Phase 1B execution budget remain outstanding. No scheduler
evaluator, RTL simulation, synthesis, place-and-route, or FPGA operation is
authorized by this packet. Phase 1B execution remains held until all
qualifications and the execution contract are reviewed and frozen.
