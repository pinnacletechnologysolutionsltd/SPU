"""Ledger conformance rows LU-* (contract §7) and event grammar tests; collected by test_p0.py."""
import sys
from math import gcd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from account import Ledger
from events import P4096, W31, Refusal, Invalid
from ledger import Q, lit
import poly, prep
TESTS = []


def test(f): TESTS.append(f); return f   # noqa: E704, E702


def mk(L, n, d=1):
    g = gcd(abs(n), d) or 1
    return Q.imp(n // g, d // g, L, "t")


def qrun(L, label, fn, qid=0):
    L.begin("Q", qid)
    with L.enter(label):
        v = fn()
    L.commit()
    return v


def cnt(L, **kw): return all(L.cum["Q"][k] == v for k, v in kw.items())   # noqa: E704


@test
def lu_h():
    for coeffs, want in (([(1, 2), (2, 1), (-3, 1), (5, 7)], (3, 3, 6)), ([(0, 1), (-4, 1), (-2, 1)], (2, 2, 4))):
        L = Ledger(P4096, "T")
        c = [mk(L, n, d) for n, d in coeffs]
        qrun(L, "a1", lambda: poly.horner(c, mk(L, 3, 5)))
        assert cnt(L, M=want[0], A=want[1], G_calls=want[2]), L.cum["Q"]


@test
def lu_dc_ts():
    L = Ledger(P4096, "T"); d = 4
    c = [mk(L, i + 1, 3) for i in range(d + 1)]
    qrun(L, "a1", lambda: poly.decas(c, mk(L, 2, 7)))
    assert cnt(L, M=10, A=20, G_calls=30), L.cum["Q"]
    L2 = Ledger(P4096, "T")
    c = [mk(L2, i + 1, 3) for i in range(d + 1)]
    qrun(L2, "a1", lambda: poly.tshift(c, mk(L2, 2, 7)))
    assert cnt(L2, M=10, A=10, G_calls=20), L2.cum["Q"]


@test
def lu_fd():
    d = 3
    L = Ledger(P4096, "T")
    c = [mk(L, i + 2, 5) for i in range(d + 1)]
    tab = qrun(L, "f", lambda: poly.fdinit(c, mk(L, 1, 16)))
    assert cnt(L, M=d * (d + 1), A=3 * d * (d + 1) // 2 + d, G_calls=5 * d * (d + 1) // 2 + d), L.cum["Q"]
    before = L.cum["Q"]["A"]
    qrun(L, "g", lambda: poly.fdstep(tab), qid=1)
    assert L.cum["Q"]["A"] - before == d and L.cum["Q"]["G_calls"] == 5 * d * (d + 1) // 2 + d + d


@test
def lu_fd_values():  # table of a cubic: entries are the forward differences, FDSTEP walks the grid
    L = Ledger(P4096, "T")
    c = [mk(L, v) for v in (1, 2, 3, 4)]               # 1 + 2t + 3t^2 + 4t^3
    d = mk(L, 1, 16)
    L.begin("P", None)
    with L.enter("P1"):
        tab = poly.fdinit(c, d)
    L.commit()
    for k in range(1, 6):
        with L.enter("x"):
            poly.fdstep(tab)
        want = poly.horner(c, mk(L, k, 16))
        assert (tab[0].n, tab[0].d) == (want.n, want.d), k


@test
def lu_s_val_d_g():
    L = Ledger(P4096, "T")
    u, v = mk(L, 3), mk(L, 5)
    qrun(L, "b9", lambda: (u * v).twice().half())
    assert cnt(L, M=1, S=2, G_calls=1)
    L = Ledger(P4096, "T")
    qrun(L, "x", lambda: mk(L, 7, 3) * mk(L, 1, 2))          # LU-VAL: value 1/2 as data is M, not S
    assert cnt(L, M=1, S=0, G_calls=1)
    L = Ledger(P4096, "T")
    qrun(L, "x", lambda: prep.pint([mk(L, 1), mk(L, 6)]))     # LU-D: integration divisor 2 is D
    assert cnt(L, D=2, S=0, G_calls=2)
    L = Ledger(P4096, "T")
    r = qrun(L, "x", lambda: mk(L, 3) * mk(L, 5))             # LU-G: integer result still one gcd
    assert (r.n, r.d) == (15, 1) and cnt(L, M=1, G_calls=1)


@test
def lu_w():
    L = Ledger(P4096, "T")
    L.begin("Q", 0)                                   # imports inside the transaction so the reduced peak sees the inputs
    a, b = mk(L, 2 ** 30, 3), mk(L, 5, 1024)
    with L.enter("x"):
        r = a * b
    L.commit()
    assert (r.n, r.d) == (5242880, 3) and L.cum["Q"]["W_bits"] == 115
    assert L.pk["Q"]["W_peak_raw"] == 33 and L.pk["Q"]["W_peak_red"] == 31, L.pk["Q"]
    L = Ledger(P4096, "T")
    L.begin("Q", 0)
    a, b = mk(L, 2 ** 30, 3), mk(L, 5, 1024)
    with L.enter("x"):
        a / b
    L.commit()
    assert L.cum["Q"]["W_bits"] == 347


@test
def lu_p_aggregation():
    L = Ledger(P4096, "T")
    L.begin("P")
    with L.enter("P1"):
        mk(L, 3, 2) * mk(L, 5, 3)
    L.commit()
    qrun(L, "a1", lambda: mk(L, 7, 2) + mk(L, 1, 3))
    t = L.total()
    assert t["M"] == 1 and t["A"] == 1 and t["G_calls"] == 2
    assert t["W_peak_raw"] == max(L.pk["P"]["W_peak_raw"], L.pk["Q"]["W_peak_raw"])


@test
def event_ids_and_refusal():
    L = Ledger(W31, "B-Horner")
    s = mk(L, 55010, 6561)
    L.begin("Q", 3)
    try:
        with L.enter("a8"):
            s * s
        raise AssertionError("expected refusal")
    except Refusal as e:
        assert e.code == "ARITH_LIMIT" and e.event == "B-Horner.Q.q03.a8.1.e1", e.event
    L.rollback()
    assert L.attempt["M"] == 1 and L.cum["Q"]["M"] == 0     # attempt evidence is separate from committed ledgers
    L = Ledger(P4096, "T")
    L.begin("Q", 0)
    try:
        with L.enter("a1"):
            mk(L, 1) / lit(0, L)
        raise AssertionError
    except Invalid as e:
        assert e.code == "DIV_ZERO"
