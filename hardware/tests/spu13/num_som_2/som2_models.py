"""Host references for NUM-SOM-2: comparator interpretations, BMU result matrix, provisional box bound.

Reuses the NUM-SOM-1 fixed-width/exact models (hardware/tests/spu13/num_som_1/som_models.py).
Three references per case: the production RTL log (orig), the experimental signed-P fixture log (new),
and host models (fixed-width keys under signed-P / unsigned-P comparators; unbounded exact winner).
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "num_som_1"))
import som_models as m1  # noqa: E402
from cases2 import CASES  # noqa: E402

LIM = 2**31 - 1


def box_bound(wp, wq):
    """Largest B such that every node's accumulated P/Q key magnitude stays within signed 32 bits when every
    feature component is independently any value in [-B, B] (host-derived; per-feature maxima at box corners)."""
    def worst(b):
        w = 0
        for n in range(7):
            sp = sq = 0
            for xp, xq in m1.NODES[n]:
                kp = kq = 0
                for p in (-b, b):
                    for q in (-b, b):
                        dp, dq = p - xp, q - xq
                        a, c = dp * dp + 3 * dq * dq, 2 * dp * dq
                        kp, kq = max(kp, abs(a * wp + 3 * c * wq)), max(kq, abs(a * wq + c * wp))
                sp, sq = sp + kp, sq + kq
            w = max(w, sp, sq)
        return w
    b = 0
    while worst(b + 1) <= LIM and b + 1 < 2**17 - 3:
        b += 1
    return b, worst(b), worst(b + 1)


def cmp_summary(rows):
    """rows: (idx, lhs, rhs, old_lt, new_lt, lat_old, lat_new). Returns (summary lines, per-vector code string)."""
    bad_old = bad_new = diff = diff_msb = diff_nomsb = 0
    lats = set()
    codes = []
    for _, lhs, rhs, old, new, lo, ln in rows:
        a, b = m1.split(lhs), m1.split(rhs)
        bad_old += bool(old) != m1.lt_unsigned_p(a, b)
        bad_new += bool(new) != m1.lt_signed_p(a, b)
        if old != new:
            diff += 1
            if max(a[0], b[0]) >= 2**31:
                diff_msb += 1
            else:
                diff_nomsb += 1
        lats.add((lo, ln))
        codes.append(str(old * 2 + new))
    lines = [f"comparator vectors: {len(rows)}",
             f"production != unsigned-P exact model: {bad_old}",
             f"experimental != signed-P exact model: {bad_new}",
             f"production != experimental: {diff} (a P operand has bit 31 set: {diff_msb}; both P < 2^31: {diff_nomsb})",
             f"latency (production, experimental) cycles seen: {sorted(lats)}"]
    return lines, codes


def matrix(tag, orig_text, new_text, wp, wq):
    lo, ln = m1.parse(orig_text), m1.parse(new_text)
    lines = [f"=== {tag}: P-weight={wp} Q-weight={wq} ===",
             f"{'case':<15}{'RTLorig':>8}{'RTLnew':>7}{'fwSgn':>6}{'idNarr':>7}{'key32Diff':>10}  outcome"]
    counts = {}
    group = lambda nm: "big" if nm.startswith("BIG_") else "boundary" if nm.startswith("B_") else "base19"
    for i, (name, feats) in enumerate(CASES):
        nf = [(m1.sx(p, 18), m1.sx(q, 18)) for p, q in feats]
        keys = [m1.fw_key(nf, n, wp, wq) for n in range(7)]
        enc = [(k[0], k[1]) for k in keys]
        fws, fwu = m1.winner(enc, m1.lt_signed_p), m1.winner(enc, m1.lt_unsigned_p)
        idn = m1.winner([m1.ideal_key(nf, n, wp, wq) for n in range(7)], m1.lt_exact)
        kd = sum((m1.sx(k[0], 32), k[1]) != m1.ideal_key(nf, n, wp, wq) for n, k in enumerate(keys))
        for tagname, log, expect, lt in (("orig", lo, fwu, m1.lt_unsigned_p), ("new", ln, fws, m1.lt_signed_p)):
            r = log[i]
            assert r["best"] == expect, f"{name} {tagname}: RTL winner {r['best']} != host model {expect}"
            for n in range(7):
                assert r["acc"][n] == (keys[n][2] & (2**64 - 1), keys[n][3] & (2**64 - 1)), f"{name} {tagname} node{n} acc"
            for st, node, a, b, d in r["cmp"]:
                assert bool(d) == lt(m1.split(a), m1.split(b)), f"{name} {tagname}: comparator decision differs from model"
        o, n_ = lo[i]["best"], ln[i]["best"]
        if o == idn and n_ == idn:
            out = "ok-both"
        elif o != idn and n_ == idn:
            out = "FIXED-by-patch"
        elif o == idn and n_ != idn:
            out = "REGRESSED-by-patch"
        elif fws != idn:
            out = "residual-arithmetic" + ("" if o == n_ else " (winner changed)")
        else:
            out = "residual-other"
        key = (group(name), out.split(" ")[0])
        counts[key] = counts.get(key, 0) + 1
        lines.append(f"{name:<15}{o:>8}{n_:>7}{fws:>6}{idn:>7}{kd:>10}  {out}")
    for g in ("base19", "boundary", "big"):
        lines.append(f"outcome counts [{g}]: " + ", ".join(f"{k[1]}={v}" for k, v in sorted(counts.items()) if k[0] == g))
    return lines
