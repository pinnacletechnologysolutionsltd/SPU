#!/usr/bin/env python3
"""run_photonic_corrected_reliability_sweep.py --
contract_photonics_corrected_reliability_model_2026-08-24.md: does a
first-order correction using E18's frozen R_i->R_{i+1} dependence predict
real whole-chain ("all 8 groups recover exactly") Monte Carlo outcomes
better than the existing product-of-marginals estimator
(predicted_p_chain), at the same locked operating point E18 was
calibrated at (M=2, K=16, sigma_det=3e-5)?

Reuses, verbatim: predicted_p_chain/p_event_fit (E16's fitted law,
run_photonic_compiler_regen_placement_sweep.py), run_chain_boundary_
noisy_m0trace (E16, run_photonic_m0_dynamic_range_sweep.py), gen_block/
SEED (E13 chain). New code (contract SS4): noiseless_trace_fixed (mirrors
greedy_place's op-handling bookkeeping against a fixed M=2 boundary list
instead of a dynamic threshold) and corrected_p_chain (contract SS2.2),
read-only against E18's frozen cell table.
"""
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_compiler_regen_placement_sweep import (  # noqa: E402
    A_FIT, BETA_FIT, p_event_fit, predicted_p_chain,
)
from run_photonic_m0_dynamic_range_sweep import (  # noqa: E402
    run_chain_boundary_noisy_m0trace,
)
from run_photonic_regen_boundary_placement_sweep import gen_block, SEED  # noqa: E402
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import (  # noqa: E402
    PhotonicQuadrayBackend, exact_qsub, exact_rotc,
)

M2_BOUNDARIES = [2, 4, 6, 8, 10, 12, 14, 16]
SIGMA_DET = 3e-5  # locked, E18's operating point (contract SS3)
E18_JSON = os.path.join(
    REPO, "results", "sweeps",
    "correlation_mechanism_sweep_frozen_v1_2026-08-23.json")
TRIAL_OFFSET = 300_000_000  # fresh namespace, disjoint from E18 (contract SS3)
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "300000"))
OUT = os.path.join(REPO, "results", "sweeps", "corrected_reliability_sweep.json")


def load_p_true_lookup(path):
    """(pair_id, m0_bin) -> P(R_i=True | R_{i-1}=True, m0_bin), read-only
    from E18's frozen cell table. All 30 frozen cells are at exact-integer
    resolution (E18 SS10); this driver only ever looks up exact integers,
    consistent with that -- raises if that assumption ever stops holding."""
    with open(path) as f:
        d = json.load(f)
    lut = {}
    for c in d["analysis"]["cells"]:
        if c["resolution"] != "exact":
            raise RuntimeError("unexpected non-exact cell in frozen E18 data: %r" % c)
        lut[(c["pair_id"], c["bin"])] = c["p_true"]
    return lut


def noiseless_trace_fixed(block, boundaries):
    """Noiseless m0 trajectory at a fixed boundary list -- identical
    op-handling bookkeeping to greedy_place
    (run_photonic_compiler_regen_placement_sweep.py), parametrized by a
    fixed boundary set instead of a dynamic m0_threshold."""
    boundary_set = set(boundaries)
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    trace = []
    for i, op in enumerate(block, 1):
        if op[0] == "QLDI":
            le = PhotonicQuadrayBackend._load_exp(op[2])
            m[op[1]] = le
            qr[op[1]] = list(op[2])
        elif op[0] == "QSUB":
            d, sa, sb = op[1], op[2], op[3]
            mc = max(m[sa], m[sb])
            m[d] = mc + 1
            qr[d] = list(exact_qsub(qr[sa], qr[sb]))
        elif op[0] == "ROTC":
            dst, src, ang = op[1], op[2], op[3]
            m[dst] = m[src] + 1
            qr[dst] = list(exact_rotc(qr[src], ang))
        if i in boundary_set:
            trace.append(m[0])
            for lane in range(13):
                m[lane] = PhotonicQuadrayBackend._load_exp(qr[lane])
    return trace


# Contract SS2.2 amendment 1 (Halt-and-Flag round 2): transition i-1->i
# (i=2..8) maps to E18 pair_id=i-2, locked and asserted here rather than
# left implicit -- E18's own convention (SS10: "pair=1 (groups 2->3)",
# "pair 0 (groups 1->2)") is pair_id p <=> groups (p+1)->(p+2).
TRANSITION_PAIR_ID = {i: i - 2 for i in range(2, 9)}
assert TRANSITION_PAIR_ID == {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}


def corrected_p_chain(m0_trace_noiseless, sigma_det, p_true_lut, coverage):
    """Contract SS2.2: still-clean-branch estimator. m0_trace_noiseless[0]
    is group 1 (no predecessor -- unmodified marginal law); for i=2..8,
    TRANSITION_PAIR_ID[i] indexes E18's frozen (group i-1 -> group i) cell
    table, falling back to the marginal law where no cell exists (SS2.3 --
    pair 0 always falls back; a known, reported coverage gap, not a bug).
    `coverage[pair_id]` is mutated in place: [n_used_e18_cell, n_fallback]
    (amendment 2 -- quantify the partial-correction claim, not just assert
    it)."""
    p = p_event_fit(m0_trace_noiseless[0], sigma_det)
    for i in range(1, len(m0_trace_noiseless)):
        pair_id = TRANSITION_PAIR_ID[i + 1]
        m0 = m0_trace_noiseless[i]
        cell_p = p_true_lut.get((pair_id, m0))
        if cell_p is None:
            coverage[pair_id][1] += 1
            p *= p_event_fit(m0, sigma_det)
        else:
            coverage[pair_id][0] += 1
            p *= cell_p
    return p


def main():
    p_true_lut = load_p_true_lookup(E18_JSON)
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)

    naive_vals, corrected_vals, empirical_hits = [], [], []
    coverage = defaultdict(lambda: [0, 0])  # pair_id -> [n_used_e18_cell, n_fallback]
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
        naive_vals.append(predicted_p_chain(m0_noiseless, SIGMA_DET))
        corrected_vals.append(corrected_p_chain(m0_noiseless, SIGMA_DET, p_true_lut, coverage))
        empirical_hits.append(1 if all(r for _, r in realized) else 0)
        accepted += 1

    n = len(empirical_hits)
    mean_naive = sum(naive_vals) / n
    mean_corrected = sum(corrected_vals) / n
    empirical_rate = sum(empirical_hits) / n
    se = math.sqrt(empirical_rate * (1 - empirical_rate) / n) if 0 < empirical_rate < 1 else 0.0
    ci_lo, ci_hi = empirical_rate - 1.96 * se, empirical_rate + 1.96 * se

    gap_naive = abs(mean_naive - empirical_rate)
    gap_corrected = abs(mean_corrected - empirical_rate)
    if mean_corrected > empirical_rate + 1.96 * se:
        tier = "Model actively wrong (over-corrected, non-conservative)"
    elif gap_naive == 0:
        tier = "Naive already exact (degenerate)"
    elif gap_corrected <= 0.5 * gap_naive:
        tier = "Model closes the gap (materially)"
    elif gap_corrected < gap_naive:
        tier = "Model partially helps"
    else:
        tier = "Model does not help"

    ratio = (gap_corrected / gap_naive) if gap_naive else float("nan")
    coverage_report = {
        str(pair_id): {"n_used_e18_cell": used, "n_fallback": fb,
                        "frac_used": used / (used + fb) if (used + fb) else None}
        for pair_id, (used, fb) in sorted(coverage.items())
    }
    total_used = sum(used for used, _ in coverage.values())
    total_fallback = sum(fb for _, fb in coverage.values())

    print("n=%d  mean_naive=%.4f  mean_corrected=%.4f  empirical=%.4f (95%% CI [%.4f, %.4f])"
          % (n, mean_naive, mean_corrected, empirical_rate, ci_lo, ci_hi))
    print("gap_naive=%.4f  gap_corrected=%.4f  ratio=%.3f  tier=%s"
          % (gap_naive, gap_corrected, ratio, tier))
    print("transition coverage: %d/%d (%.1f%%) of the 7*%d transitions used an "
          "E18 cell; rest fell back to the marginal law"
          % (total_used, total_used + total_fallback,
             100.0 * total_used / (total_used + total_fallback), n))
    for pair_id in range(7):
        used, fb = coverage.get(pair_id, [0, 0])
        print("  pair_id=%d: used=%d fallback=%d" % (pair_id, used, fb))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "experiment": "corrected_reliability_sweep",
            "contract": "contract_photonics_corrected_reliability_model_2026-08-24.md",
            "description": ("Does E18's frozen R_i->R_{i+1} dependence, folded "
                             "into a still-clean-branch corrected estimator, "
                             "predict real whole-chain recovery better than "
                             "the naive product-of-marginals model, at "
                             "M=2/K=16/sigma_det=3e-5?"),
            "seed": SEED, "n_trials": n, "trial_offset": TRIAL_OFFSET,
            "sigma_det": SIGMA_DET, "M_boundaries": M2_BOUNDARIES, "K": 16,
            "a_fit": A_FIT, "beta_fit": BETA_FIT,
            "e18_source": E18_JSON,
            "transition_coverage": coverage_report,
            "n_all_succeed": sum(empirical_hits),
            "mean_naive": mean_naive, "mean_corrected": mean_corrected,
            "empirical_rate": empirical_rate, "empirical_ci": [ci_lo, ci_hi],
            "gap_naive": gap_naive, "gap_corrected": gap_corrected,
            "gap_ratio": ratio, "tier": tier,
        }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
