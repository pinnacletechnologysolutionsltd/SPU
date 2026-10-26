"""Independent rational norm-shell enumeration; no candidate/mapping imports."""
from fractions import Fraction
from itertools import product


def member(values, system):
    n = 4 if system == 'D4' else 8 if system == 'E8' else 0
    if len(values) != n or not n or any(type(v) not in (int, Fraction) for v in values):
        return False
    row = tuple(Fraction(v) for v in values)
    integral = all(v.denominator == 1 for v in row)
    half = system == 'E8' and all(v.denominator == 2 for v in row)
    return (integral or half) and sum(row).denominator == 1 and sum(row).numerator % 2 == 0


def roots(system):
    n = {'D4': 4, 'E8': 8}[system]
    candidates = list(product((-1, 0, 1), repeat=n))
    if system == 'E8':
        candidates += list(product((Fraction(-1, 2), Fraction(1, 2)), repeat=8))
    return tuple(sorted(tuple(Fraction(v) for v in row) for row in candidates
                        if sum(v * v for v in row) == 2 and member(row, system)))


def reflect(values, alpha):
    if len(values) != len(alpha):
        raise ValueError('REFERENCE_SHAPE')
    if any(type(v) not in (int, Fraction) for v in tuple(values) + tuple(alpha)):
        raise ValueError('REFERENCE_TYPE')
    values, alpha = tuple(map(Fraction, values)), tuple(map(Fraction, alpha))
    norm = sum(a * a for a in alpha)
    if not norm:
        raise ValueError('ZERO_ROOT')
    coefficient = 2 * sum(x * a for x, a in zip(values, alpha)) / norm
    return tuple(x - coefficient * a for x, a in zip(values, alpha))


def matrix(alpha):
    if any(type(v) not in (int, Fraction) for v in alpha):
        raise ValueError('REFERENCE_TYPE')
    alpha = tuple(map(Fraction, alpha))
    norm = sum(a * a for a in alpha)
    if not norm:
        raise ValueError('ZERO_ROOT')
    return tuple(tuple(Fraction(int(i == j)) - 2 * alpha[i] * alpha[j] / norm
                       for j in range(len(alpha))) for i in range(len(alpha)))
