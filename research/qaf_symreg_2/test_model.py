"""Exact checks against independent coefficient and norm calculations."""
import unittest
from fractions import Fraction
from itertools import product

from research.qaf_symreg_1.model import Fact, Key, Machine
from research.qaf_symreg_2.model import Canonical, Proof, Sparse, admit_checked, validate


def transform(value, k, flip):
    a, b = map(Fraction, value)
    return k*a, (-k if flip else k)*b


def norm(value):
    a, b = map(Fraction, value)
    return (a+b)*(a-b)-2*b*b


def chain():
    m = Machine()
    for i, value in enumerate(((1, 2), (1, -2), (2, -4), (2, 4))):
        m.write(i, *value)
    a, b, c, d = m.reg[:4]
    edges = (m.admit_value(a, b, 1, True), m.admit_value(b, c, 2),
             m.admit_value(c, d, 1, True))
    return m, (a, b, c, d), edges


class Tests(unittest.TestCase):
    def test_three_representations_and_no_new_value_reads(self):
        m, (a, b, c, d), edges = chain()
        sparse = Sparse(m); canonical = Canonical(m, a)
        for edge in edges: self.assertEqual(canonical.attach(edge), "STORED")
        before = m.domain.reads
        for rep in (sparse, canonical):
            outcome, proof = rep.prove(a, d, 2)
            self.assertEqual(outcome, "PROVEN")
            self.assertTrue(validate(m, proof, a, d, 2))
            self.assertEqual(len(proof.path), 3)
            outcome, proof = rep.prove(a, d, 4, norm=True)
            self.assertEqual(outcome, "PROVEN")
            self.assertTrue(validate(m, proof, a, d, 4, norm=True))
        self.assertEqual(m.domain.reads, before)
        self.assertEqual(len(m.facts), 3)  # no persistent derived closure
        ab = m.compose(edges[0], edges[1]); ad = m.compose(ab, edges[2]); m.project_norm(ad)
        self.assertEqual(m.query(0, 3, "value", 2)[0], "PROVEN")
        self.assertEqual(m.query(0, 3, "norm", 4)[0], "PROVEN")
        self.assertEqual(transform((1, 2), 2, False), (2, 4))
        self.assertEqual(norm((2, 4)), 4*norm((1, 2)))

    def test_small_domain_chains_and_canonical_zero(self):
        count = 0
        for a, b, k, j, f, g in product(range(-2, 3), range(-2, 3), (-2, -1, 0, 1, 2),
                                       (-2, -1, 0, 1, 2), (False, True), (False, True)):
            m = Machine(); m.write(0, a, b)
            y = transform((a, b), k, f); m.write(1, *map(int, y))
            z = transform(y, j, g); m.write(2, *map(int, z))
            x, yid, zid = m.reg[:3]
            p = m.admit_value(x, yid, k, f); q = m.admit_value(yid, zid, j, g)
            s = Sparse(m); c = Canonical(m, x)
            self.assertEqual(c.attach(p), "STORED")
            expected_scale = k*j
            if expected_scale not in (-2, -1, 0, 1, 2):
                self.assertEqual(c.attach(q), "UNKNOWN")
                self.assertEqual(s.prove(x, zid, 1)[0], "UNKNOWN")
            else:
                self.assertEqual(c.attach(q), "STORED")
                flip = (f != g) if expected_scale else False
                for rep in (s, c):
                    outcome, proof = rep.prove(x, zid, expected_scale, flip)
                    self.assertEqual(outcome, "PROVEN")
                    self.assertTrue(validate(m, proof, x, zid, expected_scale, flip))
                    self.assertEqual(z, transform((a, b), expected_scale, flip))
                reference = m.compose(p, q)
                self.assertIsNotNone(reference)
                self.assertEqual(m.query(0, 2, "value", expected_scale, flip)[0], "PROVEN")
            count += 1
        self.assertEqual(count, 2500)

    def test_cycles_contradiction_and_missing_norm_edges(self):
        m = Machine(); m.write(0, 1, 2); m.write(1, 1, -2)
        x, y = m.reg[:2]
        xy = m.admit_value(x, y, 1, True); yx = m.admit_value(y, x, 1, True)
        s = Sparse(m)
        self.assertEqual(s.prove(x, x)[0], "PROVEN")
        self.assertIsNone(m.admit_value(x, y, 1))  # concrete contradiction
        self.assertEqual(admit_checked(m, x, y, 1)[0], "DISPROVEN")
        self.assertEqual(admit_checked(m, x, y, 9)[0], "UNKNOWN")
        self.assertEqual(admit_checked(m, x, y, 1, True)[0], "PROVEN")
        self.assertEqual(s.prove(x, y, 1)[0], "UNKNOWN")  # not inferred merely from same norm
        self.assertTrue(validate(m, s.prove(y, x, 1, True)[1], y, x, 1, True))
        c = Canonical(m, x); self.assertEqual(c.attach(xy), "STORED")
        self.assertEqual(c.attach(yx), "UNKNOWN")  # rooted tree does not store cycles
        self.assertIsNotNone(m.admit_norm(x, y))
        self.assertEqual(m.query(0, 1, "norm")[0], "PROVEN")

    def test_norm_only_and_mixed_paths(self):
        m = Machine(); m.write(0, 1, 1); m.write(1, 2, 0); m.write(2, -2, 0)
        x, y, z = m.reg[:3]
        n = m.admit_norm(x, y, -2); v = m.admit_value(y, z, -1)
        self.assertIsNotNone(n); self.assertIsNotNone(v)
        for rep in (Sparse(m), Canonical(m, x)):
            result, proof = rep.prove(x, z, -2, norm=True)
            self.assertEqual(result, "PROVEN")
            self.assertTrue(validate(m, proof, x, z, -2, norm=True))
            self.assertEqual(norm((2, 0)), -2*norm((1, 1)))

    def test_candidate_queries_never_prove_false_in_small_domain(self):
        checked = 0
        for a, b, scale, flip in product(range(-1, 2), range(-1, 2), (-2, -1, 0, 1, 2), (False, True)):
            m = Machine(); m.write(0, a, b)
            target = transform((a, b), scale, flip); m.write(1, *map(int, target))
            x, y = m.reg[:2]; fact = m.admit_value(x, y, scale, flip)
            graph, canonical = Sparse(m), Canonical(m, x); canonical.attach(fact)
            for k, f in product((-2, -1, 0, 1, 2), (False, True)):
                actual = target == transform((a, b), k, f)
                for rep in (graph, canonical):
                    result, _ = rep.prove(x, y, k, f)
                    self.assertFalse(result == "PROVEN" and not actual)
                    checked += 1
            for k in (-4, -2, -1, 0, 1, 2, 4):
                actual = norm(target) == k*norm((a, b))
                for rep in (graph, canonical):
                    result, _ = rep.prove(x, y, k, norm=True)
                    self.assertFalse(result == "PROVEN" and not actual)
                    checked += 1
        self.assertEqual(checked, 3060)

    def test_history_and_fabricated_provenance(self):
        m, (a, b, _, _), edges = chain(); s = Sparse(m); c = Canonical(m, a)
        c.attach(edges[0]); result, oldproof = s.prove(a, b, 1, True)
        self.assertEqual(result, "PROVEN")
        m.write(0, 7, 8)
        self.assertTrue(validate(m, oldproof, a, b, 1, True))
        self.assertEqual(s.current(0, 1, 1, True)[0], "UNKNOWN")
        self.assertFalse(validate(m, oldproof, m.reg[0], b, 1, True))
        fake = Fact(edges[0].key, "fabricated")
        forged = Proof(a, b, 1, True, (fake,))
        self.assertFalse(validate(m, forged, a, b, 1, True))
        self.assertEqual(c.attach(fake), "UNKNOWN")
        self.assertEqual(c.attach(None), "UNKNOWN")
        self.assertFalse(validate(m, oldproof, False, b, 1, True))
        # A forged record planted through private internals still fails proof-rule checks.
        bogus = Fact(edges[0].key, "compose", ())
        m.facts[bogus.key] = bogus
        self.assertFalse(validate(m, Proof(a, b, 1, True, (bogus,)), a, b, 1, True))
        malformed = Fact(edges[0].key, "compose", (42, 43))
        m.facts[malformed.key] = malformed
        self.assertFalse(validate(m, Proof(a, b, 1, True, (malformed,)), a, b, 1, True))
        broken = {(0, 1): "conjugate"}  # defective register-address cache
        self.assertEqual(broken[(0, 1)], "conjugate")
        self.assertNotEqual(m.domain.values[m.reg[1]], transform(m.domain.values[m.reg[0]], 1, True))

    def test_branches_join_and_stale_proof(self):
        m, (a, b, c, _), edges = chain(); group = m.branch(None)
        left, right = group.paths[False], group.paths[True]
        left.compose(edges[0], edges[1])
        joined = group.join()
        self.assertNotIn(Key("value", a, c, 2, True), joined.facts)
        outcome, proof = Sparse(joined).prove(a, c, 2, True)
        self.assertEqual(outcome, "PROVEN")  # both foundational edges are common
        self.assertTrue(validate(joined, proof, a, c, 2, True))
        self.assertFalse(validate(joined, Proof(a, b, 1, True, (edges[0],)), a, b, 1, True))
        canon = Canonical(joined, a)
        self.assertEqual(canon.attach(joined.facts[edges[0].key]), "STORED")
        self.assertEqual(canon.attach(joined.facts[edges[1].key]), "STORED")
        self.assertEqual(canon.prove(a, c, 2, True)[0], "PROVEN")
        right.write(0, 4, 5); joined2 = group.join()
        self.assertIsNone(joined2.reg[0])
        self.assertEqual(Sparse(joined2).current(0, 1, 1, True)[0], "UNKNOWN")

    def test_different_paths_lose_common_derivable_conclusion(self):
        m = Machine()
        for i in range(4): m.write(i, 1, 2)
        x, y, z, w = m.reg[:4]
        group = m.branch(None); left, right = group.paths[False], group.paths[True]
        left.admit_value(x, y); left.admit_value(y, z)
        right.admit_value(x, w); right.admit_value(w, z)
        self.assertEqual(Sparse(left).prove(x, z)[0], "PROVEN")
        self.assertEqual(Sparse(right).prove(x, z)[0], "PROVEN")
        joined = group.join()
        self.assertEqual(Sparse(joined).prove(x, z)[0], "UNKNOWN")
        self.assertEqual(joined.query(0, 2, "value", concrete=True)[0], "UNKNOWN")

    def test_resource_limits_and_incompleteness(self):
        m, (a, b, c, _), edges = chain()
        self.assertEqual(Sparse(m, max_work=0).prove(a, c, 2, True)[0], "RESOURCE_LIMIT")
        self.assertEqual(Sparse(m, max_depth=1).prove(a, c, 2, True)[0], "UNKNOWN")
        rooted = Canonical(m, a, max_depth=1)
        self.assertEqual(rooted.attach(edges[0]), "STORED")
        self.assertEqual(rooted.attach(edges[1]), "RESOURCE_LIMIT")
        self.assertEqual(rooted.prove(b, a, 1, True)[0], "UNKNOWN")
        self.assertEqual(len(m.facts), 3)
        with self.assertRaises(ValueError): Sparse(m, max_work=4097)

    def test_out_of_vocabulary_intermediate_loses_true_zero_conclusion(self):
        m = Machine()
        for i, value in enumerate((1, 2, 4, 0)): m.write(i, value, 0)
        x, y, z, w = m.reg[:4]
        a = m.admit_value(x, y, 2); b = m.admit_value(y, z, 2); c = m.admit_value(z, w, 0)
        self.assertEqual(m.domain.values[w], transform(m.domain.values[x], 0, False))
        self.assertEqual(Sparse(m).prove(x, w, 0)[0], "UNKNOWN")
        rooted = Canonical(m, x)
        self.assertEqual(rooted.attach(a), "STORED")
        self.assertEqual(rooted.attach(b), "UNKNOWN")
        self.assertEqual(rooted.attach(c), "UNKNOWN")
        self.assertEqual(rooted.prove(x, w, 0)[0], "UNKNOWN")

    def test_provenance_depth_limit_is_fail_closed(self):
        m = Machine(); m.write(0, 1, 2); source = m.reg[0]
        previous, accumulated = source, None
        for _ in range(34):
            m.write(0, 1, 2); target = m.reg[0]
            edge = m.admit_value(previous, target)
            accumulated = edge if accumulated is None else m.compose(accumulated, edge)
            previous = target
        too_deep = Proof(source, target, 1, False, (accumulated,))
        self.assertFalse(validate(m, too_deep, source, target, 1))
        result, proof = Sparse(m).prove(source, target)
        self.assertEqual(result, "UNKNOWN"); self.assertIsNone(proof)


if __name__ == "__main__":
    unittest.main()
