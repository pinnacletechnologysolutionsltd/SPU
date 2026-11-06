"""Small-domain and adversarial tests for the partial SYMREG-1 model."""
import unittest
from itertools import product

from research.spu_symreg_1.model import Bank, Relation


def oracle(a, b, k, flip):
    # Separate coefficient-level reference.
    return (a * k, b * (-k if flip else k))


class RelationTests(unittest.TestCase):
    def test_composition_and_norm_without_value_reads(self):
        m = Bank()
        a = m.write(0, 1, 2); b = m.write(1, 1, -2); c = m.write(2, 2, -4)
        f = m.check_value(a, b, 1, True)
        g = m.check_value(b, c, 2)
        self.assertIsNotNone(f); self.assertIsNotNone(g)
        before = m.value_reads
        composed = m.compose(f, g)
        self.assertEqual(composed, Relation(a, c, "value", 2, True))
        norm = m.norm_from_value(composed)
        self.assertEqual(norm, Relation(a, c, "norm", 4))
        self.assertEqual(before, m.value_reads)
        self.assertEqual(m.values[c], oracle(*m.values[a], 2, True))

    def test_overwrite_keeps_old_identity_distinct(self):
        m = Bank()
        old = m.write(0, 3, 1); same = m.write(1, 3, 1)
        fact = m.check_value(old, same, 1)
        new = m.write(0, 5, 1)
        self.assertNotEqual(old, new)
        self.assertFalse(m.current(0, old)); self.assertTrue(m.current(0, new))
        self.assertIn(fact, m.relations)  # historical identity remains unchanged
        self.assertIsNone(m.check_value(new, same, 1))

    def test_norm_equality_is_not_value_equality(self):
        m = Bank()
        x = m.write(0, 1, 2); y = m.write(1, 1, -2)
        self.assertIsNotNone(m.check_norm(x, y, 1))
        self.assertIsNone(m.check_value(x, y, 1))
        self.assertIsNotNone(m.check_value(x, y, 1, True))
        self.assertIsNone(m.check_norm(x, y, 4))

    def test_invalid_composition_and_limits(self):
        m = Bank()
        x = m.write(0, 1, 2); y = m.write(1, 2, 4); z = m.write(2, 4, 8)
        first = m.check_value(x, y, 2); second = m.check_value(y, z, 2)
        self.assertIsNone(m.compose(first, second))  # scale 4 is outside value vocabulary
        self.assertIsNone(m.compose(second, first))
        self.assertIsNone(m.compose(Relation(x, y, "value", 1), second))
        self.assertIsNone(m.check_value(x, y, True))
        self.assertIsNone(m.check_norm(x, y, -1))
        before = (list(m.registers), dict(m.values), set(m.relations))
        with self.assertRaises(ValueError): m.write(0, True, 0)
        self.assertEqual((m.registers, m.values, m.relations), before)

    def test_small_exhaustive_compositions(self):
        count = 0
        for a, b, k, j, f, g in product(range(-2, 3), range(-2, 3), (-1, 0, 1),
                                        (-1, 0, 1), (False, True), (False, True)):
            m = Bank()
            x = m.write(0, a, b)
            yv = oracle(a, b, k, f); y = m.write(1, *yv)
            zv = oracle(*yv, j, g); z = m.write(2, *zv)
            p = m.check_value(x, y, k, f); q = m.check_value(y, z, j, g)
            reads = m.value_reads
            result = m.compose(p, q)
            self.assertEqual(m.value_reads, reads)
            self.assertEqual(zv, oracle(a, b, result.scale, result.flip))
            nr = m.norm_from_value(result)
            self.assertEqual(zv[0]**2 - 3*zv[1]**2, nr.scale * (a*a - 3*b*b))
            count += 1
        self.assertEqual(count, 900)


if __name__ == "__main__":
    unittest.main()
