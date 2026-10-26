#!/usr/bin/env python3
"""Generate an abstract center-plus-12-neighbor SPU-13 anchor plan.

The output is a geometric hypothesis for coarse grouping.  It is not a legal
Gowin CST and does not claim that RTL hierarchy survives synthesis.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import coordinate_transformer as ct


SCRIPT_DIR = Path(__file__).resolve().parent


def generate_vector_equilibrium_coords(
    cx: float = 0.5,
    cy: float = 0.5,
    radius: float = 0.12,
    ring: int = 12,
) -> list[tuple[float, float]]:
    if ring < 1:
        raise ValueError("ring must contain at least one neighbor")
    if radius <= 0.0:
        raise ValueError("radius must be positive")
    points = [(cx, cy)]
    for index in range(ring):
        angle = 2.0 * math.pi * index / ring
        points.append(
            (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        )
    for point in points:
        if not (0.0 <= point[0] <= 1.0 and 0.0 <= point[1] <= 1.0):
            raise ValueError(f"ring point outside normalized canvas: {point}")
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(SCRIPT_DIR / "gowin_tang25k_grid.json"))
    parser.add_argument("--cx", type=float, default=0.5)
    parser.add_argument("--cy", type=float, default=0.5)
    parser.add_argument("--radius", type=float, default=0.12)
    parser.add_argument("--ring", type=int, default=12)
    parser.add_argument("--prefix", default="spu13_axis")
    parser.add_argument("--output-csv", default="spu13_axis_anchor_plan.csv")
    parser.add_argument("--max-radius", type=int, default=8)
    args = parser.parse_args()

    grid = ct.grid_from_config(ct.load_config(args.config))
    points = generate_vector_equilibrium_coords(
        args.cx, args.cy, args.radius, args.ring
    )
    names = [f"{args.prefix}_{index}" for index in range(len(points))]
    mappings = ct.plan_anchors(names, points, grid, args.max_radius)
    ct.write_plan_csv(
        args.output_csv,
        mappings,
        "vector-equilibrium-projection",
        grid.device,
    )
    print(
        f"Wrote {len(mappings)} abstract SPU-13 anchors to {args.output_csv}. "
        "No physical placement constraints were emitted."
    )


if __name__ == "__main__":
    main()
