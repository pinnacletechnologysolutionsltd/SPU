"""Systematic exact checks and deliberate join/provenance counterexamples."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from types import SimpleNamespace
import unittest

from research.qaf_symreg_1.model import Fact, Key, Machine, MAX_FACTS, MAX_VALUES
from research.qaf_symreg_2.model import Sparse, validate
from research.qaf_symreg_3.model import BranchRoster, Join, MAX_BUNDLE_NODES, MAX_QUERIES, bundle_nodes


def norm(v):
    a, b = map(Fraction, v)
    return (a+b)*(a-b)-2*b*b


def fixture(a=1, b=2, three=False):
    base = Machine(width=8)
    for i, v in enumerate(((a, b), (a, -b), (2*a, -2*b), (2*a, 2*b))):
        assert base.write(i, *v) == "OK"
    x, y, z, w = base.reg[:4]
    paths = base.branch(None)
    left, right = paths.paths[False], paths.paths[True]
    left.admit_value(x, y, 1, True); left.admit_value(y, z, 2)
    right.admit_value(x, w, 2); right.admit_value(w, z, 1, True)
    entries = [("A", left), ("B", right)]
    if three:
        third = base.fork(); third.admit_value(x, z, 2, True)
        entries.append(("C", third))
    return base, entries, Key("value", x, z, 2, True)


class JoinTests(unittest.TestCase):
    def test_distinct_proofs_and_exact_oracle(self):
        base, branches, key = fixture(); roster = BranchRoster(branches); join = Join(roster, [key])
        self.assertEqual(join.syntactic(key), "UNKNOWN")
        reads = base.domain.reads
        result, proof = join.prove(key, current=(0, 2))
        self.assertEqual(result, "PROVEN"); self.assertTrue(join.validate(proof))
        self.assertEqual(proof.rule, "ALL_FEASIBLE_PATHS")
        self.assertEqual(proof.branch_ids, ("A", "B"))
        self.assertEqual(proof.roster_revision, roster.revision)
        self.assertIs(proof.branch_snapshots, join.snapshots)
        self.assertEqual(proof.query_set, frozenset((key,)))
        self.assertNotEqual(proof.witnesses[0][1].path, proof.witnesses[1][1].path)
        self.assertEqual(base.domain.reads, reads)
        self.assertEqual(tuple(map(Fraction, base.domain.values[key.target])), (2, -4))
        self.assertEqual(norm((2, -4)), 4*norm((1, 2)))

    def test_systematic_small_values(self):
        total = checked = 0
        for a, b in product(range(-3, 4), repeat=2):
            base, paths, key = fixture(a, b)
            join = Join(BranchRoster(paths), [key]); result, proof = join.prove(key)
            self.assertEqual(result, "PROVEN"); self.assertTrue(join.validate(proof))
            x = tuple(map(Fraction, base.domain.values[key.source]))
            z = tuple(map(Fraction, base.domain.values[key.target]))
            self.assertEqual(z, (2*x[0], -2*x[1]))
            self.assertEqual(norm(z), 4*norm(x)); total += 1
            candidates = [Key("value", key.source, key.target, k, flip if k else False)
                          for k in (-2, -1, 0, 1, 2) for flip in (False, True) if k or not flip]
            candidates += [Key("norm", key.source, key.target, k) for k in (-4, -2, -1, 0, 1, 2, 4)]
            check_join = Join(BranchRoster(paths), candidates)
            for q in candidates:
                result, witness = check_join.prove(q)
                actual = (z == (q.k*x[0], (-q.k if q.flip else q.k)*x[1])) if q.kind == "value" else (norm(z) == q.k*norm(x))
                if result == "PROVEN":
                    self.assertTrue(actual); self.assertTrue(check_join.validate(witness))
                else:
                    self.assertIn(result, ("UNKNOWN", "RESOURCE_LIMIT"))
                checked += 1
        self.assertEqual(total, 49)
        self.assertEqual(checked, 49*16)

    def test_one_path_unknown_and_existential_mutant(self):
        _, paths, key = fixture(); b = paths[1][1]; b.facts.clear()
        join = Join(BranchRoster(paths), [key])
        self.assertEqual(join.prove(key)[0], "UNKNOWN")
        # Deliberate bug: any-path acceptance incorrectly promotes the proposition.
        mutant = any(Sparse(m).prove(key.source, key.target, key.k, key.flip)[0] == "PROVEN" for _, m in paths)
        self.assertTrue(mutant)
        self.assertEqual(Sparse(b).prove(key.source, key.target, key.k, key.flip)[0], "UNKNOWN")

    def test_historical_vs_current_and_refusal(self):
        _, paths, key = fixture(); changed = paths[1][1]
        self.assertEqual(changed.write(0, 7, 6), "OK")
        join = Join(BranchRoster(paths), [key])
        historical, proof = join.prove(key)
        self.assertEqual(historical, "PROVEN"); self.assertTrue(join.validate(proof))
        self.assertEqual(join.prove(key, current=(0, 2))[0], "UNKNOWN")
        old = changed.reg.copy(); facts = changed.facts.copy()
        self.assertEqual(changed.multiply(0, 4, 5), "INVALID")
        self.assertEqual((changed.reg, changed.facts), (old, facts)); self.assertEqual(changed.status, "INVALID")
        self.assertFalse(join.validate(proof))  # status changes invalidate the frozen context

    def test_w8_overflow_preserves_state(self):
        m = Machine(width=8); m.write(0, 120, 0); m.write(1, 2, 0); m.write(2, 120, 0)
        m.admit_value(m.reg[0], m.reg[2]); old = (m.reg.copy(), m.facts.copy(), dict(m.domain.values))
        self.assertEqual(m.multiply(0, 0, 1), "OVERFLOW")
        self.assertEqual((m.reg, m.facts, m.domain.values), old); self.assertEqual(m.status, "OVERFLOW")

    def test_join_after_refusal_preserves_common_historical_facts(self):
        _, paths, key = fixture(); left = paths[0][1]
        left.write(4, 120, 0); left.write(5, 2, 0)
        before = (left.reg.copy(), left.facts.copy())
        self.assertEqual(left.multiply(4, 4, 5), "OVERFLOW")
        self.assertEqual((left.reg, left.facts), before)
        join = Join(BranchRoster(paths), [key])
        result, proof = join.prove(key, current=(0, 2))
        self.assertEqual(result, "PROVEN"); self.assertTrue(join.validate(proof))

    def test_three_branches_and_witness_tampering(self):
        _, paths, key = fixture(three=True); roster = BranchRoster(paths); join = Join(roster, [key])
        result, p = join.prove(key); self.assertEqual(result, "PROVEN"); self.assertTrue(join.validate(p))
        self.assertEqual(tuple(len(w.path) for _, w in p.witnesses), (2, 2, 1))
        self.assertFalse(join.validate(replace(p, witnesses=p.witnesses[:-1])))
        self.assertFalse(join.validate(replace(p, branch_ids=("A", "B"))))
        a_witness = p.witnesses[0][1]
        self.assertFalse(validate(paths[1][1], a_witness, key.source, key.target, key.k, key.flip))
        swapped = (("A", a_witness), ("B", a_witness), p.witnesses[2])
        self.assertFalse(join.validate(replace(p, witnesses=swapped)))
        _, missing = join.prove(key)
        object.__setattr__(missing, "witnesses", missing.witnesses[:-1])
        self.assertFalse(join.validate(missing))  # exercise coverage check on issued object
        _, counterfeit = join.prove(key)
        object.__setattr__(counterfeit, "witnesses", swapped)
        self.assertFalse(join.validate(counterfeit))  # exercise per-branch replay
        _, malformed = join.prove(key)
        object.__setattr__(malformed, "witnesses", (("A", None),) + malformed.witnesses[1:])
        self.assertFalse(join.validate(malformed))
        roster.remove("C"); self.assertFalse(join.validate(p)); self.assertEqual(join.prove(key)[0], "UNKNOWN")

    def test_duplicate_and_binding_change(self):
        _, paths, key = fixture(); join = Join(BranchRoster(paths), [key])
        _, p = join.prove(key, current=(0, 2)); self.assertTrue(join.validate(p))
        _, p2 = join.prove(key, current=(0, 2)); self.assertTrue(join.validate(p2))
        paths[0][1].write(0, 9, 9)
        self.assertFalse(join.validate(p)); self.assertFalse(join.validate(p2))

    def test_zero_negative_norm_and_unsupported_intermediate(self):
        m = Machine(width=8)
        for i, v in enumerate(((1, 2), (-1, 2), (0, 0), (2, 4), (4, 8))): m.write(i, *v)
        x, y, zero, two, four = m.reg[:5]
        f = m.admit_value(x, y, -1, True); g = m.admit_value(y, zero, 0)
        self.assertIsNotNone(f); self.assertIsNotNone(g)
        paths = [("A", m.fork()), ("B", m.fork())]
        key = Key("value", x, zero, 0, False); nk = Key("norm", x, zero, 0)
        neg = Key("value", x, y, -1, True)
        join = Join(BranchRoster(paths), [key, nk, neg])
        self.assertEqual(join.prove(key)[0], "PROVEN"); self.assertEqual(join.prove(nk)[0], "PROVEN")
        self.assertEqual(join.prove(neg)[0], "PROVEN")
        n = m.fork(); n.facts.clear(); n.admit_value(x, two, 2); n.admit_value(two, four, 2); n.admit_value(four, zero, 0)
        only_unsupported = BranchRoster([("A", n), ("B", n.fork())])
        self.assertEqual(Join(only_unsupported, [key]).prove(key)[0], "UNKNOWN")

    def test_resource_and_candidate_limits(self):
        _, paths, key = fixture(); roster = BranchRoster(paths)
        self.assertEqual(Join(roster, [key], max_work=0).prove(key)[0], "RESOURCE_LIMIT")
        self.assertEqual(Join(roster, [key], max_edges=3).prove(key)[0], "RESOURCE_LIMIT")
        other = Key("value", key.source, key.target, 1)
        join = Join(roster, [key]); self.assertEqual(join.prove(other)[0], "UNKNOWN")
        for _ in range(MAX_QUERIES): self.assertEqual(join.prove(key)[0], "PROVEN")
        self.assertEqual(join.prove(key)[0], "RESOURCE_LIMIT")
        with self.assertRaises(ValueError): Join(roster, [key, key])

    def test_inherited_identity_and_fact_capacities(self):
        m = Machine()
        for i in range(MAX_VALUES): self.assertEqual(m.write(0, i, 0), "OK")
        old = m.reg.copy()
        with self.assertRaises(OverflowError): m.write(0, 1, 0)
        self.assertEqual(m.reg, old)
        m = Machine(); ids = []
        for _ in range(17): m.write(0, 0, 0); ids.append(m.reg[0])
        for i in range(16):
            for j in range(16): m.admit_value(ids[i], ids[j])
        with self.assertRaises(OverflowError): m.admit_value(ids[16], ids[0])
        self.assertEqual(len(m.facts), MAX_FACTS)
        with self.assertRaises(ValueError): BranchRoster([(str(i), m.fork()) for i in range(4)])

    def test_provenance_node_budget(self):
        # Synthetic malformed DAG exercises the counter only; it is never trusted.
        key = Key("value", 0, 0, 1)
        node = Fact(key, "concrete_checked")
        for _ in range(MAX_BUNDLE_NODES): node = Fact(key, "compose", (node,))
        self.assertIsNone(bundle_nodes((("A", SimpleNamespace(path=(node,))),)))


if __name__ == "__main__":
    unittest.main()
