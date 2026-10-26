"""Focused mathematical and fixture checks for D4-CYCLE-0."""

import unittest

from software.research.lattice_comparison import d4
from software.research.d4_symmetry.cycle import (
    IDENTITY_D4, act, compose, compose_edges, edge_from_frames, inverse,
    matches_expected,
)
from software.research.d4_symmetry.cycle_demo import (
    CORRUPT_BY, CYCLES, FRAMES, GAUGES, HOLONOMY, _cycle_edges, evaluate,
)
from software.research.d4_symmetry.types import (
    FrameID, GroupElementD4, OrbitKey, RelationEdge, SymmetryState,
    TransformWitness,
)


class D4CycleTests(unittest.TestCase):
    def test_typed_group_order_closure_and_inverses(self):
        typed = tuple(GroupElementD4(item) for item in d4.group())
        self.assertEqual(192, len(set(typed)))
        for left in typed:
            inv = inverse(left)
            self.assertEqual(IDENTITY_D4, compose(left, inv))
            self.assertEqual(IDENTITY_D4, compose(inv, left))
            for right in typed:
                self.assertIn(compose(left, right), set(typed))

    def test_composition_order_against_sequential_vector_action(self):
        left = GroupElementD4(d4.descriptor((0, 3, 1)))
        right = GroupElementD4(d4.descriptor((2, 0)))
        vector = (2, -3, 5, 11)
        sequential = act(left, act(right, vector))
        self.assertEqual(sequential, act(compose(left, right), vector))
        self.assertEqual((0, 0, 0, 0), act(IDENTITY_D4, (0, 0, 0, 0)))

    def test_invalid_typed_values_rejected(self):
        with self.assertRaises(ValueError):
            FrameID("")
        with self.assertRaises(ValueError):
            GroupElementD4(((0, 0, 2, 3), (0, 0, 0, 0)))
        with self.assertRaises(ValueError):
            SymmetryState("quadray", FrameID("A"), (1, 2, 3))
        with self.assertRaises(ValueError):
            SymmetryState("quadray", FrameID("A"), (1, 2, True, 4))
        with self.assertRaises(ValueError):
            OrbitKey("quadray", (1, 2, 3))
        with self.assertRaises(ValueError):
            TransformWitness(FrameID("A"), "B", IDENTITY_D4)
        with self.assertRaises(ValueError):
            RelationEdge("A", FrameID("B"), IDENTITY_D4)

    def test_path_must_be_typed_contiguous_and_closed(self):
        a, b, c = (FrameID(name) for name in "ABC")
        ab, bc, ca = (RelationEdge(a, b, IDENTITY_D4),
                      RelationEdge(b, c, IDENTITY_D4),
                      RelationEdge(c, a, IDENTITY_D4))
        self.assertEqual(IDENTITY_D4, compose_edges((ab, bc, ca)))
        with self.assertRaises(ValueError):
            compose_edges((ab, RelationEdge(c, b, IDENTITY_D4), ca))
        with self.assertRaises(ValueError):
            compose_edges((ab, bc))
        with self.assertRaises(ValueError):
            compose_edges((ab, "bad"))

    def test_frozen_consistent_frame_graph_cycles_are_identity(self):
        edge_map = {}
        for i, source in enumerate(FRAMES):
            for j, target in enumerate(FRAMES):
                if i != j:
                    edge_map[(source, target)] = edge_from_frames(
                        source, target, GAUGES[i], GAUGES[j])
        products = [compose_edges(_cycle_edges(fixture[1:], edge_map))
                    for fixture in CYCLES]
        self.assertEqual(7, len(products))
        self.assertTrue(all(product == IDENTITY_D4 for product in products))

    def test_corruption_is_detected_by_redundant_cycles_not_localized(self):
        report = evaluate()["corrupted_graph"]
        self.assertEqual("A->B", report["corrupted_edge"])
        self.assertTrue(report["inconsistent_cycles"])
        self.assertIn("BCD", [row["cycle"] for row in report["cycles"]
                               if row["matches"]])
        self.assertFalse(report["unique_fault_localization_claimed"])
        self.assertTrue(set(report["candidate_edges_only"]).issuperset({"A->B"}))

    def test_nontrivial_holonomy_is_expected_when_declared(self):
        report = evaluate()["prescribed_holonomy"]
        self.assertEqual(HOLONOMY.descriptor, report["actual"])
        self.assertTrue(report["matches_declared_expectation"])
        self.assertFalse(report["matches_identity_expectation"])
        self.assertNotEqual(IDENTITY_D4.descriptor, CORRUPT_BY.descriptor)


if __name__ == "__main__":
    unittest.main()
