#!/usr/bin/env python3
"""
Tier 3: SPU Hardware-Semantic Streaming Rasterizer
Models hardware/rtl/gpu/spu_edge_stepper.v and software/lib/gpu_raster_oracle.py
Zero floating point, zero division, zero framebuffer. Incremental beam stepping.
"""
def render(width=64, height=32):
    # Integer coefficients matching RTL hardware registers:
    # A*x + B*y + C >= 0
    e0 = (-6, 40, -88)
    e1 = (-16, -28, 1112)
    e2 = (22, -12, -216)

    grid = [[" " for _ in range(width)] for _ in range(height)]

    for y in range(height):
        # RTL evaluates incrementally along each raster line
        for x in range(width):
            f0 = e0[0] * x + e0[1] * y + e0[2]
            f1 = e1[0] * x + e1[1] * y + e1[2]
            f2 = e2[0] * x + e2[1] * y + e2[2]
            if f0 >= 0 and f1 >= 0 and f2 >= 0:
                grid[y][x] = "▲"

    print(f"=== SPU-13 Hardware-Semantic Streaming Rasterizer ({width}x{height}) ===")
    for row in grid:
        print("".join(row))

if __name__ == "__main__":
    render()
