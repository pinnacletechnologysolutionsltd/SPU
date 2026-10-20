"""T1d wire packet encoder, independent from the historical edge oracle."""

from __future__ import annotations

from .scene import Scene, Triangle, Vertex


def _edge(p: Vertex, q: Vertex) -> tuple[int, int, int]:
    a = q.y - p.y
    b = p.x - q.x
    c = -(a * p.x + b * p.y)
    return a, b, c


def _evaluate(edge: tuple[int, int, int], point: Vertex) -> int:
    a, b, c = edge
    return a * point.x + b * point.y + c


def wire_edges(triangle: Triangle) -> tuple[tuple[int, int, int], ...]:
    v0, v1, v2 = triangle.vertices
    edges = [_edge(v0, v1), _edge(v1, v2), _edge(v2, v0)]
    opposite = (v2, v0, v1)
    values = [_evaluate(edge, point) for edge, point in zip(edges, opposite)]
    if all(value < 0 for value in values):
        edges = [tuple(-coefficient for coefficient in edge) for edge in edges]
        values = [-value for value in values]
    if not all(value > 0 for value in values):
        raise ValueError("triangle edge orientation is inconsistent or degenerate")
    return tuple(edges)


def _append(record: int, offset: int, value: int, width: int, signed: bool) -> tuple[int, int]:
    low = -(1 << (width - 1)) if signed else 0
    high = (1 << (width - 1)) - 1 if signed else (1 << width) - 1
    if not low <= value <= high:
        raise ValueError(f"packet field {value} outside {low}..{high}")
    record |= (value & ((1 << width) - 1)) << offset
    return record, offset + width


def encode_triangle(triangle: Triangle) -> int:
    fields: list[tuple[int, int, bool]] = []
    for a, b, c in wire_edges(triangle):
        fields.extend(((a, 16, True), (b, 16, True), (c, 32, True)))
    fields.extend((channel, 4, False) for channel in triangle.rgb)
    v0, v1, v2 = triangle.vertices
    fields.extend(((v2.z, 16, False), (v0.z, 16, False), (v1.z, 16, False)))
    record = offset = 0
    for value, width, signed in fields:
        record, offset = _append(record, offset, value, width, signed)
    if offset != 252:
        raise AssertionError(f"T1d record is {offset} bits, expected 252")
    return record


def compile_packet(scene: Scene) -> bytes:
    payload = encode_triangle(scene.triangles[0])
    payload |= encode_triangle(scene.triangles[1]) << 252
    return b"\xA5" + payload.to_bytes(63, "little")
