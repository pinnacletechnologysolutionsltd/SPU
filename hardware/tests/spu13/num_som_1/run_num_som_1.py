#!/usr/bin/env python3
"""NUM-SOM-1 directed SOM BMU probe: build, run and compare with fixed expectations.

  python3 -I hardware/tests/spu13/num_som_1/run_num_som_1.py [--expected DIR]

Not registered in run_all_tests.py. Compiles into a temporary directory and writes nothing to the
repository. Compares the normalized simulation output of both weight configurations and the derived
result matrix with expected/*.txt. Mismatches are reported and never rewritten; there is no option to
regenerate expectations. Requires iverilog and vvp. Runs in a few seconds.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import som_models  # noqa: E402

RTL = ["hardware/rtl/core/spu13/spu_som_bmu.v", "hardware/rtl/core/spu13/spu_som_weight_bram.v"]
CONFIGS = [("wired", [], 0, 1), ("control", ["-DCTRL"], 1, 0)]
KEEP = re.compile(r"^(CASE|QREG|ACC|CMP|RES|DONE|TIMEOUT)")


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def main():
    expected = HERE / "expected"
    if "--expected" in sys.argv:
        expected = Path(sys.argv[sys.argv.index("--expected") + 1])
    print("source:", run(["git", "rev-parse", "HEAD"]).stdout.strip())
    print("iverilog:", run(["iverilog", "-V"]).stdout.splitlines()[0])
    bad, matrix = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for name, defs, wp, wq in CONFIGS:
            vvp = Path(tmp) / f"{name}.vvp"
            comp = run(["iverilog", "-g2012", *defs, "-s", "numsom1_probe", "-o", str(vvp),
                        str(HERE / "numsom1_probe.v"), *RTL])
            if comp.returncode:
                print(f"FAIL {name}: compile error\n{comp.stderr[:400]}")
                bad.append(name)
                continue
            sim = run(["vvp", str(vvp)])
            got = [ln.rstrip() for ln in sim.stdout.splitlines() if KEEP.match(ln)]
            want = (expected / f"rtl_{name}.txt").read_text().splitlines()
            ok = sim.returncode == 0 and got == want and bool(got) and got[-1] == "DONE"
            print(("PASS " if ok else "FAIL ") + f"rtl_{name} ({len(got)} lines)")
            if not ok:
                bad.append(f"rtl_{name}")
                diff = [(i, w, g) for i, (w, g) in enumerate(zip(want, got)) if w != g][:3]
                print("  first differences (index, expected, got):", diff, "lengths", len(want), len(got))
            try:
                matrix += som_models.matrix(name.upper(), "\n".join(got), wp, wq) + [""]
            except AssertionError as exc:
                print(f"FAIL model {name}: {exc}")
                bad.append(f"model_{name}")
    want_m = (expected / "matrix.txt").read_text().splitlines()
    matrix = matrix[:-1]  # drop the separator after the last block
    ok = [ln.rstrip() for ln in matrix] == want_m
    print(("PASS " if ok else "FAIL ") + f"matrix ({len(matrix)} lines)")
    if not ok:
        bad.append("matrix")
    print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
