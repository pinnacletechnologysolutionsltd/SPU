"""Settled-frame T1d device semantics; no clock or display timing model."""

from __future__ import annotations

from dataclasses import dataclass

from .device_arithmetic import PreparedDepth, prepare_depth, signed
from .device_packet import DeviceScene, DeviceTriangle, decode_packet
from .scene import HEIGHT, WIDTH


@dataclass(frozen=True)
class PreparedScene:
    decoded: DeviceScene
    depth: tuple[PreparedDepth, PreparedDepth]


def prepare_scene(packet: bytes) -> PreparedScene:
    decoded = decode_packet(packet)
    return PreparedScene(decoded, tuple(prepare_depth(item) for item in decoded.triangles))


def _edge_value(edge: tuple[int, int, int], x: int, y: int) -> int:
    a, b, c = edge
    return signed(a * x + b * y + c, 32)


def _depth_value(coeff: PreparedDepth, x: int, y: int) -> tuple[int, int]:
    accumulator = signed(coeff.c_z + coeff.a_z * x + coeff.b_z * y, 56)
    return accumulator, signed(accumulator >> coeff.frac_bits, 56)


def pixel_decision(scene: PreparedScene, x: int, y: int) -> dict[str, object]:
    if type(x) is not int or type(y) is not int or not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        raise ValueError("sample coordinate outside the active 640x480 rectangle")
    covered: list[int] = []
    depth_rows: list[dict[str, int]] = []
    for index, triangle in enumerate(scene.decoded.triangles):
        if all(_edge_value(edge, x, y) >= 0 for edge in triangle.edges):
            accumulator, value = _depth_value(scene.depth[index], x, y)
            covered.append(index)
            depth_rows.append({"triangle": index, "accumulator": accumulator, "value": value})
    winner = None if not covered else covered[0]
    if len(covered) == 2 and depth_rows[1]["value"] < depth_rows[0]["value"]:
        winner = covered[1]
    coverage = ("background" if not covered else "overlap" if len(covered) == 2
                else f"triangle{covered[0]}")
    rgb = [0, 0, 0] if winner is None else list(scene.decoded.triangles[winner].rgb)
    return {
        "x": x, "y": y, "coverage": coverage, "covered_by": covered, "depths": depth_rows,
        "winner": winner, "rgb": rgb,
    }


def _covered(triangle: DeviceTriangle, x: int, y: int) -> bool:
    return all(_edge_value(edge, x, y) >= 0 for edge in triangle.edges)


def render_rgb8(scene: PreparedScene) -> bytes:
    output = bytearray(WIDTH * HEIGHT * 3)
    cursor = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cov0 = _covered(scene.decoded.triangles[0], x, y)
            cov1 = _covered(scene.decoded.triangles[1], x, y)
            winner = None
            if cov0 and cov1:
                z0 = _depth_value(scene.depth[0], x, y)[1]
                z1 = _depth_value(scene.depth[1], x, y)[1]
                winner = 1 if z1 < z0 else 0
            elif cov0:
                winner = 0
            elif cov1:
                winner = 1
            rgb = (0, 0, 0) if winner is None else scene.decoded.triangles[winner].rgb
            output[cursor:cursor + 3] = bytes(channel * 17 for channel in rgb)
            cursor += 3
    return bytes(output)
