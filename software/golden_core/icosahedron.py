"""Exact coordinates and incidence for the standard Q(phi) icosahedron."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product

from .exact import ONE, PHI, Q5, ZERO


@dataclass(frozen=True)
class Vec3:
    x: Q5
    y: Q5
    z: Q5

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def quadrance(self) -> Q5:
        return self.x * self.x + self.y * self.y + self.z * self.z

    def dot(self, other: "Vec3") -> Q5:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def rotate_120(self) -> "Vec3":
        """Apply (x,y,z) -> (z,x,y), an exact proper 120-degree rotation."""
        return Vec3(self.z, self.x, self.y)


def vertices() -> tuple[Vec3, ...]:
    """Return 12 distinct vertices, cyclic permutations of (0, ±1, ±phi)."""
    result = []
    for s1, s2 in product((1, -1), repeat=2):
        a, b = ONE * Q5(s1), PHI * Q5(s2)
        result.extend((Vec3(ZERO, a, b), Vec3(a, b, ZERO), Vec3(b, ZERO, a)))
    return tuple(result)


def quadrance(a: Vec3, b: Vec3) -> Q5:
    return (a - b).quadrance()


def edges(points: tuple[Vec3, ...] | None = None) -> tuple[tuple[int, int], ...]:
    points = vertices() if points is None else points
    edge_q = Q5(Fraction(4))
    return tuple((i, j) for i, j in combinations(range(len(points)), 2)
                 if quadrance(points[i], points[j]) == edge_q)


def faces(points: tuple[Vec3, ...] | None = None) -> tuple[tuple[int, int, int], ...]:
    points = vertices() if points is None else points
    edge_set = set(edges(points))
    return tuple((i, j, k) for i, j, k in combinations(range(len(points)), 3)
                 if (i, j) in edge_set and (i, k) in edge_set and (j, k) in edge_set)


def connected(vertex_count: int, edge_list: tuple[tuple[int, int], ...]) -> bool:
    if vertex_count == 0:
        return False
    adjacency = [set() for _ in range(vertex_count)]
    for a, b in edge_list:
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen, todo = {0}, [0]
    while todo:
        for nxt in adjacency[todo.pop()] - seen:
            seen.add(nxt)
            todo.append(nxt)
    return len(seen) == vertex_count

