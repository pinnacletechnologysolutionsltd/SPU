"""Shared constants and metric admission for REL-1 (declared shared dependency).

Reference nodes/edges/stress come from the PHY-R1 fixture (read-only). Constants follow PHY-R2's
squared-length law (kappa = 1/2 for cables). Nothing here knows which backend is calling.
"""
from __future__ import annotations

import hashlib
import os
import sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "phy_r1"))
import fixture  # noqa: E402
from field import QF, sqrt_in_field  # noqa: E402
import exact as X  # noqa: E402

P0, E = fixture.canonical()
QHAT = fixture.signed_stress(P0, E)            # cables 1, struts -3/2 (prestress level 1)
KAPPA = Fr(1, 2)
STRUTS = [k for k, (*_, t) in enumerate(E) if t == "S"]
CABLES = [k for k, (*_, t) in enumerate(E) if t == "C"]
BOUND = 2 ** 31
IDENT = tuple(tuple(Fr(int(a == b)) for b in range(3)) for a in range(3))
OMEGA = fixture.stress_matrix(QHAT, E, len(P0))
DECLARED = ("realisable", "strut_lengths", "equilibrium", "stability")


def check_metric(M, ops):
    """Reason string or None. Order: symmetry, coefficient bound, unit diagonal, positive definite."""
    if any(M[a][b] != M[b][a] for a in range(3) for b in range(3)):
        return "NOT_SYMMETRIC"
    if any(abs(v.numerator) > BOUND or v.denominator > BOUND for r in M for v in r):
        return "COEFFICIENT_BOUND"
    if any(M[k][k] != 1 for k in range(3)):
        return "STRUT_LENGTH_CHANGED"
    rank, psd = X.ldl([list(r) for r in M], ops)
    return None if rank == 3 and psd else "NOT_POSITIVE_DEFINITE"


def cholesky_points(P, M, d, ops, count):
    """Materialise x = A p in Q(sqrt d) with A^T A = M (upper-triangular A), or None if out of field."""
    count["materialise"] += 1
    m = [[QF.of(v, d) for v in row] for row in M]
    A = [[QF.of(0, d)] * 3 for _ in range(3)]
    for j in range(3):
        s = m[j][j]
        for k in range(j):
            ops["mul"] += 1
            ops["add"] += 1
            s = s - A[k][j] * A[k][j]
        r = sqrt_in_field(s)
        if r is None or r.is_zero():
            return None
        A[j][j] = r
        for i in range(j + 1, 3):
            acc = m[j][i]
            for k in range(j):
                ops["mul"] += 1
                ops["add"] += 1
                acc = acc - A[k][j] * A[k][i]
            ops["div"] += 1
            A[j][i] = acc / r
    out = []
    for p in P:
        ops["mul"] += 9
        ops["add"] += 6
        out.append(tuple(sum((A[r][c] * QF.of(p[c], d) for c in range(3)), QF.of(0, d)) for r in range(3)))
    return normalise(out)


def normalise(points):
    """Fractions when every coordinate is rational, QF otherwise (canonical observable form)."""
    if all(isinstance(c, Fr) or c.b == 0 for p in points for c in p):
        return tuple(tuple(c if isinstance(c, Fr) else c.a for c in p) for p in points)
    return tuple(tuple(c for c in p) for p in points)


def key(c):
    return (str(c.a), str(c.b), c.d) if isinstance(c, QF) else str(c)


def digest(values):
    return hashlib.sha256(repr([key(v) for v in values]).encode()).hexdigest()[:16]


class DependencyChanged(ValueError):
    pass


from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True)
class Cert:
    name: str
    gid: str          # geometry id of the state the claim is about
    value: bool
    basis: str        # 'computed' | 'reused:<handle>' | 'reused_lemma:<handle>'
