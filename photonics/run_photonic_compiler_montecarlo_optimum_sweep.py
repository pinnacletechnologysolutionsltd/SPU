#!/usr/bin/env python3
"""run_photonic_compiler_montecarlo_optimum_sweep.py — E17 Part 3 of
contract_photonics_compiler_montecarlo_optimum_2026-08-23.md: for a
sample of individual blocks, does E17 Part 2's DP schedule achieve the
best -- or CI-tied-for-best -- *actually simulated* recovery among all
other schedules using the same REGEN-event count for that same block?

Uses common random numbers (CRN): a precomputed noise table per
(block_id, repeat), addressable by op position, shared across every
candidate schedule for that block -- NOT a stateful sequential rng,
which would desync between candidates with different REGEN counts.
This requires a new scoring function (score_schedule_addressable),
verified equivalent to E15's run_chain_boundary_noisy_diag via its own
cross-check gate before being trusted (contract SS4).
"""
import cmath
import itertools
import json
import math
import os
import sys
from math import comb

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_compiler_optimal_placement_sweep import (  # noqa: E402
    precompute_qr_traj, optimal_placement, POSITIONS,
)
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

LAMBDA = 0.01
SIGMA_DET_POINTS = [1e-6, 1e-5]
N_BLOCKS = int(os.environ.get("PHOTONIC_MC_BLOCKS", "20"))
N_REPEATS = int(os.environ.get("PHOTONIC_MC_REPEATS", "2000"))
CANDIDATE_CAP = 500
INTERIOR_POSITIONS = POSITIONS[1:-1]
assert len(INTERIOR_POSITIONS) == 14


def build_nd_table(master, block_id, repeat, sigma_det):
    """Addressable noise: one 2-lane x 4-component Gaussian(0,sigma_det)
    vector per op position 1..16, keyed only by (block_id, repeat) --
    identical for every candidate schedule evaluated on this block/repeat
    (contract SS4 common-random-numbers requirement)."""
    key = block_id * 10_000_000 + repeat
    rng = trial_rng(master, key)
    table = []
    for _ in range(16):
        lane0 = [float(rng.normal(0.0, sigma_det)) for _ in range(4)]
        lane1 = [float(rng.normal(0.0, sigma_det)) for _ in range(4)]
        table.append([lane0, lane1])
    return table


def score_schedule_addressable(pb, block, boundaries, nd_table):
    """Mirrors run_chain_boundary_noisy_diag for sigma_phi=sigma_amp=0
    (dp=0, ap=1 always -- those draws are pointless and skipped), but
    pulls detector noise from nd_table[op_position-1] instead of a
    stateful rng. Returns (all_ok, qr0)."""
    boundary_set = set(boundaries)
    fld = [[0j] * 4 for _ in range(13)]
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    angle = 0.0
    nd_last = None
    all_ok = True
    for i, op in enumerate(block, 1):
        if pb._apply_op_field(fld, m, qr, op, angle):
            rot = cmath.exp(1j * pb.dphi)
            for lane in range(13):
                fld[lane] = [z * rot for z in fld[lane]]
            angle += pb.dphi
            nd_last = nd_table[i - 1]
        if i in boundary_set:
            cK = math.cos(angle)
            rec = [[0, 0, 0, 0] for _ in range(13)]
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                for k in range(4):
                    inphase = fld[lane][k].real + (nd_last[ln][k] if nd_last else 0.0)
                    v = (1 << m[lane]) * (inphase / cK) / pb.SCALE
                    rec[lane][k] = max(-(2 ** 31), min(CLAMP, int(round(v))))
            if rec != qr:
                all_ok = False
            for lane in range(13):
                le = pb._load_exp(rec[lane])
                f = pb.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            nd_last = None
    return all_ok, qr[0]


def same_n_schedules(n_boundaries, interior_positions, cap, sample_rng):
    """Enumerate (or sample, per cap) boundary sets of size n_boundaries
    ending at 16. Returns (schedules, enumeration_mode, n_total)."""
    r = n_boundaries - 1
    if r == 0:
        return [[16]], "full", 1
    n_total = comb(len(interior_positions), r)
    if n_total <= cap:
        combos = itertools.combinations(interior_positions, r)
        schedules = [sorted(c) + [16] for c in combos]
        return schedules, "full", n_total
    seen = set()
    schedules = []
    attempts = 0
    while len(schedules) < cap and attempts < cap * 50:
        combo = tuple(sorted(sample_rng.choice(
            interior_positions, size=r, replace=False).tolist()))
        attempts += 1
        if combo not in seen:
            seen.add(combo)
            schedules.append(list(combo) + [16])
    return schedules, "sampled", n_total


def paired_stats(outcomes_j, outcomes_d):
    d = np.array(outcomes_j, dtype=float) - np.array(outcomes_d, dtype=float)
    mean_d = float(np.mean(d))
    se_d = float(np.std(d, ddof=1) / math.sqrt(len(d))) if len(d) > 1 else 0.0
    ci_lo, ci_hi = mean_d - 1.96 * se_d, mean_d + 1.96 * se_d
    return mean_d, se_d, ci_lo, ci_hi


def evaluate_block(block, block_id, sigma_det, lam, master, n_repeats, cap):
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    qr_traj = precompute_qr_traj(block)
    dp_boundaries, dp_m0_trace, dp_predicted = optimal_placement(
        block, qr_traj, sigma_det, lam)
    n_boundaries = len(dp_boundaries)

    sample_rng = np.random.default_rng(1_000_000_000 + block_id)
    schedules, enum_mode, n_total = same_n_schedules(
        n_boundaries, INTERIOR_POSITIONS, cap, sample_rng)
    if dp_boundaries not in schedules:
        schedules = [dp_boundaries] + schedules
    n_evaluated = len(schedules)

    nd_tables = [build_nd_table(master, block_id, r, sigma_det)
                 for r in range(n_repeats)]

    dp_outcomes = [
        1 if score_schedule_addressable(pb, block, dp_boundaries, t)[0] else 0
        for t in nd_tables
    ]
    dp_recovery = sum(dp_outcomes) / n_repeats

    candidates = []
    for sched in schedules:
        if sched == dp_boundaries:
            outcomes = dp_outcomes
        else:
            outcomes = [
                1 if score_schedule_addressable(pb, block, sched, t)[0] else 0
                for t in nd_tables
            ]
        recovery = sum(outcomes) / n_repeats
        mean_d, se_d, ci_lo, ci_hi = paired_stats(outcomes, dp_outcomes)
        candidates.append({
            "boundaries": sched, "recovery": recovery,
            "mean_d_vs_dp": mean_d, "se_d_vs_dp": se_d,
            "ci_lo": ci_lo, "ci_hi": ci_hi,
            "beats_dp": ci_lo > 0, "loses_to_dp": ci_hi < 0,
        })

    ranked = sorted(candidates, key=lambda c: -c["recovery"])
    rank_among_evaluated = next(
        i + 1 for i, c in enumerate(ranked) if c["boundaries"] == dp_boundaries)
    best = ranked[0]
    best_beats_dp_ci = best["boundaries"] != dp_boundaries and best["ci_lo"] > 0

    return {
        "block_id": block_id, "sigma_det": sigma_det, "lam": lam,
        "n_boundaries": n_boundaries, "dp_boundaries": dp_boundaries,
        "dp_predicted": dp_predicted, "dp_recovery_mc": dp_recovery,
        "enumeration_mode": enum_mode, "n_total_schedules": n_total,
        "n_evaluated_schedules": n_evaluated,
        "rank_among_evaluated": rank_among_evaluated,
        "best_boundaries": best["boundaries"], "best_recovery_mc": best["recovery"],
        "best_beats_dp_ci": best_beats_dp_ci,
        "best_mean_d_vs_dp": best["mean_d_vs_dp"],
        "best_ci_lo": best["ci_lo"], "best_ci_hi": best["ci_hi"],
        "dp_outcomes": dp_outcomes, "best_outcomes":
            dp_outcomes if best["boundaries"] == dp_boundaries else [
                1 if score_schedule_addressable(pb, block, best["boundaries"], t)[0] else 0
                for t in nd_tables],
        "n_repeats": n_repeats,
    }


OUT = os.path.join(REPO, "results", "sweeps", "compiler_montecarlo_optimum_sweep.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    master = make_master_rng(SEED)
    results = []
    total = len(SIGMA_DET_POINTS) * N_BLOCKS
    done = 0
    for sigma_det in SIGMA_DET_POINTS:
        trial = 0
        block_id = 0
        accepted = 0
        while accepted < N_BLOCKS:
            rng = trial_rng(master, trial)
            trial += 1
            blk = gen_block(rng, 16)
            if blk is None:
                continue
            r = evaluate_block(blk, accepted, sigma_det, LAMBDA, master,
                                N_REPEATS, CANDIDATE_CAP)
            results.append(r)
            done += 1
            print("  [%3d/%3d] sigma=%9g block=%2d n_boundaries=%d "
                  "n_evaluated=%4d (%s) rank=%3d dp_mc=%.4f best_mc=%.4f "
                  "best_beats_dp=%s"
                  % (done, total, sigma_det, accepted, r["n_boundaries"],
                     r["n_evaluated_schedules"], r["enumeration_mode"],
                     r["rank_among_evaluated"], r["dp_recovery_mc"],
                     r["best_recovery_mc"], r["best_beats_dp_ci"]), flush=True)
            with open(OUT, "w") as f:
                json.dump({
                    "experiment": "compiler_montecarlo_optimum_sweep",
                    "contract": "contract_photonics_compiler_montecarlo_optimum_2026-08-23.md",
                    "description": ("E17 Part 3: does E17 Part 2's DP schedule "
                                     "achieve the best actually-simulated "
                                     "recovery among all other same-event-count "
                                     "schedules for that block, using common "
                                     "random numbers for a paired comparison?"),
                    "seed": SEED, "n_blocks": N_BLOCKS, "n_repeats": N_REPEATS,
                    "candidate_cap": CANDIDATE_CAP,
                    "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                    "lambda": LAMBDA, "sigma_det_points": SIGMA_DET_POINTS,
                    "blocks": results,
                }, f, indent=1)
            accepted += 1
    print("wrote", OUT)


if __name__ == "__main__":
    main()
