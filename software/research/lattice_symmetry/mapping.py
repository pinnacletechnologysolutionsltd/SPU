"""Rank-aware software bridges; no CPU ISA, AOR-S1, or hardware dependencies."""
from fractions import Fraction

E = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))


def quadray(q):
    if type(q) not in (list, tuple) or len(q) != 4 or any(type(v) is not int for v in q):
        raise ValueError('QUADRAY_TYPE')
    if sum(q) % 4:
        raise ValueError('QUADRAY_FCC_DOMAIN')
    return tuple(sum(q[i] * E[i][j] for i in range(4)) // 2 for j in range(3))


def lift_fcc(x):
    if len(x) != 3 or any(type(v) is not int for v in x) or sum(x) % 2:
        raise ValueError('FCC_DOMAIN')
    return tuple(sum(a * b for a, b in zip(x, e)) // 2 for e in E)


def d4_to_quadray_and_scalar(x):
    if len(x) != 4 or any(type(v) is not int for v in x) or sum(x) % 2:
        raise ValueError('D4_DOMAIN')
    # The first three coordinates may have odd sum. Shift their first coordinate
    # by the parity of the fourth; carry that fourth coordinate as independent state.
    t = x[3]
    return lift_fcc((x[0] + t % 2, x[1], x[2])), t


def restore_d4(q, t):
    if type(t) is not int:
        raise ValueError('SCALAR_TYPE')
    x = quadray(q)
    return x[0] - t % 2, x[1], x[2], t


def constrained_block_basis(blocks=2):
    rows = []
    for block in range(blocks):
        for i in range(3):
            row = [0] * (4 * blocks)
            row[4 * block + i], row[4 * block + 3] = 1, -1
            rows.append(tuple(row))
    return tuple(rows)


def surd_coordinates(x):
    # Rational coordinates are the B=0 subspace of (A+B*sqrt(3))/D.
    return tuple((Fraction(v).numerator, 0, Fraction(v).denominator) for v in x)


def e8_to_blocks(x):
    if len(x) != 8 or any(type(v) is not int for v in x):
        raise ValueError('E8_SCALED_TYPE')
    return tuple((tuple(4 * v - sum(x[start:start + 4]) for v in x[start:start + 4]),
                  sum(x[start:start + 4])) for start in (0, 4))


def restore_blocks(blocks):
    result = []
    for q, total in blocks:
        if len(q) != 4 or any(type(v) is not int for v in q) or type(total) is not int or sum(q):
            raise ValueError('BLOCK_ENCODING')
        if any((v + total) % 4 for v in q):
            raise ValueError('BLOCK_DIVISIBILITY')
        result.extend((v + total) // 4 for v in q)
    if len(result) != 8:
        raise ValueError('BLOCK_COUNT')
    return tuple(result)


def extended_block_basis():
    return tuple(tuple((4 * int(i == j) - 1) if j // 4 == i // 4 else 0 for j in range(8))
                 for i in range(8)) + tuple(tuple(int(j // 4 == b) for j in range(8)) for b in (0, 1))
