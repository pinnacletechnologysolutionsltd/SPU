"""Literal output, primitive-count, wire and ledger controls; not qualification."""
from pathlib import Path
import sys
import copy
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from software.research.lattice_drycount.adapter import run
from software.research.lattice_drycount.meter import Meter
from software.research.lattice_drycount.exact import gcd, normalize
from software.research.lattice_drycount.ledger import replay
from software.research.lattice_drycount.wire import encode, decode, measure
from software.research.lattice_symmetry.reference import reflect
from software.research.lattice_symmetry.fixtures import simple_roots
from fractions import Fraction


class DryCount(unittest.TestCase):
    def test_all_five_literal_outputs_and_counts(self):
        case = dict(system='D4', scaled_input=[2,-2,0,0], generator_word=[0,1])
        for arm in ('coordinates','generator_word','matrix','surd','signed'):
            r, events = run(case, arm, True)
            self.assertEqual(r['output'], (-2,0,2,0))
            self.assertEqual(sum(r['counts'].values()), r['work'])
            self.assertEqual(replay(events,r)['status'],'REPLAY_PASS')
            if arm == 'coordinates':
                self.assertEqual(r['stages']['construction']['multiply'], 16)
            if arm == 'matrix':
                self.assertEqual(r['stages']['construction']['multiply'], 640)
            if arm == 'surd':
                self.assertEqual(r['stages']['evaluation']['multiply'], 176)

    def test_e8_against_independent_reference(self):
        x=(2,2,0,0,0,0,0,0)
        case=dict(system='E8',scaled_input=list(x),generator_word=[0,1])
        physical=tuple(Fraction(v,2) for v in x)
        for i in (0,1):
            physical=reflect(physical, tuple(Fraction(v,2) for v in simple_roots('E8')[i]))
        expected=tuple(int(v*2) for v in physical)
        for arm in ('coordinates','generator_word','matrix','surd'):
            r,_=run(case,arm)
            self.assertEqual(r['output'],expected)
        self.assertEqual(expected,(-2,-2,0,0,0,0,0,0))

    def test_scalar_and_storage_replay_and_mutants(self):
        case=dict(system='D4',scaled_input=[2,-2,0,0],generator_word=[0,1])
        r,events=run(case,'coordinates',True)
        self.assertEqual(replay(events,r)['status'],'REPLAY_PASS')
        bad=copy.deepcopy(r); bad['work']-=1
        with self.assertRaisesRegex(AssertionError,'LEDGER_WORK'):
            replay(events,bad)
        bad=copy.deepcopy(r); bad['simultaneous_live_bits']-=1
        with self.assertRaisesRegex(AssertionError,'LEDGER_PEAK'):
            replay(events,bad)
        bad=list(events)
        i=next(i for i,e in enumerate(bad) if e[0]=='scalar')
        e=bad[i]; bad[i]=(*e[:-1],e[-1]+1)
        with self.assertRaisesRegex(AssertionError,'LEDGER_SCALAR'):
            replay(bad,r)
        bad=list(events)
        del bad[next(i for i,e in enumerate(bad) if e[0]=='charge' and e[2]=='loop_condition')]
        with self.assertRaisesRegex(AssertionError,'LEDGER_COUNTS'):
            replay(bad,r)

    def test_euclid_literal_and_raw_growth(self):
        m=Meter(True)
        self.assertEqual(gcd(m,1071,462),21)
        self.assertEqual(m.counts['remainder'],3)
        replay(m.events,m.report())
        self.assertEqual(normalize(Meter(),(0,4)),(0,1))
        m=Meter()
        self.assertEqual(m.op('multiply',127,2),254)
        self.assertEqual(m.raw_bits,9)

    def test_wire_literals_and_negative_controls(self):
        packet=encode('word','E8',[0,1,7])
        self.assertEqual(packet,bytes((1,4,8,0,3,0,0,0,200,1)))
        self.assertEqual(decode(packet),(0,1,7))
        m=Meter(True)
        self.assertEqual(measure(m,'word','E8',[0,1,7],'wire'),packet)
        replay(m.events,m.report())
        for data,reason in ((bytes((2,))+packet[1:],'WIRE_TAG'),
                            (packet[:3]+bytes((1,))+packet[4:],'WIRE_TAG'),
                            (packet[:-1]+bytes((129,)),'WIRE_PADDING'),
                            (packet[:-1],'WIRE_LENGTH')):
            with self.assertRaisesRegex(ValueError,reason):
                decode(data)
        with self.assertRaisesRegex(ValueError,'WIRE_CANONICAL'):
            decode(encode('rational','D4',[(2,4)]*4))
        with self.assertRaisesRegex(ValueError,'WIRE_DENOMINATOR'):
            decode(encode('rational','D4',[(1,0)]*4))

    def test_inverse_and_input_preservation(self):
        case=dict(system='D4',scaled_input=[2,-2,0,0],generator_word=[0,1,1,0])
        saved=copy.deepcopy(case)
        for arm in ('coordinates','generator_word','matrix','surd','signed'):
            r,_=run(case,arm)
            self.assertEqual(r['output'],tuple(case['scaled_input']))
        self.assertEqual(case,saved)

    def test_width_refusal_and_observation_only_limits(self):
        m=Meter()
        with self.assertRaisesRegex(ValueError,'TEMPORARY_RANGE'):
            m.op('multiply',1 << 200,1 << 100)
        case=dict(system='D4',scaled_input=[0,0,-(1 << 63),0],generator_word=[3])
        saved=copy.deepcopy(case)
        with self.assertRaisesRegex(ValueError,'SCALAR_RANGE'):
            run(case,'signed')
        self.assertEqual(case,saved)
        m=Meter()
        m.charge('move',2000001)
        m.allocate('diagnostic',1048577)
        self.assertEqual(m.profile.max_operations,2000000)
        self.assertEqual(m.profile.max_live_bits,1048576)
        self.assertGreater(m.report()['work'],m.profile.max_operations)
        self.assertGreater(m.report()['simultaneous_live_bits'],m.profile.max_live_bits)


if __name__=='__main__':
    unittest.main()
