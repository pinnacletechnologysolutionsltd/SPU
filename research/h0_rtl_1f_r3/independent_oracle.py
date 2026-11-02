#!/usr/bin/env python3
"""Independent exact-polynomial check of the two frozen R3 test vectors."""
from fractions import Fraction
from itertools import product
from math import lcm
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = {
    "A": (0x7000000000000100, 0x7000010000000000, 0x7000020000000200,
          0x7000030000000000, 0x7000040000000300, 0x7000050000000000),
    "B": (0x7000000000000200, 0x7000010000000000, 0x7000020000000100,
          0x7000030000000000, 0x7000040000000200, 0x7000050000000000),
}


def oracle(words):
    # Parse six explicit SLI words; polynomial multiplication is independent of
    # the RTL implementation and uses exact rational coefficients.
    slices = []
    for index, word in enumerate(words):
        assert word >> 40 == 0x700000 + index and word & 0xff == 0
        slices.append((word >> 8) & 0xffffffff)
    fields = [slices[i] | (slices[i + 1] << 32) for i in (0, 2, 4)]
    assert all(x < 1 << 63 for x in fields[:2]) and fields[2] > 0
    coeffs = (Fraction(fields[0], fields[2]), Fraction(fields[1], fields[2]))
    out = [Fraction(0), Fraction(0)]
    for i, j in product(range(2), repeat=2):
        out[(i + j) % 2] += coeffs[i] * coeffs[j] * (3 if i + j == 2 else 1)
    den = lcm(*(x.denominator for x in out))
    vals = [int(x * den) for x in out] + [den]
    assert all(0 <= x < 1 << 64 for x in vals)
    return tuple(y for x in vals for y in (x & 0xffffffff, x >> 32))


def main():
    bench = (ROOT / "research/h0_rtl_1f_r3/cpu_check.v").read_text()
    # Independently check that fixture operands and expected result literals
    # are the actual values selected by the existing testbench.
    for index in (0, 2, 4):
        match = re.search(rf"{index}:word=which==0\?64'h([0-9a-f]+):64'h([0-9a-f]+)", bench)
        assert match and tuple(int(x, 16) for x in match.groups()) == (
            FIXTURES["A"][index], FIXTURES["B"][index])
    for index in (1, 3, 5):
        match = re.search(rf"{index}:word=64'h([0-9a-f]+)", bench)
        assert match and int(match.group(1), 16) == FIXTURES["A"][index] == FIXTURES["B"][index]
    matches = re.findall(r"check\(result==\{([^}]+)\},\"result [AB]\"\)", bench)
    assert len(matches) == 2
    for (name, fixture), literal in zip(FIXTURES.items(), matches):
        parts = [int(n) for n in re.findall(r"32'd(\d+)", literal)]
        assert len(parts) == 6
        expected = tuple(reversed(parts))
        result = oracle(fixture)
        assert result == expected, (name, result, expected)
        print(f"{name}: slices={result} match R3 testbench")
    print("INDEPENDENT_ARITHMETIC_ORACLE PASS")


if __name__ == "__main__":
    main()
