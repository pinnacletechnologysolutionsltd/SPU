# Comparative Graphics Laboratory

This laboratory maintains three independent software implementations of 3D triangle rasterization alongside physical FPGA RTL.

## The Three Tiers

```text
1. Conventional CPU Renderer (software/graphics/conventional_cpu/)
   ├── Standard IEEE 754 Float32 / Float64
   ├── Standard 4x4 Model-View-Projection (MVP) matrix pipeline
   ├── Standard barycentric interpolation & z-buffer
   └── Purpose: The control baseline against which alternative methods are measured.

2. Wildberger Rational Renderer (software/graphics/rational_cpu/)
   ├── Norman Wildberger's Rational Trigonometry & Chromogeometry
   ├── Quadrance (distance squared) & Spread (sin squared)
   ├── Pure rational numbers (Fraction) — zero square roots, zero trig functions
   └── Purpose: Mathematical research reference for exact projective geometry.

3. SPU Hardware-Semantic Simulator (software/graphics/spu_hardware_sim/)
   ├── Models exact SPU-13 RTL (hardware/rtl/gpu/spu_edge_stepper.v)
   ├── Framebuffer-less, beam-synchronous rasterization
   ├── 32-bit two's complement integer edge functions (A*x + B*y + C >= 0)
   ├── Bit-exact parity with software/gpu_vulkan/gpu_raster.comp
   └── Purpose: Software oracle and simulation target for physical silicon.
```

## Running the Comparative Demos
- Conventional CPU: `python3 software/graphics/conventional_cpu/conventional_rasterizer.py`
- Rational CPU: `python3 software/graphics/rational_cpu/rational_rasterizer.py`
- SPU Hardware Model: `python3 software/graphics/spu_hardware_sim/spu_streaming_rasterizer.py`
