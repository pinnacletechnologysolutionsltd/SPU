#!/usr/bin/env python3
"""Generate CSV test vectors for Morse potential per-material.
Outputs: hardware/common/rtl/gpu/material_morse_vectors.csv
Columns: material,r,V_scientific,p_int,q_int,recon_scientific,dissoc
"""
from decimal import Decimal, getcontext
import math

getcontext().prec = 80
SQRT3 = Decimal(3).sqrt()
SCALE32 = Decimal(2147483647)
AVOGADRO = Decimal('6.02214076e23')

# Materials: empirical De_kJ/mol converted to J/bond
materials = {
    'carbon': {'De_kJ_per_mol': Decimal('348'), 'a': Decimal('1.5'), 're': Decimal('1.54')},
    'iron':   {'De_kJ_per_mol': Decimal('413'), 'a': Decimal('1.2'), 're': Decimal('2.48')}
}
for m in materials.values():
    De_j_per_mol = m['De_kJ_per_mol'] * Decimal('1000')
    m['De'] = De_j_per_mol / AVOGADRO


def to_surd_pq(value, scale=SCALE32):
    v = Decimal(value)
    qf = v / SQRT3
    # rounding
    q_int = int((qf * scale).to_integral_value(rounding='ROUND_HALF_EVEN'))
    q = Decimal(q_int) / scale
    p = v - q * SQRT3
    p_int = int((p * scale).to_integral_value(rounding='ROUND_HALF_EVEN'))
    # clamp
    def clamp32(x):
        if x < -2**31: return -2**31
        if x > 2**31-1: return 2**31-1
        return x
    p_int = clamp32(p_int)
    q_int = clamp32(q_int)
    return p_int, q_int


def pq_to_real(p_int, q_int, scale=SCALE32):
    return Decimal(p_int) / scale + (Decimal(q_int) / scale) * SQRT3


def morse_potential(r, De, a, re):
    x = -(a * (r - re))
    ex = Decimal(str(math.exp(float(x))))
    val = De * (Decimal(1) - ex)**2
    return val

OUT = 'hardware/common/rtl/gpu/material_morse_vectors.csv'
with open(OUT, 'w') as f:
    f.write('material,r,V,p_int,q_int,recon,dissoc\n')
    points_per_material = 1024
    for name,m in materials.items():
        De = m['De']
        a = m['a']
        re = m['re']
        # sample r from re*0.5 to re*1.5
        r_min = float(re) * 0.5
        r_max = float(re) * 1.5
        for i in range(points_per_material):
            rf = Decimal(str(r_min + (r_max - r_min) * i / (points_per_material - 1)))
            V = morse_potential(rf, De, a, Decimal(str(re)))
            p_int, q_int = to_surd_pq(V)
            recon = pq_to_real(p_int, q_int)
            dissoc = V > De
            f.write(f"{name},{rf},{format(V,'E')},{p_int},{q_int},{format(recon,'E')},{int(dissoc)}\n")
print('Wrote', OUT)
