"""Exact planar predicates in Eisenstein lattice coordinates x = (a, b) = a + b*w.

Euclidean quadrance N(x) = a^2 - ab + b^2 (unit edge). Bilinear form
B(x, y) = a1 a2 - (a1 b2 + b1 a2)/2 + b1 b2. A half-plane is
f(x) = alpha a + beta b + gamma >= 0 (closed); its Euclidean gradient norm^2 is
(4/3)(alpha^2 + alpha beta + beta^2). All tests are rational: no sqrt, no float.
Shapes are closed sets; touching is never "disjoint".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as Fr

INSIDE, OUTSIDE, STRADDLE = "INSIDE", "OUTSIDE", "STRADDLE"


def N(x):
    a, b = x
    return a * a - a * b + b * b


def B(x, y):
    return x[0] * y[0] - Fr(x[0] * y[1] + x[1] * y[0], 2) + x[1] * y[1]


def sub(x, y):
    return (x[0] - y[0], x[1] - y[1])


@dataclass
class HalfPlane:
    alpha: Fr
    beta: Fr
    gamma: Fr

    def f(self, x):
        return self.alpha * x[0] + self.beta * x[1] + self.gamma

    def grad2(self):
        return Fr(4, 3) * (self.alpha ** 2 + self.alpha * self.beta + self.beta ** 2)


@dataclass
class Shape:
    """A closed disk (center, rho = squared radius) or a convex polygon (half-planes)."""
    sid: str
    disk: tuple | None = None
    planes: list = field(default_factory=list)
    version: int = 0

    def contains(self, x) -> bool:
        if self.disk is not None:
            c, rho = self.disk
            return N(sub(x, c)) <= rho
        return all(h.f(x) >= 0 for h in self.planes)


def disk_vs_halfplane(c, R2, h):
    v, g = h.f(c), h.grad2()
    if v >= 0 and v * v >= R2 * g:
        return INSIDE
    if v < 0 and v * v > R2 * g:
        return OUTSIDE
    return STRADDLE


def disk_vs_disk(c, R2, s, rho):
    """Bound disk (c, R2) vs shape disk (s, rho), via squared comparisons only.

    inside  <=> sqrt d + R <= sqrt rho   <=> rho >= R2, t = rho + R2 - d >= 0, 4 R2 rho <= t^2
    outside <=> sqrt d > sqrt rho + R    <=> u = d - rho - R2 > 0, u^2 > 4 R2 rho
    """
    d = N(sub(c, s))
    t = rho + R2 - d
    if rho >= R2 and t >= 0 and 4 * R2 * rho <= t * t:
        return INSIDE
    u = d - rho - R2
    if u > 0 and u * u > 4 * R2 * rho:
        return OUTSIDE
    return STRADDLE


def classify_disk(c, R2, shape):
    """Conservative verdict for every point within quadrance R2 of c."""
    if shape.disk is not None:
        return disk_vs_disk(c, R2, *shape.disk)
    vs = [disk_vs_halfplane(c, R2, h) for h in shape.planes]
    if OUTSIDE in vs:
        return OUTSIDE
    return INSIDE if all(v == INSIDE for v in vs) else STRADDLE


def classify_polygon(vertices, shape):
    """Verdict for a convex region given by its vertices (used only by the
    hexagon-assumption mutant): inside if all vertices in a convex shape;
    outside if all vertices strictly outside one half-plane / beyond the disk."""
    if all(shape.contains(v) for v in vertices) and shape.disk is None:
        return INSIDE
    if shape.disk is None and any(all(h.f(v) < 0 for v in vertices) for h in shape.planes):
        return OUTSIDE
    if shape.disk is not None:
        c, rho = shape.disk
        if all(N(sub(v, c)) <= rho for v in vertices):
            return INSIDE                      # disk is convex
    return STRADDLE
