"""Metric (Gram) state machine for the six-strut fixture, with SSM-style
immutable handles and dependency-checked certificate reuse.

State = fixed reference X0 + symmetric metric M (p -> A p with M = A^T A).
Edge quadrance is d^T M d. Coordinates are only produced by OBSERVE.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr

import fixture
from field import QF, rank_and_psd, sqrt_in_field

BOUND = 2 ** 31
IDENT = ((Fr(1), Fr(0), Fr(0)), (Fr(0), Fr(1), Fr(0)), (Fr(0), Fr(0), Fr(1)))


@dataclass(frozen=True)
class State:
    handle: int
    kind: str            # "metric" (affine image of X0) or "coords" (arbitrary edit)
    M: tuple | None
    coords: tuple | None
    parent: int | None


def quad(d, M):
    return sum(d[a] * M[a][b] * d[b] for a in range(3) for b in range(3))


class Machine:
    def __init__(self):
        self.X, self.E = fixture.canonical()
        q = fixture.signed_stress(self.X, self.E)
        if q is None:
            raise RuntimeError("reference is not in signed equilibrium")
        ss = fixture.super_stability(self.X, self.E, q)
        self.states = [State(0, "metric", IDENT, None, None)]
        # Certificates issued at handle 0; dependency: state is an affine image.
        self.certs = {0: {"stress": tuple(q), "super_stable": ss["super_stable"],
                          "struts_disjoint": True}}
        self.current = 0

    # ---- transitions -------------------------------------------------------
    def transform(self, M):
        M = tuple(tuple(Fr(v) for v in row) for row in M)
        if any(M[a][b] != M[b][a] for a in range(3) for b in range(3)):
            return ("REFUSED", "NOT_SYMMETRIC")
        if any(abs(v.numerator) > BOUND or v.denominator > BOUND for r in M for v in r):
            return ("REFUSED", "COEFFICIENT_BOUND")
        if any(M[k][k] != 1 for k in range(3)):
            return ("REFUSED", "STRUT_LENGTH_CHANGED")
        rank, psd = rank_and_psd([list(r) for r in M])
        if rank < 3 or not psd:
            return ("REFUSED", "NOT_POSITIVE_DEFINITE")
        return self._publish("metric", M, None)

    def adopt_coordinates(self, coords):
        """A non-metric edit (e.g. moving one strut). Accepted as geometry only."""
        return self._publish("coords", None, tuple(tuple(map(Fr, p)) for p in coords))

    def _publish(self, kind, M, coords):
        h = len(self.states)
        self.states.append(State(h, kind, M, coords, self.current))
        self.current = h
        return ("COMMITTED", h)

    # ---- certificate reuse (SSM-6 semantics) -------------------------------
    def reuse(self, h, skip_dependency_check=False):
        st = self.states[h]
        if not skip_dependency_check:
            if st.kind != "metric":
                return ("REFUSED", "DEPENDENCY_CHANGED")
            rank, psd = rank_and_psd([list(r) for r in st.M])
            if rank < 3 or not psd:
                return ("REFUSED", "DEPENDENCY_CHANGED")
        self.certs[h] = dict(self.certs[0])
        return ("REUSED", h)

    # ---- derived quantities -------------------------------------------------
    def pair_quadrances(self, h):
        st, n = self.states[h], len(self.X)
        if st.kind == "coords":
            P = st.coords
            return [[sum((P[i][k] - P[j][k]) ** 2 for k in range(3)) for j in range(n)]
                    for i in range(n)]
        X = self.X
        return [[quad([X[i][k] - X[j][k] for k in range(3)], st.M) for j in range(n)]
                for i in range(n)]

    def observe(self, h, d):
        """Materialise coordinates p' = A p in Q(sqrt d) via Cholesky, or refuse."""
        st = self.states[h]
        if st.kind == "coords":
            return ("EXACT", [tuple(QF.of(v, d) for v in p) for p in st.coords])
        m = [[QF.of(v, d) for v in row] for row in st.M]
        A = [[QF.of(0, d)] * 3 for _ in range(3)]
        for j in range(3):
            s = m[j][j] - sum((A[k][j] * A[k][j] for k in range(j)), QF.of(0, d))
            r = sqrt_in_field(s)
            if r is None or r.is_zero():
                return ("OUT_OF_FIELD", j)
            A[j][j] = r
            for i in range(j + 1, 3):
                acc = m[j][i] - sum((A[k][j] * A[k][i] for k in range(j)), QF.of(0, d))
                A[j][i] = acc / r
        pts = [tuple(sum((A[r_][c] * p[c] for c in range(3)), QF.of(0, d))
                     for r_ in range(3)) for p in self.X]
        return ("EXACT", pts)
