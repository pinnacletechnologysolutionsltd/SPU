import unittest
from research.mathstate_0.experiment import INV, NEG, U, apply, certified, fixtures, fuse, power, run, width


class ModelTests(unittest.TestCase):
    def test_fixtures(self):
        cases = fixtures()
        for name in ('F1', 'F2', 'F4', 'F7'):
            start, seq = cases[name]
            self.assertEqual(run(start, seq)['status'], 0)
            self.assertEqual(run(start, seq)['value'], fuse(start, seq)['value'])
        start, seq = cases['F3']
        eager = run(start, seq)
        self.assertEqual((eager['status'], eager['refusal'], eager['value']), (2, 1, start))
        self.assertEqual(fuse(start, seq)['value'], start)
        self.assertGreater(max(width(v) for row in power(34) for v in row), 64)
        self.assertLessEqual(run(*cases['F2'])['maximum_width'], 64)

    def test_historical_identity(self):
        old = (3, -2)
        relation = (old, U)  # immutable identity and transformation retained
        register = (7, 8)
        self.assertEqual(apply(relation[1], relation[0]), (0, -1))
        self.assertNotEqual(apply(relation[1], register), (0, -1))

    def test_certification_boundary(self):
        self.assertEqual(certified((3, -2), [U, INV], 0, False), 'CONDITIONAL_FINAL_STATE_ONLY')
        self.assertEqual(certified((3, -2), [U, INV], 0, True), 'UNKNOWN')
        self.assertEqual(certified(((1 << 63)-1, 0), [U, INV], 0, False), 'UNKNOWN')
        self.assertEqual(certified((3, -2), [U, NEG], 0, False), 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
