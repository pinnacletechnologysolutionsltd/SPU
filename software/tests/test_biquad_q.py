#!/usr/bin/env python3
"""BQ-0 fixtures for software/lib/biquad_q.py. Run: python3 software/tests/test_biquad_q.py"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from fractions import Fraction as Fr
from biquad_q import BQ

def direct(x, y):
    a, b, c, d = x; e, f, g, h = y
    return (a*e+3*b*f+5*c*g+15*d*h, a*f+b*e+5*(c*h+d*g), a*g+c*e+3*(b*h+d*f), a*h+d*e+b*g+c*f)

def s3(u, p): return (u[0]*p[0]+3*u[1]*p[1], u[0]*p[1]+u[1]*p[0])
def ad(u, v): return (u[0]+v[0], u[1]+v[1])
def sb(u, v): return (u[0]-v[0], u[1]-v[1])
def sc5(u): return (5*u[0], 5*u[1])

def nested(x, y):
    u, v, p, q = x[:2], x[2:], y[:2], y[2:]
    return ad(s3(u, p), sc5(s3(v, q))) + ad(s3(u, q), s3(v, p))

def kara(x, y):
    u, v, p, q = x[:2], x[2:], y[:2], y[2:]
    t0, t1, t2 = s3(u, p), s3(v, q), s3(ad(u, v), ad(p, q))
    return ad(t0, sc5(t1)) + sb(sb(t2, t0), t1)

def main():
    rnd = random.Random(1)
    r = lambda: tuple(rnd.randint(-2**31, 2**31) for _ in range(4))
    for _ in range(20000):
        x, y = r(), r()
        X, Y = BQ(*x), BQ(*y)
        P = X * Y
        assert P.c == tuple(map(Fr, direct(x, y))) == tuple(map(Fr, nested(x, y))) == tuple(map(Fr, kara(x, y)))
        assert P.norm() == X.norm() * Y.norm()
        assert (X + Y) - Y == X and X * Y == Y * X
        for k in range(4):
            assert P.conj(k) == X.conj(k) * Y.conj(k)
        assert BQ.from_golden(*X.to_golden()) == X and X.is_integral()
    # conjugation group: composition of flips is closed, involutive
    x = BQ(*r())
    assert x.conj(1).conj(1) == x and x.conj(1).conj(2) == x.conj(3)
    # norm examples
    assert BQ(1, 1, 1, 0).norm() == -11 and BQ(0, 0, 1, 0).norm() == 25
    assert BQ(1, 1, 0, 0).norm() == 4 and BQ(2, 1, 0, 0).norm() == 1 and BQ(0, 0, 0, 0).norm() == 0
    # golden basis: phi^2 = phi+1, (s3 phi)^2 = 3(phi+1), phi = (1+s5)/2, s5 = 2phi-1
    phi = BQ.from_golden(0, 0, 1, 0)
    assert phi * phi == phi + BQ(1) and phi == BQ(Fr(1, 2), 0, Fr(1, 2), 0)
    assert BQ(0, 0, 1, 0) == phi + phi - BQ(1) and phi.is_integral()
    assert BQ.from_golden(0, 0, 0, 1) == BQ(0, 1, 0, 0) * phi
    assert BQ(0, 0, 1, 0).to_golden() == (-1, 0, 2, 0)
    assert BQ(0, 0, 0, 1).to_golden() == (0, -1, 0, 2)
    assert not BQ(Fr(1, 2)).is_integral() and BQ(0, 0, 1, 0).is_integral()
    assert phi.norm() == 1
    # inverses: norm 0 only at 0; x*inv(x)==1; inverse of non-unit has non-integral coeffs
    one = BQ(1)
    for _ in range(2000):
        x = BQ(*r())
        if x.c == (0, 0, 0, 0): continue
        assert x.norm() != 0 and x * x.inv() == one
    for u in (phi, BQ(2, 1), BQ(2, 1) * phi):  # units: integral inverse
        assert abs(u.norm()) == 1 and u.inv().is_integral()
    assert not BQ(0, 0, 1, 0).inv().is_integral()  # N(s5)=25
    try:
        BQ().inv(); raise SystemExit("FAIL: zero inverse")
    except ZeroDivisionError:
        pass
    # nonzero random elements never have norm 0 (no zero divisors in char 0)
    assert all(BQ(*r()).norm() != 0 for _ in range(5000))
    print("PASS test_biquad_q (20000 mul/conj/norm/roundtrip, 2000 inverses)")

if __name__ == "__main__":
    main()
