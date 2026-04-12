#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
os.chdir(root)

if len(sys.argv) < 2:
    print("Usage: run_suite.py <suite_name_or_path>")
    sys.exit(2)

suite = sys.argv[1]
# If suite looks like a path, use it; else look in hardware/common/tests/<suite>.txt
if suite.endswith('.txt') or os.path.sep in suite:
    suite_path = Path(suite)
else:
    suite_path = root / f"hardware/common/tests/{suite}.txt"

if not suite_path.exists():
    print(f"Suite file not found: {suite_path}")
    sys.exit(1)

with open(suite_path) as f:
    raw_lines = [l.rstrip('\n') for l in f if l.strip()]

suite_scan_dirs = None
suite_inc_dirs = None
tb_list = []
for line in raw_lines:
    s = line.strip()
    if s.startswith('SCAN_DIRS:'):
        suite_scan_dirs = [x.strip() for x in s.split(':',1)[1].split(',') if x.strip()]
    elif s.startswith('INC_DIRS:'):
        suite_inc_dirs = [x.strip() for x in s.split(':',1)[1].split(',') if x.strip()]
    elif s.startswith('#') or s.startswith('//'):
        continue
    else:
        tb_list.append(s)

print(f"Running suite {suite_path} with {len(tb_list)} tests")
# If SCAN_DIRS header present in suite file, it'll override the default scan_dirs below

inc_dirs = [
    "hardware/common/rtl",
    "hardware/common/rtl/core",
    "hardware/common/rtl/mem",
    "hardware/common/rtl/prim",
    "hardware/common/rtl/proto",
    "hardware/common/rtl/top",
    "hardware/common/rtl/bio",
    "hardware/common/rtl/gpu",
    "hardware/common/rtl/include",
    "hardware/common/rtl/io",
    "hardware/common/rtl/audio",
    "hardware/common/rtl/hal",
    "hardware/spu13/rtl",
    "hardware/spu4/rtl",
    "hardware/common/rtl/spu4/rtl",
    "hardware/boards/tang_primer_25k",
    "hardware/boards/tang_primer_20k",
]

# iverilog args will be constructed after possible per-suite inc_dirs override

# scan src dirs (curated)
scan_dirs = [
    "hardware/common/rtl/gpu",
    "hardware/common/rtl/core",
    "hardware/common/rtl/mem",
    "hardware/common/rtl/prim",
    "hardware/common/rtl/proto",
    "hardware/common/rtl/bio",
    "hardware/common/rtl/io",
    "hardware/common/rtl/include",
    "hardware/spu13/rtl",
    "hardware/spu4/rtl",
    "hardware/common/rtl/spu4/rtl",
    "hardware/boards/tang_primer_25k",
    "hardware/boards/tang_primer_20k",
]

# allow per-suite override of scan directories (keep default if not provided)
if suite_scan_dirs is not None:
    scan_dirs = suite_scan_dirs

# allow per-suite override of include directories (keep default if not provided)
if suite_inc_dirs is not None:
    inc_dirs = suite_inc_dirs

# construct iverilog arguments using the (possibly overridden) inc_dirs
iverilog_args = ["iverilog"]
for d in inc_dirs:
    iverilog_args.extend(["-y", d, "-I", d])
iverilog_args.extend(["-I", "hardware/common/rtl"]) 

src_files = []
for d in scan_dirs:
    ad = root / d
    # small helper: avoid crash if dir missing
    if ad.exists():
        for f in ad.rglob('*.v'):
            src_files.append(str(f))

# de-duplicate
seen = set(); src_unique = []
for s in src_files:
    if s not in seen:
        seen.add(s); src_unique.append(s)

passed = 0
failed = 0
compile_errors = 0

for tb in tb_list:
    tb_path = Path(tb)
    if not tb_path.is_absolute():
        tb_path = root / tb
    print(f"\n--- Running Test: {tb_path.name} ---")
    if not tb_path.exists():
        print(f"[{tb_path.name}] NOT FOUND")
        compile_errors += 1
        continue

    out_vvp = root / f"tmp_{tb_path.stem}.vvp"
    cmd = iverilog_args + ["-o", str(out_vvp)] + src_unique + [str(tb_path)]
    cr = subprocess.run(cmd, capture_output=True, text=True)
    if cr.returncode != 0:
        print(f"[{tb_path.name}] COMPILE ERROR:\n{cr.stderr.strip()}")
        compile_errors += 1
        if out_vvp.exists(): out_vvp.unlink()
        continue

    try:
        rr = subprocess.run(["vvp", str(out_vvp)], capture_output=True, text=True, timeout=8)
        output = rr.stdout + rr.stderr
        if "FAIL" in output or rr.returncode != 0:
            print(f"[{tb_path.name}] FAILED\n{output.strip()}")
            failed += 1
        else:
            print(f"[{tb_path.name}] PASSED")
            passed += 1
    except subprocess.TimeoutExpired:
        print(f"[{tb_path.name}] TIMEOUT")
        failed += 1

    if out_vvp.exists(): out_vvp.unlink()

print('\n================== SUMMARY ==================')
print(f"Tests run: {len(tb_list)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Compile errors: {compile_errors}")
print('=============================================')

sys.exit(0)
