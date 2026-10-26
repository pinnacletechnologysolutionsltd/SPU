# Engineering Contract: GPU-SOM-0A Deterministic Observer
**Date:** 2026-10-14
**Contract ID:** `contract_gpu_som_0a_2026-10-14.md`
**Status:** COMPLETE — SOFTWARE REFERENCE MILESTONE

**Roles:**
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Assigned implementer after contract review
- **Integration Auditor:** Repository owner / focused offline GPU evaluator gates

## 1. Objective & Scoped Files

Build a software-only observer that converts the existing finite-width T1d
pixel decisions into deterministic, bounded 16×16 tile records. The
authoritative image oracle is the existing `device-preview` path: observer
output must contain byte-identical device-model image data produced from the
same prepared scene and finite-width pixel decisions. The ideal `preview` path
is a separate regression check and is not a substitute for device-model
parity. The observer is a sidecar: it does not change rendering, pixel
decisions, or scene state. This stage records features only; it does not train
or run a SOM.

**Target files to add or modify:**
- `software/spu_gpu_eval/observer.py` (new)
- `software/spu_gpu_eval/observer_artifacts.py` (new; provenance and atomic publication)
- `software/spu_gpu_eval/cli.py` (add `observe` command)
- `software/tests/test_gpu_som_0a_observer.py` (new)
- `docs/gpu_som_0a.md` (new usage and evidence-boundary note)

**Frozen inputs:**
- `examples/gpu/t1d_two_triangle.json`
- `examples/gpu/t1d_two_triangle_vertex_b.json`
- `fixtures/gpu_t1d_scene_reference.json`
- Source and fixture hashes recorded in the run manifest before evaluation.

Do not modify these inputs, their existing reference outputs, the GPU RTL,
the Soul-0 studies, D4 studies, SOM models, or existing GPU evidence.

## 2. Exact Feature Contract

Use only values exposed by `software.spu_gpu_eval.device_model.pixel_decision`
and its finite-width prepared scene:

- Pixel coverage state: `background`, `triangle0`, `triangle1`, or `overlap`.
- Covered primitive identifiers from `covered_by`.
- Selected primitive identifier from `winner`.
- Output RGB444 tuple from `rgb`.
- Finite-width depth `value` for each covered primitive in `depths`.

For each 16×16 tile, emit one record containing:

- Tile origin `(tile_x, tile_y)` and `sample_count=256`.
- Counts for all four coverage states.
- Covered-pixel counts and winner counts for primitive IDs 0 and 1.
- A sorted histogram of output RGB444 tuples and their pixel counts.
- Per-primitive minimum and maximum observed finite-width depth values; use
  JSON `null` for both bounds when that primitive has no covered samples.

Use row-major tile order, then row-major pixel order. Serialize JSON with
sorted object keys, compact separators, UTF-8, and one final newline. The
scene profile has 640×480 pixels, so a complete observation contains exactly
1,200 tile records. Reject any other tile size or record count in this
contract version.

## 3. Invariants & Hard Constraints

- [ ] **Observer isolation:** Run observation after the device-model image is
  produced. The observer must not mutate the prepared scene or rendered bytes.
- [ ] **Rendering parity:** Image bytes and their SHA-256 hashes are identical
  whether the observer is called or omitted.
- [ ] **Determinism:** Repeated extraction and serialization for identical
  source bytes produce byte-identical feature records.
- [ ] **Generated-mode completeness:** GPU-SOM-0A supports generated mode
  only. Generate the complete 640×480 coordinate grid, call the finite-width
  device-model pixel-decision function exactly once per coordinate, and track
  coordinate coverage so every coordinate appears exactly once. Any missing,
  duplicate, out-of-bounds, or invalid decision fails the run; never replace
  it with a zero-valued sample. This contract does not define or claim
  completeness validation for an externally supplied observation stream.
- [ ] **Bounded telemetry:** Allocate capacity for exactly 1,200 records. On
  overflow, fail without truncating or publishing partial artifacts.
- [ ] **Empty-tile semantics:** Emit all 256 samples as background, zero
  primitive counts, an RGB444 histogram containing only `[0,0,0]` with count
  256, and null depth bounds for both primitives.
- [ ] **No learned feedback:** No SOM BMU, prototype, adaptation, or learned
  state may affect extraction or renderer decisions.
- [ ] **No hardware claims:** This is an offline software-model observation;
  it is not a physical GPU telemetry path or silicon result.
- [ ] **No frozen evidence edits:** Write new outputs only to a fresh directory
  under `build/gpu_evaluation/gpu_som_0a/`.

## 4. Step-by-Step Implementation Instructions

Commands are repository-root commands. Each command writes only a new source
or documentation file listed in §1; generated outputs go only under
`build/gpu_evaluation/gpu_som_0a/`.

1. Add `software/spu_gpu_eval/observer.py` with pure feature-extraction and
   tile aggregation functions over the finite-width prepared scene. Enumerate
   the 640×480 pixel grid using `device_model.pixel_decision`, aggregate the
   §2 fields, and reject incomplete or out-of-profile input.
2. Add `software/spu_gpu_eval/observer_artifacts.py` for provenance, artifact
   validation, and deterministic atomic publication. Before
   creating a staging directory, reject an existing destination or symlink
   without modifying it. Create a private staging directory under the same
   parent filesystem as the destination. On success, verify coordinate
   coverage, tile count, sample count, feature and preview hashes, and
   manifest/hash consistency, then atomically rename the complete staging
   directory to the destination. On any failure, remove the private staging
   directory. If the destination was absent at invocation, leave it absent; if
   it already existed, preserve it unchanged and publish nothing.
3. Add `observe <scene.json> --out <new-directory>` to
   `software/spu_gpu_eval/cli.py`. The command must use the same prepared scene
   and finite-width pixel decisions as `device-preview`, and produce
   byte-identical device-model image data plus a `tile_features.json` sidecar.
   Include a manifest with input, feature, and preview hashes and explicit
   `device_model=true` / `physical_observation=false` fields.
4. Add `software/tests/test_gpu_som_0a_observer.py` covering both frozen
   scenes, exact aggregation against independently accumulated pixel
   decisions, empty tiles, generated-grid coordinate completeness and
   invalid decisions, capacity overflow, stable serialization, existing
   destination refusal, atomic failure cleanup, and byte/hash parity with the
   ordinary `device-preview` path using the same prepared scene. Shuffle the
   256 observations within each test tile and verify that aggregate feature
   records and their canonical serialization are unchanged. The production
   command remains generated mode; no external-stream interface is added.
5. Add `docs/gpu_som_0a.md` documenting the command, feature schema, output
   hashes, and the limitation that the two-triangle scenes validate plumbing
   only. State that codebook quality, scene generalization, and rendering
   optimization are outside GPU-SOM-0A.

## 5. Focused Verification Commands

Execute in this order after implementation:

```bash
python3 software/tests/test_gpu_som_0a_observer.py
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 software/tests/test_gpu_pixel_inspect_s3.py
python3 -m software.spu_gpu_eval.cli observe examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/two_triangle_02
python3 -m software.spu_gpu_eval.cli observe examples/gpu/t1d_two_triangle_vertex_b.json --out build/gpu_evaluation/gpu_som_0a/vertex_b_02
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/preview_parity_02
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/device_parity_02
cmp build/gpu_evaluation/gpu_som_0a/two_triangle_02/device_preview.ppm build/gpu_evaluation/gpu_som_0a/device_parity_02/device_preview.ppm
sha256sum build/gpu_evaluation/gpu_som_0a/two_triangle_02/device_preview.ppm build/gpu_evaluation/gpu_som_0a/device_parity_02/device_preview.ppm
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
git diff --check -- software/spu_gpu_eval/observer.py software/spu_gpu_eval/observer_artifacts.py software/spu_gpu_eval/cli.py software/tests/test_gpu_som_0a_observer.py docs/gpu_som_0a.md spu_strategy/contract_gpu_som_0a_2026-10-14.md
```

The `observe` output image must match `device-preview` byte-for-byte for the
same prepared scene. The ordinary ideal `preview` command is an independent
regression check only; its image is not the observer parity oracle.

Before the first evaluation command, verify frozen input and source hashes,
confirm every output directory is absent, and record the exact invocation
and source state in the manifests. Do not rerun a failed evaluation into an
existing output directory; use a fresh run ID. If artifact generation,
validation, hashing, or manifest consistency checks fail, remove staging
artifacts and leave a previously absent destination absent.

## 6. Evidence and Interpretation

GPU-SOM-0A passes only if the observer tests pass, both scene records contain
1,200 tiles and 307,200 unique generated pixel decisions, repeated extraction
hashes match, and the rendered image bytes and hashes match the ordinary
device-preview path for the same prepared scenes.
Report each criterion separately. A pass establishes deterministic software
feature extraction and renderer independence for these two T1d fixtures only.

The two-triangle fixtures are plumbing inputs. They do not establish useful
clustering, compression, scene generalization, adaptive rendering, or a SOM
advantage. RGB/depth/primitive histograms are observations, not semantic object
or material labels.

GPU-SOM-0B remains out of scope until an independent, diverse scene suite and
a task-sensitive collision oracle are specified. No learned codebook,
symmetry-based feature collapse, renderer feedback, RTL, FPGA build, or
hardware campaign is authorized by this contract.

## 7. Stop Conditions

- If the reference API cannot provide any required feature without modifying
  frozen source or reference behavior, halt and report the missing field.
- If an observer path changes image bytes or pixel decisions, halt; do not
  compensate by changing the renderer.
- If the frame is incomplete, the tile capacity is exceeded, or the output
  directory exists, fail without partial output and stop the run.
- Do not extend this contract to SOM training, codebook comparison, symmetry
  transforms, or hardware without a separate reviewed contract.

## 8. Execution Record

Implementation and the frozen software evaluation completed on 2026-10-14.
The final observer artifacts use run IDs ending in `_02`; the earlier `_01`
directories are retained as prior evidence and are not the final source-hash
matched artifacts.

Focused verification passed:

- `python3 software/tests/test_gpu_som_0a_observer.py` — 6 tests passed.
- `python3 software/tests/test_gpu_scene_compiler_s1.py` — 6 tests passed.
- `python3 software/tests/test_gpu_device_model_s2.py` — passed.
- `python3 software/tests/test_gpu_pixel_inspect_s3.py` — 5 tests passed.
- `python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0` — passed.
- `git diff --check` on the scoped implementation, test, guide, and contract paths — passed.

The final generated-mode evaluations were:

```bash
python3 -m software.spu_gpu_eval.cli observe examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/two_triangle_02
python3 -m software.spu_gpu_eval.cli observe examples/gpu/t1d_two_triangle_vertex_b.json --out build/gpu_evaluation/gpu_som_0a/vertex_b_02
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/preview_parity_02
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/device_parity_02
cmp build/gpu_evaluation/gpu_som_0a/two_triangle_02/device_preview.ppm build/gpu_evaluation/gpu_som_0a/device_parity_02/device_preview.ppm
sha256sum build/gpu_evaluation/gpu_som_0a/two_triangle_02/device_preview.ppm build/gpu_evaluation/gpu_som_0a/device_parity_02/device_preview.ppm
```

Both observer manifests report 1,200 tiles and 307,200 pixel decisions, with
`device_model=true` and `physical_observation=false`. The manifests' recorded
source and frozen-fixture hashes were checked against the files used by the
final evaluation. `cmp` reported byte identity for the observed and
`device-preview` images; both have SHA-256
`6d1ae81a7e678f19754d8cd0f5fd5e54131337d24b8bfddd35870eb8fab35cc5`.
The ordinary `preview` command was run as the separate regression check.

The final evidence directories are:

- `build/gpu_evaluation/gpu_som_0a/two_triangle_02/`
- `build/gpu_evaluation/gpu_som_0a/vertex_b_02/`
- `build/gpu_evaluation/gpu_som_0a/preview_parity_02/`
- `build/gpu_evaluation/gpu_som_0a/device_parity_02/`

`python3 tools/doc_audit.py --actual-pass 238` exited successfully and audited
244 tracked Markdown files, but did not include the then-untracked
`docs/gpu_som_0a.md`. That guide was therefore reviewed directly against the
observer implementation, CLI, and final manifests. The repository audit also
reported existing repository-wide documentation findings; this milestone did
not amend unrelated documents to address them.

This milestone establishes deterministic software observation and device
model renderer parity for the two frozen T1d fixtures. It does not establish
SOM utility, scene generalization, compression, renderer optimization,
physical GPU telemetry, timing, or silicon behavior. No learning, hardware,
or FPGA evaluation was performed.
