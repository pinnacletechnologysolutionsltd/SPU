#!/usr/bin/env python3
"""
Tier 1: Conventional CPU Reference Rasterizer
Standard floating-point 3D pipeline: Float MVP projection, barycentric coordinates, z-buffer.
"""
def orient(a, b, c):
    """2D determinant / signed area of parallelogram spanned by (b-a) and (c-a)."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def render(width=64, height=32):
    # Conventional floating-point vertices (X, Y, Z)
    v0 = (12.0, 4.0, 1.0)
    v1 = (52.0, 10.0, 2.0)
    v2 = (24.0, 26.0, 0.5)

    area = orient(v0, v1, v2)
    grid = [[" " for _ in range(width)] for _ in range(height)]
    z_buffer = [[float('inf') for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            p = (float(x), float(y))
            w0 = orient(v0, v1, p)
            w1 = orient(v1, v2, p)
            w2 = orient(v2, v0, p)

            # Inside test (counter-clockwise)
            if w0 >= 0 and w1 >= 0 and w2 >= 0:
                # Barycentric interpolation of 1/Z
                b0 = w0 / area
                b1 = w1 / area
                b2 = w2 / area
                denom = (b0/v0[2] + b1/v1[2] + b2/v2[2])
                z = 1.0 / denom if denom != 0 else 0
                if z < z_buffer[y][x]:
                    z_buffer[y][x] = z
                    grid[y][x] = "█"

    print(f"=== Conventional Float CPU Renderer ({width}x{height}) ===")
    for row in grid:
        print("".join(row))

if __name__ == "__main__":
    render()
