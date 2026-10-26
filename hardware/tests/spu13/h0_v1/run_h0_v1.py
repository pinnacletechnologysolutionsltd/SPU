#!/usr/bin/env python3
"""H0-V1 directed instruction-acceptance probes: build, run and compare with fixed expectations.

  python3 hardware/tests/spu13/h0_v1/run_h0_v1.py [--skip-core]

Not registered in run_all_tests.py. Compiles into a temporary directory, writes nothing to the
repository, and compares the normalized probe output with expected/*.txt. Mismatches are
reported and never rewritten; there is no option to regenerate expectations.
The core probe takes about 70 seconds. Requires iverilog and vvp.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DIRS = ["hardware/rtl", "hardware/rtl/arch", "hardware/rtl/common", "hardware/rtl/common/prim",
        "hardware/rtl/common/sync", "hardware/rtl/core", "hardware/rtl/core/shared",
        "hardware/rtl/core/spu13", "hardware/rtl/core/spu4", "hardware/rtl/gpu", "hardware/rtl/hal",
        "hardware/rtl/math", "hardware/rtl/accel", "hardware/rtl/top", "hardware/rtl/triage",
        "hardware/rtl/peripherals", "hardware/rtl/peripherals/artery", "hardware/rtl/peripherals/audio",
        "hardware/rtl/peripherals/bio", "hardware/rtl/peripherals/graphics", "hardware/rtl/peripherals/io",
        "hardware/rtl/peripherals/memory", "hardware/rtl/peripherals/storage",
        "hardware/rtl/peripherals/video", "hardware/tests/common", "hardware/vendor/gowin",
        "hardware/vendor/ice40", "hardware/boards/tang_primer_25k"]
EXTRA = ["hardware/tests/common/sim_spu_gowin_mult32.v"]  # multi-module file iverilog cannot find by name
CASES = [("core", "h0v1_core_probe", EXTRA), ("sidecar", "h0v1_sidecar_probe", [])]
KEEP = re.compile(r"^(==|RES|  c=|   )")


def normalize(text):
    return [ln.rstrip() for ln in text.splitlines() if KEEP.match(ln)]


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def main():
    skip_core = "--skip-core" in sys.argv
    print("source:", run(["git", "rev-parse", "HEAD"]).stdout.strip())
    print("iverilog:", run(["iverilog", "-V"]).stdout.splitlines()[0])
    libs = [a for d in DIRS for a in ("-y", d, "-I", d)]
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, top, extra in CASES:
            if skip_core and name == "core":
                continue
            vvp = Path(tmp) / f"{name}.vvp"
            comp = run(["iverilog", "-g2012", *libs, *extra, "-s", top, "-o", str(vvp), str(HERE / f"{top}.v")])
            if comp.returncode:
                print(f"FAIL {name}: compile error\n{comp.stderr[:400]}")
                bad.append(name)
                continue
            sim = run(["vvp", str(vvp)], timeout=900)
            got = normalize(sim.stdout)
            want = normalize((HERE / "expected" / f"{name}.txt").read_text())
            ok = sim.returncode == 0 and got == want and bool(got)
            print(("PASS " if ok else "FAIL ") + name + f" ({len(got)} lines)")
            if not ok:
                bad.append(name)
                diff = [(i, w, g) for i, (w, g) in enumerate(zip(want, got)) if w != g][:3]
                print("  first differences (index, expected, got):", diff, "lengths", len(want), len(got))
    print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
