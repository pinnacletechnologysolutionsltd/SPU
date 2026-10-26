"""Exact orientation-sensitive turns on directed edges of the icosahedron."""

from dataclasses import dataclass

from .exact import Q5, ZERO
from .icosahedron import Vec3, edges, vertices

DirectedEdge = tuple[int, int]


def _volume(a: Vec3, b: Vec3, c: Vec3) -> Q5:
    return (a.x * (b.y * c.z - b.z * c.y)
            - a.y * (b.x * c.z - b.z * c.x)
            + a.z * (b.x * c.y - b.y * c.x))


def oriented_link_cycles(points: tuple[Vec3, ...] | None = None) -> tuple[tuple[int, ...], ...]:
    """Return each neighbor 5-cycle oriented by positive exact volume."""
    points = vertices() if points is None else points
    edge_set = set(edges(points))
    adjacency = [set() for _ in points]
    for left, right in edge_set:
        adjacency[left].add(right)
        adjacency[right].add(left)
    cycles = []
    for center, neighbors in enumerate(adjacency):
        link = {neighbor: neighbors & adjacency[neighbor] for neighbor in neighbors}
        if len(neighbors) != 5 or any(len(values) != 2 for values in link.values()):
            raise ValueError("each vertex link must be a five-cycle")
        start = min(neighbors)
        candidates = []
        for first in sorted(link[start]):
            cycle = [start, first]
            while len(cycle) < 5:
                previous, current = cycle[-2:]
                choices = link[current] - {previous}
                if len(choices) != 1:
                    raise ValueError("vertex link is not a simple cycle")
                cycle.append(next(iter(choices)))
            if start not in link[cycle[-1]] or len(set(cycle)) != 5:
                raise ValueError("vertex link traversal did not close")
            signs = [_volume(points[center], points[cycle[i]],
                             points[cycle[(i + 1) % 5]]).sign()
                     for i in range(5)]
            if all(sign > 0 for sign in signs):
                candidates.append(tuple(cycle))
            elif not all(sign < 0 for sign in signs):
                raise ValueError("link orientation is degenerate or inconsistent")
        if len(candidates) != 1:
            raise ValueError("could not select a unique positive link orientation")
        cycles.append(candidates[0])
    return tuple(cycles)


@dataclass(frozen=True)
class OrientedEdgeTurns:
    """Two exact permutation operators on the 60 directed-edge states."""

    directed_edges: tuple[DirectedEdge, ...]
    link_cycles: tuple[tuple[int, ...], ...]
    left_image: tuple[int, ...]
    right_image: tuple[int, ...]

    @classmethod
    def build(cls) -> "OrientedEdgeTurns":
        return cls.from_link_cycles(oriented_link_cycles())

    @classmethod
    def from_link_cycles(cls, cycles: tuple[tuple[int, ...], ...]) -> "OrientedEdgeTurns":
        """Build turns from explicit cycles; useful for frozen fixtures/controls."""
        undirected = edges()
        points = vertices()
        if len(cycles) != len(points):
            raise ValueError("one link cycle is required for each vertex")
        adjacency = [set() for _ in points]
        for left_vertex, right_vertex in undirected:
            adjacency[left_vertex].add(right_vertex)
            adjacency[right_vertex].add(left_vertex)
        for center, cycle in enumerate(cycles):
            if len(cycle) != 5 or len(set(cycle)) != 5 or set(cycle) != adjacency[center]:
                raise ValueError("each link cycle must list the five adjacent vertices once")
        directed = tuple(sorted((edge for left, right in undirected
                                 for edge in ((left, right), (right, left)))))
        edge_index = {edge: i for i, edge in enumerate(directed)}
        left, right = [], []
        for incoming, center in directed:
            cycle = cycles[center]
            position = cycle.index(incoming)
            successor = cycle[(position + 1) % len(cycle)]
            predecessor = cycle[(position - 1) % len(cycle)]
            left.append(edge_index[(center, successor)])
            right.append(edge_index[(center, predecessor)])
        result = cls(directed, cycles, tuple(left), tuple(right))
        if set(result.left_image) != set(range(len(directed))) or \
                set(result.right_image) != set(range(len(directed))):
            raise AssertionError("left and right turns must permute directed edges")
        return result

    def apply_permutation(self, state: tuple[Q5, ...], image: tuple[int, ...]) -> tuple[Q5, ...]:
        if len(state) != len(self.directed_edges) or len(image) != len(state):
            raise ValueError("state and permutation must match the directed-edge domain")
        output = [ZERO] * len(state)
        for source, target in enumerate(image):
            output[target] = state[source]
        return tuple(output)

    def left(self, state: tuple[Q5, ...]) -> tuple[Q5, ...]:
        return self.apply_permutation(state, self.left_image)

    def right(self, state: tuple[Q5, ...]) -> tuple[Q5, ...]:
        return self.apply_permutation(state, self.right_image)

    def weighted(self, state: tuple[Q5, ...], left_weight: Q5,
                 right_weight: Q5) -> tuple[Q5, ...]:
        left = self.left(state)
        right = self.right(state)
        return tuple(left_weight * a + right_weight * b for a, b in zip(left, right))
