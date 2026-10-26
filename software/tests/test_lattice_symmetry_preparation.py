"""Short independent literals and accounting controls for isolated research preparation."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from software.research.lattice_symmetry.accounting import signed_bits, Work
from software.research.lattice_symmetry.comparators import run
from software.research.lattice_symmetry.mapping import quadray, lift_fcc
from software.research.lattice_symmetry.roots import reflect
from software.research.lattice_symmetry.surd_arm import run as surd_run
from software.research.lattice_symmetry.reference import reflect as reference_reflect


class PreparationLiterals(unittest.TestCase):
    def test_literal_reflections_and_padding_scale(self):
        self.assertEqual(reflect((2, 0, -2, 0), (2, -2, 0, 0)), (0, 2, -2, 0))
        self.assertEqual(reflect((2, 2, 0, 0, 0, 0, 0, 0), (1,) * 8), (1, 1, -1, -1, -1, -1, -1, -1))
        result = reference_reflect((1, 0, -1, 0), (1, -1, 0, 0))
        self.assertEqual(result, (0, 1, -1, 0))
        self.assertTrue(all(type(v) is Fraction for v in result))

    def test_fcc_bridge_domain(self):
        self.assertEqual(quadray(lift_fcc((1, -1, 0))), (1, -1, 0))
        for bad in ((1, 1, 0, 0), (True, 0, 0, 0), (2, 0, 0, 0)):
            with self.assertRaises(ValueError):
                quadray(bad)

    def test_schoolbook_cancellation_growth(self):
        work = Work()
        self.assertEqual(work.operation('subtract', Fraction(127, 2), Fraction(127, 2)), 0)
        self.assertGreaterEqual(work.peak_scalar_bits, signed_bits(254))
        self.assertEqual(work.counts['fraction_schoolbook_multiply'], 3)
        self.assertEqual([signed_bits(v) for v in (-2, -1, 0, 1, 2)], [2, 1, 1, 2, 3])

    def test_nonsymmetric_word_and_inverse(self):
        case = dict(system='D4', scaled_input=[2, -2, 0, 0], generator_word=[0, 1])
        results = [run(case, a) for a in ('coordinates', 'matrix', 'generator_word')] + [surd_run(case)]
        self.assertTrue(all(tuple(r['scaled_output']) == (-2, 0, 2, 0) for r in results))
        counts = results[0]['accounting']['operations']
        self.assertEqual((counts['multiply'], counts['add'], counts['subtract']), (16, 8, 8))
        inverse = dict(case, generator_word=[0, 1, 1, 0])
        self.assertEqual(run(inverse, 'matrix')['scaled_output'], tuple(case['scaled_input']))


if __name__ == '__main__':
    unittest.main()
