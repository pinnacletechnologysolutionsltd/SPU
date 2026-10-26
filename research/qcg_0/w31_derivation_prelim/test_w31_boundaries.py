"""Synthetic subcheck precedence and nonzero-position scheduling boundaries."""
import unittest
from unittest.mock import patch
from w31_arithmetic import Q,Trace,Refusal
from w31_routes import route
from w31_poly import Program


class Boundaries(unittest.TestCase):
    def test_subchecks(self):
        cases=[('mul',(Q(1,2**62),Q(1,4)),'.r2'),
               ('add',(Q(2**62),Q(1,4)),'.r1'),
               ('add',(Q(1,4),Q(2**62)),'.r2'),
               ('add',(Q(2**62),Q(2**62)),'.r3'),
               ('add',(Q(1,2**40),Q(1,2**40)),'.r4'),
               ('div',(Q(2**62),Q(1,4)),'.r1'),
               ('div',(Q(1,4),Q(2**62)),'.r2'),
               ('div',(Q(2**30),Q(1,2)),'.e1'),
               ('div',(Q(1,2**30),Q(2)),'.e2'),
               ('compare',(Q(1,4),Q(2**62)),'.r2'),
               ('shift2',(Q(2**30),),'.e1'),
               ('shift2',(Q(1,2**32),),'.e2')]
        for method,args,sub in cases:
            with self.assertRaises(Refusal) as cm:
                Program(Trace(),'synthetic.Q.boundary').op(method,*args)
            self.assertEqual(cm.exception.event,'synthetic.Q.boundary.1'+sub)

    def test_failure_at_nonzero_position(self):
        def sample(trace,arm,tape,state,k):
            state['count']+=1
            if k==2: raise Refusal(f'{arm}.Q.q02.a1.1.e1')
            return {'x':Q(k)}
        with patch('w31_routes.sequential',sample):
            r=route('TS',{'count':0},'S2')
        self.assertEqual((r['issued'],r['unissued']),(3,14))
        self.assertEqual([x.get('status',x.get('scheduling_outcome')) for x in r['rows'][:4]],
                         ['OK','OK','REFUSED','NOT_ISSUED'])
        row=r['rows'][2]
        self.assertEqual(row['state_before'],row['state_after'])
        self.assertEqual(r['rows'][16]['request'],'q16')

    def test_nested_counter_and_fd_evolution_order(self):
        trace=Trace(); p=Program(trace,'synthetic.P.PCOMP')
        p.pcomp([Q(2),Q(3),Q(4)],[Q(1),Q(2)])
        self.assertEqual([e[0] for e in trace.events],
                         [f'synthetic.P.PCOMP.{i}' for i in range(1,len(trace.events)+1)])
        from w31_prepare import prepare
        from w31_sequential import evaluate
        state=prepare(Trace(),'PHFD',[Q(2),Q(1)],[Q(1)])
        evaluate(Trace(),'PHFD','S3',state,0)
        trace=Trace(); evaluate(trace,'PHFD','S3',state,1)
        events=[e[0] for e in trace.events]
        self.assertLess(events.index('PHFD.Q.q01.b16.1'),events.index('PHFD.Q.q01.b5.1'))


    def test_random_access_refusal_recovery_repeat(self):
        from w31_routes import preparation
        state,prep=preparation('C1',[Q(1)],[Q(0),Q(1)],[Q(0),Q(3,5)])
        self.assertEqual(prep['status'],'OK')
        r=route('C1',state,'CellB',[Q(2**30),Q(0),Q(2**30)])
        rows=r['rows']
        self.assertEqual([x['status'] for x in rows],['REFUSED','OK','REFUSED'])
        self.assertEqual(rows[0]['state_before'],rows[0]['state_after'])
        fresh=route('C1',state,'CellB',[Q(0)])['rows'][0]
        self.assertEqual(rows[1]['values'],fresh['values'])
        self.assertEqual(rows[1]['ledger'],fresh['ledger'])
        self.assertEqual(rows[0]['event_id'].replace('q00','q02'),rows[2]['event_id'])
        self.assertEqual(rows[0]['ledger'],rows[2]['ledger'])


if __name__=='__main__': unittest.main()
