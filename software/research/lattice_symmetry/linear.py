"""Exact rational rank and matrix operations, independent of lattice generators."""
from fractions import Fraction


def rank(rows):
    if not rows:
        return 0
    matrix = [list(map(Fraction, row)) for row in rows]
    width, pivot = len(matrix[0]), 0
    if any(len(row) != width for row in matrix):
        raise ValueError('MATRIX_SHAPE')
    for column in range(width):
        chosen = next((i for i in range(pivot, len(matrix)) if matrix[i][column]), None)
        if chosen is None:
            continue
        matrix[pivot], matrix[chosen] = matrix[chosen], matrix[pivot]
        divisor = matrix[pivot][column]
        matrix[pivot] = [x / divisor for x in matrix[pivot]]
        for i in range(pivot + 1, len(matrix)):
            factor = matrix[i][column]
            matrix[i] = [x - factor * y for x, y in zip(matrix[i], matrix[pivot])]
        pivot += 1
        if pivot == len(matrix):
            break
    return pivot


def apply(matrix, values):
    return tuple(sum(a * b for a, b in zip(row, values)) for row in matrix)


def compose(left, right):
    return tuple(tuple(sum(a * b for a, b in zip(row, column))
                       for column in zip(*right)) for row in left)
