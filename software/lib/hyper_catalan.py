"""Hyper-Catalan series oracle — subdigon counts and the soft polynomial formula.

Implements Wildberger & Rubine, "A Hyper-Catalan Series Solution to
Polynomial Equations, and the Geode", Am. Math. Monthly 132:5 (2025)
383-402, DOI 10.1080/00029890.2025.2460966 (local copy in Theory/):

  Theorem 5:  C_m = (E_m - 1)! / ((V_m - 1)! * m!)  — hyper-Catalan numbers,
              computed exactly in Z (no modular factorial pitfalls; p | n!
              for n >= p, so reduction mod M31 happens after, not during).
  Theorem 4:  the soft polynomial formula — the equation
              0 = c0 - c1*x + c2*x^2 + c3*x^3 + ...   (note the minus on c1)
              has series root  x = sum_m C_m * c0^(V-1) * c1^(-E) * c^m.

Evaluation is ring-generic: over Fractions the truncated series is a
numerical approximant (bootstrappable, per the paper's Section 8); over a
jet ring with nilpotent perturbations the truncation is EXACT — every term
of high enough face weight vanishes identically, which is the only mode in
which the series "solves" anything over a finite field.

Type vectors are tuples m = (m2, m3, m4, ...): index i counts the
(i+3)-gon faces, so m[0] = triangles, m[1] = quadrilaterals, ...
"""

from itertools import product
from math import factorial


def faces(m):
    """F_m = sum m_k — equation (4)."""
    return sum(m)


def edges(m):
    """E_m = 1 + 2*m2 + 3*m3 + ... — equation (5)."""
    return 1 + sum((i + 2) * mi for i, mi in enumerate(m))


def vertices(m):
    """V_m = 2 + m2 + 2*m3 + ... — equation (6), via Euler V - E + F = 1."""
    return 2 + sum((i + 1) * mi for i, mi in enumerate(m))


def hyper_catalan(m):
    """C_m = (E_m - 1)! / ((V_m - 1)! * m2! * m3! * ...), exact in Z."""
    num = factorial(edges(m) - 1)
    den = factorial(vertices(m) - 1)
    for mi in m:
        den *= factorial(mi)
    q, r = divmod(num, den)
    assert r == 0, f"hyper-Catalan quotient not integral for m={m}"
    return q


def hyper_catalan_binomial(m):
    """Sub-multinomial form of Theorem 5: C_m = multinomial(E; V-1, m) / E.

    Independent of hyper_catalan() up to factorial bookkeeping — used as a
    cross-check in the oracle tests.
    """
    e = edges(m)
    num = factorial(e)
    den = factorial(vertices(m) - 1)
    for mi in m:
        den *= factorial(mi)
    q, r = divmod(num, den * e)
    assert r == 0, f"binomial form not integral for m={m}"
    return q


def enumerate_types(num_vars, cap, weight):
    """All type tuples m of length num_vars with weight(m) <= cap.

    weight is any monotone per-face measure — faces() for series order,
    vertices()/edges() for the paper's layerings, or a nilpotency bound.
    Includes the null type (0, ..., 0).
    """
    ranges = []
    for i in range(num_vars):
        # Walk each axis until weight exceeds cap — weight may be affine
        # (e.g. vertices(m)-1 = 1 + sum), so cap//weight(unit) under-counts.
        k = 0
        while True:
            probe = tuple(0 if j != i else k + 1 for j in range(num_vars))
            if weight(probe) > cap:
                break
            k += 1
        ranges.append(range(k + 1))
    return [m for m in product(*ranges) if weight(m) <= cap]


def soft_poly_root(c, types, ring):
    """Truncated series root of 0 = c[0] - c[1]*x + c[2]*x^2 + ... (Thm 4).

    c        : list of ring elements in the paper's sign convention.
    types    : which type vectors m to include (caller controls truncation;
               pass a nilpotency-complete set for exact jet-ring roots).
    ring     : dict with 'add', 'mul', 'zero', 'one', 'from_int', 'inv'.

    Requires c[1] invertible — the paper's own c1 != 0 caveat, i.e. the
    simple-root condition. Terms touching absent coefficients are skipped
    (equivalent to those c_k being zero).
    """
    add, mul = ring["add"], ring["mul"]

    def power(base, n):
        acc = ring["one"]
        for _ in range(n):
            acc = mul(acc, base)
        return acc

    c1_inv = ring["inv"](c[1])
    x = ring["zero"]
    for m in types:
        if any(mi and i + 2 >= len(c) for i, mi in enumerate(m)):
            continue
        term = ring["from_int"](hyper_catalan(m))
        term = mul(term, power(c[0], vertices(m) - 1))
        term = mul(term, power(c1_inv, edges(m)))
        for i, mi in enumerate(m):
            term = mul(term, power(c[i + 2], mi))
        x = add(x, term)
    return x


def fraction_ring():
    """Ring adapter over exact rationals, for numeric approximation mode."""
    from fractions import Fraction
    return {
        "add": lambda a, b: a + b,
        "mul": lambda a, b: a * b,
        "zero": Fraction(0),
        "one": Fraction(1),
        "from_int": Fraction,
        "inv": lambda a: 1 / a,
    }
