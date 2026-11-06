import unittest
from research.spu_bound_0.experiment import I, U, V, analyze, cases, compose, direct, extrema


class BoundsTest(unittest.TestCase):
    def test_all_prefixes_and_reconstruction(self):
        for name, box, seq in cases():
            with self.subTest(name=name):
                exact, interval, observed, *_ = analyze(box, seq)
                self.assertEqual(exact, observed)
                for bounds, actual in zip(interval, observed):
                    for (lo, hi), (a, b) in zip(bounds, actual):
                        self.assertLessEqual(lo, a)
                        self.assertGreaterEqual(hi, b)
        for name, box, seq in cases():
            matrix = I
            for sign in seq:
                matrix = compose(U if sign == 1 else V, matrix)
            power = I
            exponent = sum(seq)
            for _ in range(abs(exponent)):
                power = compose(U if exponent >= 0 else V, power)
            self.assertEqual(matrix, power, name)
            for a in range(box[0][0], box[0][1] + 1):
                for b in range(box[1][0], box[1][1] + 1):
                    value = (a, b)
                    for sign in seq:
                        value = direct(value, sign)
                    self.assertEqual(value, tuple(row[0]*a + row[1]*b for row in power))
        self.assertEqual(compose(U, V), I)
        self.assertEqual(direct(direct((3, -2), 1), -1), (3, -2))

    def test_dependency_loss(self):
        exact, interval, _, *_ = analyze(((-2, 2), (-2, 2)), [1, -1])
        self.assertEqual(exact[-1], ((-2, 2), (-2, 2)))
        self.assertEqual(interval[-1], ((-38, 38), (-22, 22)))

    def test_endpoint_signs(self):
        self.assertEqual(extrema(V, ((-2, 3), (-1, 4))), ((-16, 9), (-5, 10)))

if __name__ == '__main__':
    unittest.main()
