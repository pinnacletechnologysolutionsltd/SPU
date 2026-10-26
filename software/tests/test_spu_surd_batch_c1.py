"""Independent C1 Fraction oracle and focused, hardware-free checks."""
import ast
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_surd_batch_c1 as c1
c0, robot = c1.c0, c1.c0.robot


def pair(x):
    return F(x[0], x[2]), F(x[1], x[2])


def plus(x, y):
    return x[0]+y[0], x[1]+y[1]


def times(x, y):
    return x[0]*y[0]+3*x[1]*y[1], x[0]*y[1]+x[1]*y[0]


def oracle(values):
    v, j = tuple(map(pair, values[:4])), tuple(map(pair, values[4:]))
    def rotate(vector, joint):
        f, g, h = joint
        matrix = ((f, h, g), (g, f, h), (h, g, f))
        out = [vector[0]]
        for row in matrix:
            total = F(0), F(0)
            for coeff, value in zip(row, vector[1:]):
                total = plus(total, times(coeff, value))
            out.append(total)
        return tuple(out)
    forward = rotate(v, j)
    f, g, h = j
    inverse = []
    for x, y, z in ((f, g, h), (h, f, g), (g, f, h)):
        square, product = times(x, x), times(y, z)
        inverse.append((square[0]-product[0], square[1]-product[1]))
    return forward + rotate(forward, inverse)


def maintained(inputs):
    return tuple((x.p, x.q) for v in c0.kernel(inputs) for x in v.components())


def fixtures():
    """Explicit retained exact robotics cases, without executing fixture scripts."""
    result = [('software/lib/rational_robotics.py', 'sample_robot_vector/60', c0.original())]
    sample = robot.sample_robot_vector()
    p5 = robot.joint_p5_forward()
    result.extend((('software/tests/test_rational_robotics.py', 'test_p5_bypass_semantics/0',
                    (sample, p5)),
                   ('software/tests/test_rational_robotics.py', 'test_p5_bypass_semantics/1',
                    (robot.apply_joint(sample, p5), robot.joint_p5_inverse()))))
    path = 'software/tests/test_rotc_thirds_native.py'
    tree = ast.parse((ROOT / path).read_text())
    joints = (robot.joint_60(), robot.joint_120(), robot.joint_240())
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name in (
                'test_zero_sum_cases_including_negatives', 'test_surd_components_nonzero_q'):
            assignment = next(n for n in fn.body if isinstance(n, ast.Assign))
            for index, values in enumerate(ast.literal_eval(assignment.value)):
                coeffs = [(v, 0) for v in values] if isinstance(values[0], int) else values
                vector = robot.QuadrayQ(*(robot.Q3(*v) for v in coeffs))
                for angle, joint in zip((1, 3, 4), joints):
                    result.append((path, f'{fn.name}/{index:02}/angle{angle}', (vector, joint)))
    path = 'software/tests/test_rotc_six_step_rtl_trace.py'
    vector = robot.QuadrayQ(robot.q3(1), robot.q3(2, 2), robot.q3(3, 3), robot.q3(4, 4))
    result.append((path, 'generate_expected_header/root/angle1', (vector, robot.joint_60())))
    vector = robot.QuadrayQ(*(robot.q3(v) for v in (1, 2, 3, 4)))
    result.append(('tools/robotics_demo.py', 'run_demo/QLDI/angle1', (vector, robot.joint_60())))
    seen, unique = set(), []
    for source, index, inputs in sorted(result, key=lambda item: item[:2]):
        flat = c0.flatten(inputs)
        if flat not in seen:
            seen.add(flat)
            unique.append((source, index, inputs))
    return unique[:64]


class C1Tests(unittest.TestCase):
    def test_retained(self):
        for source, index, inputs in fixtures():
            self.assertEqual(c0.reconstruct(c0.flatten(inputs)), inputs)
            self.assertEqual(c0.decode(c0.encode(inputs, 2)), inputs)
            row = c1.triples(inputs)
            self.assertEqual(oracle(row), maintained(inputs), (source, index))
            for eager in (True, False):
                for shared in (row, c1.shared_block(row)):
                    self.assertEqual(c1.materialize(c1.kernel(shared, eager)), oracle(row))

    def test_batches(self):
        rows = [c1.triples(x[2]) for x in fixtures()]
        for size in (1, 16, 64):
            batch = tuple(rows[i % len(rows)] for i in range(size))
            want = tuple(map(oracle, batch))
            self.assertEqual(c1.batch_aos(batch), want)
            self.assertEqual(c1.batch_soa(c1.to_soa(batch)), want)

    def test_general_algebra(self):
        fixtures_ = ((0, 0, 7), (1, 2, 3), (-1, -2, -3),
                     (5, -4, 11), (2**70, -2**66, 17), (-1, -2, 3))
        for eager in (True, False):
            op = c1.Algebra(eager)
            for raw in fixtures_:
                x = op.canonical(raw)
                self.assertEqual(pair(x), pair(raw))
                self.assertEqual(pair(op.conjugate(x)), (pair(x)[0], -pair(x)[1]))
                for raw_y in fixtures_:
                    y = op.canonical(raw_y)
                    self.assertEqual(pair(op.add(x, y)), plus(pair(x), pair(y)))
                    self.assertEqual(pair(op.multiply(x, y)), times(pair(x), pair(y)))
                    if pair(y) != (0, 0):
                        quotient = pair(op.divide(x, y))
                        self.assertEqual(times(quotient, pair(y)), pair(x))
            self.assertEqual(op.canonical(op.add((1, 2, 3), (-1, -2, 3))), (0, 0, 1))
            with self.assertRaises(ZeroDivisionError):
                op.divide((1, 1, 2), (0, 0, 1))
            with self.assertRaises(ZeroDivisionError):
                op.canonical((1, 1, 0))

    def test_negative_controls_and_width(self):
        from software.experiments import spu_surd_batch_c1_run as runner
        with self.assertRaises(FileExistsError):
            runner.fresh_directory(ROOT)
        self.assertEqual((runner.TRIALS, runner.REPETITIONS, runner.WARMUPS), (5, 100, 3))
        inputs = c0.original()
        row = c1.triples(inputs)
        lost = tuple((a, b, 1) for a, b, d in row)
        self.assertNotEqual(c1.materialize(c1.kernel(lost)), maintained(inputs))
        trace = c1.Trace(8)
        op = c1.Algebra(trace=trace)
        result = op.multiply((100, 100, 1), (100, -100, 1))
        self.assertEqual(pair(result), times((F(100), F(100)), (F(100), F(-100))))
        self.assertGreater(trace.counts['fallback'], 0)
        self.assertGreater(trace.widths['product'], 8)
        self.assertEqual([c1.signed_width(v) for v in (0, -1, 127, -128, 128, -129)],
                         [1, 1, 8, 8, 9, 9])
        zero = c0.robot.CirculantJoint(3, robot.q3(0), robot.q3(0), robot.q3(0))
        inputs = inputs[0], zero
        self.assertEqual(c1.materialize(c1.kernel(c1.triples(inputs))), maintained(inputs))


if __name__ == '__main__':
    unittest.main()
