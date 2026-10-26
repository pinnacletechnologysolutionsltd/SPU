#!/usr/bin/env python3
"""Replay six exact joint rotations through the opt-in Python kernel."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "software"))
from lib import rational_robotics as reference
from lib.rational_robotics_unshared import apply_joint_chain


def format_q3(value):
    def part(number):
        return str(number.numerator) if number.denominator == 1 else f"{number.numerator}/{number.denominator}"

    return f"{part(value.p)} + ({part(value.q)})*sqrt(3)"


def format_vector(vector):
    labels = "ABCD"
    return " ".join(
        f"{labels[i]}={format_q3(component)}"
        for i, component in enumerate(vector.components())
    )


def main():
    start = reference.sample_robot_vector()
    joints = tuple(reference.joint_60() for _ in range(6))
    print("Exact six-step robotics replay (software only)")
    print("Kernel: opt-in unshared-scale apply_joint_chain; checked against reference")
    print("Start:", format_vector(start))
    expected_forward = reference.fk_chain(start, joints)
    expected_recovered = reference.inverse_fk_chain(expected_forward, joints)
    forward, recovered = apply_joint_chain(start, joints)
    if (forward, recovered) != (expected_forward, expected_recovered):
        print("FAIL: multi-joint output differs from reference", file=sys.stderr)
        return 1
    print("Joint count:", len(joints))
    print("Endpoint:", format_vector(forward))
    print("Recovered:", format_vector(recovered))
    if recovered != start or forward != start:
        print("FAIL: six-step orbit did not close", file=sys.stderr)
        return 1
    print("PASS: fused six-joint chain matches reference and closes exactly")
    print("Reference implementation remains available at lib.rational_robotics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
