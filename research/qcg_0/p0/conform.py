"""Conformance checks shared by run.py, test_p0.py and the mutant harness (contract §7 targets, §8 detectors)."""
from fractions import Fraction as F
import arms_a, refs
from events import W31

PREP_TARGETS = {"B-Horner": (43, 30, 8, 14, 0, 87), "B-Bezier": None, "B-TS": (43, 30, 8, 14, 0, 87),
                "B-PH": (31, 22, 5, 14, 0), "C1": (31, 22, 5, 14, 0), "C2": (27, 22, 5, 14, 0)}


def prep_targets(rows):
    """X-10: P-phase (M, A, S, D, K[, G_calls]) of every Cell A arm against the contract's analytic targets. Returns mismatches."""
    bad = []
    for r in rows:
        want = PREP_TARGETS.get(r["arm"])
        if want:
            got = tuple(r["P"][c] for c in ("M", "A", "S", "D", "K", "G_calls")[:len(want)])
            if got != want:
                bad.append((r["arm"], got, want))
    return bad


def q_division_free(rows):
    return [r["arm"] for r in rows if r["Q"]["D"] != 0]


def w31_cell_a():
    """X-15: W31 Cell A statuses and first-refusal events against the reviewer-certified traces. Returns mismatches."""
    exp = {}
    for d in refs.stage_cell_a():
        exp.update(d["W31_CellA_trace"])
    bad, src, rows = [], refs.source("PH5"), refs.cell_a_ref()
    for cls in arms_a.ARMS:
        if cls.name not in exp:
            continue
        a = cls(W31, src)
        if a.prepare() is not None:
            bad.append((cls.name, "prep"))
            continue
        for i, (t, _, _) in enumerate(rows):
            r = a.request(i, t)
            e = exp[cls.name][i]
            if r["status"] != e["status"] or (r["event"] if r["status"] == "REFUSED" else None) != e["first_refusal"]:
                bad.append((cls.name, i, r["status"], r["event"], e["first_refusal"]))
    return bad


def state_key(a):
    return repr({k: [(x.n, x.d) for x in v] if isinstance(v, list) else (v.n, v.d) for k, v in sorted(a.state.items())})


def refusal_atomic(cls):
    """X-16 (W31, Cell A, q03 refusal): committed state identical after the refusal; the next admissible request equals a fresh
    run; the repeat refuses identically. Returns True when all three hold."""
    src, rows = refs.source("PH5"), refs.cell_a_ref()
    a, fresh = cls(W31, src), cls(W31, src)
    a.prepare()
    fresh.prepare()
    before = state_key(a)
    r1 = a.request(3, rows[3][0])
    same = r1["status"] == "REFUSED" and state_key(a) == before
    nxt = a.request(4, rows[4][0])
    want = fresh.request(4, rows[4][0])
    rep = a.request(3, rows[3][0])
    return same and nxt == want and rep["status"] == "REFUSED" and rep["event"] == r1["event"]


def reversal_twice():
    """X-22 (oracle-side): reversal r(t) -> r(1-t) is h -> -h(1-t), (U, V) -> (U(1-t), V(1-t)); twice restores the hodograph."""
    import o1
    U, V, h = [F(1), F(2), F(1)], [F(1), F(-1), F(3)], [F(2), F(1)]
    sub = lambda p: o1.comp(p, [F(1), F(-1)])                               # noqa: E731
    rev = lambda u, v, hh: (sub(u), sub(v), [-x for x in sub(hh)])         # noqa: E731
    def trim(p):
        p = [F(x) for x in p]
        while len(p) > 1 and p[-1] == 0:
            p.pop()
        return p
    hod = lambda u, v, hh: trim(o1.mul(hh, o1.add(o1.mul(u, u), o1.mul(v, v), -1)))   # noqa: E731
    twice = rev(*rev(U, V, h))
    once = rev(U, V, h)
    ok_twice = hod(*twice) == hod(U, V, h)
    # r'_rev(t) = -r'(1-t): the single reversal must negate the hodograph at the mirrored parameter
    ok_once = hod(*once) == trim([-x for x in sub(hod(U, V, h))])
    return ok_twice and ok_once


def controls_e1():
    """X-24: E1a R^4 = I and E1b ((3+4i)/5)^k first columns, k = 0..16, against the pinned controls."""
    c = refs.load("QUINTIC_FIXTURE_VALUES.json")["controls"]
    R = [[F(x) for x in row] for row in c["E1a_C4"]["R"]]
    mm = lambda A, B: [[sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]   # noqa: E731
    R4 = mm(mm(R, R), mm(R, R))
    bad = [] if R4 == [[F(x) for x in row] for row in c["E1a_C4"]["R4"]] else ["E1a"]
    z = (F(1), F(0))
    for row in c["E1b"]:
        k = row["k"]
        want = [F(*p) for p in row["first_column"]]
        if [z[0], z[1]] != want:
            bad.append("E1b.%d" % k)
        z = ((z[0] * 3 - z[1] * 4) / 5, (z[0] * 4 + z[1] * 3) / 5)
    return bad
