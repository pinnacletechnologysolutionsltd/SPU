# GPU Evaluation Quickstart: T1d

This guide runs the current offline GPU evaluation path: compile a small scene
to the T1d packet format, compare an ideal mathematical reference with the
finite-width T1d software model, and inspect an individual pixel. It needs
Python 3.10+, Git on `PATH`, and the Python standard library. Run every command
from the repository root. No GPU board or package installation is needed.

The evaluator currently runs from this source checkout as
`software.spu_gpu_eval.cli`; it is not exposed by the installed `spu` console
scripts.

The [software quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md) covers VM, exact
robotics, and these offline tools in an isolated Python environment. Check
the [current status](CURRENT_STATUS.md) and
[hardware evidence ledger](hardware_evidence.md) for physical-board evidence.

## 1. Build an ideal reference preview

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/user_quickstart_20261005/ideal_01
```

This compiles the scene into a 64-byte `scene_packet.bin` and renders an ideal
exact CPU reference. The output directory contains:

- `scene_packet.bin` — compiled T1d scene packet.
- `preview.ppm` — 640×480 ideal reference image.
- `pixel_decisions.json` — exact coverage, depth, and winner decisions at
  diagnostic pixels.
- `manifest.json` — input, packet, source, profile, and output hashes, plus
  explicit `device_model` and `physical_observation` markers.

The JSON at `examples/gpu/t1d_two_triangle.json` is the edit point. Change a
vertex coordinate, depth, or triangle color and rerun with a fresh output
directory. Every `--out` path must be a new directory below
`build/gpu_evaluation`; if the example path already exists, choose another
name.

## 2. Compare against the finite-width device model

```bash
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/user_quickstart_20261005/device_01
```

This produces `scene_packet.bin`, `ideal_preview.ppm`, `device_preview.ppm`,
`pixel_comparison.json`, and `manifest.json`. The comparison records the
diagnostic ideal and model decisions plus full-frame RGB agreement counts.
The manifest binds the result to the input, software, RTL, and reciprocal ROM
hashes, and marks it as a software model rather than a physical observation.

The model represents a settled T1d frame. Its finite-width depth arithmetic
uses reciprocal approximation and truncation, so its depth can differ from
the ideal rational reference. Coverage, selected primitive, and RGB agreement
are useful separate checks; the `inspect` command below reports match flags
for those fields. For the checked-in scene at `(320, 0)`, both paths select
primitive 0 with RGB `[15, 0, 0]`, while ideal depth is 2000 and modeled depth
is 1999.

## 3. Inspect one pixel

```bash
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

This writes one JSON object to stdout with ideal and modeled coverage, depths,
covered primitives, selected primitive and RGB, plus match flags and hashes.
Try another active pixel to inspect a background, single-triangle, or overlap
case. Coordinates outside the 640×480 active image or invalid scene data
produce an error.

## 4. Edit one vertex and explain the image change

Keep the example intact by making a working copy, then render the original as
the baseline:

```bash
mkdir -p build/gpu_evaluation/vertex_edit_lesson
cp examples/gpu/t1d_two_triangle.json build/gpu_evaluation/vertex_edit_lesson/scene.json
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/vertex_edit_lesson/baseline_01
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/vertex_edit_lesson/baseline_device_01
```

Open `build/gpu_evaluation/vertex_edit_lesson/scene.json` in a text editor.
In triangle 0, change its third vertex from `[120, 460, 700]` to
`[120, 240, 700]`. This moves that corner 220 pixels upward and leaves the
second triangle unchanged. Save the file, then render the edited scene to a
different, new output directory and model its device behavior:

```bash
python3 -m software.spu_gpu_eval.cli preview build/gpu_evaluation/vertex_edit_lesson/scene.json --out build/gpu_evaluation/vertex_edit_lesson/edited_01
python3 -m software.spu_gpu_eval.cli device-preview build/gpu_evaluation/vertex_edit_lesson/scene.json --out build/gpu_evaluation/vertex_edit_lesson/device_01
```

Compare `baseline_01/preview.ppm` with `edited_01/preview.ppm`, and compare the
ideal and device images in each scene's output directory, using an image viewer
that supports PPM. The red triangle becomes shorter because its lower corner
moved upward; the green triangle stays in place. Each output directory is new,
so reruns should use another name such as `edited_02`.

The edited JSON and generated results form a saved experiment bundle in
`build/gpu_evaluation/vertex_edit_lesson/`: it contains the input scene, both
ideal and device images, packets, pixel decisions, and manifests with hashes.
Copy or archive that directory to share the exact run. The same edited scene is also provided as
`examples/gpu/t1d_two_triangle_vertex_b.json`, so another checkout can
regenerate the outputs from the baseline and edited source scenes.

Use the pixel inspector to explain a specific change. Compare the original and
edited inputs at `(100, 200)`: the original selects red triangle 0, while the
edited scene has background there. At `(300, 200)`, the original overlap is
won by red triangle 0; after the edit only green triangle 1 covers that pixel.
These decisions match in the ideal reference and the finite-width T1d model
for this example. The inspection JSON reports the coverage, winner, RGB, depth,
and match flags:

```bash
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 100 --y 200
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 300 --y 200
python3 -m software.spu_gpu_eval.cli inspect build/gpu_evaluation/vertex_edit_lesson/scene.json --x 100 --y 200
python3 -m software.spu_gpu_eval.cli inspect build/gpu_evaluation/vertex_edit_lesson/scene.json --x 300 --y 200
```

## Current profile and evidence boundary

The `t1d-two-triangle-v1` profile accepts a 640×480 scene with exactly two
triangles, unsigned 16-bit integer vertex depths, and one flat RGB444 color
per triangle. This is a fixed scene profile, not a general graphics API,
shader language, or shader compiler.

`preview` is the ideal mathematical reference. `device-preview` and `inspect`
are finite-width software-model results. None of these commands loads a
packet onto hardware, observes physical output, or models cycle-level or
display timing. A hardware capture is a separate evidence result; use the
[hardware evidence ledger](hardware_evidence.md) for physical claims.
