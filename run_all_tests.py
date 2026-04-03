import os
import subprocess
from pathlib import Path

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
    print(f"Found {len(test_files)} test files to execute.")

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
    print(f"Total Tests: {len(test_files)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Timeouts:    {timeouts}")
    print(f"Compile Err: {compile_errors}")
    print("=============================================")

if __name__ == "__main__":
    main()
