#!/usr/bin/env python3
"""A31-R3: core RPLU2 arithmetic refusal (Pade flags_v) propagation, core-level directed simulation.

  python3 -I hardware/tests/spu13/a31_r3/run_a31_r3.py [--expected DIR]

Not registered in run_all_tests.py. Builds and runs in a temporary directory, writes nothing to the repository, compares with expected/*.
No option regenerates expectations. A simulator must exit 0 as well as match (built-in negative control); two mutated cores (refused
completion published as a result; refusal pulse never produced) must be detected. Success telemetry is cross-checked against the
independent oracle software/lib/a31_field.py. The lockstep probe compares the current spu13_core with the previous one extracted
from git (BASE_COMMIT). Needs iverilog >= 12 and vvp.
"""
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "software" / "lib"))
sys.dont_write_bytecode = True
import a31_field  # noqa: E402

BASE_COMMIT = "71c8a5a46ce920f46b6e4185c21b84ba1c610fb5"
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
KEEP = re.compile(r"^(==|TXN|RST|DOM|TOTAL)")
LOCKS = [("h0_noRPLU2", 1, 1, 0, 0), ("h0_inDomain2A", 1, 1, 0, 1), ("rplu2_cfg_only", 1, 0, 0, 2),
         ("legacy_som", 0, 0, 1, 2), ("no_rplu_no_som", 0, 0, 0, 2)]
NEG_CONTROL = 'module nc; initial begin $display("DONE"); $fatal(1, "forced nonzero exit"); end endmodule\n'
WITNESS_DEN = (0x2CEE24B2, 0, 0, 1)


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


def oracle_check(lines):
    """Independent expectation: success limbs from a31_field; the witness denominator must be a flags_v refusal."""
    exp = {"S1": a31_field.pade_eval([(2, 0, 0, 0)], [(1, 0, 0, 0)], (1, 0, 0, 0)),
           "S2": a31_field.pade_eval([(3, 0, 0, 0)], [(2, 0, 0, 0)], (1, 0, 0, 0))}
    assert a31_field.pade_eval([(2, 0, 0, 0)], [WITNESS_DEN], (1, 0, 0, 0)) == (None, True), "oracle: witness is not a refusal"
    seen = 0
    for ln in lines:
        m = re.match(r"TXN (S\d)b?\b.* kind=0 .* A=([0-9a-f]+)$", ln)
        if m:
            (limbs, flag), got = exp[m.group(1)], int(m.group(2), 16)
            assert not flag and limbs == (got, 0, 0, 0), f"oracle disagrees for {m.group(1)}: {limbs} vs {got:#x}"
            seen += 1
    assert seen >= 4, "too few success transactions checked against the oracle"


def mutant_detected(tmp, name, old, new):
    text = (ROOT / CORE).read_text()
    assert text.count(old) == 1, f"mutation anchor not unique: {old}"
    mut = Path(tmp) / f"core_{name}.v"
    mut.write_text(text.replace(old, new))
    try:
        build_run(tmp, f"mut_{name}", [mut, HERE / "a31r3_core_probe.v"], "a31r3_core_probe", defs=["-DINV=0"])
    except RuntimeError as exc:
        return "simulator exited" in str(exc)
    return False


def collect(tmp):
    got = {}
    for inv, tag in ((0, "ref"), (1, "str")):
        out = build_run(tmp, f"probe_{tag}", [HERE / "a31r3_core_probe.v"], "a31r3_core_probe", defs=[f"-DINV={inv}"])
        got[f"probe_{tag}.txt"] = [ln.rstrip() for ln in out.splitlines() if KEEP.match(ln)]
    oracle_check(got["probe_ref.txt"])
    if got["probe_ref.txt"] != got["probe_str.txt"]:
        raise RuntimeError("reference and structured inverter variants produced different observable results")
    base = sh(["git", "show", f"{BASE_COMMIT}:{CORE}"])
    if base.returncode:
        raise RuntimeError("cannot extract baseline core from git: " + base.stderr[:200])
    bsrc = Path(tmp) / "core_base.v"
    bsrc.write_text(re.sub(r"\bspu13_core\b", "spu13_core_base", base.stdout))

    def lock(cfg):
        name, v2, pipe, som, mode = cfg
        o = build_run(tmp, f"lock_{name}", [bsrc, HERE / "a31r3_lock.v"], "a31r3_lock",
                      defs=[f"-DLK_V2={v2}", f"-DLK_PIPE={pipe}", f"-DLK_SOM={som}", f"-DLK_MODE={mode}"])
        return [f"{name}: {ln.rstrip()}" for ln in o.splitlines() if ln.startswith("LOCK ")]
    with ThreadPoolExecutor(max_workers=4) as ex:
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
        for mname, old, new in (("publish_refused", "assign rplu2_result_valid = rplu2_thimble_valid && !rplu2_thimble_refused;",
                                 "assign rplu2_result_valid = rplu2_thimble_valid;"),
                                ("no_refusal_pulse", "else        rplu2_arith_refused_r <= rplu2_thimble_valid && rplu2_thimble_refused;",
                                 "else        rplu2_arith_refused_r <= 1'b0;")):
            det = mutant_detected(tmp, mname, old, new)
            print(("PASS " if det else "FAIL ") + f"mutation control: '{mname}' is detected")
            if not det:
                bad.append("mutant_" + mname)
    print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
