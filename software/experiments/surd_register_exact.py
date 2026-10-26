"""Unbounded exact coefficient algebra and width bounds for S0."""
from dataclasses import dataclass
from math import gcd


@dataclass(frozen=True)
class R:
    a: int
    b: int
    d: int


def sw(v):
    return (v.bit_length() if v >= 0 else (~v).bit_length()) + 1


def uw(v):
    return max(1, v.bit_length())


def valid(r, w):
    lim = 1 << (w - 1)
    return (type(r.a) is int and type(r.b) is int and type(r.d) is int
            and -lim <= r.a < lim and -lim <= r.b < lim
            and 1 <= r.d < (1 << w))


def normalize(r):
    g = gcd(gcd(abs(r.a), abs(r.b)), r.d)
    return R(0, 0, 1) if r.a == r.b == 0 else R(r.a//g, r.b//g, r.d//g)


def import_signed(a, b, d, w):
    if any(type(x) is not int for x in (a, b, d)) or d == 0:
        return None
    r = normalize(R(a, b, d if d > 0 else -d))
    if d < 0:
        r = R(-r.a, -r.b, r.d)
    return r if valid(r, w) else None


def widths(r):
    return {'a': sw(r.a), 'b': sw(r.b), 'd': uw(r.d)}


def raw(op, x, y=None):
    if op in ('ADD', 'SUB'):
        g = gcd(x.d, y.d); u = y.d//g; v = x.d//g
        s = 1 if op == 'ADD' else -1
        terms = (x.a*u, y.a*v, x.b*u, y.b*v, x.d*u)
        aa,bb=terms[0]+s*terms[1],terms[2]+s*terms[3]
        return R(aa,bb,terms[4]), {
            'gcd': g, 'u': u, 'v': v, 'a_left': terms[0], 'a_right': terms[1],
            'b_left': terms[2], 'b_right': terms[3], 'den_product': terms[4],
            'acc_a':aa,'acc_b':bb}
    if op == 'MUL':
        p = (x.a*y.a, x.b*y.b, x.a*y.b, x.b*y.a, x.d*y.d)
        aa,bb=p[0]+3*p[1],p[2]+p[3]
        return R(aa,bb,p[4]), {
            'aa': p[0], 'bb': p[1], 'three_bb': 3*p[1],
            'ab': p[2], 'ba': p[3], 'dd': p[4], 'acc_a':aa,'acc_b':bb}
    if op == 'NEG': return R(-x.a, -x.b, x.d), {'neg_a': -x.a, 'neg_b': -x.b}
    if op == 'CONJ': return R(x.a, -x.b, x.d), {'conj_b': -x.b}
    if op == 'NORM':
        g=gcd(gcd(abs(x.a),abs(x.b)),x.d); result=normalize(x)
        return result,{'gcd':g,'quot_a':result.a,'quot_b':result.b,'quot_d':result.d}
    if op == 'EQ':
        p = (x.a*y.d, y.a*x.d, x.b*y.d, y.b*x.d)
        return (p[0] == p[1] and p[2] == p[3]), dict(zip(('a1d2','a2d1','b1d2','b2d1'), p))
    raise ValueError(op)


def intermediate_limits(op, w):
    if op in ('ADD', 'SUB'): return {'product': 2*w, 'den_product': 2*w, 'accumulator': 2*w+1}
    if op == 'MUL': return {'product': 2*w+1, 'accumulator': 2*w+2, 'den_product': 2*w}
    if op in ('NEG', 'CONJ'): return {'neg': w+1}
    if op == 'EQ': return {'cross_product': 2*w}
    if op == 'NORM': return {'magnitude': w+1, 'quotient': w}
    raise ValueError(op)
