"""Parameterized jet ring — J_N = A31[ε]/(ε^(N+1)) for arbitrary N.

Extends jet_ring.py (hardcoded N=2) to general truncation order.
Bit-exact behavioral model of what the RTL computes:
  jet_mul_N: truncated Cauchy product
  jet_inv_N: geometric-series inverse via c₀⁻¹ tower + reassembly

Every function takes an optional OpCount for cost tracking.
"""

from lib.a31_field import (
    A31_ONE,
    A31_ZERO,
    OpCount,
    a31_add,
    a31_mul,
    a31_neg,
    a31_sub,
    a31_tower_inv,
    m31,
)


def jet_zero(N):
    return tuple(A31_ZERO for _ in range(N + 1))


def jet_one(N):
    return (A31_ONE,) + tuple(A31_ZERO for _ in range(N))


def jet_from_a31(x, N):
    return (x,) + tuple(A31_ZERO for _ in range(N))


def jet_from_int(n, N):
    return ((m31(n), 0, 0, 0),) + tuple(A31_ZERO for _ in range(N))


def jet_add(a, b):
    return tuple(a31_add(x, y) for x, y in zip(a, b))


def jet_sub(a, b):
    return tuple(a31_sub(x, y) for x, y in zip(a, b))


def jet_neg(a):
    return tuple(a31_neg(x) for x in a)


def jet_mul_N(a, b, N, ctr=None):
    """Truncated Cauchy product at depth N.  Cost: (N+1)(N+2)/2 base mults."""
    if ctr is not None:
        ctr.mults += (N + 1) * (N + 2) // 2
    res = []
    for k in range(N + 1):
        acc = A31_ZERO
        for i in range(k + 1):
            acc = a31_add(acc, a31_mul(a[i], b[k - i]))
        res.append(acc)
    return tuple(res)


def jet_pow_N(base, exp, N, ctr=None):
    """Repeated jet_mul: base^exp."""
    acc = jet_one(N)
    for _ in range(exp):
        acc = jet_mul_N(acc, base, N, ctr)
    return acc


def jet_inv_N(j, N, ctr=None):
    """Jet inverse at depth N via geometric series.

    J = c₀ + c₁·ε + ... + cN·ε^N
    Let δ = (J/c₀) - 1 = (c₁/c₀)·ε + ... + (cN/c₀)·ε^N  (note δ₀ = 0)
    Then J⁻¹ = c₀⁻¹ · (1 + δ)⁻¹ = c₀⁻¹ · Σ_{k=0}^N (-1)^k · δ^k
    where δ^(N+1) = 0 by nilpotency.

    Cost: 1 tower + N base mults (for δ coefficients) +
          Σ_{k=2}^N jet_mul_cost(N) (for δ^k powers, k=2..N) +
          (N+1) base mults (for c₀⁻¹ · each term of the sum).
    """
    c0 = j[0]
    m0, flags_v = a31_tower_inv(c0, ctr)
    if flags_v:
        return None, True

    if ctr is not None:
        # δ coefficients: δ_k = ck * c0⁻¹ for k=1..N
        ctr.mults += N
        # c₀⁻¹ · sum: N+1 base mults (one per order)
        # (the δ^k jet_muls below count themselves via jet_mul_N(..., ctr))
        ctr.mults += N + 1

    # Compute δ = (c₁/c₀, c₂/c₀, ..., cN/c₀) as a jet with δ₀ = 0
    delta = [A31_ZERO]
    for k in range(1, N + 1):
        delta.append(a31_mul(j[k], m0))

    # Compute δ^k for k=2..N
    delta_pow = [None, tuple(delta)]  # delta_pow[1] = δ
    d = tuple(delta)
    for k in range(2, N + 1):
        d = jet_mul_N(d, tuple(delta), N, ctr)
        delta_pow.append(d)

    # Sum: Σ_{k=0}^N (-1)^k · δ^k
    acc = jet_one(N)
    for k in range(1, N + 1):
        term = delta_pow[k]
        if k % 2 == 1:
            term = jet_neg(term)
        acc = jet_add(acc, term)

    # Multiply by c₀⁻¹: scalar multiply each coefficient
    inv = tuple(a31_mul(x, m0) for x in acc)
    return inv, False


def jet_eval_poly_N(coeffs, x, N, ctr=None):
    """Horner evaluation of sum coeffs[i]·x^i in J_N."""
    val = coeffs[-1]
    for c in reversed(coeffs[:-1]):
        val = jet_add(jet_mul_N(val, x, N, ctr), c)
    return val


def jet_ring_ops_N(N, ctr=None):
    """Ring adapter for hyper_catalan.soft_poly_root over J_N."""
    return {
        "add": jet_add,
        "mul": lambda a, b: jet_mul_N(a, b, N, ctr),
        "zero": jet_zero(N),
        "one": jet_one(N),
        "from_int": lambda n: jet_from_int(n, N),
        "inv": lambda a: jet_inv_N(a, N, ctr)[0],
    }


def taylor_shift_N(coeffs, s, N, ctr=None):
    """Coefficients of p(y + s) via synthetic division, in J_N."""
    c = [tuple(x) for x in coeffs]
    sj = jet_from_a31(s, N)
    for j in range(len(c) - 1):
        for i in range(len(c) - 2, j - 1, -1):
            c[i] = jet_add(c[i], jet_mul_N(c[i + 1], sj, N, ctr))
    return c


def series_root_N(coeffs, x0, types, N, ctr=None):
    """Compute series root at depth N via digon-recursive traversal."""
    from lib.hyper_catalan import soft_poly_root

    b = taylor_shift_N(coeffs, x0, N, ctr)
    c = [b[0], jet_neg(b[1])] + b[2:]
    ring = jet_ring_ops_N(N, ctr)
    return soft_poly_root(c, types, ring)


def newton_root_N(coeffs, x0, N, ctr=None, max_iters=None):
    """Newton-Hensel root at depth N."""
    from lib.digon_recursive import newton_iterations

    if max_iters is None:
        max_iters = newton_iterations(N)
    y = jet_from_a31(x0, N)
    dcoeffs = [jet_mul_N(jet_from_int(i, N), c, N, ctr)
               for i, c in enumerate(coeffs)][1:]
    for _ in range(max_iters):
        num = jet_eval_poly_N(coeffs, y, N, ctr)
        dinv, err = jet_inv_N(jet_eval_poly_N(dcoeffs, y, N, ctr), N, ctr)
        if err:
            return None, True
        y = jet_sub(y, jet_mul_N(num, dinv, N, ctr))
    return y, False
