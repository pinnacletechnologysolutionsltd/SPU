"""Focused review of PHY-R3 before REL-1 relies on it. Run: python3 -B -I research/rel1/review_phy_r3.py

Independence here is of METHOD and CODE PATH, not of author (the same agent wrote PHY-R3):
  1. second variation from direct energy evaluation + exact 5-point stencil (no Hessian formula);
  2. positive-definiteness modulo rigid motions by a rigid-penalty LDL (not the nullity argument);
  3. kernels re-run through REL-1's own counted LDL/nullspace, cross-checked with PHY-R1's;
  4. mutants of the formula must fail check 1; Hooke is only numerically corroborated (Decimal).
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "phy_r3"))
sys.path.insert(0, HERE)
import hessian as Hs   # noqa: E402  (the object under review)
import exact as X      # noqa: E402
from field import rank_and_psd  # noqa: E402

A = Hs.A
MACH = Hs.model.Machine()
E, P0 = MACH.E, MACH.X
IDN = [[Fr(int(a == b)) for b in range(3)] for a in range(3)]
M1 = ((Fr(1), Fr(3, 5), Fr(0)), (Fr(3, 5), Fr(1), Fr(0)), (Fr(0), Fr(0), Fr(1)))
A1 = [[Fr(1), Fr(3, 5), Fr(0)], [Fr(0), Fr(4, 5), Fr(0)], [Fr(0), Fr(0), Fr(1)]]
STATES = ((IDN, IDN), (M1, A1))


def coords(Am):
    return [[sum(Am[r][c] * p[c] for c in range(3)) for r in range(3)] for p in P0]


def lagrangian(x, Rs, q):
    """First-principles squared-law energy + strut reaction terms, no derivatives taken."""
    kap, tot = A.SQUARED["C"], Fr(0)
    for (i, j, t), R, qe in zip(E, Rs, q):
        Q = sum((x[i][k] - x[j][k]) ** 2 for k in range(3))
        tot += kap / 4 * (Q - R) ** 2 if t == "C" else qe / 2 * (Q - 16)
    return tot


def stencil(Am, Mt, eps, s_scale=1):
    x0 = coords(Am)
    Qs = A.member_quadrances(MACH, Mt)
    Rs, q = A.rest_squared(Qs, MACH), A.target_densities(MACH)
    de = [[sum(Am[r][c] * eps[3 * i + c] for c in range(3)) for r in range(3)] for i in range(12)]
    f = {s: lagrangian([[x0[i][k] + s * de[i][k] for k in range(3)] for i in range(12)], Rs, q)
         for s in (-2, -1, 0, 1, 2)}
    d1 = (f[-2] - 8 * f[-1] + 8 * f[1] - f[2]) / 12
    d2 = (-f[2] + 16 * f[1] - 30 * f[0] + 16 * f[-1] - f[-2]) / 12
    return d1, d2     # exact for polynomials of degree <= 4


def eps_set():
    return [[Fr(((7 * i + 3 * a + s) % 5) - 2, 3) for i in range(12) for a in range(3)] for s in (0, 1, 2, 3)]


def check_formula(s_of):
    for Mt, Am in STATES:
        H, _ = Hs.build(MACH, Mt, s_of(Mt))
        for e in eps_set():
            d1, d2 = stencil(Am, Mt, e)
            if d1 != 0 or d2 != Hs.qform(H, e):
                return False
    return True


def penalty_ldl(Mt):
    """H|N + sum r r^T (r = rigid motions in N-coordinates) is PD iff H is PD modulo rigid."""
    H, J = Hs.build(MACH, Mt, Hs.stiffness(MACH, Mt, "squared"))
    ops = X.Ops()
    N, piv = X.nullspace(J, ops)
    free = [c for c in range(36) if c not in piv]
    HN = [Hs.matvec(H, v) for v in N]
    Hn = [[sum(u[a] * w[a] for a in range(36)) for w in HN] for u in N]
    rig = [[v[c] for c in free] for v in Hs.rigid_basis(MACH, Mt)]
    pen = [[Hn[a][b] + sum(r[a] * r[b] for r in rig) for b in range(len(N))] for a in range(len(N))]
    k_rank, _ = X.ldl(Hn, ops)
    ker, _ = X.nullspace(Hn, ops)
    return {"dimN": len(N), "nullity_ldl": len(N) - k_rank, "kernel_dim": len(ker),
            "penalised_rank": X.ldl(pen, ops)[0], "penalised_psd": X.ldl(pen, ops)[1],
            "phy_r1_agrees": rank_and_psd([row[:] for row in Hn]) == X.ldl(Hn, ops)}


def hooke_numeric():
    """Decimal corroboration (NOT exact): d2 of the Hooke Lagrangian vs the closed-form form."""
    getcontext().prec = 80
    Mt, Am = M1, A1
    x0 = coords(Am)
    Qs = A.member_quadrances(MACH, Mt)
    Rs, q = A.rest_hooke(Qs, MACH), A.target_densities(MACH)
    e = eps_set()[1]
    de = [[sum(Am[r][c] * e[3 * i + c] for c in range(3)) for r in range(3)] for i in range(12)]
    D = lambda v: Decimal(v.numerator) / Decimal(v.denominator)
    k, h = D(A.HOOKE["C"]), Decimal(10) ** -20

    def L(s):
        tot = Decimal(0)
        for (i, j, t), R, qe in zip(E, Rs, q):
            Q = sum((D(x0[i][a] + 0) - D(x0[j][a]) + s * (D(de[i][a]) - D(de[j][a]))) ** 2 for a in range(3))
            tot += (k / 2) * (Q.sqrt() - D(R).sqrt()) ** 2 if t == "C" else D(qe) / 2 * (Q - 16)
        return tot
    d2 = (L(h) - 2 * L(Decimal(0)) + L(-h)) / (h * h)
    H, _ = Hs.build(MACH, Mt, Hs.stiffness(MACH, Mt, "hooke"))
    return abs(d2 - D(Hs.qform(H, e))) / abs(d2) < Decimal(10) ** -30


def review():
    out = {}
    out["formula_exact_squared"] = check_formula(lambda Mt: Hs.stiffness(MACH, Mt, "squared"))
    out["mutant_s_equals_kappa_killed"] = not check_formula(
        lambda Mt: [A.SQUARED["C"] if t == "C" else Fr(0) for *_, t in E])
    out["mutant_hooke_formula_for_squared_killed"] = not check_formula(
        lambda Mt: Hs.stiffness(MACH, Mt, "hooke"))
    out["states"] = [penalty_ldl(Mt) for Mt, _ in STATES]
    om = Hs.fixture.stress_matrix(A.target_densities(MACH), E, 12)
    r, psd = X.ldl(om, X.Ops())
    out["omega"] = {"rank": r, "psd": psd, "P_in_kernel": all(
        X.dot(row, [Fr(p[k]) for p in P0], X.Ops()) == 0 for row in om for k in range(3))}
    out["hooke_numeric_corroboration"] = hooke_numeric()
    return out


if __name__ == "__main__":
    r = review()
    print(r)
    assert r["formula_exact_squared"] and r["mutant_s_equals_kappa_killed"]
    assert r["mutant_hooke_formula_for_squared_killed"] and r["hooke_numeric_corroboration"]
    for s in r["states"]:
        assert s["dimN"] == 30 and s["nullity_ldl"] == 6 and s["kernel_dim"] == 6
        assert s["penalised_rank"] == 30 and s["penalised_psd"] and s["phy_r1_agrees"]
    assert r["omega"] == {"rank": 8, "psd": True, "P_in_kernel": True}
    print("PASS PHY-R3 review (squared law exact; Hooke numeric only)")
