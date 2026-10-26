"""Small exact matrix utilities; no floating-point operations."""
from fractions import Fraction


def transpose(matrix):
    return tuple(zip(*matrix))


def columns(vectors):
    return transpose(vectors)


def identity(n=8):
    return tuple(tuple(Fraction(i == j) for j in range(n)) for i in range(n))


def inverse(matrix):
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError('MATRIX_SHAPE')
    rows = [list(map(Fraction, row))+list(identity(n)[i]) for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = next((i for i in range(j,n) if rows[i][j]), None)
        if pivot is None:
            raise ValueError('MATRIX_SINGULAR')
        rows[j], rows[pivot] = rows[pivot], rows[j]
        divisor = rows[j][j]
        rows[j] = [v/divisor for v in rows[j]]
        for i in range(n):
            if i != j:
                coefficient = rows[i][j]
                rows[i] = [a-coefficient*b for a,b in zip(rows[i],rows[j])]
    return tuple(tuple(row[n:]) for row in rows)


def apply(matrix, values):
    return tuple(sum((a*b for a,b in zip(row,values)), Fraction(0)) for row in matrix)


def multiply(left, right):
    return tuple(tuple(sum((a*b for a,b in zip(row,col)),Fraction(0))
                       for col in transpose(right)) for row in left)


def integers(values):
    if any(Fraction(v).denominator != 1 for v in values):
        raise ValueError('NONINTEGER_COORDINATE')
    return tuple(int(v) for v in values)
