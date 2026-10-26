"""H2 tests: identities, classification, enumeration and negative controls.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/h2_hex/test_h2.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import algebra as A                      # noqa: E402
import experiment as X                   # noqa: E402

PTS = X.patch(6)
EIS = {(1, -1): 3, (2, 0): 4, (3, 1): 7}
SQ3 = A.SQRT3


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def test_embedding_and_quadrance():
    for p in PTS:
        check(A.from_cart(A.to_cart(p)) == p, f"round trip {p}")
        check(A.quadrance(A.to_cart(p)) == A.Q3(F(A.e_norm(p))), f"Q==N {p}")
    check(A.from_cart((A.Q3(F(1, 2)), A.ZERO)) is None, "x=1/2,y=0 is not on L")


def test_eisenstein_two_derivations_agree():
    for z in list(EIS) + [(1, 1)]:
        m = A.eis_matrix(z)
        for v in PTS:
            check(A.apply(m, A.to_cart(v)) == A.to_cart(A.e_mul(z, v)), f"{z}*{v}")


def test_eisenstein_norm_index_and_scale():
    for z, n in EIS.items():
        c = X.classify(A.eis_matrix(z))
        check(c["kind"] == "sublattice_similarity", f"{z} kind {c}")
        check(c["index"] == n and A.e_norm(z) == n, f"{z} index {c['index']}")
        check(c["scale2"] == A.Q3(F(n)), f"{z} scale^2")
        check(X.residue_index(z, PTS) == n, f"{z} residue count")
    c = X.classify(A.eis_matrix((1, 1)))
    check(c["kind"] == "lattice_automorphism" and c["index"] == 1, "unit 1+w")


def test_eisenstein_inverse_defined_on_image_only():
    for z, n in EIS.items():
        m, zc = A.eis_matrix(z), A.e_conj(z)
        inv = A.compose(A.scale_matrix(A.Q3(F(1, n))), A.eis_matrix(zc))
        check(A.compose(inv, m) == A.IDENT, f"{z} inverse over Q(w)")
        back = [A.from_cart(A.apply(inv, A.to_cart(p))) for p in PTS]
        in_zl = [all(c % n == 0 for c in A.e_mul(p, zc)) for p in PTS]
        check([b is not None for b in back] == in_zl, f"{z} inverse on zL only")
        check(X.classify(inv)["kind"] != "lattice_automorphism", f"{z} inv")


def test_rot30_identities():
    (c, ms), (s, c2) = X.R30
    check(c == c2 and c == A.Q3(F(0), F(1, 2)) and s == A.Q3(F(1, 2)), "cos,sin")
    check(ms == -s, "rotation form")
    check(X.rot_power(12) == A.IDENT, "R^12 = I")
    check(all(X.rot_power(k) != A.IDENT for k in range(1, 12)), "order exactly 12")
    check(A.compose(X.R30, X.R30_INV) == A.IDENT, "Cayley(-t) is inverse")
    check(X.rot_power(2) == A.eis_matrix((1, 1)), "R30^2 = multiply by 1+w")
    check(A.compose(A.scale_matrix(SQ3), X.R30_INV) == A.eis_matrix((1, -1)),
          "1-w = sqrt3 * R(-30)")
    check(A.compose(A.scale_matrix(SQ3), X.R30) == A.eis_matrix((2, 1)),
          "2+w = sqrt3 * R(+30)")
    c = X.classify(X.R30)
    check(c["kind"] == "euclidean_rotation_not_lattice", f"R30 kind {c}")


def test_cayley_composition_is_not_pell_power():
    t = X.U_INV
    t60 = A.tan_half_compose(t, t)
    check(t60 == A.Q3(F(0), F(1, 3)), "tan 30 = sqrt3/3")
    check(A.cayley_rotation(t60) == X.rot_power(2), "composed parameter")
    check(t * t != t60, "u^-2 is not the 60-degree parameter")


def test_pell_is_algebraic_dilation():
    for name, k in (("pell_u", X.U), ("pell_u_inv", X.U_INV)):
        c = X.classify(X.OPERATORS[name])
        check(c["kind"] == "algebraic_dilation_not_lattice", f"{name} {c}")
        check(not c["scale2"].is_rational(), f"{name} scale^2 irrational")
        check(k.norm() == 1, f"{name} field norm 1 (AOR/Pell identity holds)")
    check(A.compose(X.OPERATORS["pell_u"], X.OPERATORS["pell_u_inv"]) == A.IDENT,
          "Pell inverse exact")
    p = A.ONE
    for n in range(1, 9):
        p = p * X.U
        check(p.norm() == 1 and (p * p).s != 0, f"u^{n}: norm 1, u^2n irrational")


def test_pell_meets_lattice_only_at_origin():
    for name in ("pell_u", "pell_u_inv"):
        e = X.enumerate_patch(X.OPERATORS[name], PTS)
        check(e["nonzero_images_on_lattice"] == 0, f"{name} {e}")
        check(e["images_on_lattice"] == 1, f"{name} only origin")
    run = X.run(4)
    check(run["pell_rotated_any_lattice_preserving"] is False, "Pell after R^k")


def test_negative_controls():
    # 1. A rational dilation (2) must be accepted: the membership test can say yes.
    check(X.classify(A.scale_matrix(A.Q3(F(2))))["kind"] == "sublattice_similarity",
          "control: scale 2 preserves L")

    # 2. A mutant membership test that reads only the "expected" component of
    #    each coordinate (rational part of x, sqrt3 part of y) must be fooled
    #    by Pell; the real test must not be.
    def mutant(p):
        x, y = p
        return A.from_cart((A.Q3(x.r), A.Q3(F(0), y.s)))
    check(X.classify(X.OPERATORS["pell_u"], mutant)["kind"] != "algebraic_dilation_not_lattice",
          "mutant membership misclassifies Pell (sensitivity)")
    # 3. A sign-flipped "rotation" must fail closure.
    (c, ms), (s, _) = X.R30
    bad = ((c, s), (s, c))
    m = A.IDENT
    for _ in range(12):
        m = A.compose(bad, m)
    check(m != A.IDENT, "control: wrong-sign rotation does not close")
    # 4. Residue counting without the modulus overcounts.
    keys = {tuple(A.e_mul(p, A.e_conj((3, 1)))) for p in PTS}
    check(len(keys) > 7, "control: un-reduced keys overcount")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} test groups")
