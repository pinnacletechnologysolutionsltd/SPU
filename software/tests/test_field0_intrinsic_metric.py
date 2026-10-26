#!/usr/bin/env python3
"""FIELD-0: which SPU geometry is intrinsically rational in its native basis?

Software-only dependency audit. Exact Fractions; Q(sqrt3) elements are (p, q)
pairs meaning p + q*sqrt3. Prints a three-way classification and asserts
every claim it makes, including negative controls.
"""

import itertools
import os
import sys
from fractions import Fraction as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

HALF = F(1, 2)


# --- tiny Q(sqrt3) -------------------------------------------------------
def smul(x, y):
    return (x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def sadd(x, y):
    return (x[0] + y[0], x[1] + y[1])


def mmul(A, B, mul=smul, add=sadd, zero=(F(0), F(0))):
    n = len(A)
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            acc = zero
            for k in range(n):
                acc = add(acc, mul(A[i][k], B[k][j]))
            row.append(acc)
        out.append(row)
    return out


def lift(M):
    return [[(F(x), F(0)) for x in r] for r in M]


def rmul(A, B):
    return mmul(A, B, lambda a, b: a * b, lambda a, b: a + b, F(0))


def tr(A):
    return [list(r) for r in zip(*A)]


def is_integer(M):
    return all(F(x).denominator == 1 for r in M for x in r)


# --- A2 (triangular lattice) --------------------------------------------
G = [[F(1), HALF], [HALF, F(1)]]
R60 = [[F(0), F(-1)], [F(1), F(1)]]
I2 = [[F(1), F(0)], [F(0), F(1)]]


def test_a2_integer_rotation():
    assert rmul(rmul(tr(R60), G), R60) == G, "R^T G R != G"
    P = I2
    for _ in range(6):
        P = rmul(P, R60)
    assert P == I2, "R^6 != I"
    P3 = rmul(rmul(R60, R60), R60)
    assert P3 == [[F(-1), F(0)], [F(0), F(-1)]]
    assert 1 - G[0][1] ** 2 == F(3, 4), "basis spread"


def test_a2_integer_isometry_group_is_d6():
    found = [
        M
        for e in itertools.product(range(-3, 4), repeat=4)
        for M in [[[F(e[0]), F(e[1])], [F(e[2]), F(e[3])]]]
        if rmul(rmul(tr(M), G), M) == G
    ]
    assert len(found) == 12, len(found)  # 6 rotations + 6 reflections
    assert sum(1 for M in found if M[0][0] * M[1][1] - M[0][1] * M[1][0] == 1) == 6


def cart_of(M):
    """Matrix M (in A2 lattice coordinates) re-expressed in Cartesian over Q(sqrt3).

    Basis columns: e1=(1,0), e2=(1/2, sqrt3/2).  C = B M B^-1.
    """
    s0, s1 = (F(0), F(0)), (F(0), F(1))
    B = [[(F(1), F(0)), (HALF, F(0))], [s0, (F(0), HALF)]]
    Binv = [[(F(1), F(0)), (F(0), F(-1, 3))], [s0, (F(0), F(2, 3))]]
    # check B*Binv = I
    assert mmul(B, Binv) == lift(I2)
    return mmul(mmul(B, lift(M)), Binv)


def test_a2_rotation_is_rational_in_lattice_basis_irrational_in_cartesian():
    C = cart_of(R60)
    assert any(x[1] != 0 for r in C for x in r), "expected sqrt3 in Cartesian R60"


def test_negative_control_345_rotation_needs_sqrt3_in_lattice_basis():
    """Cartesian-rational rotation (cos 3/5, sin 4/5): rational Gram, but its
    lattice-basis matrix is NOT rational."""
    c, s = F(3, 5), F(4, 5)
    Rc = lift([[c, -s], [s, c]])
    B = [[(F(1), F(0)), (HALF, F(0))], [(F(0), F(0)), (F(0), HALF)]]
    Binv = [[(F(1), F(0)), (F(0), F(-1, 3))], [(F(0), F(0)), (F(0), F(2, 3))]]
    M = mmul(mmul(Binv, Rc), B)
    assert any(x[1] != 0 for r in M for x in r), "3-4-5 rotation became rational"
    # its spread is nevertheless rational: s^2 = 16/25
    assert s * s == F(16, 25)
    # and 90 degrees likewise
    R90 = lift([[F(0), F(-1)], [F(1), F(0)]])
    M90 = mmul(mmul(Binv, R90), B)
    assert any(x[1] != 0 for r in M90 for x in r)


def test_rational_noninteger_a2_rotation_exists():
    """u = z/zbar, z = a + b*zeta (zeta = e^{i pi/3}): norm-1, rational, denominators N."""
    a, b = 2, 1
    N = a * a + a * b + b * b  # 7
    p, q = F(a * a - b * b, N), F(2 * a * b + b * b, N)
    M = [[p, -q], [q, p + q]]  # zeta^2 = zeta - 1
    assert rmul(rmul(tr(M), G), M) == G
    assert not is_integer(M) and {F(x).denominator for r in M for x in r} <= {1, 7}


# --- 3D Quadray / tetrahedral -------------------------------------------
E4 = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]


def test_quadray_gram_integer_and_matches_vm_form():
    for i, j in itertools.product(range(4), repeat=2):
        g = sum(x * y for x, y in zip(E4[i], E4[j]))
        assert g == (3 if i == j else -1)
    for v in itertools.product(range(-2, 3), repeat=4):
        cart = [sum(v[k] * E4[k][d] for k in range(4)) for d in range(3)]
        qc = sum(x * x for x in cart)
        qq = sum((v[i] - v[j]) ** 2 for i in range(4) for j in range(i + 1, 4))
        assert qc == qq
    # Cartesian embedding of the tetrahedral lattice is integer: no sqrt3 at all
    assert all(isinstance(x, int) for e in E4 for x in e)


def test_cube_rotations_are_signed_quadray_permutations():
    rots = []
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            sgn = 1
            for i in range(3):
                for j in range(i + 1, 3):
                    sgn *= 1 if perm[i] < perm[j] else -1
            if sgn * sg[0] * sg[1] * sg[2] == 1:
                rots.append((perm, sg))
    assert len(rots) == 24
    for perm, sg in rots:
        for e in E4:
            img = tuple(sg[d] * e[perm[d]] for d in range(3))
            hits = [(k, s) for k, f in enumerate(E4) for s in (1, -1)
                    if tuple(s * x for x in f) == img]
            assert len(hits) == 1, (perm, sg)  # image is +/- a basis quadray


def test_thirds_rotation_about_body_diagonal_is_rational():
    """60 deg about (1,1,1): axis 1/sqrt3 cancels sin's sqrt3 -> rational /3 entries."""
    u = (1, 1, 1)
    c, su = HALF, tuple(HALF * x for x in u)  # sin*u = (1/2)(1,1,1)
    k = (1 - c) / 3
    R = [[c * (i == j) + k * u[i] * u[j] + (0 if i == j else
          (-su[3 - i - j] if (j - i) % 3 == 1 else su[3 - i - j]))
          for j in range(3)] for i in range(3)]
    assert rmul(tr(R), R) == [[F(int(i == j)) for j in range(3)] for i in range(3)]
    P = R
    for _ in range(5):
        P = rmul(P, R)
    assert P == [[F(int(i == j)) for j in range(3)] for i in range(3)]
    assert not is_integer(R) and all(F(x).denominator == 3 or F(x).denominator in (1, 2)
                                     for r in R for x in r)


# --- current SPU operations ---------------------------------------------
def test_pell_rotor_is_integer_but_not_euclidean():
    from spu_vm import QuadrayVector, RationalSurd as RS
    # (a,b) pair multiplication = integer matrix [[a,3b],[b,a]] preserving x^2-3y^2
    for a, b in [(2, 1), (7, 4), (26, 15)]:
        assert a * a - 3 * b * b == 1
    v = QuadrayVector(RS(3), RS(1), RS(0), RS(0))
    w = v.rotate()
    qv, qw = v.quadrance(), w.quadrance()
    assert (qv.a, qv.b) == (24, 0)
    # Euclidean Quadray quadrance scales by u^2 = 7+4*sqrt3, NOT preserved
    assert (qw.a, qw.b) == (24 * 7, 24 * 4)


CLASSES = {
    "intrinsically rational (integer/rational, no sqrt3)": [
        "A2 quadrance/inner product/spread; 60-deg A2 rotation (integer matrix)",
        "Quadray quadrance/Gram; tetrahedral+octahedral rotations (signed perms)",
        "thirds (/3) circulant rotations about body diagonals",
    ],
    "rational only with extra state / other basis": [
        "arbitrary rational-angle rotations: 3-4-5 is Cartesian-rational, A2-irrational",
        "non-lattice A2 rotations (z/zbar): rational with denominators (norm N)",
    ],
    "genuinely needs Q(sqrt3)": [
        "one basis exposing both 60-deg and 90-deg/3-4-5 rotations",
        "60-deg A2 rotation expressed in Cartesian (test_a2_rotation_is_rational_in_lattice_basis...)",
    ],
}


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    for k, v in CLASSES.items():
        print("\n" + k)
        for x in v:
            print("  -", x)
