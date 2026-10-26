#!/usr/bin/env python3
"""GC-5 exact covariance of orientation-sensitive directed-edge turns."""

import hashlib
import itertools
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

from golden_core.exact import ONE, Q5, ZERO
from golden_core.icosahedron import Vec3, edges, vertices
from golden_core.oriented_edge_turns import OrientedEdgeTurns
from golden_core.symmetry import icosahedral_symmetries

FIXTURE_PATH = ROOT / "fixtures/golden_core_gc5_oriented_edge_turns.json"
FIXTURE_BYTES = FIXTURE_PATH.read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)
FIXTURE_SHA256 = "c7e43d55a780664337d09855cf13a154f582e34ec44aa6b0cd59ccfb9ec910cc"


def volume(a: Vec3, b: Vec3, c: Vec3) -> Q5:
    return (a.x * (b.y * c.z - b.z * c.y)
            - a.y * (b.x * c.z - b.z * c.x)
            + a.z * (b.x * c.y - b.y * c.x))


def independent_link_cycles(points, edge_set):
    """Find positively oriented links by exhaustive cyclic-order search."""
    result = []
    adjacency = [set() for _ in points]
    for left, right in edge_set:
        adjacency[left].add(right)
        adjacency[right].add(left)
    for center, adjacent in enumerate(adjacency):
        start = min(adjacent)
        positive = []
        for tail in itertools.permutations(sorted(adjacent - {start})):
            cycle = (start,) + tail
            if not all(tuple(sorted((cycle[i], cycle[(i + 1) % 5]))) in edge_set
                       for i in range(5)):
                continue
            if all(volume(points[center], points[cycle[i]],
                          points[cycle[(i + 1) % 5]]).sign() > 0
                   for i in range(5)):
                positive.append(cycle)
        if len(positive) != 1:
            raise AssertionError("independent oriented-link search was not unique")
        result.append(positive[0])
    return tuple(result)


def compose_permutations(left, right):
    return tuple(left[right[i]] for i in range(len(left)))


def push(state, image):
    output = [ZERO] * len(state)
    for source, target in enumerate(image):
        output[target] = state[source]
    return tuple(output)


def weighted(turns, state, left_weight, right_weight):
    left, right = turns.left(state), turns.right(state)
    return tuple(left_weight * a + right_weight * b for a, b in zip(left, right))


class GoldenCoreGc5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = vertices()
        cls.edge_set = set(edges(cls.points))
        cls.turns = OrientedEdgeTurns.build()
        cls.symmetries = icosahedral_symmetries()
        cls.edge_index = {edge: i for i, edge in enumerate(cls.turns.directed_edges)}

    def test_fixture_hash_and_exact_operators_are_frozen(self):
        self.assertEqual(hashlib.sha256(FIXTURE_BYTES).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(FIXTURE["weight_profile"], {
            "equal": ["1", "1"],
            "unequal": ["3+sqrt(5)", "1-sqrt(5)"],
            "coefficient_domain": "Q(sqrt(5))",
        })
        self.assertEqual(FIXTURE["directed_edges"],
                         [list(edge) for edge in self.turns.directed_edges])
        self.assertEqual(FIXTURE["link_cycles"],
                         [list(cycle) for cycle in self.turns.link_cycles])
        self.assertEqual(FIXTURE["left_image"], list(self.turns.left_image))
        self.assertEqual(FIXTURE["right_image"], list(self.turns.right_image))
        self.assertEqual(len(self.turns.directed_edges), 60)
        self.assertNotEqual(self.turns.left_image, self.turns.right_image)

    def test_independent_exhaustive_link_oracle_agrees(self):
        self.assertEqual(self.turns.link_cycles,
                         independent_link_cycles(self.points, self.edge_set))
        for center, cycle in enumerate(self.turns.link_cycles):
            self.assertEqual(len(cycle), 5)
            self.assertEqual(set(cycle), {j for edge in self.edge_set
                                           for j in (edge if center in edge else ())
                                           if j != center})

    def test_all_120_symmetries_have_the_expected_operator_covariance(self):
        for symmetry in self.symmetries:
            image = tuple(self.edge_index[(symmetry.vertex_image[u],
                                           symmetry.vertex_image[v])]
                          for u, v in self.turns.directed_edges)
            if symmetry.determinant == 1:
                self.assertEqual(compose_permutations(image, self.turns.left_image),
                                 compose_permutations(self.turns.left_image, image))
                self.assertEqual(compose_permutations(image, self.turns.right_image),
                                 compose_permutations(self.turns.right_image, image))
            else:
                self.assertEqual(compose_permutations(image, self.turns.left_image),
                                 compose_permutations(self.turns.right_image, image))
                self.assertEqual(compose_permutations(image, self.turns.right_image),
                                 compose_permutations(self.turns.left_image, image))

    def test_equal_and_unequal_weight_laws_and_mirror_covariance(self):
        equal_a = equal_b = ONE
        unequal_a, unequal_b = Q5(3, 1), Q5(1, -1)
        state = tuple(Q5(i - 20, (i % 7) - 3) for i in range(60))
        equal_internal = []
        unequal_internal = []
        for symmetry in self.symmetries:
            image = tuple(self.edge_index[(symmetry.vertex_image[u],
                                           symmetry.vertex_image[v])]
                          for u, v in self.turns.directed_edges)
            transported = push(state, image)
            left_side = push(weighted(self.turns, state, unequal_a, unequal_b), image)
            covariance_weights = ((unequal_b, unequal_a) if symmetry.determinant == -1
                                  else (unequal_a, unequal_b))
            right_side = weighted(self.turns, transported, *covariance_weights)
            self.assertEqual(left_side, right_side)

            equal_left = push(weighted(self.turns, state, equal_a, equal_b), image)
            equal_right = weighted(self.turns, transported, equal_a, equal_b)
            self.assertEqual(equal_left, equal_right)
            if (symmetry.determinant == 1 or
                    compose_permutations(image, self.turns.left_image) ==
                    compose_permutations(self.turns.right_image, image)):
                equal_internal.append(symmetry)
            if (compose_permutations(image, self.turns.left_image) ==
                    compose_permutations(self.turns.left_image, image) and
                    compose_permutations(image, self.turns.right_image) ==
                    compose_permutations(self.turns.right_image, image)):
                unequal_internal.append(symmetry)

        self.assertEqual(len(equal_internal), 120)
        self.assertEqual(sum(s.determinant == 1 for s in equal_internal), 60)
        self.assertEqual(len(unequal_internal), 60)
        self.assertTrue(all(s.determinant == 1 for s in unequal_internal))
        self.assertEqual(FIXTURE["expected_symmetry_counts"]["equal_weights"],
                         {"total": 120, "proper": 60, "orientation_reversing": 60})
        self.assertEqual(FIXTURE["expected_symmetry_counts"]["unequal_weights"],
                         {"total": 60, "proper": 60, "orientation_reversing": 0})
        self.assertEqual(FIXTURE["expected_symmetry_counts"]["unequal_weight_covariance"], 120)

    def test_basis_state_operator_identity_and_misoriented_link_negative_control(self):
        a, b = Q5(3, 1), Q5(1, -1)
        basis_states = []
        for index in range(60):
            state = [ZERO] * 60
            state[index] = ONE
            basis_states.append(tuple(state))
        # The covariance laws for all group elements are established as
        # permutation identities above; check weighted action on every basis
        # vector for one proper map and one reflection.
        representatives = (next(s for s in self.symmetries if s.determinant == 1),
                           next(s for s in self.symmetries if s.determinant == -1))
        for symmetry in representatives:
            image = tuple(self.edge_index[(symmetry.vertex_image[u],
                                           symmetry.vertex_image[v])]
                          for u, v in self.turns.directed_edges)
            weights = (b, a) if symmetry.determinant == -1 else (a, b)
            for state in basis_states:
                self.assertEqual(push(weighted(self.turns, state, a, b), image),
                                 weighted(self.turns, push(state, image), *weights))

        altered = list(self.turns.link_cycles)
        control_vertex = FIXTURE["negative_control"]["reversed_link_at_vertex"]
        altered[control_vertex] = (altered[control_vertex][0],) + tuple(
            reversed(altered[control_vertex][1:]))
        broken = OrientedEdgeTurns.from_link_cycles(tuple(altered))
        failures = 0
        for symmetry in self.symmetries:
            image = tuple(self.edge_index[(symmetry.vertex_image[u],
                                           symmetry.vertex_image[v])]
                          for u, v in self.turns.directed_edges)
            expected = (compose_permutations(broken.right_image, image)
                        if symmetry.determinant == -1 else
                        compose_permutations(broken.left_image, image))
            actual = compose_permutations(image, broken.left_image)
            failures += actual != expected
        self.assertEqual(failures, FIXTURE["negative_control"]["covariance_failures"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
