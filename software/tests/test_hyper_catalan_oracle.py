#!/usr/bin/env python3
"""Hyper-Catalan series oracle — verification against Wildberger & Rubine 2025.

Golden vectors come straight from the published paper (local copy in
Theory/): the Bi-Tri array (Section 8), the Geode factorization
(Theorem 12 / Section 11), the OEIS layerings (little Schroeder A001003,
Riordan A005043), and the Wallis cubic bootstrap (Section 8).

Then the constructive hardware claim is proven in the only mode where the
series is exact over a finite field: nilpotent (jet ring) evaluation.
Random jet-perturbed quintics over A31 are solved by the truncated soft
polynomial formula and verified by back-substitution to be EXACTLY zero
in J = A31[eps]/(eps^3) — followed by a measured MAC/tower comparison
against the classical Newton-Hensel lift.

Usage:
    python3 software/tests/test_hyper_catalan_oracle.py
"""

import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.a31_field import (
    MULT_CYCLES,
    OpCount,
    P,
    TOWER_CYCLES,
    a31_mul,
    a31_norm,
    a31_sub,
)
from lib.hyper_catalan import (
    edges,
    enumerate_types,
    faces,
    fraction_ring,
    hyper_catalan,
    hyper_catalan_binomial,
    soft_poly_root,
    vertices,
)
from lib.jet_ring import (
    JET_ONE,
    JET_ZERO,
    jet_add,
    jet_eval_poly,
    jet_from_a31,
    jet_inv,
    jet_mul,
    jet_neg,
    jet_ring_ops,
    jet_sub,
)

random.seed(0x6E0DE)

CHECKS = 0
FAILURES = 0


def check(cond, msg):
    global CHECKS, FAILURES
    CHECKS += 1
    if cond:
        print(f"  ok  {msg}")
    else:
        FAILURES += 1
        print(f"  FAIL {msg}")


# ── 1. Hyper-Catalan numbers vs the published tables ─────────────────────

print("Hyper-Catalan numbers (Theorem 5):")

CATALAN = [1, 1, 2, 5, 14, 42, 132, 429, 1430]
check(all(hyper_catalan((n,)) == CATALAN[n] for n in range(9)),
      "C[n] collapses to the Catalan numbers (A000108)")

FUSS = [1, 1, 3, 12, 55, 273, 1428]
check(all(hyper_catalan((0, n)) == FUSS[n] for n in range(7)),
      "C[0,n] gives the quadrilateral Fuss numbers (A001764)")

# Bi-Tri array, paper Section 8 (rows m2 = 0..7, cols m3 = 0..5)
BI_TRI = [
    [1, 1, 3, 12, 55, 273],
    [1, 5, 28, 165, 1001, 6188],
    [2, 21, 180, 1430, 10920, 81396],
    [5, 84, 990, 10010, 92820, 813960],
    [14, 330, 5005, 61880, 678300, 6864396],
    [42, 1287, 24024, 352716, 4476780, 51482970],
    [132, 5005, 111384, 1899240, 27457584, 354323970],
    [429, 19448, 503880, 9806280, 159352050, 2283421140],
]
check(all(hyper_catalan((m2, m3)) == BI_TRI[m2][m3]
          for m2 in range(8) for m3 in range(6)),
      "full 8x6 Bi-Tri array matches the paper")

check(hyper_catalan((2, 0, 1)) == 28,
      "C[2,0,1] = 28 (Figure 3: two triangles + one pentagon)")

all_small = enumerate_types(5, 4, faces)
check(all(hyper_catalan(m) == hyper_catalan_binomial(m) for m in all_small),
      f"factorial and sub-multinomial forms agree ({len(all_small)} types)")

check(all(sum((-1) ** j * hyper_catalan((d - j, j)) for j in range(d + 1)) == 0
          for d in range(1, 7)),
      "alternating cross-diagonal sums vanish (paper Section 8)")

print("Layerings (paper Sections 10-11):")
by_vertex = enumerate_types(7, 5, lambda m: vertices(m) - 2)
schroeder = [sum(hyper_catalan(m) for m in by_vertex if vertices(m) == v)
             for v in range(2, 8)]
check(schroeder == [1, 1, 3, 11, 45, 197],
      "vertex layering counts = little Schroeder numbers (A001003)")
by_edge = enumerate_types(7, 8, lambda m: edges(m) - 1)  # gons up to 9 (t8)
riordan = [sum(hyper_catalan(m) for m in by_edge if edges(m) == e)
           for e in range(1, 10)]
check(riordan == [1, 0, 1, 1, 3, 6, 15, 36, 91],
      "edge layering counts = Riordan numbers (A005043)")


# ── 2. The Geode factorization (Theorem 12) ───────────────────────────────

print("Geode factorization S - 1 = S1 * G:")

NV = 5  # variables t2..t6


def padd(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
        if out[k] == 0:
            del out[k]
    return out


def pshift(p, mono, c):
    return {tuple(x + y for x, y in zip(k, mono)): v * c for k, v in p.items()}


S1 = {tuple(1 if j == i else 0 for j in range(NV)): 1 for i in range(NV)}


def divide_by_s1(p):
    """Exact multivariate division by S1 (lex order, t2 most significant).

    lead(S1 * h) always contains t2, so exact divisibility guarantees no
    stall. Returns the quotient, or None if the division is not exact.
    """
    r = dict(p)
    q = {}
    while r:
        lead = max(r)
        if lead[0] == 0:
            return None
        qm = (lead[0] - 1,) + lead[1:]
        qc = r[lead]
        q[qm] = q.get(qm, 0) + qc
        r = padd(r, pshift(S1, qm, -qc))
    return q


layers = {}
for m in enumerate_types(NV, 4, faces):
    if faces(m) > 0:
        layers.setdefault(faces(m), {})[m] = hyper_catalan(m)

G1 = divide_by_s1(layers[2])
G2 = divide_by_s1(layers[3])
G3 = divide_by_s1(layers[4])
check(layers[1] == S1 and None not in (G1, G2, G3),
      "S1 divides every face layer exactly through f^4")


def mono(*m2m3m4):
    return tuple(list(m2m3m4) + [0] * (NV - len(m2m3m4)))


check(G1[mono(1)] == 2 and G1[mono(0, 1)] == 3 and G1[mono(0, 0, 1)] == 4,
      "Geode f1 layer: 2*t2 + 3*t3 + 4*t4 + ...")
check((G2[mono(2)], G2[mono(1, 1)], G2[mono(0, 2)],
       G2[mono(1, 0, 1)], G2[mono(0, 1, 1)], G2[mono(0, 0, 2)])
      == (5, 16, 12, 23, 33, 22),
      "Geode f2 layer matches (incl. G[1,0,1] = 23)")
check((G3[mono(3)], G3[mono(2, 1)], G3[mono(1, 2)], G3[mono(0, 3)])
      == (14, 70, 110, 55),
      "Geode f3 Bi-Tri slice: 14, 70, 110, 55")


# ── 3. Numeric mode over Q: the Wallis cubic with bootstrapping ───────────

print("Wallis cubic x^3 - 2x - 5 (paper Section 8, exact Fractions):")

FR = fraction_ring()
CUBIC_TYPES = enumerate_types(2, 3, faces)  # the paper's Q(t2,t3), F <= 3


def shifted_cubic(s):
    """Coefficients of f(x + s) for f = x^3 - 2x - 5, exact."""
    return [s ** 3 - 2 * s - 5, 3 * s ** 2 - 2, 3 * s, Fraction(1)]


root = Fraction(2)
first_k = None
for _ in range(3):
    a = shifted_cubic(root)
    k = soft_poly_root([a[0], -a[1], a[2], a[3]], CUBIC_TYPES, FR)
    if first_k is None:
        first_k = k
    root += k

check(abs(first_k - Fraction("0.0945345708")) < Fraction(1, 10 ** 9),
      "first pass reproduces the paper's K(-1,-10,6,1) = 0.0945345708")
check(abs(root - Fraction("2.0945514815423265915")) < Fraction(1, 10 ** 18),
      "3 bootstraps hit the true root to 19 published digits")


# ── 4. Jet ring J = A31[eps]/(eps^3) ─────────────────────────────────────

print("Jet ring (spu13_jet_mac / spu13_jet_inv model):")


def rand_a31():
    return tuple(random.randrange(P) for _ in range(4))


def rand_unit_a31():
    while True:
        z = rand_a31()
        if a31_norm(z) != 0:
            return z


ok_jet = True
for _ in range(30):
    j = (rand_unit_a31(), rand_a31(), rand_a31())
    inv, err = jet_inv(j)
    ok_jet &= not err and jet_mul(j, inv) == JET_ONE
check(ok_jet, "J * jet_inv(J) = 1 for 30 random unit jets")

SQRT15 = pow(15, (P + 1) // 4, P)
zd_jet = ((SQRT15, 0, 0, 1), rand_a31(), rand_a31())
check(jet_inv(zd_jet) == (None, True),
      "zero-divisor base component raises err_zero_divisor")


# ── 5. Exact quintic root-tracking over the jet ring ─────────────────────

print("Nilpotent series reversion (the exact mode over F_p):")

TIGHT_TYPES = enumerate_types(4, 2, lambda m: vertices(m) - 2)
WIDE_TYPES = enumerate_types(4, 3, faces)  # includes many higher terms
# Minimal nilpotency-complete set at eps^3: every term's order is at least
# V_m - 1 (the c0^(V-1) prefactor, c0 in (eps)), so only V - 1 <= 2 survives.
MIN_TYPES = enumerate_types(4, 1, lambda m: vertices(m) - 2)

# Regression (fixed 2026-07-08): affine weights like vertices(m)-1 carry a
# +1 offset, so the per-axis range pre-bound must walk the weight, not
# divide by it — otherwise (3,0,0,0) (weight 4) is silently dropped at eps^5
# and the series root is wrong there while eps^3 still passes.
AFFINE_TYPES = enumerate_types(4, 4, lambda m: vertices(m) - 1)
check((3, 0, 0, 0) in AFFINE_TYPES and len(AFFINE_TYPES) == 7,
      "eps^5 survivor set complete under affine weight (7 types incl. (3,0,0,0))")


def make_perturbed_quintic():
    """Random quintic over A31 with a planted base root x0, then every
    coefficient perturbed in the eps and eps^2 channels."""
    while True:
        base = [rand_a31() for _ in range(6)]
        x0 = rand_a31()
        acc, val = (1, 0, 0, 0), (0, 0, 0, 0)
        for b in base:
            val = tuple((v + m) % P for v, m in zip(val, a31_mul(b, acc)))
            acc = a31_mul(acc, x0)
        base[0] = a31_sub(base[0], val)  # plant: p_base(x0) = 0
        deriv = (0, 0, 0, 0)
        acc = (1, 0, 0, 0)
        for i in range(1, 6):
            term = a31_mul(base[i], acc)
            deriv = tuple((d + i * t) % P for d, t in zip(deriv, term))
            acc = a31_mul(acc, x0)
        if a31_norm(deriv) == 0:
            continue  # need a simple root: p'(x0) must be a unit
        coeffs = [(b, rand_a31(), rand_a31()) for b in base]
        return coeffs, x0


def taylor_shift(coeffs, s, ctr=None):
    """Coefficients of p(y + s) via repeated synthetic division, jet-exact."""
    c = [tuple(x) for x in coeffs]
    sj = jet_from_a31(s)
    for j in range(len(c) - 1):
        for i in range(len(c) - 2, j - 1, -1):
            c[i] = jet_add(c[i], jet_mul(c[i + 1], sj, ctr))
    return c


def series_root(coeffs, x0, types, ctr=None):
    b = taylor_shift(coeffs, x0, ctr)
    c = [b[0], jet_neg(b[1])] + b[2:]
    return soft_poly_root(c, types, jet_ring_ops(ctr))


def newton_root(coeffs, x0, ctr=None):
    y = jet_from_a31(x0)
    dcoeffs = [jet_mul(jet_from_a31((i, 0, 0, 0)), c)
               for i, c in enumerate(coeffs)][1:]
    for _ in range(2):
        num = jet_eval_poly(coeffs, y, ctr)
        dinv, err = jet_inv(jet_eval_poly(dcoeffs, y, ctr), ctr)
        assert not err
        y = jet_sub(y, jet_mul(num, dinv, ctr))
    return y


ok_exact = ok_vanish = ok_min = ok_newton = True
series_ops, min_ops, newton_ops = OpCount(), OpCount(), OpCount()
for _ in range(20):
    coeffs, x0 = make_perturbed_quintic()
    y = series_root(coeffs, x0, TIGHT_TYPES, series_ops)
    x = jet_add(jet_from_a31(x0), y)
    ok_exact &= jet_eval_poly(coeffs, x) == JET_ZERO
    ok_vanish &= series_root(coeffs, x0, WIDE_TYPES) == y
    ok_min &= series_root(coeffs, x0, MIN_TYPES, min_ops) == y
    ok_newton &= newton_root(coeffs, x0, newton_ops) == x
check(ok_exact,
      "20 perturbed quintics: series root is EXACTLY zero in the ring")
check(ok_vanish,
      f"all {len(WIDE_TYPES) - len(TIGHT_TYPES)} higher-weight terms vanish "
      "identically (nilpotency truncates the series exactly)")
check(ok_min,
      f"the {len(MIN_TYPES)}-term minimal nilpotency-complete set already "
      "gives the exact root")
check(ok_newton, "series root equals the Newton-Hensel lift (unique lift)")

print(f"\n== Cost per root (avg of 20, tower={TOWER_CYCLES}, "
      f"mult={MULT_CYCLES} cycles, naive per-term powers) ==")
for name, ops in (("closed form, 4-term set", series_ops),
                  ("closed form, minimal 2-term set", min_ops),
                  ("Newton-Hensel (2 iterations)", newton_ops)):
    print(f"  {name:<32} {ops.towers / 20:>4.1f} towers  "
          f"{ops.mults / 20:>6.1f} A31 mults  ~{ops.cycles() / 20:>6.1f} cyc")
check(series_ops.towers == 20 and min_ops.towers == 20
      and newton_ops.towers == 40,
      "closed form needs exactly 1 tower per root; Newton needs 2")


# ── Summary ───────────────────────────────────────────────────────────────

print(f"\n{CHECKS} checks, {FAILURES} failures")
if FAILURES == 0:
    print("ALL CHECKS PASS")
    sys.exit(0)
print("FAILURES PRESENT")
sys.exit(1)
