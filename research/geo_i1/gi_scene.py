"""Shapes, the irregular hierarchy rule and weights for GEO-I1 (HEX-C1 geometry read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr

import gi_metric as GM
from geom import HalfPlane, Shape, N                # noqa: E402  (HEX-C1, read-only)

K = 4
FOCUS = (3, 1)
WEIGHT = {"bound": 16, "point": 6, "table_eval": 5, "scaling": 2, "cert_compare": 1}


def refine_rule(c):
    return N((c[0] - FOCUS[0], c[1] - FOCUS[1])) <= 2 * 7 ** c[2]


@dataclass(frozen=True)
class GShape:
    sid: str
    pair: tuple | None = None        # metric shape: entry (i, j) of the REL-1 metric it depends on
    centre: tuple = (0, 0)
    rho: Fr = Fr(0)
    native: object = None            # HEX-C1 Shape (metric-independent)

    def fp(self):
        if self.native is not None:
            s = self.native
            return (self.sid, s.disk, tuple((h.alpha, h.beta, h.gamma) for h in s.planes))
        return (self.sid, self.pair, self.centre, self.rho)


def entry(M, shape):
    return None if shape.pair is None else M[shape.pair[0]][shape.pair[1]]


def contains(shape, M, p):
    if shape.native is not None:
        return shape.native.contains(p)
    return GM.Q(entry(M, shape), (p[0] - shape.centre[0], p[1] - shape.centre[1])) <= shape.rho


def scene():
    hp = lambda a, b, g: HalfPlane(Fr(a), Fr(b), Fr(g))      # noqa: E731
    return [
        GShape("nat_disk", native=Shape("nat_disk", disk=((3, 1), 40))),
        GShape("nat_halfplane", native=Shape("nat_halfplane", planes=[hp(1, -2, 5)])),
        GShape("md12", pair=(0, 1), centre=(3, 1), rho=Fr(60)),
        GShape("md13", pair=(0, 2), centre=(-4, 2), rho=Fr(70)),
        GShape("md23", pair=(1, 2), centre=(0, 0), rho=Fr(25)),       # boundary through lattice points at m = 0
    ]
