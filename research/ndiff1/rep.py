"""NDIFF-1 representations and their *maintenance* costs under exact similarity/reparametrisation steps.

Frozen cost model (extends research/ndiff0/field.py; all counts at surd level, converted as there):
  inv  (1/x in Q(sqrt3)) = 2 surd mul + 1 surd add   sqrt (sqrt_s3 root extraction) = same as inv   [placeholders]
  free: re-indexing (t->t^2 spreads coefficients), negation, copies.
Representations: POLY (X,Y + maintained dX,dY), PRIM (POLY + generators a,b, h=1), GEN (POLY + a,b,h),
GEN_REBUILD (GEN but X,Y re-integrated from the hodograph every step instead of transformed).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ndiff0"))
from types import SimpleNamespace as NS
from field import *
import field
from curve import PH
from closure import sinv, sub_t2


def inv(x):
    field.OPS["mul"] += 2; field.OPS["add"] += 1
    return sinv(x)


def root(x):
    field.OPS["mul"] += 2; field.OPS["add"] += 1
    return sqrt_s3(x)


def cmul(k, p):  # constant * polynomial
    return tuple(k * c for c in p)


def lin(k1, p, k2, q, sub=False):  # k1*p +/- k2*q coefficientwise, equal lengths
    return tuple((k1 * x - k2 * y) if sub else (k1 * x + k2 * y) for x, y in zip(p, q))


def finish(r, a=None, b=None, h=None):
    r.dX, r.dY = pder(r.X), pder(r.Y)
    r.a, r.b, r.h = a, b, h
    return r


def from_ph(c, kind):
    return finish(NS(kind=kind, X=c.X, Y=c.Y), c.a, c.b, c.h if kind != "POLY" else None)


class Unrepresentable(Exception):
    pass


def step(r, op, arg=None):
    kind = r.kind
    X, Y, a, b, h = r.X, r.Y, r.a, r.b, r.h
    if kind == "GEN_REBUILD":  # position is re-integrated below; only the constant of integration is transformed
        X, Y = X[:1], Y[:1]
    if op == "rot":
        cs, sn = arg
        nX, nY = lin(cs, X, sn, Y, True), lin(sn, X, cs, Y)
        if kind == "POLY":
            return finish(NS(kind=kind, X=nX, Y=nY))
        if kind == "PRIM":
            cphi = ZERO if cs == S3(-1) else root(S3((1 + cs.p) / 2, cs.q / 2))
            if cphi is None:
                raise Unrepresentable("rotation half-angle outside Q(sqrt3)")
            sphi = ONE if cs == S3(-1) else sn * inv(cphi + cphi)
            return finish(NS(kind=kind, X=nX, Y=nY), lin(cphi, a, sphi, b, True), lin(sphi, a, cphi, b), h)
        if cs == S3(-1):
            na, nb, nh = tuple(-x for x in b), a, h
        else:
            t = sn * inv(ONE + cs)
            rr = inv(ONE + t * t)
            na, nb, nh = lin(ONE, a, t, b, True), lin(ONE, b, t, a), cmul(rr, h)
    elif op == "scale":
        nX, nY = cmul(arg, X), cmul(arg, Y)
        if kind == "POLY":
            return finish(NS(kind=kind, X=nX, Y=nY))
        if kind == "PRIM":
            rt = root(arg)
            if rt is None:
                raise Unrepresentable("scale factor not a square in Q(sqrt3)")
            return finish(NS(kind=kind, X=nX, Y=nY), cmul(rt, a), cmul(rt, b), h)
        na, nb, nh = a, b, cmul(arg, h)
    elif op == "t2":
        nX, nY = sub_t2(X), sub_t2(Y)
        if kind == "POLY":
            return finish(NS(kind=kind, X=nX, Y=nY))
        if kind == "PRIM":
            raise Unrepresentable("h=2t is not a square")
        na, nb = sub_t2(a), sub_t2(b)
        nh = (ZERO,) + tuple(c.scale(2) for c in sub_t2(h))
    r2 = NS(kind=kind, X=nX, Y=nY)
    if kind == "GEN_REBUILD":
        g = PH(na, nb, nh, nX[0], nY[0])  # integration charged
        r2.X, r2.Y = g.X, g.Y
    return finish(r2, na, nb, nh)
