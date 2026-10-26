# Engineering Contract: GPU Evaluation User On-Ramp

- **Date:** 2026-10-05
- **Contract ID:** `contract_gpu_evaluation_onramp_2026-10-05.md`
- **Status:** COMPLETE
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Codex, after §0 review
- **Integration Auditor:** `tools/doc_audit.py` and repository gates

## 0. Pre-execution review

Run from the repository root:

```bash
git status --short
sed -n '1,180p' docs/gpu_scene_preview.md
sed -n '1,180p' docs/COMPARATIVE_GRAPHICS_LAB.md
sed -n '1,160p' software/graphics/README.md
sed -n '1,120p' docs/index.md
sed -n '1,120p' mkdocs.yml
sed -n '1,120p' pyproject.toml
sed -n '1,140p' software/graphics/spu_hardware_sim/spu_streaming_rasterizer.py
sed -n '1,140p' software/gpu_vulkan/gpu_raster.comp
```

Halt if the three current commands differ from the checked-in CLI or if the
T1d scene profile or evidence boundaries have changed. Preserve all existing
artifact paths, historical evidence, and unrelated dirty files.

## 1. Objective and scoped files

Make the existing T1d guide the primary GPU evaluation quickstart. Correct the
main software entry points and older graphics-demo descriptions so a new user
can identify the current fixed-profile tools and their limits.

Target files:

```text
README.md
docs/index.md
docs/README.md
docs/COMPARATIVE_GRAPHICS_LAB.md
docs/FIRST_HOUR.md
docs/gpu_scene_preview.md
mkdocs.yml
software/graphics/README.md
AGENTS.md
spu_strategy/contract_gpu_evaluation_onramp_2026-10-05.md
```

Do not change package metadata, software behavior, RTL, hardware evidence,
fixtures, generated files, historical experiment results, or unrelated docs.
Do not move, rename, or delete existing files or artifacts.

## 2. User path requirements

Update `docs/gpu_scene_preview.md` with the title `GPU Evaluation Quickstart:
T1d`, Python 3.10+ standard-library prerequisites, and the instruction to run
commands from the repository root. State that this evaluator is checkout-based
and is not exposed by the installed `spu` console scripts.

Show the exact current commands:

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/user_quickstart_20261005/ideal_01
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/user_quickstart_20261005/device_01
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

Explain that each `--out` path must be new. List the artifacts produced by each
command. State the current limits exactly: the `t1d-two-triangle-v1` profile is
640×480, two triangles, unsigned 16-bit vertex depths, and flat RGB444 color;
the model has no shader execution, hardware transport, physical observation, or
cycle/display timing.

Explain the evidence levels: `preview` is the ideal mathematical reference;
`device-preview` and `inspect` are finite-width software-model outputs; a
hardware capture is a separate result. Explain that ideal and device depths can
differ because the profile uses reciprocal approximation and finite-width
truncation, while coverage/winner/RGB comparisons are separately reported.

## 3. Entry points and demo boundaries

1. Add the quickstart link to the README software links and `docs/index.md`.
2. Add it to the MkDocs `Software & Toolchain` navigation.
3. Add the GPU evaluation roadmap and quickstart to the current-source-of-truth
   table in `docs/README.md`.
4. Describe `software/graphics/spu_hardware_sim/spu_streaming_rasterizer.py`
   as a hardcoded ASCII edge-coverage teaching demo, not the current T1d device
   model or a complete GPU emulator.
5. Describe `software/gpu_vulkan/gpu_raster.comp` as an optional one-triangle
   coverage compute example, not a shader language or general shader compiler.
6. Link the older graphics pages to the T1d quickstart for the current packet,
   ideal-reference, device-model, and pixel-inspection path.
7. Add a guided one-vertex edit. Preserve the original example, generate
   baseline and edited previews into fresh directories, compare the PPM images,
   run the finite-width preview, and inspect pixels whose coverage, winner, and
   color change. Keep the edited JSON with output manifests as a reproducible
   run bundle and identify the saved `t1d_two_triangle_vertex_b.json` scene.
8. Keep current suite totals in the README and first-hour guide aligned with
   the latest completed repository verifier, and link the GPU quickstart from
   the first-hour guide.

Preserve the historical comparative demos and hardware claims with their
existing scope. Do not describe software simulation as physical acceptance.

## 4. Acceptance commands

Run from the repository root:

```bash
python3 tools/doc_audit.py --actual-pass 238
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 software/tests/test_gpu_pixel_inspect_s3.py
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/vertex_edit_lesson/baseline_01
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/vertex_edit_lesson/baseline_device_01
python3 -m software.spu_gpu_eval.cli preview build/gpu_evaluation/vertex_edit_lesson/scene.json --out build/gpu_evaluation/vertex_edit_lesson/edited_01
python3 -m software.spu_gpu_eval.cli device-preview build/gpu_evaluation/vertex_edit_lesson/scene.json --out build/gpu_evaluation/vertex_edit_lesson/device_01
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 100 --y 200
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 300 --y 200
python3 -m software.spu_gpu_eval.cli inspect build/gpu_evaluation/vertex_edit_lesson/scene.json --x 100 --y 200
python3 -m software.spu_gpu_eval.cli inspect build/gpu_evaluation/vertex_edit_lesson/scene.json --x 300 --y 200
git diff --check -- AGENTS.md README.md docs/index.md docs/README.md docs/COMPARATIVE_GRAPHICS_LAB.md docs/FIRST_HOUR.md docs/gpu_scene_preview.md mkdocs.yml software/graphics/README.md
```

These documentation and offline-evaluator changes do not affect RTL,
arithmetic kernels, or hardware build flows. Per root `AGENTS.md` §4.1, the
focused T1d tests, documented commands, docs audit, and scoped diff check are
the applicable gates. `TB_FILTER` triage is not applicable.

## 5. Completion record

All three focused T1d test files passed. The documented baseline preview,
edited preview, device preview, and three pixel inspections exited
successfully. The generated ideal PPMs differ at 43,823 pixels. The baseline
pixel `(100, 200)` selects red triangle 0; the edited scene reports background
there and green triangle 1 at `(300, 200)`. The edited input matches
`examples/gpu/t1d_two_triangle_vertex_b.json`. The saved run bundle is
`build/gpu_evaluation/vertex_edit_lesson/`, with baseline and edited ideal and
device images, packets, pixel decisions, and hash manifests.

The docs audit exited 0. It reported one stale total in a historical strategy
document and other repository-wide legacy findings; all four local links in
the new quickstart were checked and resolve. No hardware behavior or physical
observation changed. Loading and observing the scene on qualified hardware is
the next separate milestone.

## 6. Stop conditions

- Stop if the quickstart commands do not correspond to the current CLI.
- Stop if a page claims shader execution, hardware loading, or display timing
  that the current software does not provide.
- Stop if a historical hardware result would be broadened or erased.
- Stop before moving or deleting any source, fixture, contract, or evidence file.
