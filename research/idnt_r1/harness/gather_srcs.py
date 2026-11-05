# Mirrors run_all_tests.py source gathering (release mode, no TB_FILTER).
import os, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(); tb = str((root / sys.argv[2]).resolve())
dirs = ["hardware/rtl","hardware/rtl/arch","hardware/rtl/common","hardware/rtl/common/prim","hardware/rtl/common/sync",
 "hardware/rtl/core","hardware/rtl/core/shared","hardware/rtl/core/spu13","hardware/rtl/core/spu4","hardware/rtl/gpu",
 "hardware/rtl/hal","hardware/rtl/math","hardware/rtl/accel","hardware/rtl/top","hardware/rtl/triage","hardware/rtl/peripherals",
 "hardware/rtl/peripherals/artery","hardware/rtl/peripherals/audio","hardware/rtl/peripherals/bio","hardware/rtl/peripherals/graphics",
 "hardware/rtl/peripherals/io","hardware/rtl/peripherals/memory","hardware/rtl/peripherals/storage","hardware/rtl/peripherals/video",
 "hardware/tests/common","hardware/boards/tang_primer_25k","hardware/boards/tang25k"]
gpu_ok = ['pade_eval_4_4.v','rplu_exp.v','rational_sine_provider.v','rational_sine_rom.v','rational_sine_rom_q32.v','spu_edge_stepper.v','spu_raster_unit.v','spu_bresenham_raster.v']
src = []
for d in dirs:
    p = root / d
    if not p.exists(): continue
    for f in sorted(p.rglob('*.v')):
        if f.name == 'spu_optional_stubs.v' or f.name.endswith('_fallback.v'): continue
        if 'hardware/tests' in d and (f.name.endswith('_tb.v') or f.name.startswith('tb_') or 'tb' in f.stem or f.name.startswith('testbench')): continue
        fp = str(f)
        if ('/hardware/rtl/gpu/' in fp or '/hardware/rtl/peripherals/graphics/' in fp) and f.name not in gpu_ok: continue
        src.append(fp)
seen, mm, out = set(), {}, []
for s in src:
    if s in seen: continue
    mods = re.findall(r'^\s*module\s+([a-zA-Z_][a-zA-Z0-9_]*)', open(s, errors='replace').read(), re.M)
    if any(m in mm for m in mods): continue
    out.append(s); seen.add(s); mm.update({m: s for m in mods})
print('\n'.join(x for x in out if x != tb))
