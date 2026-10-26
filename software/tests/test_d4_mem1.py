"""Deterministic finite-workload checks for D4-MEM-1."""

import unittest

from software.research.d4_symmetry.canonical import GROUP, orbit
from software.research.d4_symmetry.mem1 import MISS, SOURCES, evaluate
from software.research.d4_symmetry.memory import OrbitMemory


class D4Mem1Tests(unittest.TestCase):
    def test_frozen_orbit_sizes_and_stabilizer_action_contract(self):
        self.assertEqual(len(GROUP), 192)
        self.assertEqual([len(orbit(vector)) for vector, _ in SOURCES], [192, 48])
        memory = OrbitMemory()
        with self.assertRaisesRegex(ValueError, "D4_ACTION_NOT_STABILIZER_FIXED"):
            memory.store((1, 1, 2, 2), "bad", action=(1, 0, 0, 0))

    def test_comparison_results_and_non_equivalent_miss(self):
        result = evaluate()
        self.assertEqual(result["orbit_sizes"], {"generic": 192, "stabilizer": 48})
        strategies = result["strategies"]
        for name in ("augmented", "canonical", "group_aware"):
            row = strategies[name]
            self.assertEqual(row["payload_correct_supported_queries"], row["supported_query_occurrences"])
            self.assertEqual(row["action_correct_supported_queries"], row["supported_query_occurrences"])
            self.assertEqual(row["false_aliases"], 0)
        self.assertEqual(strategies["raw"]["payload_correct_supported_queries"], 4)
        self.assertEqual(strategies["raw"]["action_correct_supported_queries"], 4)
        self.assertEqual(strategies["raw"]["false_aliases"], 0)
        for name, row in strategies.items():
            self.assertEqual(row["misses"], 239 if name == "raw" else 1)
            self.assertGreater(row["serialized_association_bytes"], 0)
            self.assertEqual(
                row["total_operations"],
                sum(row["preparation_operations"].values())
                + sum(row["query_operations"].values()),
            )
        self.assertEqual(MISS, (1, 2, 4, 8))


if __name__ == "__main__":
    unittest.main()
