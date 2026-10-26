#!/usr/bin/env python3
"""SOM-RP0a: compare the exact C99 BMU (and its RTL_UNSAFE classification) with the Python oracle.

Run: python3 -B -I research/som_rp0/oracle_compare.py --harness build/som_rp0/harness
Oracle: software/lib/rational_som.py (read-only, unbounded integers). Also contains an emulator of the
CURRENT spu_som_bmu.v arithmetic, used only to check that RTL_UNSAFE is sound; the emulator is validated
against the real RTL by rtl_compare.py. RTL output is never treated as authoritative.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))
from lib.rational_som import (RationalSurd as RS, SomNode, find_bmu, classify, rs_lt, tiny_hex_fixture)  # noqa: E402

LO, HI = -(1 << 17), (1 << 17) - 1
OK, OVERFLOW, INVALID_MAP, NO_NODES, RTL_UNSAFE = 0, 1, 2, 3, 4


def w(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v


def rtl_emulate(nodes, r, x, thr=(0, 0)):
    """Arithmetic of spu_som_bmu.v (18-bit diff, 36-bit ring, 64-bit sums -> 32-bit fields) + cluster_reduce."""
    best = second = None
    flag = False
    for nid, label, ws in sorted(nodes):
        sp_tot = sq_tot = 0
        for (xp, xq), (wp_, wq_), (rp, rq) in zip(x, ws, r):
            dp, dq = w(xp - wp_, 18), w(xq - wq_, 18)
            sp = w(dp * dp + 3 * (dq * dq), 36)
            sqv = w(2 * dp * dq, 36)
            sp_tot += w(sp * rp + 3 * (sqv * rq), 36)
            sq_tot += w(sp * rq + sqv * rp, 36)
        flag |= not (0 <= sp_tot < 1 << 32 and -(1 << 31) <= sq_tot < 1 << 31)
        cand = (sp_tot & 0xFFFFFFFF, w(sq_tot, 32), nid, label)
        lt = lambda a, b: rs_lt(RS(a[0], a[1]), RS(b[0], b[1]))  # noqa: E731  (exact on the stored values)
        if best is None:
            best = cand
        elif second is None:
            best, second = (cand, best) if lt(cand, best) else (best, cand)
        elif lt(cand, best):
            best, second = cand, best
        elif lt(cand, second):
            second = cand
    gp, gq = (second[0] - best[0]) & 0xFFFFFFFF, w(second[1] - best[1], 32)
    amb = rs_lt(RS(second[0] - best[0] - thr[0], second[1] - best[1] - thr[1]), RS(0, 0)) or \
        (second[0] - best[0] == thr[0] and second[1] - best[1] == thr[1])
    return dict(best_id=best[2], second_id=second[2], label=best[3], best=(best[0], best[1]),
                second=(second[0], second[1]), gap=(gp, gq), ambiguous=amb, flag=flag)


def oracle_expect(nodes, r, x, thr):
    som_nodes = [SomNode(i, 0, 0, lab, tuple(RS(*c) for c in ws)) for i, lab, ws in nodes]
    res = find_bmu([RS(*c) for c in x], som_nodes, [RS(*c) for c in r])
    _, amb = classify(res, RS(*thr))
    return dict(best_id=res.best_node_id, second_id=res.second_node_id, label=res.cluster_label,
                best=(res.best_q.p, res.best_q.q), second=(res.second_q.p, res.second_q.q),
                gap=(res.confidence_gap.p, res.confidence_gap.q), has_second=res.has_second, ambiguous=amb)


def rtl_safe_expected(exp, nodes, r, x, thr):
    """Emulated RTL equals the exact result under the SOM1 field interpretation (P unsigned, Q signed)."""
    e = rtl_emulate(nodes, r, x, thr)
    return (not e["flag"] and e["best_id"] == exp["best_id"] and e["second_id"] == exp["second_id"]
            and e["label"] == exp["label"] and e["best"] == exp["best"] and e["second"] == exp["second"]
            and e["gap"] == exp["gap"] and e["ambiguous"] == exp["ambiguous"] and thr[0] >= 0), e


def reason_expected(exp, nodes, r, x, thr):
    """First failing condition, in the documented order, from exact big-int values (independent of the C code)."""
    for nid, _, ws in nodes:
        tp = tq = 0
        for (xp, xq), (wp_, wq_), (rp, rq) in zip(x, ws, r):
            dp, dq = xp - wp_, xq - wq_
            sp, sqv = dp * dp + 3 * dq * dq, 2 * dp * dq
            a, b = rp * sp + 3 * rq * sqv, rp * sqv + rq * sp
            if not (-(1 << 17) <= dp < 1 << 17 and -(1 << 17) <= dq < 1 << 17):
                return 1
            if not (-(1 << 35) <= a < 1 << 35 and -(1 << 35) <= b < 1 << 35):
                return 2
            tp, tq = tp + a, tq + b
        if not (0 <= tp < 1 << 32 and -(1 << 31) <= tq < 1 << 31):
            return 3
    gp, gq = exp["gap"]
    if exp["has_second"] and not (0 <= gp < 1 << 32 and -(1 << 31) <= gq < 1 << 31):
        return 4
    return 5 if thr[0] < 0 else 0


def line(nodes, r, x, thr):
    flat = lambda cs: " ".join(f"{p} {q}" for p, q in cs)  # noqa: E731
    body = " ".join(f"{i} {lab} {flat(ws)}" for i, lab, ws in nodes)
    return f"BMU {len(nodes)} {body} {flat(r)} {flat(x)} {thr[0]} {thr[1]}"


def parse(out):
    f = out.split()
    st = int(f[1])
    d = dict(status=st, best_id=int(f[2]), second_id=int(f[3]), label=int(f[4]), best=(int(f[5]), int(f[6])),
             second=(int(f[7]), int(f[8])), gap=(int(f[9]), int(f[10])), has_second=bool(int(f[11])),
             ambiguous=bool(int(f[12])))
    d.update(rtl_status=int(f[14]), rtl_reason=int(f[15]))
    return d


def run(harness, lines):
    p = subprocess.run([harness], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip().split("\n")


def rnd_map(rng, span, wspan, nn=7, surd=True):
    nodes = [(i, rng.randrange(7), [(rng.randint(-span, span - 1), rng.randint(-span, span - 1) if surd else 0)
                                    for _ in range(4)]) for i in range(nn)]
    r = [(rng.randint(-wspan, wspan - 1), rng.randint(-wspan, wspan - 1)) for _ in range(4)]
    return nodes, r


def corners(rng):
    pick = lambda: rng.choice((LO, HI, LO + 1, HI - 1, 0))  # noqa: E731
    nodes = [(i, i % 7, [(pick(), pick()) for _ in range(4)]) for i in range(7)]
    return nodes, [(pick(), pick()) for _ in range(4)], [(pick(), pick()) for _ in range(4)]


def build_cases():
    rng, cases = random.Random(20261020), []
    add = lambda tag, n, r, x, thr=(0, 0), expect="OK": cases.append((tag, n, r, x, thr, expect))  # noqa: E731
    tn, tw = tiny_hex_fixture()
    tiny = [(n.node_id, n.cluster_label, [(c.p, c.q) for c in n.weights]) for n in tn]
    trr = [(c.p, c.q) for c in tw]
    for _ in range(60):
        add("tiny", tiny, trr, [(rng.randint(-4, 4), rng.randint(-3, 3)) for _ in range(4)])
    doc = json.load(open(REPO / "software/models/iris_som_v1.json"))
    inodes = [(n["id"], n["class_label"], [(c["p"], c["q"]) for c in n["weights"]]) for n in doc["nodes"]]
    irr = [(c["p"], c["q"]) for c in doc["feature_weights"]]
    from som_trainer import parse_scaled_decimal  # noqa: E402
    for row in csv.reader(open(REPO / "software/tests/data/iris.csv")):
        if row:
            add("iris", inodes, irr, [(parse_scaled_decimal(v), 0) for v in row[:4]])
    z = [(0, 0)] * 4
    for _ in range(40):                                              # exact ties and zero gap
        nodes, r = rnd_map(rng, 50, 3)
        a, b = rng.sample(range(7), 2)
        nodes[b] = (nodes[b][0], nodes[b][1], list(nodes[a][2]))
        add("tie", nodes, r, [(rng.randint(-50, 50), rng.randint(-50, 50)) for _ in range(4)])
        add("tie_thr", nodes, r, [(rng.randint(-50, 50), rng.randint(-50, 50)) for _ in range(4)],
            (rng.randint(0, 500), rng.randint(-300, 300)))
    for _ in range(300):                                             # surd features, mixed-sign gaps
        nodes, r = rnd_map(rng, 120, 4)
        add("surd", nodes, r, [(rng.randint(-120, 120), rng.randint(-120, 120)) for _ in range(4)])
    for _ in range(300):                                             # whole domain, random
        nodes, r = rnd_map(rng, 1 << 17, 1 << 17)
        add("domain", nodes, r, [(rng.randint(LO, HI), rng.randint(LO, HI)) for _ in range(4)])
    for _ in range(400):                                             # both ends of every range
        nodes, r, x = corners(rng)
        add("corner", nodes, r, x)
    for span, wspan in ((9000, 1), (16383, 1), (16384, 1), (5181, 1), (5182, 1), (3000, 3), (400, 40)):
        for _ in range(25):                                          # around the RTL safe-region boundaries
            nodes, r = rnd_map(rng, span, wspan + 1, surd=False)
            add(f"rtl_edge_{span}_{wspan}", nodes, [(1 + rng.randrange(wspan), 0)] * 4 if wspan == 1 else r,
                [(rng.randint(-span, span), rng.randint(-span, span)) for _ in range(4)])
    for _ in range(20):                      # out-of-range difference with zero weights: RTL equal, C conservative
        nodes, _r = rnd_map(rng, 100, 2)
        add("diff_zero_weight", nodes, [(0, 0)] * 4, [(131071, 0), (0, 0), (0, 0), (0, 0)])
    pq = lambda p, q=0: (p, q)  # noqa: E731
    one = [pq(1)] * 4
    def probe(w0, r0, x0, x_all=None):
        nodes = [(i, i % 7, [pq(0)] * 3 + [w0]) for i in range(7)]
        return nodes, [pq(1)] * 3 + [r0], x_all or [pq(0)] * 3 + [x0]
    for tag, (n, r, x) in {"control": probe(pq(-20, 1), pq(1), pq(100, 3)),
                           "diffwrap": probe(pq(-131072), pq(1), pq(131071)),
                           "prodwrap": probe(pq(0), pq(16), pq(65536)),
                           "sumflag": probe(pq(0), pq(1), None, [pq(60000)] * 4)}.items():
        add("counterexample_" + tag, n, r, x)
    nodes, r = rnd_map(rng, 100, 3)
    x_ok = [(1, 1)] * 4
    for tag, bad in (("x_hi", (HI + 1, 0)), ("x_lo", (LO - 1, 0)), ("x_q_hi", (0, 1 << 17)),
                     ("x_int32max", (2147483647, 0)), ("x_int32min", (0, -2147483648))):
        add("overflow_" + tag, nodes, r, [bad] + x_ok[1:], expect="OVERFLOW")
    add("malformed_count6", nodes[:6], r, x_ok, expect="INVALID_MAP")
    add("malformed_count8", nodes + [(7, 0, nodes[0][2])], r, x_ok, expect="INVALID_MAP")
    add("malformed_dup_id", [nodes[0]] + [(0, 1, nodes[1][2])] + nodes[2:], r, x_ok, expect="INVALID_MAP")
    add("malformed_id7", nodes[:6] + [(7, 0, nodes[6][2])], r, x_ok, expect="INVALID_MAP")
    add("malformed_label7", nodes[:6] + [(6, 7, nodes[6][2])], r, x_ok, expect="INVALID_MAP")
    badw = [(i, l, list(ws)) for i, l, ws in nodes]
    badw[3][2][2] = (HI + 1, 0)
    add("malformed_node_coef", badw, r, x_ok, expect="INVALID_MAP")
    add("malformed_weight_coef", nodes, [(LO - 1, 0)] + r[1:], x_ok, expect="INVALID_MAP")
    add("malformed_int32min_weight", nodes, [(0, -2147483648)] + r[1:], x_ok, expect="INVALID_MAP")
    add("no_nodes", [], r, x_ok, expect="NO_NODES")
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()
    cases = build_cases()
    outs = run(args.harness, [line(n, r, x, t) for _, n, r, x, t, _ in cases])
    stats = dict(ok=0, refused=0, rtl_safe=0, rtl_unsafe=0, rtl_unsafe_but_emulated_equal=0)
    by_tag, by_reason = {}, {}
    names = {"OK": OK, "OVERFLOW": OVERFLOW, "INVALID_MAP": INVALID_MAP, "NO_NODES": NO_NODES}
    for (tag, n, r, x, thr, expect), o in zip(cases, outs):
        got = parse(o)
        assert got["status"] == names[expect], (tag, got["status"], expect)
        if expect != "OK":
            assert got["best_id"] == -1 + 0 or got["best_id"] == 0
            assert (got["best"], got["second"], got["gap"], got["has_second"], got["ambiguous"], got["label"]) == \
                ((0, 0), (0, 0), (0, 0), False, False, 0), (tag, "partial output on refusal")
            assert got["rtl_status"] == got["status"], tag
            stats["refused"] += 1
            continue
        exp = oracle_expect(n, r, x, thr)
        for k in ("best_id", "second_id", "label", "best", "second", "gap", "has_second", "ambiguous"):
            assert got[k] == exp[k], (tag, k, got[k], exp[k])
        stats["ok"] += 1
        safe, emu = rtl_safe_expected(exp, n, r, x, thr)
        assert got["rtl_reason"] == reason_expected(exp, n, r, x, thr), (tag, got["rtl_reason"])
        if got["rtl_status"] == OK:
            assert safe, (tag, "C says RTL-safe but the RTL arithmetic emulation differs", emu, exp)
            stats["rtl_safe"] += 1
        else:
            assert got["rtl_status"] == RTL_UNSAFE and got["rtl_reason"] in (1, 2, 3, 4, 5), (tag, got)
            stats["rtl_unsafe"] += 1
            by_reason[got["rtl_reason"]] = by_reason.get(got["rtl_reason"], 0) + 1
            stats["rtl_unsafe_but_emulated_equal"] += int(safe)
        by_tag.setdefault(tag.split("_")[0], [0, 0])[got["rtl_status"] != OK] += 1
    # comparator: boundary pairs of the surd order, including 2^60-scale Pell-style near ties
    rng, pairs = random.Random(7), []
    for da, db in ((-26, 15), (26, -15), (-7, 4), (97, -56), (-1351, 780)):    # da^2 - 3 db^2 = +-1
        for s in (1, 1 << 20, 1 << 40):
            pairs.append(((da * s, db * s), (0, 0)))
    for _ in range(4000):
        k = rng.choice((10, 30, 59))
        a = (rng.randint(-(1 << k), 1 << k), rng.randint(-(1 << (k - 1)), 1 << (k - 1)))
        b = (rng.randint(-(1 << k), 1 << k), rng.randint(-(1 << (k - 1)), 1 << (k - 1)))
        pairs += [(a, b), (a, a), (a, (a[0] + rng.choice((-1, 0, 1)), a[1] + rng.choice((-1, 0, 1))))]
    outs = run(args.harness, [f"CMP {a[0]} {a[1]} {b[0]} {b[1]}" for a, b in pairs])
    for (a, b), o in zip(pairs, outs):
        lt = rs_lt(RS(*a), RS(*b))
        assert o == f"CMP {int(lt)} {int(lt or a == b)}", (a, b, o)
    print(f"PASS {stats['ok']} accepted BMU cases bit-exact vs oracle; {stats['refused']} refusal fixtures "
          f"with no partial output; {len(pairs)} comparator pairs")
    print(f"RTL classification: safe={stats['rtl_safe']} unsafe={stats['rtl_unsafe']} (reasons {by_reason}), "
          f"unsafe-but-emulation-equal={stats['rtl_unsafe_but_emulated_equal']} (conservative)")
    print("per tag [rtl_safe, rtl_unsafe]:", by_tag)


if __name__ == "__main__":
    main()
