"""Deliberately defective observation variants must fail the literal checker."""
from dataclasses import replace
from .bounded import execute
from .literals import ROWS, check
from .boundaries import observations, check as check_boundaries

NAMES = ('free_mismatch', 'charged_zero', 'free_guard', 'budget_extra',
         'truncated_product', 'exponent_only_overflow', 'wrong_norm',
         'wrong_conjugation', 'failure_commit', 'b07_mantissa', 'b07_expansion')


def run_defect(name):
    if name in ('free_guard', 'budget_extra', 'b07_mantissa', 'b07_expansion'):
        rows = observations()
        if name == 'free_guard':
            rows['B03'].update(attempted=1, admitted=1)
        elif name == 'budget_extra':
            rows['B02'].update(status='OK', admitted=100_001, evaluations=1)
        else:
            rows['B07']['status'] = ('MANTISSA_OVERFLOW' if name == 'b07_mantissa'
                                     else 'EXPANSION_OVERFLOW')
        check_boundaries(rows)
        return
    if name == 'wrong_conjugation':
        row = ('NCONJ','CONJ',(5,2,1000),None,None,'OK',(5,-2,-1000),2)
        result = execute('CONJ',row[2])
        check(row,replace(result,value=(5,2,-1000)))
        return
    ids = dict(free_mismatch='F05',charged_zero='F07',truncated_product='F14',
               exponent_only_overflow='F19',wrong_norm='F17',
               failure_commit='F11')
    row = next(row for row in ROWS if row[0] == ids[name])
    result = execute(row[1],row[2],row[3],increment=row[4])
    if name == 'free_mismatch':
        result = replace(result,attempted=0,admitted=0)
    elif name == 'charged_zero':
        result = replace(result,attempted=1,admitted=1)
    elif name == 'truncated_product':
        result = replace(result,status='OK',value=(0,0,0),committed=True)
    elif name == 'exponent_only_overflow':
        result = replace(result,status='EXPANSION_OVERFLOW',value=(17,-19,23),committed=False)
    elif name == 'wrong_norm':
        result = replace(result,value=1)
    else:
        result = replace(result,value=(1,0,0),committed=True)
    check(row,result)
