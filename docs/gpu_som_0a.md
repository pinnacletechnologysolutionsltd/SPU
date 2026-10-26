# GPU-SOM-0A: deterministic T1d observer

GPU-SOM-0A writes an inspectable software sidecar from the finite-width T1d
device model. The observer does not train a SOM and cannot affect renderer
decisions. Its image output is produced from the same prepared scene and must
match the `device-preview` path byte for byte. The ideal `preview` path remains
a separate reference check.

Run from the repository root. Each `--out` path must be a new directory under
`build/gpu_evaluation/gpu_som_0a/`. The suffixes below are examples; choose a
fresh suffix for every run because publication refuses to overwrite evidence.

```bash
python3 -m software.spu_gpu_eval.cli observe examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/two_triangle_03
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/device_parity_03
cmp build/gpu_evaluation/gpu_som_0a/two_triangle_03/device_preview.ppm build/gpu_evaluation/gpu_som_0a/device_parity_03/device_preview.ppm
sha256sum build/gpu_evaluation/gpu_som_0a/two_triangle_03/device_preview.ppm build/gpu_evaluation/gpu_som_0a/device_parity_03/device_preview.ppm
```

The output directory contains:

- `scene_packet.bin` — compiled 64-byte T1d packet.
- `device_preview.ppm` — finite-width device-model image.
- `tile_features.json` — row-major 16×16 tile observations.
- `manifest.json` — source, fixture, packet, feature and preview hashes, with
  software-model and physical-observation markers.

Each of the 1,200 tile records describes 256 pixel decisions. It contains
coverage counts (`background`, `triangle0`, `triangle1`, `overlap`), primitive
coverage and winner counts, a sorted RGB444 histogram, and finite-width depth
minimum and maximum values per primitive. Uncovered primitives have null
depth bounds. Empty tiles contain 256 background samples, a black RGB444
histogram entry with count 256, and null depth bounds.

The observer generates the full 640×480 coordinate grid. It does not accept an
external observation stream. Any invalid or missing pixel decision, duplicate
coordinate, incomplete tile, output validation error, or write failure aborts
publication. Artifacts are staged privately and published as a complete
directory; a failed run removes its staging directory. Existing destinations
are rejected without modification.

The two checked-in scenes contain only two flat-color triangles. They verify
feature extraction, deterministic serialization, and renderer independence;
they do not establish useful clustering, compression, generalization,
adaptive rendering, or a SOM advantage. The feature fields are geometric and
pixel-model observations, not semantic object or material labels. GPU-SOM-0B
requires a separate diverse scene suite and task-sensitive collision oracle.

For a separate ideal-reference check and one-pixel inspection, use fresh
output paths for preview commands:

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/gpu_som_0a/preview_parity_03
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

These results are software-model evidence only. They do not represent
physical GPU telemetry, display timing, or silicon behavior.
