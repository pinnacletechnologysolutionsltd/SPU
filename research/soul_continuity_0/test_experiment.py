import copy
import unittest
from engines import EngineA, EngineB
from evaluate import prepare, run, summary
from model import checkpoint, digest, validate

class ContinuityTests(unittest.TestCase):
    def test_registered_comparison_and_controls(self):
        result, cp, migrated, forks, states = run()
        self.assertEqual(cp, migrated)
        self.assertTrue(result['migration']['validated'])
        self.assertEqual(result['migration']['missing_or_altered'], 0)
        self.assertTrue(all(result['controls'].values()))
        self.assertTrue(result['fork_valid'])
        self.assertEqual(result['results']['C1']['answers']['transfer'], 'chest')
        self.assertEqual(result['results']['C3']['answers']['transfer'], 'unknown')
        self.assertEqual(result['results']['C2']['answers']['transfer'], 'chest')
        self.assertEqual(result['results']['C2']['historical_recall'], 0)
        self.assertTrue(all(v['state_integrity'] for v in result['results'].values()))
        self.assertEqual(len(forks), 2)
        self.assertNotEqual(forks[0]['digest'], forks[1]['digest'])

    def test_corruption_and_normal_operation(self):
        cp = checkpoint(prepare(), 'l', 'id', None, EngineA.name)
        self.assertTrue(validate(cp, None))
        corrupt = copy.deepcopy(cp)
        corrupt['body']['state']['beliefs'][0]['evidence'] = ['o2']
        self.assertFalse(validate(corrupt, None))
        corrupt['digest'] = digest(corrupt['body'])
        self.assertFalse(validate(corrupt, None))
        self.assertEqual(EngineB().answer(cp['body']['state'], ['inside','key']), 'box')

    def test_revision_and_change_are_distinct(self):
        state = prepare()
        byid = {b['id']: b for b in state['beliefs']}
        self.assertEqual(byid['b-o3']['reason'], 'correction-of-o2')
        self.assertEqual(byid['b-o5']['reason'], 'world-changed-after-o4')
        self.assertEqual(byid['b-o2']['status'], 'superseded')
        self.assertEqual(byid['b-o4']['status'], 'superseded')
        self.assertEqual(EngineA().answer(state, ['colour','coin']), 'unknown')
        self.assertEqual(EngineB().answer(state, ['colour','coin']), 'unknown')
        self.assertLess(len(summary(state)['observations']), len(state['observations']))

if __name__ == '__main__': unittest.main()
