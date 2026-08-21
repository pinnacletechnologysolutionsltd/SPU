#!/usr/bin/env python3
"""
Run the frozen Step-5 K-operation regeneration sweep
(contract_photonics_ksweep_2026-08-20.md).

Continuous optical chain (no intermediate rounding) with per-op thermal
rotation; unconditioned (A) vs conditioned (B) regeneration evaluated from the
same trial state; independent big-int oracle; band-limited scoring [1000,30000]
with rejection diagnostic; per-op lattice-deviation trajectories and
first-boundary-crossing index; intermediate states retained for the first 1000
valid trials per cell.

Emits results/sweeps/ksweep.json. Dev hook: PHOTONIC_TRIALS=<n> overrides the
per-cell draw count.
"""
import os, json, sys, time, math
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'software', 'tests'))

from test_photonic_models_smul import ModelC_NoisyOptical, make_master_rng, trial_rng

OUTJSON = os.path.join(ROOT, 'results', 'sweeps', 'ksweep.json')
os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)

# ---------------- frozen spec parameters ----------------
N_DRAWS = int(os.environ.get('PHOTONIC_TRIALS', '60000'))
SEED = 13
KS = [1, 2, 4, 8, 16]
M_K = {1: 100, 2: 25, 4: 9, 8: 4, 16: 2}
DTS = [2.0, 5.0]
BAND_LO, BAND_HI = 1000, 30000
K_RAD = (2 * math.pi / 1550e-9) * 6.4322e-6 * 1.86e-4  # rad / K (canonical)
SUBSAMPLE_N = 1000

def exact_chain(xa, xb, ops):
    """Exact integer K-fold surd product (big ints, no intermediate clamp)."""
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
total_cells = len(DTS) * len(KS)
i = 0
for deltaT in DTS:
    dphi = K_RAD * deltaT
    for K in KS:
        i += 1
        m = M_K[K]
        t0 = time.time()
        master = make_master_rng(SEED)
        rejected = 0
        nA = nB = 0
        errA, errB = [], []
        crosses = []            # first boundary-crossing op index (K+1 if none)
        devmax_cond = []
        subsample = []          # first SUBSAMPLE_N valid trials (with states)
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
            want_states = len(subsample) < SUBSAMPLE_N
            aA, bA, aB, bB, dbg = ModelC_NoisyOptical.smul_chain_with_noise(
                a, b, ops, dphi, return_states=want_states)
            if (aA, bA) == golden:
                nA += 1
            else:
                errA += [abs(aA - golden[0]), abs(bA - golden[1])]
            if (aB, bB) == golden:
                nB += 1
            else:
                errB += [abs(aB - golden[0]), abs(bB - golden[1])]
            crosses.append(dbg['first_cross'] if dbg['first_cross'] is not None else K + 1)
            devmax_cond.append(max(dbg['dev_cond']))
            if want_states:
                subsample.append({
                    'a': a, 'b': b, 'ops': ops, 'golden': list(golden),
                    'first_cross': dbg['first_cross'],
                    'dev_uncond': dbg['dev_uncond'], 'dev_cond': dbg['dev_cond'],
                    'states': [[st.E_a_real, st.E_a_imag, st.E_b_real, st.E_b_imag,
                                st.E_a_pos, st.E_a_neg, st.E_b_pos, st.E_b_neg,
                                st.phi_a, st.phi_b] for st in dbg['states']],
                })
        n_valid = N_DRAWS - rejected
        cA = ci(nA, n_valid)
        cB = ci(nB, n_valid)
        # first-crossing histogram over ops 1..K plus "never" (bucket K+1)
        fc_hist = [crosses.count(j) for j in range(1, K + 2)]
        cells.append({
            'params': {'deltaT_K': deltaT, 'K': K, 'm_K': m, 'dphi_rad': dphi,
                       'band': [BAND_LO, BAND_HI], 'seed': SEED,
                       'n_draws': N_DRAWS, 'physical': 'canonical silicon '
                       '(n_eff=2.45, dn_eff_dT=1.86e-4, dL=6.4322e-6 m, lam0=1550 nm)'},
            'valid': n_valid, 'rejected': rejected,
            'rejection_pct': 100.0 * rejected / N_DRAWS,
            'policy_A': {'correct': nA, 'recovery_pct': 100.0 * nA / n_valid,
                         'ci_low': cA[0], 'ci_high': cA[1], **stats(errA)},
            'policy_B': {'correct': nB, 'recovery_pct': 100.0 * nB / n_valid,
                         'ci_low': cB[0], 'ci_high': cB[1], **stats(errB)},
            'diagnostics': {
                'first_cross_hist': fc_hist,       # ops 1..K, then "never"
                'devmax_cond_mean': sum(devmax_cond) / len(devmax_cond),
                'devmax_cond_max': max(devmax_cond),
                'subsample': subsample,
            },
        })
        elapsed = time.time() - t0
        print(f'Cell {i}/{total_cells} dT={deltaT:.1f}K K={K:2d} m={m:3d} -> '
              f'A={cells[-1]["policy_A"]["recovery_pct"]:6.2f}% '
              f'B={cells[-1]["policy_B"]["recovery_pct"]:6.2f}% '
              f'reject={cells[-1]["rejection_pct"]:5.1f}% ({elapsed:.0f}s) '
              f'total={(time.time()-t_start)/60:.1f}min')
        with open(OUTJSON, 'w') as f:
            json.dump({
                'sweep': 'ksweep',
                'contract': 'contract_photonics_ksweep_2026-08-20.md',
                'canonical_scheme': 'smul_chain_with_noise (continuous chain, '
                                    'no per-op rounding)',
                'master_seed': SEED,
                'n_draws_per_cell': N_DRAWS,
                'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'cells': cells,
            }, f, indent=2)

print('K-sweep complete. Output:', OUTJSON)
