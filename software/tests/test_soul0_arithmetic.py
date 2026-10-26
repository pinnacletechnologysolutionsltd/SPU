"""Focused tests for the separate arithmetic and memory-policy study."""

from __future__ import annotations

from fractions import Fraction
import json
import unittest

from software.research.soul0.arithmetic import ArithmeticModel, KINDS, make_models
from software.research.soul0.arithmetic_study import _center, load_frozen


class Soul0ArithmeticTest(unittest.TestCase):
    def test_remainder_policy_matches_exact_cumulative_sum_exhaustively(self) -> None:
        values = tuple(range(-4, 5))
        # Exhaust every bounded valid (center, count, remainder, input) state.
        # This one-step invariant proves sequence correspondence by induction;
        # the frozen long streams below also exercise concrete trajectories.
        saw_negative_numerator = False
        saw_negative_residual = False
        for center in values:
            for count in range(1, 5):
                for remainder_value in range(count):
                    total = center * count + remainder_value
                    if not -4 * count <= total <= 4 * count:
                        continue
                    for sample in values:
                        exact = ArithmeticModel("B", [0] * 8)
                        exact.total = total
                        exact.count = count
                        carried = ArithmeticModel("C", [0] * 8)
                        carried.center = center
                        carried.count = count
                        carried.remainder = remainder_value
                        saw_negative_numerator |= total + sample < 0
                        saw_negative_residual |= sample * count - total < 0
                        self.assertEqual(exact.observe(sample)[0], carried.observe(sample)[0])
                        self.assertEqual(exact.total, carried.center * carried.count + carried.remainder)
                        self.assertEqual(exact.exact_center_pair(), carried.exact_center_pair())
                        self.assertGreaterEqual(carried.remainder, 0)
                        self.assertLess(carried.remainder, carried.count)
        self.assertTrue(saw_negative_numerator)
        self.assertTrue(saw_negative_residual)

    def test_regression_matches_independent_fraction_oracle_and_preserves_floor_stall(self) -> None:
        fixture, _, _ = load_frozen()
        regression = fixture["arithmetic_regression"]
        models = {
            kind: ArithmeticModel(kind, [regression["initial_center"]] * regression["initial_count"])
            for kind in ("A", "B", "C", "D")
        }
        exact_total = regression["initial_center"] * regression["initial_count"]
        count = regression["initial_count"]
        for sample in regression["values"]:
            exact_total += sample
            count += 1
            oracle = Fraction(exact_total, count)
            for kind in ("B", "C"):
                models[kind].observe(sample)
                self.assertEqual(_center(models[kind]), oracle)
            models["A"].observe(sample)
            models["D"].observe(sample)
        self.assertEqual(models["A"].center, 193)
        self.assertEqual(models["C"].center * models["C"].count + models["C"].remainder,
                         models["B"].total)
        self.assertNotEqual(_center(models["B"]), Fraction(models["A"].center, 1))

    def test_exact_and_remainder_models_match_fraction_on_frozen_streams(self) -> None:
        fixture, _, _ = load_frozen()
        phase_order = ("regime_b", "regime_c", "regime_a_return", "regime_b_return")
        models = {kind: ArithmeticModel(kind, fixture["training"]) for kind in ("B", "C")}
        total = sum(fixture["training"])
        count = len(fixture["training"])
        for phase in phase_order:
            for value in fixture["adaptation_phases"][phase]:
                total += value
                count += 1
                expected = Fraction(total, count)
                for model in models.values():
                    model.observe(value)
                    self.assertEqual(_center(model), expected)

        alert_models = {kind: ArithmeticModel(kind, fixture["training"]) for kind in ("B", "C")}
        total = sum(fixture["training"])
        count = len(fixture["training"])
        for phase in ("regime_a", "regime_b", "regime_c", "regime_a_return", "regime_b_return"):
            for value in fixture["alert_phases"][phase]["values"]:
                total += value
                count += 1
                expected = Fraction(total, count)
                for model in alert_models.values():
                    model.observe(value)
                    self.assertEqual(_center(model), expected)

    def test_primitive_operation_counts_on_one_update(self) -> None:
        expected = {"A": 7, "B": 7, "C": 11, "D": 9, "E": 12, "F": 8}
        for kind, model in make_models([98, 99, 100, 101, 102, 98, 99, 100]).items():
            self.assertEqual(model.observe(101)[1], expected[kind], kind)

    def test_checkpoint_round_trip_is_bit_identical_and_rejects_invalid_data(self) -> None:
        models = make_models([98, 99, 100, 101, 102, 98, 99, 100])
        for kind, model in models.items():
            model.observe(200)
            checkpoint = model.to_bytes()
            restored = ArithmeticModel.from_bytes(checkpoint)
            self.assertEqual(restored.to_bytes(), checkpoint, kind)
            self.assertEqual(restored.observe(201), model.observe(201), kind)
            self.assertEqual(restored.to_bytes(), model.to_bytes(), kind)
            before = model.to_bytes()
            with self.assertRaises(ValueError):
                ArithmeticModel.from_bytes(checkpoint[: max(1, len(checkpoint) // 2)])
            self.assertEqual(model.to_bytes(), before)

        carried = ArithmeticModel("C", [98, 99, 100, 101, 102, 98, 99, 100])
        state = json.loads(carried.to_bytes())
        state["state"]["remainder"] = state["state"]["count"]
        with self.assertRaises(ValueError):
            ArithmeticModel.from_bytes(json.dumps(state).encode("ascii"))

    def test_invalid_observation_and_count_overflow_do_not_mutate_state(self) -> None:
        for kind in ("A", "B", "C", "D"):
            model = ArithmeticModel(kind, [0] * 8)
            before = model.to_bytes()
            with self.assertRaises(ValueError):
                model.observe(512)
            self.assertEqual(model.to_bytes(), before)
            model.count = 264
            before = model.to_bytes()
            with self.assertRaises(OverflowError):
                model.observe(0)
            self.assertEqual(model.to_bytes(), before)

    def test_frozen_stream_and_model_state_widths(self) -> None:
        fixture, _, _ = load_frozen()
        self.assertEqual(len(fixture["adaptation_phases"]["regime_b"]), 64)
        expected_bytes = {"A": 4, "B": 5, "C": 6, "D": 5, "E": 16, "F": 3}
        for kind, model in make_models(fixture["training"], fixture["threshold"]).items():
            self.assertEqual(model.logical_state_bytes, expected_bytes[kind], kind)

    def test_exact_model_types_are_closed(self) -> None:
        self.assertEqual(KINDS, ("A", "B", "C", "D", "E", "F"))


if __name__ == "__main__":
    unittest.main()
