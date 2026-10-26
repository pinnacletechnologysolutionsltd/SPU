"""Evaluation primitives, loop orders exactly as contract §5 (the loop order is the event order)."""
from ledger import lit


def horner(c, t):
    acc = c[-1]
    for i in range(len(c) - 2, -1, -1):
        acc = acc * t + c[i]
    return acc


def decas(b, t):
    b = list(b)                       # scratch copy: retained Bernstein list is never modified
    d = len(b) - 1
    for r in range(1, d + 1):
        for j in range(0, d - r + 1):
            b[j] = b[j] + t * (b[j + 1] - b[j])
    return b[0]


def tshift(c, t):
    c = list(c)                       # scratch copy
    d = len(c) - 1
    for j in range(0, d):
        for i in range(d - 1, j - 1, -1):
            c[i] = c[i] + t * c[i + 1]
    return c                          # c[0] = value, c[1] = derivative, ...


def fdinit(c, delta):
    """Forward-difference table with t_0 = 0: points, Horner values, then the triangular traversal."""
    d, L = len(c) - 1, delta.L
    t, p = lit(0, L), []
    for k in range(d + 1):
        if k >= 1:
            t = t + delta
        p.append(horner(c, t))
    v, table = list(p), [p[0]]
    for r in range(1, d + 1):
        for j in range(0, d - r + 1):
            v[j] = v[j + 1] - v[j]
        table.append(v[0])
    return table


def fdstep(table):
    """In-place update of a retained table: ascending j, old Delta_{j+1} is still unmodified."""
    for j in range(0, len(table) - 1):
        table[j] = table[j] + table[j + 1]
    return table
