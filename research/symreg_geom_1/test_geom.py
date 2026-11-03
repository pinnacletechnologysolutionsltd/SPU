import itertools
import json
import unittest
from fractions import Fraction
from pathlib import Path
from research.symreg_geom_1 import checker, model, oracle

I = [[1, 0], [0, 1]]
E = [[1, 0], [0, 1]]
H = [[1, 0], [0, -1]]
C = [[2, 1], [1, 2]]
R = [[0, -1], [1, 0]]
HEX = [[0, -1], [1, 1]]
SIGN = [[-1, 0], [0, 1]]
PELL_G = [[1, 0], [0, -2]]
PELL = [[3, 4], [2, 3]]


class GeometryTests(unittest.TestCase):
    def test_forms_and_compositions(self):
        for g, m in ((E, R), (H, SIGN), (C, HEX), (PELL_G, PELL)):
            self.assertEqual(checker.check(model.certificate(g, [m]))["status"], "VERIFIED")
        for g, m in ((E, R), (H, SIGN), (C, HEX)):
            for n in range(9):
                self.assertEqual(checker.check(model.certificate(g, [m]*n))["status"], "VERIFIED")
        self.assertEqual(checker.check(model.certificate([[0, 0], [0, 0]], [PELL]))["status"], "VERIFIED")

    def test_exact_rational_oracle(self):
        for g, m in ((E, R), (H, SIGN), (C, HEX), (PELL_G, PELL)):
            for vals in itertools.product(range(-2, 3), repeat=4):
                v = ((Fraction(vals[0], 2), Fraction(vals[1], 3)),
                     (Fraction(vals[2], 2), Fraction(vals[3], 3)))
                self.assertEqual(oracle.form(g, v), oracle.form(g, oracle.apply(m, v)))

    def test_form_specific_and_coincidence(self):
        self.assertEqual(checker.check(model.certificate(C, [R]))["status"], "REJECTED")
        self.assertEqual(checker.check(model.certificate(E, [HEX]))["status"], "REJECTED")
        scale = [[2, 0], [0, 1]]
        v = ((Fraction(0), Fraction(0)), (Fraction(1), Fraction(2)))
        self.assertEqual(oracle.form(E, v), oracle.form(E, oracle.apply(scale, v)))
        self.assertEqual(checker.check(model.certificate(E, [scale]))["status"], "REJECTED")

    def test_bad_inputs_and_forgery(self):
        self.assertEqual(checker.check(model.certificate([[1, 1], [0, 1]], [I]))["status"], "REJECTED")
        self.assertEqual(checker.check(model.certificate([[True, 0], [0, 1]], [I]))["status"], "REJECTED")
        self.assertEqual(checker.check(model.certificate(E, [R]*33))["status"], "REJECTED")
        self.assertEqual(checker.check(model.certificate(E, [[[4, 0], [0, 4]]]*7))["status"], "REJECTED")
        self.assertEqual(checker.check(b'{"x":1,"x":1}')["status"], "REJECTED")
        self.assertEqual(checker.check(b"x"*16385)["status"], "REJECTED")
        obj = json.loads(model.certificate(E, [R]))
        obj["composition"] = I
        self.assertEqual(checker.check(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())["status"], "REJECTED")
        obj["version"] = 1
        self.assertEqual(checker.check(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())["status"], "REJECTED")

    def test_checker_independent(self):
        self.assertNotIn("symreg_geom_1.model", Path(checker.__file__).read_text())


if __name__ == "__main__":
    unittest.main()
