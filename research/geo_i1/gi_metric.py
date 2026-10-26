"""Plane-metric predicates for GEO-I1 (exact, rational, no sqrt).

A REL-1 metric state M defines, for a pair (i, j), the quadratic form on lattice coordinates (a, b):
  Q_m(a, b) = a^2 + 2 m ab + b^2,  m = M[i][j]  (positive definite because |m| < 1; unit diagonal).
Norm triangle inequality gives the same squared tests as HEX-C1 (disk_vs_disk) with Q_m for N.
Bounds for a level-l node: R2_m[l] = max over the finite descendant set D_l of Q_m (exact, by
enumeration) or the scaled certificate 2(1+|m|) * R2_hex[l] (proof: Q_m <= (1+|m|)(a^2+b^2) <= 2(1+|m|) N).
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hex_c1"))
import hier as H                                   # noqa: E402  (HEX-C1, read-only)
from geom import INSIDE, OUTSIDE, STRADDLE         # noqa: E402

STRAD = STRADDLE


def Q(m, x):
    return x[0] * x[0] + 2 * m * x[0] * x[1] + x[1] * x[1]


def disk_vs_disk_q(m, c, R2, s, rho):
    """Bound set {x : Q_m(x - c) <= R2} against the closed shape {x : Q_m(x - s) <= rho}."""
    d = Q(m, (c[0] - s[0], c[1] - s[1]))
    t = rho + R2 - d
    if rho >= R2 and t >= 0 and 4 * R2 * rho <= t * t:
        return INSIDE
    u = d - rho - R2
    if u > 0 and u * u > 4 * R2 * rho:
        return OUTSIDE
    return STRAD


def table_exact(m, K, ctr):
    """max Q_m over every level's descendant set; counts one evaluation per descendant."""
    out = []
    for level in range(K + 1):
        pts = H.offsets(level)
        ctr["table_evals"] += len(pts)
        out.append(max(Q(m, x) for x in pts))
    return out


def table_scaled(m, K, ctr):
    ctr["table_scalings"] += K + 1
    f = 2 * (1 + abs(m))
    return [f * r for r in H.bound_table(K)]
