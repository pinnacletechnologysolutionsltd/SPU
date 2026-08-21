#!/usr/bin/env python3
"""
Run C2 physical deltaT sweep (temperature only; all other impairments ideal)
via the canonical reproducibility harness.

Emits results/sweeps/deltaT_sweep.json containing the full PhysicalParams for
every cell, so each cell is independently replayable with
photonic_experiment_config.run_experiment (see results/sweeps/README.md).

Dev hook: PHOTONIC_TRIALS=<n> overrides the per-cell trial count (smoke runs).
"""
import os, json, sys, time
from dataclasses import replace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from photonic_experiment_config import PhysicalParams, run_experiment

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'deltaT_sweep.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

num_trials = int(os.environ.get('PHOTONIC_TRIALS', '16000'))
master_seed = 13

# Grid (user-selected "Full"); canonical silicon-design physical base, so the
# only thing varying across cells is deltaT.
deltaT_vals = [-5.0, -2.0, -1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0, 2.0, 5.0]  # Kelvin
base = PhysicalParams(seed=master_seed, num_trials=num_trials,
                      noise_mode='C2', lo_track=False)

cells = []
t_start = time.time()
for i, deltaT in enumerate(deltaT_vals):
    t0 = time.time()
    p = replace(base, deltaT=deltaT)
    res = run_experiment(p)
    cells.append(res)
    elapsed = time.time() - t0
    print(f'Cell {i+1}/{len(deltaT_vals)} deltaT={deltaT:+4.1f}K -> '
          f'{res["recovery_pct"]:.2f}% ({elapsed:.1f}s) total={ (time.time()-t_start)/60:.1f}min')
    # incremental write: an interrupted run keeps completed cells
    with open(OUTJSON, 'w') as f:
        json.dump({
            'sweep': 'deltaT',
            'canonical_scheme': 'photonic_experiment_config.py',
            'master_seed': master_seed,
            'num_trials': num_trials,
            'operand_stream': 'shared across cells (trial-index aligned, paired design)',
            'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'cells': cells,
        }, f, indent=2)

print('DeltaT sweep complete. Output:', OUTJSON)
