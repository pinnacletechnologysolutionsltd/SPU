"""Ideal exact coverage/depth reference derived only from input vertices."""

from __future__ import annotations

from fractions import Fraction

from .scene import HEIGHT, WIDTH, Scene, Triangle, Vertex


def _cross(a: Vertex, b: Vertex, p: Vertex | tuple[int, int]) -> int:
    px, py = (p.x, p.y) if isinstance(p, Vertex) else p
    return (b.x - a.x) * (py - a.y) - (b.y - a.y) * (px - a.x)


def _triangle_depth(triangle: Triangle, x: int, y: int) -> tuple[int, int] | None:
    v0, v1, v2 = triangle.vertices
    area = _cross(v0, v1, v2)
    weights = (_cross(v1, v2, (x, y)), _cross(v2, v0, (x, y)), _cross(v0, v1, (x, y)))
    if area > 0:
        if any(weight < 0 for weight in weights):
            return None
    elif any(weight > 0 for weight in weights):
        return None
    numerator = sum(weight * vertex.z for weight, vertex in zip(weights, triangle.vertices))
    if area < 0:
        numerator, area = -numerator, -area
    return numerator, area


def _coverage_name(indices: list[int]) -> str:
    if not indices:
        return "background"
    if len(indices) == 2:
        return "overlap"
    return f"triangle{indices[0]}"


def pixel_decision(scene: Scene, x: int, y: int) -> dict[str, object]:
    if type(x) is not int or type(y) is not int or not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        raise ValueError("sample coordinate outside the active 640x480 rectangle")
    depths: list[tuple[int, int, int]] = []
    for index, triangle in enumerate(scene.triangles):
        depth = _triangle_depth(triangle, x, y)
        if depth is not None:
            depths.append((index, depth[0], depth[1]))
    winner: int | None = None
    if len(depths) == 1:
        winner = depths[0][0]
    elif len(depths) == 2:
        first, second = depths
        winner = first[0] if first[1] * second[2] <= second[1] * first[2] else second[0]
    rgb = list(scene.triangles[winner].rgb) if winner is not None else [0, 0, 0]
    return {
        "x": x,
        "y": y,
        "coverage": _coverage_name([item[0] for item in depths]),
        "covered_by": [item[0] for item in depths],
        "depths": [
            {"triangle": index, "numerator": Fraction(num, den).numerator,
             "denominator": Fraction(num, den).denominator}
            for index, num, den in depths
        ],
        "winner": winner,
        "rgb": rgb,
    }


def pixel_rgb(scene: Scene, x: int, y: int) -> tuple[int, int, int]:
    depths: list[tuple[int, int, int]] = []
    for index, triangle in enumerate(scene.triangles):
        depth = _triangle_depth(triangle, x, y)
        if depth is not None:
            depths.append((index, depth[0], depth[1]))
    if not depths:
        return 0, 0, 0
    winner = depths[0][0]
    if len(depths) == 2:
        first, second = depths
        if first[1] * second[2] > second[1] * first[2]:
            winner = second[0]
    return scene.triangles[winner].rgb


def render_rgb8(scene: Scene) -> bytes:
    output = bytearray(WIDTH * HEIGHT * 3)
    cursor = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            rgb = pixel_rgb(scene, x, y)
            output[cursor:cursor + 3] = bytes(channel * 17 for channel in rgb)
            cursor += 3
    return bytes(output)
