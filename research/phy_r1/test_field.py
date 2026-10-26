"""Validation of field.py on independent examples (run before any PHY-R1 use).

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/phy_r1/test_field.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from field import QF, det, nullspace_rank, rank_and_psd, sqrt_in_field  # noqa: E402


def q(a, b=0, d=3):
    return QF(Fr(a), Fr(b), d)


def raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    return False


def test_cross_field():
    assert raises(lambda: q(1, 1, 3) + q(1, 1, 5), ValueError), "surds in two fields"
    assert raises(lambda: q(1, 1, 3) * q(0, 1, 5), ValueError)
    # A rational converts explicitly into the other operand's field (the old
    # code silently produced 1 + sqrt2 here).
    assert q(1, 0, 2) + q(0, 1, 3) == q(1, 1, 3)
    assert q(0, 1, 3) * q(2, 0, 7) == q(0, 2, 3)
    assert raises(lambda: QF(Fr(1), Fr(0), 4), ValueError), "d must be non-square"
    assert QF(Fr(1), Fr(1), 1) == QF(Fr(2), Fr(0), 1), "d=1 canonical form"


def test_sign_and_inverse():
    assert q(1, -1).sign() == -1 and q(2, -1).sign() == 1 and q(-2, 1).sign() == -1
    assert q(0, 0).sign() == 0
    assert q(2, 1) * q(2, 1).inv() == q(1)
    assert raises(lambda: q(0, 0).inv(), ZeroDivisionError)


def test_sqrt_representability():
    cases = [(q(9, 0, 1), True), (q(2, 0, 1), False), (q(-1, 0, 1), False),
             (q(7, 4, 3), True), (q(3, 0, 3), True), (q(Fr(3, 4), 0, 3), True),
             (q(2, 0, 3), False), (q(Fr(5, 9), 0, 5), True), (q(3, 0, 5), False),
             (q(Fr(8, 9), 0, 3), False), (q(1, 1, 3), False)]
    for x, expect in cases:
        y = sqrt_in_field(x)
        assert (y is not None) == expect, f"sqrt representability {x}"
        if y is not None:
            assert y * y == x and y.sign() >= 0, f"sqrt value {x}"


def test_rank_psd():
    F = Fr
    cases = [
        ([[F(1), F(0), F(0)], [F(0), F(1), F(0)], [F(0), F(0), F(1)]], (3, True)),
        ([[F(1), F(1)], [F(1), F(1)]], (1, True)),          # singular PSD
        ([[F(1), F(2)], [F(2), F(1)]], (2, False)),         # indefinite
        ([[F(0), F(1)], [F(1), F(0)]], (2, False)),         # zero-diagonal indefinite
        ([[F(0), F(0)], [F(0), F(0)]], (0, True)),
        ([[F(1), F(0), F(0)], [F(0), F(-1), F(0)], [F(0), F(0), F(0)]], (2, False)),
        ([[q(2), q(0, 1)], [q(0, 1), q(2)]], (2, True)),    # det 4 - 3 > 0
        ([[q(0, 1), q(2)], [q(2), q(0, 1)]], (2, False)),   # det 3 - 4 < 0
    ]
    for m, expect in cases:
        assert rank_and_psd(m) == expect, f"rank/psd {m} -> {rank_and_psd(m)}"


def test_nullspace_and_det():
    rows = [[Fr(1), Fr(2), Fr(3)], [Fr(2), Fr(4), Fr(6)]]
    basis, piv = nullspace_rank(rows)
    assert len(basis) == 2 and piv == [0]
    for v in basis:
        assert all(sum(r[i] * v[i] for i in range(3)) == 0 for r in rows)
    basis, _ = nullspace_rank([[1, 2], [3, 4]])          # int input
    assert basis == []
    b, _ = nullspace_rank([[2, 0, 1]])
    assert all(isinstance(x, (int, Fr)) for v in b for x in v), "no floats"
    qb, _ = nullspace_rank([[q(1), q(0, 1)]])
    assert len(qb) == 1 and q(1) * qb[0][0] + q(0, 1) * qb[0][1] == q(0)
    assert det([[1, 2], [3, 4]]) == -2 and det([[1, 2], [2, 4]]) == 0
    m = [[2, -1, 0], [1, 3, 4], [0, 5, -2]]
    expand = (2 * (3 * -2 - 4 * 5) - (-1) * (1 * -2 - 4 * 0) + 0)
    assert det(m) == expand


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} field test groups")
