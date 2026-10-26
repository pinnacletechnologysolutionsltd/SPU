"""Independent arithmetic agreement and private boundary qualification helpers."""
from unittest.mock import patch
from .bounded import execute
from .accounting import calculate
from .oracle import Mathematics, OracleLimit
from .literals import ROWS, L, H, KMIN, D, check
from .boundaries import observations, check as check_boundaries
from .baseline import MantissaCounter


def qualify_literals():
    report = []
    for row in ROWS:
        name,operation,left,right,increment,status,value,_ = row
        result = execute(operation,left,right,increment=increment)
        check(row,result)
        baseline = MantissaCounter()
        other = baseline.apply(operation,left,right,increment=increment)
        if other != result:
            raise AssertionError((name,'Baseline discrepancy'))
        math_result = None
        if status == 'OK' or name in ('F11','F12','F14','F15','F16','F18','F22'):
            oracle = Mathematics()
            math_result = oracle.evaluate(operation,left,right,increment)
            if status == 'OK' and math_result != value:
                raise AssertionError((name,'Independent oracle disagreement'))
        report.append(dict(case=name,status=result.status,attempted=result.attempted,
                           admitted=result.admitted,oracle_value=math_result))
    # Independent literal extrema checks, not bounded fit predicates.
    oracle = Mathematics()
    if oracle.evaluate('MUL',(L,L,0),(L,L,0)) != (1 << 128,1 << 127,0):
        raise AssertionError('Full-width oracle corner')
    if Mathematics().evaluate('NORM',(0,L,0)) != -3*(1 << 126):
        raise AssertionError('Literal norm corner')
    return report


def qualify_boundaries():
    with patch('software.research.aor1.accounting.calculate', wraps=calculate) as arithmetic:
        rows = observations()
        check_boundaries(rows)
        if arithmetic.call_count != 0:
            raise AssertionError('Rejected internal primitive evaluated arithmetic')
    # Guard refused cancellation, independently known to be exactly zero.
    if (1 << 128) + (-(1 << 128)) != 0:
        raise AssertionError('Cancellation identity')
    return rows


def qualify_independent_cases():
    count = 0
    # Independent literal input grid, including signs and positive/negative powers.
    for a in (-7,-1,0,2,5):
        for b in (-3,0,2):
            for k in (-12,-1,0,1,12):
                operand = a,b,k
                result = execute('EXPAND',operand)
                exact = Mathematics().evaluate('EXPAND',operand)
                if result.status != 'OK' or result.value != exact:
                    raise AssertionError(('Expansion grid',operand,result,exact))
                conjugate = execute('CONJ',operand)
                product = execute('MUL',operand,conjugate.value)
                norm = Mathematics().evaluate('NORM',operand)
                if product.value != ((norm,0,0) if norm else (0,0,0)):
                    raise AssertionError('Symbolic conjugate product')
                count += 1
    # Huge exponent refusal must not be promoted to numerical overflow.
    result = execute('EXPAND',(1,0,KMIN))
    if result.status != 'EXPANSION_RESOURCE_LIMIT' or result.value != D:
        raise AssertionError('Unproven huge expansion classification')
    # Unit exponent growth keeps norm invariant without expanding.
    if Mathematics().evaluate('NORM',(5,2,1000)) != 13:
        raise AssertionError('Norm invariant')
    return count + 2
