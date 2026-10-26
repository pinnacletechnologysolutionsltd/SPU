# Comparative Graphics Laboratory

For the current GPU software evaluation workflow, start with the
[GPU Evaluation Quickstart: T1d](gpu_scene_preview.md). It compiles a fixed
two-triangle scene packet, produces an ideal reference and finite-width
software-model comparison, and inspects individual pixels. It does not load a
physical board.

This page describes the earlier comparative CPU demos, a small edge-coverage
teaching program, and separately recorded FPGA evidence. These examples have
different scopes and should not be read as one complete GPU simulator.

## Comparative software demos

### Tier 1: Conventional CPU baseline

Located at `software/graphics/conventional_cpu/`.

- Uses conventional floating-point rasterization techniques.
- Run with:

  ```bash
  python3 software/graphics/conventional_cpu/conventional_rasterizer.py
  ```

### Tier 2: Wildberger rational reference

Located at `software/graphics/rational_cpu/`.

- Explores rational geometry using quadrance and spread.
- It is a mathematical research demo, not the current T1d device model.
- Run with:

  ```bash
  python3 software/graphics/rational_cpu/rational_rasterizer.py
  ```

### Tier 3: Legacy ASCII edge-coverage demo

Located at `software/graphics/spu_hardware_sim/`.

- `spu_streaming_rasterizer.py` draws a small, hard-coded 64×32 ASCII edge-
  coverage example.
- It is a teaching demo. It does not implement the T1d packet profile, model
  the complete RTL, provide depth behavior, or act as a complete GPU emulator.
- Run with:

  ```bash
  python3 software/graphics/spu_hardware_sim/spu_streaming_rasterizer.py
  ```

## Optional Vulkan coverage example

`software/gpu_vulkan/gpu_raster.comp` is an optional compute-shader example
for one-triangle coverage. It is not the current T1d evaluator, a general
shader compiler, or a shader language. Building it requires Vulkan/GLSL tools
such as `glslangValidator`:

```bash
glslangValidator -V software/gpu_vulkan/gpu_raster.comp -o build/gpu_raster.spv
```

## Physical FPGA evidence

Historical VGA and rasterization results are recorded independently in the
[hardware evidence ledger](hardware_evidence.md). A software demo or model
result does not establish physical output or acceptance.

## Comparative Benchmark Evidence

Benchmark reports must keep these claims separate. They are independent
checks; passing one does not imply that another has passed.

| Dimension | Question answered | Report |
|---|---|---|
| Same-device repeatability | Do repeated runs on the same device, with the same input and configuration, produce the same result? | Run count, fixed inputs/seeds, comparison method, and mismatches |
| Cross-build reproducibility | Do separately produced builds from the declared source/configuration produce the same result? | Source revision, build configuration, toolchain, artifact identities, and output comparison |
| Cross-device reproducibility | Do supported devices produce the same result for the same declared workload? | Device models/revisions, configurations, output comparison, and known scope limits |
| Mathematical-oracle agreement | Does every checked result agree with an independently implemented mathematical oracle? | Oracle identity, checked domain/count, exactness rule, and mismatch count |
| Cost of reproducibility | What time, throughput, energy, memory, or resource cost accompanies each reproducibility guarantee? | Baseline, controlled guarantee level, measurement method, and measured delta |

Treat the first four as separate result fields rather than a ladder. The fifth
is a measurement attached to each guarantee being evaluated. A result can be
repeatable without being correct, oracle-correct without being repeatable on
another device, or correct on two devices without being reproducible across
builds. State the tested operator/workload and avoid extending a kernel result
to an entire graphics or inference stack.
