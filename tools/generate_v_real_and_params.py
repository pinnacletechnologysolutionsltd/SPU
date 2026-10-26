#!/usr/bin/env python3
"""Generate v_real_<material>.mem and params_<material>.hex using rplu_python_ref materials
Reads r_rom_<material>.mem (Q16.16), computes Morse V using rplu_python_ref materials (De,a,re),
writes v_real_<material>.mem (Q16.16) and v_real_dissoc_<material>.mem (0/1), and params_<material>.hex
with a_q16,re_q16,De_q16.
"""
from decimal import Decimal, getcontext
import importlib.util
import os

getcontext().prec = 80
SCALE = 1 << 16

# import rplu_python_ref as module
spec = importlib.util.spec_from_file_location("rplu_python_ref",
    os.path.join('tools','rplu_python_ref.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

materials = mod.materials

for name, m in materials.items():
    r_rom_path = f'hardware/common/rtl/gpu/r_rom_{name}.mem'
    if not os.path.exists(r_rom_path):
        print('Skipping', name, '- no r_rom file')
        continue
    # read r values
    r_vals = []
    with open(r_rom_path,'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            r_q = int(line,16)
            # convert signed
            if r_q & 0x80000000:
                r_q -= 1<<32
            r = Decimal(r_q) / Decimal(SCALE)
            r_vals.append(r)
    # compute V for each r
    De = m['De']
    a = m['a']
    re = m['re']
    out_v = f'hardware/common/rtl/gpu/vnorm_{name}.mem'
    out_d = f'hardware/common/rtl/gpu/vnorm_dissoc_{name}.mem'
    with open(out_v,'w') as fv, open(out_d,'w') as fd:
        for r in r_vals:
            # compute morse potential using same function from module
            V = mod.morse_potential(r, De, a, re)
            # normalized V = V / De
            vnorm = V / De if De != 0 else Decimal('0')
            # clamp and convert to Q16.16
            if vnorm < 0: vnorm = Decimal('0')
            if vnorm > Decimal(4): vnorm = Decimal(4)
            q = int((vnorm * Decimal(SCALE)).to_integral_value(rounding=getcontext().rounding))
            if q < -2**31: q = -2**31
            if q > 2**31-1: q = 2**31-1
            fv.write('{:08x}\n'.format(q & 0xffffffff))
            fd.write('{}\n'.format(1 if vnorm >= 1 else 0))
    # write params hex: a_q16, re_q16, De_q16(normalized=1.0)
    a_q = int((a * Decimal(SCALE)).to_integral_value())
    re_q = int((re * Decimal(SCALE)).to_integral_value())
    De_q = SCALE
    with open(f'hardware/common/rtl/gpu/params_{name}.hex','w') as fh:
        fh.write('{:08x}\n'.format(a_q & 0xffffffff))
        fh.write('{:08x}\n'.format(re_q & 0xffffffff))
        fh.write('{:08x}\n'.format(De_q & 0xffffffff))
    print('Wrote vnorm and params for', name)

print('Done')
