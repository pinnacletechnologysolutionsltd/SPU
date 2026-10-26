"""PHY-R1: metric-state tensegrity — reference, perturbation, restoration, controls.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/phy_r1/test_phy_r1.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr
from itertools import product

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture                 # noqa: E402
import model                   # noqa: E402
import reference as R          # noqa: E402


def M(a, b, c):
    return ((1, a, b), (a, 1, c), (b, c, 1))


MACH = model.Machine()
X, E = MACH.X, MACH.E
REF = R.check(MACH.pair_quadrances(0), E)

# metric, expected materialisation per field d in {1, 3, 5}
FAMILY = {
    "m12=3/5 (Pythagorean)": (M(Fr(3, 5), 0, 0), {1: True, 3: True, 5: True}),
    "m12=1/2 (needs sqrt3)": (M(Fr(1, 2), 0, 0), {1: False, 3: True, 5: False}),
    "m12=2/3 (needs sqrt5)": (M(Fr(2, 3), 0, 0), {1: False, 3: False, 5: True}),
    "general (1/3,1/4,1/5)": (M(Fr(1, 3), Fr(1, 4), Fr(1, 5)), {1: False, 3: False, 5: False}),
}


def test_reference_state():
    q = MACH.certs[0]["stress"]
    struts = {v for v, (_, _, t) in zip(q, E) if t == "S"}
    cables = {v for v, (_, _, t) in zip(q, E) if t == "C"}
    assert len(E) == 30 and cables == {Fr(1)} and struts == {Fr(-3, 2)}, "2:-3 stress"
    ss = fixture.super_stability(X, E, list(q))
    assert ss == {"omega_psd": True, "omega_nullity": 4, "conic_ok": True,
                  "super_stable": True}, ss
    assert R.balanced(REF), REF
    assert fixture.oracle_verdict(MACH.observe(0, 1)[1], E, 1) == "BALANCED"


def test_metric_family_balanced_noncongruent():
    for name, (mm, fields) in FAMILY.items():
        st, h = MACH.transform(mm)
        assert st == "COMMITTED", name
        assert MACH.reuse(h) == ("REUSED", h), name
        r = R.check(MACH.pair_quadrances(h), E)
        assert R.balanced(r), (name, r)
        assert r["quadrance_multiset"] != REF["quadrance_multiset"], f"{name} congruent"
        for d, expect in fields.items():
            status, pts = MACH.observe(h, d)
            assert (status == "EXACT") == expect, (name, d, status)
            if status == "EXACT":
                # materialised coordinates reproduce the metric quadrances exactly
                D = MACH.pair_quadrances(h)
                for i, j, _ in E:
                    qq = sum(((pts[i][k] - pts[j][k]) * (pts[i][k] - pts[j][k])
                              for k in range(3)), fixture.QF.of(0, d))
                    assert qq == fixture.QF.of(D[i][j], d), (name, d, i, j)
                if d in (1, 5):
                    assert fixture.oracle_verdict(pts, E, d) == "BALANCED", (name, d)


def test_restoration():
    st, h = MACH.transform(M(Fr(3, 5), 0, 0))
    st2, h2 = MACH.transform(M(0, 0, 0))
    assert st2 == "COMMITTED" and h2 != 0 and h2 > h, "restoration is a new handle"
    assert MACH.states[h2].M == MACH.states[0].M
    assert R.check(MACH.pair_quadrances(h2), E) == REF, "restored state equals reference"
    assert h2 not in MACH.certs, "certificates are not inherited without REUSE"
    assert MACH.reuse(h2) == ("REUSED", h2)
    assert R.check(MACH.pair_quadrances(h), E) != REF, "old handle keeps its geometry"


def test_refusals_preserve_current_state():
    for mm, reason in [(M(Fr(6, 5), 0, 0), "NOT_POSITIVE_DEFINITE"),
                       (M(Fr(1), 0, 0), "NOT_POSITIVE_DEFINITE"),       # singular
                       (((Fr(9, 8), 0, 0), (0, 1, 0), (0, 0, 1)), "STRUT_LENGTH_CHANGED"),
                       (M(Fr(1, 2 ** 32), 0, 0), "COEFFICIENT_BOUND"),
                       (((1, Fr(1, 2), 0), (0, 1, 0), (0, 0, 1)), "NOT_SYMMETRIC")]:
        before = (len(MACH.states), MACH.current)
        assert MACH.transform(mm) == ("REFUSED", reason), reason
        assert (len(MACH.states), MACH.current) == before, f"{reason} mutated state"


def test_non_affine_control():
    for shift in ((1, 0, 0), (0, 0, 1)):          # move one strut rigidly
        P = [list(p) for p in X]
        for n in (0, 1):
            P[n] = [P[n][k] + shift[k] for k in range(3)]
        st, h = MACH.adopt_coordinates(P)
        r = R.check(MACH.pair_quadrances(h), E)
        assert r["strut_lengths_ok"] and not r["equilibrium"], (shift, r)
        assert MACH.reuse(h) == ("REFUSED", "DEPENDENCY_CHANGED")
        # mutant: carry certificates without checking the dependency
        assert MACH.reuse(h, skip_dependency_check=True)[0] == "REUSED"
        assert not R.balanced(r), "independent check must catch the mutant"
        assert fixture.oracle_verdict(MACH.observe(h, 1)[1], E, 1) != "BALANCED"


def test_integer_coordinate_reach():
    """Integer A with unit-norm columns (strut lengths kept) -> only M = I."""
    cols = [v for v in product(range(-2, 3), repeat=3) if sum(c * c for c in v) == 1]
    assert len(cols) == 6
    count = 0
    for A in product(cols, repeat=3):
        Mt = [[sum(A[i][k] * A[j][k] for k in range(3)) for j in range(3)] for i in range(3)]
        if MACH.transform(Mt)[0] == "COMMITTED":
            count += 1
            assert Mt == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    assert count == 48, count


def test_bounded_sweep():
    vals = [Fr(-1, 2), Fr(-1, 4), Fr(0), Fr(1, 4), Fr(1, 2)]
    pd = bal = 0
    classes = set()
    for a, b, c in product(vals, repeat=3):
        st, h = MACH.transform(M(a, b, c))
        if st == "COMMITTED":
            pd += 1
            r = R.check(MACH.pair_quadrances(h), E)
            bal += R.balanced(r)
            classes.add(r["quadrance_multiset"])
    assert (pd, bal) == (121, 121), (pd, bal)
    assert len(classes) == 14, len(classes)    # lower bound on congruence classes


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} PHY-R1 test groups")
