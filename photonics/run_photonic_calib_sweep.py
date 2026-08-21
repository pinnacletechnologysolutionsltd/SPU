#!/usr/bin/env python3
"""
Run calibration-error sweep (C1 mode, static 1.8 dB insertion loss,
loss-normalized BQE) via the canonical reproducibility harness.

Only calibration_error eps varies; every other impairment is ideal and the
physical parameters are the frozen canonical silicon design. master_seed and
the trial-index-aligned operand stream are identical to the frozen deltaT
sweep, so per-trial operands can be cross-referenced across experiments.

Emits results/sweeps/calib_sweep.json (full PhysicalParams per cell).

Dev hook: PHOTONIC_TRIALS=<n> overrides the per-cell trial count.
"""
import os, json, sys, time
from dataclasses import replace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from photonic_experiment_config import PhysicalParams, run_experiment

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'calib_sweep.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

num_trials = int(os.environ.get('PHOTONIC_TRIALS', '16000'))
master_seed = 13

# Grid: baseline 0.0 plus +/- magnitudes spanning the transition (1e-5..1e-3)
# through the collapsed tail (up to 5e-2). Includes the older sweep's values.
calib_mags = [1e-5, 2e-5, 3e-5, 5e-5, 7.5e-5, 1e-4, 2e-4, 5e-4,
              1e-3, 2.5e-3, 5e-3, 1e-2, 2e-2, 5e-2]
calib_errors = [0.0] + sorted([-m for m in calib_mags] + [m for m in calib_mags])

# Static known insertion loss (1.8 dB) removed by loss-normalized BQE; only the
# accuracy with which the receiver knows that loss (calibration_error) varies.
base = PhysicalParams(seed=master_seed, num_trials=num_trials,
                      noise_mode='C1', lo_track=False,
                      waveguide_loss_dB=1.8, loss_normalize=True)

cells = []
t_start = time.time()
for i, eps in enumerate(calib_errors):
    t0 = time.time()
    p = replace(base, calibration_error=eps)
    res = run_experiment(p)
    cells.append(res)
    elapsed = time.time() - t0
    print(f'Cell {i+1}/{len(calib_errors)} eps={eps:+.2e} -> '
          f'{res["recovery_pct"]:.2f}% ({elapsed:.1f}s) '
          f'total={(time.time()-t_start)/60:.1f}min')
    with open(OUTJSON, 'w') as f:
        json.dump({
            'sweep': 'calib',
            'canonical_scheme': 'photonic_experiment_config.py',
            'master_seed': master_seed,
            'num_trials': num_trials,
            'operand_stream': 'shared across cells (trial-index aligned, paired design)',
            'static_loss_dB': 1.8,
            'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'cells': cells,
        }, f, indent=2)

print('Calibration-error sweep complete. Output:', OUTJSON)
