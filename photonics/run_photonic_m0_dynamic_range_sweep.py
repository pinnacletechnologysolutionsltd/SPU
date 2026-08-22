#!/usr/bin/env python3
"""run_photonic_m0_dynamic_range_sweep.py — E16 of
contract_photonics_m0_dynamic_range_2026-08-22.md: is per-REGEN-event
recovery governed by the local scale exponent m[0] (lane 0's shared
scale exponent, the only lane that ever accumulates it -- gen_block never
makes lane 1..12 a combine-op destination) and sigma_det, approximately
INDEPENDENT of which regeneration interval M produced that m0?

run_chain_boundary_noisy_m0trace generalizes E15's
run_chain_boundary_noisy_diag with one additive capture: m[0] immediately
before each boundary's readout. Same four boundary lists as E13/E14/E15
(M=16/8/4/2), run at a SHARED sigma_det grid across all four M so their
group-level (m0, g_ok) data has direct overlap -- m0 is driven mostly by
the random initial QLDI magnitude (band-scaled per K=16), only weakly by
M, so even M=16 occasionally produces low-m0 trials in M=2's range.

M-invariance and out-of-sample prediction (contract SS5/SS6) are
evaluated in a separate analysis script after this sweep produces the
per-cell m0 histograms.
"""
import cmath
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
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

BOUNDARIES = {
    16: [16],
    8: [8, 16],
    4: [4, 8, 12, 16],
    2: [2, 4, 6, 8, 10, 12, 14, 16],
}


def run_chain_boundary_noisy_m0trace(pb, block, boundaries, sigma_det, rng):
    """Identical to run_chain_boundary_noisy_diag (E15), additionally
    capturing m[0] immediately before each boundary's readout. Returns
    [(m0, g_ok), ...] per boundary -- strict additive instrumentation,
    verified bit-identical on g_ok/final-success against the
    unmodified E15 function (contract SS7 gate 0)."""
    boundary_set = set(boundaries)
    if hasattr(rng, "normal"):
        draw = lambda mu, sd: float(rng.normal(mu, sd))
    else:
        draw = lambda mu, sd: rng.gauss(mu, sd)
    fld = [[0j] * 4 for _ in range(13)]
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    angle = 0.0
    nd_last = None
    m0trace = []
    for i, op in enumerate(block, 1):
        if pb._apply_op_field(fld, m, qr, op, angle):
            dp, ap, nd = pb._noise_per_op(0.0, 0.0, sigma_det, draw)
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                rot = cmath.exp(1j * (pb.dphi + dp[ln]))
                fld[lane] = [z * rot * ap[ln] for z in fld[lane]]
            angle += pb.dphi
            nd_last = nd
        if i in boundary_set:
            m0_here = m[0]
            cK = math.cos(angle)
            rec = [[0, 0, 0, 0] for _ in range(13)]
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                for k in range(4):
                    inphase = fld[lane][k].real + (nd_last[ln][k] if nd_last else 0.0)
                    v = (1 << m[lane]) * (inphase / cK) / pb.SCALE
                    rec[lane][k] = max(-(2 ** 31), min(CLAMP, int(round(v))))
            g_ok = rec == qr
            m0trace.append((m0_here, g_ok))
            for lane in range(13):
                le = pb._load_exp(rec[lane])
                f = pb.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            nd_last = None
    return m0trace


def collect(M, level, n_trials, K=16):
    """One (M, det_level) cell: n_trials accepted, m0-binned histogram
    over every REGEN group across all trials."""
    boundaries = BOUNDARIES[M]
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    hist = defaultdict(lambda: [0, 0])  # m0 -> [n_ok, n_total]
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
        for m0, g_ok in run_chain_boundary_noisy_m0trace(pb, blk, boundaries, level, rng):
            hist[m0][1] += 1
            if g_ok:
                hist[m0][0] += 1
        accepted += 1
    return {
        "M": M, "level": level, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "m0_histogram": {str(k): v for k, v in sorted(hist.items())},
    }


DET_LEVELS = [1e-7, 1e-6, 1e-5, 3e-5]
M_VALUES = [16, 8, 4, 2]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "m0_dynamic_range_sweep.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cell_specs = [(M, level) for M in M_VALUES for level in DET_LEVELS]
    results = []
    total = len(cell_specs)
    for i, (M, level) in enumerate(cell_specs, 1):
        c = collect(M, level, N_TRIALS)
        results.append(c)
        n_groups = sum(v[1] for v in c["m0_histogram"].values())
        print("  [%3d/%3d] M=%-2d det=%9g n_groups=%8d rej=%.3f"
              % (i, total, M, level, n_groups, c["rejection"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "m0_dynamic_range_sweep",
                "contract": "contract_photonics_m0_dynamic_range_2026-08-22.md",
                "description": ("E16: is per-REGEN-event recovery governed by "
                                 "the local scale exponent m[0] and sigma_det, "
                                 "approximately independent of M? Shared "
                                 "sigma_det grid across M=16/8/4/2 for direct "
                                 "(m0, sigma) overlap."),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                "M_values": M_VALUES, "det_levels": DET_LEVELS,
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
