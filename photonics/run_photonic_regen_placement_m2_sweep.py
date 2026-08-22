#!/usr/bin/env python3
"""run_photonic_regen_placement_m2_sweep.py — E14 of
contract_photonics_regen_placement_m2_2026-08-22.md: does the M=4->M=2
improvement continue E13's accelerating trend, saturate, or reverse --
because M=2's first REGEN boundary occurs right after the two QLDIs,
before any QSUB/ROTC computation?

Reuses independent_oracle and cell (the plain recovery-curve function)
from run_photonic_regen_placement_sweep.py (E13) verbatim -- only new
code here is the lane-attribution instrumentation (contract SS4b,
APPROVED) needed to make outcome D's two candidate causes empirically
distinguishable, and the per-group diagnostic needed for the strict
noiseless gate (SS4a).

M=16/8/4 are E13's frozen curve, NOT rerun here (contract SS3).
"""
import cmath
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_regen_placement_sweep import (  # noqa: E402
    independent_oracle, cell, gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402


def run_chain_periodic_noisy_diag(pb, block, M, sigma_det, rng):
    """Like E13's run_chain_periodic_noisy, but with per-group and
    per-lane diagnostics (contract SS4a/SS4b) -- additive instrumentation
    only; must produce an identical all_ok/final_qr0 to the unmodified
    function (verified, contract SS7 gate 0c). Returns (all_ok,
    lane0_ever_failed, lane1_ever_failed, group_results, final_qr0);
    group_results is [(group_ok, lane0_ok, lane1_ok), ...] per REGEN
    boundary, for the strict per-group noiseless check."""
    if hasattr(rng, "normal"):
        draw = lambda mu, sd: float(rng.normal(mu, sd))
    else:
        draw = lambda mu, sd: rng.gauss(mu, sd)
    fld = [[0j] * 4 for _ in range(13)]
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    angle = 0.0
    all_ok = True
    lane0_failed = False
    lane1_failed = False
    group_results = []
    nd_last = None
    for i, op in enumerate(block, 1):
        if pb._apply_op_field(fld, m, qr, op, angle):
            dp, ap, nd = pb._noise_per_op(0.0, 0.0, sigma_det, draw)
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                rot = cmath.exp(1j * (pb.dphi + dp[ln]))
                fld[lane] = [z * rot * ap[ln] for z in fld[lane]]
            angle += pb.dphi
            nd_last = nd
        if i % M == 0:
            cK = math.cos(angle)
            rec = [[0, 0, 0, 0] for _ in range(13)]
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                for k in range(4):
                    inphase = fld[lane][k].real + (nd_last[ln][k] if nd_last else 0.0)
                    v = (1 << m[lane]) * (inphase / cK) / pb.SCALE
                    rec[lane][k] = max(-(2 ** 31), min(CLAMP, int(round(v))))
            g_ok = rec == qr
            l0_ok = rec[0] == qr[0]
            l1_ok = rec[1] == qr[1]
            group_results.append((g_ok, l0_ok, l1_ok))
            if not g_ok:
                all_ok = False
            if not l0_ok:
                lane0_failed = True
            if not l1_ok:
                lane1_failed = True
            for lane in range(13):
                le = pb._load_exp(rec[lane])
                f = pb.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            nd_last = None
    return all_ok, lane0_failed, lane1_failed, group_results, qr[0]


def cell_lane_attrib(M, level, n_trials, K=16):
    """Lane-attribution breakdown for FAILED trials (contract SS4b)."""
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    n_ok = 0
    n_fail_lane0_only = n_fail_lane1_only = n_fail_both = n_fail_other = 0
    rejected = 0
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, K)
        if blk is None:
            rejected += 1
            continue
        ok, l0f, l1f, _, _ = run_chain_periodic_noisy_diag(pb, blk, M, level, rng)
        if ok:
            n_ok += 1
        elif l0f and l1f:
            n_fail_both += 1
        elif l0f:
            n_fail_lane0_only += 1
        elif l1f:
            n_fail_lane1_only += 1
        else:
            n_fail_other += 1
        accepted += 1
    return {
        "M": M, "level": level, "n_trials": n_trials, "recovery": n_ok / n_trials,
        "n_fail": n_trials - n_ok,
        "fail_lane0_only": n_fail_lane0_only, "fail_lane1_only": n_fail_lane1_only,
        "fail_both": n_fail_both, "fail_other": n_fail_other,
        "rejection": rejected / (rejected + n_trials),
    }


# Locked from the smoke pass (contract SS3) -- dense around the observed
# transition (~4-5e-6), wide margin on both sides. Not moved after this.
DET_LEVELS = [1e-7, 3e-7, 1e-6, 2e-6, 3e-6, 4e-6, 5e-6, 7e-6,
              1e-5, 1.5e-5, 2e-5, 3e-5, 5e-5, 1e-4, 3e-4, 1e-3]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "regen_placement_m2_sweep.json")


def main():
    if DET_LEVELS is None:
        raise RuntimeError("DET_LEVELS must be locked from the smoke pass first")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    results = []
    total = len(DET_LEVELS)
    for i, level in enumerate(DET_LEVELS, 1):
        c = cell(2, level, N_TRIALS)
        results.append(c)
        print("  [%3d/%3d] M=2 det=%9g recovery=%.4f rej=%.3f"
              % (i, total, level, c["recovery"], c["rejection"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "regen_placement_m2_sweep",
                "contract": "contract_photonics_regen_placement_m2_2026-08-22.md",
                "description": ("M=2 extension of E13's regen-frequency sweep: "
                                 "does the accelerating trend continue toward "
                                 "K=8, saturate, or reverse at the QLDI-only "
                                 "first boundary?"),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                "M": 2, "det_levels": DET_LEVELS,
                "e13_frozen_reference": {
                    "M4_geomean": 1.732e-6, "M8_geomean": 5.477e-8,
                    "M16_geomean": 5.477e-9,
                },
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
