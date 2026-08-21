#!/usr/bin/env python3
"""
Run combined ΔT × calibration-error sweep (C2 mode) via the canonical
reproducibility harness, on the SAME frozen canonical physical base as
deltaT_sweep_frozen_v1 and calib_sweep_frozen_v1 (silicon design, seed 13,
shared trial-index-aligned operand stream).

Purpose: map the joint error surface — do thermo-optic drift (deltaT) and
loss-calibration error (eps) add, interact nonlinearly, or cancel?
Predicted mechanism: recovered = round(x * cos(dphi) / (1+eps)), so a trial
fails iff |x| * |1 - cos(dphi)/(1+eps)| >= 0.5; eps < 0 can partially cancel
cos-attenuation (ridge at eps* ~= -dphi^2/2).

Emits results/sweeps/deltaT_calib_sweep.json (full PhysicalParams per cell).

Dev hook: PHOTONIC_TRIALS=<n> overrides the per-cell trial count.
"""
import os, json, sys, time
from dataclasses import replace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from photonic_experiment_config import PhysicalParams, run_experiment

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'deltaT_calib_sweep.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

num_trials = int(os.environ.get('PHOTONIC_TRIALS', '16000'))
master_seed = 13

# Grids: deltaT resolves the thermal envelope (frozen #1), eps resolves the
# calibration envelope (frozen #2), including the predicted cancellation ridge
# at eps* ~= -dphi^2/2 (dphi(2K)=0.0097 -> ~-4.7e-5; dphi(5K)=0.0242 -> ~-2.9e-4).
deltaT_vals = [-5.0, -2.0, -1.0, 0.0, 1.0, 2.0, 5.0]  # Kelvin
calib_mags = [1e-5, 2e-5, 3e-5, 5e-5, 7.5e-5, 1e-4, 2e-4, 3e-4, 5e-4,
              1e-3, 2.5e-3, 5e-3, 1e-2, 2e-2, 5e-2]
calib_errors = [0.0] + sorted([-m for m in calib_mags] + [m for m in calib_mags])

# Canonical frozen base: C2 thermal drift + static 1.8 dB loss with
# loss-normalized BQE under calibration error; everything else ideal.
base = PhysicalParams(seed=master_seed, num_trials=num_trials,
                      noise_mode='C2', lo_track=False,
                      waveguide_loss_dB=1.8, loss_normalize=True)

cells = []
t_start = time.time()
total = len(deltaT_vals) * len(calib_errors)
i = 0
for deltaT in deltaT_vals:
    for eps in calib_errors:
        i += 1
        t0 = time.time()
        p = replace(base, deltaT=deltaT, calibration_error=eps)
        res = run_experiment(p)
        cells.append(res)
        elapsed = time.time() - t0
        print(f'Cell {i}/{total} deltaT={deltaT:+4.1f}K eps={eps:+.2e} -> '
              f'{res["recovery_pct"]:.2f}% ({elapsed:.1f}s) '
              f'total={(time.time()-t_start)/60:.1f}min')
        with open(OUTJSON, 'w') as f:
            json.dump({
                'sweep': 'deltaT_calib',
                'canonical_scheme': 'photonic_experiment_config.py',
                'master_seed': master_seed,
                'num_trials': num_trials,
                'operand_stream': 'shared across cells (trial-index aligned, paired design)',
                'static_loss_dB': 1.8,
                'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'cells': cells,
            }, f, indent=2)

print('ΔT × calib sweep complete. Output:', OUTJSON)
