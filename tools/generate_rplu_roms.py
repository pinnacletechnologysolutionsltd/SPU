#!/usr/bin/env python3
"""Generate per-material ROM mem files for RPLU skeleton from material_morse_vectors.csv
Outputs:
 - hardware/common/rtl/gpu/rplu_rom_<material>.mem (64-bit hex: p32<<32 | (q32 & 0xffffffff))
 - hardware/common/rtl/gpu/rplu_dissoc_<material>.mem (1 hex per line: 0/1)
"""
import csv
from collections import defaultdict

IN='hardware/common/rtl/gpu/material_morse_vectors.csv'
OUT_ROM='hardware/common/rtl/gpu/rplu_rom_{}.mem'
OUT_DISS='hardware/common/rtl/gpu/rplu_dissoc_{}.mem'

materials=defaultdict(list)
with open(IN,'r') as f:
    reader=csv.DictReader(f)
    for row in reader:
        name=row['material'].strip()
        # p_int and q_int fields
        p_int=int(row['p_int'])
        q_int=int(row['q_int'])
        diss=int(row['dissoc'])
        # pack p and q into 64-bit unsigned hex
        p32 = p_int & 0xffffffff
        q32 = q_int & 0xffffffff
        packed = (p32 << 32) | q32
        materials[name].append((packed,diss))

# write roms
for name,entries in materials.items():
    with open(OUT_ROM.format(name),'w') as fr, open(OUT_DISS.format(name),'w') as fd:
        for packed,diss in entries:
            fr.write('{:016x}\n'.format(packed))
            fd.write('{:01x}\n'.format(diss))
print('Wrote ROMs for', list(materials.keys()))
