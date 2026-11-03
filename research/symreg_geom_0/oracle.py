"""Independent concrete Q(sqrt(3)) arithmetic on Fraction coefficient pairs."""
from fractions import Fraction


def add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def mul(x, y):
    return (x[0]*y[0] + 3*x[1]*y[1], x[0]*y[1] + x[1]*y[0])


def quadrance(vector):
    x, y = vector
    return add(mul(x, x), mul(y, y))


def transform(matrix, vector):
    return tuple(tuple(sum(Fraction(matrix[i][j])*vector[j][k] for j in range(2))
                       for k in range(2)) for i in range(2))
