#!/usr/bin/env python3
"""Generate CSV test vectors for Morse potential per-material.

Outputs: hardware/rtl/arch/material_morse_vectors.csv
Columns: material,r,V,p_int,q_int,recon,dissoc

Engineering element set (8 elements):
  C, Fe, Al, Si, Ti, Ni, Cu, W
"""

from decimal import Decimal, getcontext

getcontext().prec = 80
SQRT3 = Decimal(3).sqrt()
SCALE32 = Decimal(2147483647)
AVOGADRO = Decimal("6.02214076e23")

# Engineering element set: empirical bond energies and lengths
# De from CRC Handbook / NIST; a estimated from force-constant scaling.
materials = {
    "carbon":   {"De_kJ_per_mol": Decimal("348"), "a": Decimal("1.5"), "re": Decimal("1.54"), "Z": 6},
    "iron":     {"De_kJ_per_mol": Decimal("413"), "a": Decimal("1.2"), "re": Decimal("2.48"), "Z": 26},
    "aluminum": {"De_kJ_per_mol": Decimal("186"), "a": Decimal("1.3"), "re": Decimal("2.86"), "Z": 13},
    "silicon":  {"De_kJ_per_mol": Decimal("222"), "a": Decimal("1.4"), "re": Decimal("2.35"), "Z": 14},
    "titanium": {"De_kJ_per_mol": Decimal("284"), "a": Decimal("1.2"), "re": Decimal("2.93"), "Z": 22},
    "nickel":   {"De_kJ_per_mol": Decimal("203"), "a": Decimal("1.4"), "re": Decimal("2.49"), "Z": 28},
    "copper":   {"De_kJ_per_mol": Decimal("202"), "a": Decimal("1.3"), "re": Decimal("2.56"), "Z": 29},
    "tungsten": {"De_kJ_per_mol": Decimal("480"), "a": Decimal("1.4"), "re": Decimal("2.74"), "Z": 74},
}

for m in materials.values():
    De_j_per_mol = m["De_kJ_per_mol"] * Decimal("1000")
    m["De"] = De_j_per_mol / AVOGADRO


def to_surd_pq(value, scale=SCALE32):
    v = Decimal(value)
    qf = v / SQRT3
    q_int = int((qf * scale).to_integral_value(rounding="ROUND_HALF_EVEN"))
    q = Decimal(q_int) / scale
    p = v - q * SQRT3
    p_int = int((p * scale).to_integral_value(rounding="ROUND_HALF_EVEN"))

    def clamp32(x):
        return max(-(2**31), min(2**31 - 1, x))

    return clamp32(p_int), clamp32(q_int)


def pq_to_real(p_int, q_int, scale=SCALE32):
    return Decimal(p_int) / scale + (Decimal(q_int) / scale) * SQRT3


def morse_potential(r, De, a, re):
    x = -(a * (r - re))
    ex = x.exp()
    return De * (Decimal(1) - ex) ** 2


OUT = "hardware/rtl/arch/material_morse_vectors.csv"
with open(OUT, "w") as f:
    f.write("material,Z,r,V,p_int,q_int,recon,dissoc\n")
    points_per_material = 1024
    for name, m in materials.items():
        De = m["De"]
        a = m["a"]
        re = m["re"]
        Z = m["Z"]
        r_min = float(re) * 0.5
        r_max = float(re) * 1.5
        for i in range(points_per_material):
            rf = Decimal(
                str(r_min + (r_max - r_min) * i / (points_per_material - 1))
            )
            V = morse_potential(rf, De, a, Decimal(str(re)))
            p_int, q_int = to_surd_pq(V)
            recon = pq_to_real(p_int, q_int)
            dissoc = 1 if V > De else 0
            f.write(
                f"{name},{Z},{rf},{format(V,'E')},{p_int},{q_int},{format(recon,'E')},{dissoc}\n"
            )
print(f"Wrote {OUT} ({len(materials)} elements × {points_per_material} points)")
