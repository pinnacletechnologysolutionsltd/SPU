# Engineering Contract: SPU Lossless Scene Storage R1

Date: 2026-10-05
Status: COMPLETE — scoped software checks passed; device equivalence untested.
Roles: Codex authors, implements and audits; no delegation.

## 0. Preflight

Run from the repository root:

```bash
git rev-parse HEAD
git status --short
sha256sum software/experiments/spu_lossless_reduction.py software/tests/test_spu_lossless_reduction.py software/spu_gpu_eval/reference.py examples/gpu/t1d_two_triangle.json examples/gpu/t1d_two_triangle_vertex_b.json
```

Preserve the preflight identity and hashes in the evidence directory. Read
`AGENTS.md`, the R0 codec and its independent vertex-area oracle before edits.

## 1. Scope and invariants

Add only these implementation/test files and this contract:

```text
software/experiments/spu_lossless_storage.py
software/experiments/spu_lossless_reduction_r1.py
software/tests/test_spu_lossless_reduction_r1.py
spu_strategy/contract_spu_lossless_storage_r1_2026-10-05.md
```

Reuse R0 packing, factor extraction, triangle preparation and independent
vertex-area reference. Preserve R0 sources, reports, maintained examples and
all other worktree changes. Use Python 3.10+ standard library and exact integer/
Fraction arithmetic. No RTL, ISA, hardware operations, UART packet edits,
synthesis, dependencies or variable-width execution. Keep each new runtime
module at most 150 lines. This is a host coefficient-storage experiment.

## 2. Freeze the tagged block formats

Store one triangle's nine coefficients, opposite vertices 0/1/2, in each
experiment block. Decoder maximum is 32 values. Begin every representation
with one mode byte; the following format includes its own count:

| Tag | Complete body |
|---|---|
| 0 | uint32 little-endian count, followed by signed int64 values |
| 1 | uint32 count, followed by signed fields repeating 16/16/32 bits for a/b/c |
| 2 | Complete R0 Candidate-A encoding, including its count and width bytes |
| 3 | Positive uint64 factor followed by complete Candidate-A reduced coefficients |

Use little-endian byte order, positive factors and canonical R0 encoding.
Reject invalid types/ranges, count above 32, unknown tags, truncation, padding,
trailing bytes, zero/noncanonical factors and reconstructed int64 overflow.
Reject tag 1 encoding when a coefficient exceeds its assigned field range.
Select the smallest eligible complete tagged encoding; break ties by lowest
tag. Tag 0 is always eligible for accepted int64 inputs. Selection does not
require a compression or speed win. Compare raw renderer coefficient fields
separately from tagged/count-bearing storage; nine raw fields occupy 24 bytes.
Do not equate either coefficient comparison to the current 64-byte GPU packet.
Depth, colour, scene metadata and packet framing are outside these byte totals.

## 3. Freeze corpus and correctness

Use seed 13, twelve hand-designed synthetic scene shapes and twenty-four
seeded synthetic scenes, each with two triangles, plus the two existing T1d
JSON examples when available. Label synthetic versus maintained inputs.
Include tiny/large triangles, translations, reversed windings, depth limits,
depth ties, shared factors, coprime/sliver coefficients, clipped/background
geometry and large host-only coordinates. Reject degeneracy and any int64
coefficient overflow. Report renderer field ineligibility explicitly.
Save the generated corpus and its hash; do not claim statistical
representativeness or workload frequency from these designed cases.

Reconstruct every eligible mode and automatically selected block exactly.
Check selection against independently computed byte-count formulas. Include
fixed fallback, packed and factored winners, ties, all-zero blocks, signed
endpoints and malformed streams. Compare coverage, exact depth and overlap
winners with the independent vertex-area oracle on selected scenes. Check
the full 640x480 awkward scene and a 16-pixel grid plus vertex/boundary samples
for six other named synthetic/maintained scenes. Geometry consumes reconstructed
original coefficients, never uncompensated reduced tuples.

## 4. Freeze timing and reporting

Run correctness first; stop and preserve failures before timing. Separately
measure encode/decode with `perf_counter_ns()`, five trials and 100 repetitions
per eligible corpus block for each fixed mode and automatic selection. Record
both the whole int64 corpus and the common renderer-field-eligible cohort.
Perform eligibility and encoded-stream construction outside the timed loops.
Record
integer trial totals, block/value/byte counts, median totals and exact ratios
for nanoseconds per block. Include validation/canonicality in strict decode;
automatic encode includes candidate construction and selection. Do not subtract
loop overhead or characterize these Python measurements as FPGA costs.

Write fresh evidence below `build/spu_lossless_reduction/r1_20261005/` containing
`corpus.json` and `results.json`: source/input hashes, HEAD/dirty identity,
correctness counts/failures, complete sizes and exclusions, timing, frozen
limits, `hardware_operations=0`, `device_equivalence_tested=false` and
`DEVICE_EQUIVALENCE_NOT_TESTED`. Preserve size expansion and costly decoding
as valid findings. Refuse an existing output directory.

## 5. Scoped commands and stop conditions

```bash
timeout 60s python3 software/tests/test_spu_lossless_reduction_r1.py
timeout 60s python3 software/experiments/spu_lossless_reduction_r1.py --out build/spu_lossless_reduction/r1_20261005/run_01
git diff --check -- software/experiments/spu_lossless_storage.py software/experiments/spu_lossless_reduction_r1.py software/tests/test_spu_lossless_reduction_r1.py spu_strategy/contract_spu_lossless_storage_r1_2026-10-05.md
python3 tools/doc_audit.py --actual-pass 238
```

Perform a syntax/whitespace scan for these new untracked files. These are the
R1 isolated-experiment checks: production arithmetic kernels, RTL and shared
verification infrastructure are untouched. This contract does not change the
repository gate policy or authorize unrelated synthesis. Each correctness/
experiment command has a frozen 60-second limit and one initial attempt.
Do not rerun or increase a timeout after TIMEOUT. A prospective software
correction may receive one focused check in a fresh evidence path; retain the
original failure. Halt on accepted invalid data, reference coupling, coefficient
loss, unsupported-input truncation or a request for physical execution.

## 6. Execution record

Read [results.json](../build/spu_lossless_reduction/r1_20261005/run_01/results.json)
and [corpus.json](../build/spu_lossless_reduction/r1_20261005/run_01/corpus.json).
The evidence directory retains preflight hashes/status, both command logs,
integer-nanosecond command durations and the active contract snapshot.

| Gate | Result |
|---|---|
| R1 correctness command, external 60-second bound | COMPLETE, exit 0; 5 tests; 9.785 seconds |
| R1 experiment command, external 60-second bound | COMPLETE, exit 0; 23.562 seconds |
| Exact coefficient reconstruction | PASS; 76 blocks, 300 eligible-mode round trips |
| Strict malformed streams | PASS; 82 rejections |
| Independent selected-scene geometry | PASS; 314,552 points, 629,104 triangle samples |
| Source/input/corpus hashes | Match recorded artifacts; inspected R0 sources and examples unchanged |
| New-file syntax/whitespace and scoped diff check | PASS |
| Documentation audit | Exit 0; existing tracked-document inventory unchanged; new contract reviewed directly |

The corpus contains 36 synthetic scenes and two maintained examples. Four
blocks exceed renderer coefficient field ranges. Among the remaining 72 blocks,
complete tagged int64/fixed-renderer/packed/factored sizes total
5544/2088/1926/2448 bytes. Automatic selection also totals 1926 bytes: 29 fixed
renderer blocks and 43 packed blocks; no factored blocks. Fixed selections
tie packing in byte size and win by the frozen tag rule. Raw renderer coefficient
fields total 1728 bytes; the selected representation includes block framing.

On the common 72-block cohort, median strict decode time per block is about
8.481 microseconds for fixed renderer fields, 22.164 for packed, 32.031 for
factored and 16.784 for automatic selection. Automatic encode costs about
52.351 microseconds per block versus 6.474 for fixed renderer fields. Exact
integer trial totals and ratios are retained in the report. These are Python
costs on the recorded host. Correctness passed without a size or speed condition.

Retain the codec as an experiment. The measured gain over complete tagged
renderer fields is 7.8%, while selected storage exceeds raw fields by 11.5% and
strict decoding costs about twice as much. Production integration is deferred.
Hardware operations: 0. Device equivalence tested: false.
