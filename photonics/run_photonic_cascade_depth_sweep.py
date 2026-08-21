#!/usr/bin/env python3
"""run_photonic_cascade_depth_sweep.py — E11 of
contract_photonics_cascade_depth_2026-08-22.md: controlled two-arm test of
whether uncompensated /3 divisions from "exact-thirds" ROTC angles (1,3,4)
explain E9's disproportionate K=8->K=16 detector-noise collapse. Pure
self-rotation chains (no QSUB, no lane-mixing) at K=16, Arm T restricted
to angles {1,3,4}, Arm N to {0,2,5} -- both have identical deterministic
per-trial m=23. Reuses PhotonicQuadrayBackend.run_chain_noisy and
exact_rotc verbatim; the only new code is the block generator (contract
SS4) -- validated against an independent oracle before this sweep runs
(contract SS7 step 0a/0b).

35 det levels (E9's K=16 split grid, reused) x 2 arms = 70 cells.
sigma_phi=sigma_amp=0 (isolated axis, same as E9). PHOTONIC_TRIALS
overrides the per-cell trial count (smoke runs).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_detector_boundary_sweep import DET_LEVELS, DET_LEVELS_K16_EXTRA  # noqa: E402
from run_photonic_envelope_sweep import M_K, BAND, SEED, rint  # noqa: E402
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, exact_rotc  # noqa: E402

DET_LEVELS_ALL = DET_LEVELS_K16_EXTRA + DET_LEVELS
K = 16
ARMS = {"T": (1, 3, 4), "N": (0, 2, 5)}
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "cascade_depth_sweep.json")


def gen_self_rotc_chain(rng, angle_set):
    """QLDI once, then K-1 self-ROTCs (dst=src=0), angle drawn from
    angle_set each step (shuffled, first lattice-safe wins). Returns None
    (rejected) if no angle in the set is lattice-safe at some step, or if
    the final |QR0 component| falls outside BAND."""
    mK = M_K[K]
    v0 = [rint(rng, -mK, mK) for _ in range(4)]
    qr0 = list(v0)
    block = [("QLDI", 0, tuple(v0))]
    for _ in range(K - 1):
        angles = list(angle_set)
        rng.shuffle(angles)
        placed = False
        for ang in angles:
            r = exact_rotc(qr0, ang)
            if r is not None:
                block.append(("ROTC", 0, 0, ang))
                qr0 = list(r)
                placed = True
                break
        if not placed:
            return None
    final = max(abs(c) for c in qr0)
    if not (BAND[0] <= final <= BAND[1]):
        return None
    return block


def cell(arm_name, level, n_trials):
    """One (arm, det_level) cell at fixed K=16: n_trials accepted, arms
    A/B (per-op vs chain REGEN) paired, same convention as E8/E9's cell()."""
    angle_set = ARMS[arm_name]
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    n_ok_a = n_ok_b = 0
    rejected = 0
    first_failed_hist = [0] * K
    total_m_sum = 0.0
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_self_rotc_chain(rng, angle_set)
        if blk is None:
            rejected += 1
            continue
        ok_a, ff, ok_b, tm = pb.run_chain_noisy([blk], 0.0, 0.0, level, rng)
        n_ok_a += 1 if ok_a else 0
        n_ok_b += 1 if ok_b else 0
        if ff:
            first_failed_hist[min(ff, K) - 1] += 1
        total_m_sum += tm
        accepted += 1
    pa = n_ok_a / n_trials
    pb_ = n_ok_b / n_trials
    ci = 1.96 * (max(pa, pb_) * (1 - max(pa, pb_)) / n_trials) ** 0.5
    return {
        "arm": arm_name, "level": level, "K": K,
        "recovery_A": pa, "recovery_B": pb_,
        "ci": ci, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "first_failed_A_hist": first_failed_hist,
        "mean_total_m": total_m_sum / n_trials,
    }


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cell_specs = [(arm, level) for arm in ARMS for level in DET_LEVELS_ALL]
    results = []
    total = len(cell_specs)
    for i, (arm, level) in enumerate(cell_specs, 1):
        c = cell(arm, level, N_TRIALS)
        results.append(c)
        print("  [%3d/%3d] arm=%s det=%9g A=%.4f  B=%.4f  rej=%.3f  m=%.1f"
              % (i, total, arm, level, c["recovery_A"], c["recovery_B"],
                 c["rejection"], c["mean_total_m"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "cascade_depth_sweep",
                "contract": "contract_photonics_cascade_depth_2026-08-22.md",
                "description": ("Controlled thirds-vs-no-thirds self-rotation "
                                 "chain test at K=16, isolating uncompensated "
                                 "/3 divisions as a candidate mechanism for "
                                 "E9's K=8->K=16 detector-noise collapse."),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[K], "deltaT_K": 2.0, "K": K,
                "arms": {name: list(angles) for name, angles in ARMS.items()},
                "det_levels": DET_LEVELS_ALL,
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
