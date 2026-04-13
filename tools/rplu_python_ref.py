#!/usr/bin/env python3
"""RPLU Python reference: rational-surd helpers and Morse potential demo.
Generates Material Matrix samples (Carbon, Iron) and evaluates Morse potential
and dissociation checks for sample displacements.
"""
from decimal import Decimal, getcontext
import math

getcontext().prec = 80

SQRT3 = Decimal(3).sqrt()
SCALE32 = Decimal(2147483647)

def to_surd_pq(value, scale=SCALE32):
    # Project real value onto basis {1, sqrt(3)}: find Q approx then P
    # q = round((v / sqrt3) * scale) / scale
    v = Decimal(value)
    qf = v / SQRT3
    q_int = int(qf * scale + Decimal('0.5')) if qf >= 0 else int(qf * scale - Decimal('0.5'))
    q = Decimal(q_int) / scale
    p = v - q * SQRT3
    p_int = int(p * scale + Decimal('0.5')) if p >= 0 else int(p * scale - Decimal('0.5'))
    # clamp to signed 32-bit
    def clamp32(x):
        if x < -2**31: return -2**31
        if x > 2**31-1: return 2**31-1
        return x
    p_int = clamp32(p_int)
    q_int = clamp32(q_int)
    return p_int, q_int

def pq_to_real(p_int, q_int, scale=SCALE32):
    return Decimal(p_int) / scale + (Decimal(q_int) / scale) * SQRT3

# Morse potential: V(r) = De * (1 - exp(-a*(r - re)))^2
# Use Decimal exp for high precision

def morse_potential(r, De, a, re):
    # r, De, a, re are Decimal
    x = -(a * (r - re))
    # use Decimal.exp via math.exp on float? Decimal doesn't have exp by default prior to 3.11
    # Use Taylor via math.exp with high precision by converting to float - acceptable for ref
    ex = Decimal(str(math.exp(float(x))))
    val = De * (Decimal(1) - ex)**2
    return val

# Material matrix example
# Material constants: use empirical dissociation energies (kJ/mol -> J per bond)
# Values chosen as examples: C-C single bond ~348 kJ/mol, Fe cohesive ~413 kJ/mol
AVOGADRO = Decimal('6.02214076e23')
materials = {
    'carbon': {
        'De_kJ_per_mol': Decimal('348'),   # kJ/mol
        'a': Decimal('1.5'),               # 1/Angstrom (approx)
        're': Decimal('1.54')              # Angstrom (C-C single)
    },
    'iron': {
        'De_kJ_per_mol': Decimal('413'),
        'a': Decimal('1.2'),
        're': Decimal('2.48')              # Approximate nearest-neighbour distance (Angstrom)
    }
}
# Convert kJ/mol -> J per bond and store De as Decimal
for m in materials.values():
    De_j_per_mol = m['De_kJ_per_mol'] * Decimal('1000')
    m['De'] = De_j_per_mol / AVOGADRO

# Sample scenario: a tensegrity bond with base spread s -> map to r
# Simplify: use spread as normalized displacement r in [0,2]

def run_demo():
    print('Material matrix entries (surd P32/Q32):')
    for name,m in materials.items():
        De = m['De']; a = m['a']; re = m['re']
        # encode De and a into P/Q surd fields
        pD,qD = to_surd_pq(De)
        pA,qA = to_surd_pq(a)
        print(f"- {name}: De={De} J (per bond) => P/Q=({pD},{qD}), a=({pA},{qA}), re={re}")

    print('\nSample Morse evaluations:')
    for name,m in materials.items():
        De = m['De']; a = m['a']; re = m['re']
        print(f'\n{name.upper()}')
        for r_float in [0.5, 0.9, 1.0, 1.1, 1.4, 2.0]:
            r = Decimal(str(r_float))
            V = morse_potential(r, De, a, re)
            pV,qV = to_surd_pq(V)
            recon = pq_to_real(pV,qV)
            # check dissociation if V > De
            diss = V > De
            print(f'r={r_float:0.2f} V={format(V, "E")} => PQ=({pV},{qV}) recon={format(recon, "E")} dissoc={diss}')

if __name__ == '__main__':
    run_demo()
