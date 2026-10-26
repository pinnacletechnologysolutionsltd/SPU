"""PHY-R3 tests: exact tangent stability of the PHY-R2 equilibrium family.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/phy_r3/test_phy_r3.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hessian as Hs                      # noqa: E402
from field import QF, nullspace_rank, rank_and_psd, sqrt_in_field  # noqa: E402

A = Hs.A
MACH = Hs.model.Machine()
E, X = MACH.E, MACH.X
CABLES = [k for k, (*_, t) in enumerate(E) if t == "C"]


def M(a, b, c):
    return ((1, a, b), (a, 1, c), (b, c, 1))


M0 = M(0, 0, 0)
M1 = M(Fr(3, 5), 0, 0)
M2 = M(Fr(1, 3), Fr(1, 4), Fr(1, 5))
SAMPLES = [Fr(0), Fr(7, 15), Fr(25, 39), Fr(40, 51), Fr(5, 6), Fr(1)]


def at(target, t):
    return tuple(tuple(Fr(v) for v in r) for r in A.path_metric(target, t))


def equilibrium(Mt, law):
    """Static equilibrium for the law's rest schedule (PHY-R2 code, unchanged)."""
    st, h = MACH.transform(Mt)
    if st != "COMMITTED":
        return st, h, False
    Qs = A.member_quadrances(MACH, Mt)
    tgt = A.target_densities(MACH)
    if law == "squared":
        R = A.rest_squared(Qs, MACH)
        dens = A.densities_squared(Qs, R, E)
        return st, h, dens == tgt and A.relational_equilibrium(MACH, h, dens)
    R = A.rest_hooke(Qs, MACH)
    return st, h, A.hooke_matches(Qs, R, MACH) and A.relational_equilibrium(MACH, h, tgt)


def certify(Mt, law):
    st, h, eq = equilibrium(Mt, law)
    if not eq:
        return {"verdict": "NOT_EQUILIBRIUM"}
    H, J = Hs.build(MACH, Mt, Hs.stiffness(MACH, Mt, law))
    f = Hs.analyze(H, J, Hs.rigid_basis(MACH, Mt))
    f["verdict"] = "STRICT_STABLE" if Hs.strictly_stable(f) else "NOT_STRICT"
    return f


# ---- independent derivation: s^2 coefficient of the Lagrangian along a line -------------
def series(Aq, Mt, law, eps):
    """(s^1, s^2) coefficients of L(x + s delta), computed from the energies themselves."""
    n = len(X)
    x = [[sum(Aq[r][c] * p[c] for c in range(3)) for r in range(3)] for p in X]
    de = [[sum(Aq[r][c] * eps[3 * i + c] for c in range(3)) for r in range(3)] for i in range(n)]
    Qs = A.member_quadrances(MACH, Mt)
    R = (A.rest_squared if law == "squared" else A.rest_hooke)(Qs, MACH)
    c1 = c2 = Fr(0)
    for (i, j, t), Q, Rq, q in zip(E, Qs, R, A.target_densities(MACH)):
        d = [x[i][k] - x[j][k] for k in range(3)]
        D = [de[i][k] - de[j][k] for k in range(3)]
        dD, DD = sum(u * v for u, v in zip(d, D)), sum(u * u for u in D)
        assert sum(u * u for u in d) == Q
        if t == "S":                      # mu (Q(s) - 16) with mu = q/2
            c1, c2 = c1 + q * dD, c2 + q * DD / 2
        elif law == "squared":            # kappa/4 (Q(s) - R)^2
            k = A.SQUARED["C"]
            c1, c2 = c1 + k / 4 * 2 * (Q - Rq) * 2 * dD, c2 + k / 4 * ((2 * dD) ** 2 + 2 * (Q - Rq) * DD)
        else:                             # k/2 Q [(1+u) - 2c sqrt(1+u) + c^2], l0 = c l
            c = sqrt_in_field(QF(Rq / Q, Fr(0), 1)).a
            a_, b_ = dD / Q, DD / Q
            k = A.HOOKE["C"]
            c1 += k / 2 * Q * (2 * a_ - 2 * c * a_)
            c2 += k / 2 * Q * (b_ - 2 * c * (b_ / 2 - a_ * a_ / 2))
    return c1, c2


def eps_patterns():
    return [[Fr(((7 * i + 3 * a + s) % 5) - 2, 3) for i in range(12) for a in range(3)] for s in (0, 1, 2)]


def test_hessian_matches_independent_energy_series():
    Aq = [[Fr(1), Fr(3, 5), Fr(0)], [Fr(0), Fr(4, 5), Fr(0)], [Fr(0), Fr(0), Fr(1)]]
    assert all(sum(Aq[k][a] * Aq[k][b] for k in range(3)) == M1[a][b] for a in range(3) for b in range(3))
    for Mt, Aq_ in ((M0, [[Fr(int(a == b)) for b in range(3)] for a in range(3)]), (M1, Aq)):
        for law in ("squared", "hooke"):
            H, _ = Hs.build(MACH, Mt, Hs.stiffness(MACH, Mt, law))
            for eps in eps_patterns():
                c1, c2 = series(Aq_, Mt, law, eps)
                assert c1 == 0, (law, "equilibrium: first variation must vanish")
                assert c2 == Hs.qform(H, eps) / 2, (law, "closed-form Hessian != energy series")


def test_rigid_motions_are_in_the_kernel_and_tangent_space():
    for Mt in (M0, M1, M2, at(M2, Fr(25, 39))):
        for law in ("squared", "hooke"):
            f = certify(Mt, law)
            assert f["rigid_in_N"] and f["rigid_in_kernel"] and f["J_rank"] == 6 and f["dim_N"] == 30


def test_reference_and_noncongruent_state_are_strictly_stable_under_both_laws():
    for Mt in (M0, M1):
        for law in ("squared", "hooke"):
            f = certify(Mt, law)
            assert f["verdict"] == "STRICT_STABLE", (law, f)
            assert f["psd"] and f["nullity"] == 6 and f["rank"] == 24


def test_path_samples_both_targets_both_laws():
    for target in (M1, M2):
        for t in SAMPLES:
            for law in ("squared", "hooke"):
                assert certify(at(target, t), law)["verdict"] == "STRICT_STABLE", (target, t, law)


def test_whole_path_proof_lemmas():
    q = A.target_densities(MACH)
    om = Hs.fixture.stress_matrix(q, E, 12)
    rank, psd = rank_and_psd(om)
    assert psd and 12 - rank == 4                        # Omega PSD, nullity 4, independent of t
    for k in range(3):                                   # ker Omega contains 1 and the coordinate columns
        col = [Fr(p[k]) for p in X]
        assert all(sum(om[r][c] * col[c] for c in range(12)) == 0 for r in range(12))
    rows = []                                            # conic condition on the 24 CABLES alone
    for k in CABLES:
        i, j, _ = E[k]
        d = [X[i][a] - X[j][a] for a in range(3)]
        rows.append([Fr(d[0] ** 2), Fr(2 * d[0] * d[1]), Fr(2 * d[0] * d[2]),
                     Fr(d[1] ** 2), Fr(2 * d[1] * d[2]), Fr(d[2] ** 2)])
    assert len(nullspace_rank(rows)[1]) == 6
    assert A.SQUARED["C"] > 0 and A.HOOKE["C"] > max(q[k] for k in CABLES)   # s_c > 0 for every t
    for t in SAMPLES + [Fr(1, 1000)]:                    # M(t) PD => Q_c > 0 => Hooke s_c = (k - q)/Q > 0
        Mt = at(M2, t)
        assert all(s > 0 for s in (Hs.stiffness(MACH, Mt, "hooke")[k] for k in CABLES))
        assert all(s == 1 for s in (Hs.stiffness(MACH, Mt, "squared")[k] for k in CABLES))


def test_laws_agree_on_sign_and_differ_in_stiffness():
    for t in (Fr(0), Fr(1, 2), Fr(1)):
        Mt = at(M1, t)
        vals = {}
        for law in ("squared", "hooke"):
            H, _ = Hs.build(MACH, Mt, Hs.stiffness(MACH, Mt, law))
            vals[law] = [Hs.qform(H, Hs.shear_mode(MACH, Mt, a, b)) for a, b in ((0, 1), (0, 2), (1, 2))]
            assert all(v > 0 for v in vals[law])
        assert vals["squared"] != vals["hooke"]
    h0 = Hs.build(MACH, M0, Hs.stiffness(MACH, M0, "hooke"))[0]
    h1 = Hs.build(MACH, at(M1, 1), Hs.stiffness(MACH, at(M1, 1), "hooke"))[0]
    s = lambda Mt, H: Hs.qform(H, Hs.shear_mode(MACH, Mt, 0, 1))
    assert s(M0, h0) != s(at(M1, 1), h1)


def test_negative_controls_reject_for_the_intended_reason():
    # N1: prestress only (s = 0): PSD but not strict; kernel = rigid + the 3 family-tangent shears
    H, J = Hs.build(MACH, M1, [Fr(0)] * len(E))
    f = Hs.analyze(H, J, Hs.rigid_basis(MACH, M1))
    assert f["psd"] and f["nullity"] == 9 and not Hs.strictly_stable(f)
    for a, b in ((0, 1), (0, 2), (1, 2)):
        assert all(x == 0 for x in Hs.matvec(H, Hs.shear_mode(MACH, M1, a, b)))
    # N2: negative cable stiffness (Hooke k < q, i.e. negative rest length: refused by PHY-R2)
    s = Hs.stiffness(MACH, M1, "hooke", k=Fr(1, 2))
    assert all(s[k] < 0 for k in CABLES)
    H, J = Hs.build(MACH, M1, s)
    f = Hs.analyze(H, J, Hs.rigid_basis(MACH, M1))
    w = Hs.shear_mode(MACH, M1, 0, 1)
    assert not f["psd"] and Hs.qform(H, w) < 0
    # N3: stale rest parameters (solved at t=0, used at t=1) are not an equilibrium: refused first
    Mt = at(M1, 1)
    Qs0, Qs1 = A.member_quadrances(MACH, M0), A.member_quadrances(MACH, Mt)
    dens = A.densities_squared(Qs1, A.rest_squared(Qs0, MACH), E)
    assert dens != A.target_densities(MACH)
    st, h = MACH.transform(Mt)
    assert not A.relational_equilibrium(MACH, h, dens)
    # N4: omit the strut reaction: rigid rotations leave the kernel, so the Hessian is wrong
    H, J = Hs.build(MACH, M1, Hs.stiffness(MACH, M1, "squared"), with_struts=False)
    assert not Hs.analyze(H, J, Hs.rigid_basis(MACH, M1))["rigid_in_kernel"]
    # N5: conic test rejects a cable subset whose directions span fewer than 6 quadratic forms
    rows = []
    for k in CABLES[:5]:
        i, j, _ = E[k]
        d = [X[i][a] - X[j][a] for a in range(3)]
        rows.append([Fr(d[0] ** 2), Fr(2 * d[0] * d[1]), Fr(2 * d[0] * d[2]),
                     Fr(d[1] ** 2), Fr(2 * d[1] * d[2]), Fr(d[2] ** 2)])
    assert len(nullspace_rank(rows)[1]) < 6


def test_field_and_state_refusals_are_preserved():
    assert MACH.transform(M(Fr(1), 0, 0)) == ("REFUSED", "NOT_POSITIVE_DEFINITE")
    assert MACH.transform(M(Fr(6, 5), 0, 0)) == ("REFUSED", "NOT_POSITIVE_DEFINITE")
    assert certify(M(Fr(1), 0, 0), "squared")["verdict"] == "NOT_EQUILIBRIUM"   # refused state: no certificate
    assert MACH.observe(MACH.transform(M2)[1], 1)[0] == "OUT_OF_FIELD"          # M2 is relational-only


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} PHY-R3 test groups")
