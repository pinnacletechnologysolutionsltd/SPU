"""Software candidate for tagged scheduling. This is not sparse RTL."""

from lib.a31_field import a31_add, a31_mul
from sparse_jet_reference import P, ZERO


def windows(n):
    return [(n + 1, 0)] + [(lo, hi) for lo in range(n + 1) for hi in range(lo, n + 1)]


def validate_tag(n, tag):
    if (not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= 15
            or not isinstance(tag, tuple) or len(tag) != 2
            or any(type(x) is not int for x in tag)
            or not (tag == (n + 1, 0) or 0 <= tag[0] <= tag[1] <= n)):
        raise ValueError("invalid tag")


def validate(n, values, tag):
    validate_tag(n, tag)
    if len(values) != n + 1:
        raise ValueError("invalid jet length")
    for i, row in enumerate(values):
        if len(row) != 4 or any(type(x) is not int or not 0 <= x < P for x in row):
            raise ValueError("noncanonical coefficient")
        if not tag[0] <= i <= tag[1] and tuple(row) != ZERO:
            raise ValueError("tag promise violated")


def result_tag(n, a, b, mul=True):
    validate_tag(n, a)
    validate_tag(n, b)
    empty = (n + 1, 0)
    if not mul:
        return b if a == empty else a if b == empty else (min(a[0], b[0]), max(a[1], b[1]))
    if a == empty or b == empty or a[0] + b[0] > n:
        return empty
    return (a[0] + b[0], min(n, a[1] + b[1]))


def schedule(n, a, b):
    validate_tag(n, a)
    validate_tag(n, b)
    return [(order, i, order - i) for order in range(n + 1) for i in range(order + 1)
            if a[0] <= i <= a[1] and b[0] <= order - i <= b[1]]


def count(n, a, b):
    validate_tag(n, a)
    validate_tag(n, b)
    return sum(max(0, min(a[1], k - b[0]) - max(a[0], k - b[1]) + 1)
               for k in range(n + 1))


def execute(n, a, b, at, bt, mul=True):
    validate(n, a, at)
    validate(n, b, bt)
    out = [ZERO] * (n + 1)
    if mul:
        for k, i, j in schedule(n, at, bt):
            out[k] = a31_add(out[k], a31_mul(a[i], b[j]))
    else:
        out = [a31_add(x, y) for x, y in zip(a, b)]
    return tuple(out), result_tag(n, at, bt, mul), False
