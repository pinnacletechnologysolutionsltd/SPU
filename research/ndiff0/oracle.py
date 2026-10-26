"""Independent reference: plain (p,q) Fraction pairs, no import of field.py/curve.py.

Derivatives come from the binomial Taylor shift P(t0+h) (not from the k*c_k rule used by the candidate)."""
from fractions import Fraction as F
from math import comb


def mul(u, v):
    return (u[0] * v[0] + 3 * u[1] * v[1], u[0] * v[1] + u[1] * v[0])


def add(u, v):
    return (u[0] + v[0], u[1] + v[1])


def conv(a, b):
    out = [(F(0), F(0))] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = add(out[i + j], mul(x, y))
    return out


def shift(poly, t0):
    """Coefficients c_k(t0) of poly(t0+h) = sum c_k h^k  (c_1 = P', 2*c_2 = P'')."""
    n = len(poly)
    pw = [(F(1), F(0))]
    for _ in range(n):
        pw.append(mul(pw[-1], t0))
    out = []
    for k in range(n):
        s = (F(0), F(0))
        for j in range(k, n):
            s = add(s, mul(poly[j], tuple(comb(j, k) * x for x in pw[j - k])))
        out.append(s)
    return out


def curve_facts(a, b, h, x0, y0, t0):
    """a,b,h: lists of (p,q). Returns value/derivative/speed^2/quadrance facts at t0, built from scratch."""
    a2, b2, ab = conv(a, a), conv(b, b), conv(a, b)
    neg = lambda u: (-u[0], -u[1])
    n = max(len(a2), len(b2))
    pad = lambda p: list(p) + [(F(0), F(0))] * (n - len(p))
    xp = conv(h, [add(u, neg(v)) for u, v in zip(pad(a2), pad(b2))])
    yp = conv(h, [(2 * u[0], 2 * u[1]) for u in ab])

    def integ(p, c0):
        return [c0] + [(u[0] / (k + 1), u[1] / (k + 1)) for k, u in enumerate(p)]

    X, Y = integ(xp, x0), integ(yp, y0)
    sx, sy = shift(X, t0), shift(Y, t0)
    px, py = sx[0], sy[0]
    tx, ty = sx[1], sy[1]
    sp2 = add(mul(tx, tx), mul(ty, ty))
    Q = add(mul(px, px), mul(py, py))
    dQ = tuple(2 * v for v in add(mul(px, tx), mul(py, ty)))
    return {"P": (px, py), "T": (tx, ty), "P2": (tuple(2 * v for v in sx[2]), tuple(2 * v for v in sy[2])),
            "speed2": sp2, "Q": Q, "dQ": dQ, "X": X, "Y": Y, "xp": xp, "yp": yp}


def pairs(poly):
    return [(c.p, c.q) for c in poly]
