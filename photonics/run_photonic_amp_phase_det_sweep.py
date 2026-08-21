#!/usr/bin/env python3
"""
Run combined amplitude x phase x detector-noise sweep (C1 mode) via the
canonical reproducibility harness, on the SAME frozen canonical base as
results #1-#3 (silicon design, seed 13, shared trial-index-aligned stream).

Amplitude noise draws from the per-trial RNG (post-2026-08-20 rng fix), so all
three axes are bit-reproducible and per-trial predictable.

Emits results/sweeps/amp_phase_det_sweep.json (full PhysicalParams per cell).

Dev hook: PHOTONIC_TRIALS=<n> overrides the per-cell trial count.
"""
import os, json, sys, time
from dataclasses import replace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from photonic_experiment_config import PhysicalParams, run_experiment

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'amp_phase_det_sweep.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

num_trials = int(os.environ.get('PHOTONIC_TRIALS', '16000'))
master_seed = 13

# Grids: differential phase (deg), amplitude fluctuation, detector noise.
sigma_phi_deg_vals = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]
sigma_amp_vals = [0.0, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2]
detector_noise_vals = [0.0, 1e-4, 1e-3, 5e-3, 1e-2]

# Canonical frozen base: C1 (differential phase), everything else ideal.
base = PhysicalParams(seed=master_seed, num_trials=num_trials,
                      noise_mode='C1', lo_track=False)

cells = []
t_start = time.time()
total = len(sigma_phi_deg_vals) * len(sigma_amp_vals) * len(detector_noise_vals)
i = 0
for phi_deg in sigma_phi_deg_vals:
    for amp in sigma_amp_vals:
        for det in detector_noise_vals:
            i += 1
            t0 = time.time()
            p = replace(base, sigma_phi_deg=phi_deg, sigma_amp=amp,
                        detector_noise=det)
            res = run_experiment(p)
            cells.append(res)
            elapsed = time.time() - t0
            print(f'Cell {i}/{total} phi={phi_deg:+.1f}deg amp={amp:.0e} det={det:.0e} -> '
                  f'{res["recovery_pct"]:.2f}% ({elapsed:.1f}s) '
                  f'total={(time.time()-t_start)/60:.1f}min')
            with open(OUTJSON, 'w') as f:
                json.dump({
                    'sweep': 'amp_phase_det',
                    'canonical_scheme': 'photonic_experiment_config.py',
                    'master_seed': master_seed,
                    'num_trials': num_trials,
                    'operand_stream': 'shared across cells (trial-index aligned, paired design)',
                    'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'cells': cells,
                }, f, indent=2)

print('Amp x phase x det sweep complete. Output:', OUTJSON)
