"""Readback only: inspect canonical values, certify bounded file and report selected fields."""
import json
from pathlib import Path
p=Path('research/qcg_0/QUINTIC_FIXTURE_VALUES.json')
d=json.loads(p.read_text())
print(json.dumps({k:d['PH5'][k] for k in ('N_raw','D_raw','endpoint','endpoint_curvature_pairs_corrected','bernstein')}))
print(json.dumps(d['controls']['harmonic_order4']))
