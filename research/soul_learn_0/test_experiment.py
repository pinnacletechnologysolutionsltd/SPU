import unittest
from evaluate import run
from learner import initial, observe, infer, serialize, load
from scenarios import TRAIN, COUNTER, observed

class Tests(unittest.TestCase):
    def test_registered_measurements(self):
        r=run(); m=r['metrics']
        self.assertTrue(all(r['controls'].values()))
        self.assertEqual(m['training_recall'],m['training_total'])
        self.assertEqual(m['pre_heldout_correct'],m['pre_heldout_total'])
        self.assertFalse(m['counter_prediction_correct'])
        self.assertTrue(m['prior_hypothesis_rejected_by_counter'])
        self.assertTrue(m['revision_changed_hypothesis'])
        self.assertEqual(m['post_heldout_correct'],m['post_heldout_total'])
        self.assertTrue(m['restored_exactly'] and m['restored_post_equal'])
    def test_states_and_duplicate(self):
        s=initial(); self.assertEqual(infer(s,TRAIN[0])['status'],'unknown')
        for c in TRAIN: s=observe(s,observed(c))
        self.assertEqual(s['status'],'unresolved')
        with self.assertRaises(ValueError): observe(s,observed(TRAIN[0]))
        s=observe(s,observed(COUNTER))
        self.assertEqual(s['status'],'established')
        self.assertEqual(s['rejected']['linked'],COUNTER['id'])
        self.assertEqual(load(serialize(s)),s)
    def test_unseen_no_prediction_without_training(self):
        self.assertIsNone(infer(initial(),COUNTER)['answer'])

if __name__=='__main__':unittest.main()
