#!/usr/bin/env python3
"""run_photonic_detector_boundary_sweep.py — E9 of
contract_photonics_detector_boundary_2026-08-21.md: dense detector-only
sweep resolving the 99.9/99/95% crossings for K in {1,2,4,8,16}, plus the
R_K = sigma*_det(K) / sigma_det,pred(K) scaling-law consistency test (see
contract SS2.1). Reuses cell()/gen_block()/PhotonicQuadrayBackend from
run_photonic_envelope_sweep.py verbatim -- no new physics, no reimplementation.

K in {1,2,4,8} use a 23-point log-spaced grid (1e-7-5e-4); K=16 gets a
36th-point extension below the grid floor (contract SS3, revised 2026-08-21
after the SS8 smoke pass found K=16's crossing below 1e-7). 127 cells total.
sigma_phi=0, sigma_amp=0 (isolated axis, locked per SS2 of the contract).
PHOTONIC_TRIALS overrides the per-cell trial count (smoke runs).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from run_photonic_envelope_sweep import cell, M_K, BAND, SEED, KS  # noqa: E402

# ── frozen grid (contract SS3): log-spaced, ~5 points/decade, spans the two
# E8 anchors (K=1 ~1.96e-4, K=16 ~5.8e-7) with margin on both ends. ──
DET_LEVELS = [
    1e-7, 1.5e-7, 2e-7, 3e-7, 5e-7, 7e-7,
    1e-6, 1.5e-6, 2e-6, 3e-6, 5e-6, 7e-6,
    1e-5, 1.5e-5, 2e-5, 3e-5, 5e-5, 7e-5,
    1e-4, 1.5e-4, 2e-4, 3e-4, 5e-4,
]
# K=16 only: below the main grid's floor, no overlap/duplication (SS3 revision).
DET_LEVELS_K16_EXTRA = [
    1e-9, 1.5e-9, 2e-9, 3e-9, 5e-9, 7e-9,
    1e-8, 1.5e-8, 2e-8, 3e-8, 5e-8, 7e-8,
]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "detector_boundary_sweep.json")


def levels_for(K):
    return DET_LEVELS_K16_EXTRA + DET_LEVELS if K == 16 else DET_LEVELS


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cell_specs = [(level, K) for K in KS for level in levels_for(K)]
    results = []
    total = len(cell_specs)
    for i, (level, K) in enumerate(cell_specs, 1):
        c = cell("det", level, K, N_TRIALS)
        results.append(c)
        print("  [%3d/%3d] det=%9g K=%-2d  A=%.4f  B=%.4f  rej=%.3f  m=%.1f"
              % (i, total, level, K, c["recovery_A"], c["recovery_B"],
                 c["rejection"], c["mean_total_m"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "detector_boundary_sweep",
                "contract": "contract_photonics_detector_boundary_2026-08-21.md",
                "description": ("Dense detector-only sweep (phi=0, amp=0) "
                                 "resolving 99.9/99/95% crossings per K, for "
                                 "the R_K scaling-law consistency test "
                                 "(contract SS2.1). K=16 uses a split grid "
                                 "extending below the main floor (SS3)."),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K": M_K, "deltaT_K": 2.0,
                "det_levels": DET_LEVELS,
                "det_levels_k16_extra": DET_LEVELS_K16_EXTRA,
                "K_values": KS,
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
