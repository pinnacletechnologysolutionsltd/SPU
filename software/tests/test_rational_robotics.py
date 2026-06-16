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
    circulant_determinant,
    circulant_inverse,
    fk_chain,
    inverse_fk_chain,
    is_closed,
    joint_60,
    joint_240,
    pell_step,
    q3,
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
