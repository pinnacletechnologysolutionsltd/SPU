#!/usr/bin/env python3
"""run_photonic_pair0_sensitivity_check.py -- Phase 0 of
contract_photonics_pair0_calibration_2026-08-24.md: is pair-0's missing
calibration even quantitatively capable of explaining the corrected
reliability model's overshoot
(contract_photonics_corrected_reliability_model_2026-08-24.md SS9)?

Pure sensitivity/attribution check, not a new calibration -- replays the
SAME trial sequence (SEED, TRIAL_OFFSET, N_TRIALS unchanged from
run_photonic_corrected_reliability_sweep.py) and asks: for a swept
hypothetical flat correction factor p_hat_0 replacing pair 0's
p_event_fit(m0_2, sigma_det) fallback term, does ANY plausible p_hat_0
bring mean_corrected back inside empirical_rate's 95% CI?

mean_corrected(p_hat_0) = p_hat_0 * mean(base), where
base = corrected_p_chain / p_event_fit(m0_2, sigma_det)
     = p_event_fit(m0_1, sigma_det) * product over pairs 1-6 (E18 cell or
       their own rare fallback) -- linear in p_hat_0, so only mean(base)
       is needed, not per-trial logging. Also reports R_1's raw marginal
       n_true/n_false (Phase 1 Gate 0's rare-event-vs-binning question,
       contract SS3) as a byproduct of the same run.

Reuses, verbatim: everything run_photonic_corrected_reliability_sweep.py
reuses (predicted_p_chain/p_event_fit, run_chain_boundary_noisy_m0trace,
gen_block/SEED, noiseless_trace_fixed, TRANSITION_PAIR_ID,
load_p_true_lookup) by importing from that module directly, plus one new
function (corrected_base_ex_pair0) that is corrected_p_chain with the
pair-0 term factored out instead of multiplied in.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_compiler_regen_placement_sweep import p_event_fit  # noqa: E402
from run_photonic_corrected_reliability_sweep import (  # noqa: E402
    E18_JSON, M2_BOUNDARIES, SEED, SIGMA_DET, TRANSITION_PAIR_ID,
    TRIAL_OFFSET, load_p_true_lookup, noiseless_trace_fixed,
)
from run_photonic_m0_dynamic_range_sweep import (  # noqa: E402
    run_chain_boundary_noisy_m0trace,
)
from run_photonic_regen_boundary_placement_sweep import gen_block  # noqa: E402
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend  # noqa: E402

N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "300000"))
P_HAT_0_GRID = [round(0.05 * k, 2) for k in range(21)]  # 0.00, 0.05, ..., 1.00
OUT = os.path.join(REPO, "results", "sweeps", "pair0_sensitivity_check.json")


def corrected_base_ex_pair0(m0_trace_noiseless, sigma_det, p_true_lut):
    """corrected_p_chain (contract_photonics_corrected_reliability_model
    SS2.2) with the pair-0 term (i=2, TRANSITION_PAIR_ID[2]=0, always a
    fallback per that contract's SS2.3) factored OUT instead of
    multiplied in -- so mean_corrected(p_hat_0) = p_hat_0 * mean(base)
    for any swept p_hat_0, without per-trial storage."""
    base = p_event_fit(m0_trace_noiseless[0], sigma_det)
    for i in range(2, len(m0_trace_noiseless)):  # skip i=1 (pair_id=0)
        pair_id = TRANSITION_PAIR_ID[i + 1]
        m0 = m0_trace_noiseless[i]
        cell_p = p_true_lut.get((pair_id, m0))
        base *= cell_p if cell_p is not None else p_event_fit(m0, sigma_det)
    return base


def main():
    p_true_lut = load_p_true_lookup(E18_JSON)
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)

    base_sum = 0.0
    empirical_hits = []
    r1_true = r1_false = 0
    trial = 0
    accepted = 0
    while accepted < N_TRIALS:
        rng = trial_rng(master, TRIAL_OFFSET + trial)
        trial += 1
        blk = gen_block(rng, 16)
        if blk is None:
            continue
        m0_noiseless = noiseless_trace_fixed(blk, M2_BOUNDARIES)
        realized = run_chain_boundary_noisy_m0trace(pb, blk, M2_BOUNDARIES, SIGMA_DET, rng)
        base_sum += corrected_base_ex_pair0(m0_noiseless, SIGMA_DET, p_true_lut)
        empirical_hits.append(1 if all(r for _, r in realized) else 0)
        r1_ok = realized[0][1]
        if r1_ok:
            r1_true += 1
        else:
            r1_false += 1
        accepted += 1

    n = len(empirical_hits)
    mean_base = base_sum / n
    empirical_rate = sum(empirical_hits) / n
    se = math.sqrt(empirical_rate * (1 - empirical_rate) / n) if 0 < empirical_rate < 1 else 0.0
    ci_lo, ci_hi = empirical_rate - 1.96 * se, empirical_rate + 1.96 * se

    # mean_corrected(p_hat_0) = p_hat_0 * mean_base is EXACTLY linear, so the
    # viable range is solved in closed form, not read off a discrete grid --
    # a coarse grid can miss a narrow CI window entirely (caught in review:
    # the original 0.05-step grid showed "no viable point" while the exact
    # range [ci_lo/mean_base, ci_hi/mean_base] is real and non-degenerate).
    # The grid below is retained only as an illustrative printout.
    exact_lo = max(0.0, ci_lo / mean_base) if mean_base > 0 else None
    exact_hi = min(1.0, ci_hi / mean_base) if mean_base > 0 else None
    lo, hi = (exact_lo, exact_hi) if (exact_lo is not None and exact_lo <= exact_hi) else (None, None)

    sweep = []
    for p_hat_0 in P_HAT_0_GRID:
        mean_corrected = p_hat_0 * mean_base
        sweep.append({"p_hat_0": p_hat_0, "mean_corrected": mean_corrected,
                       "inside_empirical_ci": ci_lo <= mean_corrected <= ci_hi})

    if lo is not None:
        plausible = not (lo <= 0.02 or hi >= 0.98)  # near-0/near-1 flagged implausible, contract SS2
        verdict = ("Pair-0 hypothesis quantitatively viable" if plausible else
                    "Pair-0 hypothesis technically closes the gap only at an "
                    "implausible p_hat_0 (near 0 or 1) -- treat as NOT viable")
    else:
        verdict = "Pair-0 hypothesis not viable: no p_hat_0 in [0,1] closes the gap"

    print("n=%d  mean_base=%.6f  empirical=%.4f (95%% CI [%.4f, %.4f])"
          % (n, mean_base, empirical_rate, ci_lo, ci_hi))
    print("R_1 marginal: n_true=%d  n_false=%d  (n_min=200 bar: %s)"
          % (r1_true, r1_false, "MET" if r1_false >= 200 else "NOT MET"))
    print("exact viable p_hat_0 range: %s" % (f"[{lo:.4f}, {hi:.4f}]" if lo is not None else "none"))
    print("VERDICT:", verdict)
    for row in sweep:
        print("  p_hat_0=%.2f  mean_corrected=%.4f  inside_CI=%s"
              % (row["p_hat_0"], row["mean_corrected"], row["inside_empirical_ci"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "experiment": "pair0_sensitivity_check",
            "contract": "contract_photonics_pair0_calibration_2026-08-24.md",
            "description": ("Phase 0: is pair-0's missing calibration "
                             "quantitatively capable of explaining the "
                             "corrected-reliability-model's overshoot? "
                             "Sensitivity sweep over a hypothetical flat "
                             "pair-0 correction factor, no new calibration "
                             "data gathered."),
            "seed": SEED, "n_trials": n, "trial_offset": TRIAL_OFFSET,
            "sigma_det": SIGMA_DET, "M_boundaries": M2_BOUNDARIES, "K": 16,
            "e18_source": E18_JSON,
            "mean_base": mean_base,
            "empirical_rate": empirical_rate, "empirical_ci": [ci_lo, ci_hi],
            "r1_marginal": {"n_true": r1_true, "n_false": r1_false,
                             "n_min_200_met": r1_false >= 200},
            "p_hat_0_sweep": sweep,
            "viable_p_hat_0_range_exact": [lo, hi] if lo is not None else None,
            "verdict": verdict,
        }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
