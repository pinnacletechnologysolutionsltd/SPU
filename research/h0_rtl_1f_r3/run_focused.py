#!/usr/bin/env python3
"""Deterministic focused runner for the experimental H0-RTL-1F-R3 simulations.

Compiles the explicit source list, runs the seven focused cases, the four
negative controls and the independent arithmetic oracle. Writes logs and a
summary under a new --output directory (refuses to overwrite). Not a release test.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
R3 = "research/h0_rtl_1f_r3/"
CASES = [("normal", [], "H0_RTL_1F EXPERIMENTAL PASS")] + [
    (n, ["+" + n], "CONTROL %s PASS" % n)
    for n in ("stopped", "collisions", "stale_issue", "before_accept", "duplicate", "held_start")]


def run(cmd, log):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
    text = p.stdout + p.stderr
    log.write_text(text)
    return p.returncode, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    out = Path(ap.parse_args().output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    lines, ok = [], True
    for f in sorted(l.split()[-1] for l in (ROOT / R3 / "sources.f").read_text().split("\n")
                    if l.startswith(("hardware", "research"))):
        lines.append("SOURCE %s %s" % (hashlib.sha256((ROOT / f).read_bytes()).hexdigest(), f))
    vvp = out / "test.vvp"
    rc, _ = run(["iverilog", "-g2012", "-s", "cpu_check", "-o", str(vvp), "-f", R3 + "sources.f"], out / "compile.log")
    if rc:
        sys.exit("compile failed")
    for name, args, expect in CASES:
        rc, text = run(["vvp", str(vvp)] + args, out / (name + ".log"))
        good = rc == 0 and expect in text and "FAIL" not in text
        ok &= good
        lines.append("CASE %s %s" % (name, "PASS" if good else "FAIL"))
    rc, text = run([sys.executable, "-I", R3 + "controls.py", "--output", str(out / "controls")], out / "controls.log")
    ok &= rc == 0
    lines += [("CONTROL " + l) for l in text.splitlines()] or ["CONTROL none"]
    rc, text = run([sys.executable, "-I", R3 + "independent_oracle.py"], out / "oracle.log")
    ok &= rc == 0 and "INDEPENDENT_ARITHMETIC_ORACLE PASS" in text
    lines.append("ORACLE " + ("PASS" if rc == 0 else "FAIL"))
    lines.append("H0_RTL_1F_R3_FOCUSED " + ("PASS" if ok else "FAIL"))
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
