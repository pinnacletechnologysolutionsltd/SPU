import copy
import json
import unittest
from research.spu_bound_2.certificate import issue,verify,summarize,reference_trace,LIMIT

class CertificateTests(unittest.TestCase):
    def test_bounded_domains(self):
        c=summarize(((-2,2),(-2,2)),[1,-1])
        self.assertTrue(verify(json.loads(json.dumps(c))))
        self.assertEqual(c['steps'][-1]['bounds'],((-2,2),(-2,2)))
        self.assertEqual(c['steps'][-1]['interval'],((-38,38),(-22,22)))
        c=summarize(((-2,2),(-1,1)),[1,1,-1,1])
        self.assertEqual(c['steps'][-1]['bounds'],((-26,26),(-15,15)))
    def test_negative_controls(self):
        c=issue(((-2,2),(-2,2)),[1,-1])
        for key in ('bits','bounds','matrix','interval'):
            d=copy.deepcopy(c); d['steps'][0][key]=[[0,0],[0,0]]
            self.assertFalse(verify(d),key)
        d=copy.deepcopy(c); d['seq']=[1,0]; self.assertFalse(verify(d))
    def test_refusal_and_events(self):
        e=reference_trace(LIMIT,0,[1,-1]); self.assertEqual(len(e),1)
        self.assertEqual((e[0]['status'],e[0]['write'],e[0]['tuple']),(2,0,(LIMIT,0,1)))
        e=reference_trace(3,-2,[1,-1]); self.assertEqual(e[-1]['tuple'],(3,-2,1))
        self.assertEqual([(x['write'],x['retire']) for x in e],[(1,1),(1,1)])
    def test_no_gain(self):
        c=issue(((-2,2),(-2,2)),[1]); self.assertEqual(c['steps'][0]['bounds'],c['steps'][0]['interval'])

if __name__=='__main__': unittest.main()
