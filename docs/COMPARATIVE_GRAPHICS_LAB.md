# Comparative Graphics Laboratory

The SPU project maintains three independent software implementations of 3D triangle rasterization alongside physical FPGA RTL.

## Why Three Renderers?

The goal of the Comparative Graphics Laboratory is to prevent premature architectural coupling. Graphics engineers and researchers can test and measure exactly where exact rational arithmetic provides benefits compared to standard floating-point GPU pipelines.

```text
┌────────────────────────────────────────────────────────┐
│              Comparative Graphics Lab                  │
├──────────────────────────┬─────────────────────────────┤
│ 1. Conventional CPU Ref  │ Float32/64, MVP, clipping,  │
│                          │ standard barycentric        │
├──────────────────────────┼─────────────────────────────┤
│ 2. Wildberger Rational   │ Exact arithmetic, quadrance │
│                          │ & spread, no sqrt / sin     │
├──────────────────────────┼─────────────────────────────┤
│ 3. SPU Hardware Model    │ Streaming beam, zero FB,    │
│                          │ edge steppers, exact depth  │
├──────────────────────────┼─────────────────────────────┤
│ 4. Physical FPGA Silicon │ Artix-7 100T VGA output     │
└──────────────────────────┴─────────────────────────────┘
```

## The Three Tiers

### Tier 1: Conventional CPU Baseline
Located at `software/graphics/conventional_cpu/`.
* **Technology:** Standard IEEE 754 floating-point, 4x4 Model-View-Projection (MVP) matrix, z-buffer, barycentric interpolation.
* **Role:** The control baseline. It gives standard graphics programmers a completely familiar point of comparison.
* **Run:**
  ```bash
  python3 software/graphics/conventional_cpu/conventional_rasterizer.py
  ```

### Tier 2: Wildberger Rational Reference
Located at `software/graphics/rational_cpu/`.
* **Technology:** Norman Wildberger's Rational Trigonometry and Chromogeometry. Replaces Euclidean distance with Quadrance ($Q = \Delta x^2 + \Delta y^2$) and angles with Spread ($s = \sin^2 \theta$).
* **Role:** Research reference exploring purely rational projective geometry with zero transcendental function approximation.
* **Run:**
  ```bash
  python3 software/graphics/rational_cpu/rational_rasterizer.py
  ```

### Tier 3: SPU Hardware-Semantic Simulator
Located at `software/graphics/spu_hardware_sim/`.
* **Technology:** Framebuffer-less streaming beam rasterizer. Directly models RTL `spu_edge_stepper.v` and GPU compute shader `software/gpu_vulkan/gpu_raster.comp`.
* **Role:** Software oracle and simulation target for FPGA silicon.
* **Run:**
  ```bash
  python3 software/graphics/spu_hardware_sim/spu_streaming_rasterizer.py
  ```

## Running the Compute Shader
For hardware-free evaluation of SPU edge stepping at GPU scale:
```bash
# Vulkan compute shader
glslangValidator -V software/gpu_vulkan/gpu_raster.comp -o build/gpu_raster.spv
```
