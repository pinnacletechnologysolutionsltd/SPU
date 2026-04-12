#!/usr/bin/env python3
"""
Generate deterministic phinary golden vectors for use by RTL and VM tests.
Writes software/tools/phinary_vectors.json
"""
from pathlib import Path
import importlib.util
import json

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("phinary_ref", str(here / "phinary_ref.py"))
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

vectors = {}

# Full small [4-bit, INT_BITS=2] table (all 0..15 pairs)
w = 4
ib = 2
pairs = []
for a in range(0, 1<<w):
    for b in range(0, 1<<w):
        for chir in (0, 1):
            out, void_out, ovf = ph.add_phinary(a, b, width=w, int_bits=ib, laminar_thr=10, chirality=bool(chir), void_state_in=False)
            pairs.append({"A": a, "B": b, "chir": chir, "out": out, "void": int(void_out), "ovf": int(ovf)})
vectors[f"toy_{w}_{ib}"] = pairs

# Representative samples for wider widths
w = 16
ib = 8
samples = [ (0, 0), (1, 1), (0xffff, 0xffff), (0x1234, 0x0f0f), (0x00ff, 0x00ff) ]
pairs16 = []
for a, b in samples:
    for chir in (0,1):
        out, void_out, ovf = ph.add_phinary(a, b, width=w, int_bits=ib, laminar_thr=10, chirality=bool(chir), void_state_in=False)
        pairs16.append({"A": a, "B": b, "chir": chir, "out": out, "void": int(void_out), "ovf": int(ovf)})

vectors[f"sample_{w}_{ib}"] = pairs16

# Write JSON
out_file = here / "phinary_vectors.json"
with open(out_file, 'w') as fh:
    json.dump(vectors, fh, indent=2)

print(f"Wrote {out_file} ({sum(len(v) for v in vectors.values())} vectors)")
