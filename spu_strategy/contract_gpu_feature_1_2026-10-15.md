# Engineering Contract: GPU-FEATURE-1 Task-Sensitive Spatial Refinement
**Date:** 2026-10-15
**Contract ID:** `contract_gpu_feature_1_2026-10-15.md`
**Status:** DRAFT — REVIEW REQUIRED

**Roles:**
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Repository owner / assigned implementer
- **Integration Auditor:** Repository owner / focused offline GPU evaluator gates

## 1. Objective and Scope

Measure how much task-relevant information is recovered by adding bounded
within-tile spatial descriptors to the existing GPU-SOM-0A observation
payload. Preserve the completed GPU scene-diversity evaluation as an immutable
baseline and negative control.

The selected task output is the per-pixel tuple `(covered_by, winner, RGB444)`
for the existing two-triangle T1d profile. Exact rational depth is retained in
the independent reference artifacts, but depth-only differences do not define
task-output inequality in this study.

Proposed files after review and separate implementation authorization:

- `examples/gpu/feature_1/` — frozen scene suite and manifest.
- `fixtures/gpu_feature_1_reference.json` — independent per-pixel task maps,
  fixture expectations, and suite declarations.
- `fixtures/gpu_feature_1_source_lock.json` — frozen evaluator/source hashes.
- `software/spu_gpu_eval/feature_1.py` — deterministic descriptor evaluation.
- `software/spu_gpu_eval/feature_1_artifacts.py` — hash checks and report
  assembly.
- `software/spu_gpu_eval/feature_1_publish.py` — atomic output publication.
- `software/tests/test_gpu_feature_1.py` — focused scene, descriptor, oracle,
  collision, cost, and publication tests.
- `docs/gpu_feature_1_2026-10-15.md` — exact results and evidence limits.
- `software/spu_gpu_eval/cli.py` — `feature-1` subcommand only.

Do not modify GPU-SOM-0A, the completed scene-diversity evaluator or its
fixtures/results, renderer/device-model behavior, GPU RTL, SOM, Soul, D4/E8,
or hardware. This study does not train a SOM or claim that a descriptor is a
useful learned representation.

## 2. Frozen Baseline and Scene Suite

Reuse the six frozen scenes from
`examples/gpu/scene_diversity/manifest.json` as the development/control set.
Add exactly 12 new valid scenes under `examples/gpu/feature_1/heldout/` before
evaluation. Freeze all 18 scene inputs, expected sample coordinates, the
reference maps, and hashes before launching the evaluator.

The 12 held-out scenes must include, with at least two scenes per category:

1. Integer translations that remain inside one 16×16 tile.
2. Translations that cross a 16×16 tile boundary.
3. Partial overlap with each triangle as the depth winner.
4. Equal-depth overlap and a shared-RGB control.
5. Different geometry with equal tile-level aggregate statistics, when
   constructible under the frozen T1d profile.

All scenes must use the existing parser, packet compiler, and
`t1d-two-triangle-v1` profile. Do not alter the profile to force a desired
collision. Record the construction rationale before computing evaluator
results. If a named case cannot be constructed, halt and document the
obstruction; do not replace it after hashes are frozen.

The `disjoint_a`/`disjoint_b` collision from the completed scene-diversity
study must appear unchanged as the required positive control. Verify its
fixture hashes against the prior frozen manifest and its output artifacts
against `build/gpu_evaluation/scene_diversity_01/`. Do not regenerate or
overwrite that prior output.

The completed study's primary result artifacts are frozen by these hashes:

| Artifact | SHA-256 |
|---|---|
| `build/gpu_evaluation/scene_diversity_01/report.json` | `15dfff817a5b1a5b868d3f13a6e8c3f89ffd9716f27c9e9e640ab4eed3275dc5` |
| `build/gpu_evaluation/scene_diversity_01/collision_report.json` | `853112538f1ba9107344081acb1274bdf481d43bc37bb586585e7a336ce99cd8` |
| `build/gpu_evaluation/scene_diversity_01/manifest.json` | `067731e3a3e475fb85a6c177fe3adf974ce835474c8e585ac8f7b80800386806` |

## 3. Descriptor Variants

For each 16×16 tile, compare these four variants using identical device-model
task decisions:

| ID | Representation | Definition |
|---|---|---|
| B0 | Existing observer | The canonical GPU-SOM-0A `tile_features.json` payload. |
| B1 | 4×4 spatial task histograms | Divide each tile into sixteen 4×4-pixel cells. In each cell, store a canonical histogram of the per-pixel task tuple `(covered_by, winner, RGB444)`. |
| B2 | 8×8 spatial task histograms | Divide each tile into sixty-four 2×2-pixel cells and store the same canonical task-tuple histograms. |
| B3 | Exact tile task map | Store all 256 per-pixel task tuples in row-major order. This is the lossless task-output reference, not an expected compression win. |

For B1 and B2, sort histogram entries by the canonical task-tuple encoding;
omit zero-count entries; encode counts as unsigned integers; include the
subtile coordinates and descriptor version. For B3, use a fixed 16-bit
encoding per pixel: `covered_by` bit mask (2 bits), winner (`triangle0`,
`triangle1`, or `none`, 2 bits), and RGB444 (12 bits). Reject values outside
the supported profile rather than truncating them.

Canonical serialization must be deterministic. Report both canonical payload
bytes and operation counts for descriptor generation. Report the exact byte
count of each complete frame representation, including the B0 payload and
all added descriptor fields, but excluding provenance metadata. Do not use
compression libraries or trainable codebooks. Operation accounting must
report separate counters, not a composite total: source pixel reads, task-tuple
encodings, histogram insert/increment operations, histogram key comparisons
used for canonical sorting, B3 packed-word writes, and serialized payload
bytes. Count each counter exactly where the corresponding operation occurs in
the reference implementation; do not infer hardware cycles or energy.

## 4. Independent Evaluation and Metrics

Generate device observations through the existing finite-width device model.
Generate task maps independently through `reference.pixel_decision`. Keep
device/oracle disagreements visible in the report; do not correct either path
to make them agree.

For each of B0–B3, compare every unordered scene pair using byte equality of
the complete canonical frame representation. For each pair, compare the
independent ideal task maps over `(covered_by, winner, RGB444)` and record
whether they are equal and the differing-pixel count.

Report separately:

1. Task-relevant false merges: equal representation, unequal ideal task maps.
2. Task-equivalent false splits: unequal representation, equal ideal task maps.
3. Representation bytes per frame and bytes added over B0.
4. Descriptor-generation operation counts, with counting rules frozen before
   evaluation; do not combine dimensions into a composite score.
5. Per-scene and pairwise hashes, device/oracle disagreement counts, complete
   coordinate coverage, and deterministic replay hashes.

The minimum correctness gates are: all frozen scenes parse and packet-compile;
all pixel coordinates occur exactly once; outputs replay byte-identically;
B3 reconstructs every selected device task tuple exactly; and B3 has no
task-relevant false merges over the finite suite. A B1/B2 false merge is a
measured result, not an automatic study failure. No minimum advantage is
required of B1 or B2.

## 5. Implementation and Focused Verification

After technical review and separate repository-owner implementation
authorization:

1. Add the 12 held-out scenes, analytical fixture rationale, independent
   reference maps, and suite manifest. Freeze hashes before evaluator runs.
2. Implement B1–B3 in `feature_1.py`, reusing the existing observer and
   device-model APIs. Do not duplicate or alter GPU-SOM-0A extraction.
3. Implement frozen-hash preflight and result assembly in
   `feature_1_artifacts.py`; publish only through atomic staging in
   `feature_1_publish.py`.
4. Add the `feature-1` CLI command and focused tests for canonical encoding,
   all descriptor levels, task-map equality, false merges/splits, bounds,
   deterministic replay, hashes, and publication failure cleanup.
5. Run, in order:

   ```bash
   python3 software/tests/test_gpu_feature_1.py
   python3 software/tests/test_gpu_scene_compiler_s1.py
   python3 software/tests/test_gpu_device_model_s2.py
   python3 software/tests/test_gpu_pixel_inspect_s3.py
   python3 -m software.spu_gpu_eval.cli feature-1 --suite examples/gpu/feature_1/manifest.json --out build/gpu_evaluation/feature_1_01
   python3 tools/doc_audit.py --actual-pass 238
   git diff --check -- <changed paths>
   ```

6. Record all commands, source/fixture hashes, output hashes, measured results,
   and unrun claims in `docs/gpu_feature_1_2026-10-15.md`.

## 6. Evaluation Launch Budget (Proposed; Not Authorized)

The evaluator processes 18 scenes. Use a detached runner if the measured
focused test or evaluator preflight indicates execution may exceed 60 seconds.
Proposed allocation: one attempt, 600-second per-attempt timeout, 600-second
cumulative campaign budget, no automatic retries, no hardware/FPGA operations.

Proposed runner evidence root: `build/gpu_evaluation/feature_1_runner_01/`.
Evaluator output: `build/gpu_evaluation/feature_1_01/`.
Both paths must be absent before launch. Exact proposed invocation:

```bash
tools/run_detached_job.sh --output build/gpu_evaluation/feature_1_runner_01 --timeout 600 --notify-desktop -- python3 -m software.spu_gpu_eval.cli feature-1 --suite examples/gpu/feature_1/manifest.json --out build/gpu_evaluation/feature_1_01
```

Before launch, record owner authorization, verify every frozen source and
fixture hash, verify the prior scene-diversity evidence hashes, and confirm
both output paths are absent. Launch once only. A launched attempt consumes
the full allocation regardless of result. Do not retry, extend the timeout,
or change the evaluation without renewed authorization. Interpret the result
only after exactly one durable `COMPLETE`, `FAILED`, or `TIMEOUT` marker.

No implementation or evaluation authorization is implied by this draft.

## 7. Stop Conditions and Claim Limits

- Halt on any source/fixture hash mismatch, missing prior evidence, occupied
  output path, invalid fixture, or device/oracle disagreement hidden by the
  evaluator.
- Halt on incomplete or duplicate pixel coordinates, nondeterministic output,
  serialization ambiguity, overflow/truncation, or non-atomic publication.
- Do not change the frozen scene-diversity result or the GPU-SOM-0A observer.
- Do not add SOM learning, Soul integration, symmetry transforms, GPU feedback,
  RTL, FPGA builds, or physical hardware operations.
- A passing result establishes only the measured information/cost properties
  of B0–B3 on this frozen 18-scene T1d suite. It does not establish general
  scene sufficiency, a SOM advantage, compression benefit, hardware efficiency,
  or renderer improvement.
