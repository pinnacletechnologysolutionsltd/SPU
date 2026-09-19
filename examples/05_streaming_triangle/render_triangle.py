#!/usr/bin/env python3
"""
Example 5: SPU Streaming Edge-Stepper Rasterizer
Models hardware/rtl/gpu/spu_edge_stepper.v and software/lib/gpu_raster_oracle.py
Renders a rational triangle to terminal ASCII and optional PPM image.
"""
import sys

def edge_step(a, b, c, x, y):
    """Exact 32-bit two's complement evaluation matching RTL spu_edge_stepper.v"""
    return (a * x + b * y + c) >= 0

def main():
    width = 64
    height = 32

    # Integer edge coefficients matching RTL accumulator registers:
    # f = A*x + B*y + C >= 0
    e0 = (-6, 40, -88)
    e1 = (-16, -28, 1112)
    e2 = (22, -12, -216)

    print(f"=== SPU-13 Streaming Beam Rasterizer ({width}x{height}) ===")
    print("Exact integer arithmetic: A*x + B*y + C >= 0 (Zero floating point, Zero framebuffer)\n")

    pixels = []
    for y in range(height):
        row = []
        for x in range(width):
            in0 = edge_step(e0[0], e0[1], e0[2], x, y)
            in1 = edge_step(e1[0], e1[1], e1[2], x, y)
            in2 = edge_step(e2[0], e2[1], e2[2], x, y)
            covered = in0 and in1 and in2
            row.append("▲" if covered else " ")
            pixels.append((240, 180, 50) if covered else (20, 25, 35))
        print("".join(row))

    if "--save" in sys.argv:
        out_file = "triangle.ppm"
        with open(out_file, "w") as f:
            f.write(f"P3\n{width} {height}\n255\n")
            for r, g, b in pixels:
                f.write(f"{r} {g} {b}\n")
        print(f"\n[Saved exact raster image to {out_file}]")

if __name__ == "__main__":
    main()
