"""Independent exhaustive oracle, exhaustive-with-cache, and the coordinate-materialised baseline."""
from __future__ import annotations

import os
import sys
from collections import Counter
from fractions import Fraction as Fr

import gi_scene as S

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phy_r1"))
from field import QF, sqrt_in_field  # noqa: E402


class OutOfField(ValueError):
    pass


def oracle_contains(shape, M, p):
    """Written independently of geom.py / gi_metric.py: direct formulas on exact rationals."""
    if shape.native is not None:
        s = shape.native
        if s.disk is not None:
            (ca, cb), rho = s.disk
            da, db = p[0] - ca, p[1] - cb
            return da * da - da * db + db * db <= rho
        return all(h.alpha * p[0] + h.beta * p[1] + h.gamma >= 0 for h in s.planes)
    m = M[shape.pair[0]][shape.pair[1]]
    da, db = p[0] - shape.centre[0], p[1] - shape.centre[1]
    return da * da + 2 * m * da * db + db * db <= shape.rho


def oracle(shape, M, pts, ctr):
    ctr["oracle_point"] += len(pts)
    return {p for p in pts if oracle_contains(shape, M, p)}


class ExhaustiveCached:
    """Per-point verdict certificates with the same dependency keys (no hierarchy)."""

    def __init__(self):
        self.certs, self.ctr = {}, Counter()

    def query(self, shape, M, pts):
        dep = (shape.fp(), S.entry(M, shape))
        out = set()
        for p in pts:
            self.ctr["cert_compare"] += 1
            c = self.certs.get((p, shape.sid))
            if c is not None and c[1] == dep:
                self.ctr["reused"] += 1
                v = c[0]
            else:
                self.ctr["point"] += 1
                v = oracle_contains(shape, M, p)
                self.certs[(p, shape.sid)] = (v, dep)
            if v:
                out.add(p)
        return out

    def footprint(self):
        return {"certs": len(self.certs)}


def embed(m):
    """Coordinates (a + m b, r b) with r = sqrt(1 - m^2) in Q, or OutOfField."""
    r = sqrt_in_field(QF(1 - m * m, Fr(0), 1))
    if r is None:
        raise OutOfField("sqrt(1 - m^2) not in Q")
    return r.a


def coord_query(shape, M, pts, ctr):
    if shape.native is not None:
        return oracle(shape, M, pts, Counter())
    m = M[shape.pair[0]][shape.pair[1]]
    r = embed(m)
    ctr["materialise"] += 1
    sx, sy = shape.centre[0] + m * shape.centre[1], r * shape.centre[1]
    ctr["coord_point"] += len(pts)
    return {p for p in pts if (p[0] + m * p[1] - sx) ** 2 + (r * p[1] - sy) ** 2 <= shape.rho}
