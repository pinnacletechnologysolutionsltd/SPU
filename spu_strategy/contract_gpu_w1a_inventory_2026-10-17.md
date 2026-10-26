# GPU-W1A — T1d workbench inventory and implementation contract preparation

**Date:** 2026-10-17
**Status:** W1-A inventory complete; W1-B/W1-C proposed, not authorized
**Scope performed:** Read-only source inventory, command-line pixel inspection, and contract preparation. No implementation or tests run.

## 1. Source identity and provenance

The inspected repository reports `HEAD=963a685004b96e275e7e58ebefac98c6e1321597`.
The T1d evaluator, scenes, fixtures, and S1/S2/S3 tests in this checkout are
untracked. They therefore have no immutable source commit in this worktree.
The SHA-256 values below identify the inspected files in this local state; they
do not substitute for a source commit or clean-checkout provenance.

| File | SHA-256 |
|---|---|
| `software/spu_gpu_eval/cli.py` | `091b9880d537fafba85bf7d2398b3c242d285c14bee932124dde744c5a47b407` |
| `software/spu_gpu_eval/scene.py` | `a80beae64f0b59bdeb16b68c0fbd5e012710c29cdc96d535ceb2d478a8f3102f` |
| `software/spu_gpu_eval/packet.py` | `a897aa5252c74810cb31d67c19e73c9eb239f86d817ea250a7d7f6ec4aa25885` |
| `software/spu_gpu_eval/device_packet.py` | `cd58f46c68625b473a224d5454e1fdae34600d86cf9426af227d52b077f4d2d1` |
| `software/spu_gpu_eval/reference.py` | `78eaa547f08e1410d34f442ae43c5e8e0c0e5b5ba6855b0b67715fccd74702e9` |
| `software/spu_gpu_eval/device_model.py` | `cc507652fabc257a7baf36ceac905de5fc4a97e7d61871d4d3e57b25f9d059d6` |
| `software/spu_gpu_eval/device_preview.py` | `9c7a0b1700a5809b6cee7d569e69d264e3534ecfc3f583676609974136290c57` |
| `software/spu_gpu_eval/device_inspect.py` | `2014edf02655cd0232b9ec8cab875e770634727c4facb281e5c083f19392f8f1` |
| `software/tests/test_gpu_scene_compiler_s1.py` | `7c45e5906952573d49bd886924bdd767fbdfe6ea1c24d1e3b8f82d417eec964e` |
| `software/tests/test_gpu_device_model_s2.py` | `8195e912b05177e914492af32202169b0af2a973ec192d4e74c15c6a6f79d6f7` |
| `software/tests/test_gpu_pixel_inspect_s3.py` | `f6533fb098eb8be4744ca11ab7f2ad37e7debf1ad347a2e4576f2a0436c5bf2e` |
| `fixtures/gpu_t1d_scene_reference.json` | `7c48bdeffac97bba871e5c92663168900cb617f8586976e66f09077e11b7f138` |
| `fixtures/gpu_t1d_scene_wire_64b.bin` | `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| `examples/gpu/t1d_two_triangle.json` | `fbe44dd9f21e05a51e544ef88c0cee47c060fd36b7eeb309e38b846bab0566ef` |
| `examples/gpu/t1d_two_triangle_vertex_b.json` | `f0b6be3ccb39c919af5c4eb8cb9ab12f4ccd37b6e7bc5eae90365a489c7e17f5` |
| `fixtures/golden_core_t1d_tetra_views_reference.json` | `395874b62c2cac5957003e930bcb06c5930e7269690ad42a3ddc2a809c046deb` |

The separate Golden Core tetrahedron suite has three scenes under
`examples/gpu/golden_core_tetra_views/`; its frozen fixture records scene and
packet hashes and selected pixel expectations. The scene-diversity suite has
six scenes and a manifest at `examples/gpu/scene_diversity/manifest.json`.
These suites are candidate selector entries, not newly qualified W1 results.

| Candidate scene | SHA-256 |
|---|---|
| `examples/gpu/golden_core_tetra_views/identity.json` | `27dda4d08c307640672f1ed5b655061a9d57889fb8afebfdc1c87e67a2e5d372` |
| `examples/gpu/golden_core_tetra_views/rotate_bcd.json` | `d779dc731b941d734a417e2e5c0be43eb461b11625d4d7356257550dadb0ceda` |
| `examples/gpu/golden_core_tetra_views/reflect_bc.json` | `dade87cc881f9ee6b4ec336b2aa32ff0894583317e03a3ed24305e092940c056` |
| `examples/gpu/scene_diversity/disjoint_a.json` | `ade2b3dad4cfaccc9303dbb8a31a6c3a2dc20733e2f61b111fd389f115bdcef1` |
| `examples/gpu/scene_diversity/disjoint_b.json` | `43b9a2e76951f2cdf53a28844a38c22c41672879b07733ed4605924a530f6a13` |
| `examples/gpu/scene_diversity/overlap_t0_near.json` | `713c92361dd6e680707666b8d0749424007250e8376f1ecae8e52399c3796e04` |
| `examples/gpu/scene_diversity/overlap_t1_near.json` | `969101289e5536f89142fe051a1dc0839ca05b061db8c1103e97f3218c512db1` |
| `examples/gpu/scene_diversity/overlap_tie.json` | `ab14581d71c98469b3cf2f396a966f8977536e96929b94ff7aff549ba53c3cfc` |
| `examples/gpu/scene_diversity/overlap_shared_rgb.json` | `7e08c9958d91cb097112e3dd4049dcb98fd872e5ec96a734a9dab727c09bfc19` |
| `examples/gpu/scene_diversity/manifest.json` | `7e00dc3f42275f8ec20337107a3a329e9091800c22e0d2bd12233c470ca2c4c3` |
| `fixtures/gpu_scene_diversity_reference.json` | `9cdfa631cac3cbb35de95eb60551b8099af0759511ee0e53dffd74c42083e65b` |
| `fixtures/golden_core_t1d_tetra_views_reference.json` | `395874b62c2cac5957003e930bcb06c5930e7269690ad42a3ddc2a809c046deb` |

## 2. Existing interface inventory

Run from the repository root. The Python CLI entry point is
`python3 -m software.spu_gpu_eval.cli`.

| Capability | Existing command/API | Output and limit |
|---|---|---|
| Ideal reference render | `preview <scene.json> --out <new-dir>` | 64-byte T1d packet, 640×480 P6 PPM, pixel-decision JSON, source/hash manifest. Exact rational reference path. |
| Finite-width model render | `device-preview <scene.json> --out <new-dir>` | Packet, ideal and device PPMs, pixel-comparison JSON, source/profile hashes. Settled-frame model; not cycle timing or physical output. |
| One-pixel comparison | `inspect <scene.json> --x <int> --y <int>` | Deterministic JSON to stdout; no report file. Rejects coordinates outside 640×480. |
| T1d packet decode | `software.spu_gpu_eval.device_packet.decode_packet(bytes)` | Python API only; validates the 64-byte packet and `0xA5` start byte, then returns two decoded triangle records. No CLI inspector exists. |
| Frozen scene selection | None | Callers currently pass a filesystem path. No scene catalogue or selector exists. |
| Frame viewer / click-to-inspect | None | Renders are PPM files; viewing and pixel-coordinate entry are external. |

The strict scene parser accepts exactly `spu_gpu_scene_v1` /
`t1d-two-triangle-v1`: 640×480, exactly two nondegenerate triangles,
integer screen coordinates within the active frame, unsigned 16-bit vertex
depths, and flat RGB444 per-triangle color. It rejects other primitive counts,
unknown JSON keys, out-of-range coordinates, invalid colors, duplicate JSON
keys, and unsupported format/profile identifiers. This is not a general shader
or graphics API.

The ideal renderer computes exact rational coverage/depth decisions. The
finite-width model decodes the same 64-byte packet and applies bounded edge,
reciprocal-ROM, depth, and tie semantics. It is a host-CPU model, not compute
shader execution, a cycle/timing model, or an FPGA capture.

## 3. Frozen depth-difference control

The read-only command

```bash
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

returned an overlap at `(320,0)`. The ideal depths are `2000` for both
triangles; the finite-width device-model depths are `1999` for both. Both choose
triangle 0 and RGB `[15,0,0]`. Thus depth differs while coverage, winner, and
RGB agree. The S3 report includes both depth records but its `decision_match`
map currently compares only coverage, covered primitives, winner, and RGB.
W1 must show depth equality separately rather than infer it from
`decision_match`.

The baseline packet fixture has SHA-256
`aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`. The
S1/S2/S3 tests respectively cover scene/packet/reference behavior, the
finite-width model and selected RTL parity paths, and deterministic pixel
inspection/schema/errors. Existing test commands are listed in §5; no tests
were executed during W1-A.

## 4. W1-B implementation contract proposal

After separate authorization, add a CLI workbench that orchestrates existing
scene parser, packet compiler, ideal renderer, finite-width model, and packet
decoder. Do not implement a second rasterizer.

Proposed operations:

```bash
python3 -m software.spu_gpu_eval.workbench list
python3 -m software.spu_gpu_eval.workbench render baseline --mode ideal --out build/gpu_evaluation/gpu_w1_baseline_ideal_01
python3 -m software.spu_gpu_eval.workbench render baseline --mode device --out build/gpu_evaluation/gpu_w1_baseline_device_01
python3 -m software.spu_gpu_eval.workbench inspect baseline --x 320 --y 0
python3 -m software.spu_gpu_eval.workbench inspect-packet build/gpu_evaluation/gpu_w1_baseline_ideal_01/scene_packet.bin
```

Use a frozen, explicit scene-ID allowlist, not recursive file discovery. The
initial candidate set is the two baseline scenes, the three Quadray tetrahedron
views, and the six scene-diversity scenes. Each entry must pin its source path
and SHA-256 in a versioned manifest. Unknown IDs, malformed JSON, malformed
packets, invalid pixels, and output-path collisions must fail with a concise
diagnostic and nonzero status without partial output.

Every inspected pixel must report ideal and device-model coverage, covered
triangles, depth values, winner, and RGB. Report `depths_equal` independently
from winner/color equality. The `(320,0)` baseline control must show ideal
`2000`, modeled `1999`, and unchanged winner/color. Preserve the existing S3
JSON API unless a later reviewed amendment requires a compatible additive
field.

The packet inspector must report packet hash, profile, start byte, and both
decoded triangle records. It must reject lengths other than 64 bytes and a
start byte other than `0xA5`. It must not reinterpret the packet as a richer
profile.

## 5. W1-B verification proposal

After W1-B authorization, run:

```bash
python3 -m unittest discover -s software/tests -p 'test_gpu_scene_compiler_s1.py' -v
python3 -m unittest discover -s software/tests -p 'test_gpu_device_model_s2.py' -v
python3 -m unittest discover -s software/tests -p 'test_gpu_pixel_inspect_s3.py' -v
python3 -m unittest discover -s software/tests -p 'test_gpu_workbench_w1.py' -v
python3 -m software.spu_gpu_eval.workbench list
python3 -m software.spu_gpu_eval.workbench inspect baseline --x 320 --y 0
python3 -m software.spu_gpu_eval.workbench inspect-packet build/gpu_evaluation/gpu_w1_baseline_ideal_01/scene_packet.bin
```

Also render one frozen scene in each mode to distinct new output directories,
compare repeated output bytes, and confirm manifests identify ideal versus
device-model execution and mark `physical_observation: false`. Run the
documentation-specified commands after any docs changes. Only after the short
tests pass and no conflicting detached regression is active may one repository
gate be launched under `tools/run_detached_job.sh`; record its unique output
path and frozen timeout in the W1-B execution contract.

## 6. W1-C viewer proposal

After W1-B review, add a dependency-free viewer for existing P6 PPM outputs.
Provide separate ideal and device-model frame panes, file selection, clickable
pixel inspection, and visible coverage/depth/winner/RGB fields. Label the two
arithmetic paths. Do not silently pick the ideal image as the device result.
Keep view-only behavior separate from the renderer; no GPU compute backend,
new packet semantics, or hardware execution.

## 7. Hold boundaries

W1-A is complete as inventory and preparation only. W1-B/W1-C remain proposed
until separately authorized. Do not edit the renderer, scene schema, packet
format, RTL, ISA, or physical deployment flows in W1-A. The S3 repository gate
is independent; do not poll or overlap it during this preparation.
