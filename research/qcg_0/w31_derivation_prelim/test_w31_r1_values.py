"""Synthetic reference mapping and rejection; no registered evaluation."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from w31_arithmetic import Q
from w31_certified import check_route, load_reference
from w31_prepare import SEQUENTIAL
from w31_routes import preparation, route


def pair(value):
    q = F(value)
    return [q.numerator, q.denominator]


def synthetic_reference():
    # Independent straight-line fixture: r=(3t,4t), sigma=5, kappa=0.
    rows = [dict(t=pair(F(k,16)), S1=[pair(F(3*k,16)),pair(F(k,4))],
                 S2_add=[[3,1],[4,1],[5,1],[3,5],[4,5]], S3_kappa=[0,1],
                 S3_arc_increment_to_next=[5,16] if k<16 else None) for k in range(17)]
    return {'sequential':{'SYN':rows}, 'SYN':{'S':[[0,1],[5,1]]}}


class Values(unittest.TestCase):
    def test_all_synthetic_tapes_against_independent_rows(self):
        reference = synthetic_reference()
        for arm in SEQUENTIAL:
            state, p = preparation(arm,[Q(2)],[Q(1)])
            self.assertEqual(p['status'], 'OK')
            for tape in ('S1','S2','S3'):
                result = route(arm,state,tape)
                result['curve'] = 'SYN'
                check_route(result,reference)

    def test_mismatch_and_wrong_grid_rejected(self):
        state, _ = preparation('Horner',[Q(2)],[Q(1)])
        result = route('Horner',state,'S3')
        result['curve'] = 'SYN'
        reference = synthetic_reference()
        wrong = deepcopy(result)
        wrong['rows'][8]['values']['x'] = [999,1]
        with self.assertRaisesRegex(ValueError, 'certified mismatch: SYN/Horner/S3/q08/x'):
            check_route(wrong,reference)
        wrong = deepcopy(result)
        wrong['rows'][8]['parameter'] = [1,3]
        with self.assertRaisesRegex(ValueError, 'parameter'):
            check_route(wrong,reference)
        wrong_reference = deepcopy(reference)
        wrong_reference['sequential']['SYN'][8]['t'] = [1,3]
        wrong['rows'][8]['parameter'] = [1,3]
        with self.assertRaisesRegex(ValueError, 'grid'):
            check_route(wrong,wrong_reference)

    def test_cell_b_reference_mapping(self):
        state, p = preparation('C1',[Q(1)],[Q(0),Q(1)],[Q(0),Q(3,5)])
        self.assertEqual(p['status'],'OK')
        result = route('C1',state,'CellB',[Q(1,4)])
        result['curve'] = 'SYN'
        f, g = F(3,20), F(3,5)
        v = [f-f**3/3,f*f,g*(1-f*f),2*g*f,g*(1+f*f),g*(1+f*f),f+f**3/3]
        reference = {'cell_B':{'rows':[dict(t=[1,4],values=[pair(x) for x in v])]}}
        check_route(result,reference)
        result['rows'][0]['values']['dy'] = [0,1]
        with self.assertRaisesRegex(ValueError, '/dy'):
            check_route(result,reference)

    def test_missing_certified_reference_is_hold(self):
        with self.assertRaisesRegex(ValueError, 'HOLD: missing certified reference: /nonexistent/w31_reference.json'):
            load_reference('/nonexistent/w31_reference.json','0'*64)


if __name__ == '__main__': unittest.main()
