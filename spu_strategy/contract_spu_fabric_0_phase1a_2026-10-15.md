# Engineering Contract: SPU-FABRIC-0 Phase 1A Trace Preparation
**Date:** 2026-10-15
**Contract ID:** `contract_spu_fabric_0_phase1a_2026-10-15.md`
**Status:** OWNER-AUTHORIZED — TRACE PREPARATION ONLY
**Parent:** `contract_spu_fabric_0_2026-10-15.md`

## 1. Exact Scope

Create `tools/prepare_spu_fabric_0_traces.py` and the single-purpose data,
serialization, and manifest modules under `software/experiments/` to extract,
independently check, serialize, hash, and atomically publish the complete
frozen workloads defined by the parent Phase 0 contract. Verify all inputs
against `spu_strategy/spu_fabric_0_phase1a_sources_2026-10-15.sha256` before
and after generation. Generate the trace manifest at
`fixtures/spu_fabric_0_trace_manifest.json` and compressed canonical trace files
`traces/isolated.jsonl.gz`, `traces/burst_synthetic.jsonl.gz`, and
`traces/steady_synthetic.jsonl.gz` under `fixtures/spu_fabric_0/`. Save a
machine-readable generation result and source/configuration hashes under
`build/spu_fabric/fabric_0_tracefreeze_01/`.

Do not implement or execute candidate schedulers, Verilator, RTL, synthesis,
placement/routing, or hardware. Do not modify the parent workload scope or
thresholds. Phase 1B remains unauthorized.

## 2. Frozen Inputs and Exact Trace Rules

Read only these parent-contract sources and their direct mathematical oracle
dependencies:

- Surd: `software/experiments/surd_wide_correctness_vectors.py`,
  `software/tests/test_surd_wide_rtl_vectors.py`,
  `hardware/tests/math/surd_mul_normalizer_vectors_harness.v`,
  `hardware/rtl/math/surd_smul_unit.v`,
  `hardware/rtl/math/surd_normalize_unit.v`,
  `hardware/rtl/math/surd_binary_gcd3.v`,
  `hardware/rtl/math/surd_exact_quotient.v`.
- D4: `software/tests/test_d4_reflection_rtl.py`,
  `software/tests/test_d4_reflection_oracle.py`,
  `hardware/rtl/math/spu_d4_reflection_unit.v`.
- SOM: `software/tests/test_spu4_som_edge_oracle.py`,
  `software/lib/spu4_som_edge_oracle.py`,
  `software/lib/rational_som.py`,
  `hardware/rtl/core/spu4/spu4_som_edge.v`,
  `hardware/tests/spu4/spu4_som_edge_full_chain_tb.v`.

Include all 327 Surd cases at W=32 and W=64, all 288,132 D4 cases in source
order, and all eight SOM queries with the exact four-node/four-feature fixture.
Use stable source case IDs, exact initial state, read/write sets, empty
predecessors for these independent source cases, and the expected values
defined by the parent contract. Run the Surd rational consistency checks;
cross-check every D4 formula result and invalid status against the specialized
independent oracle; verify all SOM answers against the exact BMU oracle and
the fixture's declared expected pairs. Any disagreement halts publication.

For D4 overflow, serialize `invalid=true`, `result_defined=false`,
`result=null`; include status and the definedness marker in the expected digest
and exclude result bits. For valid D4 rows, serialize the complete exact
result. Never copy the RTL's wrapped invalid output into an expected value.

Use three deterministic profiles:

1. `isolated`: one client stream at a time, one offered operation per cycle;
   stream order is Surd W32, Surd W64, SOM, D4.
2. `burst_synthetic`: all mixed clients begin at cycle 0; each client offers
   its next source-ordered operation every cycle.
3. `steady_synthetic`: the same mixed source cases, with each client offering
   its next source-ordered operation every 8 cycles.

Mixed client order for canonical serialization is `surd_w32`, `surd_w64`,
`som`, `d4`; equal-cycle serialization order does not define scheduler
priority. All profiles are synthetic throughput workloads with no sourced
real-time deadline. Record deadlines as `NOT SPECIFIED` and make no real-time
claim. Use four external ingress entries per client and zero additional
candidate-internal request queue entries for A, B, and C. Keep the parent
contract's candidate-independent offered cycles. Candidate A dispatches
directly to independent units without a global arbiter. Candidates B and C
use work-conserving round-robin arbitration over ready shared-product clients
in the fixed rotation `surd_w32`, `surd_w64`, `som`, initially pointing at
`surd_w32`; C selects up to two ready clients per cycle, advancing the
rotation after each selection. D4 remains on its dedicated path. Trace
serialization order is not arbitration priority. Record source operation
counts (five products per Surd multiply; two squares per feature for each of
four SOM nodes; one D4 reflection). Exact candidate service-cycle latencies,
including variable normalization latency, are `NOT SPECIFIED` in Phase 1A and
must be derived and frozen in the separate Phase 1B contract before scheduler
comparison.

Each operation record contains `profile`, stable `operation_id`,
`source_case_id`, `client`, `client_order`, `offered_cycle`, `operation`,
`operands`, `initial_state`, `read_set`, `write_set`, `predecessors`, and
`expected`. Canonical JSON uses UTF-8, sorted keys, compact separators, and one
LF per record. Gzip streams use `mtime=0` and an empty embedded filename.
Manifest source hashes cover every listed source plus all generator files and
the frozen source-lock file. Trace hashes cover each final compressed trace
and the canonical expected-value stream.
Record Python and zlib versions, profile parameters, complete case counts,
candidate profiles, ingress/queue capacities, and all digests.

## 3. Publication and Stop Conditions

Refuse to run if any requested final path exists. Build all artifacts in
private staging paths on the same filesystem. Verify exact counts, oracle
checks, deterministic ordering, hashes, and manifest/file consistency before
publication. Publish only complete fixtures and manifests. On a handled
failure, remove staging and any newly published fixture/manifest paths, but
preserve the build evidence directory with a `FAILED` or `TIMEOUT` result
marker. Never overwrite or clean up pre-existing paths.

Halt on missing source cases, invalid/duplicate IDs, oracle mismatch, a changed
source during generation, D4 invalid-result bits entering a digest, a hash or
count mismatch, a non-deterministic serialization, or publication failure.
Do not relax a fixture or regenerate after a failure under this authorization.

## 4. Authorized Command and Evidence

Maximum attempts: 1. Execution timeout: 55 seconds. No retries.

Preflight commands:

```bash
test ! -e fixtures/spu_fabric_0
test ! -e fixtures/spu_fabric_0_trace_manifest.json
test ! -e build/spu_fabric/fabric_0_tracefreeze_01
sha256sum -c spu_strategy/spu_fabric_0_phase1a_sources_2026-10-15.sha256
```

Execute exactly once:

```bash
timeout 55s python3 -B tools/prepare_spu_fabric_0_traces.py --evidence-dir build/spu_fabric/fabric_0_tracefreeze_01
```

The generator self-checks all listed oracles and fixtures. After completion,
verify the result marker is `COMPLETE`, exit status is zero, all frozen source
hashes still match, the three final paths exist, and every manifest hash and
case count matches its artifact. These are Phase 1A trace-freeze checks only;
do not run scheduler or hardware checks.

One launched attempt consumes the authorization regardless of outcome. On
timeout or failure, preserve evidence and stop; no automatic retry or budget
extension is authorized.
