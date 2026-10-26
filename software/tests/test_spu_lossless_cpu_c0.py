#!/usr/bin/env python3
"""Focused C0 checks. Importing the runner never creates child processes."""
import json
import math
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_lossless_cpu_c0 as c0
from software.experiments import spu_lossless_storage as storage
from software.tests.test_spu_lossless_reduction import LosslessReductionTests


class TestCpuStorage(unittest.TestCase):
    def test_retained_input_and_reference(self):
        vector, joint = c0.original()
        self.assertEqual(c0.flatten((vector, joint)),
                         (1,1,0,1,0,1,1,1,1,3,0,1,-2,1,0,1,2,3,0,1,2,3,0,1,-1,3,0,1))
        forward, recovered = c0.kernel((vector, joint))
        # Direct retained-value calculation; independent of codec or edge reducers.
        expected = c0.robot.QuadrayQ(c0.robot.q3(1),
                                    c0.robot.q3(Fraction(-13,9), Fraction(2,3)),
                                    c0.robot.q3(Fraction(8,9), Fraction(2,3)),
                                    c0.robot.q3(Fraction(-10,9), Fraction(-1,3)))
        self.assertEqual(forward, expected)
        self.assertEqual(recovered, vector)
        frame = c0.robot.six_step_kinematics_trace()[0]
        self.assertEqual((forward, recovered), (frame.commanded_vector, frame.recovered_vector))
        for mode in c0.MODES:
            decoded = c0.decode(c0.encode((vector, joint), mode))
            self.assertEqual(decoded, (vector, joint))
            self.assertEqual(c0.kernel(decoded), (expected, vector))

    def test_sizes_selection_and_order(self):
        values = c0.flatten(c0.original())
        streams, exclusions = c0.candidate_streams(values)
        self.assertFalse(exclusions)
        for mode, stream in streams.items():
            self.assertEqual(len(stream), c0.independent_sizes(values)[mode])
            self.assertEqual(storage.decode(stream[5:]), list(values))
        chosen = min(streams, key=lambda m: (c0.independent_sizes(values)[m], m))
        self.assertEqual(c0.encode(c0.original(), 5), streams[chosen])
        # Independent tie fixture: one value 2**54 has packed=fixed complete size.
        tie = (1 << 54,)
        streams, _ = c0.candidate_streams(tie)
        self.assertEqual(c0.independent_sizes(tie)[0], c0.independent_sizes(tie)[2])
        self.assertEqual(min(streams, key=lambda m: (len(streams[m]), m)), 0)
        for values in ((), (0,)*32, (-2**63,2**63-1), (6,-12,18), (1,)*31):
            for mode, stream in c0.candidate_streams(values)[0].items():
                self.assertEqual(len(stream), c0.independent_sizes(values)[mode])
                self.assertEqual(storage.decode(stream[5:]), list(values))
        for bad in ((True,), (2**63,), (-2**63-1,), (0,)*33):
            with self.assertRaises(ValueError):
                c0.candidate_streams(bad)

    def test_malformed_and_corruption(self):
        rejected = 0
        for mode in (0,2,3,4):
            stream = c0.encode(c0.original(), mode)
            bad = [stream[:i] for i in range(len(stream))]
            bad += [stream+b'\0', b'XX'+stream[2:], stream[:5]+b'\xff'+stream[6:]]
            if mode in (0,2,3):
                offset = 6 + (8 if mode == 3 else 0)
                bad.append(stream[:offset]+(33).to_bytes(4,'little')+stream[offset+4:])
            if mode in (2,3):
                width_offset = 10 + (8 if mode == 3 else 0)
                bad.append(stream[:width_offset]+b'\x41'+stream[width_offset+1:])
                bad.append(stream[:-1]+bytes([stream[-1] | 128]))
            for corrupt in bad:
                with self.assertRaises(ValueError):
                    c0.decode(corrupt)
                rejected += 1
        # Valid framing but changed coefficient: equivalence detects corruption.
        fixed = bytearray(c0.encode(c0.original(), 0))
        fixed[10] = 2
        self.assertNotEqual(c0.kernel(c0.decode(bytes(fixed))), c0.kernel(c0.original()))
        print('C0 malformed rejections:', rejected, '; coefficient corruption detected')

    def test_denominators_and_errors(self):
        values = list(c0.flatten(c0.original()))
        for denominator in (0,-1,2):
            changed = values.copy()
            changed[1] = denominator
            if denominator == 2:  # force reducible 2/2
                changed[0] = 2
            with self.assertRaises(ValueError):
                c0.reconstruct(changed)
        with self.assertRaises(ValueError):
            c0.reconstruct(values[:-1])
        inputs = c0.original()
        invalid_joint = c0.robot.CirculantJoint(3,c0.robot.q3(0),c0.robot.q3(0),c0.robot.q3(0))
        # Maintained inverse assumes determinant one; it does not trap a zero joint.
        retained_behavior = c0.kernel((inputs[0],invalid_joint))
        self.assertEqual(c0.kernel(c0.decode(c0.encode((inputs[0],invalid_joint), 2))),
                         retained_behavior)

    def test_output_refusal(self):
        from software.experiments.spu_lossless_cpu_c0_run import fresh_directory
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                fresh_directory(Path(directory))


def check_correctness():
    suite = unittest.TestSuite()
    # Reuse R0 strict codec checks in full; no subprocess and no GPU prerequisite.
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestCpuStorage))
    for name in ('test_packing_exhaustive_and_seeded', 'test_packing_golden_and_boundaries',
                 'test_packing_invalid_inputs_and_streams', 'test_factors_rationals_and_surds'):
        suite.addTest(LosslessReductionTests(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return {'passed': result.wasSuccessful(), 'tests_run': result.testsRun,
            'failures': [str(test)+': '+detail for test,detail in result.failures+result.errors]}


if __name__ == '__main__':
    raise SystemExit(0 if check_correctness()['passed'] else 1)
