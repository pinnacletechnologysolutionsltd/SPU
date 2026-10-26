#!/usr/bin/env python3
"""GC-5A fixed-seed trajectories, exact parity transport, and observables."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

from golden_core.dynamics import (coefficient_max_bit_length, state_sha256,
                                  state_sum, trajectory, turn_channel_imbalance)
from golden_core.exact import ONE, Q5, ZERO
from golden_core.oriented_edge_turns import OrientedEdgeTurns
from golden_core.symmetry import icosahedral_symmetries

FIXTURE_PATH = ROOT / "fixtures/golden_core_gc5a_edge_dynamics.json"
FIXTURE_BYTES = FIXTURE_PATH.read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)
FIXTURE_SHA256 = "09c5af3a2f3d72447ee9bf3adfa8dc37e641e0de9d6608178f73720bc4b22fa4"
STEPS = 12
EQUAL = (ONE, ONE)
SIGNED = (Q5(3, 1), Q5(1, -1))


def push(state, image):
    result = [ZERO] * len(state)
    for source, target in enumerate(image):
        result[target] = state[source]
    return tuple(result)


def pair(value):
    return [[value.a.numerator, value.a.denominator],
            [value.b.numerator, value.b.denominator]]


def trajectory_record(states, turns, seed_index):
    return [{
        "step": step,
        "state_sha256": state_sha256(state),
        "max_coefficient_bit_length": coefficient_max_bit_length(state),
        "total_coefficient_sum": pair(state_sum(state)),
        "left_minus_right_probe": pair(turn_channel_imbalance(state, seed_index, turns)),
    } for step, state in enumerate(states)]


class GoldenCoreGc5aTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.turns = OrientedEdgeTurns.build()
        cls.symmetries = icosahedral_symmetries()
        cls.edge_index = {edge: i for i, edge in enumerate(cls.turns.directed_edges)}
        cls.seed_index = cls.edge_index[(0, 1)]
        cls.initial = tuple(ONE if i == cls.seed_index else ZERO for i in range(60))

    def edge_image(self, symmetry):
        return tuple(self.edge_index[(symmetry.vertex_image[u],
                                      symmetry.vertex_image[v])]
                     for u, v in self.turns.directed_edges)

    def test_frozen_configuration_and_per_step_measurements(self):
        self.assertEqual(hashlib.sha256(FIXTURE_BYTES).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(FIXTURE["steps"], STEPS)
        self.assertEqual(FIXTURE["initial_edge"], [0, 1])
        self.assertEqual(FIXTURE["profiles"], {
            "equal": {"left": "1", "right": "1"},
            "signed": {"left": "3+sqrt(5)", "right": "1-sqrt(5)"},
        })
        equal_states = trajectory(self.initial, self.turns, *EQUAL, STEPS)
        signed_states = trajectory(self.initial, self.turns, *SIGNED, STEPS)
        self.assertEqual(trajectory_record(equal_states, self.turns, self.seed_index),
                         FIXTURE["trajectories"]["equal"])
        self.assertEqual(trajectory_record(signed_states, self.turns, self.seed_index),
                         FIXTURE["trajectories"]["signed"])

    def test_exact_mirror_trajectories_for_all_spatial_maps(self):
        equal_states = trajectory(self.initial, self.turns, *EQUAL, STEPS)
        signed_states = trajectory(self.initial, self.turns, *SIGNED, STEPS)
        counts = {"equal": {"proper": 0, "orientation_reversing": 0},
                  "signed": {"proper": 0, "orientation_reversing": 0}}
        for symmetry in self.symmetries:
            image = self.edge_image(symmetry)
            mirrored_seed = push(self.initial, image)
            equal_mirror = trajectory(mirrored_seed, self.turns, *EQUAL, STEPS)
            if symmetry.determinant == -1:
                signed_mirror = trajectory(mirrored_seed, self.turns,
                                           SIGNED[1], SIGNED[0], STEPS)
                group = "orientation_reversing"
            else:
                signed_mirror = trajectory(mirrored_seed, self.turns, *SIGNED, STEPS)
                group = "proper"
            counts["equal"][group] += 1
            counts["signed"][group] += 1
            mirrored_seed_index = image[self.seed_index]
            for step in range(STEPS + 1):
                self.assertEqual(push(equal_states[step], image), equal_mirror[step])
                self.assertEqual(push(signed_states[step], image), signed_mirror[step])
                equal_probe = turn_channel_imbalance(equal_states[step], self.seed_index,
                                                     self.turns)
                equal_mirror_probe = turn_channel_imbalance(equal_mirror[step],
                                                            mirrored_seed_index, self.turns)
                signed_probe = turn_channel_imbalance(signed_states[step], self.seed_index,
                                                     self.turns)
                signed_mirror_probe = turn_channel_imbalance(signed_mirror[step],
                                                             mirrored_seed_index, self.turns)
                sign = -1 if symmetry.determinant == -1 else 1
                signed_equal_probe = -equal_probe if sign < 0 else equal_probe
                signed_signed_probe = -signed_probe if sign < 0 else signed_probe
                self.assertEqual(equal_mirror_probe, signed_equal_probe)
                self.assertEqual(signed_mirror_probe, signed_signed_probe)
        self.assertEqual(counts, FIXTURE["mirror_trajectory_counts"])

    def test_exact_total_and_signed_turn_probe(self):
        equal_states = trajectory(self.initial, self.turns, *EQUAL, STEPS)
        signed_states = trajectory(self.initial, self.turns, *SIGNED, STEPS)
        for step, state in enumerate(equal_states):
            self.assertEqual(state_sum(state), Q5(2 ** step))
            self.assertEqual(turn_channel_imbalance(state, self.seed_index, self.turns), ZERO)
        for step, state in enumerate(signed_states):
            self.assertEqual(state_sum(state), Q5(4 ** step))
        self.assertEqual(turn_channel_imbalance(signed_states[1], self.seed_index,
                                               self.turns), Q5(2, 2))
        self.assertLess(SIGNED[1], ZERO)  # signed linear coefficient, not a probability

    def test_wrong_weight_exchange_and_corrupted_transport_are_detected(self):
        reflection = next(s for s in self.symmetries if s.determinant == -1)
        self.assertEqual(list(reflection.vertex_image),
                         FIXTURE["negative_control"]["reflection_vertex_image"])
        correct_image = self.edge_image(reflection)
        corrupted = list(correct_image)
        first, second = FIXTURE["negative_control"]["swap_edge_image_targets"]
        corrupted[first], corrupted[second] = corrupted[second], corrupted[first]
        signed_states = trajectory(self.initial, self.turns, *SIGNED, STEPS)
        correct_seed = push(self.initial, correct_image)
        bad_seed = push(self.initial, tuple(corrupted))
        self.assertNotEqual(push(signed_states[0], correct_image), bad_seed)
        self.assertNotEqual(correct_seed, bad_seed)

        wrong_mirror = trajectory(correct_seed, self.turns, *SIGNED, STEPS)
        self.assertNotEqual(push(signed_states[1], correct_image), wrong_mirror[1])
        self.assertEqual(FIXTURE["negative_control"]["rejected_at_step"], 0)
        self.assertEqual(FIXTURE["negative_control"]["wrong_exchange_rejected_at_step"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
