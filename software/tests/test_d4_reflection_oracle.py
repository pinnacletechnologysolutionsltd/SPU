#!/usr/bin/env python3
"""Independent exact oracle for the fixed D4 simple-root reflections."""

from __future__ import annotations

from itertools import product
import random
import sys


ROOTS = (
    (1, -1, 0, 0),
    (0, 1, -1, 0),
    (0, 0, 1, -1),
    (0, 0, 1, 1),
)


def reflect_formula(vector: tuple[int, ...], root: tuple[int, ...]) -> tuple[int, ...]:
    """Evaluate v - (v dot alpha) alpha with unbounded integer arithmetic."""
    dot = sum(value * coefficient for value, coefficient in zip(vector, root))
    return tuple(value - dot * coefficient
                 for value, coefficient in zip(vector, root))


def reflect_specialized(vector: tuple[int, ...], selector: int,
                        width: int) -> tuple[tuple[int, ...] | None, bool]:
    """Independent swap/sign-swap implementation with signed-width checks."""
    v0, v1, v2, v3 = vector
    if selector == 0:
        result = (v1, v0, v2, v3)
    elif selector == 1:
        result = (v0, v2, v1, v3)
    elif selector == 2:
        result = (v0, v1, v3, v2)
    elif selector == 3:
        result = (v0, v1, -v3, -v2)
    else:
        raise ValueError(f"invalid root selector {selector}")

    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    if any(value < minimum or value > maximum for value in result):
        return None, True
    return result, False


def squared_norm(vector: tuple[int, ...]) -> int:
    return sum(value * value for value in vector)


def check_case(vector: tuple[int, ...], selector: int, width: int) -> bool:
    expected = reflect_formula(vector, ROOTS[selector])
    observed, invalid = reflect_specialized(vector, selector, width)
    expected_invalid = any(value < -(1 << (width - 1)) or
                           value > (1 << (width - 1)) - 1
                           for value in expected)
    if invalid != expected_invalid:
        raise AssertionError(
            f"invalid mismatch width={width} selector={selector} v={vector} "
            f"formula={expected} specialized={observed} invalid={invalid}")
    if invalid:
        if selector != 3:
            raise AssertionError("a swap root unexpectedly overflowed")
        return False
    if observed != expected:
        raise AssertionError(
            f"value mismatch width={width} selector={selector} v={vector} "
            f"formula={expected} specialized={observed}")
    if squared_norm(observed) != squared_norm(vector):
        raise AssertionError(f"norm mismatch selector={selector} v={vector}")
    twice, second_invalid = reflect_specialized(observed, selector, width)
    if second_invalid or twice != vector:
        raise AssertionError(
            f"involution mismatch selector={selector} v={vector} "
            f"twice={twice} invalid={second_invalid}")
    return True


def check_root_system() -> list[list[int]]:
    norms = [squared_norm(root) for root in ROOTS]
    if norms != [2, 2, 2, 2]:
        raise AssertionError(f"unexpected simple-root norms: {norms}")
    cartan = [[sum(a * b for a, b in zip(left, right))
               for right in ROOTS] for left in ROOTS]
    expected = [
        [2, -1, 0, 0],
        [-1, 2, -1, -1],
        [0, -1, 2, 0],
        [0, -1, 0, 2],
    ]
    if cartan != expected:
        raise AssertionError(f"unexpected D4 Cartan matrix: {cartan}")
    return cartan


def main() -> int:
    try:
        cartan = check_root_system()

        reduced_width = 4
        reduced_min = -(1 << (reduced_width - 1))
        reduced_max = (1 << (reduced_width - 1)) - 1
        reduced_cases = 0
        reduced_valid = 0
        for vector in product(range(reduced_min, reduced_max + 1), repeat=4):
            for selector in range(4):
                reduced_valid += check_case(vector, selector, reduced_width)
                reduced_cases += 1

        boundary_values = (-32768, -32767, -1, 0, 1, 32766, 32767)
        boundary_cases = 0
        boundary_valid = 0
        for vector in product(boundary_values, repeat=4):
            for selector in range(4):
                boundary_valid += check_case(vector, selector, 16)
                boundary_cases += 1

        rng = random.Random(0xD4_2026)
        random_cases = 0
        random_valid = 0
        for _ in range(4096):
            vector = tuple(rng.randint(-32768, 32767) for _ in range(4))
            for selector in range(4):
                random_valid += check_case(vector, selector, 16)
                random_cases += 1

        print("D4 root norms: [2, 2, 2, 2]")
        print("D4 Cartan matrix:")
        for row in cartan:
            print("  " + " ".join(f"{value:2d}" for value in row))
        print(f"reduced exhaustive cases: {reduced_cases} "
              f"({reduced_valid} valid results)")
        print(f"signed-16 boundary cases: {boundary_cases} "
              f"({boundary_valid} valid results)")
        print(f"seeded random cases: {random_cases} "
              f"({random_valid} valid results; seed=0xD42026)")
        print("D4 reflection oracle: PASS")
        return 0
    except AssertionError as error:
        print(f"D4 reflection oracle: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
