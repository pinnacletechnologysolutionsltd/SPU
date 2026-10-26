#!/usr/bin/env python3
"""GC-3 exact field, icosahedron, independent-oracle and negative-control checks."""

import json
import hashlib
import random
import sys
import unittest
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))
sys.path.insert(0, str(ROOT / "software" / "tests"))

from golden_core.exact import ONE, PHI, Q5, ZERO
from golden_core.icosahedron import Vec3, connected, edges, faces, quadrance, vertices
from lib.tensegrity_balancer import Fraction as PhiFraction
from lib.tensegrity_balancer import Phi


FIXTURE = json.loads((ROOT / "fixtures/golden_core_gc3_icosahedron.json").read_text())
FIXTURE_BYTES = (ROOT / "fixtures/golden_core_gc3_icosahedron.json").read_bytes()
FIXTURE_SHA256 = "02e4265f511a968d4926e3e60dbc339e7bda58cdb49dfeeb6a984bd51ce92fca"


def phi_oracle(value: Q5) -> Phi:
    """Convert to the retained independent a+b*phi implementation."""
    return Phi(*(PhiFraction(c.numerator, c.denominator) for c in value.to_phi()))


def phi_coefficients(value: Phi) -> tuple[Fraction, Fraction]:
    return (Fraction(value.a.num, value.a.den), Fraction(value.b.num, value.b.den))


def oracle_vertices() -> tuple[tuple[Phi, Phi, Phi], ...]:
    """Construct the same point set directly in the retained phi basis."""
    result = []
    p0, p1 = Phi.from_int(0), Phi.from_int(1)
    pphi = Phi(PhiFraction(0), PhiFraction(1))
    for s1 in (1, -1):
        for s2 in (1, -1):
            a = Phi.from_int(s1)
            b = pphi * s2
            result.extend(((p0, a, b), (a, b, p0), (b, p0, a)))
    return tuple(result)


def oracle_quadrance(a: tuple[Phi, Phi, Phi], b: tuple[Phi, Phi, Phi]) -> Phi:
    delta = tuple(x - y for x, y in zip(a, b))
    return sum((d * d for d in delta), Phi.from_int(0))


class GoldenCoreGc3Tests(unittest.TestCase):
    def test_fixture_hash_is_frozen(self):
        self.assertEqual(hashlib.sha256(FIXTURE_BYTES).hexdigest(), FIXTURE_SHA256)

    def test_qsqrt5_field_cross_checks_retained_qphi_implementation(self):
        phi_squared = PHI * PHI
        self.assertEqual(phi_squared, PHI + ONE)
        self.assertEqual(phi_squared.to_phi(), (Fraction(1), Fraction(1)))
        self.assertEqual(Q5.from_phi(2, 3), Q5.from_phi(Fraction(4, 2), Fraction(6, 2)))
        self.assertEqual(Q5(0), ZERO)
        self.assertLess(Q5(1) - PHI, ZERO)  # 1 - phi < 0
        self.assertGreater(Q5(2) - PHI, ZERO)  # 2 - phi > 0
        self.assertEqual((PHI * PHI.conjugate()), Q5(-1))
        self.assertEqual(PHI * PHI.inverse(), ONE)
        with self.assertRaises(ZeroDivisionError):
            ONE / ZERO

        rng = random.Random(20261016)
        cases = 0
        for _ in range(2048):
            def rational():
                return Fraction(rng.randint(-80, 80), rng.randint(1, 19))

            x, y = Q5(rational(), rational()), Q5(rational(), rational())
            ox, oy = phi_oracle(x), phi_oracle(y)
            for exact, reference in ((x + y, ox + oy), (x - y, ox - oy), (x * y, ox * oy)):
                self.assertEqual(exact.to_phi(), phi_coefficients(reference))
                self.assertEqual(phi_oracle(exact), reference)
            delta = x - y
            self.assertEqual(delta.sign() > 0, (phi_oracle(delta)).is_positive())
            self.assertEqual(delta.sign() == 0, delta == ZERO)
            if y != ZERO:
                exact, reference = x / y, ox / oy
                self.assertEqual(exact.to_phi(), phi_coefficients(reference))
            cases += 1
        self.assertEqual(cases, 2048)

    def test_frozen_icosahedron_incidence_and_independent_phi_geometry(self):
        points = vertices()
        self.assertEqual(len(points), 12)
        self.assertEqual(len(set(points)), 12)
        exact_pairs = [[[int(c), int(d)] for c, d in (coord.to_phi() for coord in (p.x, p.y, p.z))]
                       for p in points]
        self.assertEqual(exact_pairs, FIXTURE["vertices_phi"])

        edge_list, face_list = edges(points), faces(points)
        self.assertEqual([list(e) for e in edge_list], FIXTURE["edges"])
        self.assertEqual([list(f) for f in face_list], FIXTURE["faces"])
        self.assertTrue(all(quadrance(points[i], points[j]) == Q5(4) for i, j in edge_list))
        self.assertEqual(len(edge_list), 30)
        self.assertEqual(len(face_list), 20)
        degree = Counter(i for edge in edge_list for i in edge)
        self.assertEqual([degree[i] for i in range(12)], [5] * 12)
        self.assertTrue(connected(12, edge_list))

        independent = oracle_vertices()
        self.assertEqual(len(independent), 12)
        self.assertEqual(
            [[list(phi_coefficients(coord)) for coord in p] for p in independent],
            exact_pairs,
        )
        independent_edges = tuple(
            (i, j) for i, j in combinations(range(12), 2)
            if oracle_quadrance(independent[i], independent[j]) == Phi.from_int(4)
        )
        self.assertEqual([list(e) for e in independent_edges], FIXTURE["edges"])

    def test_exact_proper_rotation_preserves_geometry(self):
        points = vertices()
        rotation = tuple(point.rotate_120() for point in points)
        point_indices = {point: i for i, point in enumerate(points)}
        image_indices = [point_indices[p] for p in rotation]
        self.assertEqual(image_indices, FIXTURE["proper_rotation"]["vertex_image_indices"])
        self.assertEqual(len(set(rotation)), 12)
        self.assertEqual(set(rotation), set(points))
        rotation2 = tuple(p.rotate_120() for p in rotation)
        rotation3 = tuple(p.rotate_120() for p in rotation2)
        self.assertEqual(set(rotation2), set(points))
        self.assertEqual(rotation3, points)

        # Independently check the cyclic permutation matrix in ordinary rational arithmetic.
        matrix = FIXTURE["proper_rotation"]["matrix"]
        det = (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
               - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
               + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))
        self.assertEqual(det, 1)
        self.assertEqual(matrix, [[0, 0, 1], [1, 0, 0], [0, 1, 0]])
        self.assertTrue(all(quadrance(points[i], points[j]) ==
                            quadrance(rotation[i], rotation[j])
                            for i, j in combinations(range(12), 2)))
        oracle_rotated = tuple((p[2], p[0], p[1]) for p in oracle_vertices())
        self.assertEqual(set(oracle_rotated), set(oracle_vertices()))

    def test_frozen_broken_coordinate_negative_control_is_rejected(self):
        points = list(vertices())
        control = FIXTURE["negative_control"]
        i = control["vertex_index"]
        delta = Q5.from_phi(*control["delta_phi"])
        p = points[i]
        points[i] = Vec3(p.x + delta, p.y, p.z)
        bad_points = tuple(points)
        bad_edges = edges(bad_points)
        degrees = Counter(v for edge in bad_edges for v in edge)
        degree_multiset = sorted(degrees.get(k, 0) for k in range(12))
        self.assertEqual(len(bad_edges), control["expected_edge_count"])
        self.assertEqual(degree_multiset, control["expected_degree_multiset"])
        self.assertEqual(connected(12, bad_edges), control["expected_connected"])
        self.assertNotEqual(len(faces(bad_points)), 20)

    def test_visual_demo_embeds_the_frozen_exact_source_data_and_boundary_label(self):
        page = (ROOT / "examples/golden_core/icosahedron_phi.html").read_text()
        start = page.index("const MODEL = ") + len("const MODEL = ")
        end = page.index(";\nconst PHI_APPROX", start)
        model = json.loads(page[start:end])
        self.assertEqual(model["vertices_phi"], FIXTURE["vertices_phi"])
        self.assertEqual(model["edges"], FIXTURE["edges"])
        self.assertEqual(model["faces"], FIXTURE["faces"])
        symmetry_fixture = json.loads(
            (ROOT / "fixtures/golden_core_gc4_icosahedral_symmetries.json").read_text())
        self.assertEqual(model["symmetries"], symmetry_fixture["symmetries"])
        self.assertIn("approximate floating-point camera projection", page.lower())
        self.assertIn("exact coordinate", page.lower())
        self.assertIn("orientation-reversing", page.lower())
        self.assertIn("distinguished vertex / weight", page)
        self.assertIn("w2", page)
        self.assertIn("exact weight 2", page)
        self.assertIn("addEventListener(\"click\"", page)


if __name__ == "__main__":
    unittest.main(verbosity=2)
