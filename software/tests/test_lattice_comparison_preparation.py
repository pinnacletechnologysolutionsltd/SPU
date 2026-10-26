"""Short readiness witnesses; deliberately does not run the 120-case comparison."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from software.research.lattice_comparison import d4
from software.research.lattice_comparison.limits import Meter, Profile, Refusal, atomic_d4
from software.research.lattice_comparison import rational
from software.research.lattice_symmetry.reference import reflect
from software.research.lattice_symmetry.fixtures import simple_roots
from fractions import Fraction


class Readiness(unittest.TestCase):
    def test_descriptor_domain_and_encoding(self):
        values = d4.group()
        self.assertEqual(len(set(values)), 192)
        self.assertEqual(len({d4.pack(v) for v in values}), 192)
        self.assertTrue(all(d4.unpack(d4.pack(v)) == v for v in values))
        for bad in (True, -1, 4096, 0, 256 + d4.pack(d4.IDENTITY)):
            with self.assertRaises(ValueError):
                d4.unpack(bad)

    def test_literal_order_and_inverse(self):
        x = (2, -2, 0, 0)
        self.assertEqual(d4.act(d4.descriptor([0, 1]), x), (-2, 0, 2, 0))
        self.assertEqual(d4.descriptor([0, 1, 1, 0]), d4.IDENTITY)
        self.assertNotEqual(d4.descriptor([0, 1]), d4.descriptor([1, 0]))

    def test_generators_against_independent_rational_formula(self):
        x = (2, 0, -2, 0)
        for i, root in enumerate(simple_roots('D4')):
            physical = tuple(Fraction(v, 2) for v in x)
            alpha = tuple(Fraction(v, 2) for v in root)
            expected = tuple(2 * v for v in reflect(physical, alpha))
            self.assertEqual(d4.act(d4.GENERATORS[i], x), expected)

    def test_refusal_is_atomic(self):
        original = [0, 0, -(1 << 63), 0]
        saved = original[:]
        with self.assertRaisesRegex(Refusal, 'SCALAR_RANGE'):
            atomic_d4([3], original)
        self.assertEqual(original, saved)
        self.assertEqual(atomic_d4([], (2, -2, 0, 0)), (2, -2, 0, 0))
        with self.assertRaisesRegex(Refusal, 'WORD_LIMIT'):
            atomic_d4([0] * 257, (0, 0, 0, 0))

    def test_raw_cancellation_and_euclid_accounting(self):
        m = Meter()
        self.assertEqual(rational.add(m, (127, 2), (-127, 2)), (0, 1))
        self.assertEqual(m.counts['multiply'], 3)
        self.assertEqual(m.counts['quotient'], 2)
        self.assertEqual(m.counts['remainder'], 3)
        self.assertGreaterEqual(m.peak_bits, 9)
        m = Meter()
        self.assertEqual(rational.gcd(m, 1071, 462), 21)
        self.assertEqual(m.counts['remainder'], 3)

    def test_resource_and_quotient_controls(self):
        for action, name in (
            (lambda: Meter(Profile(max_operations=1)).integer(0), 'WORK_LIMIT'),
            (lambda: Meter(Profile(temporary_bits=4)).integer(8), 'TEMPORARY_RANGE'),
            (lambda: rational.quotient(Meter(), 3, 2), 'INEXACT_QUOTIENT'),
            (lambda: rational.normalize(Meter(), 1, 0), 'ZERO_DENOMINATOR'),
            (lambda: Meter().integer(True), 'INTEGER_TYPE'),
            (lambda: Profile(scalar_bits=True), 'PROFILE_INVALID'),
        ):
            with self.assertRaisesRegex(Refusal, name):
                action()

    def test_simultaneous_storage_and_refusal(self):
        m = Meter(Profile(max_live_bits=100))
        m.acquire('old', 40)
        m.acquire('new', 50)
        self.assertEqual(m.peak_live_bits, 90)
        with self.assertRaisesRegex(Refusal, 'STORAGE_LIMIT'):
            m.acquire('workspace', 20)
        self.assertEqual(m.live, {'old': 40, 'new': 50})
        m.release('old')
        self.assertEqual(m.peak_live_bits, 90)


if __name__ == '__main__':
    unittest.main()
