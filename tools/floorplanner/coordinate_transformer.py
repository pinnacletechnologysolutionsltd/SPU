#!/usr/bin/env python3
"""Generate deterministic *abstract* FPGA floorplan anchor coordinates.

This tool maps an already ordered list of logical groups onto either a Hilbert
traversal or a Sierpinski-carpet point set.  It deliberately emits a CSV plan,
not Gowin ``INS_LOC`` constraints: a legal ``INS_LOC`` identifies a packed
primitive and a concrete slice/LUT slot, while logical RTL module names are
normally flattened by Yosys.

The missing stages between this plan and a build constraint are intentional and
must remain explicit:

1. derive a one-dimensional order from the synthesized connectivity graph;
2. associate each logical group with packed primitive cells;
3. legalize anchors against the device's heterogeneous BEL inventory; and
4. apply the result through a nextpnr pre-place hook or fully specified CST.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class GridBounds:
    """Inclusive abstract nextpnr X/Y bounds.

    These are a bounding box, not a declaration that every coordinate contains
    a legal BEL for every resource type.
    """

    x_min: int
    x_max: int
    y_min: int
    y_max: int
    device: str = "unspecified"

    def __post_init__(self) -> None:
        if self.x_min > self.x_max or self.y_min > self.y_max:
            raise ValueError("grid minima must not exceed maxima")

    @property
    def capacity(self) -> int:
        return (self.x_max - self.x_min + 1) * (self.y_max - self.y_min + 1)


def _require_nonnegative(value: int, label: str) -> None:
    if value < 0:
        raise ValueError(f"{label} must be non-negative")


def sierpinski_carpet(depth: int) -> list[tuple[float, float]]:
    """Return centers of retained Sierpinski-carpet cells.

    This is a deterministic de-clustering geometry, not a space-filling curve
    traversal and not a substitute for connectivity-derived ordering.
    """

    _require_nonnegative(depth, "depth")
    cells = [(0, 0)]
    scale = 1
    for _ in range(depth):
        next_cells: list[tuple[int, int]] = []
        scale *= 3
        for x, y in cells:
            for dy in range(3):
                for dx in range(3):
                    if dx == 1 and dy == 1:
                        continue
                    next_cells.append((3 * x + dx, 3 * y + dy))
        cells = next_cells
    return [((x + 0.5) / scale, (y + 0.5) / scale) for x, y in cells]


def _hilbert_rotate(n: int, x: int, y: int, rx: int, ry: int) -> tuple[int, int]:
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    return x, y


def _hilbert_d2xy(side: int, distance: int) -> tuple[int, int]:
    x = 0
    y = 0
    span = 1
    remaining = distance
    while span < side:
        rx = 1 & (remaining // 2)
        ry = 1 & (remaining ^ rx)
        x, y = _hilbert_rotate(span, x, y, rx, ry)
        x += span * rx
        y += span * ry
        remaining //= 4
        span *= 2
    return x, y


def hilbert_curve(order: int) -> list[tuple[float, float]]:
    """Return a discrete Hilbert traversal in locality-preserving order."""

    _require_nonnegative(order, "order")
    side = 1 << order
    return [
        ((x + 0.5) / side, (y + 0.5) / side)
        for distance in range(side * side)
        for x, y in [_hilbert_d2xy(side, distance)]
    ]


def load_config(path: str | Path | None) -> dict:
    if path is None:
        return {}
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def grid_from_config(config: dict) -> GridBounds:
    required = ("x_min", "x_max", "y_min", "y_max")
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(
            "grid config is missing " + ", ".join(missing)
            + "; legacy rows/cols configs are not physical-placement evidence"
        )
    return GridBounds(
        x_min=int(config["x_min"]),
        x_max=int(config["x_max"]),
        y_min=int(config["y_min"]),
        y_max=int(config["y_max"]),
        device=str(config.get("device", "unspecified")),
    )


def map_normalized_to_grid(x: float, y: float, grid: GridBounds) -> tuple[int, int]:
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("normalized coordinates must be finite")
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError(f"normalized coordinate outside [0,1]: ({x}, {y})")
    gx = round(grid.x_min + x * (grid.x_max - grid.x_min))
    gy = round(grid.y_min + y * (grid.y_max - grid.y_min))
    return gx, gy


def find_nearest_free(
    x: int,
    y: int,
    occupied: set[tuple[int, int]],
    grid: GridBounds,
    max_radius: int = 8,
) -> tuple[int, int]:
    """Find a deterministic free anchor or fail instead of overlapping."""

    _require_nonnegative(max_radius, "max_radius")
    if (x, y) not in occupied:
        return x, y
    for radius in range(1, max_radius + 1):
        candidates: list[tuple[int, int]] = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                candidate = (x + dx, y + dy)
                if not (
                    grid.x_min <= candidate[0] <= grid.x_max
                    and grid.y_min <= candidate[1] <= grid.y_max
                ):
                    continue
                if candidate not in occupied:
                    candidates.append(candidate)
        if candidates:
            # Stable Manhattan-nearest, then row-major tie break.
            return min(
                candidates,
                key=lambda p: (abs(p[0] - x) + abs(p[1] - y), p[1], p[0]),
            )
    raise RuntimeError(
        f"no free anchor within radius {max_radius} of ({x}, {y}); "
        "increase the grid/order spacing or collision radius"
    )


def load_instance_order(path: str | Path) -> list[str]:
    names = [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not names:
        raise ValueError("instance-order file contains no names")
    if len(names) != len(set(names)):
        raise ValueError("instance-order file contains duplicate names")
    return names


def validate_packed_cell_names(names: Iterable[str], netlist_path: str | Path) -> None:
    """Require exact cell-name matches in a Yosys/nextpnr JSON netlist."""

    data = load_config(netlist_path)
    available: set[str] = set()
    for module in data.get("modules", {}).values():
        available.update(module.get("cells", {}).keys())
    missing = sorted(set(names) - available)
    if missing:
        preview = ", ".join(missing[:5])
        suffix = " ..." if len(missing) > 5 else ""
        raise ValueError(
            f"{len(missing)} planned names are not packed-cell names in {netlist_path}: "
            f"{preview}{suffix}"
        )


def plan_anchors(
    names: Sequence[str],
    points: Sequence[tuple[float, float]],
    grid: GridBounds,
    max_radius: int,
) -> list[tuple[int, str, int, int, float, float]]:
    if len(names) > len(points):
        raise ValueError(
            f"{len(names)} names require more than {len(points)} geometry points"
        )
    if len(names) > grid.capacity:
        raise ValueError(f"{len(names)} names exceed abstract grid capacity {grid.capacity}")

    occupied: set[tuple[int, int]] = set()
    mappings: list[tuple[int, str, int, int, float, float]] = []
    for index, (name, (nx, ny)) in enumerate(zip(names, points)):
        x, y = map_normalized_to_grid(nx, ny, grid)
        x, y = find_nearest_free(x, y, occupied, grid, max_radius)
        occupied.add((x, y))
        mappings.append((index, name, x, y, nx, ny))
    return mappings


def write_plan_csv(
    path: str | Path,
    mappings: Sequence[tuple[int, str, int, int, float, float]],
    geometry: str,
    device: str,
) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "order",
                "logical_group",
                "anchor_x",
                "anchor_y",
                "norm_x",
                "norm_y",
                "geometry",
                "device",
            ]
        )
        for index, name, x, y, nx, ny in mappings:
            writer.writerow([index, name, x, y, nx, ny, geometry, device])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--geometry",
        choices=("hilbert", "sierpinski-carpet"),
        default="hilbert",
    )
    parser.add_argument(
        "--order",
        "--depth",
        dest="order",
        type=int,
        default=3,
        help="recursion order",
    )
    parser.add_argument("--count", type=int, help="number of generated logical anchors")
    parser.add_argument(
        "--instances",
        help="ordered text file of logical-group or packed-cell names",
    )
    parser.add_argument(
        "--prefix",
        default="logical_group",
        help="generated name prefix when --instances is omitted",
    )
    parser.add_argument("--config", default=str(SCRIPT_DIR / "gowin_tang25k_grid.json"))
    parser.add_argument("--netlist-json", help="validate --instances as exact packed-cell names")
    parser.add_argument("--output-csv", default="floorplan_anchor_plan.csv")
    parser.add_argument("--max-radius", type=int, default=8)
    args = parser.parse_args()

    config = load_config(args.config)
    grid = grid_from_config(config)
    points = (
        hilbert_curve(args.order)
        if args.geometry == "hilbert"
        else sierpinski_carpet(args.order)
    )

    if args.instances:
        names = load_instance_order(args.instances)
    else:
        count = len(points) if args.count is None else args.count
        if count < 0:
            raise ValueError("count must be non-negative")
        names = [f"{args.prefix}_{index}" for index in range(count)]

    if args.netlist_json:
        if not args.instances:
            raise ValueError("--netlist-json requires an explicit --instances file")
        validate_packed_cell_names(names, args.netlist_json)

    mappings = plan_anchors(names, points, grid, args.max_radius)
    write_plan_csv(args.output_csv, mappings, args.geometry, grid.device)
    print(
        f"Wrote {len(mappings)} abstract {args.geometry} anchors to {args.output_csv}. "
        "No physical placement constraints were emitted."
    )


if __name__ == "__main__":
    main()
