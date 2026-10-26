"""Relational backend: state = reference points P + metric M (x = A P, A^T A = M). Coordinates are
materialised only by MOVE-from-metric and OBSERVE. Stability uses the PHY-R3 form in eps-space:
  H(eps) = sum_members q (de)^T M (de) + sum_cables 2 kappa (dp^T M de)^2, tangent: dp^T M de = 0 (struts).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr

import exact as X
import geometry as G
from geometry import Cert, DependencyChanged


@dataclass(frozen=True)
class RState:
    kind: str          # 'metric' (affine image of P0) or 'coords' (explicit points, M = I)
    M: tuple
    P: tuple
    gid: str


def quad(dp, M, ops):
    ops["mul"] += 12
    ops["add"] += 8
    return sum(dp[a] * M[a][b] * dp[b] for a in range(3) for b in range(3))


def delta(P, i, j):
    return [P[i][k] - P[j][k] for k in range(3)]


def make(kind, M, P, ops):
    n = len(P)
    q = [quad(delta(P, i, j), M, ops) for i in range(n) for j in range(i + 1, n)]
    return RState(kind, M, P, G.digest(q))


def admit(ops):
    return make("metric", G.IDENT, tuple(tuple(Fr(c) for c in p) for p in G.P0), ops)


def transform(state, M, ops):
    why = G.check_metric(M, ops)
    if why:
        raise ValueError(why)
    return make("metric", M, admit(X.Ops()).P, ops)


def move(state, nodes, off, d, ops, count):
    x = state.P if state.kind == "coords" else G.cholesky_points(state.P, state.M, d, ops, count)
    if x is None:
        raise ValueError("OUT_OF_FIELD")
    y = [tuple(c + off[k] for k, c in enumerate(p)) if i in nodes else p for i, p in enumerate(x)]
    return make("coords", G.IDENT, G.normalise([list(p) for p in y]), ops)


def pd(state, ops):
    rank, psd = X.ldl([list(r) for r in state.M], ops)
    return rank == 3 and psd


def realisable(state, ops):
    n = len(state.P)
    cen = [sum(state.P[i][k] for i in range(n)) / n for k in range(3)]
    ops["add"] += 3 * n
    ops["mul"] += 9 * n
    gram = [[sum((state.P[i][a] - cen[a]) * (state.P[i][b] - cen[b]) for i in range(n)) for b in range(3)]
            for a in range(3)]
    rank, psd = X.ldl(gram, ops)
    return pd(state, ops) and rank == 3 and psd


def strut_lengths(state, ops):
    return all(quad(delta(state.P, *G.E[k][:2]), state.M, ops) == 16 for k in G.STRUTS)


def equilibrium(state, ops):
    cols = [[Fr(p[k]) if not hasattr(p[k], "d") else p[k] for p in state.P] for k in range(3)]
    if not all(X.zero(v) for k in range(3) for v in X.matvec(G.OMEGA, cols[k], ops)):
        return False
    if not pd(state, ops):
        return False
    return all(quad(delta(state.P, *G.E[k][:2]), state.M, ops) > G.QHAT[k] / G.KAPPA for k in G.CABLES)


def stability(state, ops):
    """True/False for strictness, None when stability is undefined (not an equilibrium / struts)."""
    if not (strut_lengths(state, ops) and equilibrium(state, ops)):
        return None
    n, M = len(state.P), state.M
    H = [[Fr(0)] * (3 * n) for _ in range(3 * n)]
    J = []

    def add(i, j, W):
        ops["add"] += 36
        for a in range(3):
            for b in range(3):
                H[3*i+a][3*i+b] += W[a][b]
                H[3*j+a][3*j+b] += W[a][b]
                H[3*i+a][3*j+b] -= W[a][b]
                H[3*j+a][3*i+b] -= W[a][b]
    for (i, j, t), q in zip(G.E, G.QHAT):
        dp = delta(state.P, i, j)
        g = [sum(M[a][b] * dp[b] for b in range(3)) for a in range(3)]
        ops["mul"] += 9
        add(i, j, [[q * M[a][b] for b in range(3)] for a in range(3)])
        ops["mul"] += 9
        if t == "S":
            row = [Fr(0)] * (3 * n)
            for a in range(3):
                row[3*i+a], row[3*j+a] = g[a], -g[a]
            J.append(row)
        else:
            add(i, j, [[2 * G.KAPPA * g[a] * g[b] for b in range(3)] for a in range(3)])
            ops["mul"] += 9
    N, _ = X.nullspace(J, ops)
    HN = [X.matvec(H, v, ops) for v in N]
    Hn = [[X.dot(u, w, ops) for w in HN] for u in N]
    rank, psd = X.ldl(Hn, ops)
    return len(N) == 30 and psd and len(N) - rank == 6


def compute(state, name, ops):
    return {"realisable": realisable, "strut_lengths": strut_lengths,
            "equilibrium": equilibrium, "stability": stability}[name](state, ops)


def observe(state, d, ops, count):
    if state.kind == "coords":
        return state.P
    x = G.cholesky_points(state.P, state.M, d, ops, count)
    if x is None:
        raise ValueError("OUT_OF_FIELD")
    return x


def reuse(cert, src, dst, lemma, ops, handle, skip_dependency_check=False):
    """Carry a certificate to dst only if its dependencies are preserved (checked, never recomputed)."""
    if skip_dependency_check:
        return Cert(cert.name, dst.gid, cert.value, f"reused:{handle}")
    if dst.gid == src.gid:                                   # restoration: same geometry
        return Cert(cert.name, dst.gid, cert.value, f"reused:{handle}")
    n = cert.name
    if n in ("strut_lengths", "realisable"):
        ok = strut_lengths(dst, ops) if n == "strut_lengths" else realisable(dst, ops)
        basis = f"reused:{handle}"
    else:                                                    # equilibrium, stability: affine image of P0
        ok = dst.kind == "metric" and equilibrium(dst, ops) and (n == "equilibrium" or lemma)
        basis = f"reused:{handle}" if n == "equilibrium" else f"reused_lemma:{handle}"
    if not ok or not cert.value:
        raise DependencyChanged(n)
    return Cert(n, dst.gid, cert.value, basis)
