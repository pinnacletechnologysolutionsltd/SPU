"""Exact aperture-7 (GBT-style) digit algebra over Z[w].

pi = 2 - w (norm 7). Digit set D = {0, +-1, +-w, +-w^2}, a complete residue
system mod pi (verified in tests). A level-l cell is a point of pi^l * L,
identified by (a, b, l) with (a, b) its fine-lattice Eisenstein coordinates.
Reuses the H2 exact Eisenstein arithmetic read-only.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "h2_hex"))
from algebra import e_conj, e_mul, e_norm  # noqa: E402

PI = (2, -1)
NORM = e_norm(PI)                                       # 7
PI_C = e_conj(PI)
DIGITS = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]   # 0,1,-1,w,-w,-w^2,w^2


def _key(x):
    return tuple(c % NORM for c in e_mul(x, PI_C))


DIGIT_OF = {_key(d): i for i, d in enumerate(DIGITS)}


def add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def sub(x, y):
    return (x[0] - y[0], x[1] - y[1])


def div_pi(x):
    """Exact x / pi for x in pi*L; raises if not divisible."""
    a, b = e_mul(x, PI_C)
    if a % NORM or b % NORM:
        raise ValueError("not divisible by pi")
    return (a // NORM, b // NORM)


def pi_pow(k):
    p = (1, 0)
    for _ in range(k):
        p = e_mul(p, PI)
    return p


def encode(x, K):
    """Digits (least significant first) of x, or None if x needs > K digits."""
    out = []
    for _ in range(K):
        i = DIGIT_OF[_key(x)]
        out.append(i)
        x = div_pi(sub(x, DIGITS[i]))
    return out if x == (0, 0) else None


def decode(digits):
    x, p = (0, 0), (1, 0)
    for i in digits:
        x = add(x, e_mul(DIGITS[i], p))
        p = e_mul(p, PI)
    return x


def domain(K):
    """All fine points with a K-digit expansion (7^K points)."""
    pts = [(0, 0)]
    for k in range(K):
        p = pi_pow(k)
        pts = [add(x, e_mul(d, p)) for x in pts for d in DIGITS]
    return pts


def parent(cell):
    """(a, b, l) -> (A, B, l+1): drop the lowest digit of the level-l address."""
    a, b, l = cell
    x = (a, b)
    for _ in range(l):
        x = div_pi(x)                                    # coordinates in pi^l L units
    d = DIGITS[DIGIT_OF[_key(x)]]
    y = div_pi(sub(x, d))
    P = e_mul(y, pi_pow(l + 1))
    return (P[0], P[1], l + 1)


def children(cell):
    a, b, l = cell
    step = pi_pow(l - 1)
    return [(a + e_mul(d, step)[0], b + e_mul(d, step)[1], l - 1) for d in DIGITS]


def address(cell, K):
    """Level-l cell -> its K-l high digits (most significant first)."""
    a, b, l = cell
    x = (a, b)
    for _ in range(l):
        x = div_pi(x)
    digs = encode(x, K - l)
    return None if digs is None else list(reversed(digs))
