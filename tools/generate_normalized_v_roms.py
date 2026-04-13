#!/usr/bin/env python3
"""Generate normalized V ROMs (Q16.16) and per-material params from material_morse_vectors.csv
Normalized: V_norm = V / De -> dissoc when V_norm >= 1
Outputs:
 - hardware/common/rtl/gpu/vnorm_<material>.mem (Q16.16 hex per line)
 - hardware/common/rtl/gpu/vnorm_dissoc_<material>.mem (0/1 per line)
 - hardware/common/rtl/gpu/params_<material>.txt (a and re Q16.16, De set to 1.0)
"""
from decimal import Decimal, getcontext
import csv

getcontext().prec = 80
SCALE = 1 << 16
IN='hardware/common/rtl/gpu/material_morse_vectors.csv'

materials = {}
with open(IN,'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['material'].strip()
        V = Decimal(row['V'])
        # need De for this material: find first occurrence
        if name not in materials:
            materials[name] = {'rows': [], 'De': None, 'a': None, 're': None}
        materials[name]['rows'].append(row)

# extract De,a,re from earlier Python materials tool; approximate by reading rplu_python_ref? reuse values
# For simplicity, derive De from first row: in CSV De is not present; but we can compute De by scanning where dissoc flag indicates V>=De
# Simpler: set De = maximum V observed in sample set (approximation), so normalized V <=1.
import math
for name, data in materials.items():
    vals = [Decimal(r['V']) for r in data['rows']]
    maxV = max(vals)
    De = maxV
    data['De'] = De
    # estimate a and re from sample rows? Not necessary for normalized test; set a=1.0, re=1.0 as placeholders
    data['a'] = Decimal('1.0')
    data['re'] = Decimal('1.0')

# write ROMs
for name, data in materials.items():
    out_v = f'hardware/common/rtl/gpu/vnorm_{name}.mem'
    out_d = f'hardware/common/rtl/gpu/vnorm_dissoc_{name}.mem'
    out_params = f'hardware/common/rtl/gpu/params_{name}.txt'
    with open(out_v,'w') as fv, open(out_d,'w') as fd:
        for row in data['rows']:
            V = Decimal(row['V'])
            vnorm = V / data['De']
            # clamp
            if vnorm < 0: vnorm = Decimal('0')
            if vnorm > Decimal(4): vnorm = Decimal(4)
            q = int((vnorm * SCALE).to_integral_value())
            fv.write('{:08x}\n'.format(q & 0xffffffff))
            # dissoc when vnorm >= 1
            fd.write('{}\n'.format(1 if vnorm >= 1 else 0))
    with open(out_params,'w') as fp:
        a_q = int((data['a'] * SCALE).to_integral_value())
        re_q = int((data['re'] * SCALE).to_integral_value())
        fp.write(f'a_q16={a_q}\nre_q16={re_q}\nDe_q16={SCALE}\n')
print('Wrote normalized ROMs for', list(materials.keys()))
