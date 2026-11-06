import copy
import unittest
from evaluate import controls, run_scenario
from memory import Memory, archive_digest, valid_archive
from scenarios import SCENARIOS, fact

class Tests(unittest.TestCase):
    def test_controls(self): self.assertTrue(all(controls().values()), controls())
    def test_equal_streams_and_storage(self):
        for s in SCENARIOS:
            runs=[run_scenario(s,p) for p in ('M0','M1','M2')]
            self.assertEqual([q['query'] for q in runs[0]['queries']], [q['query'] for q in runs[1]['queries']])
            self.assertEqual([q['query'] for q in runs[1]['queries']], [q['query'] for q in runs[2]['queries']])
            self.assertEqual(runs[1]['persistent_archive_records'],len(s['records']))
            self.assertEqual(runs[2]['persistent_archive_records'],len(s['records']))
            self.assertEqual(runs[0]['persistent_archive_records'],0)
    def test_conflict_is_unknown(self):
        for policy in ('M0','M1','M2'):
            m=Memory(policy); m.ingest(fact('a','x','yes')); m.ingest(fact('b','x','no'))
            self.assertEqual(m.answer({'key':'x','kind':'current','epoch':None})[0],'unknown')
    def test_valid_and_corrupt_archive(self):
        records=SCENARIOS[5]['records']; d=archive_digest(records)
        self.assertTrue(valid_archive(records,d))
        bad=copy.deepcopy(records); bad[2]['target']='d1'
        self.assertFalse(valid_archive(bad,d))
        self.assertFalse(valid_archive(bad,archive_digest(bad)))
    def test_summary_and_history_conditions(self):
        stable=SCENARIOS[0]
        self.assertTrue(all(run_scenario(stable,p)['queries'][0]['correct'] for p in ('M0','M1','M2')))
        for s in (SCENARIOS[1],SCENARIOS[5]):
            self.assertEqual(run_scenario(s,'M0')['queries'][0]['answer'],'unknown')
            self.assertTrue(run_scenario(s,'M2')['queries'][0]['correct'])

if __name__=='__main__': unittest.main()
