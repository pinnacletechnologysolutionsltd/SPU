import os
import sys
import subprocess
from pathlib import Path

SKIP_DISCOVERY_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    # Archived RTL and its historical regressions document superseded
    # implementations; they are not part of the active verification gate.
    "archive",
}


def is_under_skipped_dir(path, root_dir):
    """Return true for generated/cache/vendor trees that are not repo tests."""

    try:
        parts = path.relative_to(root_dir).parts
    except ValueError:
        parts = path.parts
    return any(part in SKIP_DISCOVERY_DIRS for part in parts)


def run_cpp_tests(root_dir):
    """Discover, compile and run *_test.cpp files. Returns (passed, failed, errors)."""
    cpp_tests = [
        p for p in root_dir.rglob("*_test.cpp")
        if not is_under_skipped_dir(p, root_dir)
    ]
    if not cpp_tests:
        return 0, 0, 0

    passed = failed = errors = 0
    cpp_inc = [
        "software/common/include",
    ]
    build_dir = root_dir / "build" / "cpp_tests"
    build_dir.mkdir(parents=True, exist_ok=True)

    for tf in cpp_tests:
        print(f"\n--- Running C++ Test: {tf.name} ---")
        binary = build_dir / tf.stem
        inc_flags = [f"-I{root_dir / d}" for d in cpp_inc]
        compile_cmd = ["g++", "-std=c++17"] + inc_flags + [str(tf), "-o", str(binary)]

        cr = subprocess.run(compile_cmd, capture_output=True, text=True)
        if cr.returncode != 0:
            print(f"[{tf.name}] COMPILE ERROR:\n{cr.stderr.strip()}")
            errors += 1
            continue

        try:
            rr = subprocess.run([str(binary)], capture_output=True, timeout=10)
            out = rr.stdout.decode('utf-8', errors='replace') + rr.stderr.decode('utf-8', errors='replace')
            has_fail_line = any(line.lstrip().startswith("FAIL") for line in out.splitlines())
            if has_fail_line or rr.returncode != 0:
                print(f"[{tf.name}] FAILED\n{out.strip()}")
                failed += 1
            else:
                print(f"[{tf.name}] PASSED")
                passed += 1
        except subprocess.TimeoutExpired:
            print(f"[{tf.name}] TIMEOUT")
            failed += 1
        finally:
            if binary.exists():
                binary.unlink()

    return passed, failed, errors


def main():
    root_dir = Path(__file__).resolve().parent
    os.chdir(root_dir)

    # Find all testbenches
    patterns = ['*_tb.v', '*tb*.v', 'testbench*.v']
    test_files = set()
    for p in patterns:
        for f in root_dir.rglob(p):
            if is_under_skipped_dir(f, root_dir):
                continue
            # Skip heavy legacy/reference tests during triage
            if '/reference/' in str(f):
                continue
            test_files.add(f)

    test_files = list(test_files)
    # Optional: limit to a single test file prefix for quicker triage
    tb_filter = os.getenv('TB_FILTER')
    if tb_filter:
        test_files = [f for f in test_files if tb_filter in f.name]
    print(f"Found {len(test_files)} Verilog test files to execute.")

    # Directories for auto-discovery (-y) and includes (-I)
    inc_dirs = [
        "hardware/rtl",
        "hardware/rtl/arch",
        "hardware/rtl/common",
        "hardware/rtl/common/prim",
        "hardware/rtl/common/sync",
        "hardware/rtl/core",
        "hardware/rtl/core/shared",
        "hardware/rtl/core/spu13",
        "hardware/rtl/core/spu4",
        "hardware/rtl/gpu",
        "hardware/rtl/hal",
        "hardware/rtl/math",
        "hardware/rtl/accel",
        "hardware/rtl/top",
        "hardware/rtl/triage",
        "hardware/rtl/peripherals",
        "hardware/rtl/peripherals/artery",
        "hardware/rtl/peripherals/audio",
        "hardware/rtl/peripherals/bio",
        "hardware/rtl/peripherals/graphics",
        "hardware/rtl/peripherals/io",
        "hardware/rtl/peripherals/memory",
        "hardware/rtl/peripherals/storage",
        "hardware/rtl/peripherals/video",
        "hardware/boards/tang_primer_25k",
        "hardware/boards/artix7",         # A7 probe tops (resolved on demand via -y)
        "hardware/vendor/gowin",          # Gowin DSP / BSRAM primitives
        "hardware/vendor/ice40",          # iCE40 simulation stubs
        "hardware/archive/legacy_rtl",
        "hardware/archive/legacy_rtl/common/rtl",
    ]

    iverilog_args = ["iverilog", "-g2012"]
    for d in inc_dirs:
        iverilog_args.extend(["-y", d, "-I", d])
    # Top-level include for spu_arch_defines.vh and sqr_params.vh
    iverilog_args.extend(["-I", "hardware/rtl/arch"])

    passed = 0
    failed = 0
    timeouts = 0
    compile_errors = 0

    for tb in test_files:
        print(f"\n--- Running Test: {tb.name} ---")
        out_vvp = root_dir / f"tmp_{tb.stem}.vvp"

        # Compile
        # Gather all source files from include directories so iverilog sees every module
        # Gather source files from a curated set of directories to avoid duplicates
        scan_dirs = [
            "hardware/rtl",
            "hardware/rtl/arch",
            "hardware/rtl/common",
            "hardware/rtl/common/prim",
            "hardware/rtl/common/sync",
            "hardware/rtl/core",
            "hardware/rtl/core/shared",
            "hardware/rtl/core/spu13",
            "hardware/rtl/core/spu4",
            "hardware/rtl/gpu",
            "hardware/rtl/hal",
            "hardware/rtl/math",
            "hardware/rtl/accel",
            "hardware/rtl/top",
            "hardware/rtl/triage",
            "hardware/rtl/peripherals",
            "hardware/rtl/peripherals/artery",
            "hardware/rtl/peripherals/audio",
            "hardware/rtl/peripherals/bio",
            "hardware/rtl/peripherals/graphics",
            "hardware/rtl/peripherals/io",
            "hardware/rtl/peripherals/memory",
            "hardware/rtl/peripherals/storage",
            "hardware/rtl/peripherals/video",
            "hardware/boards/tang_primer_25k",
            "hardware/boards/tang25k",
            "hardware/tests/common",  # behavioral test helpers (e.g., sim_sd_card)
        ]
        src_files = []
        module_map = {}
        for d in scan_dirs:
            absd = root_dir / d
            if absd.exists():
                for f in absd.rglob('*.v'):
                    # Skip testbench tops in the helper scan; only support
                    # RTL helpers such as sim_sd_card.v should be included.
                    if 'hardware/tests' in d:
                        name = f.name
                        if name.endswith("_tb.v") or name.startswith("tb_") or "tb" in f.stem or name.startswith("testbench"):
                            continue
                    # Skip GPU/graphics RTL (may contain unsupported SV constructs for iverilog)
                    fp = str(f)
                    # For GPU/graphics sources, only include a tested subset to avoid SV-only files breaking iverilog
                    if '/hardware/rtl/gpu/' in fp or '/hardware/rtl/peripherals/graphics/' in fp:
                        allowed_gpu = ['pade_eval_4_4.v', 'rplu_exp.v', 'rational_sine_provider.v', 'rational_sine_rom.v', 'rational_sine_rom_q32.v', 'spu_edge_stepper.v', 'spu_raster_unit.v', 'spu_bresenham_raster.v']
                        if os.path.basename(fp) not in allowed_gpu:
                            continue
                    src_files.append(str(f))
        # De-duplicate source files while avoiding multiple definitions of the same module
        src_unique = []
        seen_files = set()
        for s in src_files:
            if s in seen_files:
                continue
            # read module names in this file
            try:
                with open(s,'r') as fh:
                    text = fh.read()
            except Exception:
                text = ''
            import re
            modules_in_file = re.findall(r'^\s*module\s+([a-zA-Z_][a-zA-Z0-9_]*)', text, re.M)
            conflict = False
            for m in modules_in_file:
                if m in module_map:
                    conflict = True
                    break
            if not conflict:
                src_unique.append(s)
                seen_files.add(s)
                for m in modules_in_file:
                    module_map[m] = s
            else:
                # skip this file to avoid duplicate module definitions
                pass
        # Remove the testbench file from src list if it was discovered in scan_dirs
        tb_str = str(tb)
        src_unique = [s for s in src_unique if s != tb_str]
        # Also remove any source files that the testbench `include`s inline to avoid duplicate module declarations.
        try:
            with open(tb_str,'r') as _tf:
                tb_text = _tf.read()
            included_files = re.findall(r'^\s*`include\s+"([^"]+)"', tb_text, re.M)
            if included_files:
                src_unique = [s for s in src_unique if os.path.basename(s) not in included_files]
        except Exception:
            pass

        # If TB_FILTER is set, restrict the source set to minimal directories to avoid pulling board tops and unrelated cores
        tb_filter = os.getenv('TB_FILTER')
        if tb_filter:
            allowed_dirs = [str(root_dir / p) for p in ("hardware/rtl", "hardware/rtl/core/shared", "hardware/rtl/core/spu13", "hardware/tests/common", "hardware/rtl/arch")]
            excluded_dirs = [str(root_dir / p) for p in ("hardware/rtl/gpu", "hardware/rtl/peripherals/graphics")]
            src_unique = [
                s for s in src_unique
                if any(s.startswith(d) for d in allowed_dirs)
                and not any(s.startswith(d) for d in excluded_dirs)
            ]

        top_mod = None
        try:
            import re as _re
            with open(tb_str, 'r') as _tf:
                tb_text = _tf.read()
            m = _re.search(r'^\s*module\s+([A-Za-z_][A-Za-z0-9_]*)', tb_text, _re.M)
            if m:
                top_mod = m.group(1)
        except Exception:
            top_mod = None

        cmd = iverilog_args + (["-s", top_mod] if top_mod else []) + ["-o", str(out_vvp)] + src_unique + [str(tb)]
        compile_result = subprocess.run(cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            # If GPU sources are in the source set, attempt a Verilator simulation fallback
            gpu_present = any('/hardware/rtl/gpu/' in s for s in src_unique)
            if gpu_present:
                print(f"[{tb.name}] iverilog failed; attempting Verilator simulation fallback...")
                # Determine TB top module name
                try:
                    if not top_mod:
                        raise Exception('Top module not found')
                except Exception as e:
                    print(f"[{tb.name}] Verilator fallback: cannot determine top module: {e}")
                    print(f"[{tb.name}] COMPILE ERROR:")
                    print(compile_result.stderr.strip())
                    compile_errors += 1
                    if out_vvp.exists():
                        out_vvp.unlink()
                    continue

                build_dir = root_dir / "build" / "verilator" / tb.stem
                build_dir.mkdir(parents=True, exist_ok=True)
                sim_cpp = build_dir / "sim_main.cpp"
                sim_cpp.write_text(f'''#include "verilated.h"\n#include "V{top_mod}.h"\n#include <iostream>\nint main(int argc, char **argv) {{\n    VerilatedContext* contextp = new VerilatedContext;\n    contextp->commandArgs(argc, argv);\n    V{top_mod}* top = new V{top_mod}(contextp);\n    while (!contextp->gotFinish()) {{\n        top->eval();\n        contextp->timeInc(1);\n    }}\n    delete top;\n    delete contextp;\n    return 0;\n}}\n''')

                # When using TB_FILTER, restrict Verilator include paths to a minimal set to avoid pulling in board tops
                tb_filter = os.getenv('TB_FILTER')
                if tb_filter:
                    verilator_inc_dirs = ["hardware/rtl", "hardware/rtl/gpu", "hardware/rtl/core/shared", "hardware/rtl/core/spu13", "hardware/rtl/arch"]
                else:
                    verilator_inc_dirs = inc_dirs

                verilator_cmd = [
                    "verilator", "--cc",
                    "--Mdir", str(build_dir),
                    "--top-module", top_mod,
                    "--timing",
                    "-Wno-fatal",
                ]
                for d in verilator_inc_dirs:
                    verilator_cmd.append("-I" + d)
                verilator_cmd.extend(src_unique + [tb_str])
                verilator_cmd.extend(["--exe", str(sim_cpp)])

                vcr = subprocess.run(verilator_cmd, capture_output=True, text=True)
                if vcr.returncode != 0:
                    print(f"[{tb.name}] Verilator PREPROCESS ERROR:\n{vcr.stderr}\n{vcr.stdout}")
                    compile_errors += 1
                    if out_vvp.exists():
                        out_vvp.unlink()
                    continue

                make_cmd = ["make", "-C", str(build_dir), "-f", f"V{top_mod}.mk", f"V{top_mod}", "-j"]
                mcr = subprocess.run(make_cmd, capture_output=True, text=True)
                if mcr.returncode != 0:
                    print(f"[{tb.name}] Verilator make error:\n{mcr.stderr}\n{mcr.stdout}")
                    compile_errors += 1
                    if out_vvp.exists():
                        out_vvp.unlink()
                    continue

                exe = build_dir / f"V{top_mod}"
                try:
                    rr = subprocess.run([str(exe)], capture_output=True, timeout=5)
                    output = rr.stdout.decode('utf-8', errors='replace') + rr.stderr.decode('utf-8', errors='replace')
                    if "FAIL" in output or "FAIL:" in output:
                        print(f"[{tb.name}] FAILED")
                        print(output.strip())
                        failed += 1
                    elif "PASS" in output or "PASS:" in output:
                        print(f"[{tb.name}] PASSED")
                        passed += 1
                    else:
                        print(f"[{tb.name}] EXECUTED (No explicit PASS/FAIL)")
                        if rr.returncode == 0:
                            passed += 1
                        else:
                            failed += 1
                except subprocess.TimeoutExpired:
                    print(f"[{tb.name}] TIMEOUT (Verilator run)")
                    timeouts += 1
                    failed += 1

                if out_vvp.exists():
                    out_vvp.unlink()
                continue
            else:
                print(f"[{tb.name}] COMPILE ERROR:")
                print(compile_result.stderr.strip())
                compile_errors += 1
                if out_vvp.exists():
                    out_vvp.unlink()
                continue

        # Execute (with timeout safeguard). 15s, not 5: the safeguard is for
        # hung TBs (no $finish), but spu13_core_rotc_opcode_tb.v legitimately
        # takes ~5.0s wallclock — at timeout=5 it was a coin-flip against
        # machine load, the source of every phantom "2 FAIL" this week
        # (measured 2026-07-10: three trials, 5.03-5.04s, $finish reached).
        run_cmd = ["vvp", str(out_vvp)]
        try:
            run_result = subprocess.run(run_cmd, capture_output=True, timeout=15)
            try:
                output = run_result.stdout.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                output = run_result.stdout.decode('latin-1', errors='replace')
            if "FAIL" in output or "FAIL:" in output:
                print(f"[{tb.name}] FAILED")
                print(output.strip())
                failed += 1
            elif "PASS" in output or "PASS:" in output:
                print(f"[{tb.name}] PASSED")
                passed += 1
            else:
                print(f"[{tb.name}] EXECUTED (No explicit PASS/FAIL)")
                if run_result.returncode == 0:
                    passed += 1
                else:
                    failed += 1
        except subprocess.TimeoutExpired:
            print(f"[{tb.name}] TIMEOUT (Testbench hung, likely no $finish)")
            timeouts += 1
            # Fails in simulation logic
            failed += 1

        if out_vvp.exists():
            out_vvp.unlink()

    print("\n================== SUMMARY ==================")
    print(f"Verilog Tests: {len(test_files)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Timeouts:    {timeouts}")
    print(f"Compile Err: {compile_errors}")

    # C++ tests
    cpp_p, cpp_f, cpp_e = run_cpp_tests(root_dir)
    print(f"\nC++ Tests:   {cpp_p + cpp_f + cpp_e}")
    print(f"Passed:      {cpp_p}")
    print(f"Failed:      {cpp_f}")
    print(f"Compile Err: {cpp_e}")

    # Python VM test
    py_pass = py_fail = 0
    vm_test = os.path.join(root_dir, "software", "spu_vm_test.py")
    if os.path.exists(vm_test):
        result = subprocess.run(
            [sys.executable, vm_test],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            py_pass = 1
        else:
            py_fail = 1
            print(f"\n  spu_vm_test.py FAILED:\n{result.stdout[-500:]}")

    # Cross-validation: spu_vm.py vs C++ reference
    cv_pass = cv_fail = 0
    audio_pass = audio_fail = 0
    cv_script = os.path.join(root_dir, "software", "cross_validate.py")
    if os.path.exists(cv_script):
        result_cv = subprocess.run(
            [sys.executable, cv_script],
            capture_output=True, text=True, timeout=60,
            cwd=root_dir
        )
        if result_cv.returncode == 0:
            cv_pass = 1
        else:
            cv_fail = 1
            print(f"\n  cross_validate.py FAILED:\n{result_cv.stdout[-800:]}")

    # Lucas MAC oracle
    lucas_pass = 0
    lucas_test = os.path.join(root_dir, "software", "tests", "test_lucas_mac_oracle.py")
    if os.path.exists(lucas_test):
        result_lucas = subprocess.run(
            [sys.executable, lucas_test],
            capture_output=True, text=True, timeout=30
        )
        if "PASS" in result_lucas.stdout:
            lucas_pass = 1
        else:
            print(f"\n  test_lucas_mac_oracle.py FAILED:\n{result_lucas.stdout[-500:]}")

    # Lucas MAC state-machine harness
    lucas_harness_pass = 0
    lucas_harness_test = os.path.join(root_dir, "software", "tests", "test_lucas_mac_harness.py")
    if os.path.exists(lucas_harness_test):
        result_lh = subprocess.run(
            [sys.executable, lucas_harness_test],
            capture_output=True, text=True, timeout=30
        )
        if "0 failed" in result_lh.stdout:
            lucas_harness_pass = 1
        else:
            print(f"\n  test_lucas_mac_harness.py FAILED:\n{result_lh.stdout[-500:]}")

    # Icosahedral catalog derivation oracle
    icosa_pass = 0
    icosa_test = os.path.join(root_dir, "software", "tests", "test_icosahedral_catalog.py")
    if os.path.exists(icosa_test):
        result_ic = subprocess.run(
            [sys.executable, icosa_test],
            capture_output=True, text=True, timeout=60
        )
        if "ICOSAHEDRAL CATALOG DERIVATION: ALL PASS" in result_ic.stdout:
            icosa_pass = 1
        else:
            print(f"\n  test_icosahedral_catalog.py FAILED:\n{result_ic.stdout[-500:]}")

    # SU(3) oracle
    su3_pass = 0
    su3_test = os.path.join(root_dir, "software", "tests", "test_su3_oracle.py")
    if os.path.exists(su3_test):
        result_su3 = subprocess.run(
            [sys.executable, su3_test],
            capture_output=True, text=True, timeout=30
        )
        if "PASS" in result_su3.stdout:
            su3_pass = 1
        else:
            print(f"\n  test_su3_oracle.py FAILED:\n{result_su3.stdout[-500:]}")

    # Padé batch inversion oracle
    pade_batch_pass = 0
    pade_batch_test = os.path.join(root_dir, "software", "tests", "test_pade_batch_inversion.py")
    if os.path.exists(pade_batch_test):
        result_pade = subprocess.run(
            [sys.executable, pade_batch_test],
            capture_output=True, text=True, timeout=30
        )
        if "ALL CHECKS PASS" in result_pade.stdout:
            pade_batch_pass = 1
        else:
            print(f"\n  test_pade_batch_inversion.py FAILED:\n{result_pade.stdout[-500:]}")

    # Hyper-Catalan series oracle
    hc_pass = 0
    hc_test = os.path.join(root_dir, "software", "tests", "test_hyper_catalan_oracle.py")
    if os.path.exists(hc_test):
        result_hc = subprocess.run(
            [sys.executable, hc_test],
            capture_output=True, text=True, timeout=60
        )
        if "ALL CHECKS PASS" in result_hc.stdout:
            hc_pass = 1
        else:
            print(f"\n  test_hyper_catalan_oracle.py FAILED:\n{result_hc.stdout[-500:]}")

    # Digon-recursive cost model + series vs Newton validation
    digon_pass = 0
    digon_test = os.path.join(root_dir, "software", "lib", "digon_recursive.py")
    if os.path.exists(digon_test):
        result_digon = subprocess.run(
            [sys.executable, digon_test],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONPATH": os.path.join(root_dir, "software")}
        )
        # Both depths (eps^3 and eps^5) must PASS — a bare substring check
        # would accept eps^3 PASS while eps^5 FAILs below it.
        if (result_digon.stdout.count("series=Newton PASS") == 2
                and "FAIL" not in result_digon.stdout):
            digon_pass = 1
        else:
            print(f"\n  digon_recursive.py FAILED:\n{result_digon.stdout[-500:]}")
    else:
        digon_pass = 0

    # Audio sink tests
    audio_test = os.path.join(root_dir, "software", "tests", "test_rplu2_audio.py")
    if os.path.exists(audio_test):
        result_audio = subprocess.run(
            [sys.executable, audio_test],
            capture_output=True, text=True, timeout=30
        )
        if result_audio.returncode == 0:
            audio_pass = 1
        else:
            audio_pass = 0
            audio_fail = 1
            print(f"\n  test_rplu2_audio.py FAILED:\n{result_audio.stdout[-500:]}")
    else:
        audio_pass = audio_fail = 0

    # ROTC thirds-angle exactness research (dead-end audit trail + verified
    # exponent-tagged fix) — no hardware required
    rotc_fix_test = os.path.join(root_dir, "software", "tests", "test_rotc_thirds_native.py")
    if os.path.exists(rotc_fix_test):
        result_rotc_fix = subprocess.run(
            [sys.executable, rotc_fix_test],
            capture_output=True, text=True, timeout=60
        )
        if result_rotc_fix.returncode == 0:
            rotc_fix_pass, rotc_fix_fail = 1, 0
        else:
            rotc_fix_pass, rotc_fix_fail = 0, 1
            print(f"\n  test_rotc_thirds_native.py FAILED:\n{result_rotc_fix.stdout[-500:]}")
    else:
        rotc_fix_pass = rotc_fix_fail = 0

    # Cartesian bridge sensor/legacy boundary oracle (no hardware required)
    bridge_test = os.path.join(root_dir, "software", "tests", "test_cartesian_bridge.py")
    if os.path.exists(bridge_test):
        result_bridge = subprocess.run(
            [sys.executable, bridge_test],
            capture_output=True, text=True, timeout=30
        )
        if result_bridge.returncode == 0:
            bridge_pass, bridge_fail = 1, 0
        else:
            bridge_pass, bridge_fail = 0, 1
            print(f"\n  test_cartesian_bridge.py FAILED:\n{result_bridge.stdout[-500:]}")
    else:
        bridge_pass = bridge_fail = 0

    # ROTC bad-angle fault (VM side of the "don't corrupt the manifold" fix,
    # 2026-07-09) — no hardware required
    rotc_bad_angle_test = os.path.join(root_dir, "software", "tests", "test_rotc_bad_angle.py")
    if os.path.exists(rotc_bad_angle_test):
        result_rotc_bad_angle = subprocess.run(
            [sys.executable, rotc_bad_angle_test],
            capture_output=True, text=True, timeout=30
        )
        if result_rotc_bad_angle.returncode == 0:
            rotc_bad_angle_pass, rotc_bad_angle_fail = 1, 0
        else:
            rotc_bad_angle_pass, rotc_bad_angle_fail = 0, 1
            print(f"\n  test_rotc_bad_angle.py FAILED:\n{result_rotc_bad_angle.stdout[-500:]}")
    else:
        rotc_bad_angle_pass = rotc_bad_angle_fail = 0

    # ROTC VM-vs-RTL trace equivalence, all 12 angles (0-11) against both
    # rotor datapaths — needs iverilog/vvp, same as the Verilog TBs above.
    # This is the load-bearing cross-verification proof behind
    # ROTC_MAX_VERIFIED_ANGLE=23; a regression here means VM and RTL have
    # diverged, which the angle gate exists to prevent.
    rotc_trace_test = os.path.join(root_dir, "software", "tests", "test_rotc_vm_rtl_trace.py")
    if os.path.exists(rotc_trace_test):
        result_rotc_trace = subprocess.run(
            [sys.executable, rotc_trace_test],
            capture_output=True, text=True, timeout=120
        )
        if result_rotc_trace.returncode == 0:
            rotc_trace_pass, rotc_trace_fail = 1, 0
        else:
            rotc_trace_pass, rotc_trace_fail = 0, 1
            print(f"\n  test_rotc_vm_rtl_trace.py FAILED:\n{result_rotc_trace.stdout[-500:]}")
    else:
        rotc_trace_pass = rotc_trace_fail = 0

    # IROTC VM suite (trace equivalence / poison proofs / chain tests) —
    # φ-plane icosahedral opcodes, no hardware required. The trace and
    # chain tests import test_icosahedral_catalog.py, so the derivation's
    # self-checks re-run inside them (a broken derivation fails here too).
    irotc_results = {}
    for irotc_name in ("test_irotc_vm_trace.py", "test_irotc_poison.py",
                       "test_irotc_chains.py"):
        irotc_path = os.path.join(root_dir, "software", "tests", irotc_name)
        if not os.path.exists(irotc_path):
            irotc_results[irotc_name] = (0, 0)
            continue
        result_irotc = subprocess.run(
            [sys.executable, irotc_path],
            capture_output=True, text=True, timeout=120
        )
        if result_irotc.returncode == 0:
            irotc_results[irotc_name] = (1, 0)
        else:
            irotc_results[irotc_name] = (0, 1)
            print(f"\n  {irotc_name} FAILED:\n{result_irotc.stdout[-500:]}")
    irotc_pass = sum(p for p, _ in irotc_results.values())
    irotc_fail = sum(f for _, f in irotc_results.values())

    # Tensegrity balancer exact oracle/state-machine tests.
    tensegrity_results = {}
    for tensegrity_name in ("test_tensegrity_balancer.py",):
        tensegrity_path = os.path.join(root_dir, "software", "tests", tensegrity_name)
        if not os.path.exists(tensegrity_path):
            tensegrity_results[tensegrity_name] = (0, 0)
            continue
        result_tensegrity = subprocess.run(
            [sys.executable, tensegrity_path],
            capture_output=True, text=True, timeout=120
        )
        if result_tensegrity.returncode == 0:
            tensegrity_results[tensegrity_name] = (1, 0)
        else:
            tensegrity_results[tensegrity_name] = (0, 1)
            print(f"\n  {tensegrity_name} FAILED:\n{result_tensegrity.stdout[-500:]}")
    tensegrity_pass = sum(p for p, _ in tensegrity_results.values())
    tensegrity_fail = sum(f for _, f in tensegrity_results.values())

    # Canonical boot-sequence FSM oracle/state-machine tests.
    boot_sequence_results = {}
    for boot_sequence_name in ("test_boot_sequence.py",):
        boot_sequence_path = os.path.join(root_dir, "software", "tests", boot_sequence_name)
        if not os.path.exists(boot_sequence_path):
            boot_sequence_results[boot_sequence_name] = (0, 0)
            continue
        result_boot_sequence = subprocess.run(
            [sys.executable, boot_sequence_path],
            capture_output=True, text=True, timeout=120
        )
        if result_boot_sequence.returncode == 0:
            boot_sequence_results[boot_sequence_name] = (1, 0)
        else:
            boot_sequence_results[boot_sequence_name] = (0, 1)
            print(f"\n  {boot_sequence_name} FAILED:\n{result_boot_sequence.stdout[-500:]}")
    boot_sequence_pass = sum(p for p, _ in boot_sequence_results.values())
    boot_sequence_fail = sum(f for _, f in boot_sequence_results.values())

    # spu_host console parser (no hardware required)
    host_test = os.path.join(root_dir, "software", "tests", "test_spu_host_parser.py")
    if os.path.exists(host_test):
        result_host = subprocess.run(
            [sys.executable, host_test],
            capture_output=True, text=True, timeout=30
        )
        if result_host.returncode == 0:
            host_pass, host_fail = 1, 0
        else:
            host_pass, host_fail = 0, 1
            print(f"\n  test_spu_host_parser.py FAILED:\n{result_host.stdout[-500:]}")
    else:
        host_pass = host_fail = 0

    # SOM product artifact/trainer/data gates (no hardware required). These pin
    # Iris, the generalized CSV path, and the deterministic Paderborn importer.
    som_product_results = {}
    for som_product_name in (
        "test_iris_som_demo.py",
        "test_som_csv_trainer.py",
        "test_som_sensor_replay.py",
        "test_matlab_v5.py",
        "test_paderborn_bearing.py",
    ):
        som_product_path = os.path.join(
            root_dir, "software", "tests", som_product_name
        )
        if not os.path.exists(som_product_path):
            som_product_results[som_product_name] = (0, 0)
            continue
        result_som_product = subprocess.run(
            [sys.executable, som_product_path],
            capture_output=True, text=True, timeout=60
        )
        if result_som_product.returncode == 0:
            som_product_results[som_product_name] = (1, 0)
        else:
            som_product_results[som_product_name] = (0, 1)
            print(
                f"\n  {som_product_name} FAILED:\n"
                f"{result_som_product.stdout[-500:]}"
                f"{result_som_product.stderr[-500:]}"
            )
    som_product_pass = sum(p for p, _ in som_product_results.values())
    som_product_fail = sum(f for _, f in som_product_results.values())

    # Per-spin demo scripts (tools/*_demo.py, no hardware required).
    # Explicit list rather than a glob so in-flight/unregistered demo tests
    # don't silently join the gate before their author intends them to.
    spin_demo_tests = ["test_robotics_demo.py", "test_lucas_demo.py",
                       "test_tensegrity_demo.py"]
    robotics_demo_pass = robotics_demo_fail = 0
    for demo_name in spin_demo_tests:
        demo_path = os.path.join(root_dir, "software", "tests", demo_name)
        if not os.path.exists(demo_path):
            continue
        result_demo = subprocess.run(
            [sys.executable, demo_path],
            capture_output=True, text=True, timeout=60
        )
        if result_demo.returncode == 0:
            robotics_demo_pass += 1
        else:
            robotics_demo_fail += 1
            print(f"\n  {demo_name} FAILED:\n{result_demo.stdout[-500:]}")

    print(f"\nPython Tests: {py_pass + py_fail + cv_pass + cv_fail}")
    print(f"Passed:      {py_pass + cv_pass}")
    print(f"Failed:      {py_fail + cv_fail}")

    print(f"\nAudio Sink Tests: {audio_pass + audio_fail}")
    print(f"Passed:           {audio_pass}")
    print(f"Failed:           {audio_fail}")

    print(f"\nHost Library Tests: {host_pass + host_fail}")
    print(f"Passed:             {host_pass}")
    print(f"Failed:             {host_fail}")

    print(f"\nSOM Product Tests: {som_product_pass + som_product_fail}")
    print(f"Passed:           {som_product_pass}")
    print(f"Failed:           {som_product_fail}")

    print(f"\nSpin Demo Tests: {robotics_demo_pass + robotics_demo_fail}")
    print(f"Passed:          {robotics_demo_pass}")
    print(f"Failed:          {robotics_demo_fail}")

    print(f"\nCartesian Bridge Tests: {bridge_pass + bridge_fail}")
    print(f"Passed:                 {bridge_pass}")
    print(f"Failed:                 {bridge_fail}")

    print(f"\nROTC Thirds Fix Tests: {rotc_fix_pass + rotc_fix_fail}")
    print(f"Passed:                {rotc_fix_pass}")
    print(f"Failed:                {rotc_fix_fail}")

    print(f"\nROTC Bad-Angle Fault Tests: {rotc_bad_angle_pass + rotc_bad_angle_fail}")
    print(f"Passed:                     {rotc_bad_angle_pass}")
    print(f"Failed:                     {rotc_bad_angle_fail}")

    print(f"\nROTC Trace Equivalence Tests: {rotc_trace_pass + rotc_trace_fail}")
    print(f"Passed:                       {rotc_trace_pass}")
    print(f"Failed:                       {rotc_trace_fail}")

    print(f"\nIcosahedral Catalog Tests: {1}")
    print(f"Passed:                    {icosa_pass}")
    print(f"Failed:                    {1 - icosa_pass}")

    print(f"\nIROTC VM Tests: {irotc_pass + irotc_fail}")
    print(f"Passed:         {irotc_pass}")
    print(f"Failed:         {irotc_fail}")

    print(f"\nTensegrity Balancer Tests: {tensegrity_pass + tensegrity_fail}")
    print(f"Passed:                    {tensegrity_pass}")
    print(f"Failed:                    {tensegrity_fail}")

    print(f"\nBoot Sequence FSM Tests: {boot_sequence_pass + boot_sequence_fail}")
    print(f"Passed:                 {boot_sequence_pass}")
    print(f"Failed:                 {boot_sequence_fail}")

    total_pass = (
        passed + cpp_p + py_pass + cv_pass + lucas_pass + lucas_harness_pass
        + icosa_pass + su3_pass + pade_batch_pass + hc_pass + digon_pass
        + audio_pass + host_pass + som_product_pass + robotics_demo_pass
        + bridge_pass + rotc_fix_pass + rotc_bad_angle_pass + rotc_trace_pass
        + irotc_pass + tensegrity_pass + boot_sequence_pass
    )
    total_fail = (
        failed + cpp_f + timeouts + compile_errors + cpp_e + py_fail + cv_fail
        + audio_fail + host_fail + som_product_fail + robotics_demo_fail
        + bridge_fail + rotc_fix_fail + rotc_bad_angle_fail + rotc_trace_fail
        + irotc_fail + tensegrity_fail + boot_sequence_fail
        + (0 if lucas_harness_pass else 1) + (1 - icosa_pass) + (1 - su3_pass)
    )
    print(f"\nTotal PASS:  {total_pass}")
    print(f"Total FAIL:  {total_fail}")
    print("=============================================")

if __name__ == "__main__":
    main()
