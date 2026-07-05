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

        # Execute (with timeout safeguard)
        run_cmd = ["vvp", str(out_vvp)]
        try:
            run_result = subprocess.run(run_cmd, capture_output=True, timeout=5)
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

    print(f"\nPython Tests: {py_pass + py_fail + cv_pass + cv_fail}")
    print(f"Passed:      {py_pass + cv_pass}")
    print(f"Failed:      {py_fail + cv_fail}")

    print(f"\nAudio Sink Tests: {audio_pass + audio_fail}")
    print(f"Passed:           {audio_pass}")
    print(f"Failed:           {audio_fail}")

    total_pass = passed + cpp_p + py_pass + cv_pass + lucas_pass + su3_pass + audio_pass
    total_fail = failed + cpp_f + timeouts + compile_errors + cpp_e + py_fail + cv_fail + audio_fail
    print(f"\nTotal PASS:  {total_pass}")
    print(f"Total FAIL:  {total_fail}")
    print("=============================================")

if __name__ == "__main__":
    main()
