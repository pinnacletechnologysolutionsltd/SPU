#!/usr/bin/env python3
"""NUM-SOM-2: production SOM comparator vs the experimental signed-P fixture.

  python3 -I hardware/tests/spu13/num_som_2/run_num_som_2.py [--expected DIR]

Not registered in run_all_tests.py. Builds and runs everything in a temporary directory, writes nothing to
the repository, and compares with expected/*. Mismatches are reported and never rewritten; there is no option
to regenerate expectations. Requires iverilog and vvp. Takes about 30 seconds.
"""
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import cmp_vectors  # noqa: E402
import fixture_build  # noqa: E402
import som2_models as m2  # noqa: E402
from cases2 import CASES  # noqa: E402

RTL = ROOT / "hardware/rtl/core/spu13"
PROD, BRAM = RTL / "spu_som_bmu.v", RTL / "spu_som_weight_bram.v"
FIXTURE = HERE / "spu_som_bmu_expsgn.v"
TRAIN = RTL / "spu_som_train.v"
TESTS = ROOT / "hardware/tests/spu13"
KEEP = re.compile(r"^(CASE|RES|CMP|DONE|TIMEOUT)")
CONFIGS = [("wired", [], 0, 1), ("control", ["-DCTRL"], 1, 0)]


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)


def build_run(tmp, name, srcs, top, defs=(), plus=(), cwd=None):
    vvp = Path(tmp) / f"{name}.vvp"
    c = sh(["iverilog", "-g2012", *defs, "-s", top, "-o", str(vvp), *map(str, srcs)])
    if c.returncode:
        raise RuntimeError(f"{name}: compile error\n{c.stderr[:400]}")
    return sh(["vvp", str(vvp), *plus], cwd=cwd or tmp).stdout


def legacy(tmp):
    lines, outs = [], {}
    work = Path(tmp) / "legacy"
    (work / "build").mkdir(parents=True)
    for tb, extra in (("spu13_som_bmu_tb", []), ("spu_som_train_tb", [TRAIN])):
        text = (TESTS / f"{tb}.v").read_text()
        for variant, mod, bmu in (("production", "spu_som_bmu", PROD), ("experimental", "spu_som_bmu_expsgn", FIXTURE)):
            t = work / f"{tb}_{variant}.v"
            t.write_text(text.replace("spu_som_bmu #(", f"{mod} #("))
            out = build_run(tmp, f"{tb}_{variant}", [t, bmu, BRAM, *extra], tb, cwd=work)
            keep = [re.sub(r"\s+", " ", x.strip()) for x in out.splitlines() if re.search(r"PASS|FAIL|CLASSIFY", x)]
            outs[(tb, variant)] = keep
            lines.append(f"{tb} {variant}: PASS lines={sum('PASS' in x for x in keep)} FAIL lines={sum('FAIL' in x for x in keep)}")
        lines.append(f"{tb}: outputs identical between variants: {outs[(tb, 'production')] == outs[(tb, 'experimental')]}")
    return lines


def collect():
    got = {}
    prod = PROD.read_text()
    if FIXTURE.read_text() != fixture_build.fixture(prod):
        raise RuntimeError("experimental fixture differs from production + documented patch (production changed?)")
    vecs = cmp_vectors.vectors()
    hx = "\n".join(cmp_vectors.hex_lines(vecs)) + "\n"
    got["vectors.sha256"] = [hashlib.sha256(hx.encode()).hexdigest() + "  vectors (34641 lines of 32 hex digits, newline-terminated)"]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "vectors.hex").write_text(hx)
        out = build_run(tmp, "cmp", [HERE / "cmp_probe.v", PROD, FIXTURE, BRAM], "cmp_probe",
                        plus=[f"+n={len(vecs)}", f"+vec={tmp}/vectors.hex"])
        rows = [(int(f[1]), int(f[2], 16), int(f[3], 16), int(f[4]), int(f[5]), int(f[6]), int(f[7]))
                for f in (ln.split() for ln in out.splitlines() if ln.startswith("V "))]
        assert len(rows) == len(vecs) and "DONE" in out, "comparator probe incomplete"
        summ, codes = m2.cmp_summary(rows)
        got["cmp_codes.txt"] = ["".join(codes[i:i + 100]) for i in range(0, len(codes), 100)]
        summary = summ
        logs = {}
        for cfg, defs, wp, wq in CONFIGS:
            for variant, mod, bmu in (("orig", "spu_som_bmu", PROD), ("new", "spu_som_bmu_expsgn", FIXTURE)):
                text = build_run(tmp, f"bmu_{variant}_{cfg}", [HERE / "numsom2_probe.v", bmu, BRAM], "numsom2_probe",
                                 defs=[*defs, f"-DBMU_MOD={mod}"])
                logs[(variant, cfg)] = text
                got[f"bmu_{variant}_{cfg}.txt"] = [ln.rstrip() for ln in text.splitlines() if KEEP.match(ln)]
        for cfg, _, wp, wq in CONFIGS:
            summary += [""] + m2.matrix(cfg.upper(), logs[("orig", cfg)], logs[("new", cfg)], wp, wq)
        for tag, wp, wq in (("wired", 0, 1), ("control", 1, 0)):
            b, w0, w1 = m2.box_bound(wp, wq)
            summary += [f"host-derived box bound ({tag}, provisional): |P|,|Q| <= {b}; worst accumulated key {w0} at B, {w1} at B+1"]
        summary += [""] + legacy(tmp)
    got["summary.txt"] = summary
    return got


def main():
    expected = HERE / "expected"
    if "--expected" in sys.argv:
        expected = Path(sys.argv[sys.argv.index("--expected") + 1])
    print("source:", sh(["git", "rev-parse", "HEAD"]).stdout.strip())
    print("iverilog:", sh(["iverilog", "-V"]).stdout.splitlines()[0])
    try:
        got = collect()
    except (RuntimeError, AssertionError) as exc:
        print("FAIL:", exc)
        return 1
    bad = []
    for name, lines in sorted(got.items()):
        want = (expected / name).read_text().splitlines()
        ok = [ln.rstrip() for ln in lines] == want
        print(("PASS " if ok else "FAIL ") + f"{name} ({len(lines)} lines)")
        if not ok:
            bad.append(name)
            diff = [(i, w, g) for i, (w, g) in enumerate(zip(want, lines)) if w != g][:2]
            print("  first differences (index, expected, got):", diff, "lengths", len(want), len(lines))
    print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
