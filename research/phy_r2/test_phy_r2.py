"""PHY-R2 tests: exact cable actuation along a path of static equilibria.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/phy_r2/test_phy_r2.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import actuation as A      # noqa: E402

model, fixture = A.model, A.fixture
MACH = model.Machine()
E = MACH.E


def M(a, b, c):
    return ((1, a, b), (a, 1, c), (b, c, 1))


M1 = M(Fr(3, 5), 0, 0)                       # PHY-R1 admitted, non-congruent, Q-materialisable
M2 = M(Fr(1, 3), Fr(1, 4), Fr(1, 5))         # relational-only endpoint
SAMPLES = [Fr(0), Fr(7, 15), Fr(25, 39), Fr(40, 51), Fr(5, 6), Fr(1)]


def state(Mt):
    st, h = MACH.transform(Mt)
    assert st == "COMMITTED", Mt
    return h, A.member_quadrances(MACH, Mt)


def test_conventions_recovered():
    q = MACH.certs[0]["stress"]
    assert sum(t == "C" for *_, t in E) == 24 and sum(t == "S" for *_, t in E) == 6
    assert all((v == 1) if t == "C" else (v == Fr(-3, 2)) for v, (*_, t) in zip(q, E))


def test_path_admission_is_proved_on_whole_interval():
    for target in (M1, M2):
        st, info = A.admit_path(MACH, target)
        assert st == "ADMITTED", info
        # PD on [0,1] follows from convexity of the PD cone (proof in FINDINGS);
        # the cable bound uses the affine-in-t quadrances checked below
        assert info["cable_qmin"] > A.LAM / A.SQUARED["C"]
    for t in SAMPLES:                               # sampled confirmation of the proof
        assert MACH.transform(A.path_metric(M2, t))[0] == "COMMITTED"
    # cable quadrances along the path are affine in t (exactly)
    q0, q1 = (A.member_quadrances(MACH, A.path_metric(M1, s)) for s in (0, 1))
    for t in SAMPLES:
        qt = A.member_quadrances(MACH, A.path_metric(M1, t))
        assert qt == [(1 - t) * a + t * b for a, b in zip(q0, q1)]
    assert len(set(q1[i] for i, (*_, t) in enumerate(E) if t == "C")) > 1, "non-congruent"


def test_equilibrium_both_laws_relational_and_coordinates():
    for target in (M1, M2):
        for t in SAMPLES:
            Mt = A.path_metric(target, t)
            h, Qs = state(Mt)
            Rh, Rs = A.rest_hooke(Qs, MACH), A.rest_squared(Qs, MACH)
            dh, ds = A.densities_hooke(Qs, Rh, E), A.densities_squared(Qs, Rs, E)
            assert dh == ds == A.target_densities(MACH), (t, "induced stress")
            assert A.hooke_matches(Qs, Rh, MACH)
            assert all(r > 0 for r in Rh) and all(r > 0 for r in Rs)
            # cables taut: rest quadrance strictly below current quadrance
            assert all(R < Q for R, Q, (*_, ty) in zip(Rs, Qs, E) if ty == "C")
            assert all(R < Q for R, Q, (*_, ty) in zip(Rh, Qs, E) if ty == "C")
            assert A.relational_equilibrium(MACH, h, ds), t
            for d in (1, 3, 5):
                status, pts = MACH.observe(h, d)
                if status == "EXACT":
                    assert A.coordinate_equilibrium(pts, dh, E, d), (t, d)
                    assert A.coordinate_equilibrium(pts, ds, E, d), (t, d)
                    if d in (1, 5):
                        assert fixture.oracle_verdict(pts, E, d) == "BALANCED"


def test_strut_reaction_constant_and_compressive():
    rh = rs = None
    for t in SAMPLES:
        _, Qs = state(A.path_metric(M1, t))
        Rh, Rs = A.rest_hooke(Qs, MACH), A.rest_squared(Qs, MACH)
        sh = {R for R, (*_, ty) in zip(Rh, E) if ty == "S"}
        ss = {R for R, (*_, ty) in zip(Rs, E) if ty == "S"}
        assert len(sh) == len(ss) == 1, "all struts share one rest parameter"
        rh, rs = rh or sh, rs or ss
        assert sh == rh and ss == rs, "strut rest parameters constant along the path"
    assert rh == {16 * (1 + Fr(3, 2) / 40) ** 2} and rs == {16 + Fr(3, 2) / 5}
    assert min(rh) > 16 and min(rs) > 16, "struts held in compression"


def test_laws_are_not_equivalent():
    _, Q0 = state(A.path_metric(M1, 0))
    _, Q1 = state(A.path_metric(M1, 1))
    c = 0                                    # first cable
    # different rest schedules for the same equilibrium tension
    assert A.rest_hooke(Q1, MACH)[c] / Q1[c] == A.rest_hooke(Q0, MACH)[c] / Q0[c]
    assert Q1[c] - A.rest_squared(Q1, MACH)[c] == Q0[c] - A.rest_squared(Q0, MACH)[c]
    assert A.rest_hooke(Q1, MACH)[c] != A.rest_squared(Q1, MACH)[c]
    # tangent stiffness dT/dl at t=0: Hooke k vs squared kappa(3Q - R)
    k_sq = A.SQUARED["C"] * (3 * Q0[c] - A.rest_squared(Q0, MACH)[c])
    assert A.HOOKE["C"] == 4 and k_sq == 7
    # cross-law control: Hooke rest schedule under the squared law. The unique
    # self-stress needs all cable densities equal. At t=0 (all cable Q equal) the
    # cable densities stay uniform, so only the strut prestress level is off;
    # at t=1 they become non-uniform, so no strut setting can restore equilibrium.
    for Qs, s in ((Q0, 0), (Q1, 1)):
        h = MACH.transform(A.path_metric(M1, s))[1]
        d = A.densities_squared(Qs, A.rest_hooke(Qs, MACH), E)
        cables = {v for v, (*_, ty) in zip(d, E) if ty == "C"}
        assert not A.relational_equilibrium(MACH, h, d), s
        assert (len(cables) == 1) is (s == 0), (s, cables)


def test_negative_controls():
    h1, Q1 = state(A.path_metric(M1, 1))
    _, Q0 = state(A.path_metric(M1, 0))
    # stale rest parameters (solved for t=0, used at t=1)
    assert not A.relational_equilibrium(MACH, h1, A.densities_squared(Q1, A.rest_squared(Q0, MACH), E))
    assert not A.hooke_matches(Q1, A.rest_hooke(Q0, MACH), MACH)
    # slack cable: rest quadrance >= current quadrance carries no force
    Rs = A.rest_squared(Q1, MACH)
    Rs[0] = Q1[0]
    d = A.densities_squared(Q1, Rs, E)
    assert d[0] == 0 and not A.relational_equilibrium(MACH, h1, d)
    Rh = A.rest_hooke(Q1, MACH)
    Rh[0] = Q1[0] * Fr(9, 4)                    # l0 = 1.5 l: slack, exact square ratio
    dh = A.densities_hooke(Q1, Rh, E)
    assert dh is not None and dh[0] == 0, "slack Hooke cable carries no force"
    assert not A.relational_equilibrium(MACH, h1, dh)
    assert not A.hooke_matches(Q1, Rh, MACH)
    # invalid cable parameters
    old = dict(A.SQUARED)
    A.SQUARED["C"] = Fr(1, 4)                    # LAM/kappa = 4 > min cable quadrance 18/5
    try:
        assert A.admit_path(MACH, M1) == ("REFUSED", "INVALID_CABLE_SQUARED")
    finally:
        A.SQUARED.update(old)
    oldh = dict(A.HOOKE)
    A.HOOKE["C"] = Fr(1)                         # LAM*q/k = 1: zero rest length
    try:
        assert A.admit_path(MACH, M1) == ("REFUSED", "INVALID_CABLE_HOOKE")
        try:
            A.rest_hooke(Q1, MACH)
            raise AssertionError("expected INVALID_CABLE")
        except ValueError:
            pass
    finally:
        A.HOOKE.update(oldh)
    # singular / indefinite endpoints
    assert A.admit_path(MACH, M(Fr(1), 0, 0)) == ("REFUSED", "NOT_POSITIVE_DEFINITE")
    assert A.admit_path(MACH, M(Fr(6, 5), 0, 0)) == ("REFUSED", "NOT_POSITIVE_DEFINITE")


def test_incorrect_certificate_reuse():
    X = MACH.X
    for frac in (Fr(1, 2), Fr(1)):               # midpoint and end of a strut-translation path
        P = [list(p) for p in X]
        for n in (0, 1):
            P[n][2] += frac
        st, h = MACH.adopt_coordinates(P)
        assert MACH.reuse(h) == ("REFUSED", "DEPENDENCY_CHANGED")
        assert MACH.reuse(h, skip_dependency_check=True)[0] == "REUSED"   # mutant
        assert not A.relational_equilibrium(MACH, h, A.target_densities(MACH))
        pts = MACH.observe(h, 1)[1]
        assert not A.coordinate_equilibrium(pts, A.target_densities(MACH), E, 1)


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} PHY-R2 test groups")
