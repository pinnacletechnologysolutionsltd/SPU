"""Independent Fraction oracle and falsifiable lifecycle tests."""
import unittest
from fractions import Fraction

from research.qaf_symreg_0.model import Model
from software.experiments.surd_register_exact import R


def oracle(r):
    a, b = Fraction(r.a, r.d), Fraction(r.b, r.d)
    return (a + b) * (a - b) - 2 * b * b


class Tests(unittest.TestCase):
    def test_small_domain_against_independent_oracle(self):
        m = Model(width=8)
        for a in range(-3, 4):
            for b in range(-3, 4):
                for d in range(1, 5):
                    value = R(a, b, d)
                    self.assertEqual(m.load(0, value), "OK")
                    self.assertEqual(m.norm(0), oracle(value))

    def test_equality_norm_reuse_and_versions(self):
        m = Model()
        self.assertEqual(m.load(0, R(1, 2, 3)), "OK")
        self.assertEqual(m.load(1, R(2, 4, 6)), "OK")
        self.assertTrue(m.prove_equal(0, 1))
        self.assertEqual(m.norm(0), oracle(m.reg[0]))
        self.assertEqual(m.norm(1), oracle(m.reg[1]))
        self.assertEqual(m.stats["norm_evaluations"], 1)
        self.assertEqual(m.load(0, R(3, 1, 2)), "OK")
        self.assertFalse(m.equal)
        self.assertEqual(m.norm(0), oracle(m.reg[0]))
        self.assertEqual(m.norm(1), oracle(m.reg[1]))

    def test_invalid_claim_and_bounds(self):
        m = Model()
        m.load(0, R(2, 1, 3)); m.load(1, R(3, 1, 3))
        self.assertFalse(m.prove_equal(0, 1))
        self.assertFalse(m.prove_norm_equal(0, 1))
        self.assertFalse(m.prove_bounds(0, 1, 1, 3))
        self.assertTrue(m.prove_bounds(0, 2, 1, 3))
        self.assertEqual(m.norm(0), oracle(m.reg[0]))
        self.assertEqual(m.norm(1), oracle(m.reg[1]))
        self.assertEqual(m.stats["norm_evaluations"], 2)

    def test_norm_relationship_without_value_equality(self):
        m = Model()
        m.load(0, R(1, 2, 3)); m.load(1, R(1, -2, 3))
        self.assertFalse(m.prove_equal(0, 1))
        self.assertTrue(m.prove_norm_equal(0, 1))
        self.assertEqual(m.norm(0), oracle(m.reg[0]))
        self.assertEqual(m.norm(1), oracle(m.reg[1]))
        self.assertEqual(m.stats["norm_reuses"], 1)
        m.load(0, R(3, 0, 1))
        self.assertFalse(m.norm_equal)
        self.assertEqual(m.norm(0), oracle(m.reg[0]))

    def test_refusal_preserves_destination_and_relations(self):
        m = Model(width=8)
        m.load(0, R(120, 0, 1)); m.load(1, R(120, 0, 1)); m.load(2, R(2, 0, 1))
        self.assertTrue(m.prove_equal(0, 1))
        self.assertEqual(m.norm(1), oracle(m.reg[1]))
        before = (m.reg[0], m.version[0], set(m.equal), set(m.norm_equal), dict(m.cache), m.bounds[0])
        self.assertEqual(m.multiply(0, 0, 2), "OVERFLOW")
        self.assertEqual((m.reg[0], m.version[0], m.equal, m.norm_equal, m.cache, m.bounds[0]), before)
        self.assertEqual(m.load(0, R(0, 0, 0)), "INVALID")
        self.assertEqual(m.norm(0), oracle(m.reg[0]))
        self.assertEqual(m.stats["norm_reuses"], 1)

    def test_raw_fit_and_rescue(self):
        m = Model(width=8)
        m.load(0, R(2, 0, 4)); m.load(1, R(2, 0, 4))
        self.assertEqual(m.multiply(2, 0, 1), "OK")
        self.assertEqual(m.reg[2], R(4, 0, 16))  # raw fit is not normalized
        m.load(0, R(100, 0, 100)); m.load(1, R(100, 0, 100))
        self.assertEqual(m.multiply(2, 0, 1), "OK")
        self.assertEqual(m.reg[2], R(1, 0, 1))  # normalized only after overflow
        self.assertEqual(m.norm(2), oracle(m.reg[2]))


if __name__ == "__main__":
    unittest.main()
