#!/usr/bin/env python3
"""Exact full-group, incidence, orientation, and structure classification."""

import contextlib
import hashlib
import io
import json
import runpy
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

from golden_core.exact import ONE, Q5, ZERO
from golden_core.icosahedron import edges, faces, vertices
from golden_core.symmetry import icosahedral_symmetries

FIXTURE_PATH = ROOT / "fixtures/golden_core_gc4_icosahedral_symmetries.json"
FIXTURE_BYTES = FIXTURE_PATH.read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)
FIXTURE_SHA256 = "6321eb4d3f753094cabd210588edfc38d726fa4aef4c0b70e39f7e597390d776"


class GoldenCoreGc4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = vertices()
        cls.edge_set = set(edges(cls.points))
        cls.face_set = set(faces(cls.points))
        cls.symmetries = icosahedral_symmetries()

    def test_fixture_is_frozen_and_matches_exact_enumeration(self):
        self.assertEqual(hashlib.sha256(FIXTURE_BYTES).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(len(self.points), FIXTURE["vertex_count"])
        self.assertEqual(len(self.edge_set), FIXTURE["edge_count"])
        self.assertEqual(len(self.face_set), FIXTURE["face_count"])
        actual = [{"vertex_image": list(s.vertex_image), "determinant": s.determinant}
                  for s in self.symmetries]
        self.assertEqual(actual, FIXTURE["symmetries"])

    def test_full_group_has_60_proper_and_60_orientation_reversing_maps(self):
        counts = Counter(s.determinant for s in self.symmetries)
        self.assertEqual(len(self.symmetries), 120)
        self.assertEqual(counts, {1: 60, -1: 60})
        self.assertEqual(FIXTURE["unlabelled"], {
            "total": 120, "proper": 60, "orientation_reversing": 60,
        })
        index_of = {point: i for i, point in enumerate(self.points)}
        inversion = tuple(index_of[type(point)(-point.x, -point.y, -point.z)]
                          for point in self.points)
        self.assertIn((inversion, -1),
                      {(s.vertex_image, s.determinant) for s in self.symmetries})

    def test_enumerated_permutations_are_closed_under_composition(self):
        group = {s.vertex_image for s in self.symmetries}
        for left in group:
            for right in group:
                composed = tuple(left[right[i]] for i in range(12))
                self.assertIn(composed, group)

    def test_every_map_preserves_exact_vertices_edges_faces_and_metric(self):
        point_index = {point: i for i, point in enumerate(self.points)}
        edge_set, face_set = self.edge_set, self.face_set
        identity = ((ONE, ZERO, ZERO), (ZERO, ONE, ZERO), (ZERO, ZERO, ONE))
        for symmetry in self.symmetries:
            self.assertEqual(set(symmetry.vertex_image), set(range(12)))
            self.assertEqual(_matmul(_transpose(symmetry.matrix), symmetry.matrix), identity)
            mapped_edges = {tuple(sorted((symmetry.vertex_image[i],
                                          symmetry.vertex_image[j])))
                            for i, j in edge_set}
            mapped_faces = {tuple(sorted(symmetry.vertex_image[i] for i in face))
                            for face in face_set}
            self.assertEqual(mapped_edges, edge_set)
            self.assertEqual(mapped_faces, face_set)
            for index, point in enumerate(self.points):
                self.assertEqual(point_index[_apply(symmetry.matrix, point)],
                                 symmetry.vertex_image[index])

    def test_structure_labels_and_weights_reduce_geometric_symmetry(self):
        marked = [1] + [0] * 11
        single_weight = [2] + [1] * 11
        unique_labels = list(range(12))
        marked_group = [s for s in self.symmetries
                        if s.preserves_attributes(labels=marked)]
        weighted_group = [s for s in self.symmetries
                          if s.preserves_attributes(weights=single_weight)]
        uniquely_labelled = [s for s in self.symmetries
                             if s.preserves_attributes(labels=unique_labels)]
        self.assertEqual(len(marked_group), 10)
        self.assertEqual(len(weighted_group), 10)
        self.assertEqual(Counter(s.determinant for s in marked_group), {1: 5, -1: 5})
        self.assertEqual(len(uniquely_labelled), 1)
        self.assertEqual(uniquely_labelled[0].vertex_image, tuple(range(12)))
        self.assertEqual(FIXTURE["single_marked_vertex_0"], {
            "total": 10, "proper": 5, "orientation_reversing": 5,
        })
        self.assertEqual(FIXTURE["all_vertices_uniquely_labelled"]["total"], 1)
        self.assertEqual(len(self.symmetries), 120)  # unlabelled solid stays achiral

    def test_arbitrary_vertex_swap_is_not_a_geometric_symmetry(self):
        swap = list(range(12))
        swap[0], swap[1] = swap[1], swap[0]
        self.assertNotIn(tuple(swap), {s.vertex_image for s in self.symmetries})
        image_edges = {tuple(sorted((swap[i], swap[j]))) for i, j in self.edge_set}
        self.assertNotEqual(image_edges, self.edge_set)

    def test_proper_group_matches_independent_retained_flag_construction(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            oracle = runpy.run_path(str(ROOT / "software/tests/test_icosahedral_catalog.py"))
        self.assertEqual(oracle["fails"], 0)
        self.assertEqual(oracle["checks"], 23)
        def convert(value):
            return Q5.from_phi(value.a, value.b)
        converted = {tuple(tuple(convert(value) for value in row) for row in matrix)
                     for matrix in oracle["rset"]}
        proper = {s.matrix for s in self.symmetries if s.proper}
        self.assertEqual(len(converted), 60)
        self.assertEqual(proper, converted)


def _matmul(left, right):
    return tuple(tuple(sum((left[i][k] * right[k][j] for k in range(3)), ZERO)
                       for j in range(3)) for i in range(3))


def _transpose(matrix):
    return tuple(tuple(matrix[j][i] for j in range(3)) for i in range(3))


def _apply(matrix, point):
    values = (point.x, point.y, point.z)
    from golden_core.icosahedron import Vec3
    return Vec3(*(sum((matrix[i][j] * values[j] for j in range(3)), ZERO)
                  for i in range(3)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
