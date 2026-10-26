"""Deterministic software sidecar for finite-width T1d pixel observations."""

from __future__ import annotations

import json
from typing import Iterable

from .device_model import PreparedScene, pixel_decision
from .scene import HEIGHT, WIDTH

TILE_SIZE = 16
TILES_X = WIDTH // TILE_SIZE
TILES_Y = HEIGHT // TILE_SIZE
TILE_CAPACITY = TILES_X * TILES_Y
PIXEL_CAPACITY = WIDTH * HEIGHT


class ObserverError(ValueError):
    """Raised when a T1d observation is incomplete or out of contract."""


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("utf-8")


def _new_tile(tile_x: int, tile_y: int) -> dict[str, object]:
    return {
        "tile_x": tile_x, "tile_y": tile_y, "sample_count": TILE_SIZE * TILE_SIZE,
        "coverage_counts": {name: 0 for name in ("background", "triangle0", "triangle1", "overlap")},
        "covered_pixels": {"0": 0, "1": 0}, "winner_counts": {"0": 0, "1": 0},
        "rgb444_histogram": {},
        "depth_ranges": {"0": {"min": None, "max": None}, "1": {"min": None, "max": None}},
    }


def _add_decision(tile: dict[str, object], decision: dict[str, object]) -> None:
    coverage = decision.get("coverage")
    covered = decision.get("covered_by")
    winner = decision.get("winner")
    rgb = decision.get("rgb")
    depths = decision.get("depths")
    if coverage not in ("background", "triangle0", "triangle1", "overlap"):
        raise ObserverError("invalid coverage state")
    if (not isinstance(covered, list) or any(type(i) is not int or i not in (0, 1) for i in covered)
            or len(set(covered)) != len(covered)):
        raise ObserverError("invalid covered primitive identifiers")
    expected_coverage = ("background" if not covered else "overlap" if len(covered) == 2
                         else f"triangle{covered[0]}")
    if coverage != expected_coverage:
        raise ObserverError("coverage state disagrees with covered primitives")
    if ((not covered and winner is not None)
            or (covered and (type(winner) is not int or winner not in covered))):
        raise ObserverError("winner is not a covered primitive")
    if (not isinstance(rgb, list) or len(rgb) != 3
            or any(type(channel) is not int or not 0 <= channel <= 15 for channel in rgb)):
        raise ObserverError("invalid RGB444 output")
    if (not isinstance(depths, list) or any(not isinstance(row, dict) for row in depths)
            or any(type(row.get("triangle")) is not int or row.get("triangle") not in (0, 1)
                   for row in depths)
            or {row.get("triangle") for row in depths} != set(covered)):
        raise ObserverError("depth rows do not match covered primitives")

    tile["coverage_counts"][coverage] += 1
    for primitive in covered:
        tile["covered_pixels"][str(primitive)] += 1
    if winner is not None:
        tile["winner_counts"][str(winner)] += 1
    rgb_key = ",".join(str(channel) for channel in rgb)
    tile["rgb444_histogram"][rgb_key] = tile["rgb444_histogram"].get(rgb_key, 0) + 1
    for row in depths:
        primitive = row.get("triangle")
        value = row.get("value")
        if (type(primitive) is not int or primitive not in covered or type(value) is not int
                or not -(1 << 55) <= value < (1 << 55)):
            raise ObserverError("invalid finite-width depth observation")
        bounds = tile["depth_ranges"][str(primitive)]
        bounds["min"] = value if bounds["min"] is None else min(bounds["min"], value)
        bounds["max"] = value if bounds["max"] is None else max(bounds["max"], value)


def _tile_record(tile_x: int, tile_y: int,
                 observations: Iterable[tuple[int, int, dict[str, object]]]) -> dict[str, object]:
    expected = {(tile_x * TILE_SIZE + dx, tile_y * TILE_SIZE + dy)
                for dy in range(TILE_SIZE) for dx in range(TILE_SIZE)}
    seen: set[tuple[int, int]] = set()
    tile = _new_tile(tile_x * TILE_SIZE, tile_y * TILE_SIZE)
    for x, y, decision in observations:
        point = (x, y)
        if point not in expected or point in seen:
            raise ObserverError("tile observations contain an out-of-tile or duplicate coordinate")
        seen.add(point)
        _add_decision(tile, decision)
    if seen != expected:
        raise ObserverError("tile observation is missing one or more pixel coordinates")
    histogram = tile["rgb444_histogram"]
    tile["rgb444_histogram"] = [
        {"rgb": [int(channel) for channel in key.split(",")], "count": histogram[key]}
        for key in sorted(histogram, key=lambda value: tuple(map(int, value.split(","))))
    ]
    return tile


def _check_tile_capacity(record_count: int) -> None:
    if record_count < 0 or record_count > TILE_CAPACITY:
        raise ObserverError("tile record capacity exceeded")


def extract_tile_features(prepared: PreparedScene) -> bytes:
    """Generate all device-model observations and return canonical tile JSON."""
    records: list[dict[str, object]] = []
    seen = bytearray((PIXEL_CAPACITY + 7) // 8)
    observed = 0
    for tile_y in range(TILES_Y):
        for tile_x in range(TILES_X):
            batch = []
            for dy in range(TILE_SIZE):
                y = tile_y * TILE_SIZE + dy
                for dx in range(TILE_SIZE):
                    x = tile_x * TILE_SIZE + dx
                    index = y * WIDTH + x
                    bit = 1 << (index & 7)
                    if seen[index >> 3] & bit:
                        raise ObserverError("generated coordinate appeared more than once")
                    decision = pixel_decision(prepared, x, y)
                    seen[index >> 3] |= bit
                    observed += 1
                    batch.append((x, y, decision))
            records.append(_tile_record(tile_x, tile_y, batch))
            _check_tile_capacity(len(records))
    if observed != PIXEL_CAPACITY or any(value != 0xFF for value in seen):
        raise ObserverError("generated pixel grid is incomplete")
    if len(records) != TILE_CAPACITY:
        raise ObserverError("tile record capacity exceeded or frame incomplete")
    return _json_bytes({"format": "spu_gpu_som_tile_features_v1", "tile_size": TILE_SIZE,
                        "width": WIDTH, "height": HEIGHT, "pixel_decisions": observed,
                        "tiles": records})
