#!/usr/bin/env python3
"""run_photonic_compiler_regen_placement_sweep.py — E17 of
contract_photonics_compiler_regen_placement_2026-08-23.md: does greedy,
threshold-based REGEN placement -- inserting a boundary whenever the
noiseless m0 trajectory reaches m0_safe(sigma_det, P_target), computed
entirely at "compile time" -- produce actual (noisy) recovery rates that
match what E16's own fitted law predicts for that specific placement?

Reuses E15's run_chain_boundary_noisy_diag verbatim (it already accepts
an arbitrary boundary list) and E16's fitted law constants (a=-4.79,
beta=3.19, contract_photonics_m0_dynamic_range_2026-08-22.md SS10) as
frozen, not refit. The only new logic is the greedy placement algorithm
itself (contract SS4).
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

from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    run_chain_boundary_noisy_diag, gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import (  # noqa: E402
    PhotonicQuadrayBackend, exact_qsub, exact_rotc,
)

A_FIT = -4.79
BETA_FIT = 3.19
P_TARGET = 0.999


def m0_safe(sigma_det, p_target=P_TARGET, a=A_FIT, beta=BETA_FIT):
    """Per-event safe threshold (design rule doc SS2 formula)."""
    return a - math.log2(sigma_det) - math.log(p_target / (1 - p_target)) / beta


def p_event_fit(m0, sigma_det, a=A_FIT, beta=BETA_FIT):
    """E16's fitted per-event recovery law, frozen constants."""
    z = beta * (a - math.log2(sigma_det) - m0)
    if z > 700:
        return 1.0
    if z < -700:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def predicted_p_chain(m0_trace, sigma_det):
    p = 1.0
    for m0 in m0_trace:
        p *= p_event_fit(m0, sigma_det)
    return p


def greedy_place(block, m0_threshold):
    """Walks the block using exact noiseless bookkeeping (mirrors E15/E16's
    noiseless-trajectory logic); places a REGEN boundary immediately after
    any mirrored op that leaves m[0] >= m0_threshold, and always at the
    block's own end. Returns (boundaries, m0_trace): boundaries is a
    strictly increasing 1-indexed list ending at len(block); m0_trace[i]
    is the noiseless m0 at boundaries[i] (contract SS4)."""
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    boundaries = []
    m0_trace = []
    n = len(block)
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
        if m[0] >= m0_threshold or i == n:
            boundaries.append(i)
            m0_trace.append(m[0])
            for lane in range(13):
                m[lane] = PhotonicQuadrayBackend._load_exp(qr[lane])
    return boundaries, m0_trace


def cell(sigma_det, n_trials, K=16):
    threshold = m0_safe(sigma_det)
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    records = []
    trial = 0
    rejected = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, K)
        if blk is None:
            rejected += 1
            continue
        boundaries, m0_trace = greedy_place(blk, threshold)
        predicted = predicted_p_chain(m0_trace, sigma_det)
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
        "sigma_det": sigma_det, "m0_threshold": threshold, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "n_regen_histogram": dict(sorted(n_regen_counts.items())),
        "records": records,
    }


SIGMA_DET_POINTS = [1e-6, 1e-5, 1e-4]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "compiler_regen_placement_sweep.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    results = []
    total = len(SIGMA_DET_POINTS)
    for i, sigma_det in enumerate(SIGMA_DET_POINTS, 1):
        c = cell(sigma_det, N_TRIALS)
        results.append(c)
        mean_pred = sum(r["predicted"] for r in c["records"]) / len(c["records"])
        mean_obs = sum(r["observed_ok"] for r in c["records"]) / len(c["records"])
        print("  [%d/%d] sigma_det=%9g m0_safe=%6.2f n_regen_hist=%s "
              "mean_predicted=%.4f mean_observed=%.4f rej=%.3f"
              % (i, total, sigma_det, c["m0_threshold"], c["n_regen_histogram"],
                 mean_pred, mean_obs, c["rejection"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "compiler_regen_placement_sweep",
                "contract": "contract_photonics_compiler_regen_placement_2026-08-23.md",
                "description": ("E17: does greedy, threshold-based REGEN "
                                 "placement (insert whenever the noiseless "
                                 "m0 trajectory reaches m0_safe) produce "
                                 "actual recovery rates matching E16's own "
                                 "fitted law's predictions for that "
                                 "placement?"),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                "p_target": P_TARGET, "a_fit": A_FIT, "beta_fit": BETA_FIT,
                "sigma_det_points": SIGMA_DET_POINTS,
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
