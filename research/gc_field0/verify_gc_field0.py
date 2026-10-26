#!/usr/bin/env python3
"""GC-FIELD-0: A4 lattice, Z[phi] coefficients, phi/sqrt5 bases, fivefold plane.

Software-only, exact (int / Fraction). No floats anywhere. Run:
    python3 research/gc_field0/verify_gc_field0.py
Prints PASS/FAIL per check; exit 1 on any failure.

Notation: Z[phi] element a+b*phi is the integer pair (a, b), phi^2 = phi + 1.
"""
import itertools
import sys
from fractions import Fraction as F

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


# ---- Z[phi] pair arithmetic ------------------------------------------------
def phi_mul(x, y):
    a, b = x
    c, d = y
    p, q, r = a * c, b * d, (a + b) * (c + d)  # 3 integer products (Karatsuba)
    return (p + q, r - p)


def phi_mul4(x, y):
    a, b = x
    c, d = y
    return (a * c + b * d, a * d + b * c + b * d)  # 4 integer products


def phi_scale(x):  # multiply by phi: integer swap-and-add
    a, b = x
    return (b, a + b)


def phi_conj(x):  # phi -> 1 - phi  (sqrt5 -> -sqrt5)
    a, b = x
    return (a + b, -b)


def phi_norm(x):
    a, b = x
    return a * a + a * b - b * b


# ---- phi <-> sqrt5 basis ---------------------------------------------------
def phi_to_s5(x):  # a + b*phi = (2a+b)/2 + (b/2) sqrt5
    a, b = x
    return (F(2 * a + b, 2), F(b, 2))


def s5_to_phi(x):  # x + y sqrt5 = (x - y) + 2y phi  (rational pair)
    u, v = x
    return (u - v, 2 * v)


def s5_mul(x, y):
    return (x[0] * y[0] + 5 * x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def in_zphi(x):  # (x,y) in Q(sqrt5) lies in Z[phi] iff both phi-coords are integers
    a, b = s5_to_phi(x)
    return a.denominator == 1 and b.denominator == 1


def in_zs5(x):
    return x[0].denominator == 1 and x[1].denominator == 1


# ---- A4 lattice -----------------------------------------------------------
def dot(u, v):
    return sum(x * y for x, y in zip(u, v))


def cyc(v, k=1):  # cyclic shift of 5 coordinates
    return tuple(v[(i - k) % 5] for i in range(5))


def sumzero_vectors(lo=-2, hi=2):
    return [v for v in itertools.product(range(lo, hi + 1), repeat=5) if sum(v) == 0]


ROOTS = [v for v in sumzero_vectors() if dot(v, v) == 2]
SIMPLE = [tuple((1 if i == k else -1 if i == k + 1 else 0) for i in range(5)) for k in range(4)]


def lat_coords(v):  # integer coordinates of sum-zero v in simple-root basis
    c, acc = [], 0
    for k in range(4):
        acc += v[k]
        c.append(acc)
    return tuple(c)


def from_coords(c):
    return tuple(sum(c[k] * SIMPLE[k][i] for k in range(4)) for i in range(5))


# ---- fivefold plane: z(v) = sum v_k w^k in Z[w] = Z[x]/(Phi5) ---------------
def zw_from(v):  # reduce polynomial sum v_k x^k modulo x^4+x^3+x^2+x+1
    c = list(v)
    top = c[4]
    return tuple(c[k] - top for k in range(4))  # x^4 = -(1+x+x^2+x^3)


def zw_mul(p, q):
    prod = [0] * 7
    for i in range(4):
        for j in range(4):
            prod[i + j] += p[i] * q[j]
    for k in range(6, 3, -1):  # reduce x^k, k>=4, using x^5 = 1 and Phi5
        c = prod[k]
        prod[k] = 0
        for t in range(4):
            prod[k - 4 + t] -= c
    return tuple(prod[:4])


def zw_conj(p):  # w -> w^4 = w^-1
    full = [0] * 5
    for k in range(4):
        full[(-k) % 5] += p[k]
    return zw_from(tuple(full))


def plane_quadrance_x2(v):
    """2*|z1(v)|^2 as a Z[phi] pair, via Z[w] arithmetic.

    z*conj(z) is real: c0 + c1 (w+w^4) + c2 (w^2+w^3); w+w^4 = phi-1, w^2+w^3 = -phi.
    """
    z = zw_from(v)
    n = zw_mul(z, zw_conj(z))
    # real element c0 + c1(w+w^4) + c2(w^2+w^3) reduces to (c0-c1, 0, c2-c1, c2-c1) in basis 1,w,w^2,w^3
    assert n[1] == 0 and n[2] == n[3], "z*conj(z) must be real"
    # value = c0 + c1(phi-1) - c2*phi = (c0-c1) + (c1-c2) phi
    return (2 * n[0], -2 * n[2])


def plane_quadrance_x2_closed(v):
    s1 = 2 * sum(v[j] * v[(j + 1) % 5] for j in range(5))
    s2 = 2 * sum(v[j] * v[(j + 2) % 5] for j in range(5))
    return (2 * dot(v, v) - s1, s1 - s2)


def main():
    # ---- A4: rational/integer Gram, order-five cyclic permutation ----------
    check("A4 has 20 roots", len(ROOTS) == 20)
    cartan = [[dot(SIMPLE[i], SIMPLE[j]) for j in range(4)] for i in range(4)]
    check("A4 Gram in simple-root basis is the integer Cartan matrix",
          cartan == [[2, -1, 0, 0], [-1, 2, -1, 0], [0, -1, 2, -1], [0, 0, -1, 2]])
    vs = sumzero_vectors()
    check("cyclic shift preserves sum-zero lattice and 4D quadrance",
          all(sum(cyc(v)) == 0 and dot(cyc(v), cyc(v)) == dot(v, v) for v in vs))
    check("cyclic shift has order exactly 5 on A4",
          all(cyc(v, 5) == v for v in vs) and any(cyc(v, 1) != v for v in vs))
    cmat = [lat_coords(cyc(s)) for s in SIMPLE]  # rows = images of simple roots
    check("cyclic shift is an integer 4x4 matrix in the simple-root basis",
          all(isinstance(x, int) for r in cmat for x in r))
    check("lattice coordinate map round-trips", all(from_coords(lat_coords(v)) == v for v in vs))

    # ---- exhaustive A4 automorphisms (integer, Gram-preserving) -----------
    autos = []
    for img in itertools.product(ROOTS, repeat=4):
        if all(dot(img[i], img[j]) == cartan[i][j] for i in range(4) for j in range(i, 4)):
            autos.append(img)
    check("Aut(A4 lattice) has exactly 240 elements (= S5 x {+-1})", len(autos) == 240)

    def apply(img, v):
        c = lat_coords(v)
        return tuple(sum(c[k] * img[k][i] for k in range(4)) for i in range(5))

    test_vs = [v for v in vs if dot(v, v) <= 4]
    planar = [m for m in autos
              if all(plane_quadrance_x2(apply(m, v)) == plane_quadrance_x2(v) for v in test_vs)]
    check("only 20 of the 240 automorphisms preserve the planar quadrance (D5 x +-1)", len(planar) == 20)
    check("NEG: 220 automorphisms preserve 4D quadrance but change planar quadrance",
          len(autos) - len(planar) == 220)

    # ---- order-5 in rank 2 impossible; rank 4 needed -----------------------
    I2 = ((1, 0), (0, 1))

    def mm(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)) for i in range(2))

    found = []
    for e in itertools.product(range(-6, 7), repeat=4):
        M = ((e[0], e[1]), (e[2], e[3]))
        P = M
        for _ in range(4):
            P = mm(P, M)
        if P == I2 and M != I2:
            found.append(M)
    check("NEG: no integer 2x2 matrix (|entries|<=6) has order 5", not found)

    # ---- Z[phi] arithmetic -------------------------------------------------
    grid = [(a, b) for a in range(-4, 5) for b in range(-4, 5)]
    check("phi_scale is multiplication by (0,1)... i.e. phi*(a+b phi) = b+(a+b)phi",
          all(phi_scale(x) == phi_mul(x, (0, 1)) for x in grid))
    check("Karatsuba (3 products) equals 4-product multiplication",
          all(phi_mul(x, y) == phi_mul4(x, y) for x in grid for y in grid))
    check("phi^n = (F(n-1), F(n))", all(_pow_phi(n) == _fib_pair(n) for n in range(1, 25)))
    check("norm is multiplicative and phi is a unit (norm -1)",
          phi_norm((0, 1)) == -1 and all(
              phi_norm(phi_mul(x, y)) == phi_norm(x) * phi_norm(y) for x in grid for y in grid))
    check("conjugation is a ring automorphism",
          all(phi_conj(phi_mul(x, y)) == phi_mul(phi_conj(x), phi_conj(y)) for x in grid for y in grid))
    check("NEG: a non-unit has no inverse in Z[phi] (norm 4 for x=2)", abs(phi_norm((2, 0))) == 4)

    # ---- phi <-> sqrt5 basis ----------------------------------------------
    check("phi->sqrt5->phi round trip exact",
          all(s5_to_phi(phi_to_s5(x)) == (F(x[0]), F(x[1])) for x in grid))
    check("sqrt5-basis multiplication agrees with phi-basis multiplication",
          all(s5_to_phi(s5_mul(phi_to_s5(x), phi_to_s5(y))) == tuple(map(F, phi_mul(x, y)))
              for x in grid for y in grid))
    check("Z[phi] in sqrt5 basis has half-integer coordinates iff b is odd",
          all(in_zs5(phi_to_s5(x)) == (x[1] % 2 == 0) for x in grid))
    check("Z[sqrt5] embeds in Z[phi] (with the b-even check above: index 2)",
          all(in_zphi((F(u), F(v))) for u in range(-3, 4) for v in range(-3, 4)))
    check("NEG: (1/2,1/2) sqrt5-pair is phi (in Z[phi]); (1/2,0) is not",
          in_zphi((F(1, 2), F(1, 2))) and not in_zphi((F(1, 2), F(0))))

    # ---- planar quadrance: intrinsic 4D vs projected 2D ---------------------
    check("planar quadrance via Z[w] arithmetic == closed form",
          all(plane_quadrance_x2(v) == plane_quadrance_x2_closed(v) for v in vs))
    check("TRACE IDENTITY: 4D quadrance = (2a+b)/5 where 2|z1|^2 = a + b phi",
          all(F(2 * plane_quadrance_x2(v)[0] + plane_quadrance_x2(v)[1], 5) == dot(v, v) for v in vs))
    w = (1, -1, 0, 0, 0)
    pq = plane_quadrance_x2(w)
    check("NEG: planar quadrance of a root is irrational (b != 0): witness (1,-1,0,0,0)",
          pq[1] != 0 and dot(w, w) == 2)
    # sin(72deg)^2 = (5+sqrt5)/8 is not a square in Q(sqrt5): its norm 5/16 is not a rational square
    n = F(5 + 0, 8) ** 2 - 5 * F(1, 8) ** 2
    check("NEG: planar Cartesian y-coordinate needs sin72 outside Q(sqrt5) (norm 5/16 not a square; sin^2 72 = (5+sqrt5)/8 is hand-derived, not checked here)",
          n == F(5, 16) and not _is_square_frac(n))

    # ---- phi scaling as an integer matrix on A4 -----------------------------
    def T(v):
        return tuple(v[i] + v[(i - 1) % 5] + v[(i + 1) % 5] for i in range(5))

    check("T = I + C + C^-1 maps A4 to A4", all(sum(T(v)) == 0 for v in vs))
    check("T^2 = T + I on A4 (T acts as phi)",
          all(tuple(a - b - c for a, b, c in zip(T(T(v)), T(v), v)) == (0,) * 5 for v in vs))
    check("T scales planar quadrance by phi^2 exactly",
          all(plane_quadrance_x2(T(v)) == phi_mul(phi_mul((0, 1), (0, 1)), plane_quadrance_x2(v)) for v in vs))
    check("NEG: T is not a 4D isometry/similarity (quadrance ratio not constant)",
          len({F(dot(T(v), T(v)), dot(v, v)) for v in vs if dot(v, v)}) > 1)

    print("\nFAILED: %d" % len(FAILS) if FAILS else "\nALL PASS")
    return 1 if FAILS else 0


def _pow_phi(n):
    r = (1, 0)
    for _ in range(n):
        r = phi_scale(r)
    return r


def _fib_pair(n):
    f = [0, 1]
    while len(f) <= n:
        f.append(f[-1] + f[-2])
    return (f[n - 1], f[n])


def _is_square_frac(q):
    from math import isqrt
    return isqrt(q.numerator) ** 2 == q.numerator and isqrt(q.denominator) ** 2 == q.denominator


if __name__ == "__main__":
    sys.exit(main())
