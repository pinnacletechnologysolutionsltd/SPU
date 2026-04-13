#!/usr/bin/env python3
"""
phinary_vm_test.py

Run automated checks comparing phinary_vm_helpers.add_phinary against
software/tools/phinary_vectors.json golden vectors.
"""
import os
import json
import importlib.util

here = os.path.dirname(__file__)
# load helpers
spec = importlib.util.spec_from_file_location('phinary_vm_helpers', os.path.join(here,'phinary_vm_helpers.py'))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

vec_file = os.path.join(here, 'phinary_vectors.json')
if not os.path.exists(vec_file):
    print('phinary_vectors.json not found; run generate_phinary_vectors.py first')
    raise SystemExit(1)

vectors = json.load(open(vec_file))

failures = 0
checked = 0
for setname, vecs in vectors.items():
    print('Testing set', setname)
    for v in vecs:
        A = int(v['A'])
        B = int(v['B'])
        chir = int(v.get('chir',0))
        expected_out = int(v['out'])
        expected_void = int(v.get('void',0))
        expected_ovf = int(v.get('ovf',0))
        # width / int_bits inferred from setname if possible
        if setname.startswith('toy_'):
            width = 4
            int_bits = 2
        elif setname.startswith('sample_'):
            parts = setname.split('_')
            width = int(parts[1])
            int_bits = int(parts[2])
        else:
            width = 16
            int_bits = 8
        out, void_out, ovf = helpers.add_phinary(A, B, width=width, int_bits=int_bits, laminar_thr=10, chirality=bool(chir), void_state=False)
        checked += 1
        if out != expected_out or int(void_out) != expected_void or int(ovf) != expected_ovf:
            print(f"FAIL {setname}: A={A} B={B} chir={chir} -> got out={out} void={int(void_out)} ovf={int(ovf)} expected out={expected_out} void={expected_void} ovf={expected_ovf}")
            failures += 1

print('\nChecked', checked, 'vectors; failures =', failures)
if failures == 0:
    print('phinary_vm_test: PASS')
    raise SystemExit(0)
else:
    print('phinary_vm_test: FAIL')
    raise SystemExit(2)
