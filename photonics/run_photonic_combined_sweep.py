#!/usr/bin/env python3
"""
Run combined calibration-error × amplitude × detector-noise sweep (C1 mode,
static 1.8 dB loss, loss-normalized BQE with calibration error) via the
canonical reproducibility harness.

Emits results/sweeps/calib_amp_det_combined.json containing the full
PhysicalParams for every cell, so each cell is independently replayable with
photonic_experiment_config.run_experiment (see results/sweeps/README.md).

Dev hook: PHOTONIC_TRIALS=<n> overrides the per-cell trial count (smoke runs).
"""
import os, json, sys, time
from dataclasses import replace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from photonic_experiment_config import PhysicalParams, run_experiment

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'calib_amp_det_combined.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

num_trials = int(os.environ.get('PHOTONIC_TRIALS', '16000'))
master_seed = 13

# Grid definitions (user-selected "Full")
calib_errors = [0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.05]
sigma_amps = [0.0, 0.001, 0.005, 0.01, 0.02]
detector_noises = [0.0, 1e-4, 1e-3, 5e-3, 1e-2]

# C1 (stochastic differential phase, sigma_phi ideal), known static insertion
# loss with imperfect calibration via loss_normalize + calibration_error.
base = PhysicalParams(seed=master_seed, num_trials=num_trials,
                      noise_mode='C1', lo_track=False,
                      waveguide_loss_dB=1.8, loss_normalize=True)

cells = []
t_start = time.time()
total_cells = len(calib_errors) * len(sigma_amps) * len(detector_noises)
i = 0
for eps in calib_errors:
    for amp in sigma_amps:
        for det in detector_noises:
            i += 1
            t0 = time.time()
            p = replace(base, sigma_amp=amp, detector_noise=det,
                        calibration_error=eps)
            res = run_experiment(p)
            cells.append(res)
            elapsed = time.time() - t0
            print(f'Cell {i}/{total_cells} eps={eps} amp={amp} det={det} -> '
                  f'{res["recovery_pct"]:.2f}% ({elapsed:.1f}s) '
                  f'total={(time.time()-t_start)/60:.1f}min')
            with open(OUTJSON, 'w') as f:
                json.dump({
                    'sweep': 'calib_amp_det_combined',
                    'canonical_scheme': 'photonic_experiment_config.py',
                    'master_seed': master_seed,
                    'num_trials': num_trials,
                    'operand_stream': 'shared across cells (trial-index aligned, paired design)',
                    'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'cells': cells,
                }, f, indent=2)

print('Sweep complete. Output:', OUTJSON)
