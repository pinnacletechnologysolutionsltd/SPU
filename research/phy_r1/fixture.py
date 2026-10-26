"""Canonical six-strut fixture, exact self-stress and super-stability checks.

The fixture is taken from the existing oracle (make_tensegrity_six_strut);
nothing here redefines it. Stress is solved on the reference coordinates.
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

from field import QF, nullspace_rank, rank_and_psd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_ROOT, "software", "lib"))
import tensegrity_balancer as TB  # noqa: E402


def _int(phi) -> int:
    if phi.b.num != 0 or phi.a.den != 1:
        raise ValueError("canonical fixture is expected to be integral")
    return phi.a.num


def canonical():
    """Return (X, E): 12 integer nodes and (i, j, 'C'|'S') edges."""
    s = TB.make_tensegrity_six_strut()
    X = [tuple(_int(c) for c in (v.x, v.y, v.z)) for v in s.nodes]
    E = [(e.node_a, e.node_b, "S" if e.edge_type == TB.EdgeType.STRUT else "C")
         for e in s.edges]
    return X, E


def self_stress_basis(X, E):
    """Basis of {q : sum_e q_e (x_i - x_j) = 0 at every node}, exact."""
    n = len(X)
    rows = []
    for node in range(n):
        for k in range(3):
            row = []
            for i, j, _ in E:
                if node == i:
                    row.append(Fr(X[i][k] - X[j][k]))
                elif node == j:
                    row.append(Fr(X[j][k] - X[i][k]))
                else:
                    row.append(Fr(0))
            rows.append(row)
    return nullspace_rank(rows)[0]


def signed_stress(X, E):
    """The unique self-stress, scaled so cables are positive, or None."""
    basis = self_stress_basis(X, E)
    if len(basis) != 1:
        return None
    q = [Fr(v) for v in basis[0]]
    k = next(v for v, (_, _, t) in zip(q, E) if t == "C")
    q = [v / k for v in q]
    ok = all((v > 0) if t == "C" else (v < 0) for v, (_, _, t) in zip(q, E))
    return q if ok else None


def stress_matrix(q, E, n):
    om = [[Fr(0)] * n for _ in range(n)]
    for v, (i, j, _) in zip(q, E):
        om[i][j] -= v
        om[j][i] -= v
        om[i][i] += v
        om[j][j] += v
    return om


def conic_condition(X, E) -> bool:
    """No nonzero symmetric S with d^T S d = 0 on every member direction."""
    rows = []
    for i, j, _ in E:
        d = [X[i][k] - X[j][k] for k in range(3)]
        rows.append([Fr(d[0] * d[0]), Fr(2 * d[0] * d[1]), Fr(2 * d[0] * d[2]),
                     Fr(d[1] * d[1]), Fr(2 * d[1] * d[2]), Fr(d[2] * d[2])])
    return len(nullspace_rank(rows)[1]) == 6


def super_stability(X, E, q):
    """Connelly's sufficient conditions: Omega PSD, nullity d+1 = 4, conic."""
    n = len(X)
    rank, psd = rank_and_psd(stress_matrix(q, E, n))
    return {"omega_psd": psd, "omega_nullity": n - rank,
            "conic_ok": conic_condition(X, E),
            "super_stable": psd and n - rank == 4 and conic_condition(X, E)}


def to_oracle(points, E, d):
    """Build an oracle TensegritySystem from coordinates in Q or Q(sqrt5)."""
    if d not in (1, 5):
        raise ValueError("oracle coordinates are Q(phi); need d in {1, 5}")

    def phi(v: QF):
        # r + s*sqrt5 = (r - s) + 2s*phi, since sqrt5 = 2*phi - 1
        r, s = v.a, v.b
        a, b = r - s, 2 * s
        return TB.Phi(TB.Fraction(a.numerator, a.denominator),
                      TB.Fraction(b.numerator, b.denominator))

    nodes = [TB.Vec3Phi(*(phi(c) for c in p)) for p in points]
    edges = [TB.Edge(i, j, TB.EdgeType.STRUT if t == "S" else TB.EdgeType.CABLE)
             for i, j, t in E]
    return TB.TensegritySystem(nodes=nodes, grid_states=[TB.GridState.MAIN] * len(nodes),
                               edges=edges)


def oracle_verdict(points, E, d) -> str:
    s = to_oracle(points, E, d).configure()
    if s.state == TB.TensegrityState.CONFIGURING:
        s.verify_balance()
    return s.state.name
