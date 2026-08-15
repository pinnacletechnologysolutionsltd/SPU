#!/usr/bin/env python3
"""Rebuild board targets and compare bitstream hashes against a manifest.

Why this exists
---------------
`run_all_tests.py` covers simulation only.  A board target can be completely
unbuildable while the suite reports a confident 193/193 -- which is exactly
what happened between 2026-07-17 and 2026-08-14, when
`build_25k_spu13_som_sidecar.sh` failed placement for four weeks with nothing
to notice.  The cause was 13 functionally-null lines: a UART constant-modulo
swapped for a down-counter, correct for Xilinx and catastrophic for Gowin.
Simulation could not see it, code review did not see it, and a line-count diff
would not have shown it either.  Only rebuild-and-compare finds this class.

What a hash mismatch means
--------------------------
DIFFERS is not automatically a bug.  It means the artifact changed and nobody
recorded that it was meant to.  Intentional changes are resolved by rerunning
with `--record`, which is a deliberate act that shows up in review.  Silent
drift is the thing being prevented.

The manifest is NOT silicon evidence
------------------------------------
`sha256` here is "what this tree builds today".  The hashes in
`docs/hardware_evidence.md` are "what was actually flashed to a board".  Those
are different claims and they drift apart legitimately.  Never copy a value
from this manifest into a silicon-evidence entry: that would assert a bitstream
was hardware-tested when it was not.

Three check modes
-----------------
`sha`         rebuild and compare the bitstream hash.  The strongest signal,
              and the default.  Only meaningful for narrow probes, whose small
              source set makes a hash change attributable.

`builds`      rebuild and require only that a bitstream appears.  For full-core
              spins, which absorb every core commit, so a hash mismatch says
              nothing but a BUILD_FAILED says everything (see 3.6e).

`utilisation` synthesise and pack, then compare LUT4 occupancy against a
              ceiling.  Placement and routing are skipped entirely.

Why `utilisation` exists
------------------------
Five Tang spins were retired on 2026-08-16 for exceeding the GW5A-25A's 23,040
LUT4 -- by 3%, 27%, 45%, 167% and 205%.  Not one was noticed while it crossed.
`rotc_probe` fit at 13,352 LUT4 when it was proven in silicon and reached
33,456; `southbridge` was recorded as not fitting at 25.5k and reached 61,439.

Neither `sha` nor `builds` can catch that early, because both need a build that
completes, and a design over capacity never completes.  They report the failure
only once it is total, and they take hours to do it.  Occupancy is the quantity
that actually moves, it moves gradually, and `nextpnr --pack-only` reports it
in about two seconds.  This mode watches the number instead of the outcome.

It is also the only mode that can watch a target which does not build at all.
`six_step_probe` sits at 96% and no longer routes; gating it on buildability
would fail every run and train everyone to ignore the check, while retiring it
would discard the one spin positioned to give early warning.

`max_lut4_pct` is the failing threshold.  Growth below it is reported but does
not fail -- the recorded `lut4` moves in the manifest diff, so it surfaces in
review rather than as noise.

Usage
-----
    python3 tools/board_build_check.py                 # check every entry
    python3 tools/board_build_check.py --only spu4     # substring filter
    python3 tools/board_build_check.py --record        # rewrite the manifest
    python3 tools/board_build_check.py --self-test     # prove it can fail

Builds are slow (minutes each), so this is deliberately not wired into
`run_all_tests.py`.  `utilisation` entries are cheap by comparison -- synthesis
dominates, and packing is seconds.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hardware" / "boards" / "board_build_manifest.json"
BUILD_TIMEOUT = 3600

# Defaults for utilisation entries; every current target is this Tang part.
# An entry may override any of them.
DEFAULT_DEVICE = "GW5A-LV25MG121NES"
DEFAULT_FAMILY = "GW5A-25A"
DEFAULT_VOPTS = ["sspi_as_gpio"]

# "Info: <tab> LUT4:   22212/  23040    96%"
_UTIL_RE = re.compile(r"^\s*Info:\s+(\w+):\s+(\d+)/\s*(\d+)\s+(\d+)%")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def toolchain_versions():
    """Record the toolchain. A silent toolchain swap changes every hash."""
    out = {}
    for name, cmd in (("yosys", ["yosys", "-V"]),
                      ("nextpnr-himbaechel", ["nextpnr-himbaechel", "--version"])):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            out[name] = (r.stdout + r.stderr).strip().splitlines()[0]
        except Exception as exc:                       # noqa: BLE001
            out[name] = f"(unavailable: {exc})"
    return out


def git_commit():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() or "(unknown)"
    except Exception:                                   # noqa: BLE001
        return "(unknown)"


def build_one(entry):
    """Run one build. Returns (status, actual_hash_or_None, detail)."""
    script = ROOT / entry["script"]
    artifact = ROOT / entry["artifact"]
    if not script.exists():
        return "MISSING_SCRIPT", None, str(script)

    # Remove any stale artifact first.  Without this a failed build leaves the
    # previous .fs in place and hashing it reports a pass for a build that did
    # not run -- a trap hit for real on 2026-08-14.
    if artifact.exists():
        artifact.unlink()

    # Per-entry override.  A spin that cannot route does not fail fast: the
    # irotc_spi livelock ran 8.5 h without converging and had to be killed by
    # hand (docs/hardware_evidence.md 3.6f).  Budget from approx_seconds so one
    # pathological target cannot stall the whole check.
    limit = entry.get("timeout_seconds") or min(
        BUILD_TIMEOUT, max(600, 10 * entry.get("approx_seconds", 120)))
    try:
        r = subprocess.run(["bash", str(script)], cwd=ROOT, capture_output=True,
                           text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        return "BUILD_TIMEOUT", None, f"exceeded {limit}s"

    if r.returncode != 0:
        tail = [ln for ln in (r.stdout + r.stderr).splitlines()
                if "ERROR" in ln or "Unable to find legal" in ln]
        return "BUILD_FAILED", None, (tail[-1] if tail else f"exit {r.returncode}")

    if not artifact.exists():
        return "NO_ARTIFACT", None, str(artifact)

    return "BUILT", sha256_file(artifact), ""


def measure_utilisation(entry):
    """Synthesise and pack one target; return (status, util_dict, detail).

    Deliberately stops before placement.  Placement and routing are where the
    hours go and where seed-dependent noise enters; occupancy is settled once
    packing is done, and is reproducible.
    """
    cfg = entry.get("utilisation") or {}
    for required in ("ys", "json"):
        if required not in cfg:
            return "BAD_ENTRY", None, f"utilisation.{required} missing"

    ys = ROOT / cfg["ys"]
    netlist = ROOT / cfg["json"]
    if not ys.exists():
        return "MISSING_SCRIPT", None, str(ys)

    # Drop any stale netlist, for the same reason build_one drops a stale
    # artifact: packing a previous run's netlist would report a healthy number
    # for a synthesis that did not happen.
    if netlist.exists():
        netlist.unlink()

    limit = entry.get("timeout_seconds") or min(
        BUILD_TIMEOUT, max(600, 10 * entry.get("approx_seconds", 120)))

    try:
        r = subprocess.run(["yosys", str(ys)], cwd=ROOT, capture_output=True,
                           text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        return "SYNTH_TIMEOUT", None, f"exceeded {limit}s"
    if r.returncode != 0:
        tail = [ln for ln in (r.stdout + r.stderr).splitlines() if "ERROR" in ln]
        return "SYNTH_FAILED", None, (tail[-1] if tail else f"exit {r.returncode}")
    if not netlist.exists():
        return "NO_NETLIST", None, str(netlist)

    cmd = ["nextpnr-himbaechel",
           "--device", cfg.get("device", DEFAULT_DEVICE),
           "--vopt", f"family={cfg.get('family', DEFAULT_FAMILY)}"]
    for vopt in cfg.get("vopts", DEFAULT_VOPTS):
        cmd += ["--vopt", vopt]
    if cfg.get("cst"):
        cmd += ["--vopt", f"cst={cfg['cst']}"]
    cmd += ["--json", str(netlist), "--pack-only"]

    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return "PACK_TIMEOUT", None, "exceeded 900s"
    if r.returncode != 0:
        tail = [ln for ln in (r.stdout + r.stderr).splitlines() if "ERROR" in ln]
        return "PACK_FAILED", None, (tail[-1] if tail else f"exit {r.returncode}")

    util = {}
    for line in (r.stdout + r.stderr).splitlines():
        m = _UTIL_RE.match(line)
        if m:
            util[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    if "LUT4" not in util:
        return "NO_UTILISATION", None, "no LUT4 line in pack output"
    return "PACKED", util, ""


def check_utilisation(entry, record):
    """Gate one target on LUT4 occupancy. Returns (status, detail)."""
    name = entry["name"]
    status, util, detail = measure_utilisation(entry)
    if status != "PACKED":
        print(f"[{name}] {status}: {detail}")
        return status, detail

    used, avail = util["LUT4"]
    pct = 100.0 * used / avail
    cfg = entry["utilisation"]
    ceiling = cfg.get("max_lut4_pct", 100)

    prev = cfg.get("lut4")
    delta = "" if prev is None else (
        " unchanged" if used == prev else f" {used - prev:+d} since baseline")

    if record:
        cfg["lut4"], cfg["lut4_avail"] = used, avail
        cfg["lut4_pct"] = round(pct, 1)
        print(f"[{name}] RECORDED {used}/{avail} = {pct:.1f}%")
        return "RECORDED", ""

    summary = f"{used}/{avail} = {pct:.1f}% (ceiling {ceiling}%){delta}"
    if pct > ceiling:
        print(f"[{name}] OVER {summary}")
        return "OVER", summary
    print(f"[{name}] FITS {summary}")
    return "FITS", summary


def check(entries, record):
    results, tools = [], toolchain_versions()
    for entry in entries:
        name = entry["name"]

        # Utilisation entries never place or route, so they take a separate
        # path entirely -- including targets that cannot build at all.
        if entry.get("check") == "utilisation":
            print(f"[{name}] synthesising + packing ...", flush=True)
            status, detail = check_utilisation(entry, record)
            if record and status == "RECORDED":
                entry["recorded_at_commit"] = git_commit()
                entry["recorded_toolchain"] = tools
            results.append((name, status, detail))
            continue

        print(f"[{name}] building ...", flush=True)
        status, actual, detail = build_one(entry)

        if status != "BUILT":
            print(f"[{name}] {status}: {detail}")
            results.append((name, status, detail))
            continue

        # Build-only entries: the gate is "does it still build", not "is the
        # bitstream identical".  Full-core spins compile most of the core, so
        # they absorb every core commit and a hash mismatch says nothing --
        # see docs/hardware_evidence.md 3.6e.  What they DO need is a
        # buildability check: the SOM sidecar was unbuildable for four weeks
        # and irotc_spi still is, and both were found by accident.
        if entry.get("check") == "builds":
            entry["last_built_sha256"] = actual
            if record:
                entry["recorded_at_commit"] = git_commit()
                entry["recorded_toolchain"] = tools
            print(f"[{name}] BUILDS {actual[:16]}")
            results.append((name, "BUILDS", actual))
            continue

        if record:
            entry["sha256"] = actual
            entry["recorded_at_commit"] = git_commit()
            entry["recorded_toolchain"] = tools
            print(f"[{name}] RECORDED {actual[:16]}")
            results.append((name, "RECORDED", actual))
            continue

        expected = entry.get("sha256")
        if not expected:
            print(f"[{name}] NO_BASELINE (run --record) got {actual[:16]}")
            results.append((name, "NO_BASELINE", actual))
        elif actual == expected:
            print(f"[{name}] REPRODUCES {actual[:16]}")
            results.append((name, "REPRODUCES", actual))
        else:
            print(f"[{name}] DIFFERS expected {expected[:16]} got {actual[:16]}")
            if entry.get("recorded_toolchain") not in (None, tools):
                print(f"[{name}]   note: toolchain differs from the recorded one")
            results.append((name, "DIFFERS", actual))
    return results, tools


def self_test(entries):
    """Prove every comparison this tool makes can fail.

    A check that has never been observed failing is not evidence.  Each mode
    with a baseline to corrupt gets its own case; a mode that is present in the
    manifest but untested here would be an unverified gate.  Nothing on disk is
    modified -- the entries are copied and corrupted in memory.
    """
    failures = []

    # --- sha mode: corrupt the expected hash, require DIFFERS ---------------
    hashed = [e for e in entries
              if e.get("check") not in ("builds", "utilisation") and e.get("sha256")]
    if hashed:
        entry = dict(sorted(hashed, key=lambda e: e.get("approx_seconds", 9999))[0])
        real = entry["sha256"]
        entry["sha256"] = "0" * 64
        print(f"self-test [sha]: building {entry['name']} against a wrong hash")
        status = check([entry], record=False)[0][0][1]
        if status == "DIFFERS":
            print(f"self-test [sha]: PASS -- reported DIFFERS as required")
            print(f"self-test [sha]: (true hash {real[:16]} unchanged on disk)")
        else:
            print(f"self-test [sha]: FAIL -- expected DIFFERS, got {status}")
            failures.append("sha")
    else:
        print("self-test [sha]: SKIP -- no hash-compared entries with a baseline")

    # --- utilisation mode: corrupt the ceiling, require OVER ----------------
    # The ceiling is lowered to 0%, so any design at all must exceed it.  This
    # proves the comparison is live; it does not depend on the target's size.
    utils = [e for e in entries if e.get("check") == "utilisation"]
    if utils:
        src = sorted(utils, key=lambda e: e.get("approx_seconds", 9999))[0]
        entry = json.loads(json.dumps(src))          # deep copy, config nested
        real_ceiling = entry["utilisation"].get("max_lut4_pct", 100)
        entry["utilisation"]["max_lut4_pct"] = 0
        print(f"self-test [utilisation]: packing {entry['name']} against a 0% ceiling")
        status = check([entry], record=False)[0][0][1]
        if status == "OVER":
            print(f"self-test [utilisation]: PASS -- reported OVER as required")
            print(f"self-test [utilisation]: (true ceiling {real_ceiling}% unchanged on disk)")
        else:
            print(f"self-test [utilisation]: FAIL -- expected OVER, got {status}")
            failures.append("utilisation")
    else:
        print("self-test [utilisation]: SKIP -- no utilisation entries")

    # `builds` mode has no baseline to corrupt: it is gated on the build's exit
    # status, which cannot be faked without breaking a real build.  Its failure
    # path was observed for real on 2026-08-15, when the widened check found
    # seven failing targets.

    if failures:
        print(f"\nself-test: FAIL -- {', '.join(failures)}")
        return 1
    print("\nself-test: PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="substring filter on entry name")
    ap.add_argument("--record", action="store_true",
                    help="rewrite the manifest from what this tree builds")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the comparison can fail, then exit")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"manifest not found: {MANIFEST}")
        return 2
    data = json.loads(MANIFEST.read_text())
    entries = data["targets"]
    if args.only:
        entries = [e for e in entries if args.only in e["name"]]
        if not entries:
            print(f"no entries match {args.only!r}")
            return 2

    if args.self_test:
        return self_test(entries)

    results, tools = check(entries, args.record)

    if args.record:
        data["recorded_toolchain"] = tools
        data["recorded_at_commit"] = git_commit()
        MANIFEST.write_text(json.dumps(data, indent=2) + "\n")
        print(f"\nmanifest written: {MANIFEST.relative_to(ROOT)}")
        return 0

    print("\n================ BOARD BUILD CHECK ================")
    OK = ("REPRODUCES", "BUILDS", "FITS")
    bad = [r for r in results if r[1] not in OK]
    for name, status, detail in results:
        suffix = f"  {detail}" if status in ("FITS", "OVER") else ""
        print(f"  {status:<14} {name}{suffix}")
    n_repro = sum(1 for r in results if r[1] == "REPRODUCES")
    n_build = sum(1 for r in results if r[1] == "BUILDS")
    n_fits = sum(1 for r in results if r[1] == "FITS")
    print(f"\n{n_repro} reproduce, {n_build} build (build-only), "
          f"{n_fits} fit (utilisation), {len(bad)} not")
    if bad:
        print("\nA DIFFERS is not automatically a bug -- it means the artifact")
        print("changed and no one recorded that it was meant to. If the change")
        print("was intended, rerun with --record so it appears in review.")
        print("A BUILD_FAILED is always a bug: that target cannot be built at")
        print("all from this tree.")
        print("An OVER means the design no longer fits its ceiling. That is a")
        print("scope decision, not a debugging task -- trim it, move it to a")
        print("larger part, or retire it. See hardware_evidence.md 3.6g.")
    print("===================================================")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
