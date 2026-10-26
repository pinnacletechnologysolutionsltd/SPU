#!/usr/bin/env python3
"""GC-5B exact seed controls and mirror covariance on the frozen GC-5 operator."""

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

FIXTURE_PATH = ROOT / "fixtures/golden_core_gc5b_seed_controls.json"
DEMO_PATH = ROOT / "examples/golden_core/gc5b_seed_dynamics.html"
FIXTURE_BYTES = FIXTURE_PATH.read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)
FIXTURE_SHA256 = "256ab9a1a4a4f401c1689e2538cde1858c066a292d4d74e7b9577963edb28e5e"
STEPS = 12
PROFILES = {
    "equal": (ONE, ONE),
    "signed": (Q5(3, 1), Q5(1, -1)),
}


def pair(value):
    return [[value.a.numerator, value.a.denominator],
            [value.b.numerator, value.b.denominator]]


def push(state, image):
    result = [ZERO] * len(state)
    for source, target in enumerate(image):
        result[target] = state[source]
    return tuple(result)


def first_recurrence(states):
    for current in range(1, len(states)):
        for earlier in range(current):
            if states[current] == states[earlier]:
                return [earlier, current]
    return None


def make_seeds(turns):
    edge_index = {edge: i for i, edge in enumerate(turns.directed_edges)}
    impulse = [ZERO] * len(edge_index)
    impulse[edge_index[(0, 1)]] = ONE
    uniform = [ONE] * len(edge_index)
    face = [ZERO] * len(edge_index)
    for edge in ((0, 1), (1, 2), (2, 0)):
        face[edge_index[edge]] = ONE
    dense = [Q5(i % 3 - 1, (7 * i) % 5 - 2)
             for i in range(len(turns.directed_edges))]
    return {
        "impulse_01": tuple(impulse),
        "uniform": tuple(uniform),
        "face_cycle_012": tuple(face),
        "dense_signed": tuple(dense),
    }


def edge_image(turns, symmetry):
    edge_index = {edge: i for i, edge in enumerate(turns.directed_edges)}
    return tuple(edge_index[(symmetry.vertex_image[u], symmetry.vertex_image[v])]
                 for u, v in turns.directed_edges)


def record(states, turns, image):
    return {
        "measurements": [{
            "step": step,
            "state_sha256": state_sha256(state),
            "max_coefficient_bit_length": coefficient_max_bit_length(state),
            "total_coefficient_sum": pair(state_sum(state)),
            "left_minus_right_probe": pair(turn_channel_imbalance(
                state, turns.directed_edges.index((0, 1)), turns)),
            "parity_defect_count": sum(a != b for a, b in zip(state, push(state, image))),
        } for step, state in enumerate(states)],
        "first_recurrence": first_recurrence(states),
    }


class GoldenCoreGc5bTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.turns = OrientedEdgeTurns.build()
        cls.symmetries = icosahedral_symmetries()
        cls.reflection = next(s for s in cls.symmetries if s.determinant == -1)
        cls.image = edge_image(cls.turns, cls.reflection)
        cls.seeds = make_seeds(cls.turns)

    def test_frozen_fixture_and_exact_measurements(self):
        self.assertEqual(hashlib.sha256(FIXTURE_BYTES).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(FIXTURE["steps"], STEPS)
        self.assertEqual(FIXTURE["reflection_vertex_image"],
                         list(self.reflection.vertex_image))
        self.assertEqual(FIXTURE["reflection_edge_image"], list(self.image))
        self.assertEqual(FIXTURE["directed_edge_basis"],
                         [list(edge) for edge in self.turns.directed_edges])
        basis_json = json.dumps(self.turns.directed_edges, separators=(",", ":"))
        self.assertEqual(FIXTURE["directed_edge_basis_sha256"],
                         hashlib.sha256(basis_json.encode()).hexdigest())
        self.assertEqual(FIXTURE["profiles"], {
            "equal": {"left": "1", "right": "1"},
            "signed": {"left": "3+sqrt(5)", "right": "1-sqrt(5)"},
        })
        self.assertEqual(set(FIXTURE["seeds"]), set(self.seeds))
        for seed_name, initial in self.seeds.items():
            self.assertEqual(FIXTURE["seeds"][seed_name]["state_sha256"],
                             state_sha256(initial))
            for profile_name, (left, right) in PROFILES.items():
                states = trajectory(initial, self.turns, left, right, STEPS)
                self.assertEqual(record(states, self.turns, self.image),
                                 FIXTURE["runs"][seed_name][profile_name])

    def test_mirror_covariance_for_every_seed_and_profile(self):
        for initial in self.seeds.values():
            for profile_name, (left, right) in PROFILES.items():
                base = trajectory(initial, self.turns, left, right, STEPS)
                mirrored_seed = push(initial, self.image)
                if profile_name == "signed":
                    mirror_weights = (right, left)
                else:
                    mirror_weights = (left, right)
                mirrored = trajectory(mirrored_seed, self.turns, *mirror_weights, STEPS)
                self.assertEqual(tuple(push(state, self.image) for state in base), mirrored)

    def test_uniform_seed_is_parity_neutral_control(self):
        for left, right in PROFILES.values():
            states = trajectory(self.seeds["uniform"], self.turns, left, right, STEPS)
            self.assertTrue(all(state == push(state, self.image) for state in states))
            expected_sum = Q5(60)
            for step, state in enumerate(states):
                self.assertEqual(state_sum(state), expected_sum)
                self.assertEqual(turn_channel_imbalance(
                    state, self.turns.directed_edges.index((0, 1)), self.turns), ZERO)
                expected_sum *= left + right

    def test_demo_embeds_fixture_and_explains_observables(self):
        page = DEMO_PATH.read_text()
        marker = "const DATA = "
        self.assertIn(marker, page)
        embedded, _ = page.split(marker, 1)[1].split(";", 1)
        self.assertEqual(json.loads(embedded), FIXTURE)
        for text in ("Parity defect", "Left-minus-right probe", "Coefficient sum",
                     "Maximum coefficient bits", "State hash", "linearity",
                     "No physical chirality"):
            self.assertIn(text.lower(), page.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
