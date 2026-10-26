"""Measured instrumentation for the GEO-I1 program. Run: python3 -B -I research/geo_i1/report.py"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gi_engine as E       # noqa: E402
import gi_scene as S        # noqa: E402
import gi_session as G      # noqa: E402

W = S.WEIGHT


def ops(c):
    return (c["bound"] * W["bound"] + c["point"] * W["point"] + c["table_evals"] * W["table_eval"]
            + c["table_scalings"] * W["scaling"] + c["cert_compare"] * W["cert_compare"])


def run(**kw):
    s = G.Session(**kw)
    for _, cmd in G.PROGRAM:
        if cmd:
            s.command(cmd)
        s.query_all(_)
    return s


s = run()
tot = {n: Counter(e.ctr) for n, (e, _) in s.engines.items()}
tot["flat"], tot["exh_cached"] = Counter(s.flat.ctr), Counter(s.exh.ctr)
tot["exh_uncached"] = Counter({"point": s.oracle_ctr["oracle_point"]})
print("approach            bound point table_evals scalings reused compare  weighted_ops")
for n, c in tot.items():
    print(f"{n:18s} {c['bound']:6d} {c['point']:5d} {c['table_evals']:11d} {c['table_scalings']:8d} "
          f"{c['reused']:6d} {c['cert_compare']:7d} {ops(c):13d}")
print("footprint:", s.footprint())
print("coordinate baseline: materialisations", s.coord_ctr["materialise"], "points", s.coord_ctr["coord_point"],
      "refused steps:", [r["step"] for r in s.log if r["status"] == "OK" and
                         any("refused" in v["coord"] for v in r["shapes"].values())])
print("REL-1 coordinate materialisations (whole program):", s.rel.count["materialise"],
      "REL-1 ops:", sum(v.total() for v in s.rel.cost.values()))
print("per step (new tests = bound+point):")
for r in s.log:
    if r["status"] != "OK":
        print(f"  {r['step']:26s} {r['error']}")
        continue
    d = r["delta"]
    print(f"  {r['step']:26s} " + " ".join(f"{n}={d[n]['bound'] + d[n]['point']}" for n in
                                           ("H_exact_refine", "H_content_refine", "H_scaled_refine", "flat", "exh")))
