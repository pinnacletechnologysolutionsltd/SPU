"""Independent integer formulas; no production arithmetic or encoder imports."""
MIN32, MAX32 = -(1 << 31), (1 << 31) - 1


def add(x, y):
    return x[0] + y[0], x[1] + y[1]


def subtract(x, y):
    return x[0] - y[0], x[1] - y[1]


def multiply(x, y):
    a, b = x
    c, d = y
    return a*c + 3*b*d, a*d + b*c


def nearest(value, denominator):
    quotient, remainder = divmod(abs(value), denominator)
    quotient += 2*remainder >= denominator
    return -quotient if value < 0 else quotient


def rotc(q, angle):
    # Rows are literal linear maps on B,C,D, derived from the six-angle contract.
    rows = {0: ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            1: ((2, -1, 2), (2, 2, -1), (-1, 2, 2)),
            2: ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
            3: ((-1, 2, 2), (2, -1, 2), (2, 2, -1)),
            4: ((2, 2, -1), (-1, 2, 2), (2, -1, 2)),
            5: ((0, 1, 0), (0, 0, 1), (1, 0, 0))}[angle]
    den = 3 if angle in (1, 3, 4) else 1
    return [q[0]] + [tuple(nearest(sum(row[j]*q[j+1][k] for j in range(3)), den)
                           for k in range(2)) for row in rows]


def fits(pair):
    return all(MIN32 <= value <= MAX32 for value in pair)


def seed():
    # Poison every bank so failure preservation cannot pass on default zeros.
    scalar = [(i+7, -i-3, -1) for i in range(26)]
    quadray = [[(i*4+j+1, -j-1) for j in range(4)] for i in range(13)]
    return scalar, quadray
