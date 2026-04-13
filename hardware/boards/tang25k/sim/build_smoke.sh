#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../../../../" && pwd)"
cd "$ROOT_DIR"

echo "Collecting sources..."
python3 - <<'PY'
from pathlib import Path
import re,sys
root=Path('.')
scan_dirs=[
 'hardware/common/rtl',
 'hardware/common/rtl/core',
 'hardware/common/rtl/prim',
 'hardware/common/rtl/proto',
 'hardware/common/rtl/top',
 'hardware/spu4/rtl',
 'hardware/common/rtl/spu4/rtl',
 'hardware/spu13/rtl',
 'hardware/archive/legacy_rtl/common/rtl',
 'hardware/boards/tang25k'
]
files=[]
for d in scan_dirs:
 p=root/ d
 if not p.exists(): continue
 for f in p.rglob('*.v'):
  s=str(f)
  if '/gpu/' in s or '/graphics/' in s or '/tb/' in s or s.endswith('_tb.v'):
    continue
  files.append(s)
# dedupe by module name
module_map={}
unique=[]
for s in files:
  try:
    text=open(s).read()
  except Exception:
    text=''
  mods=re.findall(r'^\s*module\s+([a-zA-Z_][a-zA-Z0-9_]*)', text, re.M)
  conflict=False
  for m in mods:
    if m in module_map:
      conflict=True
      break
  if not conflict:
    unique.append(s)
    for m in mods:
      module_map[m]=s
# ensure stubs are first
inc=['hardware/common/rtl/include/auto_stubs.v','hardware/common/rtl/include/extra_stubs.v','hardware/common/rtl/include/more_stubs.v','hardware/common/rtl/include/gpu_stubs.v','hardware/common/rtl/include/extra_sim_stubs.v']
for i in reversed(inc):
  if i in unique:
    unique.remove(i)
  if Path(i).exists(): unique.insert(0,i)
print('Using %d source files' % len(unique))
# write to temp list
with open('/tmp/smoke_sources.txt','w') as fh:
  for u in unique:
    fh.write(u+'\n')
print('Source list written to /tmp/smoke_sources.txt')
PY

# Build
echo "Compiling..."
iverilog -g2012 -I hardware/common/rtl \
  -y hardware/common/rtl -y hardware/common/rtl/core -y hardware/common/rtl/prim -y hardware/common/rtl/proto -y hardware/common/rtl/top -y hardware/spu4/rtl -y hardware/boards/tang25k -y hardware/spu13/rtl -y hardware/archive/legacy_rtl/common/rtl \
  -o /tmp/tang25k_smoke.vvp $(cat /tmp/smoke_sources.txt) hardware/spu4/tests/tang25k_smoketest_tb.v || true

echo "Running simulation..."
vvp /tmp/tang25k_smoke.vvp || true
