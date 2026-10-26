"""Exact finite GC-2B reference model over Q(sqrt(3))."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Q3:
    """p + q*sqrt(3), with arbitrary-precision rational coefficients."""

    p: Fraction = Fraction(0)
    q: Fraction = Fraction(0)

    def __post_init__(self):
        object.__setattr__(self, "p", Fraction(self.p))
        object.__setattr__(self, "q", Fraction(self.q))

    def __add__(self, other):
        other = q3(other)
        return Q3(self.p + other.p, self.q + other.q)

    __radd__ = __add__

    def __neg__(self):
        return Q3(-self.p, -self.q)

    def __sub__(self, other):
        return self + -q3(other)

    def __mul__(self, other):
        other = q3(other)
        return Q3(self.p * other.p + 3 * self.q * other.q,
                  self.p * other.q + self.q * other.p)

    __rmul__ = __mul__

    def is_zero(self):
        return self.p == 0 and self.q == 0

    def is_positive(self):
        """Exact sign under sqrt(3) -> positive real sqrt(3)."""
        p, q = self.p, self.q
        if p >= 0 and q >= 0:
            return p != 0 or q != 0
        if p <= 0 and q <= 0:
            return False
        if p > 0:
            return p * p > 3 * q * q
        return 3 * q * q > p * p

    def to_pair(self):
        return [fraction_text(self.p), fraction_text(self.q)]


def q3(value=0):
    if isinstance(value, Q3):
        return value
    if isinstance(value, tuple):
        return Q3(*value)
    return Q3(Fraction(value), Fraction(0))


def fraction_text(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def vector(values):
    return tuple(q3(value) for value in values)


def p_transport(x):
    return tuple(x[(-j) % 4] for j in range(4))


def rotate(x, k):
    out = [q3(0)] * 4
    for i, value in enumerate(x):
        out[(i + k) % 4] = value
    return tuple(out)


def apply_left(x, weights):
    out = [q3(0)] * 4
    for i in range(4):
        out[(i + 1) % 4] = weights[i] * x[i]
    return tuple(out)


def apply_right(x, weights):
    return tuple(weights[i] * x[(i + 1) % 4] for i in range(4))


def apply_f(x, weights, a, b):
    left, right = apply_left(x, weights), apply_right(x, weights)
    return tuple(q3(a) * left[i] + q3(b) * right[i] for i in range(4))


def transported_weights(weights):
    # P(e_i) = e^P_{-i-1}; this is a permutation, not conjugation.
    out = [q3(0)] * 4
    for i, weight in enumerate(weights):
        out[(-i - 1) % 4] = weight
    return tuple(out)


def equal_vectors(lhs, rhs):
    return len(lhs) == len(rhs) and all(a == b for a, b in zip(lhs, rhs))


def admissible_rotations(weights, mirrored_weights):
    return [k for k in range(4)
            if all(mirrored_weights[i] == weights[(i + k) % 4]
                   for i in range(4))]


def q_map(x, k):
    return rotate(p_transport(x), k)


def trajectory(x, weights, a, b, steps):
    states = [tuple(x)]
    for _ in range(steps):
        states.append(apply_f(states[-1], weights, a, b))
    return tuple(states)


def vector_payload(values):
    return [value.to_pair() for value in values]
