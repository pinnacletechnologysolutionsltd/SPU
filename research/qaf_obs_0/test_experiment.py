import unittest
import copy
from fractions import Fraction
from itertools import product
from research.qaf_obs_0.experiment import pure_cancel,pure_identity,assessment,observe
from research.qaf_expr_graph_1.model import ORIGINAL,IDENTITY,CONJ_MUL,NORM,HIGH,execute

class ObserverLegalityTests(unittest.TestCase):
    def test_pure_exact_scope(self):
        for a,b in product(range(-4,5),repeat=2):
            self.assertEqual(pure_cancel((a,b)),pure_identity((a,b)))
        for x in [(Fraction(1,3),Fraction(-2,5)),(HIGH,0),(HIGH+1,-HIGH)]:
            self.assertEqual(pure_cancel(x),pure_identity(x))
    def test_small_observer_difference(self):
        r=assessment(ORIGINAL,IDENTITY,(3,-2))
        self.assertEqual((r['pure_rule'],r['final_fixture_match'],r['strict_fixture_match']),('PROVED_FOR_DEFINED_CONTEXT',True,False))
        self.assertEqual(len(r['original']['events']),2)
        self.assertEqual(len(r['candidate']['events']),0)
    def test_overflow_hides_refusal(self):
        r=assessment(ORIGINAL,IDENTITY,(HIGH,0))
        self.assertTrue(r['math_form_match']); self.assertFalse(r['final_fixture_match']); self.assertFalse(r['strict_fixture_match'])
        self.assertEqual(r['original']['status'],2); self.assertEqual(r['candidate']['status'],0)
        self.assertEqual(r['original']['result'],r['candidate']['result'])  # value-only hides refusal
    def test_status_and_norm(self):
        r=assessment(ORIGINAL,IDENTITY,(1,0),2)
        self.assertEqual(r['original']['result'],r['candidate']['result'])
        self.assertFalse(r['final_fixture_match']); self.assertFalse(r['strict_fixture_match'])
        r=assessment(CONJ_MUL,NORM,(1,2))
        self.assertTrue(r['math_form_match']); self.assertTrue(r['final_fixture_match']); self.assertFalse(r['strict_fixture_match'])
        self.assertEqual(r['pure_rule'],'UNKNOWN')
    def test_fail_closed(self):
        # Arbitrary coincident outputs cannot inherit the named rewrite proof.
        r=assessment(ORIGINAL,NORM,(1,0))
        self.assertEqual(r['original']['result'],r['candidate']['result'])
        self.assertFalse(r['math_form_match']); self.assertEqual(r['pure_rule'],'UNKNOWN')
        self.assertTrue(assessment(ORIGINAL,ORIGINAL,(1,0))['strict_fixture_match'])
        self.assertEqual(assessment(ORIGINAL,ORIGINAL,(1,0))['pure_rule'],'UNKNOWN')

    def test_mutated_event_and_status(self):
        original=execute(ORIGINAL,(3,-2))
        mutant=copy.deepcopy(original)
        mutant['events'][0]['retire']=False
        self.assertEqual(observe(original,'O2'),observe(mutant,'O2'))
        self.assertNotEqual(observe(original,'O3'),observe(mutant,'O3'))
        mutant=copy.deepcopy(original)
        mutant['status']=2
        self.assertNotEqual(observe(original,'O2'),observe(mutant,'O2'))
        mutant=copy.deepcopy(original)
        mutant['events'][0]['status']=2  # refusal occurrence, final status unchanged
        self.assertNotEqual(observe(original,'O2'),observe(mutant,'O2'))
        with self.assertRaises(ValueError): observe(original,'unknown')

if __name__=='__main__': unittest.main()
