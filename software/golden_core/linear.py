"""Small exact linear-algebra helpers over the Golden Core Q(sqrt(5)) field."""

from .exact import Q5, ZERO


def rref(matrix: tuple[tuple[Q5, ...], ...]) -> tuple[tuple[tuple[Q5, ...], ...], tuple[int, ...]]:
    """Return reduced row echelon form and pivot columns using exact field ops."""
    if not matrix:
        return (), ()
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("matrix rows must have equal length")
    rows = [list(row) for row in matrix]
    pivots = []
    pivot_row = 0
    for column in range(width):
        candidate = next((r for r in range(pivot_row, len(rows))
                          if rows[r][column] != ZERO), None)
        if candidate is None:
            continue
        rows[pivot_row], rows[candidate] = rows[candidate], rows[pivot_row]
        scale = rows[pivot_row][column].inverse()
        rows[pivot_row] = [value * scale for value in rows[pivot_row]]
        for r in range(len(rows)):
            if r == pivot_row or rows[r][column] == ZERO:
                continue
            factor = rows[r][column]
            rows[r] = [value - factor * pivot
                       for value, pivot in zip(rows[r], rows[pivot_row])]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return tuple(tuple(row) for row in rows), tuple(pivots)


def inverse(matrix: tuple[tuple[Q5, ...], ...]) -> tuple[tuple[Q5, ...], ...]:
    """Return a two-sided inverse, or raise ValueError for a singular matrix."""
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise ValueError("inverse requires a square matrix")
    identity = tuple(tuple(Q5(int(i == j)) for j in range(size))
                     for i in range(size))
    augmented = tuple(tuple(left) + tuple(right)
                      for left, right in zip(matrix, identity))
    reduced, pivots = rref(augmented)
    if pivots[:size] != tuple(range(size)):
        raise ValueError("matrix is singular")
    return tuple(tuple(row[size:]) for row in reduced)


def nullspace(matrix: tuple[tuple[Q5, ...], ...]) -> tuple[tuple[Q5, ...], ...]:
    """Return a basis of column vectors for the exact nullspace."""
    reduced, pivots = rref(matrix)
    width = len(matrix[0]) if matrix else 0
    free_columns = [column for column in range(width) if column not in pivots]
    basis = []
    for free in free_columns:
        vector = [ZERO] * width
        vector[free] = Q5(1)
        for row, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row][free]
        basis.append(tuple(vector))
    return tuple(basis)


def matmul(left: tuple[tuple[Q5, ...], ...],
           right: tuple[tuple[Q5, ...], ...]) -> tuple[tuple[Q5, ...], ...]:
    """Multiply compatible exact matrices."""
    if not left:
        return ()
    if not right or len(left[0]) != len(right):
        raise ValueError("matrix dimensions do not compose")
    columns = tuple(zip(*right))
    return tuple(tuple(sum((a * b for a, b in zip(row, column)), ZERO)
                       for column in columns) for row in left)


def apply(matrix: tuple[tuple[Q5, ...], ...], vector: tuple[Q5, ...]) -> tuple[Q5, ...]:
    """Apply an exact row-major matrix to a column vector."""
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("matrix and vector dimensions do not match")
    return tuple(sum((a * b for a, b in zip(row, vector)), ZERO) for row in matrix)
