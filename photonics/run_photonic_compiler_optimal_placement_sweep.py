#!/usr/bin/env python3
"""run_photonic_compiler_optimal_placement_sweep.py — E17 Part 2 of
contract_photonics_compiler_optimal_placement_2026-08-23.md: does a
dynamic-programming, whole-chain-optimal REGEN placement -- maximizing
predicted P_chain = prod(P_event(m0_i,sigma)) for a given REGEN-event
cost lambda, rather than E17's per-event worst-case floor -- dominate
E17's greedy placement when actually executed?

Reuses E15's run_chain_boundary_noisy_diag verbatim and E17/E16's fitted
law constants (a=-4.79, beta=3.19) unrefit. New code: the DP itself.
Candidate boundaries are restricted to {0, 2, 3, ..., 16} -- never
between the two initial QLDIs, matching E13-E17's implicit convention
that the first group always contains both.
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
    p_event_fit, A_FIT, BETA_FIT,
)
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    run_chain_boundary_noisy_diag, gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import (  # noqa: E402
    PhotonicQuadrayBackend, exact_qsub, exact_rotc,
)

K = 16
POSITIONS = [0] + list(range(2, K + 1))


def precompute_qr_traj(block):
    """qr[lane] at every position 0..K -- independent of REGEN placement
    (pure algebra, contract SS2)."""
    qr = [[0, 0, 0, 0] for _ in range(13)]
    traj = [[list(row) for row in qr]]
    for op in block:
        if op[0] == "QLDI":
            qr[op[1]] = list(op[2])
        elif op[0] == "QSUB":
            d, sa, sb = op[1], op[2], op[3]
            qr[d] = list(exact_qsub(qr[sa], qr[sb]))
        elif op[0] == "ROTC":
            dst, src, ang = op[1], op[2], op[3]
            qr[dst] = list(exact_rotc(qr[src], ang))
        traj.append([list(row) for row in qr])
    return traj


def segment_m0(block, qr_traj, i, j):
    """m[0] at position j given a REGEN (or start) reset at position i
    (contract SS2). Must track m[1] too: QSUB reads sources from
    {lane0, lane1} and sets m[0] = max(m[sa], m[sb]) + 1 (production
    semantics, test_regen_equivalence.py's _apply_op_field) -- NOT a
    flat +1 from m[0]'s own previous value. A first attempt assumed the
    flat +1 and was caught by the gate-0 cross-check against E17's
    already-verified sequential greedy_place (734-1330 mismatches on
    600 trials) before being trusted for any prediction. ROTC always has
    src=dst=0 (gen_block invariant), so it has no such dependency."""
    m0 = PhotonicQuadrayBackend._load_exp(qr_traj[i][0])
    m1 = PhotonicQuadrayBackend._load_exp(qr_traj[i][1])
    for k in range(i, j):
        op = block[k]
        if op[0] == "QLDI":
            if op[1] == 0:
                m0 = PhotonicQuadrayBackend._load_exp(op[2])
            elif op[1] == 1:
                m1 = PhotonicQuadrayBackend._load_exp(op[2])
        elif op[0] == "QSUB":
            sa, sb = op[2], op[3]
            ma = m0 if sa == 0 else m1
            mb = m0 if sb == 0 else m1
            m0 = max(ma, mb) + 1
        elif op[0] == "ROTC":
            m0 = m0 + 1
    return m0


def optimal_placement(block, qr_traj, sigma_det, lam):
    """DP over POSITIONS (contract SS2): score[j] = max_i (score[i] +
    logp(i,j) - lam). Returns (boundaries, m0_trace, predicted_p_chain)
    -- predicted_p_chain uses the pure logp sum, not the lambda-penalized
    score (lambda only steers path choice)."""
    best_score = {0: 0.0}
    best_logp = {0: 0.0}
    backptr = {}
    for j in POSITIONS[1:]:
        best = None
        for i in POSITIONS:
            if i >= j:
                break
            if i not in best_score:
                continue
            m0 = segment_m0(block, qr_traj, i, j)
            p = max(p_event_fit(m0, sigma_det), 1e-300)
            lp = math.log(p)
            score = best_score[i] + lp - lam
            if best is None or score > best[0]:
                best = (score, best_logp[i] + lp, i, m0)
        best_score[j] = best[0]
        best_logp[j] = best[1]
        backptr[j] = (best[2], best[3])
    boundaries = []
    m0_trace = []
    pos = K
    while pos != 0:
        prev, m0 = backptr[pos]
        boundaries.append(pos)
        m0_trace.append(m0)
        pos = prev
    boundaries.reverse()
    m0_trace.reverse()
    predicted_p_chain = math.exp(best_logp[K])
    return boundaries, m0_trace, predicted_p_chain


def cell(sigma_det, lam, n_trials, K_=K):
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    records = []
    trial = 0
    rejected = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, K_)
        if blk is None:
            rejected += 1
            continue
        qr_traj = precompute_qr_traj(blk)
        boundaries, m0_trace, predicted = optimal_placement(blk, qr_traj, sigma_det, lam)
        ok, _, _, _, _ = run_chain_boundary_noisy_diag(
            pb, blk, boundaries, sigma_det, rng)
        records.append({
            "predicted": predicted, "observed_ok": bool(ok),
            "n_regen": len(boundaries),
        })
        accepted += 1
    n_regen_counts = defaultdict(int)
    for r in records:
        n_regen_counts[r["n_regen"]] += 1
    return {
        "sigma_det": sigma_det, "lam": lam, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "n_regen_histogram": dict(sorted(n_regen_counts.items())),
        "records": records,
    }


SIGMA_DET_POINTS = [1e-6, 1e-5]
LAMBDA_SWEEP = [0, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "10000"))
OUT = os.path.join(REPO, "results", "sweeps", "compiler_optimal_placement_sweep.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cell_specs = [(s, lam) for s in SIGMA_DET_POINTS for lam in LAMBDA_SWEEP]
    results = []
    total = len(cell_specs)
    for i, (sigma_det, lam) in enumerate(cell_specs, 1):
        c = cell(sigma_det, lam, N_TRIALS)
        results.append(c)
        mean_pred = sum(r["predicted"] for r in c["records"]) / len(c["records"])
        mean_obs = sum(r["observed_ok"] for r in c["records"]) / len(c["records"])
        mean_n_regen = sum(r["n_regen"] for r in c["records"]) / len(c["records"])
        print("  [%3d/%3d] sigma=%9g lam=%9g mean_n_regen=%5.2f "
              "mean_predicted=%.4f mean_observed=%.4f rej=%.3f"
              % (i, total, sigma_det, lam, mean_n_regen, mean_pred, mean_obs,
                 c["rejection"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "compiler_optimal_placement_sweep",
                "contract": "contract_photonics_compiler_optimal_placement_2026-08-23.md",
                "description": ("E17 Part 2: does DP whole-chain-optimal "
                                 "REGEN placement dominate E17's greedy "
                                 "placement (2.62 mean events / 1.0 "
                                 "recovery at sigma=1e-6; 6.67 mean events "
                                 "/ 0.9793 recovery at sigma=1e-5) when "
                                 "actually executed?"),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": K,
                "a_fit": A_FIT, "beta_fit": BETA_FIT,
                "sigma_det_points": SIGMA_DET_POINTS, "lambda_sweep": LAMBDA_SWEEP,
                "e17_greedy_reference": {
                    "1e-06": {"mean_n_regen": 2.62, "observed": 1.0000},
                    "1e-05": {"mean_n_regen": 6.67, "observed": 0.9793},
                },
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
