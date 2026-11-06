import unittest
from itertools import product
from research.qaf_expr_graph_0.model import eval_graph, normal
from research.qaf_expr_graph_1.model import (ORIGINAL, IDENTITY, CONJ_MUL, NORM,
    compare, execute, HIGH, OVERFLOW)
from software.experiments.surd_cpu_stream import Stream

class ObserverTests(unittest.TestCase):
    def test_small_cancellation_and_full_trace(self):
        for x in product(range(-2,3),repeat=2):
            c=compare(ORIGINAL,IDENTITY,x)
            self.assertTrue(c['mathematical'])
            self.assertTrue(c['final_value_status'])
            self.assertFalse(c['strict_trace'])
            self.assertEqual([e['write'][0] for e in c['left']['events']],['r0','r0'])
            self.assertEqual(len(c['right']['events']),0)
            self.assertEqual(tuple(int(v) for v in eval_graph(ORIGINAL.root,{'x':x,'y':(0,0)})),c['left']['result'])

    def test_overflow_refusal_preserves_destination(self):
        c=compare(ORIGINAL,IDENTITY,(HIGH,0))
        self.assertTrue(c['mathematical'])
        self.assertFalse(c['final_value_status'])
        self.assertFalse(c['strict_trace'])
        e=c['left']['events'][0]
        self.assertEqual((e['exact'],e['bits'],e['status'],e['write'],e['retire']),((2*HIGH,HIGH),(65,64),2,None,True))
        self.assertEqual(c['left']['result'],(HIGH,0))

    def test_smuls_against_existing_reference(self):
        for x in list(product(range(-2,3),repeat=2))+[(HIGH,0)]:
            s=Stream(); s.load(0,(*x,1)); s.load(1,(2,1,1)); s.load(2,(2,-1,1))
            trace=execute(ORIGINAL,x)
            for e, reg in zip(trace['events'],('S1','S2')):
                s.command('SMUL',['S0','S0',reg])
                row=s.lines[-1].split()
                self.assertEqual((e['status'],bool(e['write'])),(int(row[2]),bool(int(row[3]))))
                self.assertEqual((*e['registers']['r0'],1),s.bank[0])

    def test_norm_conjugation_observer(self):
        for x in product(range(-2,3),repeat=2):
            c=compare(CONJ_MUL,NORM,x)
            self.assertTrue(c['mathematical'])
            self.assertTrue(c['final_value_status'])
            self.assertFalse(c['strict_trace'])
            self.assertEqual([e['op'] for e in c['left']['events']],['CONJ','MUL'])
            self.assertEqual([e['op'] for e in c['right']['events']],['NORM'])
            self.assertEqual(c['left']['result'][1],0)

    def test_nonzero_status_and_negative_controls(self):
        c=compare(ORIGINAL,IDENTITY,(1,0),initial_status=OVERFLOW)
        self.assertTrue(c['mathematical']); self.assertFalse(c['final_value_status'])
        c=compare(ORIGINAL,ORIGINAL,(1,2))
        self.assertTrue(c['strict_trace'])
        c=compare(ORIGINAL,NORM,(1,0))
        self.assertFalse(c['mathematical'])  # coincident concrete result is not identity
        with self.assertRaises(ValueError): execute(ORIGINAL,(HIGH+1,0))

if __name__=='__main__': unittest.main()
