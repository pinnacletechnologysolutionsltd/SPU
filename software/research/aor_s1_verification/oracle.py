"""Exact rational root isolation and bounded Pell/value identities.

This module never imports candidate code, fixtures, schedule counters or reducers.
Resource ceilings describe oracle infrastructure, never arithmetic verdicts.
"""
from math import isqrt

MAX_BITS = 1_000_000
MAX_PRODUCTS = 100_000


class OracleUnavailable(RuntimeError):
    """Required exact semantic witness exceeded its infrastructure ceiling."""


def ordering(p, q):
    """Isolate sqrt(3) between consecutive dyadic rationals using integer isqrt."""
    if p == q == 0:
        return 0
    bits = 8
    while bits <= MAX_BITS:
        if max(abs(p).bit_length(), abs(q).bit_length()) + bits + 2 > MAX_BITS:
            raise OracleUnavailable('ROOT_ISOLATION_BITS_LIMIT')
        scale = 1 << bits
        lower = isqrt(3 * scale * scale)
        low, high = (lower, lower + 1) if q >= 0 else (lower + 1, lower)
        left, right = p * scale + q * low, p * scale + q * high
        if left > 0:
            return 1
        if right < 0:
            return -1
        bits *= 2
    raise OracleUnavailable('ROOT_ISOLATION_LIMIT')


def comparator(a, b):
    sx, sy = ordering(a, b), ordering(a, -b)
    x, y = (sx * a, sx * b), (sy * a, -sy * b)
    lower = (2 * x[0] + 3 * x[1] - y[0], x[0] + 2 * x[1] - y[1])
    upper = (x[0] - 2 * y[0] - 3 * y[1], x[1] - y[0] - 2 * y[1])
    lo, hi = ordering(*lower), ordering(*upper)
    return dict(embedding_sign=sx, conjugate_embedding_sign=sy,
                lower_expression=lower, upper_expression=upper,
                lower_sign=lo, upper_sign=hi, balanced=lo >= 0 and hi < 0)


class Expansion:
    def __init__(self):
        self.products = 0

    def checked(self, pair):
        if any(abs(n).bit_length() > MAX_BITS for n in pair):
            raise OracleUnavailable('COEFFICIENT_BITS_LIMIT')
        return pair

    def product(self, x, y):
        self.products += 1
        if self.products > MAX_PRODUCTS:
            raise OracleUnavailable('PAIR_PRODUCTS_LIMIT')
        self.checked(x); self.checked(y)
        # Refuse before materializing a potentially oversized exact result.
        size = max(abs(n).bit_length() for n in x) + max(abs(n).bit_length() for n in y) + 3
        if size > MAX_BITS:
            raise OracleUnavailable('PRE_PRODUCT_BITS_LIMIT')
        a, b = x; c, d = y
        return self.checked((a * c + 3 * b * d, a * d + b * c))

    def pell(self, exponent):
        power, result = (2, 1 if exponent >= 0 else -1), (1, 0)
        n = abs(exponent)
        while n:
            if n & 1:
                result = self.product(result, power)
            n >>= 1
            if n:
                power = self.product(power, power)
        return result

    def value(self, descriptor):
        a, b, k = descriptor
        if a == b == 0:
            return (0, 0)
        return self.product((a, b), self.pell(k))


def answer(fixture):
    """Semantic witness: scalar answer or expanded value, independently of labels."""
    op, args = fixture['operation'], fixture['arguments']
    if fixture['expected_status'] != 'OK':
        return dict(proof='FROZEN_REFUSAL_AND_INDEPENDENT_SCHEDULE', result=None)
    a, b, k = args[0]
    if op == 'sign':
        return dict(proof='RATIONAL_ROOT_ISOLATION', result=ordering(a, b))
    if op == 'norm':
        return dict(proof='NORM_UNIT_INVARIANCE', result=a * a - 3 * b * b)
    if op == 'equality':
        return dict(proof='CANONICAL_UNIQUENESS', result=tuple(args[0]) == tuple(args[1]))
    expansion = Expansion()
    if op == 'multiply':
        c, d, m = args[1]
        raw = expansion.product((a, b), (c, d))
        value = expansion.value((*raw, k + m))
    elif op == 'same_k_sum':
        c, d, _ = args[1]
        value = expansion.value((a + c, b + d, k))
    elif op in ('conjugate', 'unit_inverse'):
        if op == 'unit_inverse' and a * a - 3 * b * b != 1:
            raise AssertionError('Unsupported inverse semantic witness')
        value = expansion.value((a, -b, -k))
    elif op == 'step':
        value = expansion.value((a, b, k + args[1]))
    else:
        value = expansion.value((a, b, k))
    return dict(proof='ZERO_ANNIHILATION' if value == (0, 0) else 'BOUNDED_PELL_VALUE_IDENTITY',
                expanded_value=value, pair_products=expansion.products)
