"""Explicit doubled-integer roots. Coordinate X represents the physical X/2."""
from itertools import combinations, product


def vector(values, dimension):
    if type(values) not in (list, tuple) or len(values) != dimension:
        raise ValueError('VECTOR_SHAPE')
    if any(type(x) is not int for x in values):
        raise ValueError('VECTOR_TYPE')
    return tuple(values)


def member(values):
    n = len(values)
    if n not in (4, 8):
        return False
    if any(type(x) is not int for x in values):
        return False
    parity = {x % 2 for x in values}
    return sum(values) % 4 == 0 and (parity == {0} or (n == 8 and parity == {1}))


def roots(system):
    if system not in ('D4', 'E8'):
        raise ValueError('ROOT_SYSTEM')
    n = 4 if system == 'D4' else 8
    result = []
    for i, j in combinations(range(n), 2):
        for a, b in product((-2, 2), repeat=2):
            row = [0] * n
            row[i], row[j] = a, b
            result.append(tuple(row))
    if n == 8:
        result += [row for row in product((-1, 1), repeat=8) if row.count(-1) % 2 == 0]
    return tuple(sorted(result))


def reflect(values, alpha):
    n = len(alpha)
    x, a = vector(values, n), vector(alpha, n)
    if not member(a) or sum(t * t for t in a) != 8:
        raise ValueError('INVALID_ROOT')
    if not member(x):
        raise ValueError('OUTSIDE_LATTICE')
    dot = sum(t * u for t, u in zip(x, a))
    if dot % 4:
        raise ValueError('NONINTEGRAL_REFLECTION')
    return tuple(t - (dot // 4) * u for t, u in zip(x, a))
