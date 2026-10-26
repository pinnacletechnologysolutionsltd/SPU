# Example 5: Streaming Triangle Rasterizer

Demonstrates the exact arithmetic edge-function rasterizer executed by SPU-13 RTL (`spu_edge_stepper.v`) and GPU compute shader (`software/gpu_vulkan/gpu_raster.comp`).

## The Math
No floating-point barycentric coordinates and no framebuffer. Pixels stream synchronously with beam scan:
$$f(x, y) = A \cdot x + B \cdot y + C \ge 0$$
Evaluated with 32-bit two's complement integer arithmetic.

## Running the Demo
```bash
python3 examples/05_streaming_triangle/render_triangle.py
```
