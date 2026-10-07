"""Strict parser and value types for editable T1d scenes."""

from __future__ import annotations

import json
from dataclasses import dataclass


WIDTH = 640
HEIGHT = 480
FORMAT = "spu_gpu_scene_v1"
PROFILE = "t1d-two-triangle-v1"


class SceneError(ValueError):
    """Raised when input is not a complete supported T1d scene."""


@dataclass(frozen=True)
class Vertex:
    x: int
    y: int
    z: int


@dataclass(frozen=True)
class Triangle:
    vertices: tuple[Vertex, Vertex, Vertex]
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class Scene:
    triangles: tuple[Triangle, Triangle]


def _object_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SceneError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _keys(value: object, expected: set[str], where: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise SceneError(f"{where} must contain exactly keys {sorted(expected)}")
    return value


def _integer(value: object, low: int, high: int, where: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise SceneError(f"{where} must be an integer in {low}..{high}")
    return value


def parse_scene_data(data: object) -> Scene:
    root = _keys(data, {"format", "profile", "width", "height", "triangles"}, "scene")
    if root["format"] != FORMAT or root["profile"] != PROFILE:
        raise SceneError("unsupported scene format or profile")
    if _integer(root["width"], WIDTH, WIDTH, "width") != WIDTH:
        raise SceneError("width must equal 640")
    if _integer(root["height"], HEIGHT, HEIGHT, "height") != HEIGHT:
        raise SceneError("height must equal 480")

    raw_triangles = root["triangles"]
    if not isinstance(raw_triangles, list) or len(raw_triangles) != 2:
        raise SceneError("triangles must contain exactly two primitives")

    parsed: list[Triangle] = []
    for index, raw_triangle in enumerate(raw_triangles):
        item = _keys(raw_triangle, {"vertices", "rgb"}, f"triangle {index}")
        raw_vertices = item["vertices"]
        if not isinstance(raw_vertices, list) or len(raw_vertices) != 3:
            raise SceneError(f"triangle {index} must contain three vertices")
        vertices: list[Vertex] = []
        for vi, raw_vertex in enumerate(raw_vertices):
            if not isinstance(raw_vertex, list) or len(raw_vertex) != 3:
                raise SceneError(f"triangle {index} vertex {vi} must be [x,y,z]")
            x = _integer(raw_vertex[0], 0, WIDTH - 1, f"triangle {index} vertex {vi} x")
            y = _integer(raw_vertex[1], 0, HEIGHT - 1, f"triangle {index} vertex {vi} y")
            z = _integer(raw_vertex[2], 0, 65535, f"triangle {index} vertex {vi} z")
            vertices.append(Vertex(x, y, z))
        rgb = item["rgb"]
        if not isinstance(rgb, list) or len(rgb) != 3:
            raise SceneError(f"triangle {index} rgb must contain three channels")
        color = tuple(_integer(c, 0, 15, f"triangle {index} rgb channel") for c in rgb)
        v0, v1, v2 = vertices
        area2 = (v1.x - v0.x) * (v2.y - v0.y) - (v1.y - v0.y) * (v2.x - v0.x)
        if area2 == 0:
            raise SceneError(f"triangle {index} has zero signed twice-area")
        parsed.append(Triangle(tuple(vertices), color))
    return Scene(tuple(parsed))


def parse_scene_bytes(raw: bytes) -> Scene:
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SceneError(f"invalid UTF-8 JSON: {exc}") from exc
    return parse_scene_data(data)
