# Engineering Contract: SPU-FABRIC-0 Shared Execution Feasibility
**Date:** 2026-10-15
**Contract ID:** `contract_spu_fabric_0_2026-10-15.md`
**Status:** PHASE 0 RATIFIED — PHASE 1A AUTHORIZED

**Roles:**
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Repository owner / assigned implementer
- **Integration Auditor:** Repository owner / software and FPGA evidence review

## 1. Objective and Phase Boundary

Prepare a frozen, workload-based comparison of dedicated arithmetic, maximal
arithmetic sharing, and selective sharing. Test the hypothesis:

> Share arithmetic resources only when the mapped resource savings survive
> control, scheduling, storage, timing, and contention costs.

This document is the Phase 0 deliverable. It defines the trace sources and
selection rules, matched baselines, cost metrics, proposed resource limits,
and kill criteria for owner review. It does not itself freeze generated trace
artifacts. Phase 1A must materialize and hash those traces before Phase 1B
runs any scheduler comparison. This phase authorizes no test execution, software
scheduler, Verilator, RTL edit, synthesis, placement/routing, FPGA, or
hardware operation.

Phase 1A trace preparation, Phase 1B software scheduling, Phase 2 standalone
RTL/Verilator, Phase 3 FPGA physical comparison, and Phase 4 integration
decision require separate contracts and owner authorization. In particular,
Phase 1B may not begin until the Phase 1A trace fixtures and manifest have been
independently reviewed and frozen. Do not redesign or modify the CPU/GPU.

## 2. Candidate Workload Sources

Use only workloads with an existing exact software oracle and a corresponding
bounded operator implementation. The trace preparer shall emit canonical input
records, expected result/status digests, provenance, and hashes before any
scheduler comparison.

| Family | Frozen source basis | Included behavior |
|---|---|---|
| Surd multiply | `hardware/rtl/math/surd_smul_unit.v`; `hardware/tests/math/surd_mul_normalizer_vectors_harness.v`; `software/experiments/surd_wide_correctness_vectors.py`; driver `software/tests/test_surd_wide_rtl_vectors.py` | W=32 and W=64; LANES=1,2,5; valid products, signed boundaries, normalization requests/responses, overflow preservation, and invalid zero-denominator cases. |
| D4 reflection | `hardware/rtl/math/spu_d4_reflection_unit.v`; `software/tests/test_d4_reflection_oracle.py`; `software/tests/test_d4_reflection_rtl.py` | Four simple-root reflections, signed-16 boundaries, and exact result/invalid-flag behavior, including the `-32768` negation boundary. The 2-bit selector encodes only valid roots. Keep this as a dedicated-path control; it does not consume the shared multiplier. |
| SOM BMU | `hardware/rtl/core/spu4/spu4_som_edge.v`; `software/lib/spu4_som_edge_oracle.py`; `software/tests/test_spu4_som_edge_oracle.py`; `hardware/tests/spu4/spu4_som_edge_full_chain_tb.v` | Four nodes, four features, WIDTH=16; exact quadrance, negative deltas, near misses, exact ties, feature-4-sensitive case, and lower-index tie rule. |

The trace manifest must identify exact source hashes, generator source hash
and version, vector counts, widths, seeds, release cycles, dependencies, and
expected output/status digests. Use the complete source-defined finite sets:
327 Surd vectors at each of W=32 and W=64; all 288,132 D4 RTL-oracle cases
(65,536 reduced vectors, 2,401 boundary vectors, and 4,096 seeded vectors,
each across four selectors); and all eight SOM queries against the four-node,
four-feature weight fixture. Preserve source order and case identifiers.
Reuse named existing vectors and seeds; do not invent expected answers from
the candidate model. Where existing tests do not expose an input vector as
data, the preparer may extract it into a frozen fixture only with an
independent oracle result.

Each frozen operation record must include a stable operation ID, source case
ID, client, offered release cycle, operands, initial state, read/write set,
predecessor operation IDs, and oracle result/status. Source-derived read-after-
write dependencies must be retained; independent requests may run concurrently
only when the source workload permits it. Freeze the generator version and
hash, serialized trace hash, exact case count, and deterministic ordering.
Reject the entire trace set on an invalid record, oracle mismatch, missing or
duplicate operation ID, broken dependency, hash mismatch, or incomplete
source-defined case set. Do not drop a difficult operation after freezing.

For D4 signed-16 overflow cases, the independent oracle's `invalid` flag is
authoritative. If `invalid=true`, result bits are unspecified: encode
`result_defined=false` and `result=null`. Verify status only; do not infer or
assert wrapped output bits from the RTL. If `invalid=false`, encode
`result_defined=true` and the full exact signed-16 result vector, and verify
every result bit. The canonical expected-result digest includes `invalid` and
`result_defined`; it includes `result` only when `result_defined=true`. An
incorrectly set or cleared invalid flag rejects the fixture. This validity
policy applies to Candidates A, B, and C. Unspecified bits are not required to
agree across candidates; acceptance, completion, retirement, status, and all
defined outputs remain subject to exact agreement.

The per-record expected-value schema is explicit. For example:

```json
{"expected":{"invalid":true,"result_defined":false,"result":null}}
```

For a valid operation, use `invalid=false`, `result_defined=true`, and the
four-element exact result vector. The digest canonicalization must omit no
defined field and must never substitute a value for an undefined result.

E8, M31 modular multiplication, RPLU jets, SU(3), GPU rasterization, SOM
learning/update, and Soul persistence are excluded from the initial trace
set. E8 may be added only after a separately reviewed software reference and
finite-domain contract exist. RPLU and SU(3) are later stress workloads.

## 3. Matched Architecture Definitions

All candidates consume the same ordered per-family operation traces. The
candidate scheduler may change issue/completion times only. Mathematical
inputs, operation order dependencies, defined output values, flags,
normalization semantics, and overflow behavior must remain identical. Compare
outputs only when the frozen oracle marks `result_defined=true`; otherwise
compare the authoritative status and lifecycle fields, not unspecified bits.

All candidates expose the same externally observable command acceptance,
completion, result, and error semantics. Candidate A may use direct per-unit
dispatch and independent dedicated units; do not burden it with an unnecessary
global arbiter. Candidate-specific dispatch, muxes, queues, registers, and
scheduler logic are included in that candidate's measured totals. No candidate
may omit control overhead required by its own architecture.

Candidate A, B, and C use the same clock constraint, operand widths, exact
overflow/normalization contracts, trace inputs, initial state, and offered
arrival cycles. Their independent oracles—not cross-candidate agreement—are
the correctness authority. Any optimization of a candidate must preserve the
oracle-visible result, status, acceptance, and retirement behavior.

| Candidate | Frozen model | Comparison role |
|---|---|---|
| A — Dedicated | Existing operator-level parallelism: Surd LANES=5; dedicated D4 reflection; the current four-node/four-feature SOM datapath. | Correctness, area-vector, and throughput baseline. |
| B — Shared | One exact integer product lane with explicit signed/unsigned operand mode and one shared add/accumulate issue resource for Surd and SOM arithmetic. Keep Surd normalization/control, SOM winner comparison/tie logic, and D4 reflection dedicated. | Characterize maximum practical arithmetic sharing and its serialization cost. |
| C — Hybrid | Two exact integer product lanes with explicit signed/unsigned operand mode, shared between Surd and SOM arithmetic; retain separate Surd normalization/control, SOM accumulation/comparison/tie logic, and dedicated D4 reflection. | Test selective sharing while preserving operation-specific state and cheap paths. |

The shared-lane widths, signedness mode, operation mapping, accumulator widths,
register/queue capacity, and per-op service cycles must be derived from the
listed implementations and exact contracts, then frozen in the trace/config
manifest. Do not silently narrow operands or intermediates to make a shared
profile look cheaper. If a common unit cannot represent both operations
without changing their arithmetic contract, mark that sharing edge
INCOMPATIBLE and retain the candidate as a documented negative result.

## 4. Trace and Contention Profiles

Freeze at least these three profiles for each eligible family before running a
scheduler model:

1. **Isolated:** one operation stream at a time, preserving each operation's
   dependency order.
2. **Concurrent burst:** interleave Surd and SOM requests from the frozen
   traces at cycle zero; preserve per-client order and declare queue depth,
   backpressure, and arbitration before evaluation.
3. **Steady arrival:** replay the same operations at a fixed period declared
   in the frozen manifest. Derive the period from a cited existing workload
   or hardware protocol. If no defensible input period/deadline exists, mark
   deadline performance `NOT SPECIFIED` and report service rate, stalls, and
   queue occupancy without a real-time claim.

D4 requests run concurrently on their dedicated path in the two mixed profiles
to test dispatch and control interference, not arithmetic-resource sharing.
No rasterizer or timing-critical GPU request may be routed through the fabric.

Generate the offered arrival schedule once, independently of A/B/C scheduling.
For concurrent and steady profiles, assign each operation an immutable
`offered_cycle` and client order in the frozen trace file. All candidates
receive that same schedule through the same bounded external ingress depth.
When ingress is full, hold the request and record producer backpressure; do
not move its offered cycle, drop it, reorder it, or regenerate arrivals based
on a candidate's `ready` signal. Internal queue depths are declared per
candidate before evaluation and their storage cost is included in that
candidate's resource total.

The isolated profile must include each complete family trace. The mixed
profiles must include the complete declared Surd and SOM traces plus the
dedicated D4 control trace; do not choose only cases that exercise a preferred
resource. The concurrent-burst profile releases the first request from each
client at cycle 0 and releases subsequent requests in source order at the
frozen burst interval. The steady-arrival profile uses one fixed, predeclared
period per client. Its periods and the burst interval must be frozen before
any candidate model is run. If no sourced real-world period exists, label the
profile synthetic and make no product workload claim.

The owner must mark each nominated workload `LATENCY_CRITICAL` or `THROUGHPUT_ORIENTED`
in the frozen manifest. Every latency-critical workload must cite an existing
interface or product requirement and carry a numeric deadline in cycles. If
no sourced deadline exists, mark it `NOT SPECIFIED`; do not claim real-time
acceptance for it. For each throughput-oriented workload under steady arrivals,
the provisional hybrid requirement is throughput of at least 90% of Candidate
A **for that workload individually**, not averaged across workloads. This 10%
maximum degradation is a proposed threshold for owner ratification. Report
worst-case latency in cycles independently for every workload and candidate.
Phase 1 reports modeled completed operations per cycle; report operations per
second only after Phase 3 qualifies the common 25 MHz physical clock.

Each job has a deterministic acceptance, issue, completion, and retirement
record. Define whether same-cycle arbitration is fixed-priority or round-robin
in the manifest. Record queue occupancy, blocked cycles, issue order, latency,
initiation interval, and completed operations per cycle. No unbounded queue,
unbounded path, runtime floating point, or data-dependent variable-latency
operation is allowed in a candidate schedule model.

## 5. Phase 0 Review Items and Commands

The review must ratify or amend the following before Phase 1 is proposed:

1. Review the source semantics in §2. Halt if any named oracle and
   implementation disagree on the exact semantics used.
2. Ratify the trace-generation rules in §§2 and 4. Phase 1A will produce
   `fixtures/spu_fabric_0_trace_manifest.json` and frozen trace files under
   `fixtures/spu_fabric_0/`. That manifest must contain candidate A/B/C
   profiles, workload parameters, input-arrival profiles, dependencies,
   queue depth, arbitration rule, service-cycle derivation, expected
   result/status digests, and source hashes. Phase 1A is limited to fixture
   extraction, independent oracle verification, and manifest/hash generation;
   it must not execute candidate schedulers. Review and freeze its artifacts
   before separately authorizing Phase 1B. Phase 1B may consume only those
   reviewed, frozen fixtures. Confirm the full source-defined finite case
   counts in §2; no cases may be removed after evaluation starts.
3. Ratify a matched resource budget for the named target (`XC7A100T`, same
   Yosys/nextpnr version and constraints for A/B/C). Report LUT, FF, DSP, and
   BRAM as a vector; do not add incomparable units into a fabricated scalar.
   The draft hybrid gate is: C saves at least one DSP48E1 versus A (necessary,
   not sufficient), remains within +15% LUT and +15% FF of A, uses no
   additional BRAM, and meets the frozen 25 MHz clock constraint. B is
   characterization-only. Report absolute resource counts and deltas,
   including all candidate-specific interface, dispatch, mux, queue, register,
   and scheduler overhead. The one-DSP minimum alone is not an architectural
   success; C must also satisfy the frozen correctness, throughput, and
   deadline gates. Do not label the result “lower total area” using an
   invented scalar over LUT/FF/DSP/BRAM. The owner must ratify or amend these
   thresholds before execution authorization.
4. Ratify cycle-accounting rules, per-resource idle/stall attribution, and the
   deadline policy. The report must identify idle cycles and stall cycles by
   resource and cause, including product lane 0/1, accumulator, ingress,
   internal queue, normalization wait, and arbitration. The two-lane C profile
   must report per-lane utilization; do not infer benefit from its lane count.
   The draft kill gate
   is: reject a sharing profile if it fails exact semantic agreement, has an
   unbounded schedule, misses any sourced latency-critical deadline, falls
   below 90% of A's throughput on any nominated throughput-oriented workload,
   or produces no reduction in a targeted mapped resource after
   candidate-specific overhead is counted. The throughput threshold and
   resource target must be ratified before evaluation.
5. Keep proposed output paths distinct by stage: Phase 1A
   `build/spu_fabric/fabric_0_tracefreeze_01/`; Phase 1B
   `build/spu_fabric/fabric_0_schedule_01/`; Phase 2
   `build/spu_fabric/fabric_0_rtl_01/`; Phase 3
   `build/spu_fabric/fabric_0_a7_01/`.
6. Run only the documentation checks for this Phase 0 contract change:

   ```bash
   python3 tools/doc_audit.py --actual-pass 238
   git diff --check -- spu_strategy/contract_spu_fabric_0_2026-10-15.md
   ```

Phase 0 is complete when the owner has reviewed the three architecture
definitions, workload sources/selection rules, proposed resource thresholds,
throughput threshold, and deadline policy. Record any amendments in this
contract. Report any unmeasurable item as `NOT SPECIFIED`; do not guess. Phase
0 review does not authorize Phase 1 execution.

## 6. Later-Phase Gates (Not Authorized Here)

1. **Phase 1A — Trace preparation and freeze:** under a separate contract and
   owner authorization, extract the complete source-defined finite workloads,
   independently verify oracle outputs, and materialize/hash the manifest and
   fixtures described in §§2 and 4. Do not execute a candidate scheduler.
   Submit the fixtures for independent review. A failed or incomplete fixture
   preparation halts without relaxing the source set or changing its rules.
2. **Phase 1B — Software scheduling:** only after Phase 1A artifacts are
   reviewed and frozen, and under separate owner authorization, compare A/B/C
   using those artifacts. Verify exact digests and deterministic bounded
   schedules. Report modeled latency in cycles, initiation interval, completed
   operations per cycle, stalls, queues, per-resource idle/utilization, and
   modeled deadline misses against sourced cycle limits. These are
   scheduler-model results only; Phase 1B must not report LUT, FF, DSP, BRAM,
   Fmax, routing, or physical deadline evidence. No RTL changes.
3. **Phase 2 — Standalone RTL/Verilator:** implement only surviving profiles;
   compare against independent oracles and Phase 1B schedules. Require a new
   contract with exact module scope and focused verification commands.
4. **Phase 3 — FPGA physical comparison:** synthesize/place/route matched A/B/C
   snapshots for the same XC7A100T constraints. Only this phase can establish
   mapped LUT/FF/DSP/BRAM counts, routed Fmax, and physical timing against
   25 MHz. Use a detached runner and a separate owner-approved
   attempt/timeout/cumulative budget. Report resource vectors and critical
   paths; do not infer integrated CPU/GPU timing from standalone results.
5. **Phase 4 — Integration decision:** require separate review and evidence
   that the existing GPU path and qualified CPU behavior remain protected.

## 7. Stop Conditions and Claim Limits

- Halt if source inspection finds incompatible mathematical semantics,
  unbounded normalization, unknown overflow behavior, or an oracle gap.
- Halt if a candidate cannot preserve input ordering, backpressure, reset,
  acceptance, completion, retirement, error, or tie semantics.
- Halt on source/fixture hash changes after freeze, missing expected outputs,
  nondeterministic trace generation, or unbounded queue/resource demand.
- Do not launch any later phase from this contract. No Phase 0 result can
  establish a silicon advantage, integrated timing, or a general SPU fabric.
- Keep execution sharing separate from representation sharing. D4 memory
  compression and symbolic-state storage are not evidence that arithmetic
  resource sharing is beneficial.

## 8. Review Record

The preliminary review requested clarification of the value of DSP savings,
contention acceptance, evidence levels, and baseline fairness. This amendment
incorporates those points: a single DSP saved is necessary but insufficient;
throughput-oriented hybrid workloads have a proposed 90% of Candidate A
threshold; latency-critical deadlines require a cited source; Candidate A
uses the same external command semantics without an unnecessary global
arbiter; and only Phase 3 may establish mapped resources or routed timing.

The review record also separates Phase 1A fixture preparation from Phase 1B
scheduler evaluation. Phase 1B requires review and freeze of Phase 1A
artifacts plus separate owner authorization. On 2026-10-15, the repository
owner ratified Phase 0, including the proposed workload rules and thresholds:
the 90% per-workload throughput floor, at least one DSP48E1 saved as a
necessary but insufficient condition, +15% maximum LUT/FF overhead, no BRAM
increase, and the 25 MHz physical clock gate. This ratification approves the
study methodology only. On 2026-10-15, the owner authorized Phase 1A. During
preflight, review found that the D4 test checks the invalid flag but deliberately
does not check result bits for signed-16 overflow. The owner approved the
status-only invalid-result policy above. A read-only consistency check
confirmed that the D4 oracle returns no result on overflow, the RTL test
compares output bits only for valid cases, and the proposed fixture schema
records invalid results as undefined. Phase 1A may proceed under its separate
execution contract. No Phase 1B, RTL, synthesis, placement/routing, or
hardware operation is authorized by this review record.
