"""Oracle O1 (contract §9 oracles): Fraction polynomial route. Independent of the ledgered arms: stdlib only, no shared helpers."""
from fractions import Fraction as F


def fr(pairs):
    return [F(n, d) for n, d in pairs]


def mul(a, b):
    r = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            r[i + j] += x * y
    return r


def add(a, b, s=1):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0) + s * (b[i] if i < len(b) else 0) for i in range(n)]


def ev(c, t):
    return sum((x * t ** i for i, x in enumerate(c)), F(0))


def der(c):
    return [i * c[i] for i in range(1, len(c))] or [F(0)]


def integ(c):
    return [F(0)] + [x / (i + 1) for i, x in enumerate(c)]


def comp(a, b):
    r = [F(0)]
    for i in range(len(a) - 1, -1, -1):
        r = add(mul(r, b), [a[i]])
    return r


def derive(U, V):
    uu, vv, uv = mul(U, U), mul(V, V), mul(U, V)
    dx, dy, sg = add(uu, vv, -1), [2 * x for x in uv], add(uu, vv)
    nk = [2 * x for x in add(mul(U, der(V)), mul(der(U), V), -1)]
    return {"X": integ(dx), "Y": integ(dy), "dx": dx, "dy": dy, "sg": sg, "SS": integ(sg), "Nk": nk}


def cell_a(U, V, t):
    p = derive(fr(U), fr(V))
    s = ev(p["sg"], t)
    return [ev(p["X"], t), ev(p["Y"], t), ev(p["dx"], t), ev(p["dy"], t), s * s, s, ev(p["SS"], t), ev(p["Nk"], t), s * s]


def cell_b(U, V, phi, t):
    p, f = derive(fr(U), fr(V)), fr(phi)
    g = ev(der(f), t)
    c = {k: comp(v, f) for k, v in p.items()}
    sg = g * ev(c["sg"], t)
    return [ev(c["X"], t), ev(c["Y"], t), g * ev(c["dx"], t), g * ev(c["dy"], t), sg, sg, ev(c["SS"], t)]
