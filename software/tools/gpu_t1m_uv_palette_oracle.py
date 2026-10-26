#!/usr/bin/env python3
"""Exploratory T1m palette oracle using frozen T1i scene fixtures.

This is preparation data only: it does not compile RTL or qualify a hardware
profile. It independently derives the covered depth winner and its U/V values,
then maps all four U[12]/V[12] classes to visible RGB colours so covered
fragments remain distinguishable from the black background.
"""

from __future__ import annotations

import argparse
from collections import Counter
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "software" / "tests"))
from test_gpu_t1i_uv import ROOT, decode, load_scene, oracle


SCENES = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
COLORS = ("red", "green", "blue", "yellow")


def rgb_from_uv(u: int, v: int) -> int:
    u_bit = (u >> 12) & 1
    v_bit = (v >> 12) & 1
    r_bit = int(u_bit == v_bit)
    g_bit = v_bit
    b_bit = u_bit & (1 - v_bit)
    return (r_bit << 2) | (g_bit << 1) | b_bit


def palette_class(u: int, v: int) -> int:
    return (((u >> 12) & 1) << 1) | ((v >> 12) & 1)


def analyze(width: int, height: int) -> int:
    decoded = [decode(scene[1]) for scene in SCENES]
    scene_counts = [Counter() for _ in range(3)]
    lane_counts = [[[0] * 4 for _ in range(4)] for _ in range(3)]
    first_a: dict[tuple[int, int], int] = {}
    changes = [0, 0]
    coverage = [0, 0, 0]
    uncovered = [0, 0, 0]
    return_a_mismatches = 0

    for sid in range(4):
        scene_index = 0 if sid == 3 else sid
        for y in range(height):
            for x in range(width):
                valid, lane, u, v = oracle(decoded[scene_index], x, y)
                rgb = rgb_from_uv(u, v) if valid else 0
                if valid:
                    if sid != 3:
                        coverage[scene_index] += 1
                        color_class = palette_class(u, v)
                        scene_counts[scene_index][color_class] += 1
                        lane_counts[scene_index][lane][color_class] += 1
                elif sid != 3:
                    uncovered[scene_index] += 1
                if sid == 0:
                    first_a[(x, y)] = rgb
                elif sid in (1, 2):
                    changes[sid - 1] += rgb != first_a[(x, y)]
                elif rgb != first_a[(x, y)]:
                    return_a_mismatches += 1

    print(f"ROI: {width}x{height} per scene")
    print("Palette: U/V bits 00=red, 01=green, 10=blue, 11=yellow")
    for sid, label in enumerate("ABC"):
        counts = " ".join(f"{COLORS[color]}={scene_counts[sid][color]}"
                          for color in range(4))
        lanes = "; ".join(
            f"lane{lane}:" + ",".join(str(lane_counts[sid][lane][color])
                                         for color in range(4))
            for lane in range(4)
        )
        print(f"{label}: covered={coverage[sid]} uncovered={uncovered[sid]} {counts}")
        print(f"  lane/color counts (red,green,blue,yellow): {lanes}")
    print(f"changed pixels versus A: B={changes[0]} C={changes[1]}")
    print(f"return-A mismatches: {return_a_mismatches}")
    return int(not all(changes) or return_a_mismatches != 0 or
               not all(all(sum(lane) > 0 for lane in scene) for scene in lane_counts))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="analyze all active 640x480 pixels")
    args = parser.parse_args()
    width, height = (640, 480) if args.production else (80, 100)
    return analyze(width, height)


if __name__ == "__main__":
    raise SystemExit(main())
