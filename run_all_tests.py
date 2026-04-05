import os
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
        "hardware/common/rtl/io",
        "hardware/spu13/rtl",
        "hardware/spu4/rtl",
        "hardware/boards/icesugar",       # local board tops (must precede reference/)
        "hardware/boards/tang_nano_9k",
        "hardware/boards/tang_primer_25k",
        "hardware/vendor/gowin",          # Gowin DSP / BSRAM primitives
        "hardware/vendor/ice40",          # iCE40 simulation stubs
        "reference/synergeticrenderer/Laminar-Core/hardware/archive",
        "reference/synergeticrenderer/Laminar-Core/hardware/rtl",
        "reference/synergeticrenderer/Laminar-Core/hardware/tests",
    ]
    
    iverilog_args = ["iverilog"]
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
        cmd = iverilog_args + ["-o", str(out_vvp), str(tb)]
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

    total_pass = passed + cpp_p
    total_fail = failed + cpp_f + timeouts + compile_errors + cpp_e
    print(f"\nTotal PASS:  {total_pass}")
    print(f"Total FAIL:  {total_fail}")
    print("=============================================")

if __name__ == "__main__":
    main()
