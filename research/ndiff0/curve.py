"""Planar PH curve P'(t) = h(t)*(a^2-b^2, 2ab), h real polynomial (h=1: primitive generator form)."""
from field import *


class PH:
    def __init__(self, a, b, h=None, x0=ZERO, y0=ZERO):
        self.a, self.b, self.h = tuple(a), tuple(b), tuple(h or (ONE,))
        a2, b2, ab = pmul(self.a, self.a), pmul(self.b, self.b), pmul(self.a, self.b)
        self.sigma = pmul(self.h, padd(a2, b2))
        hx, hy = pmul(self.h, padd(a2, b2, True)), pmul(self.h, tuple(c.scale(2) for c in ab))
        self.xp, self.yp = hx, hy
        self.X, self.Y = padd(pint(hx), (x0,)), padd(pint(hy), (y0,))
        self.dX, self.dY = pder(self.X), pder(self.Y)  # baseline's derivative polynomials (costed separately)


def denominators(poly):
    ds = sorted({c.p.denominator for c in poly} | {c.q.denominator for c in poly})
    return ds


def sample_curve():
    """Degree-5 curve, generators of degree 2 with surd coefficients and denominators."""
    a = (S3(1, 0), S3(0, 1), S3(F(1, 2), 0))
    b = (S3(2, -1), S3(F(-1, 3), 0), S3(0, F(1, 4)))
    return PH(a, b, x0=S3(1, 1), y0=S3(F(-1, 2), 0))
