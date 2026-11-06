import unittest
from evaluate import run
from scenarios import fixtures
from checker import check

class Tests(unittest.TestCase):
    def test_all_registered_cases(self):
        r=run(); self.assertTrue(all(x['pass'] for x in r['cases']),[x['name'] for x in r['cases'] if not x['pass']])
    def test_precedence_invalid_before_missing(self):
        f=next(x for x in fixtures() if x['name']=='missing_record');f['trusted_anchor']='bad'
        r=check(f['claim'],f['records'],f['language'],f['rules'],f['trusted_manifest'],f['trusted_anchor'])
        self.assertEqual(r['verdict'],'INVALID_EVIDENCE')
    def test_prediction_is_not_accuracy(self):
        r=run();c=next(x for x in r['cases'] if x['name']=='prediction_derived_incorrect_empirically')
        self.assertEqual(c['result']['verdict'],'SUPPORTED');self.assertFalse(r['prediction_accuracy_control']['empirically_correct'])
    def test_uniqueness_not_from_subset(self):
        c=next(x for x in run()['cases'] if x['name']=='incomplete_false_unique')
        self.assertEqual(c['result']['verdict'],'UNKNOWN');self.assertNotIn('finding',c['result'])

if __name__=='__main__':unittest.main()
