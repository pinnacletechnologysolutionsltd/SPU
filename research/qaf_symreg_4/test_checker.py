"""Adversarial certificate cases and an independent exact-arithmetic oracle."""
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from itertools import product
from pathlib import Path

from research.qaf_symreg_4.checker import DOMAIN, MAX_BYTES, MAX_DEPTH, MAX_STEPS, canonical, verify
from research.qaf_symreg_4.examples import build_example


def norm(v):
    a, b = map(Fraction, v)
    return (a+b)*(a-b)-2*b*b


def load_example(n=3):
    ctx, cert = build_example(n)
    return json.loads(ctx), json.loads(cert)


def encode(ctx, cert):
    context = canonical(ctx)
    cert["context_sha256"] = hashlib.sha256(context).hexdigest()
    return canonical(cert), context


def single(value, k, flip):
    a, b = value
    target = [k*a, -k*b if flip else k*b]
    flip = flip if k else False
    claim = {"kind": "value", "source": "x", "target": "y", "k": k, "flip": flip}
    ctx = {"version": 1, "domain": DOMAIN, "scope": "test_scope", "values": {"x": [a, b], "y": target},
           "branches": {"A": {"bindings": {"r0": "x", "r1": "y"}, "premises": {"p": claim}}}}
    step = {"branch": "A", "rule": "PREMISE", "claim": claim, "inputs": [], "premise": "p"}
    cert = {"version": 1, "domain": DOMAIN, "scope": "test_scope", "context_sha256": "", "branches": ["A"], "steps": [step],
            "conclusion": {"rule": "ALL_FEASIBLE_PATHS", "claim": claim, "witnesses": {"A": 0},
                           "current": {"source": "r0", "target": "r1"}}}
    return ctx, cert


class CertificateTests(unittest.TestCase):
    def assert_rejected(self, ctx, cert, reason=None):
        result = verify(*encode(ctx, cert))
        self.assertEqual(result["status"], "REJECTED", result)
        if reason: self.assertEqual(result["reason"], reason)

    def test_predecessor_adapters_and_independent_oracle(self):
        for number in (1, 2, 3):
            context, certificate = build_example(number)
            result = verify(certificate, context)
            self.assertEqual(result["status"], "VERIFIED")
            ctx, cert = json.loads(context), json.loads(certificate)
            for step in cert["steps"]:
                claim = step["claim"]
                x, y = ctx["values"][claim["source"]], ctx["values"][claim["target"]]
                if claim["kind"] == "value":
                    self.assertEqual(tuple(map(Fraction, y)),
                                     (claim["k"]*Fraction(x[0]), (-claim["k"] if claim["flip"] else claim["k"])*Fraction(x[1])))
                else:
                    self.assertEqual(norm(y), claim["k"]*norm(x))

    def test_systematic_direct_and_norm_cases(self):
        count = 0
        for a, b, k, flip in product(range(-1, 2), range(-1, 2), (-2, -1, 0, 1, 2), (False, True)):
            ctx, cert = single((a, b), k, flip)
            self.assertEqual(verify(*encode(ctx, cert))["status"], "VERIFIED")
            fact = cert["steps"][0]["claim"]
            projected = {"kind": "norm", "source": "x", "target": "y", "k": k*k, "flip": False}
            cert["steps"].append({"branch": "A", "rule": "NORM", "claim": projected, "inputs": [0], "premise": None})
            cert["conclusion"]["claim"] = projected; cert["conclusion"]["witnesses"]["A"] = 1
            self.assertEqual(verify(*encode(ctx, cert))["status"], "VERIFIED")
            self.assertEqual(norm(ctx["values"]["y"]), k*k*norm(ctx["values"]["x"]))
            count += 1
        self.assertEqual(count, 90)

    def test_untrusted_false_and_wrong_branch_premises(self):
        ctx, cert = load_example(); cert["steps"][0]["premise"] = "invented"
        self.assert_rejected(ctx, cert, "UNTRUSTED_PREMISE")
        ctx, cert = load_example(); claim = ctx["branches"]["A"]["premises"]["p0"]
        claim["flip"] = False; cert["steps"][0]["claim"]["flip"] = False
        self.assert_rejected(ctx, cert, "FALSE_PREMISE")
        ctx, cert = load_example(); cert["steps"][0]["branch"] = "B"
        self.assert_rejected(ctx, cert)
        ctx, cert = load_example(); false_claim = dict(ctx["branches"]["A"]["premises"]["p0"])
        false_claim["flip"] = False
        ctx["branches"]["A"]["premises"]["unused_false"] = false_claim
        self.assert_rejected(ctx, cert, "FALSE_PREMISE")

    def test_wrong_rules_references_and_norm_scaling(self):
        ctx, cert = load_example(1); cert["steps"][-1]["claim"]["k"] = 2
        self.assert_rejected(ctx, cert, "RULE")
        for bad in (-1, 99, True):
            ctx, cert = load_example(2); cert["steps"][-1]["inputs"][0] = bad
            self.assert_rejected(ctx, cert, "REFERENCE")
        ctx, cert = load_example(3); cert["steps"][-1]["inputs"][0] = 0
        self.assert_rejected(ctx, cert, "CROSS_BRANCH")
        ctx, cert = load_example(2); cert["steps"][-1]["rule"] = "MAGIC"
        self.assert_rejected(ctx, cert, "UNSUPPORTED_RULE")
        ctx, cert = load_example(2); cert["steps"][-1]["claim"]["k"] = 4
        self.assert_rejected(ctx, cert, "UNSUPPORTED")

    def test_coverage_stale_context_and_binding(self):
        ctx, cert = load_example(); del cert["conclusion"]["witnesses"]["B"]
        self.assert_rejected(ctx, cert, "BRANCH_COVERAGE")
        ctx, cert = load_example(); cert["conclusion"]["witnesses"]["B"] = cert["conclusion"]["witnesses"]["A"]
        self.assert_rejected(ctx, cert, "BRANCH_WITNESS")
        ctx, cert = load_example(); old_cert = canonical(cert); ctx["branches"]["A"]["bindings"]["r0"] = "v1"
        self.assertEqual(verify(old_cert, canonical(ctx))["reason"], "STALE_CONTEXT")
        self.assert_rejected(ctx, cert, "STALE_BINDING")  # even if rehashed, current binding is wrong
        ctx, cert = load_example(); del ctx["branches"]["B"]
        self.assert_rejected(ctx, cert, "BRANCH_COVERAGE")
        ctx, cert = load_example(); ctx["scope"] = "new_epoch"
        self.assert_rejected(ctx, cert, "STALE_SCOPE")

    def test_resource_limits_and_malformed_serialization(self):
        ctx, cert = load_example(2); cert["steps"] *= MAX_STEPS
        self.assert_rejected(ctx, cert, "RESOURCE_LIMIT")
        self.assertEqual(verify(b"x"*(MAX_BYTES+1), canonical(ctx))["reason"], "RESOURCE_LIMIT")
        context, certificate = build_example(2)
        self.assertEqual(verify(b'{"x":1,"x":2}', context)["reason"], "DUPLICATE_KEY")
        self.assertEqual(verify(certificate+b"\n", context)["reason"], "NON_CANONICAL")
        ctx, cert = load_example(2)
        for i in range(65): ctx["values"]["extra" + str(i)] = [0, 0]
        self.assert_rejected(ctx, cert, "RESOURCE_LIMIT")
        ctx, cert = load_example(2); claim = ctx["branches"]["A"]["premises"]["p0"]
        ctx["branches"]["A"]["premises"] = {"p" + str(i): claim for i in range(257)}
        self.assert_rejected(ctx, cert, "RESOURCE_LIMIT")

    def test_depth_limit(self):
        ctx, cert = single((1, 2), 1, False)
        # Change the reference to a self-relation so it can be composed repeatedly.
        claim = {"kind": "value", "source": "x", "target": "x", "k": 1, "flip": False}
        ctx["branches"]["A"]["premises"]["p"] = claim
        cert["steps"][0]["claim"] = claim
        for i in range(1, MAX_DEPTH+1):
            cert["steps"].append({"branch": "A", "rule": "COMPOSE", "claim": claim, "inputs": [i-1, 0], "premise": None})
        cert["conclusion"]["claim"] = claim; cert["conclusion"]["witnesses"]["A"] = MAX_DEPTH
        cert["conclusion"]["current"] = None
        self.assert_rejected(ctx, cert, "RESOURCE_LIMIT")

    def test_checker_does_not_import_inference(self):
        source = Path(__file__).with_name("checker.py").read_text()
        tree = ast.parse(source)
        imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        self.assertFalse(any(s.startswith("research.") for s in imports))

    def test_portable_cli_in_isolated_interpreter(self):
        context, certificate = build_example(3)
        checker = Path(__file__).with_name("checker.py").resolve()
        with tempfile.TemporaryDirectory(prefix="symreg4_cli_") as directory:
            root = Path(directory); cert_path = root / "proof.json"; ctx_path = root / "trusted.json"
            cert_path.write_bytes(certificate); ctx_path.write_bytes(context)
            run = subprocess.run([sys.executable, "-I", str(checker), str(cert_path), str(ctx_path)],
                                 cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["status"], "VERIFIED")
            cert_path.write_bytes(certificate+b"\n")
            bad = subprocess.run([sys.executable, "-I", str(checker), str(cert_path), str(ctx_path)],
                                 cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(bad.returncode, 1)
            self.assertEqual(json.loads(bad.stdout)["reason"], "NON_CANONICAL")


if __name__ == "__main__":
    unittest.main()
