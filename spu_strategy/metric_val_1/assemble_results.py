#!/usr/bin/env python3
"""Assemble results.json and the TERMINAL marker. Terminal outcome is infrastructure-only;
audit dispositions are assigned by a human reviewer from results.json (a clean exit is not an audit PASS)."""
import argparse, glob, json, os, time

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--mode", required=True); ap.add_argument("--start", type=float, required=True)
a = ap.parse_args(); out = a.out
stages = {}
for f in sorted(glob.glob(out + "/stages/*.json")):
    r = json.load(open(f)); stages[r["name"]] = r
    r["checks"] = []
    for line in open(f[:-5] + ".log", errors="replace"):
        if line.startswith("RESULT "):
            try: r["checks"].append(json.loads(line[7:]))
            except ValueError: r["checks"].append({"id": "UNPARSEABLE", "ok": None, "detail": line[:200]})
wall = round(time.time() - a.start, 2)
if a.mode == "selftest":
    exp = {"st_timeout": "TIMEOUT", "st_memcap": "NONZERO", "st_confine": "OK", "st_ok": "OK"}
    good = all(stages.get(k, {}).get("status") == v for k, v in exp.items())
    good &= os.path.exists(out + "/work/confine_probe.txt") and not os.path.exists("confine_probe.txt")
    good &= stages["st_timeout"]["wall_s"] < 4
    term = "SELFTEST_PASS" if good else "SELFTEST_FAIL"
    res = {"mode": "selftest", "terminal": term, "wall_s": wall, "stages": stages}
else:
    def rd(p):
        try: return open(out + "/logs/" + p).read()
        except OSError: return None
    integ = dict(l.split("=", 1) for l in (rd("integrity.txt") or "").splitlines() if "=" in l)
    ok_src = integ.get("src_tree_pre") == integ.get("src_tree_post") and bool(integ.get("src_tree_pre"))
    ok_clone = rd("clone_status_pre.txt") == "" and rd("clone_status_post.txt") == ""
    ok_wt = rd("wt_hash_pre.txt") == rd("wt_hash_post.txt") and rd("wt_hash_pre.txt")
    infra_bad = [k for k, v in stages.items() if v["status"] in ("TIMEOUT", "SKIPPED_BUDGET")]
    term = "RUN_COMPLETE" if (ok_src and ok_clone and ok_wt and not infra_bad) else "RUN_INTEGRITY_OR_INFRA_FAILURE"
    res = {"mode": "run", "terminal": term, "wall_s": wall, "wall_budget_s": 900,
           "integrity": {"src_unchanged": ok_src, "clone_clean_pre_post": ok_clone, "worktree_files_unchanged": bool(ok_wt)},
           "infra_problems": infra_bad, "identity": integ,
           "nonzero_stages": [k for k, v in stages.items() if v["status"] == "NONZERO"],
           "peak_maxrss_kib": max([v.get("maxrss_kib", 0) for v in stages.values()] or [0]),
           "note": "Dispositions UNASSIGNED: reviewer classifies each check per contract §3.",
           "stages": stages}
json.dump(res, open(out + "/results.json", "w"), indent=1)
open(out + "/TERMINAL", "w").write(term + "\n")
