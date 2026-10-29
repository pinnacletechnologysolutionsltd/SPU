#!/usr/bin/env python3
"""REGRESS-EXIT-1: run_all_tests.py must not accept PASS text from a bench
whose simulator process exited nonzero (vvp path and Verilator-fallback path).

Runs the production runner in a throwaway tree holding one probe bench: PATH-
shimmed tools for the deterministic cases, plus REAL Icarus (>= 11) and REAL
Verilator (>= 5) cases. Missing/unsuitable real tools FAIL the test (exit 1);
SPU_ALLOW_SKIP_REAL_TOOLS=1 skips them but the test then still exits
EXIT_INCOMPLETE (3, never 0) and prints a "SKIPPED-REAL-TOOLS:" marker, which
the outer runner reports as INCOMPLETE and counts as a failure.
Tools are searched in $OSS_CAD_SUITE/bin, ~/.local/opt/oss-cad-suite-*/bin, PATH.
A passing probe asserts the verdict line and Verilog "Failed: 0" only: the
throwaway tree lacks the other stages' inputs, so overall exit is nonzero by
design. Failing probes must also make the runner exit nonzero.
RUNNER_UNDER_TEST=<path> points the test at another runner (negative control).
SPU_EXIT_VERDICT_NESTED guards against the nested runner re-entering this test.
"""
import glob, os, re, shutil, subprocess, sys, tempfile
RUNNER = os.environ.get("RUNNER_UNDER_TEST") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "run_all_tests.py")
PROBE = "zz_exit_probe_tb"
SHIMS = {
 "iverilog": '#!/bin/bash\n[ -n "$IVL_FAIL" ] && { echo shim-compile-error >&2; exit 1; }\nwhile [ $# -gt 0 ]; do [ "$1" = -o ] && : > "$2"; shift; done; exit 0\n',
 "vvp": '#!/bin/bash\necho "$PROBE_OUT"\n[ "$PROBE_RC" = sig ] && kill -SEGV $$\nexit ${PROBE_RC:-0}\n',
 "verilator": "#!/bin/bash\nexit 0\n",
 "make": '#!/bin/bash\n{ echo "#!/bin/bash"; echo "echo \\"$PROBE_OUT\\""; [ "$PROBE_RC" = sig ] && echo "kill -SEGV \\$\\$"; echo "exit ${PROBE_RC:-0}"; } > "$2/V'+PROBE+'"; chmod +x "$2/V'+PROBE+'"\n',
}
EXIT_INCOMPLETE = 3
passed = failed = 0
skipped = []

def ok(cond, msg):
    global passed, failed
    passed += bool(cond); failed += not cond
    print(("  PASS: " if cond else "  FAIL: ") + msg)

def candidate_dirs(env=None):
    env = os.environ if env is None else env
    home = env.get("HOME") or os.path.expanduser("~")
    suites = [env["OSS_CAD_SUITE"]] if env.get("OSS_CAD_SUITE") else []
    suites += sorted(glob.glob(os.path.join(home, ".local/opt/oss-cad-suite-*")), reverse=True)
    return [s + "/bin" for s in suites] + [p for p in env.get("PATH", "").split(os.pathsep) if p]

def tool_env(d):  # suites keep Verilator's data next to bin/
    r = os.path.join(os.path.dirname(d.rstrip("/")), "share", "verilator")
    return dict(os.environ, VERILATOR_ROOT=r) if os.path.isdir(r) else dict(os.environ)

def version(exe, args, pat, d):
    if not (os.path.isfile(exe) and os.access(exe, os.X_OK)): return None
    try:
        r = subprocess.run([exe] + args, capture_output=True, text=True, timeout=30, env=tool_env(d))
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(pat, r.stdout + r.stderr)
    return tuple(int(x) for x in m.groups()) if m else None

def suitable_icarus(dirs):  # iverilog + vvp, Icarus >= 11
    for d in dirs:
        v = version(f"{d}/iverilog", ["-V"], r"Icarus Verilog version (\d+)", d)
        if v and v[0] >= 11 and os.access(f"{d}/vvp", os.X_OK) and os.path.isfile(f"{d}/vvp"): return d
    return None

def suitable_verilator(dirs):  # Verilator >= 5 (runner passes --timing) and make
    if not shutil.which("make"): return None
    for d in dirs:
        v = version(f"{d}/verilator", ["--version"], r"Verilator (\d+)", d)
        if v and v[0] >= 5: return d
    return None

def tree(src, vfb):
    d = tempfile.mkdtemp(prefix="exitverdict_")
    shutil.copy(RUNNER, f"{d}/run_all_tests.py")
    os.makedirs(f"{d}/hardware/tests/common")
    open(f"{d}/hardware/tests/common/{PROBE}.v", "w").write(src)
    if vfb:  # any '/hardware/rtl/gpu/' source arms the Verilator fallback
        g = f"{d}/hardware/rtl/core/shared/hardware/rtl/gpu"
        os.makedirs(g); open(f"{g}/rplu_exp.v", "w").write("module zz_gpu_dummy; endmodule\n")
    return d

def run(d, path, extra=None):
    env = dict(os.environ, PATH=path, TB_FILTER=PROBE, SPU_EXIT_VERDICT_NESTED="1", **(extra or {}))
    r = subprocess.run([sys.executable, "run_all_tests.py"], cwd=d, env=env, capture_output=True, text=True, timeout=180)
    m = re.findall(r"\[%s\.v\] ([^\n]*)" % PROBE, r.stdout)  # fallback prints a notice first; last line is the verdict
    f = re.search(r"Verilog Tests:.*?Failed:\s+(\d+)", r.stdout, re.S)
    return r.returncode, (m[-1] if m else ""), (int(f.group(1)) if f else -1)

def verdict_check(name, verdict, want, code, nfail):
    ok(verdict.startswith(want), f"{name}: verdict {verdict!r} starts with {want!r}")
    if want == "PASSED":
        ok(nfail == 0, f"{name}: Verilog stage Failed: {nfail}")
    else:
        ok(code != 0 and nfail == 1, f"{name}: runner exit {code}, Verilog Failed: {nfail}")

def shimmed(name, out, rc, want, vfb=False):
    d = tree("module %s; endmodule\n" % PROBE, vfb)
    try:
        b = f"{d}/bin"; os.makedirs(b)
        for n, s in SHIMS.items():
            open(f"{b}/{n}", "w").write(s); os.chmod(f"{b}/{n}", 0o755)
        code, verdict, nfail = run(d, b + os.pathsep + os.environ["PATH"],
                                   {"PROBE_OUT": out, "PROBE_RC": str(rc), **({"IVL_FAIL": "1"} if vfb else {})})
        verdict_check(name, verdict, want, code, nfail)
    finally:
        shutil.rmtree(d, ignore_errors=True)

def real(name, bindir, vfb, want_prefix, body):
    d = tree("module %s; initial begin %s end endmodule\n" % (PROBE, body), vfb)
    try:
        b = f"{d}/bin"; os.makedirs(b)
        if vfb:  # force the fallback; Verilator and make are the real ones
            open(f"{b}/iverilog", "w").write(SHIMS["iverilog"]); os.chmod(f"{b}/iverilog", 0o755)
        extra = {"IVL_FAIL": "1"} if vfb else {}
        if "VERILATOR_ROOT" in tool_env(bindir): extra["VERILATOR_ROOT"] = tool_env(bindir)["VERILATOR_ROOT"]
        code, verdict, nfail = run(d, b + os.pathsep + bindir + os.pathsep + os.environ["PATH"], extra)
        verdict_check(name, verdict, want_prefix, code, nfail)
    finally:
        shutil.rmtree(d, ignore_errors=True)

def require(label, found, hint):
    if found: return True
    if os.environ.get("SPU_ALLOW_SKIP_REAL_TOOLS") == "1":
        skipped.append(label); print(f"  SKIP (opt-in): no suitable {label}"); return False
    ok(False, f"REQUIRED real {label} unavailable ({hint}); SPU_ALLOW_SKIP_REAL_TOOLS=1 permits an INCOMPLETE run")
    return False

def main():
    if os.environ.get("SPU_EXIT_VERDICT_NESTED"):
        print("FAIL: recursion guard: test re-entered from a nested runner"); return 1
    print("shimmed vvp path")
    shimmed("vvp PASS rc0", "PASS: ok", 0, "PASSED")
    shimmed("vvp PASS then rc1", "PASS: ok", 1, "FAILED (vvp exit 1)")
    shimmed("vvp PASS then SIGSEGV", "PASS: ok", "sig", "FAILED (vvp exit -11)")
    shimmed("vvp FAIL text rc0", "FAIL: bad", 0, "FAILED")
    shimmed("vvp no verdict", "hello", 0, "NO VERDICT")
    print("shimmed Verilator-fallback path")
    shimmed("fallback PASS rc0", "PASS: ok", 0, "PASSED", vfb=True)
    shimmed("fallback PASS then rc1", "PASS: ok", 1, "FAILED (Verilator exe exit 1)", vfb=True)
    shimmed("fallback PASS then SIGSEGV", "PASS: ok", "sig", "FAILED (Verilator exe exit -11)", vfb=True)
    shimmed("fallback FAIL text rc0", "FAIL: bad", 0, "FAILED", vfb=True)
    dirs = candidate_dirs()
    ic, v5 = suitable_icarus(dirs), suitable_verilator(dirs)
    print(f"real Icarus ({ic})")
    if require("Icarus >= 11 (iverilog+vvp)", ic, "set OSS_CAD_SUITE or install iverilog"):
        real("icarus PASS then $fatal", ic, False, "FAILED (vvp exit", '$display("PASS: ok"); $fatal(1, "boom");')
        real("icarus PASS $finish", ic, False, "PASSED", '$display("PASS: ok"); $finish;')
    print(f"real Verilator fallback ({v5})")
    if require("Verilator >= 5 and make", v5, "set OSS_CAD_SUITE or install verilator >= 5"):
        real("verilator PASS then $fatal", v5, True, "FAILED (Verilator exe exit", '$display("PASS: ok"); $fatal(1, "boom");')
        real("verilator PASS $finish", v5, True, "PASSED", '$display("PASS: ok"); $finish;')
    print(f"\n{passed} passed, {failed} failed, {len(skipped)} skipped")
    if skipped:
        print("SKIPPED-REAL-TOOLS: " + "; ".join(skipped))
    print("FAIL" if failed else ("INCOMPLETE (real-tool coverage skipped by explicit opt-in; exit 3)" if skipped else "PASS"))
    return 1 if failed else (EXIT_INCOMPLETE if skipped else 0)

if __name__ == "__main__":
    sys.exit(main())
