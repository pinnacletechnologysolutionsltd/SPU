"""Preparation tests ONLY. No registered curves, tape, outputs or derivation."""
import unittest
from fractions import Fraction as F
from unittest.mock import patch
from copy import deepcopy
from w31_arithmetic import Q,Trace,Refusal,Invalid
from w31_poly import Program
from w31_prepare import prepare,SEQUENTIAL,CELL_B
from w31_routes import route,preparation,state_hash


class Synthetic(unittest.TestCase):
    def primitive(self):
        t=Trace()
        return t,Program(t,'synthetic.P.test')

    def test_arithmetic_and_classification(self):
        t,p=self.primitive()
        self.assertEqual(p.op('mul',Q(2**30,3),Q(5,2**10)),Q(5242880,3))
        self.assertEqual(t.counts['W_bits'],115)
        self.assertEqual(t.counts['G_bits'],33)
        self.assertEqual(t.counts['G_calls'],1)
        p.op('shift2',Q(3,2)); p.op('mul',Q(3),Q(1,2))
        self.assertEqual((t.counts['M'],t.counts['S']),(2,1))
        self.assertEqual(p.op('div',Q(15,7),Q(3,5)),Q(25,7))
        self.assertEqual(p.sub(Q(2,7),Q(3,5)),Q(-11,35))

    def test_width_order(self):
        for fn,args,event in [('mul',(Q(2**30),Q(2)),'.e1'),
                              ('mul',(Q(1,2**30),Q(1,2)),'.e2'),
                              ('mul',(Q(2**62),Q(4)),'.r1'),
                              ('compare',(Q(2**62),Q(1,4)),'.r1')]:
            t,p=self.primitive()
            with self.assertRaises(Refusal) as cm:
                p.op(fn,*args)
            self.assertEqual(cm.exception.event,'synthetic.P.test.1'+event)
        t,p=self.primitive()
        with self.assertRaises(Invalid) as cm:
            p.op('div',Q(2**100),Q(0))
        self.assertEqual(cm.exception.event,'synthetic.P.test.1')
        self.assertEqual(t.counts['G_calls'],0)
        self.assertEqual(p.op('mul',Q(2**31-1),Q(1)),Q(2**31-1))
        self.assertEqual(p.op('mul',Q(0),Q(2**62)),Q(0))

    def test_polynomial_values_and_counts(self):
        a=[Q(3),Q(-2),Q(5)]
        for method,counts in [('horner',(2,2)),('decas',(3,6)),('tshift',(3,3))]:
            t,p=self.primitive()
            coefficients=p.bern(a) if method=='decas' else a
            t.counts={k:0 for k in t.counts}; t.events=[]; p.index=0
            result=getattr(p,method)(coefficients,Q(1,3))
            if method=='tshift': result=result[0]
            self.assertEqual(result,Q(26,9))
            self.assertEqual((t.counts['M'],t.counts['A']),counts)
            self.assertEqual([x[0] for x in t.events],
                             [f'synthetic.P.test.{i}' for i in range(1,sum(counts)+1)])
        t,p=self.primitive(); fd=p.fdinit(a,Q(1,8))
        self.assertEqual((t.counts['M'],t.counts['A']),(6,11))
        self.assertEqual(fd[0],a[0])
        self.assertEqual(p.fdstep(fd)[0],Q(181,64))
        self.assertEqual(p.padd([Q(2)],[Q(3),Q(4)],True),[Q(-1),Q(-4)])
        self.assertEqual(p.pder([Q(5)]),[Q(0)])
        self.assertEqual(p.pcomp([Q(2),Q(3)],[Q(1),Q(2)]),[Q(5),Q(6)])

    def test_preparation_and_all_sequential_arms(self):
        # Synthetic straight line r(t)=(3t,4t), speed 5; not a registered curve.
        for arm in SEQUENTIAL:
            state,p=preparation(arm,[Q(2)],[Q(1)])
            self.assertEqual(p['status'],'OK',arm)
            for tape in ('S1','S2','S3'):
                result=route(arm,state,tape)
                self.assertEqual((result['issued'],result['unissued']),(17,0))
                for k,row in enumerate(result['rows']):
                    self.assertEqual(row['status'],'OK',(arm,tape,row))
                    self.assertEqual(row['values']['x'],[3*k//16,1] if 3*k%16==0 else [Q(3*k,16).n,Q(3*k,16).d])
                    self.assertEqual(row['values']['y'],[Q(k,4).n,Q(k,4).d])
                    if tape!='S1': self.assertEqual(row['values']['Tx'],[3,5])
                    if tape=='S3': self.assertEqual(row['values']['increment_to_next'],[5,16] if k<16 else None)

    def test_nonlinear_evolution(self):
        for arm in SEQUENTIAL:
            state,p=preparation(arm,[Q(2),Q(1)],[Q(1)])
            self.assertEqual(p['status'],'OK')
            for tape in ('S1','S2','S3'):
                rows=route(arm,state,tape)['rows']
                for k,row in enumerate(rows):
                    self.assertEqual(row['status'],'OK',(arm,tape,k,row))
                    t=F(k,16)
                    expected={'x':3*t+2*t*t+t**3/3,'y':4*t+t*t}
                    if tape!='S1':
                        expected.update(dx=3+4*t+t*t,dy=4+2*t,sg=5+4*t+t*t)
                    if tape=='S3': expected.update(S=5*t+2*t*t+t**3/3,Nk=F(-2))
                    for name,value in expected.items():
                        self.assertEqual(row['values'][name],[value.numerator,value.denominator],(arm,tape,k,name))

    def test_cell_b_preparation_and_queries(self):
        # All Cell B programs specialize the registered base generator (1,t).
        # A synthetic retiming 3t/5 and only two synthetic query points.
        for arm in CELL_B:
            state,p=preparation(arm,[Q(1)],[Q(0),Q(1)],[Q(0),Q(3,5)])
            self.assertEqual(p['status'],'OK')
            result=route(arm,state,'CellB',[Q(0),Q(1,4)])
            self.assertEqual([r['status'] for r in result['rows']],['OK','OK'])
            row=result['rows'][1]['values']
            f=F(3,20)
            self.assertEqual(row['x'],[Q((f-f**3/3).numerator,(f-f**3/3).denominator).n,
                                       Q((f-f**3/3).numerator,(f-f**3/3).denominator).d])
            self.assertEqual(row['dy'],[9,50])
            self.assertEqual(result['rows'][1]['ledger']['D'],0)

    def test_scheduling_and_rollback(self):
        state={'sentinel':[Q(7)]}
        def fail(trace,arm,tape,working,k):
            working['sentinel']=[Q(99)]
            trace.add(Q(1),Q(1),'probe.Q.1')
            raise Refusal(f'{arm}.Q.q{k:02d}.a1.1.e1')
        for arm,tape,issued in [('FD','S1',1),('Horner','S1',17),('Horner','S3',1)]:
            with patch('w31_routes.sequential',fail):
                result=route(arm,state,tape)
            self.assertEqual(result['issued'],issued)
            self.assertEqual(result['unissued'],17-issued)
            for row in result['rows']:
                if 'status' in row: self.assertEqual(row['state_before'],row['state_after'])
                else:
                    self.assertNotIn('event_id',row); self.assertNotIn('ledger',row)
                    self.assertNotIn('status',row)
        self.assertEqual(state,{'sentinel':[Q(7)]})

    def test_preparation_refusal_import(self):
        state,row=preparation('Horner',[Q(2**31)],[Q(1)])
        self.assertEqual(state,{})
        self.assertEqual(row['preparation_outcome'],'PREPARATION_REFUSED')
        self.assertEqual(row['event_id'],'Horner.P.import.U.0')


if __name__=='__main__':
    unittest.main()
