import itertools
import json
import unittest
from fractions import Fraction
from pathlib import Path
from research.symreg_geom_0 import checker, model, oracle


class GeometryTests(unittest.TestCase):
    def test_universal_and_compositions(self):
        for length in range(9):
            cert = model.certificate([model.QUARTER] * length)
            self.assertEqual(checker.check(cert)["status"], "VERIFIED")
        self.assertEqual(checker.check(model.certificate([]))["status"], "VERIFIED")

    def test_all_small_rational_vectors(self):
        for values in itertools.product(range(-2, 3), repeat=4):
            v = ((Fraction(values[0], 2), Fraction(values[1], 3)),
                 (Fraction(values[2], 2), Fraction(values[3], 3)))
            self.assertEqual(oracle.quadrance(v), oracle.quadrance(oracle.transform(model.QUARTER, v)))

    def test_concrete_coincidence_not_universal(self):
        bad = ((2, 0), (0, 1))
        v = ((Fraction(0), Fraction(0)), (Fraction(3), Fraction(1)))
        self.assertEqual(oracle.quadrance(v), oracle.quadrance(oracle.transform(bad, v)))
        self.assertEqual(checker.check(model.certificate([bad]))["status"], "REJECTED")
        w = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(0)))
        self.assertNotEqual(oracle.quadrance(w), oracle.quadrance(oracle.transform(bad, w)))

    def test_forged_composition_and_labels(self):
        obj = json.loads(model.certificate([((2, 0), (0, 1))]))
        obj["composition"] = [[1, 0], [0, 1]]
        encoded = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(checker.check(encoded)["status"], "REJECTED")
        obj["preserves"] = True
        self.assertEqual(checker.check(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())["status"], "REJECTED")

    def test_bad_inputs_and_limits(self):
        self.assertEqual(checker.check(b"{}")['status'], "REJECTED")
        self.assertEqual(checker.check(b'{"x":1,"x":1}')['status'], "REJECTED")
        self.assertEqual(checker.check(b"x"*16385)['status'], "REJECTED")
        self.assertEqual(checker.check(model.certificate([model.QUARTER]*33))['status'], "REJECTED")
        self.assertEqual(checker.check(model.certificate([((True, 0), (0, 1))]))['status'], "REJECTED")
        self.assertEqual(checker.check(model.certificate([((2, 0), (0, 2))]*11))['status'], "REJECTED")

    def test_checker_independent(self):
        self.assertNotIn("symreg_geom_0.model", Path(checker.__file__).read_text())


if __name__ == "__main__":
    unittest.main()
