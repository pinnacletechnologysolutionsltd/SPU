#!/usr/bin/env python3
"""Controls for test_runner_exit_verdict.py (REGRESS-EXIT-1 review fixes):
required real tools fail the test by default; unsuitable versions are
rejected; PATH installs are discovered; opted-in skips exit 3, show in the
outer runner summary and count as a failure; the PASS-then-nonzero defect is still detected (mutant
runner with both returncode checks disabled); the nested-run guard fires.
Not part of run_all_tests.py: ~1-2 min, starts nested runners.
"""
import importlib.util, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEST = os.path.join(HERE, "test_runner_exit_verdict.py")
spec = importlib.util.spec_from_file_location("erv", TEST)
erv = importlib.util.module_from_spec(spec); spec.loader.exec_module(erv)
passed = failed = 0

def ok(cond, msg):
    global passed, failed
    passed += bool(cond); failed += not cond
    print(("  PASS: " if cond else "  FAIL: ") + msg)

def fake(path, text, mode=0o755):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text); os.chmod(path, mode)

def sh(cmd, env, cwd=None):
    r = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr

tmp = tempfile.mkdtemp(prefix="exitverdict_ctl_")
try:
    home = f"{tmp}/home"; os.makedirs(home)
    bare = f"{tmp}/bare"; os.makedirs(bare)  # no simulators; chmod is all the shims need
    os.symlink(shutil.which("chmod"), f"{bare}/chmod")
    base = {"HOME": home, "PATH": bare, "LANG": "C"}

    print("1. missing required real tools fail by default")
    rc, out = sh([sys.executable, TEST], base)
    ok(rc != 0 and "REQUIRED real Icarus" in out and "REQUIRED real Verilator" in out, f"exit {rc}, both REQUIRED messages")
    ok("SKIPPED-REAL-TOOLS" not in out, "no skip marker without opt-in")

    print("2. unsuitable versions rejected / suitable accepted")
    v4, v5 = f"{tmp}/v4", f"{tmp}/v5"
    fake(f"{v4}/verilator", "#!/bin/bash\necho 'Verilator 4.038 2020-07-11 rev v4.036'\n")
    fake(f"{v5}/verilator", "#!/bin/bash\necho 'Verilator 5.020 2024-01-01'\n")
    fake(f"{tmp}/nx/verilator", "#!/bin/bash\necho 'Verilator 5.020'\n", 0o644)
    ok(erv.suitable_verilator([v4]) is None, "Verilator 4.038 rejected")
    ok(erv.suitable_verilator([f"{tmp}/nx"]) is None, "non-executable verilator rejected")
    ok(erv.suitable_verilator([v4, v5]) == v5, "first suitable (5.x) chosen after rejecting 4.x")
    i9, i14 = f"{tmp}/i9", f"{tmp}/i14"
    for d, v in ((i9, "9.0"), (i14, "14.0")):
        fake(f"{d}/iverilog", f"#!/bin/bash\necho 'Icarus Verilog version {v} (devel)'\n"); fake(f"{d}/vvp", "#!/bin/bash\nexit 0\n")
    ok(erv.suitable_icarus([i9]) is None, "Icarus 9.0 rejected")
    ok(erv.suitable_icarus([i9, i14]) == i14, "Icarus 14.0 accepted")
    fake(f"{tmp}/ni/iverilog", "#!/bin/bash\necho 'Icarus Verilog version 14.0'\n")
    ok(erv.suitable_icarus([f"{tmp}/ni"]) is None, "iverilog without vvp rejected")

    print("3. discovery order: $OSS_CAD_SUITE, installed suites, PATH")
    fake(f"{home}/.local/opt/oss-cad-suite-1/bin/verilator", "#!/bin/bash\necho 'Verilator 5.1'\n")
    e = {"HOME": home, "PATH": f"{v5}{os.pathsep}/nonexistent", "OSS_CAD_SUITE": f"{tmp}/s"}
    ok(erv.candidate_dirs(e) == [f"{tmp}/s/bin", f"{home}/.local/opt/oss-cad-suite-1/bin", v5, "/nonexistent"], "suite env, installed suite, then PATH")
    ok(erv.suitable_verilator(erv.candidate_dirs({"HOME": home + "/x", "PATH": v5})) == v5, "suitable PATH install discovered")

    print("4. opted-in skip exits nonzero, is visible, and counts as a failure in the outer runner")
    rc, out = sh([sys.executable, TEST], dict(base, SPU_ALLOW_SKIP_REAL_TOOLS="1"))
    ok(rc == 3 and "SKIPPED-REAL-TOOLS:" in out and "0 failed" in out, f"test exits {rc} (== 3, never 0) with the marker and no case failures")
    def outer_tree(name, test_src):
        d = f"{tmp}/{name}"; os.makedirs(f"{d}/software/tests")
        shutil.copy(f"{ROOT}/run_all_tests.py", d)
        open(f"{d}/software/tests/test_runner_exit_verdict.py", "w").write(test_src)
        return d
    def total_fail(o):
        m = re.search(r"Total FAIL:\s+(\d+)", o); return int(m.group(1)) if m else -1
    ev = dict(base, TB_FILTER="zz_no_such_bench")
    # reference: identical outer tree whose test just succeeds (a throwaway tree is nonzero anyway: other stages are missing)
    _, ref = sh([sys.executable, "run_all_tests.py"], ev, outer_tree("ref", "import sys; sys.exit(0)\n"))
    outer = outer_tree("outer", open(TEST).read())
    rc, out = sh([sys.executable, "run_all_tests.py"], dict(ev, SPU_ALLOW_SKIP_REAL_TOOLS="1"), outer)
    ok(rc != 0, f"outer runner exit {rc} is nonzero")
    ok("QUALIFICATION INCOMPLETE" in out and "INCOMPLETE:" in out and "SKIPPED-REAL-TOOLS:" in out, "outer summary shows INCOMPLETE and the skipped tools")
    ok(total_fail(ref) >= 0 and total_fail(out) == total_fail(ref) + 1, f"Total FAIL {total_fail(out)} == reference {total_fail(ref)} + 1")
    ok("Passed:                     0" in out.split("Runner Exit-Verdict Tests:")[1].split("\n\n")[0], "exit-verdict stage reports 0 passed")
    ok("QUALIFICATION INCOMPLETE" not in ref and "Runner Exit-Verdict Tests:  1" in ref, "reference (successful test) shows no INCOMPLETE")
    rc, out = sh([sys.executable, "run_all_tests.py"], ev, outer)
    ok("test_runner_exit_verdict.py FAILED" in out and "QUALIFICATION INCOMPLETE" not in out and total_fail(out) == total_fail(ref) + 1,
       "without opt-in the outer runner reports FAILED (still one extra failure)")

    print("5. PASS-then-nonzero defect still detected (mutant runner)")
    src = open(f"{ROOT}/run_all_tests.py").read()
    mut = src.replace("if run_result.returncode != 0:", "if False:").replace("if rr.returncode != 0:", "if False:")
    ok(mut.count("if False:") == 2, "mutant disables both returncode checks")
    open(f"{tmp}/mutant.py", "w").write(mut)
    rc, out = sh([sys.executable, TEST], dict(os.environ, RUNNER_UNDER_TEST=f"{tmp}/mutant.py", SPU_ALLOW_SKIP_REAL_TOOLS="1"))
    ok(rc != 0 and "FAIL: vvp PASS then rc1" in out and "FAIL: fallback PASS then rc1" in out, "test fails the mutant on both paths")

    print("6. nested-run guard")
    rc, out = sh([sys.executable, TEST], dict(os.environ, SPU_EXIT_VERDICT_NESTED="1"))
    ok(rc != 0 and "recursion guard" in out and "shimmed" not in out, "re-entry fails closed without running any case")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{passed} passed, {failed} failed")
print("FAIL" if failed else "PASS")
sys.exit(1 if failed else 0)
