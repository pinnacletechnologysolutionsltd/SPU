"""Jet ring oracle — J = A31[eps]/(eps^3), the RTL's local jet algebra.

Python behavioral model of the jet arithmetic implemented in RTL:

  spu13_jet_mac.v — jet multiply: (a0 + a1*eps + a2*eps^2)(b0 + b1*eps + ...)
                    truncated at eps^3, 6 base multiplies.
  spu13_jet_inv.v — jet inverse via the geometric series for local rings:
                    J^-1 = c0^-1 - eps*(c1*c0^-2) + eps^2*(c1^2*c0^-3 - c2*c0^-2)
                    (1 Conjugate Reduction Tower run + 6 multiplies, with the
                    zero-divisor check on c0 -> err_zero_divisor).

A jet is a 3-tuple of A31 elements (c0, c1, c2). Base-field costs are
tracked through the same OpCount as a31_field, so jet workloads can be
compared against tower/MAC budgets directly.
"""

from lib.a31_field import (
    A31_ONE,
    A31_ZERO,
    a31_add,
    a31_mul,
    a31_neg,
    a31_sub,
    a31_tower_inv,
    m31,
)

JET_ZERO = (A31_ZERO, A31_ZERO, A31_ZERO)
JET_ONE = (A31_ONE, A31_ZERO, A31_ZERO)


def jet_from_a31(x):
    return (x, A31_ZERO, A31_ZERO)


def jet_from_int(n):
    return ((m31(n), 0, 0, 0), A31_ZERO, A31_ZERO)


def jet_add(a, b):
    return tuple(a31_add(x, y) for x, y in zip(a, b))


def jet_sub(a, b):
    return tuple(a31_sub(x, y) for x, y in zip(a, b))


def jet_neg(a):
    return tuple(a31_neg(x) for x in a)


def jet_mul(a, b, ctr=None):
    """Truncated product at eps^3 — 6 base multiplies, as in spu13_jet_mac."""
    a0, a1, a2 = a
    b0, b1, b2 = b
    return (
        a31_mul(a0, b0, ctr),
        a31_add(a31_mul(a0, b1, ctr), a31_mul(a1, b0, ctr)),
        a31_add(a31_mul(a0, b2, ctr),
                a31_add(a31_mul(a1, b1, ctr), a31_mul(a2, b0, ctr))),
    )


def jet_inv(j, ctr=None):
    """Geometric-series inverse, multiply-for-multiply spu13_jet_inv.v.

    Returns (inverse, err_zero_divisor). Costs 1 tower + 6 multiplies.
    """
    c0, c1, c2 = j
    m0, flags_v = a31_tower_inv(c0, ctr)
    if flags_v:
        return None, True
    sq = a31_mul(m0, m0, ctr)            # c0^-2
    cu = a31_mul(sq, m0, ctr)            # c0^-3
    h1 = a31_mul(c1, sq, ctr)            # c1*c0^-2
    s1 = a31_mul(c1, c1, ctr)            # c1^2
    t1 = a31_mul(s1, cu, ctr)            # c1^2*c0^-3
    t2 = a31_mul(c2, sq, ctr)            # c2*c0^-2
    return (m0, a31_neg(h1), a31_sub(t1, t2)), False


def jet_eval_poly(coeffs, x, ctr=None):
    """Horner evaluation of sum coeffs[i]*x^i; coeffs[0] is the constant."""
    val = coeffs[-1]
    for c in reversed(coeffs[:-1]):
        val = jet_add(jet_mul(val, x, ctr), c)
    return val


def jet_ring_ops(ctr=None):
    """Ring adapter for hyper_catalan.soft_poly_root over the jet ring."""
    return {
        "add": jet_add,
        "mul": lambda a, b: jet_mul(a, b, ctr),
        "zero": JET_ZERO,
        "one": JET_ONE,
        "from_int": jet_from_int,
        "inv": lambda a: jet_inv(a, ctr)[0],
    }
