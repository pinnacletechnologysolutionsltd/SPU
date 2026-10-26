"""Phase 4 (exploratory): the Eisenstein-norm analogue.  Z[w] element a+b*w, w=(-1+sqrt(-3))/2, w^2=-1-w.

Norm N(a+bw)=a^2-ab+b^2 is the *Euclidean* quadrance in oblique coordinates (a+bw -> (a-b/2, b*sqrt3/2)), so the
identity N(z^2)=N(z)^2 is the unchanged Euclidean PH identity, with generators in Q(w) instead of Q(sqrt3).
Counts are kept at rational-op level: E*E = 4mR+3aR, E+E = 2aR, E*rational = 2mR.
"""
from fractions import Fraction as F
from collections import Counter

C = Counter()


class E:
    __slots__ = ("a", "b")

    def __init__(s, a=0, b=0):
        s.a, s.b = F(a), F(b)

    def __add__(x, y):
        C["aR"] += 2
        return E(x.a + y.a, x.b + y.b)

    def __sub__(x, y):
        C["aR"] += 2
        return E(x.a - y.a, x.b - y.b)

    def __mul__(x, y):
        C["mR"] += 4
        C["aR"] += 3
        return E(x.a * y.a - x.b * y.b, x.a * y.b + x.b * y.a - x.b * y.b)

    def rmul(x, r):
        C["mR"] += 2
        return E(x.a * r, x.b * r)

    def conj(x):
        return E(x.a - x.b, -x.b)

    def norm(x):
        C["mR"] += 3
        C["aR"] += 2
        return x.a * x.a - x.a * x.b + x.b * x.b

    def trace(x):
        return 2 * x.a - x.b

    def __eq__(x, y):
        return (x.a, x.b) == (y.a, y.b)

    def cart(x):  # (x, y) = ((p, 0), (0, q)) in Q(sqrt3): x = a-b/2, y = (b/2)*sqrt3
        return (x.a - x.b / 2, F(0)), (F(0), x.b / 2)


def horner_r(poly, t):
    r = poly[-1]
    for c in reversed(poly[:-1]):
        r = r.rmul(t) + c
    return r


def pmul(p, q):
    out = [E()] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            out[i + j] = out[i + j] + x * y
    return out


def rpoly(p, h):  # real polynomial h (list of Fractions) times E polynomial
    out = [E()] * (len(p) + len(h) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(h):
            out[i + j] = out[i + j] + x.rmul(y)
    return out


class EPH:
    def __init__(self, zeta, h=(F(1),), w0=E()):
        self.zeta, self.h = list(zeta), list(h)
        self.w = rpoly(pmul(self.zeta, self.zeta), self.h)  # hodograph x'+i y' in Q(w)[t]
        self.W = [w0] + [c.rmul(F(1, k + 1)) for k, c in enumerate(self.w)]
        self.dW = [c.rmul(k) for k, c in enumerate(self.W) if k]


def _tail(P, T, sp2):
    return {"P": P, "T": T, "speed2": sp2, "Q": P.norm(), "dQ": (P * T.conj()).trace()}


def eph_eval(c, t):
    z, h = horner_r(c.zeta, t), sum((F(x) * t ** k for k, x in enumerate(c.h)), F(0))
    nz = z.norm()
    T = (z * z).rmul(h)
    out = _tail(horner_r(c.W, t), T, (nz * h) ** 2)
    out["sigma"] = nz * h
    return out


def poly_eval(c, t):
    T = horner_r(c.dW, t)
    return _tail(horner_r(c.W, t), T, T.norm())
