"""Short focused development checks; formal full fixture/control run is separate."""
import ast
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.research.aor_s1.execute import execute
from software.research.aor_s1_verification import codec, mutations, obligations, oracle, qualification, schedule


class AorS1Tests(unittest.TestCase):
    def test_root_isolation(self):
        self.assertEqual(oracle.ordering(0, 0), 0)
        self.assertEqual(oracle.ordering(-1, 1), 1)
        self.assertEqual(oracle.ordering(1, -1), -1)
        # A close Pell cancellation forces precision refinement.
        a, b = oracle.Expansion().pell(64)
        self.assertEqual(oracle.ordering(a, -b), 1)
        self.assertEqual(oracle.ordering(-a, b), -1)

    def test_codec_and_direct_api(self):
        args = codec.arguments('step', [[True, 0, 0], 1.0])
        self.assertIs(type(args), tuple)
        self.assertIs(type(args[0]), tuple)
        self.assertIs(args[0][0], True)
        self.assertIs(type(args[1]), float)
        bad = execute('canonicalize', ([1, 0, 0],), (7, -2, 11))
        self.assertEqual((bad.status, bad.charged_units), ('INVALID_INPUT', 3))
        outer = execute('canonicalize', [(1, 0, 0)], (7, -2, 11))
        self.assertEqual((outer.status, outer.charged_units), ('INVALID_INPUT', 2))

    def test_false_and_zero_success(self):
        false = execute('equality', ((1, 0, 0), (-1, 0, 0)), (7, -2, 11))
        zero = execute('sign', ((0, 0, 0),), (7, -2, 11))
        self.assertEqual(false.status, 'OK'); self.assertIs(false.result, False)
        self.assertEqual(zero.status, 'OK'); self.assertIs(type(zero.result), int)
        self.assertEqual(zero.result, 0)
        self.assertFalse(codec.identical(False, 0))

    def test_charge_precedes_callable(self):
        from software.research.aor_s1.budget import Meter, Refusal
        calls = []
        m = Meter(0)
        with self.assertRaises(Refusal):
            m.scalar('unreachable', lambda: calls.append(1))
        self.assertEqual(calls, [])
        self.assertEqual(m.events, [])
        self.assertEqual(m.next_action, 'unreachable')

    def test_immutable_outcome(self):
        from dataclasses import FrozenInstanceError
        outcome = execute('sign', ((1, 0, 0),), (7, -2, 11))
        with self.assertRaises(FrozenInstanceError):
            outcome.result = 0
        with self.assertRaises(TypeError):
            outcome.events[0]['value'] = False
        with self.assertRaises(TypeError):
            outcome.primitive_counts['width_checks'] = 0

    def test_direct_zero_kernel_rejection(self):
        from software.research.aor_s1.budget import InvariantError
        from software.research.aor_s1.execute import run_kernel
        with self.assertRaises(InvariantError):
            run_kernel((0, 0), 0)
        # Public canonical zero still takes its valid explicit dispatch path.
        result = execute('canonicalize', ((0, 0, 0),), (7, -2, 11))
        self.assertEqual((result.status, result.result, result.charged_units), ('OK', (0, 0, 0), 14))

    def test_private_arithmetic_and_checker_meta(self):
        fixtures = codec.load(ROOT / 'spu_strategy/aor_s1_literal_fixtures_2026-10-14.json')['fixtures']
        fixture = next(f for f in fixtures if f['id'] == 'multiply_upper_negative_norm')
        control = dict(id='DROPPED_3BD')
        observe = lambda: qualification.observe('operation', fixture, {})
        clean = observe()
        changed = mutations.candidate(control, clean, observe)
        self.assertEqual(obligations.operation(fixture, clean), set())
        self.assertFalse(codec.identical(clean, changed))
        labels = obligations.operation(fixture, changed)
        self.assertIn('REJECT_PRODUCT_VALUE', labels)
        broken, outer = mutations.checker_meta(labels, 'REJECT_PRODUCT_VALUE')
        self.assertNotIn('REJECT_PRODUCT_VALUE', broken)
        self.assertIn('META_REJECT_CHECKER_MISSED_REQUIRED_LABEL', outer)
        self.assertTrue(codec.identical(clean, observe()))

    def test_oracle_fault_with_clean_candidate(self):
        fixtures = codec.load(ROOT / 'spu_strategy/aor_s1_qualification_supplement_2026-10-14.json')['fixtures']
        fixture = next(f for f in fixtures if f['id'] == 'supplement_norm_success')
        clean = qualification.observe('operation', fixture, {})
        answer = oracle.answer(fixture)
        changed = mutations.oracle(dict(id='ORACLE_BAD_NORM'), answer)
        self.assertEqual(obligations.operation(fixture, clean, answer), set())
        self.assertIn('REJECT_NORM_VALUE', obligations.operation(fixture, clean, changed))

    def test_identity_budget_boundaries(self):
        fixtures = codec.load(ROOT / 'spu_strategy/aor_s1_qualification_supplement_2026-10-14.json')['fixtures'][-3:]
        for fixture in fixtures:
            observed = codec.plain(execute(fixture['operation'], codec.arguments(fixture['operation'], fixture['arguments']),
                                      tuple(fixture['initial_destination']), budget=fixture['budget']))
            self.assertEqual(obligations.operation(fixture, observed), set())
            self.assertTrue(codec.identical(observed['events'], schedule.operation(fixture)['events']))

    def test_import_independence(self):
        for name in ('oracle', 'obligations', 'schedule', 'schedule_arithmetic', 'codec'):
            path = ROOT / f'software/research/aor_s1_verification/{name}.py'
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or '']
                else:
                    continue
                self.assertFalse(any(m == 'software.research.aor_s1' or m.startswith('software.research.aor_s1.') for m in modules))


if __name__ == '__main__':
    unittest.main()
