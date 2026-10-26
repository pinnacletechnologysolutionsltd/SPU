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
from typing import Iterable, Sequence


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


@dataclass(frozen=True)
class SixStepKinematicsFrame:
    """One commanded rational-robotics rotor phase and inverse-balance check."""

    phase: int
    forward_angle: int
    inverse_angle: int
    input_vector: QuadrayQ
    commanded_vector: QuadrayQ
    recovered_vector: QuadrayQ
    closure_error_vector: QuadrayQ
    quadrance_before: Q3
    quadrance_after: Q3
    inverse_balanced: bool
    orbit_closed: bool


def joint_identity(axis_id: int = 0) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(1), q3(0), q3(0))


def joint_60(axis_id: int = 3) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(Fraction(2, 3)), q3(Fraction(2, 3)), q3(Fraction(-1, 3)))


def joint_120(axis_id: int = 3) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(Fraction(-1, 3)), q3(Fraction(2, 3)), q3(Fraction(2, 3)))


def joint_240(axis_id: int = 3) -> CirculantJoint:
    return CirculantJoint(axis_id, q3(Fraction(2, 3)), q3(Fraction(-1, 3)), q3(Fraction(2, 3)))


def joint_p5_forward(axis_id: int = 3) -> CirculantJoint:
    """Pure P5 cyclic bypass: B'=D, C'=B, D'=C."""

    return CirculantJoint(axis_id, q3(0), q3(1), q3(0))


def joint_p5_inverse(axis_id: int = 3) -> CirculantJoint:
    """Inverse P5 cycle: B'=C, C'=D, D'=B."""

    return CirculantJoint(axis_id, q3(0), q3(0), q3(1))


def circulant_determinant(joint: CirculantJoint) -> Q3:
    f, g, h = joint.f, joint.g, joint.h
    return f * f * f + g * g * g + h * h * h - q3(3) * f * g * h


def compose_circulant(first: CirculantJoint, second: CirculantJoint) -> CirculantJoint:
    """Compose circulants: result applies `second`, then `first`."""

    f1, g1, h1 = first.f, first.g, first.h
    f2, g2, h2 = second.f, second.g, second.h
    return CirculantJoint(
        first.axis_id,
        f1 * f2 + h1 * g2 + g1 * h2,
        g1 * f2 + f1 * g2 + h1 * h2,
        h1 * f2 + g1 * g2 + f1 * h2,
    )


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


def circulant_period(joint: CirculantJoint, max_steps: int = 12) -> int | None:
    """Return the smallest n where joint^n is identity, or None."""

    identity = joint_identity(joint.axis_id)
    current = identity
    for n in range(1, max_steps + 1):
        current = compose_circulant(joint, current)
        if current == identity:
            return n
    return None


ROTATION_KINEMATICS = {
    "identity": joint_identity(),
    "thirds_period6": joint_60(),
    "thirds_period6_inverse": joint_240(),
    "thirds_period2": joint_120(),
    "p5_forward": joint_p5_forward(),
    "p5_inverse": joint_p5_inverse(),
}


CORRECTED_ROTC_ANGLE_TABLE = {
    0: joint_identity(),
    1: joint_60(),
    2: joint_p5_forward(),
    3: joint_120(),
    4: joint_240(),
    5: joint_p5_inverse(),
}


ROTC_INVERSE_ANGLE_TABLE = {
    0: 0,
    1: 4,
    2: 5,
    3: 3,
    4: 1,
    5: 2,
}


LEGACY_ROTC_ANGLE_TABLE = {
    # Matches the current VM/compiler angle descriptions for audit purposes.
    # Do not treat this as the corrected hardware contract.
    0: joint_identity(),
    1: joint_60(),
    2: joint_120(),
    3: CirculantJoint(3, q3(Fraction(-1, 3)), q3(Fraction(-1, 3)), q3(Fraction(-1, 3))),
    4: joint_240(),
    5: joint_60(),
}


def legacy_rotc_table_issues() -> list[str]:
    """Return known issues in the legacy 0..5 ROTC angle table."""

    issues: list[str] = []
    for angle, joint in LEGACY_ROTC_ANGLE_TABLE.items():
        det = circulant_determinant(joint)
        if det != Q3_ONE:
            issues.append(f"angle {angle}: determinant {det} != 1")

    if LEGACY_ROTC_ANGLE_TABLE[2] != joint_p5_forward():
        issues.append("angle 2: VM/compiler thirds coefficients disagree with hardware P5 bypass")
    if LEGACY_ROTC_ANGLE_TABLE[5] == LEGACY_ROTC_ANGLE_TABLE[1]:
        issues.append("angle 5: duplicates angle 1 instead of providing an inverse/reverse rotation")

    return issues


def sample_robot_vector() -> QuadrayQ:
    return QuadrayQ(q3(1), q3(0, 1), q3(Fraction(1, 3)), q3(-2))


def inverse_angle_for(angle: int) -> int:
    """Return the corrected ROTC angle that exactly inverts `angle`."""

    if angle not in ROTC_INVERSE_ANGLE_TABLE:
        raise ValueError(f"unsupported corrected ROTC angle: {angle}")
    return ROTC_INVERSE_ANGLE_TABLE[angle]


def six_step_kinematics_trace(
    start: QuadrayQ | None = None,
    angle: int = 1,
) -> tuple[SixStepKinematicsFrame, ...]:
    """
    Emit the recovered six-step rational robotics rotor trace.

    The default angle is the corrected period-6 ROTC step. Each frame advances
    the commanded state once, then applies the inverse angle to prove that the
    command is topologically balanced before the next command is accepted.
    """

    if angle not in CORRECTED_ROTC_ANGLE_TABLE:
        raise ValueError(f"unsupported corrected ROTC angle: {angle}")

    root = sample_robot_vector() if start is None else start
    current = root
    forward_joint = CORRECTED_ROTC_ANGLE_TABLE[angle]
    inverse_angle = inverse_angle_for(angle)
    inverse_joint = CORRECTED_ROTC_ANGLE_TABLE[inverse_angle]
    frames: list[SixStepKinematicsFrame] = []

    for phase in range(6):
        commanded = apply_joint(current, forward_joint)
        recovered = apply_joint(commanded, inverse_joint)
        error = closure_error(current, recovered)
        frames.append(SixStepKinematicsFrame(
            phase=phase,
            forward_angle=angle,
            inverse_angle=inverse_angle,
            input_vector=current,
            commanded_vector=commanded,
            recovered_vector=recovered,
            closure_error_vector=error,
            quadrance_before=current.quadrance(),
            quadrance_after=commanded.quadrance(),
            inverse_balanced=error.is_zero(),
            orbit_closed=is_closed(root, commanded),
        ))
        current = commanded

    return tuple(frames)


def six_step_trace_is_balanced(trace: Sequence[SixStepKinematicsFrame]) -> bool:
    """Return true when every phase is inverse-balanced and the orbit closes."""

    return bool(trace) and all(frame.inverse_balanced for frame in trace) and trace[-1].orbit_closed


def fraction_to_trace_string(value: Fraction) -> str:
    return str(value)


def q3_to_trace_value(value: Q3) -> dict[str, str]:
    return {
        "p": fraction_to_trace_string(value.p),
        "q": fraction_to_trace_string(value.q),
    }


def quadray_to_trace_value(value: QuadrayQ) -> dict[str, dict[str, str]]:
    return {
        "a": q3_to_trace_value(value.a),
        "b": q3_to_trace_value(value.b),
        "c": q3_to_trace_value(value.c),
        "d": q3_to_trace_value(value.d),
    }


def six_step_frame_to_dict(frame: SixStepKinematicsFrame) -> dict:
    return {
        "phase": frame.phase,
        "forward_angle": frame.forward_angle,
        "inverse_angle": frame.inverse_angle,
        "input_vector": quadray_to_trace_value(frame.input_vector),
        "commanded_vector": quadray_to_trace_value(frame.commanded_vector),
        "recovered_vector": quadray_to_trace_value(frame.recovered_vector),
        "closure_error_vector": quadray_to_trace_value(frame.closure_error_vector),
        "quadrance_before": q3_to_trace_value(frame.quadrance_before),
        "quadrance_after": q3_to_trace_value(frame.quadrance_after),
        "inverse_balanced": frame.inverse_balanced,
        "orbit_closed": frame.orbit_closed,
    }


def six_step_trace_to_dict(trace: Sequence[SixStepKinematicsFrame]) -> dict:
    return {
        "name": "rational_robotics_six_step_trace",
        "field": "Q(sqrt(3))",
        "steps": len(trace),
        "balanced": six_step_trace_is_balanced(trace),
        "frames": [six_step_frame_to_dict(frame) for frame in trace],
    }
