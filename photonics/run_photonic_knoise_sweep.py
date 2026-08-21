#!/usr/bin/env python3
"""
Run the frozen Step-6 K-chain with per-op stochastic noise sweep
(contract_photonics_knoise_sweep_2026-08-20.md).

Single-factor sub-sweeps (sigma_phi / sigma_amp / detector_noise), 4 levels
each x K in {1,2,4,8,16}, dT=2K conditioned. Arm A (regenerate every op) vs
arm B (chain, one final regeneration) from the SAME paired per-trial stream.
Independent big-int oracle, band [1000,30000], rejection diagnostic.

Emits results/sweeps/knoise_sweep.json. Dev hook: PHOTONIC_TRIALS=<n> overrides
the per-cell draw count.
"""
import os, json, sys, time, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from test_photonic_models_smul import ModelC_NoisyOptical, make_master_rng, trial_rng

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'knoise_sweep.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

# ---------------- frozen spec parameters ----------------
N_DRAWS = int(os.environ.get('PHOTONIC_TRIALS', '30000'))
SEED = 13
KS = [1, 2, 4, 8, 16]
M_K = {1: 100, 2: 25, 4: 9, 8: 4, 16: 2}
DT = 2.0
K_RAD = (2 * math.pi / 1550e-9) * 6.4322e-6 * 1.86e-4
DPHI = K_RAD * DT
BAND_LO, BAND_HI = 1000, 30000
SUBSAMPLE_N = 200

# factor -> (levels, other-params-zero)
FACTORS = [
    ('phi_deg', [0.0, 0.25, 0.5, 1.0]),
    ('amp', [0.0, 1e-5, 2.5e-5, 5e-5]),
    ('det', [0.0, 1e-4, 3e-4, 1e-3]),
]

def exact_chain(xa, xb, ops):
    for c, d in ops:
        xa, xb = xa * c + 3 * xb * d, xa * d + xb * c
    return xa, xb

def stats(errors):
    if not errors:
        return dict(mae=0.0, rmse=0.0, median=0.0, q95=0.0, q99=0.0)
    srt = sorted(errors)
    return dict(
        mae=sum(errors) / len(errors),
        rmse=math.sqrt(sum(e * e for e in errors) / len(errors)),
        median=srt[len(srt) // 2],
        q95=srt[max(0, int(0.95 * len(srt)) - 1)],
        q99=srt[max(0, int(0.99 * len(srt)) - 1)],
    )

def ci(n_correct, n_total):
    p = n_correct / n_total
    se = math.sqrt(max(p * (1 - p), 0.0) / n_total)
    return max(0.0, (p - 1.96 * se) * 100.0), min(100.0, (p + 1.96 * se) * 100.0)

cells = []
t_start = time.time()
total_cells = len(FACTORS) * 4 * len(KS)
i = 0
for factor, levels in FACTORS:
    for level in levels:
        for K in KS:
            i += 1
            m = M_K[K]
            t0 = time.time()
            if factor == 'phi_deg':
                sphi, samp, sdet = level * math.pi / 180.0, 0.0, 0.0
            elif factor == 'amp':
                sphi, samp, sdet = 0.0, level, 0.0
            else:
                sphi, samp, sdet = 0.0, 0.0, level
            master = make_master_rng(SEED)
            rejected = 0
            nA = nB = 0
            errA, errB = [], []
            first_fail_hist = [0] * (K + 1)   # op 1..K, bucket K+1 = never
            sigmas = []                       # arm B total_scale per valid trial
            subsample = []
            for trial in range(N_DRAWS):
                rng = trial_rng(master, trial)
                a = int(rng.integers(-m, m + 1)); b = int(rng.integers(-m, m + 1))
                ops = [(int(rng.integers(-m, m + 1)), int(rng.integers(-m, m + 1)))
                       for _ in range(K)]
                xa, xb = exact_chain(a, b, ops)
                if not (BAND_LO <= max(abs(xa), abs(xb)) <= BAND_HI):
                    rejected += 1
                    continue
                golden = (max(-32768, min(32767, xa)), max(-32768, min(32767, xb)))
                want = len(subsample) < SUBSAMPLE_N
                rngA = trial_rng(master, trial)
                ra, rb, dbgA = ModelC_NoisyOptical.smul_chain_noise(
                    a, b, ops, DPHI, sphi, samp, sdet, rngA, mode='A',
                    return_debug=True)
                rngB = trial_rng(master, trial)
                sa2, sb2, dbgB = ModelC_NoisyOptical.smul_chain_noise(
                    a, b, ops, DPHI, sphi, samp, sdet, rngB, mode='B',
                    return_debug=True)
                if (ra, rb) == golden:
                    nA += 1
                else:
                    errA += [abs(ra - golden[0]), abs(rb - golden[1])]
                if (sa2, sb2) == golden:
                    nB += 1
                else:
                    errB += [abs(sa2 - golden[0]), abs(sb2 - golden[1])]
                ff = dbgA['first_failed_op']
                first_fail_hist[(ff - 1) if (ff and ff > 0) else K] += 1
                sigmas.append(dbgB['total_scale'])
                if want:
                    subsample.append({'a': a, 'b': b, 'ops': ops,
                                      'golden': list(golden),
                                      'first_failed_A': ff,
                                      'total_scale_B': dbgB['total_scale']})
            n_valid = N_DRAWS - rejected
            cA = ci(nA, n_valid)
            cB = ci(nB, n_valid)
            cells.append({
                'params': {'factor': factor, 'level': level, 'K': K, 'm_K': m,
                           'deltaT_K': DT, 'dphi_rad': DPHI,
                           'sigma_phi_deg': factor == 'phi_deg' and level or 0.0,
                           'sigma_amp': factor == 'amp' and level or 0.0,
                           'detector_noise': factor == 'det' and level or 0.0,
                           'band': [BAND_LO, BAND_HI], 'seed': SEED,
                           'n_draws': N_DRAWS, 'conditioning': 'dT=2K, cos-trimmed'},
                'valid': n_valid, 'rejected': rejected,
                'rejection_pct': 100.0 * rejected / N_DRAWS,
                'arm_A': {'correct': nA, 'recovery_pct': 100.0 * nA / n_valid,
                          'ci_low': cA[0], 'ci_high': cA[1], **stats(errA)},
                'arm_B': {'correct': nB, 'recovery_pct': 100.0 * nB / n_valid,
                          'ci_low': cB[0], 'ci_high': cB[1], **stats(errB)},
                'diagnostics': {
                    'first_fail_A_hist': first_fail_hist,
                    'sigma_total_mean': sum(sigmas) / len(sigmas),
                    'sigma_total_max': max(sigmas),
                    'subsample': subsample,
                },
            })
            elapsed = time.time() - t0
            cell = cells[-1]
            print(f'Cell {i}/{total_cells} {factor}={level:g} K={K:2d} -> '
                  f'A={cell["arm_A"]["recovery_pct"]:6.2f}% '
                  f'B={cell["arm_B"]["recovery_pct"]:6.2f}% '
                  f'reject={cell["rejection_pct"]:5.1f}% ({elapsed:.0f}s) '
                  f'total={(time.time()-t_start)/60:.1f}min')
            with open(OUTJSON, 'w') as f:
                json.dump({
                    'sweep': 'knoise_sweep',
                    'contract': 'contract_photonics_knoise_sweep_2026-08-20.md',
                    'master_seed': SEED,
                    'n_draws_per_cell': N_DRAWS,
                    'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'cells': cells,
                }, f, indent=2)

print('K-noise sweep complete. Output:', OUTJSON)
