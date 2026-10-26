#!/usr/bin/env python3
"""Exact Quadray transformations and T1d simulator regression fixture."""

from __future__ import annotations

import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.lib.gc2b_weighted_cycle import (  # noqa: E402
    Q3, apply_f, p_transport, transported_weights, vector, vector_payload,
)
from software.spu_gpu_eval.device_model import pixel_decision as device_pixel_decision  # noqa: E402
from software.spu_gpu_eval.device_model import prepare_scene  # noqa: E402
from software.spu_gpu_eval.packet import compile_packet  # noqa: E402
from software.spu_gpu_eval.quadray import (  # noqa: E402
    ALL_PERMUTATIONS, DEMO_POINTS, TETRA_BASIS, active_permutation,
    VIEW_MATRIX, distance_squared, determinant3, make_demo_scene, matrix_apply,
    permutation_sign, project_to_t1d, quadrance, quadray_to_cartesian,
    round_fraction_even, spatial_determinant_sign, zero_sum,
)
from software.spu_gpu_eval.reference import pixel_decision as ideal_pixel_decision  # noqa: E402
from software.spu_gpu_eval.scene import parse_scene_bytes  # noqa: E402


SCENE_PATH = ROOT / "examples/gpu/golden_core_quadray_covariance.json"
REFERENCE_PATH = ROOT / "fixtures/golden_core_quadray_projection_reference.json"


def exact_vector(values):
    return tuple(Fraction(value) for value in values)


def xyz_distance_squared(p, q):
    pp, qq = quadray_to_cartesian(p), quadray_to_cartesian(q)
    return sum(((a - b) ** 2 for a, b in zip(pp, qq)), Fraction(0))


def signed_area2(triangle):
    v0, v1, v2 = triangle.vertices
    return ((v1.x - v0.x) * (v2.y - v0.y)
            - (v1.y - v0.y) * (v2.x - v0.x))


class QuadrayGpuSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        cls.raw_scene = SCENE_PATH.read_bytes()
        cls.scene = parse_scene_bytes(cls.raw_scene)

    def test_gauge_distance_and_all_permutation_orientation_classes(self):
        q = exact_vector((3, 1, 0, -2))
        offset = Fraction(7, 3)
        shifted = tuple(value + offset for value in q)
        self.assertEqual(zero_sum(q), zero_sum(shifted))
        self.assertEqual(quadray_to_cartesian(q), quadray_to_cartesian(shifted))
        self.assertEqual(quadrance(q), quadrance(shifted))
        self.assertEqual(sum(zero_sum(q), Fraction(0)), 0)

        other = exact_vector((-1, 2, 3, 0))
        self.assertEqual(distance_squared(q, other), xyz_distance_squared(q, other))
        proper = improper = unlabelled_matches = 0
        labelled_matches = 0
        basis_points = set(TETRA_BASIS)
        for permutation in ALL_PERMUTATIONS:
            sign = permutation_sign(permutation)
            spatial_sign = spatial_determinant_sign(permutation)
            self.assertEqual(spatial_sign, sign)
            proper += spatial_sign == 1
            improper += spatial_sign == -1
            self.assertEqual(quadrance(active_permutation(q, permutation)), quadrance(q))
            mapped_set = {quadray_to_cartesian(active_permutation(point, permutation))
                          for point in DEMO_POINTS}
            self.assertEqual(mapped_set, basis_points)
            unlabelled_matches += mapped_set == basis_points
            labelled_matches += all(permutation[i] == i for i in range(4))
        self.assertEqual((proper, improper), (12, 12))
        self.assertEqual(unlabelled_matches,
                         self.reference["permutation_examples"]["unlabelled_regular_tetrahedron_matches"])
        self.assertEqual(labelled_matches,
                         self.reference["permutation_examples"]["distinct_fixed_vertex_labels_preserving_permutations"])

    def test_proper_rotation_and_reflection_examples(self):
        examples = self.reference["permutation_examples"]
        rotation = tuple(examples["proper_rotation_bcd"]["source_to_target"])
        reflection = tuple(examples["reflection_bc"]["source_to_target"])
        self.assertEqual(permutation_sign(rotation), 1)
        self.assertEqual(spatial_determinant_sign(rotation), 1)
        self.assertEqual(permutation_sign(reflection), -1)
        self.assertEqual(spatial_determinant_sign(reflection), -1)
        self.assertEqual(active_permutation(exact_vector((1, 2, 3, 4)), rotation),
                         exact_vector((1, 4, 2, 3)))
        self.assertEqual(active_permutation(exact_vector((1, 2, 3, 4)), reflection),
                         exact_vector((1, 3, 2, 4)))
        point_fixture = self.reference["interactive_point"]
        point = exact_vector(point_fixture["quadray"])
        self.assertEqual(list(quadray_to_cartesian(point)),
                         [Fraction(value) for value in point_fixture["cartesian"]])
        screen = project_to_t1d(point)
        self.assertEqual([screen.x, screen.y, screen.z], point_fixture["t1d_screen_xy_depth"])
        for permutation, case in ((rotation, "proper_rotation_bcd"),
                                  (reflection, "reflection_bc")):
            moved = active_permutation(point, permutation)
            expected = point_fixture[case]
            self.assertEqual(list(moved), [Fraction(value) for value in expected["quadray"]])
            screen = project_to_t1d(moved)
            self.assertEqual([screen.x, screen.y, screen.z], expected["t1d_screen_xy_depth"])

    def test_rational_view_is_orientation_preserving_and_rounding_is_frozen(self):
        identity = ((Fraction(1), Fraction(0), Fraction(0)),
                    (Fraction(0), Fraction(1), Fraction(0)),
                    (Fraction(0), Fraction(0), Fraction(1)))
        for i, row in enumerate(VIEW_MATRIX):
            for j, other in enumerate(VIEW_MATRIX):
                dot = sum((a * b for a, b in zip(row, other)), Fraction(0))
                self.assertEqual(dot, identity[i][j])
        self.assertEqual(determinant3(VIEW_MATRIX), 1)
        self.assertEqual([list(quadray_to_cartesian(point)) for point in DEMO_POINTS],
                         [[Fraction(value) for value in row]
                          for row in self.reference["projection"]["cartesian_points"]])
        self.assertEqual(matrix_apply(VIEW_MATRIX, (Fraction(1), Fraction(0), Fraction(0))),
                         (Fraction(1, 9), Fraction(8, 9), Fraction(-4, 9)))
        self.assertEqual([round_fraction_even(Fraction(n, 2)) for n in (5, 7, -5, -7)],
                         [2, 4, -2, -4])

    def test_exact_projection_is_frozen_into_t1d_scene(self):
        expected_vertices = self.reference["projection"]["t1d_screen_xy_depth"]
        projected = [project_to_t1d(point) for point in DEMO_POINTS]
        self.assertEqual([[v.x, v.y, v.z] for v in projected], expected_vertices)
        self.assertEqual([list(quadray_to_cartesian(point)) for point in DEMO_POINTS],
                         [[Fraction(value) for value in row]
                          for row in self.reference["projection"]["cartesian_points"]])
        self.assertEqual(make_demo_scene(), self.scene)
        self.assertEqual([signed_area2(triangle) for triangle in self.scene.triangles],
                         self.reference["projection"]["signed_twice_areas"])

    def test_independent_expected_pixels_match_ideal_and_device_simulators(self):
        device_scene = prepare_scene(compile_packet(self.scene))
        for expected in self.reference["gpu_samples"]:
            x, y = expected["x"], expected["y"]
            ideal = ideal_pixel_decision(self.scene, x, y)
            device = device_pixel_decision(device_scene, x, y)
            for result in (ideal, device):
                self.assertEqual(result["coverage"], expected["coverage"])
                self.assertEqual(result["winner"], expected["winner"])
                self.assertEqual(result["rgb"], expected["rgb"])

    def test_gc2b_weighted_covariance_uses_the_frozen_single_parity_transport(self):
        reference = self.reference["weighted_covariance"]
        weights = vector(tuple(Q3(*pair) for pair in reference["weights"]))
        mirrored = transported_weights(weights)
        state = vector(tuple(Q3(*pair) for pair in reference["initial_state"]))
        self.assertEqual(vector_payload(mirrored),
                         [[str(p), str(q)] for p, q in reference["mirrored_weights"]])
        self.assertEqual(vector_payload(p_transport(state)),
                         [[str(p), str(q)] for p, q in ((1, 0), (2, 0), (0, 1), (0, 0))])
        for law_key, expected_key in (("neutral_law", "expected_covariant_state_neutral"),
                                      ("biased_law", "expected_covariant_state_biased")):
            a, b = (Q3(*pair) for pair in reference[law_key])
            lhs = p_transport(apply_f(state, weights, a, b))
            rhs = apply_f(p_transport(state), mirrored, b, a)
            self.assertEqual(lhs, rhs)
            self.assertEqual(vector_payload(lhs),
                             [[str(p), str(q)] for p, q in reference[expected_key]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
