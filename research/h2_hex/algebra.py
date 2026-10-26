"""Exact algebra for H2: Q(sqrt3) scalars, Eisenstein integers, planar maps.

The hex lattice is L = Z[w], w = (-1 + sqrt(-3))/2, unit edge quadrance.
Cartesian embedding: a + b*w  ->  (a - b/2, (b/2)*sqrt3), so coordinates lie
in Q(sqrt3). No floating point is used anywhere in this package.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F


@dataclass(frozen=True)
class Q3:
    """Exact element r + s*sqrt3 of Q(sqrt3)."""
    r: F
    s: F = F(0)

    @staticmethod
    def of(x) -> "Q3":
        return x if isinstance(x, Q3) else Q3(F(x))

    def __add__(self, o):
        o = Q3.of(o)
        return Q3(self.r + o.r, self.s + o.s)

    __radd__ = __add__

    def __neg__(self):
        return Q3(-self.r, -self.s)

    def __sub__(self, o):
        return self + (-Q3.of(o))

    def __rsub__(self, o):
        return Q3.of(o) - self

    def __mul__(self, o):
        o = Q3.of(o)
        return Q3(self.r * o.r + 3 * self.s * o.s, self.r * o.s + self.s * o.r)

    __rmul__ = __mul__

    def inv(self) -> "Q3":
        n = self.r * self.r - 3 * self.s * self.s   # field norm; 0 only at 0
        if n == 0:
            raise ZeroDivisionError("zero in Q(sqrt3)")
        return Q3(self.r / n, -self.s / n)

    def __truediv__(self, o):
        return self * Q3.of(o).inv()

    def is_rational(self) -> bool:
        return self.s == 0

    def norm(self) -> F:
        return self.r * self.r - 3 * self.s * self.s


SQRT3 = Q3(F(0), F(1))
ZERO, ONE = Q3(F(0)), Q3(F(1))

# ---- Eisenstein integers, stored as (a, b) meaning a + b*w -------------

def e_mul(z, v):
    """(a+bw)(c+dw) with w^2 = -1 - w."""
    a, b = z
    c, d = v
    return (a * c - b * d, a * d + b * c - b * d)


def e_norm(z) -> int:
    a, b = z
    return a * a - a * b + b * b


def e_conj(z):
    """Complex conjugate: w -> w^2 = -1 - w."""
    a, b = z
    return (a - b, -b)


def to_cart(z):
    a, b = z
    return (Q3(F(a) - F(b, 2)), Q3(F(0), F(b, 2)))


def from_cart(p):
    """Return (a, b) if the Cartesian point lies on L, else None.

    Independent of e_mul: reads lattice coordinates back from Q(sqrt3) parts.
    y must be pure (b/2)*sqrt3 with b in Z; x must be rational with
    a = x + b/2 in Z.
    """
    x, y = p
    if y.r != 0 or x.s != 0:
        return None
    b = 2 * y.s
    a = x.r + b / 2
    if b.denominator != 1 or a.denominator != 1:
        return None
    return (int(a), int(b))


def quadrance(p) -> Q3:
    x, y = p
    return x * x + y * y


# ---- 2x2 planar linear maps over Q(sqrt3), rows ((m00, m01), (m10, m11)) --

def apply(m, p):
    (m00, m01), (m10, m11) = m
    x, y = p
    return (m00 * x + m01 * y, m10 * x + m11 * y)


def compose(m, n):
    """m after n."""
    (a, b), (c, d) = m
    (e, f), (g, h) = n
    return ((a * e + b * g, a * f + b * h), (c * e + d * g, c * f + d * h))


def gram(m):
    """M^T M — equals s*I exactly for a similarity with scale-squared s."""
    (a, b), (c, d) = m
    return ((a * a + c * c, a * b + c * d), (a * b + c * d, b * b + d * d))


def det(m) -> Q3:
    (a, b), (c, d) = m
    return a * d - b * c


IDENT = ((ONE, ZERO), (ZERO, ONE))


def eis_matrix(z):
    """Cartesian matrix of multiplication by z (derived from to_cart(z))."""
    x, y = to_cart(z)
    return ((x, -y), (y, x))


def scale_matrix(k: Q3):
    return ((k, ZERO), (ZERO, k))


def cayley_rotation(t: Q3):
    """Rotation with half-angle tangent t: cos=(1-t^2)/(1+t^2), sin=2t/(1+t^2)."""
    d = ONE + t * t
    c = (ONE - t * t) / d
    s = (2 * t) / d
    return ((c, -s), (s, c))


def tan_half_compose(t1: Q3, t2: Q3) -> Q3:
    """Half-angle tangent of the composed rotation (tangent addition)."""
    return (t1 + t2) / (ONE - t1 * t2)
