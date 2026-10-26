"""Exact sign and half-open balance comparisons; no floating arithmetic."""
from .budget import InvariantError, fits


def _count(counters, key, amount=1):
    if counters is not None:
        counters[key] += amount


def _workspace(value, counters):
    _count(counters, 'kernel_width_checks')
    if not fits(value, 280):
        raise InvariantError('comparator workspace bound violated')
    return value


def sign(a, b, counters=None):
    if type(a) is not int or type(b) is not int:
        raise InvariantError('sign input must be exact integers')
    if not fits(a, 139) or not fits(b, 139):
        raise InvariantError('sign square-kernel precondition violated')
    _count(counters, 'kernel_sign_calls')
    _count(counters, 'kernel_comparisons')
    if a == 0:
        _count(counters, 'kernel_comparisons', 2)
        return (b > 0) - (b < 0)
    _count(counters, 'kernel_comparisons')
    if b == 0:
        _count(counters, 'kernel_comparisons', 2)
        return (a > 0) - (a < 0)
    _count(counters, 'kernel_comparisons', 3)
    sa, sb = (1 if a > 0 else -1), (1 if b > 0 else -1)
    if sa == sb:
        return sa
    _count(counters, 'kernel_multiplications', 3)
    aa = _workspace(a * a, counters)
    bb = _workspace(b * b, counters)
    triple = _workspace(3 * bb, counters)
    _count(counters, 'kernel_comparisons')
    return sa if aa > triple else sb


def expression(a, b, upper=False, counters=None):
    if not fits(a, 136) or not fits(b, 136):
        raise InvariantError('balance mantissa exceeds signed136')
    alpha = sign(a, b, counters)
    beta = sign(a, -b, counters)
    _count(counters, 'kernel_negations', 2)
    _count(counters, 'kernel_multiplications', 4)
    A, B, C, D = alpha*a, alpha*b, beta*a, -beta*b
    _count(counters, 'kernel_multiplications', 3)
    _count(counters, 'kernel_additions', 4)
    if upper:
        twice, triple = _workspace(2*C, counters), _workspace(3*D, counters)
        first = _workspace(twice + triple, counters)
        p = _workspace(A - first, counters)
        second = _workspace(2*D, counters)
        second = _workspace(second + C, counters)
        q = _workspace(B - second, counters)
    else:
        twice, triple = _workspace(2*A, counters), _workspace(3*B, counters)
        first = _workspace(twice + triple, counters)
        p = _workspace(first - C, counters)
        second = _workspace(2*B, counters)
        second = _workspace(second + A, counters)
        q = _workspace(second - D, counters)
    return p, q


def boundary(a, b, upper=False, counters=None):
    return sign(*expression(a, b, upper, counters), counters=counters)


def probe(a, b):
    lower, upper = expression(a, b), expression(a, b, True)
    lo, hi = sign(*lower), sign(*upper)
    return dict(embedding_sign=sign(a, b), conjugate_embedding_sign=sign(a, -b),
                lower_expression=list(lower), upper_expression=list(upper),
                lower_sign=lo, upper_sign=hi, balanced=lo >= 0 and hi < 0)
