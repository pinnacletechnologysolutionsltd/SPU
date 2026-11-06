import unittest
from evaluate import controls, trial, BUDGETS
from memory import empty, ingest, items, size, query, index_valid
from scenarios import SCENARIOS, fact
from support import check

class Tests(unittest.TestCase):
    def test_controls(self): self.assertTrue(all(controls().values()),controls())
    def test_budget_after_every_update(self):
        for scenario in SCENARIOS:
            for policy in ('M0','M1','M2'):
                for budget in BUDGETS.values():
                    result=trial(scenario,policy,budget)
                    self.assertEqual(result['status'],'OK')
                    for u in result['updates']:
                        self.assertLessEqual(u['occupancy'],budget)
                        self.assertEqual(size(u['state']),u['occupancy'])
                        self.assertTrue(index_valid(u['state']))
    def test_multiple_alternatives(self):
        state=empty('M0')
        for i in range(3): state,_=ingest(state,fact(str(i),'key',str(i),strength=i+1),815)
        self.assertEqual(len(items(state)),3)
    def test_checker_specifics(self):
        a=fact('a','A','B'); b=fact('b','B','C'); c=fact('c','A','X')
        self.assertEqual(check(('A','C',0),['a','b'],[a,b],('transitive',)),'SUPPORTED')
        self.assertEqual(check(('A','C',0),['a','c'],[a,b,c],('transitive',)),'UNSUPPORTED')
        self.assertEqual(check(('A','C',0),['a','missing'],[a,b],('transitive',)),'UNKNOWN')
    def test_no_future_oracle_in_query(self):
        state,_=ingest(empty('M1'),fact('a','key','value'),815)
        result=query(state,'key')
        self.assertEqual(result['answer'],'value')
        self.assertNotIn('expected',result)

if __name__=='__main__': unittest.main()
