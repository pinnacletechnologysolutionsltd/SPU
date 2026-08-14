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

Usage
-----
    python3 tools/board_build_check.py                 # check every entry
    python3 tools/board_build_check.py --only spu4     # substring filter
    python3 tools/board_build_check.py --record        # rewrite the manifest
    python3 tools/board_build_check.py --self-test     # prove it can fail

Builds are slow (minutes each), so this is deliberately not wired into
`run_all_tests.py`.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hardware" / "boards" / "board_build_manifest.json"
BUILD_TIMEOUT = 3600


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

    try:
        r = subprocess.run(["bash", str(script)], cwd=ROOT, capture_output=True,
                           text=True, timeout=BUILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return "BUILD_TIMEOUT", None, f"exceeded {BUILD_TIMEOUT}s"

    if r.returncode != 0:
        tail = [ln for ln in (r.stdout + r.stderr).splitlines()
                if "ERROR" in ln or "Unable to find legal" in ln]
        return "BUILD_FAILED", None, (tail[-1] if tail else f"exit {r.returncode}")

    if not artifact.exists():
        return "NO_ARTIFACT", None, str(artifact)

    return "BUILT", sha256_file(artifact), ""


def check(entries, record):
    results, tools = [], toolchain_versions()
    for entry in entries:
        name = entry["name"]
        print(f"[{name}] building ...", flush=True)
        status, actual, detail = build_one(entry)

        if status != "BUILT":
            print(f"[{name}] {status}: {detail}")
            results.append((name, status, detail))
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
    """Prove the comparison can fail.

    A check that has never been observed failing is not evidence.  This
    corrupts the expected hash of the cheapest entry in memory and confirms
    the comparison reports DIFFERS.  Nothing on disk is modified.
    """
    if not entries:
        print("self-test: no entries")
        return 1
    entry = dict(sorted(entries, key=lambda e: e.get("approx_seconds", 9999))[0])
    real = entry.get("sha256")
    if not real:
        print(f"self-test: {entry['name']} has no baseline; run --record first")
        return 1

    entry["sha256"] = "0" * 64
    print(f"self-test: building {entry['name']} against a deliberately wrong hash")
    results, _ = check([entry], record=False)
    status = results[0][1]
    if status == "DIFFERS":
        print(f"self-test: PASS -- comparison reported DIFFERS as required")
        print(f"self-test: (true hash {real[:16]} is unchanged on disk)")
        return 0
    print(f"self-test: FAIL -- expected DIFFERS, got {status}")
    return 1


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
    bad = [r for r in results if r[1] != "REPRODUCES"]
    for name, status, detail in results:
        print(f"  {status:<14} {name}")
    print(f"\n{len(results) - len(bad)} reproduce, {len(bad)} not")
    if bad:
        print("\nA DIFFERS is not automatically a bug -- it means the artifact")
        print("changed and no one recorded that it was meant to. If the change")
        print("was intended, rerun with --record so it appears in review.")
    print("===================================================")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
