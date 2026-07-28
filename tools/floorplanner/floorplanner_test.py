#!/usr/bin/env python3
"""Focused regression tests for the abstract floorplan planners."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import coordinate_transformer as ct
from generate_spu4_floorplan import generate_vector_equilibrium_coords


class FloorplannerTest(unittest.TestCase):
    def test_hilbert_order_two_is_unique_and_edge_contiguous(self) -> None:
        points = ct.hilbert_curve(2)
        self.assertEqual(len(points), 16)
        cells = [(int(x * 4), int(y * 4)) for x, y in points]
        self.assertEqual(len(set(cells)), 16)
        for first, second in zip(cells, cells[1:]):
            self.assertEqual(
                abs(first[0] - second[0]) + abs(first[1] - second[1]), 1
            )

    def test_sierpinski_carpet_is_a_point_set(self) -> None:
        points = ct.sierpinski_carpet(2)
        self.assertEqual(len(points), 64)
        self.assertEqual(len(set(points)), 64)
        self.assertNotIn((0.5, 0.5), points)

    def test_mapping_respects_inclusive_bounds(self) -> None:
        grid = ct.GridBounds(4, 12, 7, 11, "test")
        self.assertEqual(ct.map_normalized_to_grid(0.0, 0.0, grid), (4, 7))
        self.assertEqual(ct.map_normalized_to_grid(1.0, 1.0, grid), (12, 11))

    def test_collision_failure_is_explicit(self) -> None:
        grid = ct.GridBounds(0, 0, 0, 0, "test")
        with self.assertRaises(RuntimeError):
            ct.find_nearest_free(0, 0, {(0, 0)}, grid, max_radius=2)

    def test_plan_rejects_more_names_than_geometry(self) -> None:
        grid = ct.GridBounds(0, 3, 0, 3, "test")
        with self.assertRaises(ValueError):
            ct.plan_anchors(["a", "b"], [(0.5, 0.5)], grid, max_radius=1)

    def test_exact_packed_cell_validation(self) -> None:
        netlist = {"modules": {"top": {"cells": {"packed_a": {}, "packed_b": {}}}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "netlist.json"
            path.write_text(json.dumps(netlist), encoding="utf-8")
            ct.validate_packed_cell_names(["packed_a"], path)
            with self.assertRaises(ValueError):
                ct.validate_packed_cell_names(["logical_module"], path)

    def test_vector_equilibrium_projection_is_bounded(self) -> None:
        points = generate_vector_equilibrium_coords(radius=0.12)
        self.assertEqual(len(points), 13)
        self.assertEqual(points[0], (0.5, 0.5))
        self.assertTrue(
            all(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 for x, y in points)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
