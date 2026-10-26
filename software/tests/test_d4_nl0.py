"""Independent exact equivariance and width checks for D4-NL-0."""

from itertools import product
import unittest

from software.research.lattice_comparison import d4
from software.research.d4_symmetry import nonlinear
from software.research.d4_symmetry.nonlinear_demo import domain


GROUP = tuple(d4.group())
OPERATORS = (nonlinear.identity, nonlinear.radial,
             nonlinear.cubic_coupled, nonlinear.odd_threshold)


def oracle_action(descriptor, vector):
    permutation, signs = descriptor
    return tuple((-vector[permutation[i]] if signs[i]
                  else vector[permutation[i]]) for i in range(4))


def oracle_radial(x):
    q = sum(xi * xi for xi in x)
    return tuple((1 + q) * xi for xi in x)


def oracle_cubic(x):
    q = sum(xi * xi for xi in x)
    return tuple(xi + xi * xi * xi + xi * q for xi in x)


def oracle_odd_threshold(x):
    result = []
    for xi in x:
        if xi >= 2:
            result.append(xi - 2)
        elif xi <= -2:
            result.append(xi + 2)
        else:
            result.append(0)
    return tuple(result)


class D4NL0Tests(unittest.TestCase):
    def test_frozen_group_and_domain(self):
        self.assertEqual(192, len(GROUP))
        self.assertEqual(192, len(set(GROUP)))
        self.assertEqual(3281, len(domain()))

    def test_exact_equivariance_against_independent_formulas(self):
        oracle_operators = (lambda x: tuple(x), oracle_radial,
                            oracle_cubic, oracle_odd_threshold)
        for operator, oracle in zip(OPERATORS, oracle_operators):
            for vector in domain():
                self.assertEqual(oracle(vector), operator(vector))
                for element in GROUP:
                    transformed = oracle_action(element, vector)
                    lhs = operator(transformed)
                    rhs = oracle_action(element, oracle(vector))
                    self.assertEqual(lhs, rhs)

    def test_group_action_composition_control(self):
        vector = (1, -2, 3, -4)
        for left in GROUP:
            for right in GROUP:
                composed = d4.compose(left, right)
                self.assertEqual(oracle_action(left, oracle_action(right, vector)),
                                 oracle_action(composed, vector))

    def test_stabilizer_preservation(self):
        vectors = ((0, 0, 0, 0), (1, 1, 2, 2))
        for vector in vectors:
            for element in GROUP:
                if oracle_action(element, vector) == vector:
                    for operator in OPERATORS:
                        self.assertEqual(oracle_action(element, operator(vector)),
                                         operator(vector))

    def test_width_bounds_and_observed_outputs(self):
        report = nonlinear.width_report(4)
        self.assertEqual(7, report["norm2_unsigned_bits"])
        self.assertEqual(10, report["radial_output_signed_bits"])
        self.assertEqual(8, report["cubic_term_signed_bits"])
        self.assertEqual(10, report["coupled_product_signed_bits"])
        self.assertEqual(10, report["cubic_output_signed_bits"])
        self.assertEqual(3, report["odd_threshold_output_signed_bits"])
        maxima = {"radial": 260, "cubic_coupled": 324, "odd_threshold": 2}
        for name, operator in zip(("radial", "cubic_coupled", "odd_threshold"),
                                  (nonlinear.radial, nonlinear.cubic_coupled,
                                   nonlinear.odd_threshold)):
            observed = max(abs(value) for x in domain() for value in operator(x))
            self.assertLessEqual(observed, maxima[name])
            self.assertLessEqual(observed, report["max_magnitudes"][
                {"radial": "radial_output", "cubic_coupled": "cubic_output",
                 "odd_threshold": "odd_threshold_output"}[name]])

    def test_declared_source_level_counts(self):
        counts = nonlinear.primitive_counts()
        self.assertEqual({"multiplications": 8, "additions": 4}, counts["radial"])
        self.assertEqual({"multiplications": 12, "additions": 11},
                         counts["cubic_coupled"])
        self.assertEqual({"absolute_values": 4, "comparisons": 12,
                          "subtractions": 4, "selections": 12,
                          "sign_applications": 4}, counts["odd_threshold"])

    def test_nonlinear_maps_differ_from_identity_on_frozen_inputs(self):
        vector = (1, 2, 3, 4)
        for operator in (nonlinear.radial, nonlinear.cubic_coupled,
                         nonlinear.odd_threshold):
            self.assertNotEqual(vector, operator(vector))

    def test_validation(self):
        with self.assertRaisesRegex(ValueError, "D4_NL_VECTOR"):
            nonlinear.radial((1, 2, 3))
        with self.assertRaisesRegex(ValueError, "D4_NL_THRESHOLD"):
            nonlinear.odd_threshold((1, 2, 3, 4), -1)
        with self.assertRaisesRegex(ValueError, "D4_NL_BOUND"):
            nonlinear.width_report(-1)


if __name__ == "__main__":
    unittest.main()
