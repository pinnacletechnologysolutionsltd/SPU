#!/usr/bin/env python3
"""Exact Q(sqrt(3)) reference vectors for W=32 and W=64."""
from fractions import Fraction
from math import gcd
import random


def fits(value, width, signed=True):
    if signed:
        return -(1 << (width - 1)) <= value < (1 << (width - 1))
    return 0 < value < (1 << width)


def evaluate(width, operands, destination):
    a, b, d, c, e, f = operands
    assert all(fits(x, width) for x in (a, b, c, e))
    assert all(0 <= x < (1 << width) for x in (d, f))
    assert fits(destination[0], width) and fits(destination[1], width)
    assert fits(destination[2], width, False)
    if d == 0 or f == 0:
        return dict(raw=None, reduced=None, request_normalization=False,
                    invalid=True, overflow=False, destination=list(destination))
    raw = (a*c + 3*b*e, a*e + b*c, d*f)
    assert fits(raw[0], 2*width+2)
    assert fits(raw[1], 2*width+1)
    assert fits(raw[2], 2*width, False)
    common = gcd(gcd(abs(raw[0]), abs(raw[1])), raw[2])
    reduced = tuple(x // common for x in raw)
    raw_fit = (fits(raw[0], width) and fits(raw[1], width)
               and fits(raw[2], width, False))
    reduced_fit = (fits(reduced[0], width) and fits(reduced[1], width)
                   and fits(reduced[2], width, False))
    committed = raw if raw_fit else reduced if reduced_fit else destination
    return dict(raw=list(raw), reduced=list(reduced),
                request_normalization=not raw_fit, invalid=False,
                overflow=not raw_fit and not reduced_fit,
                destination=list(committed))


def vectors(width, random_count=256):
    m, u = 1 << (width-1), (1 << width)-1
    dest = (17, -19, 23)
    cases = [
        ('positive_identity', (1,0,1,1,0,1)),
        ('zero_noncanonical_raw_fit', (0,0,2,7,-3,3)),
        ('zero_denominator_a', (1,2,0,3,4,1)),
        ('zero_denominator_b', (1,2,1,3,4,0)),
        ('both_denominators_zero', (0,0,0,0,0,0)),
        ('min_identity', (-m,-m,1,1,0,1)),
        ('max_identity', (m-1,m-1,1,1,0,1)),
        ('min_negation_overflow', (-m,0,1,-1,0,1)),
        ('real_requires_2w_plus_2', (-m,-m,1,-m,-m,1)),
        ('radical_requires_2w_plus_1', (-m,-m,1,-m,-m,1)),
        ('mixed_sign_cancellation', (-m,m-1,1,m-1,-m,1)),
        ('unsigned_denominator_max_fit', (1,0,u,1,0,1)),
        ('unsigned_denominator_overflow_coprime', (1,0,u,1,0,2)),
        ('denominator_rescue', (m//2,0,m,2,0,2)),
        ('zero_overflow_canonical_rescue', (0,0,u,1,0,u)),
        ('all_extrema_rescue', (-m,-m,m,-m,-m,m)),
        ('coefficient_plus_denominator_rescue', (m-1,0,m-1,2,0,2)),
    ]
    edges = (-m,-m+1,-2,-1,0,1,2,m-2,m-1)
    for x in edges:
        for y in (-1,1,2):
            cases.append((f'real_edge_{x}_{y}',(x,0,1,y,0,1)))
            cases.append((f'radical_edge_{x}_{y}',(0,x,1,y,0,1)))
    rng = random.Random(0x53555244 + width)
    for n in range(random_count):
        coeff = [rng.randint(-m,m-1) for _ in range(4)]
        d, f = rng.randint(1,u), rng.randint(1,u)
        cases.append((f'random_{n:04d}',(coeff[0],coeff[1],d,coeff[2],coeff[3],f)))
    for name, values in cases:
        yield dict(name=name,width=width,operands=list(values),
                   initial_destination=list(dest),
                   expected=evaluate(width,values,dest))


def self_test(rows):
    for row in rows:
        a,b,d,c,e,f=row['operands']; ex=row['expected']
        if not d or not f:
            assert ex['invalid'] and not ex['request_normalization']
            assert ex['destination']==row['initial_destination']
            continue
        real=Fraction(a,d)*Fraction(c,f)+3*Fraction(b,d)*Fraction(e,f)
        radical=Fraction(a,d)*Fraction(e,f)+Fraction(b,d)*Fraction(c,f)
        for tup in (ex['raw'],ex['reduced']):
            assert Fraction(tup[0],tup[2])==real
            assert Fraction(tup[1],tup[2])==radical
        assert gcd(gcd(abs(ex['reduced'][0]),abs(ex['reduced'][1])),ex['reduced'][2])==1
        if ex['overflow']:
            assert ex['destination']==row['initial_destination']
        else:
            out=ex['destination']
            assert Fraction(out[0],out[2])==real
            assert Fraction(out[1],out[2])==radical
    for width in (32,64):
        by_name={r['name']:r for r in rows if r['width']==width}
        real=by_name['real_requires_2w_plus_2']['expected']['raw'][0]
        radical=by_name['radical_requires_2w_plus_1']['expected']['raw'][1]
        assert real==1<<(2*width) and not fits(real,2*width+1)
        assert radical==1<<(2*width-1) and not fits(radical,2*width)
        assert by_name['denominator_rescue']['expected']['request_normalization']
        assert not by_name['denominator_rescue']['expected']['overflow']
        assert by_name['zero_overflow_canonical_rescue']['expected']['destination']==[0,0,1]
