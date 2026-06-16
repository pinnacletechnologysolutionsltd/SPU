#!/usr/bin/env python3
"""Tests for the exact rational robotics simulation oracle."""

import ast
import inspect
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import rational_robotics
from lib.rational_robotics import (
    PELL_FWD,
    PELL_INV,
    Q3_ONE,
    apply_inverse_joint,
    apply_joint,
    compose_circulant,
    CORRECTED_ROTC_ANGLE_TABLE,
    circulant_determinant,
    circulant_inverse,
    circulant_period,
    fk_chain,
    inverse_fk_chain,
    is_closed,
    joint_60,
    joint_120,
    joint_240,
    joint_identity,
    joint_p5_forward,
    joint_p5_inverse,
    legacy_rotc_table_issues,
    pell_step,
    q3,
    ROTATION_KINEMATICS,
    sample_robot_vector,
)


PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def test_pell_inverse_closure():
    check("Pell forward inverse scalar = 1", PELL_FWD * PELL_INV == Q3_ONE)
    v0 = sample_robot_vector()
    v1 = pell_step(v0, 7)
    v2 = pell_step(v1, -7)
    check("Pell trajectory closes after inverse steps", is_closed(v0, v2))
    check("forward-only Pell step is not closed", not is_closed(v0, v1))


def test_circulant_inverse_coefficients():
    j60 = joint_60(axis_id=3)
    inv = circulant_inverse(j60)
    j240 = joint_240(axis_id=3)

    check("60-degree determinant = 1", circulant_determinant(j60) == Q3_ONE)
    check("inverse of 60 has F=2/3", inv.f == q3(Fraction(2, 3)))
    check("inverse of 60 has G=-1/3", inv.g == q3(Fraction(-1, 3)))
    check("inverse of 60 has H=2/3", inv.h == q3(Fraction(2, 3)))
    check("inverse of 60 equals 240-degree joint", inv == j240)


def test_recalculated_rotation_catalog():
    for name, joint in ROTATION_KINEMATICS.items():
        identity = joint_identity(joint.axis_id)
        check(f"{name} determinant = 1", circulant_determinant(joint) == Q3_ONE)
        inv = circulant_inverse(joint)
        check(f"{name} inverse closes", compose_circulant(joint, inv) == identity)

    check("thirds period-6 rotor has period 6", circulant_period(joint_60()) == 6)
    check("thirds period-2 rotor has period 2", circulant_period(joint_120()) == 2)
    check("P5 forward bypass has period 3", circulant_period(joint_p5_forward()) == 3)
    check("P5 inverse is reverse cycle", circulant_inverse(joint_p5_forward()) == joint_p5_inverse())


def test_p5_bypass_semantics():
    v = sample_robot_vector()
    p5 = apply_joint(v, joint_p5_forward())
    p5_inv = apply_joint(p5, joint_p5_inverse())

    check("P5 forward B'=D", p5.b == v.d)
    check("P5 forward C'=B", p5.c == v.b)
    check("P5 forward D'=C", p5.d == v.c)
    check("P5 inverse closes vector", p5_inv == v)


def test_legacy_rotc_table_audit():
    issues = legacy_rotc_table_issues()
    joined = "\n".join(issues)

    check("legacy audit catches singular angle 3", "angle 3: determinant" in joined)
    check("legacy audit catches angle 2 P5 mismatch", "angle 2:" in joined)
    check("legacy audit catches duplicated angle 5", "angle 5:" in joined)


def test_corrected_rotc_angle_table():
    expected_inverse = {
        0: 0,
        1: 4,
        2: 5,
        3: 3,
        4: 1,
        5: 2,
    }
    expected_period = {
        0: 1,
        1: 6,
        2: 3,
        3: 2,
        4: 6,
        5: 3,
    }

    for angle, joint in CORRECTED_ROTC_ANGLE_TABLE.items():
        check(f"corrected ROTC angle {angle} determinant = 1",
              circulant_determinant(joint) == Q3_ONE)
        check(f"corrected ROTC angle {angle} period",
              circulant_period(joint) == expected_period[angle])
        inv = circulant_inverse(joint)
        check(f"corrected ROTC angle {angle} inverse angle",
              inv == CORRECTED_ROTC_ANGLE_TABLE[expected_inverse[angle]])


def test_single_joint_inverse_closure():
    v0 = sample_robot_vector()
    j = joint_60(axis_id=3)
    v1 = apply_joint(v0, j)
    v2 = apply_inverse_joint(v1, j)

    check("single joint forward inverse closes", is_closed(v0, v2))
    check("single joint forward only is not closed", not is_closed(v0, v1))


def test_fk_inverse_chain_closure():
    v0 = sample_robot_vector()
    joints = [joint_60(axis_id=3), joint_240(axis_id=1), joint_60(axis_id=2)]

    end = fk_chain(v0, joints)
    recovered = inverse_fk_chain(end, joints)

    check("FK chain inverse closes", is_closed(v0, recovered))
    check("FK chain forward only is not closed", not is_closed(v0, end))


def test_arc_out_and_back_closure():
    v0 = sample_robot_vector()
    out = pell_step(v0, 12)
    back = pell_step(out, -12)

    check("Pell arc out and back closes", is_closed(v0, back))


def test_no_float_or_sqrt_calls():
    source = inspect.getsource(rational_robotics)
    tree = ast.parse(source)
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"float", "sqrt"}:
                forbidden.append(node.func.id)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "sqrt":
                forbidden.append("sqrt")
    check("no sqrt call in rational_robotics", "sqrt" not in forbidden)
    check("no float conversion call in rational_robotics", "float" not in forbidden)


def main():
    test_pell_inverse_closure()
    test_circulant_inverse_coefficients()
    test_recalculated_rotation_catalog()
    test_p5_bypass_semantics()
    test_legacy_rotc_table_audit()
    test_corrected_rotc_angle_table()
    test_single_joint_inverse_closure()
    test_fk_inverse_chain_closure()
    test_arc_out_and_back_closure()
    test_no_float_or_sqrt_calls()

    if FAIL:
        print(f"FAIL ({FAIL} failures, {PASS} passes)")
        return 1
    print(f"PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
