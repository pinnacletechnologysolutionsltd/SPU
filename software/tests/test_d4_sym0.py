"""Focused exact checks for D4-SYM-0 canonical associative memory."""

from itertools import product
import unittest

from software.research.lattice_comparison import d4
from software.research.d4_symmetry.canonical import GROUP, canonicalize, inverse, orbit
from software.research.d4_symmetry.memory import OrbitMemory


class D4Sym0Tests(unittest.TestCase):
    def test_group_laws(self):
        self.assertEqual(len(GROUP), 192)
        self.assertEqual(len(set(GROUP)), 192)
        for left in GROUP:
            self.assertIn(inverse(left), GROUP)
            self.assertEqual(d4.compose(left, inverse(left)), d4.IDENTITY)
            self.assertEqual(d4.compose(inverse(left), left), d4.IDENTITY)
            for right in GROUP:
                self.assertIn(d4.compose(left, right), GROUP)
        for vector in ((0, 0, 0, 0), (1, 2, 4, 7), (-4, 3, 2, 1)):
            for left in GROUP:
                for right in GROUP:
                    self.assertEqual(
                        d4.act(d4.compose(left, right), vector),
                        d4.act(left, d4.act(right, vector)),
                    )

    def test_full_bounded_state_orbits_and_witnesses(self):
        states = tuple(x for x in product(range(-4, 5), repeat=4) if sum(x) % 2 == 0)
        self.assertEqual(len(states), 3281)
        keys = {}
        for state in states:
            key, witness = canonicalize(state)
            keys[state] = key
            self.assertEqual(d4.act(inverse(witness), key), state)
        self.assertEqual(set(keys), set(states))
        for state in states:
            key = keys[state]
            for transform in GROUP:
                transformed = d4.act(transform, state)
                self.assertEqual(keys[transformed], key)

    def test_orbit_memory_unseen_transforms_and_action(self):
        source = (1, 2, 4, 7)
        variants = orbit(source)
        self.assertEqual(len(variants), 192)
        memory = OrbitMemory()
        memory.store(source, "known", action=(1, 0, 0, 0))
        self.assertEqual(len(memory), 1)
        for value in variants:
            expected = next(g for g in GROUP if d4.act(g, source) == value)
            self.assertEqual(memory.lookup(value), ("known", d4.act(expected, (1, 0, 0, 0))))

    def test_reject_invalid_symmetry_and_stabilizer_action(self):
        memory = OrbitMemory()
        source = (1, 2, 4, 7)
        related = d4.act(((1, 0, 2, 3), (0, 0, 0, 0)), source)
        memory.store(source, source[0])
        with self.assertRaisesRegex(ValueError, "D4_CONFLICTING_ASSOCIATION"):
            memory.store(related, related[0])
        with self.assertRaisesRegex(ValueError, "D4_ACTION_NOT_STABILIZER_FIXED"):
            memory.store((0, 0, 0, 0), "origin", action=(1, 0, 0, 0))

    def test_input_validation_and_deterministic_witness(self):
        self.assertEqual(canonicalize([1, 2, 4, 7]), canonicalize((1, 2, 4, 7)))
        with self.assertRaisesRegex(ValueError, "D4_VECTOR"):
            canonicalize((1, 2, 3))
        with self.assertRaisesRegex(ValueError, "D4_VECTOR"):
            canonicalize((1, 2, 3, 4.0))


if __name__ == "__main__":
    unittest.main()
