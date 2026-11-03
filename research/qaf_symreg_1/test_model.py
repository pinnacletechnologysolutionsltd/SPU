"""Independent exact checks and deliberately broken negative controls."""
import unittest
from fractions import Fraction
from itertools import product

from research.qaf_symreg_1.model import Fact, Key, Machine, MAX_FACTS, MAX_VALUES


def exact_transform(value, k, flip):
    a, b = map(Fraction, value)
    return (k*a, (-k if flip else k)*b)


def oracle_norm(value):
    a, b = map(Fraction, value)
    return (a+b)*(a-b)-2*b*b


class Tests(unittest.TestCase):
    def test_e1_composition_without_numerical_reads(self):
        m = Machine()
        m.write(0, 1, 2); m.write(1, 1, -2); m.write(2, 2, -4)
        x, y, z = m.reg[:3]
        f = m.admit_value(x, y, 1, True); g = m.admit_value(y, z, 2)
        before = m.domain.reads
        h = m.compose(f, g); n = m.project_norm(h)
        self.assertEqual(h.key, Key("value", x, z, 2, True))
        self.assertEqual(n.key, Key("norm", x, z, 4))
        self.assertEqual((h.rule, h.parents, n.parents), ("compose", (f, g), (h,)))
        self.assertTrue(all(q.valid for q in (f, g, h, n)))
        self.assertEqual(m.query(0, 2, "value", 2, True)[0], "PROVEN")
        self.assertEqual(m.query(0, 2, "norm", 4)[0], "PROVEN")
        self.assertEqual(m.domain.reads, before)
        self.assertEqual(exact_transform((1, 2), 2, True), (2, -4))
        self.assertEqual(oracle_norm((2, -4)), 4*oracle_norm((1, 2)))

    def test_exhaustive_supported_compositions(self):
        count = 0
        for a, b, k, j, flip1, flip2 in product(range(-2, 3), range(-2, 3), (-1, 0, 1),
                                                 (-1, 0, 1), (False, True), (False, True)):
            m = Machine(); m.write(0, a, b)
            y = exact_transform((a, b), k, flip1); m.write(1, *map(int, y))
            z = exact_transform(y, j, flip2); m.write(2, *map(int, z))
            f = m.admit_value(m.reg[0], m.reg[1], k, flip1)
            g = m.admit_value(m.reg[1], m.reg[2], j, flip2)
            reads = m.domain.reads; h = m.compose(f, g)
            self.assertEqual(m.domain.reads, reads)
            self.assertEqual(z, exact_transform((a, b), h.key.k, h.key.flip))
            norm = m.project_norm(h)
            self.assertEqual(oracle_norm(z), norm.key.k*oracle_norm((a, b)))
            count += 1
        self.assertEqual(count, 900)

    def test_three_valued_queries_against_exact_reference(self):
        checks = 0
        for a, b, scale, flip in product(range(-1, 2), range(-1, 2), (-2, -1, 0, 1, 2), (False, True)):
            m = Machine(); m.write(0, a, b)
            target = exact_transform((a, b), scale, flip)
            m.write(1, *map(int, target))
            fact = m.admit_value(m.reg[0], m.reg[1], scale, flip)
            m.project_norm(fact)
            for k, conj in product((-2, -1, 0, 1, 2), (False, True)):
                actual = target == exact_transform((a, b), k, conj)
                result, _ = m.query(0, 1, "value", k, conj, concrete=True)
                self.assertIn(result, ("PROVEN", "DISPROVEN", "UNKNOWN"))
                self.assertFalse(result == "PROVEN" and not actual)
                self.assertFalse(result == "DISPROVEN" and actual)
                checks += 1
            for k in (-4, -2, -1, 0, 1, 2, 4):
                actual = oracle_norm(target) == k*oracle_norm((a, b))
                result, _ = m.query(0, 1, "norm", k, concrete=True)
                self.assertFalse(result == "PROVEN" and not actual)
                self.assertFalse(result == "DISPROVEN" and actual)
                checks += 1
        self.assertEqual(checks, 1530)

    def test_overwrite_and_bad_register_number_control(self):
        m = Machine(); m.write(0, 1, 2); m.write(1, 1, -2)
        old = m.reg[0]; f = m.admit_value(old, m.reg[1], 1, True)
        broken = {(0, 1): "conjugate"}  # deliberately keyed by mutable registers
        m.write(0, 4, 5)
        self.assertNotEqual(old, m.reg[0]); self.assertIn(f.key, m.facts)
        self.assertEqual(m.query(0, 1, "value", 1, True)[0], "UNKNOWN")
        self.assertEqual(m.query(0, 1, "value", 1, True, concrete=True)[0], "DISPROVEN")
        self.assertEqual(broken[(0, 1)], "conjugate")  # false current-register claim

    def test_unknown_disproven_and_norm_does_not_imply_value(self):
        m = Machine(); m.write(0, 1, 2); m.write(1, 1, -2)
        m.admit_norm(m.reg[0], m.reg[1])
        self.assertEqual(m.query(0, 1, "norm")[0], "PROVEN")
        self.assertEqual(m.query(0, 1, "value")[0], "UNKNOWN")
        self.assertEqual(m.query(0, 1, "value", concrete=True)[0], "DISPROVEN")
        self.assertEqual(m.query(0, 1, "value", 1, True)[0], "UNKNOWN")
        self.assertEqual(m.query(0, 1, "value", 1, True, concrete=True)[0], "UNKNOWN")

    def test_negative_norm_scale(self):
        m = Machine(); m.write(0, 1, 1); m.write(1, 2, 0)
        self.assertIsNotNone(m.admit_norm(m.reg[0], m.reg[1], -2))
        self.assertEqual(m.query(0, 1, "norm", -2)[0], "PROVEN")

    def test_double_conjugation_negative_and_zero_scale(self):
        m = Machine(); m.write(0, 2, 3); m.write(1, 2, -3); m.write(2, 2, 3)
        first = m.admit_value(m.reg[0], m.reg[1], 1, True)
        second = m.admit_value(m.reg[1], m.reg[2], 1, True)
        self.assertEqual(m.compose(first, second).key, Key("value", m.reg[0], m.reg[2], 1, False))
        self.assertEqual(m.query(0, 2, "value")[0], "PROVEN")
        m.write(3, -4, -6); m.write(4, 0, 0)
        self.assertIsNotNone(m.admit_value(m.reg[0], m.reg[3], -2))
        self.assertIsNotNone(m.admit_value(m.reg[3], m.reg[4], 0))
        self.assertEqual(m.query(0, 4, "value", 0)[0], "PROVEN")

    def test_branches_merge_and_refusal(self):
        m = Machine(width=8); m.write(0, 1, 2); m.write(1, 1, -2)
        f = m.admit_value(m.reg[0], m.reg[1], 1, True)
        group = m.branch(None); left, right = group.paths[False], group.paths[True]
        with self.assertRaises(TypeError): del group.paths[False]
        left.project_norm(f)  # path-specific until established in the other feasible path
        joined = group.join()
        self.assertEqual(joined.query(0, 1, "norm")[0], "UNKNOWN")
        right.project_norm(f)
        joined = group.join()
        outcome, path = joined.query(0, 1, "norm")
        self.assertEqual(outcome, "PROVEN")
        self.assertEqual(path[0].rule, "merge_all_feasible")
        before = (right.reg.copy(), right.facts.copy(), dict(right.domain.values))
        self.assertEqual(right.write(0, 128, 0), "OVERFLOW")
        self.assertEqual((right.reg, right.facts, right.domain.values), before)
        self.assertEqual(right.write(0, True, 1), "INVALID")
        right.write(0, 0, 0)
        self.assertIsNone(left.admit_value(right.reg[0], left.reg[1], 0))
        divergent = group.join()
        self.assertIsNone(divergent.reg[0])
        self.assertNotIn(right.reg[0], divergent.known)
        self.assertEqual(divergent.query(0, 1, "value", 1, True)[0], "UNKNOWN")
        definite = left.branch(True)
        self.assertEqual(set(definite.paths), {True})
        self.assertEqual(definite.join().query(0, 1, "norm")[0], "PROVEN")
        with self.assertRaises(ValueError): m.branch(1)

    def test_multiply_overflow_refusal_keeps_identity_facts_and_status(self):
        m = Machine(width=8)
        m.write(0, 120, 0); m.write(1, 2, 0); m.write(2, 120, 0)
        fact = m.admit_value(m.reg[0], m.reg[2])
        old = (m.reg.copy(), m.facts.copy(), dict(m.domain.values))
        self.assertEqual(m.multiply(0, 0, 1), "OVERFLOW")
        self.assertEqual((m.reg, m.facts, m.domain.values), old)
        self.assertEqual(m.status, "OVERFLOW")
        self.assertIs(m.facts[fact.key], fact)
        self.assertEqual(m.multiply(3, 1, 1), "OK")
        self.assertEqual(m.domain.values[m.reg[3]], (4, 0))
        self.assertEqual(m.status, "OK")

    def test_forgery_mixed_rules_and_unsupported_scale(self):
        m = Machine(); m.write(0, 1, 2); m.write(1, 2, 4); m.write(2, 4, 8)
        x, y, z = m.reg[:3]
        p = m.admit_value(x, y, 2); q = m.admit_value(y, z, 2)
        self.assertIsNone(m.compose(p, q))  # scale 4 outside vocabulary
        fabricated = Fact(p.key, "fake", ())
        self.assertIsNone(m.compose(fabricated, q))
        n = m.project_norm(p)
        self.assertIsNone(m.compose(p, n))
        self.assertIsNone(m.admit_value(x, y, True))
        self.assertIsNone(m.admit_value(x, y, 1))
        self.assertIsNone(m.admit_norm(x, y, 1))
        self.assertIsNone(m.admit_value(False, y, 1))
        with self.assertRaises(ValueError): m.query(-1, 0, "value")

    def test_capacity_refusal_has_no_silent_eviction(self):
        m = Machine()
        for i in range(MAX_VALUES): self.assertEqual(m.write(0, i, 0), "OK")
        old = m.reg.copy()
        with self.assertRaises(OverflowError): m.write(0, 0, 0)
        self.assertEqual(m.reg, old)
        m = Machine()
        ids = []
        for _ in range(17): m.write(0, 0, 0); ids.append(m.reg[0])
        for i in range(16):
            for j in range(16): m.admit_value(ids[i], ids[j])
        self.assertEqual(len(m.facts), MAX_FACTS)
        with self.assertRaises(OverflowError): m.admit_value(ids[16], ids[0])
        self.assertEqual(len(m.facts), MAX_FACTS)


if __name__ == "__main__":
    unittest.main()
