#!/usr/bin/env python3
"""Evidence of what the CURRENT RTL does versus the exact oracle and the RTL_UNSAFE classification.

Run: python3 -B -I research/som_rp0/rtl_compare.py --harness build/som_rp0/harness [--n 600]
Needs iverilog/vvp (host simulation only). Claims checked on the in-domain accepted cases:
  1. the arithmetic emulator in oracle_compare.py equals the real RTL on EVERY vector (validates it);
  2. every vector the C code classifies RTL-safe equals the exact oracle in the real RTL (no flag);
  3. count vectors where the real RTL differs from the oracle (confirmed-defect inventory).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import oracle_compare as OC  # noqa: E402

RTL = ["hardware/rtl/core/spu13/spu_som_bmu.v", "hardware/rtl/core/spu13/spu_som_weight_bram.v"]


def word(c):
    return ((c[1] & 0x3FFFF) << 18) | (c[0] & 0x3FFFF)


def max_box_d(harness, a, b):
    lo, hi = 0, 131071
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if OC.run(harness, [f"BOX {a} {b} {mid}"])[0] == "BOX 1":
            lo = mid
        else:
            hi = mid - 1
    return lo


def box_cases(harness):
    """Tightness of the map-level certificate: at its maximal D every node is RTL-safe, at D+1 the
    worst-case input (all Delta = +D, weights (a,b) >= 0) is not. Returns [(tag, nodes, r, x, maxD)]."""
    out = []
    for a, b in ((1, 0), (1, 1), (5, 2), (100, 3), (1000, 0), (37, 21)):
        d = max_box_d(harness, a, b)
        for dd in (d, d + 1):
            nodes = [(i, i, [(0, 0)] * 4) for i in range(7)]
            out.append((f"box_{a}_{b}_{'at' if dd == d else 'over'}", nodes, [(a, b)] * 4, [(dd, dd)] * 4, d))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", required=True)
    ap.add_argument("--n", type=int, default=600)
    a = ap.parse_args()
    cases = [c for c in OC.build_cases() if c[5] == "OK" and c[4] == (0, 0)]
    step = max(1, len(cases) // a.n)
    cases = cases[::step][:a.n] + [c for c in cases if c[0].startswith("counterexample")]
    boxes = box_cases(a.harness)
    cases += [(t, n, r, x, (0, 0), "OK") for t, n, r, x, _ in boxes]
    words = []
    for _, nodes, r, x, _, _ in cases:
        for _, _, ws in sorted(nodes):
            words += [word(c) for c in ws]
        words += [word(c) for c in r] + [word(c) for c in x]
    (REPO / "build/som_rp0").mkdir(parents=True, exist_ok=True)
    (REPO / "build/som_rp0/rtl_vectors.mem").write_text("\n".join(f"{v:09x}" for v in words) + "\n")
    subprocess.run(["iverilog", "-g2012", "-o", "build/som_rp0/rtl_vectors.vvp", "research/som_rp0/som_rtl_vectors.v"] + RTL,
                   cwd=REPO, check=True)
    sim = subprocess.run(["vvp", "-n", "build/som_rp0/rtl_vectors.vvp", f"+N={len(cases)}"], cwd=REPO,
                         capture_output=True, text=True, timeout=55)
    rows = [l.split() for l in sim.stdout.splitlines() if l.startswith("R ")]
    assert len(rows) == len(cases), (len(rows), len(cases), sim.stdout[-300:])
    outs = OC.run(a.harness, [OC.line(n, r, x, t) for _, n, r, x, t, _ in cases])
    safe = unsafe = differ = differ_unsafe = 0
    equal_by_tag = {}
    for (tag, n, r, x, t, _), row, o in zip(cases, rows, outs):
        got, exp = OC.parse(o), OC.oracle_expect(n, r, x, t)
        bq, sq, gap, flag = int(row[4], 16), int(row[5], 16), int(row[6], 16), int(row[7])
        rtl = dict(best_id=int(row[2]), second_id=int(row[3]), best=(bq >> 32, OC.w(bq, 32)),
                   second=(sq >> 32, OC.w(sq, 32)), gap=(gap >> 32, OC.w(gap, 32)), flag=bool(flag))
        emu = OC.rtl_emulate(n, r, x)
        for k in ("best_id", "second_id", "best", "second", "gap", "flag"):
            assert rtl[k] == emu[k], (tag, k, rtl[k], emu[k])               # claim 1: emulator == real RTL
        equal = (not rtl["flag"] and rtl["best_id"] == exp["best_id"] and rtl["second_id"] == exp["second_id"]
                 and rtl["best"] == exp["best"] and rtl["second"] == exp["second"] and rtl["gap"] == exp["gap"])
        equal_by_tag[tag] = equal
        if got["rtl_status"] == OC.OK:
            assert equal, (tag, "RTL-safe vector differs in the real RTL", rtl, exp)   # claim 2
            safe += 1
        else:
            unsafe += 1
            differ_unsafe += not equal
        differ += not equal
    byt = {t: OC.parse(o) for (t, *_), o in zip(cases, outs)}
    for t, _, _, _, d in boxes:
        g = byt[t]
        if t.endswith("_at"):
            assert g["rtl_status"] == OC.OK and equal_by_tag[t], (t, g)             # certificate => RTL exact
        else:
            assert g["rtl_status"] == OC.RTL_UNSAFE and g["rtl_reason"] in (2, 3), (t, g)
            assert not equal_by_tag[t], (t, "tightness: the real RTL must fail at D+1")
    print("box certificate tight for", sorted({t.rsplit("_", 1)[0] for t, *_ in boxes}), {t.rsplit("_", 1)[0]: d for t, _, _, _, d in boxes})
    print(f"PASS emulator == real RTL on {len(cases)} vectors; {safe} RTL-safe vectors equal the exact oracle in the real RTL")
    print(f"real RTL differs from the exact oracle on {differ} vectors, all classified RTL_UNSAFE "
          f"({differ_unsafe}/{unsafe} unsafe vectors differ; the rest are conservative)")


if __name__ == "__main__":
    main()
