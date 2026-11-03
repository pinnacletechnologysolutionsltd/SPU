"""Concrete rational-coefficient oracle, independent of certificate code."""
from fractions import Fraction


def product(a, b):
    return (a[0]*b[0] + 3*a[1]*b[1], a[0]*b[1] + a[1]*b[0])


def form(g, v):
    products = [[product(v[i], v[j]) for j in range(2)] for i in range(2)]
    return tuple(sum(Fraction(g[i][j])*products[i][j][k]
                     for i in range(2) for j in range(2)) for k in range(2))


def apply(m, v):
    return tuple(tuple(sum(Fraction(m[i][j])*v[j][k] for j in range(2))
                       for k in range(2)) for i in range(2))
