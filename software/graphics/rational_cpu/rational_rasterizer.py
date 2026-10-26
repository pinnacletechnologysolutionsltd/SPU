#!/usr/bin/env python3
"""
Tier 2: Wildberger Rational CPU Reference Rasterizer
Norman Wildberger's rational trigonometry: rational affine charts, quadrance, exact ray intersection.
Zero floating-point, zero square roots.
"""
from fractions import Fraction as F

def quadrance(p1, p2):
    """Quadrance (Q): exact squared distance between two points."""
    return (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2

def render(width=64, height=32):
    # Vertices as exact rational fractions
    v0 = (F(12), F(4))
    v1 = (F(52), F(10))
    v2 = (F(24), F(26))

    # Cross product determinants in Fraction
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    grid = [[" " for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            p = (F(x), F(y))
            o1 = orient(v0, v1, p)
            o2 = orient(v1, v2, p)
            o3 = orient(v2, v0, p)
            if o1 >= 0 and o2 >= 0 and o3 >= 0:
                grid[y][x] = "◆"

    print(f"=== Wildberger Rational CPU Renderer ({width}x{height}) ===")
    for row in grid:
        print("".join(row))

if __name__ == "__main__":
    render()
