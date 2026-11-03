import unittest
from fractions import Fraction
from pathlib import Path

from research.qaf_symreg_4.checker import canonical, parse
from research.qaf_symreg_5.authority import Authority, MAX_EPOCHS
from research.qaf_symreg_5.checker import assess
from research.qaf_symreg_5.producer import produce


def fixture():
    auth = Authority("owner")
    epoch = auth.allocate("episode")
    x = auth.identity(1, 2)
    y = auth.identity(1, -2)
    claim = {"kind": "value", "source": x, "target": y, "k": 1, "flip": True}
    branches = {b: {"bindings": {"r0": x, "r1": y}, "premises": {"claim": claim}}
                for b in ("A", "B")}
    rev, ctx = auth.provision([x, y], branches)
    env = produce(ctx, auth.name, epoch, rev, "r0", "r1")
    return auth, epoch, x, y, branches, env


class ContextTests(unittest.TestCase):
    def test_original_and_exact_oracle(self):
        a, _, x, y, _, env = fixture()
        result = assess(env, a.view())
        self.assertEqual(result["math"]["status"], "VERIFIED")
        self.assertEqual(result["identity"], "MATCH")
        self.assertEqual(result["authorization"], "AUTHORIZED_CURRENT")
        p, q = a.registry[x], a.registry[y]
        self.assertEqual((Fraction(p[0]), -Fraction(p[1])), tuple(map(Fraction, q)))

    def test_small_domain_against_independent_oracle(self):
        for p in range(-3, 4):
            for q in range(-3, 4):
                a = Authority("oracle")
                epoch = a.allocate("test")
                x, y = a.identity(p, q), a.identity(p, -q)
                claim = {"kind": "value", "source": x, "target": y, "k": 1, "flip": True}
                branches = {"A": {"bindings": {"r0": x, "r1": y}, "premises": {"claim": claim}}}
                rev, ctx = a.provision([x, y], branches)
                proof = produce(ctx, a.name, epoch, rev, "r0", "r1")
                self.assertEqual((Fraction(p), -Fraction(q)), tuple(map(Fraction, a.registry[y])))
                self.assertEqual(assess(proof, a.view())["authorization"], "AUTHORIZED_CURRENT")

    def test_overwrite_preserves_history(self):
        a, epoch, x, y, branches, old = fixture()
        replacement = a.identity(7, 9)
        for b in branches.values():
            b["bindings"]["r0"] = replacement
        revision, ctx = a.provision([x, y, replacement], branches)
        old_result = assess(old, a.view())
        self.assertEqual(old_result["math"]["status"], "VERIFIED")
        self.assertEqual(old_result["authorization"], "REJECTED")
        historical = produce(ctx, a.name, epoch, revision, "r0", "r1", current=False)
        self.assertEqual(assess(historical, a.view())["authorization"], "AUTHORIZED_HISTORICAL")
        stale_current = produce(ctx, a.name, epoch, revision, "r0", "r1")
        self.assertEqual(assess(stale_current, a.view())["math"]["reason"], "STALE_BINDING")

    def test_expiry_and_explicit_label_reuse(self):
        a, _, _, _, _, env = fixture()
        with self.assertRaises(ValueError):
            a.allocate("episode")
        a.expire()
        self.assertEqual(assess(env, a.view())["math"]["status"], "VERIFIED")
        self.assertEqual(assess(env, a.view())["authorization"], "REJECTED")
        self.assertEqual(a.allocate("episode", reuse=True), 2)
        self.assertEqual(assess(env, a.view())["authorization"], "REJECTED")
        with self.assertRaises(ValueError):
            a.identity(1, 2, requested="v0")

    def test_unrelated_and_identity_collision(self):
        a, _, _, _, _, env = fixture()
        b, _, _, _, _, _ = fixture()
        b.name = "other"
        self.assertEqual(assess(env, b.view())["reason"], "AUTHORITY")
        view = parse(a.view())
        view["registry"]["v0"] = [99, 2]
        result = assess(env, canonical(view))
        self.assertEqual(result["identity"], "MISMATCH")
        self.assertEqual(result["authorization"], "REJECTED")

    def test_branch_and_premise_controls(self):
        a, _, _, _, branches, env = fixture()
        changed = parse(env)
        del changed["certificate"]["conclusion"]["witnesses"]["B"]
        self.assertEqual(assess(canonical(changed), a.view())["math"]["reason"], "BRANCH_COVERAGE")
        changed = parse(env)
        changed["certificate"]["steps"][0]["premise"] = "unauthorized"
        self.assertEqual(assess(canonical(changed), a.view())["math"]["reason"], "UNTRUSTED_PREMISE")
        del branches["B"]
        a.provision(["v0", "v1"], branches)
        self.assertEqual(assess(env, a.view())["authorization"], "REJECTED")

    def test_context_substitution_and_epoch_mutation(self):
        a, _, _, _, _, env = fixture()
        obj = parse(env)
        obj["epoch"] = 2
        self.assertEqual(assess(canonical(obj), a.view())["authorization"], "REJECTED")
        obj["epoch"] = True
        self.assertEqual(assess(canonical(obj), a.view())["authorization"], "REJECTED")
        obj = parse(env)
        obj["certificate"]["context_sha256"] = "0" * 64
        self.assertEqual(assess(canonical(obj), a.view())["math"]["reason"], "STALE_CONTEXT")

    def test_bounded_no_wrap(self):
        a = Authority("owner")
        for i in range(MAX_EPOCHS):
            a.allocate("label" + str(i))
        with self.assertRaises(ValueError):
            a.allocate("overflow")
        self.assertEqual(a.active, MAX_EPOCHS)

    def test_bad_concrete_premise_rejected_at_provision(self):
        a, _, x, y, branches, _ = fixture()
        branches["A"]["premises"]["claim"]["k"] = 2
        with self.assertRaises(Exception):
            a.provision([x, y], branches)

    def test_independent_checker_imports_no_producer(self):
        import research.qaf_symreg_5.checker as checker
        source = Path(checker.__file__).read_text(encoding="utf8")
        self.assertNotIn("producer", source.split("if __name__")[0].split("\n", 1)[1])

    def test_same_name_new_authority_is_not_durable(self):
        first, _, _, _, _, old = fixture()
        second, _, _, _, _, _ = fixture()
        # A restarted, identically initialized authority is indistinguishable.
        self.assertEqual(first.view(), second.view())
        self.assertEqual(assess(old, second.view())["authorization"], "AUTHORIZED_CURRENT")


if __name__ == "__main__":
    unittest.main()
