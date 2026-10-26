#!/usr/bin/env python3
"""Summarise the Karatsuba sidecar P&R A/B sweep.

Reads the per-build metrics the build script emits and reports, per
(spin, arm): the guard_clk Fmax distribution across seeds, the constraint
margin, and the area figures.

Deliberately does NOT report a significance test. With a seed spread of
~12 MHz around an arm difference of ~2-3 MHz, n=10 cannot resolve the
difference, and a p-value here would imply a precision the data does not
have. The questions this sweep CAN answer are: does the candidate hold the
constraint on every seed, and what does it cost in area.

Usage: python3 zk_analyse.py [campaign_dir]
"""
import json
import glob
import os
import re
import sys
import statistics as st
import subprocess

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip() or os.getcwd()
camp = sys.argv[1] if len(sys.argv) > 1 else None

files = sorted(glob.glob(os.path.join(REPO, "build/metrics/artix7_100t_TENSEGRITY*_ZK*_S*.json")))

# A killed or never-run build leaves the PREVIOUS campaign's metrics file sitting
# on disk under the same name. Seed-number completeness cannot see that: the seed
# is "present", just stale by two weeks. Filter to the campaign window instead.
# Without this the 2026-08-08 run silently absorbed the 07-31 PROBE ZK1 S1 build
# and reported n=10 for a cell that actually has 9.
CAMP_START = None
if camp:
    prov = os.path.join(camp, "provenance.txt")
    if os.path.exists(prov):
        for ln in open(prov):
            if ln.startswith("started_utc="):
                CAMP_START = ln.split("=", 1)[1].strip()
    if CAMP_START is None:
        print(f"FATAL: {prov} has no started_utc; cannot separate this campaign "
              f"from stale metrics on disk.")
        raise SystemExit(1)
    kept = []
    for f in files:
        gen = json.load(open(f)).get("generated_utc", "")
        (kept if gen >= CAMP_START else None) is not None and gen >= CAMP_START and kept.append(f)
    dropped = len(files) - len(kept)
    files = kept
    print(f"Campaign filter: started_utc={CAMP_START}; kept {len(files)}, "
          f"dropped {dropped} stale metrics file(s) predating this campaign.")
    print()

rows = []
for f in files:
    m = re.search(r"TENSEGRITY(\w+?)_ZK(\d)_S(\d+)", os.path.basename(f))
    if not m:
        continue
    d = json.load(open(f))
    fm = d.get("fmax", {})
    g = fm.get("guard_clk", {})
    u = d.get("log_utilization", {})
    rows.append(dict(
        spin=m.group(1), arm=int(m.group(2)), seed=int(m.group(3)),
        fmax=g.get("achieved_mhz"), cons=g.get("constraint_mhz"),
        status=g.get("status"),
        lut=u.get("SLICE_LUTX", {}).get("used"),
        ff=u.get("SLICE_FFX", {}).get("used"),
        dsp=u.get("DSP48E1", {}).get("used"),
        commit=d.get("git_commit"),
    ))

commits = sorted({r["commit"] for r in rows if r["commit"]})
print(f"builds: {len(rows)}   commits present: {commits}")

# collect_fpga_metrics.py stamps git_commit with HEAD *at collection time*, not
# the commit the design was built from. A long sweep therefore picks up any
# commit made while it runs -- three docs commits landed during the 2026-08-08
# campaign. So a bare commit-count check produces false alarms.
#
# What actually decides comparability is whether the SOURCE changed. Ask git.
if len(commits) > 1:
    src = []
    for a, b in zip(commits, commits[1:]):
        try:
            out = subprocess.run(["git", "diff", "--name-only", a, b],
                                 cwd=REPO, capture_output=True, text=True, check=True).stdout
        except Exception as e:                       # noqa: BLE001
            print(f"  WARNING: cannot compare {a}..{b} ({e}); treat as UNVERIFIED.")
            src = None
            break
        src += [p for p in out.split()
                if p.startswith(("hardware/", "software/", "tools/"))]
    if src is None:
        pass
    elif src:
        print("  WARNING: builds span commits that changed SOURCE -- arms are NOT comparable:")
        for p in sorted(set(src)):
            print(f"    {p}")
        print("  This is the defect in the 2026-07-22 sweep. Filter to one commit.")
    else:
        print("  OK: the differing commits touched documentation only; no source changed,")
        print("      so every build came from identical RTL. Comparable.")
print()

ARM = {0: "reference", 1: "candidate"}

# Completeness check. A cell reporting n=9 because one build was killed looks
# identical to a cell that was only ever run nine times -- and quoting a
# distribution without declaring the missing seed is precisely what
# ZPHI_KARATSUBA_SWAP_CRITERIA.md criterion 2 forbids. State it loudly.
EXPECTED_SEEDS = {1, 2, 3, 5, 7, 11, 13, 17, 19, 23}
print("Completeness:")
_missing_any = False
for _spin in sorted({r["spin"] for r in rows}):
    for _arm in (0, 1):
        got = {r["seed"] for r in rows if r["spin"] == _spin and r["arm"] == _arm}
        if not got:
            continue
        missing = EXPECTED_SEEDS - got
        if missing:
            _missing_any = True
            print(f"  {_spin} {ARM[_arm]}: n={len(got)} of {len(EXPECTED_SEEDS)} "
                  f"-- MISSING seed(s) {sorted(missing)}")
        else:
            print(f"  {_spin} {ARM[_arm]}: n={len(got)} complete")
if _missing_any:
    print("  Any distribution from a cell above must be quoted with its missing")
    print("  seeds declared. See build/zk_pnr_campaign/*/NONCONVERGED_*.md.")
print()
hdr = f"{'spin':<7}{'arm':<11}{'n':>3}{'min':>8}{'med':>8}{'max':>8}{'spread':>8}{'cons':>7}{'worst margin':>14}{'all pass':>10}"
print(hdr)
print("-" * len(hdr))
summary = {}
for spin in sorted({r["spin"] for r in rows}):
    for arm in (0, 1):
        v = [r["fmax"] for r in rows if r["spin"] == spin and r["arm"] == arm and r["fmax"]]
        if not v:
            continue
        cons = next(r["cons"] for r in rows if r["spin"] == spin and r["arm"] == arm)
        ok = all(r["status"] == "PASS" for r in rows if r["spin"] == spin and r["arm"] == arm)
        summary[(spin, arm)] = v
        print(f"{spin:<7}{ARM[arm]:<11}{len(v):>3}{min(v):>8.2f}{st.median(v):>8.2f}{max(v):>8.2f}"
              f"{max(v)-min(v):>8.2f}{cons:>7.0f}{min(v)-cons:>13.2f} {'YES' if ok else 'NO':>9}")

print()
print("Area (deterministic per arm -- synthesis is seed-independent, gate-verified):")
ah = f"{'spin':<7}{'arm':<11}{'LUTX':>8}{'FFX':>8}{'DSP':>6}"
print(ah)
print("-" * len(ah))
for spin in sorted({r["spin"] for r in rows}):
    base = {}
    for arm in (0, 1):
        vals = {(r["lut"], r["ff"], r["dsp"]) for r in rows if r["spin"] == spin and r["arm"] == arm}
        if not vals:
            continue
        if len(vals) > 1:
            print(f"{spin:<7}{ARM[arm]:<11}  INCONSISTENT across seeds: {sorted(vals)}")
            continue
        lut, ff, dsp = vals.pop()
        base[arm] = (lut, ff, dsp)
        print(f"{spin:<7}{ARM[arm]:<11}{lut:>8}{ff:>8}{dsp:>6}")
    if 0 in base and 1 in base:
        d = [b - a for a, b in zip(base[0], base[1])]
        print(f"{spin:<7}{'delta':<11}{d[0]:>+8}{d[1]:>+8}{d[2]:>+6}")

print()
print("Reading:")
for spin in sorted({r["spin"] for r in rows}):
    a, b = summary.get((spin, 0)), summary.get((spin, 1))
    if not (a and b):
        continue
    overlap = not (max(a) < min(b) or max(b) < min(a))
    print(f"  {spin}: reference median {st.median(a):.2f} vs candidate {st.median(b):.2f} MHz; "
          f"ranges {'OVERLAP' if overlap else 'are DISJOINT'} "
          f"(ref {min(a):.1f}-{max(a):.1f}, cand {min(b):.1f}-{max(b):.1f}).")
    if overlap:
        print("    -> seed choice dominates the arm difference; no Fmax claim is supportable.")
