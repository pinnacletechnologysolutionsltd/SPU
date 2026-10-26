"""Focused tests for the frozen held-out Soul-0 fixture and operation counters."""

from __future__ import annotations

import unittest

from software.research.soul0.counted import (
    CountedRollingMean,
    CountedSoul0,
    CountedStateless,
    as_reference_soul,
)
from software.research.soul0.heldout_experiment import (
    _validate_transient_envelopes,
    load_frozen_inputs,
)
from software.research.soul0.model import RollingMeanBaseline, Soul0, StatelessBaseline


class Soul0HeldoutTest(unittest.TestCase):
    def test_fixture_transients_are_outside_all_noise_bounded_prototypes(self) -> None:
        fixture, _, _ = load_frozen_inputs()
        envelopes = _validate_transient_envelopes(fixture)
        for phase_name, phase in fixture["phases"].items():
            index = phase["fault_index"]
            normal = phase["nominal_center"] + fixture["noise_cycle"][index % 5]
            self.assertEqual(phase["values"][index], normal + 140, phase_name)
            self.assertGreater(envelopes[phase_name]["minimum_distance"], fixture["threshold"])
        self.assertEqual(envelopes["regime_a"]["margin"], 16)
        self.assertEqual(envelopes["regime_c"]["margin"], 66)

    def test_counted_models_match_reference_decisions_and_state(self) -> None:
        fixture, _, _ = load_frozen_inputs()
        training = fixture["training"]
        center = sum(training) // len(training)
        reference_soul = Soul0([(center, len(training))], threshold=20, capacity=3)
        counted_soul = CountedSoul0([(center, len(training))], threshold=20, capacity=3)
        reference_stateless = StatelessBaseline(center, 20)
        counted_stateless = CountedStateless(center, 20)
        reference_rolling = RollingMeanBaseline(training, 20, window=8)
        counted_rolling = CountedRollingMean(training, 20, window=8)
        for phase in fixture["phases"].values():
            for value in phase["values"]:
                self.assertEqual(counted_soul.observe(value)[0], reference_soul.observe(value)[0])
                self.assertEqual(as_reference_soul(counted_soul).to_bytes(), reference_soul.to_bytes())
                self.assertEqual(counted_stateless.observe(value)[0], reference_stateless.observe(value)[0])
                self.assertEqual(counted_rolling.observe(value)[0], reference_rolling.observe(value)[0])
                self.assertEqual(counted_rolling.values, reference_rolling.values)

    def test_primitive_counts_cover_executed_update_operations(self) -> None:
        stateless = CountedStateless(100, 20)
        rolling = CountedRollingMean([98, 99, 100, 101, 102, 98, 99, 100], 20, window=8)
        soul = CountedSoul0([(100, 8)], threshold=20, capacity=3)
        self.assertEqual(stateless.observe(101)[1], 3)
        self.assertEqual(rolling.observe(101)[1], 11)
        self.assertEqual(soul.observe(100)[1], 7)
        self.assertEqual(soul.observe(200)[1], 4)

    def test_seeded_profile_stall_is_preserved_as_a_regression(self) -> None:
        fixture, _, _ = load_frozen_inputs()
        soul = CountedSoul0([(180, 2)], threshold=20, capacity=3)
        healthy_values = [
            fixture["phases"]["regime_b"]["nominal_center"] + fixture["noise_cycle"][index % 5]
            for index in range(16)
        ]
        for value in healthy_values:
            soul.observe(value)
        self.assertEqual(soul.profiles[0].center, 193)
        self.assertGreater(abs(soul.profiles[0].center - 200), 5)
        self.assertEqual(len(soul.profiles), 1)

    def test_threshold_equality_is_inside_acceptance_region(self) -> None:
        soul = CountedSoul0([(100, 8)], threshold=20, capacity=3)
        self.assertFalse(soul.observe(120)[0])


if __name__ == "__main__":
    unittest.main()
