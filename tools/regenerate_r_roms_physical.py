#!/usr/bin/env python3
"""Regenerate r_rom_<material>.mem using physical units (Angstroms) from rplu_python_ref materials.
Produces 1024 Q16.16 samples spanning [re*0.5, re*1.5]
"""
import importlib.util, os
from decimal import Decimal, getcontext
getcontext().prec = 80
SCALE = 1 << 16

spec = importlib.util.spec_from_file_location("rplu_python_ref", os.path.join('tools','rplu_python_ref.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

materials = mod.materials
N = 1024
for name, m in materials.items():
    re = m['re']
    rmin = re * Decimal('0.5')
    rmax = re * Decimal('1.5')
    path = f'hardware/common/rtl/gpu/r_rom_{name}.mem'
    with open(path,'w') as f:
        for i in range(N):
            r = rmin + (rmax - rmin) * Decimal(i) / Decimal(N-1)
            q = int((r * Decimal(SCALE)).to_integral_value())
            f.write('{:08x}\n'.format(q & 0xffffffff))
    print('Wrote', path, 'range', float(rmin), float(rmax))
print('Done')
