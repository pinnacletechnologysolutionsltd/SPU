"""PHY-R3: exact constrained second variation of the PHY-R2 equilibria.

Lagrangian L = sum_cables U_c + sum_struts mu_s (Q_s - 16), mu_s = q_s / 2, so the
strut reaction enters as geometric stiffness q_s only (rigid struts have no axial
term). With node displacements delta_i = A eps_i (A^T A = M) every entry is rational:

  second form  H(eps) = sum_members q_e (de)^T M (de) + sum_cables s_c (dp^T M de)^2
  de = eps_i - eps_j, dp = reference p_i - p_j, Q_c = dp^T M dp
  squared law  s_c = 2 kappa                     (axial stiffness a = q + 2 kappa Q)
  Hooke law    s_c = (k - q)/Q = k (l0/l)/Q      (axial stiffness a = k, transverse q)
Tangent space N: dp^T M de = 0 for every strut. Rigid motions: eps_i = c + M^-1 S p_i.
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phy_r2"))
import actuation as A                      # noqa: E402
from field import nullspace_rank, rank_and_psd  # noqa: E402

model, fixture = A.model, A.fixture


def mv(M, v):
    return [sum(M[a][b] * v[b] for b in range(3)) for a in range(3)]


def inv3(M):
    a = [[Fr(v) for v in r] + [Fr(int(i == j)) for j in range(3)] for i, r in enumerate(M)]
    for c in range(3):
        k = next(i for i in range(c, 3) if a[i][c] != 0)
        a[c], a[k] = a[k], a[c]
        a[c] = [v / a[c][c] for v in a[c]]
        for i in range(3):
            if i != c:
                a[i] = [x - a[i][c] * y for x, y in zip(a[i], a[c])]
    return [r[3:] for r in a]


def stiffness(mach, M, law, k=None):
    """Per-cable s_c for 'squared' or 'hooke'; k overrides the Hooke stiffness (diagnostic)."""
    out = []
    for (i, j, t), q in zip(mach.E, A.target_densities(mach)):
        if t != "C":
            out.append(Fr(0))
        elif law == "squared":
            out.append(2 * A.SQUARED["C"])
        else:
            dp = [mach.X[i][a] - mach.X[j][a] for a in range(3)]
            out.append(((k if k is not None else A.HOOKE["C"]) - q) / model.quad(dp, M))
    return out


def build(mach, M, s, q=None, with_struts=True):
    """36x36 Hessian-form matrix and the 6 strut constraint rows."""
    q = A.target_densities(mach) if q is None else q
    n = len(mach.X)
    H = [[Fr(0)] * (3 * n) for _ in range(3 * n)]
    J = []

    def add(i, j, W):
        for a in range(3):
            for b in range(3):
                H[3 * i + a][3 * i + b] += W[a][b]
                H[3 * j + a][3 * j + b] += W[a][b]
                H[3 * i + a][3 * j + b] -= W[a][b]
                H[3 * j + a][3 * i + b] -= W[a][b]
    for (i, j, t), qe, se in zip(mach.E, q, s):
        dp = [mach.X[i][a] - mach.X[j][a] for a in range(3)]
        g = mv(M, dp)
        if t == "S":
            row = [Fr(0)] * (3 * n)
            for a in range(3):
                row[3 * i + a], row[3 * j + a] = g[a], -g[a]
            J.append(row)
        if t == "C" or with_struts:
            add(i, j, [[qe * M[a][b] for b in range(3)] for a in range(3)])
        if t == "C" and se != 0:
            add(i, j, [[se * g[a] * g[b] for b in range(3)] for a in range(3)])
    return H, J


def qform(H, v):
    return sum(v[a] * H[a][b] * v[b] for a in range(len(v)) for b in range(len(v)) if v[a] and v[b])


def matvec(H, v):
    return [sum(H[a][b] * v[b] for b in range(len(v))) for a in range(len(H))]


def rigid_basis(mach, M):
    n, Mi = len(mach.X), inv3(M)
    vs = []
    for c in range(3):
        vs.append([Fr(int(a == c)) for _ in range(n) for a in range(3)])
    for S in ([[0, 1, 0], [-1, 0, 0], [0, 0, 0]], [[0, 0, 1], [0, 0, 0], [-1, 0, 0]],
              [[0, 0, 0], [0, 0, 1], [0, -1, 0]]):
        B = [[sum(Mi[a][c] * S[c][b] for c in range(3)) for b in range(3)] for a in range(3)]
        vs.append([x for p in mach.X for x in mv(B, p)])
    return vs


def shear_mode(mach, M, a, b):
    """eps = M^-1 C p with C = E_ab + E_ba: strut-preserving, tangent to the PHY-R1 family."""
    C = [[Fr(0)] * 3 for _ in range(3)]
    C[a][b] = C[b][a] = Fr(1)
    B = [[sum(inv3(M)[r][c] * C[c][d] for c in range(3)) for d in range(3)] for r in range(3)]
    return [x for p in mach.X for x in mv(B, p)]


def analyze(H, J, rigid):
    """Exact test of H restricted to N = ker J. Returns a dict of facts."""
    N = [[Fr(x) for x in v] for v in nullspace_rank(J)[0]]
    HN = [matvec(H, v) for v in N]
    Hn = [[sum(u[a] * w[a] for a in range(len(u))) for w in HN] for u in N]
    rank, psd = rank_and_psd(Hn)
    return {"dim_N": len(N), "J_rank": len(J) - len(nullspace_rank([list(r) for r in zip(*J)])[0]),
            "rank": rank, "nullity": len(N) - rank, "psd": psd,
            "rigid_in_N": all(all(sum(r[a] * v[a] for a in range(len(v))) == 0 for r in J) for v in rigid),
            "rigid_in_kernel": all(all(x == 0 for x in matvec(H, v)) for v in rigid)}


def strictly_stable(f):
    """PD modulo rigid motions: PSD, kernel on N is exactly the 6 rigid motions."""
    return f["psd"] and f["nullity"] == 6 and f["rigid_in_N"] and f["rigid_in_kernel"] and f["J_rank"] == 6
