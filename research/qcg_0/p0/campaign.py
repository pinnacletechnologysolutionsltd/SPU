"""Cells A, B and the sequential tapes: run every arm under a profile, check EQ-3 against the pinned references, summarize ledgers."""
from fractions import Fraction as F
import arms_a, arms_b, arms_seq, arms_seq2, refs

OPS = ("M", "A", "S", "D", "K")
SEQ_ARMS = (arms_seq.SeqH, arms_seq.SeqZ, arms_seq.SeqT, arms_seq.SeqF, arms_seq2.SeqPH, arms_seq2.SeqPHFD, arms_seq2.SeqC1, arms_seq2.SeqC2)


def st(r):
    return r["status"] if r["code"] is None else "%s(%s)" % (r["status"], r["code"])


def summary(L):
    return {"P": L.cum["P"], "Q": L.cum["Q"], "peaks": L.pk, "total": L.total(), "attempt": L.attempt}


def ops(L):
    """Counted operations over committed and attempt ledgers (budget view)."""
    return sum(L.cum[p][c] + 0 for p in "PQ" for c in OPS) + sum(L.attempt[c] for c in OPS)


def _run(a, rows, check):
    prep = a.prepare()
    sts, bad, first = [], 0, None
    for i, row in enumerate(rows):
        r = a.request(i, row[0])
        sts.append(st(r))
        if r["status"] == "OK":
            bad += 0 if check(r["outputs"], row) else 1
        elif first is None and r["status"] == "REFUSED":
            first = r["event"]
    return {"arm": a.name, "prep": prep, "statuses": sts, "mismatches": bad, "first_refusal": first, **summary(a.L)}


def cell_a(profile):
    src = refs.source("PH5")
    rows = refs.cell_a_ref()
    chk = lambda o, row: [tuple(x) for x in o["values"]] == row[1] and o["ok"] == row[2]     # noqa: E731
    return [_run(c(profile, src), rows, chk) for c in arms_a.ARMS], rows


def cell_b(profile):
    src = dict(refs.source("PH3"), phi=refs.phi()["phi"])
    chk = lambda o, row: [tuple(x) for x in o["values"]] == row[1]                         # noqa: E731
    return [_run(c(profile, src), refs.cell_b_ref(), chk) for c in arms_b.ARMS_B]


def _fr(p):
    return F(p[0], p[1])


def seq_ok(res, ref, tape, curve):
    bad = 0
    for k, r in enumerate(res):
        if r["status"] != "OK":
            continue
        v, rr = r["outputs"]["values"], ref[k]
        exp = [tuple(x) for x in rr["S1"]] + ([] if tape == "S1" else [tuple(x) for x in rr["S2_add"]])
        bad += [tuple(x) for x in v[:len(exp)]] != exp
        if tape == "S3":
            sig = _fr(rr["S2_add"][2])
            d = sig * sig
            bad += (_fr(v[7]), _fr(v[8])) != (_fr(rr["S3_kappa"]) * d, d)
            if k >= 1:
                bad += _fr(res[k]["outputs"]["inc_prev"]) != _fr(ref[k - 1]["S3_arc_increment_to_next"])
    return bad


def seq(profile, curves=("PH3", "PH5")):
    out = []
    for curve in curves:
        ref, src = refs.seq_ref(curve), refs.source(curve)
        for cls in SEQ_ARMS:
            for tape in ("S1", "S2", "S3"):
                a = cls(profile, src, tape)
                prep = a.prepare()
                res = a.run_tape() if prep is None else []
                sts = [st(r) for r in res]
                first = next((r["event"] for r in res if r["status"] == "REFUSED"), None)
                out.append({"curve": curve, "arm": a.name, "tape": tape, "prep": prep, "statuses": sts,
                            "mismatches": seq_ok(res, ref, tape, curve), "first_refusal": first, **summary(a.L)})
    return out
