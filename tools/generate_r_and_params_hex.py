#!/usr/bin/env python3
"""Generate r_rom_<material>.mem and params_<material>.hex from material_morse_vectors.csv and params txt
Produces:
 - hardware/common/rtl/gpu/r_rom_<material>.mem (r in Q16.16 hex)
 - hardware/common/rtl/gpu/params_<material>.hex (three 32-bit hex words: a_q16,re_q16,De_q16)
"""
from decimal import Decimal, getcontext
import csv
import re

getcontext().prec = 80
SCALE = 1 << 16
IN='hardware/common/rtl/gpu/material_morse_vectors.csv'

# read rows grouped by material
materials = {}
with open(IN,'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['material'].strip()
        if name not in materials:
            materials[name] = []
        materials[name].append(row)

for name, rows in materials.items():
    # write r rom
    with open(f'hardware/common/rtl/gpu/r_rom_{name}.mem','w') as fr:
        for row in rows:
            r = Decimal(row['r'])
            rq = int((r * SCALE).to_integral_value())
            fr.write('{:08x}\n'.format(rq & 0xffffffff))
    # read params txt if exists
    try:
        with open(f'hardware/common/rtl/gpu/params_{name}.txt') as fp:
            txt = fp.read()
            a_match = re.search(r'a_q16=(\d+)', txt)
            re_match = re.search(r're_q16=(\d+)', txt)
            De_match = re.search(r'De_q16=(\d+)', txt)
            a_q = int(a_match.group(1)) if a_match else SCALE
            re_q = int(re_match.group(1)) if re_match else SCALE
            De_q = int(De_match.group(1)) if De_match else SCALE
    except FileNotFoundError:
        a_q = SCALE; re_q = SCALE; De_q = SCALE
    # write hex params (three 32-bit words)
    with open(f'hardware/common/rtl/gpu/params_{name}.hex','w') as fh:
        fh.write('{:08x}\n'.format(a_q & 0xffffffff))
        fh.write('{:08x}\n'.format(re_q & 0xffffffff))
        fh.write('{:08x}\n'.format(De_q & 0xffffffff))

print('Wrote r_rom and params hex for', list(materials.keys()))
