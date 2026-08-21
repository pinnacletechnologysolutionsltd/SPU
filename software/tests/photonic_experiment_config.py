"""
photonic_experiment_config.py — Phase 1 reproducibility scaffold for Model C.

Purpose: make single-operation physical-noise experiments auditable and
rerunnable — "same params + same seed -> same result" — before any Phase 2
sweep or Phase 3/4 (K-op cascade) work begins. See spu_strategy/SESSION_SUMMARY.md
for the phased plan this supports.

Wraps ModelC_NoisyOptical.smul_with_noise (test_photonic_models_smul.py) rather
than reimplementing it. NOT all listed fields are wired into the underlying
noise model yet — coupler_error and crosstalk_dB are recorded for audit
completeness but currently have no effect; see NOT_WIRED below.
"""

import json
import math
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from test_photonic_models_smul import (
    ModelA_ExactSPU, ModelC_NoisyOptical, make_master_rng, trial_rng, _HAS_NUMPY,
)

NOT_WIRED = ('coupler_error', 'crosstalk_dB')


@dataclass
class PhysicalParams:
    """Auditable physical parameterization for one Model C experiment."""
    seed: int = 13
    num_trials: int = 500
    noise_mode: str = 'C2'          # 'C0'/'C1' stochastic phase, 'C2' physical thermo-optic drift
    lo_track: bool = False

    # Thermo-optic / waveguide (used when noise_mode == 'C2')
    # Canonical silicon design values, consistent with the physical constants in
    # test_photonic_surd_oracle.py (n_eff=2.45, dn_eff_dT=1.86e-4, 60° delay line
    # delta_L_m10 = 6.4322 um). Single source of truth for unspecified params.
    lambda0_nm: float = 1550.0
    n_eff: float = 2.45
    dn_eff_dT: float = 1.86e-4       # 1/K, silicon thermo-optic coefficient
    deltaT: float = 0.0             # K, the swept variable in a temperature experiment
    deltaL_a: float = 6.4322e-6     # m, m=10 delay-line length
    deltaL_b: float = 6.4322e-6     # m
    dphi_dlambda_a: float = 0.0
    dphi_dlambda_b: float = 0.0
    delta_lambda_nm: float = 0.0

    # Stochastic residuals / impairments (all noise_modes)
    sigma_phi_deg: float = 0.0
    sigma_amp: float = 0.0
    waveguide_loss_dB: float = 0.0
    coupler_error: float = 0.0      # reserved, not yet wired — see NOT_WIRED
    crosstalk_dB: float = 0.0       # reserved, not yet wired — see NOT_WIRED
    detector_noise: float = 0.0
    calibration_error: float = 0.0
    loss_normalize: bool = False

    def to_c2_dict(self) -> Dict[str, Any]:
        return {
            'deltaT': self.deltaT, 'dn_eff_dT': self.dn_eff_dT, 'n_eff': self.n_eff,
            'dDeltaL_dT_a': 0.0, 'dDeltaL_dT_b': 0.0,
            'lam_a_nm': self.lambda0_nm, 'lam_b_nm': self.lambda0_nm,
            'dphi_dlambda_a': self.dphi_dlambda_a, 'dphi_dlambda_b': self.dphi_dlambda_b,
            'delta_lambda': self.delta_lambda_nm,
            'deltaL_a': self.deltaL_a, 'deltaL_b': self.deltaL_b,
        }


def run_experiment(params: PhysicalParams, out_path: Optional[str] = None) -> Dict[str, Any]:
    """Run one Model-C single-operation sweep point under `params`.

    Reruns with identical params reproduce identical results: operand draws and
    noise draws both come from trial_rng(master_rng(params.seed), trial_index).
    """
    master = make_master_rng(params.seed)
    sigma_phi_rad = params.sigma_phi_deg * math.pi / 180.0
    c2_params = params.to_c2_dict() if params.noise_mode == 'C2' else None

    correct = 0
    errors: List[int] = []  # coordinate-wise |delta| over failed trials

    for trial in range(params.num_trials):
        rng = trial_rng(master, trial)
        if _HAS_NUMPY:
            a, b, c, d = (int(rng.integers(-100, 101)) for _ in range(4))
        else:
            a, b, c, d = (rng.randint(-100, 100) for _ in range(4))

        golden = ModelA_ExactSPU.smul(a, b, c, d)
        noisy = ModelC_NoisyOptical.smul_with_noise(
            a, b, c, d,
            sigma_phi=sigma_phi_rad,
            sigma_amp=params.sigma_amp,
            loss_dB=params.waveguide_loss_dB,
            noise_mode=params.noise_mode,
            lo_track=params.lo_track,
            detector_noise=params.detector_noise,
            trial_rng_obj=rng,
            loss_normalize=params.loss_normalize,
            calibration_error=params.calibration_error,
            physical_params=c2_params,
        )

        if noisy == golden:
            correct += 1
        else:
            errors.append(abs(noisy[0] - golden[0]))
            errors.append(abs(noisy[1] - golden[1]))

    n = params.num_trials
    p = correct / n
    se = math.sqrt(max(p * (1 - p), 0.0) / n)
    ci_low = max(0.0, (p - 1.96 * se) * 100.0)
    ci_high = min(100.0, (p + 1.96 * se) * 100.0)
    if errors:
        mae = sum(errors) / len(errors)
        rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
        srt = sorted(errors)
        median = srt[len(srt) // 2]
        q95 = srt[max(0, int(0.95 * len(srt)) - 1)]
        q99 = srt[max(0, int(0.99 * len(srt)) - 1)]
    else:
        mae = rmse = median = q95 = q99 = 0.0

    result = {
        'params': asdict(params),
        'not_wired': NOT_WIRED,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'correct': correct,
        'num_trials': n,
        'recovery_pct': 100.0 * p,
        'ci_low': ci_low,
        'ci_high': ci_high,
        'mae': mae,
        'rmse': rmse,
        'median': median,
        'q95': q95,
        'q99': q99,
    }

    if out_path:
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)

    return result


def verify_reproducible(params: PhysicalParams) -> bool:
    """Run twice with identical params; same seed must give bit-identical results."""
    r1 = run_experiment(params)
    r2 = run_experiment(params)
    return r1['correct'] == r2['correct'] and r1['mae'] == r2['mae']


if __name__ == '__main__':
    p = PhysicalParams(seed=13, num_trials=500, noise_mode='C2', deltaT=10.0)
    assert verify_reproducible(p), "same seed did not reproduce identical results"
    result = run_experiment(p)
    print(json.dumps(result, indent=2))
