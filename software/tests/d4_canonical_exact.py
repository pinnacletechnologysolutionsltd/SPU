"""Exact bounded D4 states, signed permutations, and chamber operations."""

from __future__ import annotations

from itertools import permutations, product


IDENTITY = ((0, 1, 2, 3), (0, 0, 0, 0))
STATES = tuple(x for x in product(range(-4, 5), repeat=4) if sum(x) % 2 == 0)
GROUP = tuple((p, b) for p in permutations(range(4))
              for b in product((0, 1), repeat=4) if sum(b) % 2 == 0)
GENERATORS = (
    ((1, 0, 2, 3), (0, 0, 0, 0)),
    ((0, 2, 1, 3), (0, 0, 0, 0)),
    ((0, 1, 3, 2), (0, 0, 0, 0)),
    ((0, 1, 3, 2), (0, 0, 1, 1)),
)


def act(w, x):
    p, b = w
    return tuple((-1 if b[i] else 1) * x[p[i]] for i in range(4))


def compose(left, right):
    """Apply right, then left."""
    lp, lb = left
    rp, rb = right
    return (tuple(rp[lp[i]] for i in range(4)),
            tuple(lb[i] ^ rb[lp[i]] for i in range(4)))


def chamber(x):
    return x[0] >= x[1] >= x[2] >= abs(x[3])


def norm(x):
    return sum(v * v for v in x)


def label(x):
    return norm(x), tuple(sorted((abs(v) for v in x), reverse=True))


def rejects_nonfixed_zero_action():
    zero = (0, 0, 0, 0)
    e0 = (1, 0, 0, 0)
    return any(act(w, zero) == zero and act(w, e0) != e0 for w in GROUP)
