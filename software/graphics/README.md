# Graphics Software Examples

For the current GPU evaluation path, see the
[T1d GPU Evaluation Quickstart](../../docs/gpu_scene_preview.md). It runs from
the repository checkout and provides scene packet compilation, an ideal
reference, a finite-width T1d model, and pixel inspection.

The examples in this directory are separate demonstrations:

- `conventional_cpu/` — conventional floating-point rasterization demo.
- `rational_cpu/` — rational-geometry research demo.
- `spu_hardware_sim/spu_streaming_rasterizer.py` — hard-coded 64×32 ASCII
  edge-coverage teaching demo. It is not the T1d device model or a complete
  GPU emulator.

The optional `software/gpu_vulkan/gpu_raster.comp` example computes one
triangle's coverage mask. It is not a shader language or general shader
compiler. Physical FPGA results are recorded separately in
[`docs/hardware_evidence.md`](../../docs/hardware_evidence.md).
