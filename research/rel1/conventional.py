"""Conventional exact backend: state = explicit coordinates in Q(sqrt d), materialised at every
transition. Equilibrium is explicit node force sums; stability builds the x-space Hessian
Omega (x) I3 + sum_cables 2 kappa u u^T with u the member displacement-difference 36-vectors.
Affinity (for reuse) is decided from coordinates by an exact linear solve. Independent of
relational.py; shares only exact.py kernels and geometry.py constants/admission.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr

import exact as X
import geometry as G
from field import QF
from geometry import Cert, DependencyChanged


@dataclass(frozen=True)
class CState:
    x: tuple
    gid: str


def rat(v):
    """Rational value of a coordinate-quadratic (its surd part must vanish)."""
    if isinstance(v, QF):
        assert v.b == 0, "quadrance must be rational"
        return v.a
    return v


def sq(d, ops):
    ops["mul"] += 3
    ops["add"] += 2
    return rat(sum((c * c for c in d), Fr(0)))


def diff(x, i, j):
    return [x[i][k] - x[j][k] for k in range(3)]


def make(x, ops):
    n = len(x)
    return CState(x, G.digest([sq(diff(x, i, j), ops) for i in range(n) for j in range(i + 1, n)]))


def admit(d, ops, count):
    return make(G.cholesky_points(G.P0, G.IDENT, d, ops, count), ops)


def transform(M, d, ops, count):
    why = G.check_metric(M, ops)
    if why:
        raise ValueError(why)
    x = G.cholesky_points(G.P0, M, d, ops, count)
    if x is None:
        raise ValueError("OUT_OF_FIELD")
    return make(x, ops)


def move(state, nodes, off, d, ops, count):
    y = [tuple(c + off[k] for k, c in enumerate(p)) if i in nodes else p for i, p in enumerate(state.x)]
    return make(G.normalise([list(p) for p in y]), ops)


def realisable(s, ops):
    n = len(s.x)
    cen = [sum(s.x[i][k] for i in range(n)) / n for k in range(3)]
    ops["mul"] += 9 * n
    ops["add"] += 3 * n
    gram = [[sum((s.x[i][a] - cen[a]) * (s.x[i][b] - cen[b]) for i in range(n)) for b in range(3)]
            for a in range(3)]
    rank, psd = X.ldl(gram, ops)
    return rank == 3 and psd


def strut_lengths(s, ops):
    return all(sq(diff(s.x, *G.E[k][:2]), ops) == 16 for k in G.STRUTS)


def equilibrium(s, ops):
    for node in range(len(s.x)):
        f = [Fr(0)] * 3
        for q, (i, j, _) in zip(G.QHAT, G.E):
            if node in (i, j):
                o = j if node == i else i
                ops["mul"] += 3
                ops["add"] += 3
                f = [f[k] + q * (s.x[o][k] - s.x[node][k]) for k in range(3)]
        if any(not X.zero(c) for c in f):
            return False
    return all(sq(diff(s.x, *G.E[k][:2]), ops) > G.QHAT[k] / G.KAPPA for k in G.CABLES)


def stability(s, ops):
    if not (strut_lengths(s, ops) and equilibrium(s, ops)):
        return None
    n = len(s.x)
    H = [[Fr(0)] * (3 * n) for _ in range(3 * n)]
    for i in range(n):
        for j in range(n):
            w = G.OMEGA[i][j]
            if w != 0:
                for a in range(3):
                    H[3*i+a][3*j+a] += w
    J = []
    for (i, j, t) in G.E:
        d = diff(s.x, i, j)
        u = [Fr(0)] * (3 * n)
        for a in range(3):
            u[3*i+a], u[3*j+a] = d[a], -d[a]
        if t == "S":
            J.append(u)
        else:
            nz = [r for r in range(3 * n) if not X.zero(u[r])]
            ops["mul"] += len(nz) ** 2
            ops["add"] += len(nz) ** 2
            for r in nz:
                for c in nz:
                    H[r][c] += 2 * G.KAPPA * u[r] * u[c]
    N, _ = X.nullspace(J, ops)
    HN = [X.matvec(H, v, ops) for v in N]
    Hn = [[X.dot(u, w, ops) for w in HN] for u in N]
    rank, psd = X.ldl(Hn, ops)
    return len(N) == 30 and psd and len(N) - rank == 6


def compute(s, name, ops):
    return {"realisable": realisable, "strut_lengths": strut_lengths,
            "equilibrium": equilibrium, "stability": stability}[name](s, ops)


def _basis():
    for a in range(1, 12):
        for b in range(a + 1, 12):
            for c in range(b + 1, 12):
                m = [[Fr(G.P0[i][k] - G.P0[0][k]) for i in (a, b, c)] for k in range(3)]
                if X_det(m) != 0:
                    return (a, b, c), inv3(m)


def X_det(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
            + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))


def inv3(m):
    det = X_det(m)
    c = [[(m[(j+1) % 3][(i+1) % 3]*m[(j+2) % 3][(i+2) % 3] - m[(j+1) % 3][(i+2) % 3]*m[(j+2) % 3][(i+1) % 3]) / det
          for j in range(3)] for i in range(3)]
    return c


BASIS, PINV = _basis()


def affine(s, ops):
    """Exact: is there A with x_i - x_0 = A (p_i - p_0) for every node?"""
    cols = [diff(s.x, i, 0) for i in BASIS]                      # three x-difference columns
    A = [[sum((cols[c][r] * PINV[c][k] for c in range(3)), Fr(0)) for k in range(3)] for r in range(3)]
    ops["mul"] += 27
    ops["add"] += 18
    for i in range(len(s.x)):
        ops["mul"] += 9
        ops["add"] += 6
        for r in range(3):
            if sum((A[r][k] * (G.P0[i][k] - G.P0[0][k]) for k in range(3)), Fr(0)) != s.x[i][r] - s.x[0][r]:
                return False
    return True


def observe(s, d, ops, count):
    return s.x


def reuse(cert, src, dst, lemma, ops, handle, skip_dependency_check=False):
    if skip_dependency_check or dst.gid == src.gid:
        return Cert(cert.name, dst.gid, cert.value, f"reused:{handle}")
    n = cert.name
    if n in ("strut_lengths", "realisable"):
        ok = strut_lengths(dst, ops) if n == "strut_lengths" else realisable(dst, ops)
        basis = f"reused:{handle}"
    else:
        ok = affine(dst, ops) and equilibrium(dst, ops) and (n == "equilibrium" or lemma)
        basis = f"reused:{handle}" if n == "equilibrium" else f"reused_lemma:{handle}"
    if not ok or not cert.value:
        raise DependencyChanged(n)
    return Cert(n, dst.gid, cert.value, basis)
