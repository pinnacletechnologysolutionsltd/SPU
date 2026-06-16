"""
rational_robotics.py — exact rational robotics simulation oracle.

This module reconstructs the first public-facing rational robotics layer:
Pell forward/inverse closure, F/G/H circulant joint inverse closure, FK chains,
and topological balance checks.  Coefficients live in Q(sqrt(3)) with exact
rational coefficients so joints such as 2/3, 2/3, -1/3 are represented exactly.

This is a simulation oracle for tests and RTL vectors.  RTL should implement
the hot paths with scaled integer constants, not runtime rational division.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable


@dataclass(frozen=True)
class Q3:
    """Element p + q*sqrt(3), with p and q exact rational coefficients."""

    p: Fraction = Fraction(0)
    q: Fraction = Fraction(0)

    def __init__(self, p=0, q=0):
        object.__setattr__(self, "p", Fraction(p))
        object.__setattr__(self, "q", Fraction(q))

    def __add__(self, other: "Q3") -> "Q3":
        return Q3(self.p + other.p, self.q + other.q)

    def __sub__(self, other: "Q3") -> "Q3":
        return Q3(self.p - other.p, self.q - other.q)

    def __neg__(self) -> "Q3":
        return Q3(-self.p, -self.q)

    def __mul__(self, other: "Q3") -> "Q3":
        return Q3(
            self.p * other.p + 3 * self.q * other.q,
            self.p * other.q + self.q * other.p,
        )

    def square(self) -> "Q3":
        return self * self

    def conjugate(self) -> "Q3":
        return Q3(self.p, -self.q)

    def norm(self) -> Fraction:
        return self.p * self.p - 3 * self.q * self.q

    def is_zero(self) -> bool:
        return self.p == 0 and self.q == 0


Q3_ZERO = Q3(0)
Q3_ONE = Q3(1)
PELL_FWD = Q3(2, 1)
PELL_INV = Q3(2, -1)


def q3(p=0, q=0) -> Q3:
    return Q3(p, q)


@dataclass(frozen=True)
class QuadrayQ:
    """Quadray vector with Q3 components."""

    a: Q3 = Q3_ZERO
    b: Q3 = Q3_ZERO
    c: Q3 = Q3_ZERO
    d: Q3 = Q3_ZERO

    def components(self) -> tuple[Q3, Q3, Q3, Q3]:
        return self.a, self.b, self.c, self.d

    def __add__(self, other: "QuadrayQ") -> "QuadrayQ":
        return QuadrayQ(
            self.a + other.a,
            self.b + other.b,
            self.c + other.c,
            self.d + other.d,
        )

    def __sub__(self, other: "QuadrayQ") -> "QuadrayQ":
        return QuadrayQ(
            self.a - other.a,
            self.b - other.b,
            self.c - other.c,
            self.d - other.d,
        )

    def scale(self, scalar: Q3) -> "QuadrayQ":
        return QuadrayQ(
            self.a * scalar,
            self.b * scalar,
            self.c * scalar,
            self.d * scalar,
        )

    def quadrance(self) -> Q3:
        comps = self.components()
        total = Q3_ZERO
        for i in range(4):
            for j in range(i + 1, 4):
                diff = comps[i] - comps[j]
                total = total + diff.square()
        return total

    def circulant_rotate(self, f: Q3, g: Q3, h: Q3) -> "QuadrayQ":
        """Apply B/C/D circulant rotation. A is invariant."""

        b2 = f * self.b + h * self.c + g * self.d
        c2 = g * self.b + f * self.c + h * self.d
        d2 = h * self.b + g * self.c + f * self.d
        return QuadrayQ(self.a, b2, c2, d2)

    def is_zero(self) -> bool:
        return all(comp.is_zero() for comp in self.components())


@dataclass(frozen=True)
class CirculantJoint:
    axis_id: int
    f: Q3
    g: Q3
    h: Q3


def joint_identity(axis_id: int = 0) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(1), q3(0), q3(0))


def joint_60(axis_id: int = 3) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(Fraction(2, 3)), q3(Fraction(2, 3)), q3(Fraction(-1, 3)))


def joint_120(axis_id: int = 3) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(Fraction(-1, 3)), q3(Fraction(2, 3)), q3(Fraction(2, 3)))


def joint_240(axis_id: int = 3) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(Fraction(2, 3)), q3(Fraction(-1, 3)), q3(Fraction(2, 3)))


def circulant_determinant(joint: CirculantJoint) -> Q3:
    f, g, h = joint.f, joint.g, joint.h
    return f * f * f + g * g * g + h * h * h - q3(3) * f * g * h


def circulant_inverse(joint: CirculantJoint) -> CirculantJoint:
    """
    Invert an F/G/H circulant with determinant 1.

    For the SPU matrix convention:
      B' = F*B + H*C + G*D
      C' = G*B + F*C + H*D
      D' = H*B + G*C + F*D
    the determinant-1 inverse coefficients are:
      F_inv = F^2 - G*H
      G_inv = H^2 - F*G
      H_inv = G^2 - F*H
    """

    f, g, h = joint.f, joint.g, joint.h
    return CirculantJoint(
        joint.axis_id,
        f * f - g * h,
        h * h - f * g,
        g * g - f * h,
    )


def apply_joint(v: QuadrayQ, joint: CirculantJoint) -> QuadrayQ:
    return v.circulant_rotate(joint.f, joint.g, joint.h)


def apply_inverse_joint(v: QuadrayQ, joint: CirculantJoint) -> QuadrayQ:
    return apply_joint(v, circulant_inverse(joint))


def fk_chain(base: QuadrayQ, joints: Iterable[CirculantJoint]) -> QuadrayQ:
    v = base
    for joint in joints:
        v = apply_joint(v, joint)
    return v


def inverse_fk_chain(end_effector: QuadrayQ, joints: Iterable[CirculantJoint]) -> QuadrayQ:
    v = end_effector
    for joint in reversed(tuple(joints)):
        v = apply_inverse_joint(v, joint)
    return v


def pell_step(v: QuadrayQ, steps: int = 1) -> QuadrayQ:
    scalar = Q3_ONE
    rotor = PELL_FWD if steps >= 0 else PELL_INV
    for _ in range(abs(steps)):
        scalar = scalar * rotor
    return v.scale(scalar)


def closure_error(start: QuadrayQ, recovered: QuadrayQ) -> QuadrayQ:
    return recovered - start


def is_closed(start: QuadrayQ, recovered: QuadrayQ) -> bool:
    return closure_error(start, recovered).is_zero()


def sample_robot_vector() -> QuadrayQ:
    return QuadrayQ(q3(1), q3(0, 1), q3(Fraction(1, 3)), q3(-2))

