import os
import sys
import subprocess
from pathlib import Path

def run_cpp_tests(root_dir):
    """Discover, compile and run *_test.cpp files. Returns (passed, failed, errors)."""
    cpp_tests = list(root_dir.rglob("*_test.cpp"))
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
            rr = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
            out = rr.stdout + rr.stderr
            if "FAIL" in out or rr.returncode != 0:
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
    root_dir = Path("/home/john/projects/hardware/SPU")
    os.chdir(root_dir)

    # Find all testbenches
    patterns = ['*_tb.v', '*tb*.v', 'testbench*.v']
    test_files = set()
    for p in patterns:
        for f in root_dir.rglob(p):
            test_files.add(f)
            
    test_files = list(test_files)
    print(f"Found {len(test_files)} Verilog test files to execute.")

    # Directories for auto-discovery (-y) and includes (-I)
    inc_dirs = [
        "hardware/common/rtl",
        "hardware/common/rtl/core",
        "hardware/common/rtl/mem",
        "hardware/common/rtl/prim",
        "hardware/common/rtl/proto",
        "hardware/common/rtl/top",
        "hardware/common/rtl/bio",
        "hardware/common/rtl/graphics",
        "hardware/common/rtl/include",
        "hardware/common/rtl/io",
        "hardware/common/rtl/audio",
        "hardware/common/rtl/hal",
        "hardware/spu13/rtl",
        "hardware/spu4/rtl",
        "hardware/common/rtl/spu4/rtl",
        "hardware/boards/icesugar",       # local board tops (must precede reference/)
        "hardware/boards/tang_nano_9k",
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
    iverilog_args.extend(["-I", "hardware/common/rtl"])

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
            "hardware/common/rtl",
            "hardware/common/rtl/core",
            "hardware/common/rtl/mem",
            "hardware/common/rtl/prim",
            "hardware/common/rtl/proto",
            "hardware/common/rtl/include",
            "hardware/spu13/rtl",
            "hardware/spu4/rtl",
            "hardware/common/rtl/spu4/rtl",
            "hardware/boards/tang_primer_25k",
            "hardware/boards/tang25k",
            "hardware/common/tests",  # include behavioral test helpers (e.g., sim_sd_card)
        ]
        src_files = []
        module_map = {}
        for d in scan_dirs:
            absd = root_dir / d
            if absd.exists():
                for f in absd.rglob('*.v'):
                    # Skip helper testbench files in the common tests directory
                    if d == "hardware/common/tests" and f.name.endswith("_tb.v"):
                        continue
                    # Skip GPU/graphics RTL (may contain unsupported SV constructs for iverilog)
                    fp = str(f)
                    if '/hardware/common/rtl/gpu/' in fp or '/hardware/common/rtl/graphics/' in fp:
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
        cmd = iverilog_args + ["-o", str(out_vvp)] + src_unique + [str(tb)]
        compile_result = subprocess.run(cmd, capture_output=True, text=True)
        
        if compile_result.returncode != 0:
            print(f"[{tb.name}] COMPILE ERROR:")
            print(compile_result.stderr.strip())
            compile_errors += 1
            if out_vvp.exists():
                out_vvp.unlink()
            continue
            
        # Execute (with timeout safeguard)
        run_cmd = ["vvp", str(out_vvp)]
        try:
            run_result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=5)
            output = run_result.stdout
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

    print(f"\nPython Tests: {py_pass + py_fail + cv_pass + cv_fail}")
    print(f"Passed:      {py_pass + cv_pass}")
    print(f"Failed:      {py_fail + cv_fail}")

    total_pass = passed + cpp_p + py_pass + cv_pass
    total_fail = failed + cpp_f + timeouts + compile_errors + cpp_e + py_fail + cv_fail
    print(f"\nTotal PASS:  {total_pass}")
    print(f"Total FAIL:  {total_fail}")
    print("=============================================")

if __name__ == "__main__":
    main()
