"""Independent polynomial reference; no production A31 multiplication calls."""

P = (1 << 31) - 1
ZERO = (0, 0, 0, 0)


def multiply(a, b):
    out = [0] * 4
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            sx, sy = (i & 1) + (j & 1), (i >> 1) + (j >> 1)
            out[(sx & 1) + 2 * (sy & 1)] += x * y * 3 ** (sx // 2) * 5 ** (sy // 2)
    return tuple(x % P for x in out)


def dense(a, b):
    out = [[0] * 4 for _ in a]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if i + j < len(a):
                for c, value in enumerate(multiply(x, y)):
                    out[i + j][c] += value
    return tuple(tuple(x % P for x in row) for row in out)


def pairs(n, a, b):
    return sorted(((i + j, i, j) for i in range(a[0], a[1] + 1)
                   for j in range(b[0], b[1] + 1) if i + j <= n))
