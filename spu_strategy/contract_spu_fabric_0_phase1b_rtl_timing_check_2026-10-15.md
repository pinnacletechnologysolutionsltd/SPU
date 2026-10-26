# SPU-FABRIC-0 Phase 1B RTL Timing Confirmation

**Status:** DRAFT — REVIEW AND OWNER AUTHORIZATION REQUIRED
**Scope:** Focused software RTL simulation only; no scheduler or FPGA work
**Purpose:** Independently compare selected frozen Surd timing cases with the
source-derived cycle reference before Phase 1B scheduler evaluation.

## 1. Frozen inputs and source identity

The checker reads `fixtures/spu_fabric_0/manifest.json`, validates all three
Phase 1A trace hashes, and requires selected cases to match across
`isolated`, `burst_synthetic`, and `steady_synthetic`. It selects these
frozen cases:

| Width | Operation ID | Source-derived latency | Check |
| ----- | ------------ | ---------------------: | ----- |
| W32 | `surd_w32:min_negation_overflow` | 107 cycles | Normalization checkpoint |
| W32 | `surd_w32:random_0046` | 237 cycles | Frozen-fixture maximum |
| W32 | `surd_w32:zero_denominator_a` | 0 cycles | Invalid status/path; result is prior destination |
| W32 | `surd_w32:zero_overflow_canonical_rescue` | 3 cycles | Zero-numerator normalization bypass |
| W32 | `surd_w32:unsigned_denominator_max_fit` | 1 cycle | Raw-fit boundary |
| W64 | `surd_w64:min_negation_overflow` | 203 cycles | Minimum-signed-value normalization boundary |
| W64 | `surd_w64:random_0137` | 467 cycles | Frozen-fixture maximum |
| W64 | `surd_w64:zero_denominator_a` | 0 cycles | Invalid status/path; result is prior destination |
| W64 | `surd_w64:zero_overflow_canonical_rescue` | 3 cycles | Zero-numerator normalization bypass |
| W64 | `surd_w64:unsigned_denominator_max_fit` | 1 cycle | Raw-fit boundary |

For defined valid results, the checker requires the RTL harness's measured
single-vector latency to equal the source-derived value. For zero-denominator
cases, the existing harness checks invalid status, no normalization, and
preservation of the destination. It does not expose a numeric invalid-path
latency in its summary; the zero-cycle classification therefore remains
source/edge-derived and must not be reported as an independently sampled
latency.

The harness calls `issue_seed` before every vector. That task performs the
frozen multiply with operands `(a,b,d,c,e,f)=(17,-19,23,1,0,1)`, then checks
that the visible destination is `(17,-19,23)`. The checker now requires each
selected trace row's `initial_state.destination` to equal that seeded value.
It writes the frozen expected final `result` into the harness's expected
output columns; it rejects invalid or overflow rows unless that result equals
the frozen initial destination. Thus the held-destination assertion is checked
against the state actually produced by the harness seed, rather than merely
against profile-to-profile equality.

Before inspecting any command return code, the runner saves the exact command,
stdout, stderr, and return code in per-command files. It writes `result.json`
with `RUNNING` before compiling and updates it after each command and case; on
an exception it records `FAILED` and the failure text before exiting. Failed
compile and VVP diagnostics therefore remain available within the attempt.

The checker also recomputes each width's maximum across all 327 frozen Surd
cases and requires the selected maximum row and value to match. It uses the
existing `surd_mul_normalizer_vectors_harness.v` with `LANES=5`; it does not
modify the frozen Phase 1A harness or any RTL source.

### Pinned inputs

| Input | SHA-256 |
| ----- | ------- |
| `fixtures/spu_fabric_0/manifest.json` | `24e7e35204baa8ee1e44a1cb09f788073a2bf721045190acb2a120ad1081ca13` |
| `traces/isolated.jsonl.gz` | `18585af72c7f65b4767e0526890424e56218af9eb20a6dbf90d943bf30c8a440` |
| `traces/burst_synthetic.jsonl.gz` | `4db6e7458794b4a36f07d2cfd29a135f4301fb1a9e46ec73f77dc7f5b1060067` |
| `traces/steady_synthetic.jsonl.gz` | `64359fdf2079299bbc1bfe95fe1b439f601084be288b62c9ace234dd5c4f3844` |
| `software/experiments/spu_fabric_0_timing_reference.py` | `80b753da559a19b4a3fc3dada6829806846b74449513040bc52adfdc516a603d` |
| `software/experiments/spu_fabric_0_rtl_timing_check.py` | `ea616e25eb2b2e6e10dfc87698118e9c83c11856d68751b43581f35284eeffcd` |
| `hardware/tests/math/surd_mul_normalizer_vectors_harness.v` | `31ce5470a8b8f565e607b3452123e4f04ff927773970fa7a73a51880c6a4eaa0` |
| `hardware/rtl/math/surd_smul_unit.v` | `0cebd08aec2cd9ea6603ae655b9a15d65d9651eca958e1935137bd6deb04fdaa` |
| `hardware/rtl/math/surd_normalize_unit.v` | `4d43e03f3745326a3f7d26fcf7a34219c8bc0ba1a4826a568eb3c74ab82291fa` |
| `hardware/rtl/math/surd_binary_gcd3.v` | `e994552b50f34017b176d91303ac6c85774748d64d4014755d0979d6fcd3097c` |
| `hardware/rtl/math/surd_exact_quotient.v` | `2a78246d9ab13d439ee0be88b57dd58029d1d5ed0e77fcd61d1bac4837fd15cd` |

## 2. Exact bounded execution proposal

This is a new authorization gate for RTL simulation; prior Phase 1B scheduler
authorization does not authorize this run.

- Attempts: 1 maximum.
- Per-attempt timeout: 120 seconds.
- Cumulative campaign budget: 120 seconds.
- Automatic retries: none.
- Execution: detached runner, with durable terminal marker and notification
  attempt.
- Hardware: none. No synthesis, placement, routing, programming, or board I/O.
- Output directory: `build/spu_fabric/fabric_0_phase1b_rtl_timing_20261015/`.
- Runner evidence: `<output>/runner/`.
- Checker artifacts: `<output>/artifacts/`.
- Required output: `artifacts/result.json`, one result per selected case,
  per-command invocation/stdout/stderr/return-code files, input hashes,
  source hashes, and observed latency for valid paths. Partial results remain
  available if a command or comparison fails.

Before launch, verify the output path is absent and all pinned hashes match.
The exact authorized invocation would be:

```bash
tools/run_detached_job.sh \
  --output build/spu_fabric/fabric_0_phase1b_rtl_timing_20261015/runner \
  --timeout 120 \
  --notify-desktop \
  -- python3 software/experiments/spu_fabric_0_rtl_timing_check.py \
    --output-dir build/spu_fabric/fabric_0_phase1b_rtl_timing_20261015/artifacts
```

Exactly one terminal marker must be present before interpreting the run.
Timeout, failure, unavailable evidence, hash mismatch, missing case, malformed
summary, RTL/oracle disagreement, or latency mismatch consumes the one attempt
and halts this qualification. No retries, timeout extensions, or alternate
commands are authorized by this draft.

## 3. Pass criteria and evidence boundary

PASS requires all pinned hashes to match, the same selected rows to exist in
all three frozen profiles, the checker to verify the selected full-fixture
maxima, all ten harness invocations to pass their output/status checks, and
all eight valid-path observed latencies to equal their source-derived values.
The two invalid-denominator rows must report invalid status and no
normalization; their latency remains source-derived rather than independently
sampled.

This packet can qualify selected intrinsic RTL timings. It cannot qualify a
general latency bound by sampling alone, validate Candidate B/C timing, compare
resource sharing, or authorize the Phase 1B scheduler. The scheduler remains
held until the timing and schedule packets are independently reviewed and the
separate Phase 1B execution contract is frozen and authorized.

## 4. Candidate C schedule amendment

The accompanying schedule draft proposes C2: independent, dedicated W32 and
W64 Surd final reducers, each with one-cycle latency and initiation interval
1, while retaining shared product lanes. The schedule also makes W32 and W64
normalization/control independently dedicated, with no cross-width arbitration
or free shared normalizer. These choices resolve the model's resource identities
but remain pending independent review and freeze. They are not evidence of
physical area, timing, or implementation feasibility.
