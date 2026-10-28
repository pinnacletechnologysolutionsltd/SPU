#!/usr/bin/env python3
"""NUM-SOM-4 Phase B: RPLU2 numeric-domain guard and atomic refusal indication, core-level directed simulation.

  python3 -I hardware/tests/spu13/num_som_4_phaseB/run_num_som_4_phaseB.py [--expected DIR]

Not registered in run_all_tests.py. Builds and runs in a temporary directory, writes nothing to the repository, compares with
expected/*. Mismatches are reported and never rewritten; there is no option to regenerate expectations. A simulator process must exit 0
as well as match (built-in negative control), and two mutated guards must be detected (built-in sensitivity controls).
The lockstep probes compare the current spu13_core with the previous one extracted from git (BASE_COMMIT). Needs iverilog >= 12 and vvp.
"""
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE_COMMIT = "2a9a9f12760bb13fb47bcf192b66f44645f35ef9"
CORE = "hardware/rtl/core/spu13/spu13_core.v"
DIRS = ["hardware/rtl", "hardware/rtl/arch", "hardware/rtl/common", "hardware/rtl/common/prim", "hardware/rtl/common/sync",
        "hardware/rtl/core", "hardware/rtl/core/shared", "hardware/rtl/core/spu13", "hardware/rtl/core/spu4", "hardware/rtl/gpu",
        "hardware/rtl/hal", "hardware/rtl/math", "hardware/rtl/accel", "hardware/rtl/top", "hardware/rtl/triage",
        "hardware/rtl/peripherals", "hardware/rtl/peripherals/artery", "hardware/rtl/peripherals/audio", "hardware/rtl/peripherals/bio",
        "hardware/rtl/peripherals/graphics", "hardware/rtl/peripherals/io", "hardware/rtl/peripherals/memory",
        "hardware/rtl/peripherals/storage", "hardware/rtl/peripherals/video", "hardware/tests/common", "hardware/vendor/gowin",
        "hardware/vendor/ice40", "hardware/boards/tang_primer_25k"]
EXTRA = ["hardware/tests/common/sim_spu_gowin_mult32.v"]
LIBS = [a for d in DIRS for a in ("-y", d, "-I", d)]
KEEP_PROBE = re.compile(r"^(==|CASE|SEQ|RST|HIST|OBS|TOTAL)")
# lockstep configurations: name, V2, PIPE, SOM, MODE
LOCKS = [("h0_noRPLU2", 1, 1, 0, 0), ("h0_inDomain2A", 1, 1, 0, 1), ("rplu2_cfg_only", 1, 0, 0, 2),
         ("legacy_som", 0, 0, 1, 2), ("no_rplu_no_som", 0, 0, 0, 2)]
NEG_CONTROL = 'module nc; initial begin $display("DONE"); $fatal(1, "forced nonzero exit"); end endmodule\n'


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)


def build_run(tmp, name, srcs, top, defs=()):
    vvp = Path(tmp) / f"{name}.vvp"
    c = sh(["iverilog", "-g2012", *defs, *LIBS, *EXTRA, "-s", top, "-o", str(vvp), *map(str, srcs)])
    if c.returncode:
        raise RuntimeError(f"{name}: compile error\n{c.stderr[:500]}")
    run = sh(["vvp", str(vvp)], cwd=tmp)
    if run.returncode:
        raise RuntimeError(f"{name}: simulator exited with status {run.returncode} (matching output is not a pass)")
    return run.stdout


def negative_control(tmp):
    src = Path(tmp) / "nc.v"
    src.write_text(NEG_CONTROL)
    try:
        build_run(tmp, "nc", [src], "nc")
    except RuntimeError:
        return True
    return False


def mutant_detected(tmp, name, old, new):
    text = (ROOT / CORE).read_text()
    assert text.count(old) == 1, f"mutation anchor not unique: {old}"
    mut = Path(tmp) / f"core_{name}.v"
    mut.write_text(text.replace(old, new))
    try:
        build_run(tmp, f"mut_{name}", [mut, HERE / "numsom4b_probe.v"], "numsom4b_probe")
    except RuntimeError as exc:
        return "simulator exited" in str(exc)
    return False


def collect(tmp):
    got = {}
    out = build_run(tmp, "probe", [HERE / "numsom4b_probe.v"], "numsom4b_probe")
    got["probe.txt"] = [ln.rstrip() for ln in out.splitlines() if KEEP_PROBE.match(ln)]
    base = sh(["git", "show", f"{BASE_COMMIT}:{CORE}"])
    if base.returncode:
        raise RuntimeError("cannot extract baseline core from git: " + base.stderr[:200])
    bsrc = Path(tmp) / "core_base.v"
    bsrc.write_text(re.sub(r"\bspu13_core\b", "spu13_core_base", base.stdout))

    def lock(cfg):
        name, v2, pipe, som, mode = cfg
        o = build_run(tmp, f"lock_{name}", [bsrc, HERE / "numsom4b_lock.v"], "numsom4b_lock",
                      defs=[f"-DLK_V2={v2}", f"-DLK_PIPE={pipe}", f"-DLK_SOM={som}", f"-DLK_MODE={mode}"])
        return [f"{name}: {ln.rstrip()}" for ln in o.splitlines() if ln.startswith("LOCK ")]
    with ThreadPoolExecutor(max_workers=5) as ex:
        got["lock.txt"] = [ln for res in ex.map(lock, LOCKS) for ln in res]
    return got


def main():
    expected = HERE / "expected"
    if "--expected" in sys.argv:
        expected = Path(sys.argv[sys.argv.index("--expected") + 1])
    print("source:", sh(["git", "rev-parse", "HEAD"]).stdout.strip())
    print("iverilog:", sh(["iverilog", "-V"]).stdout.splitlines()[0])
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        nc = negative_control(tmp)
        print(("PASS " if nc else "FAIL ") + "negative control (matching output then nonzero simulator exit is rejected)")
        if not nc:
            bad.append("negative_control")
        try:
            got = collect(tmp)
        except (RuntimeError, AssertionError) as exc:
            print("FAIL:", exc)
            return 1
        for name, lines in sorted(got.items()):
            want = (expected / name).read_text().splitlines()
            ok = lines == want and bool(lines)
            print(("PASS " if ok else "FAIL ") + f"{name} ({len(lines)} lines)")
            if not ok:
                bad.append(name)
                diff = [(i, w, g) for i, (w, g) in enumerate(zip(want, lines)) if w != g][:2]
                print("  first differences (index, expected, got):", diff, "lengths", len(want), len(lines))
        for mname, old, new in (("bound_9458", "($signed(v) <= 32'sd9457)", "($signed(v) <= 32'sd9458)"),
                                ("skip_D_Q", " && rplu2_in_domain(qrf_rd_D[63:32]);", ";")):
            det = mutant_detected(tmp, mname, old, new)
            print(("PASS " if det else "FAIL ") + f"sensitivity control: mutated guard '{mname}' is detected")
            if not det:
                bad.append("mutant_" + mname)
    print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
