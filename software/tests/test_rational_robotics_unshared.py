#!/usr/bin/env python3
"""Reference-equivalence tests for the opt-in unshared robotics kernel."""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib import rational_robotics as reference
from lib import rational_robotics_unshared as candidate


def check(label, condition):
    if not condition:
        raise AssertionError(label)


def q(p, b=0):
    return reference.Q3(Fraction(p), Fraction(b))


def deterministic_cases():
    vectors = [reference.sample_robot_vector()]
    for k in range(1, 9):
        parts = [q(Fraction(k + i - 2, i + 1), Fraction((k * (i + 1)) % 7 - 3, i + 2))
                 for i in range(4)]
        vectors.append(reference.QuadrayQ(*parts))
    joints = list(reference.ROTATION_KINEMATICS.values())
    joints += [reference.joint_identity(), reference.joint_p5_forward(),
               reference.CirculantJoint(3, q(0), q(0), q(0))]
    for k in range(1, 10):
        joints.append(reference.CirculantJoint(
            3, q(Fraction(k, 3), Fraction(1-k, 5)),
            q(Fraction(2-k, 7), Fraction(k, 4)),
            q(Fraction(k-3, 8), Fraction(2*k+1, 9))))
    return vectors, joints


def main():
    vectors, joints = deterministic_cases()
    comparisons = 0
    for vector in vectors:
        for joint in joints:
            forward, recovered = candidate.apply_joint_pair(vector, joint)
            expected_forward = reference.apply_joint(vector, joint)
            expected_recovered = reference.apply_inverse_joint(expected_forward, joint)
            check("forward matches reference", forward == expected_forward)
            check("adjugate recovery matches reference", recovered == expected_recovered)
            check("output wrapper types", isinstance(forward, reference.QuadrayQ)
                  and isinstance(recovered, reference.QuadrayQ))
            comparisons += 1
    for joint in reference.ROTATION_KINEMATICS.values():
        for vector in vectors:
            _, recovered = candidate.apply_joint_pair(vector, joint)
            check("determinant-one closure", recovered == vector)
    chain_comparisons = 0
    for vector in vectors:
        for length in (0, 1, 3, 6, 12):
            chain = tuple(joints[i % len(joints)] for i in range(length))
            actual = candidate.apply_joint_chain(vector, chain)
            endpoint = reference.fk_chain(vector, chain)
            expected = endpoint, reference.inverse_fk_chain(endpoint, chain)
            check("chain forward and reverse recovery match reference", actual == expected)
            check("chain recovery preserves reference inverse behavior",
                  actual[1] == reference.inverse_fk_chain(actual[0], chain))
            chain_comparisons += 1
    chain = tuple(reference.ROTATION_KINEMATICS.values())
    result, trace = candidate.trace_joint_chain(vectors[0], chain)
    check("traced chain matches normal chain", result == candidate.apply_joint_chain(vectors[0], chain))
    check("trace records forward and recovery stages", len(trace['steps']) == 2 * len(chain))
    check("signed widths include inputs, products, accumulators, state and outputs",
          all(trace.get(key, 0) > 0 for key in
              ('input', 'product', 'accumulator', 'state', 'output')))
    print(f"PASS: {comparisons} pair and {chain_comparisons} chain comparisons; "
          "determinant-one closure and width trace checked")


if __name__ == "__main__":
    main()
