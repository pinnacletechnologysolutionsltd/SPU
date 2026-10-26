"""Exact finite-domain preparation checks and named root-set falsifiers."""
from collections import Counter
from fractions import Fraction

from . import reference
from .linear import rank, apply
from .roots import member, reflect


def need(condition, name, *detail):
    if not condition:
        raise AssertionError((name,) + detail)


def check_roots(system, values):
    n, count = (4, 24) if system == 'D4' else (8, 240)
    need(len(values) == count, 'ROOT_COUNT', system, len(values))
    need(all(type(row) is tuple and len(row) == n for row in values), 'ROOT_SHAPE')
    need(all(type(v) is int for row in values for v in row), 'ROOT_INTEGER_TYPE')
    need(len(set(values)) == count, 'DUPLICATE_ROOT')
    need(all(member(row) for row in values), 'LATTICE_MEMBERSHIP')
    need(all(sum(v * v for v in row) == 8 for row in values), 'SCALED_ROOT_NORM')
    need(rank(values) == n, 'ROOT_RANK')
    rational = {tuple(Fraction(v, 2) for v in row) for row in values}
    need(rational == set(reference.roots(system)), 'INDEPENDENT_ROOT_SET')
    histogram, pairs = Counter(), 0
    for alpha in values:
        need(tuple(-v for v in alpha) in values, 'NEGATIVE_ROOT')
        for x in values:
            dot = sum(v * w for v, w in zip(x, alpha))
            need(dot % 4 == 0 and dot // 4 in (-2, -1, 0, 1, 2), 'INNER_PRODUCT')
            histogram[dot // 4] += 1
            result = reflect(x, alpha)
            need(result in values, 'REFLECTION_CLOSURE', x, alpha, result)
            need(reflect(result, alpha) == x, 'REFLECTION_INVOLUTION', x, alpha)
            pairs += 1
    expected = {-2: 24, -1: 192, 0: 144, 1: 192, 2: 24} if n == 4 else {
        -2: 240, -1: 13440, 0: 30240, 1: 13440, 2: 240}
    need(dict(histogram) == expected, 'INNER_PRODUCT_DISTRIBUTION')
    # Rational formula and dense matrix agreement on declared deterministic pairs.
    samples = [(i, j) for i in range(0, count, max(1, count // 8)) for j in (0, count - 1)]
    for i, j in samples:
        x, alpha = (tuple(Fraction(v, 2) for v in values[k]) for k in (i, j))
        output = tuple(Fraction(v, 2) for v in reflect(values[i], values[j]))
        need(reference.reflect(x, alpha) == output, 'RATIONAL_REFLECTION')
        need(apply(reference.matrix(alpha), x) == output, 'MATRIX_REFLECTION')
    return dict(system=system, roots=count, rank=n, squared_length=2,
                inner_products=dict(sorted(histogram.items())), reflection_pairs=pairs,
                rational_matrix_pairs=len(samples), status='PREPARATION_CHECK_PASS')
