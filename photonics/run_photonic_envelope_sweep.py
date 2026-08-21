#!/usr/bin/env python3
"""run_photonic_envelope_sweep.py — deliverable 2 of
contract_photonics_backend_2026-08-20.md: the DECLARED REGENERATION ENVELOPE.

For the PhotonicQuadrayBackend under the frozen per-op noise sources
(differential phase, amplitude, detector — E6/E7 semantics), the per-K
recovery budget and the K* regeneration-frequency phase diagram:

    P_A(K, sigma) — per-op REGEN (regenerate every op)
    P_B(K, sigma) — chain (one conditioned REGEN per block)

60 cells: 3 axes x 4 levels x K in {1,2,4,8,16}; 30,000 accepted trials/cell;
output band [1000, 30000] on the block's max |QR0 component|; per-K operand
scaling m_K = {1:100, 2:25, 4:9, 8:4, 16:2}; seed 13. Arms A and B are
evaluated from the SAME per-trial draw stream (paired draws). Canonical
incremental JSON output (frozen discipline: run twice, bit-identical).
"""
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from test_regen_equivalence import (  # noqa: E402
    PhotonicQuadrayBackend, chain_oracle, exact_rotc, exact_qsub, FGH,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402

# ── frozen cell grid (E6/E7 levels) ──
PHI_LEVELS = [0.0, 0.25, 0.5, 1.0]          # degrees (lane differential phase)
AMP_LEVELS = [0.0, 1e-5, 2.5e-5, 5e-5]      # relative amplitude error
DET_LEVELS = [0.0, 1e-4, 3e-4, 1e-3]        # detector noise
KS = [1, 2, 4, 8, 16]
M_K = {1: 2000, 2: 2000, 4: 2000, 8: 2000, 16: 2000}  # Quadray operands (sub-geometric growth; band rejection)
BAND = (1000, 30000)
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
SEED = 13
OUT = os.path.join(REPO, "results", "sweeps", "photonic_envelope.json")

DEG = 3.141592653589793 / 180.0


def rint(rng, lo, hi):
    if hasattr(rng, "integers"):
        return int(rng.integers(lo, hi + 1))
    return rng.randint(lo, hi + 1)


def gen_block(rng, K):
    """One band-targeted Quadray block: QLDI QR0/QR1 (m_K-scaled) + K-2
    lattice-safe transforms. Returns the block and the exact per-op states,
    or None if the final max |QR0 component| is outside the band."""
    mK = M_K[K]
    v0 = [rint(rng, -mK, mK) for _ in range(4)]
    qr = [[0, 0, 0, 0] for _ in range(13)]
    qr[0] = list(v0)
    block = [("QLDI", 0, tuple(v0))]
    if K >= 2:
        v1 = [rint(rng, -mK, mK) for _ in range(4)]
        qr[1] = list(v1)
        block.append(("QLDI", 1, tuple(v1)))
    for _ in range(max(0, K - 2)):
        if rng.random() < 0.5:
            angles = list(range(6))
            rng.shuffle(angles)
            placed = False
            for ang in angles:
                r = exact_rotc(qr[0], ang)
                if r is not None:
                    block.append(("ROTC", 0, 0, ang))
                    qr[0] = list(r)
                    placed = True
                    break
            if not placed:
                sa, sb = rint(rng, 0, 1), rint(rng, 0, 1)
                block.append(("QSUB", 0, sa, sb))
                qr[0] = list(exact_qsub(qr[sa], qr[sb]))
        else:
            sa, sb = rint(rng, 0, 1), rint(rng, 0, 1)
            block.append(("QSUB", 0, sa, sb))
            qr[0] = list(exact_qsub(qr[sa], qr[sb]))
    final = max(abs(c) for c in qr[0])
    if not (BAND[0] <= final <= BAND[1]):
        return None
    return block


def cell(axis, level, K, n_trials):
    """One (axis, level, K) cell: 30,000 accepted trials, arms A/B paired."""
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    if axis == "phi":
        sphi, samp, sdet = level * DEG, 0.0, 0.0
    elif axis == "amp":
        sphi, samp, sdet = 0.0, level, 0.0
    else:
        sphi, samp, sdet = 0.0, 0.0, level
    n_ok_a = n_ok_b = 0
    rejected = 0
    first_failed_hist = [0] * (K + 1)
    total_m_sum = 0.0
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, K)
        if blk is None:
            rejected += 1
            continue
        ok_a, ff, ok_b, tm = pb.run_chain_noisy([blk], sphi, samp, sdet, rng)
        n_ok_a += 1 if ok_a else 0
        n_ok_b += 1 if ok_b else 0
        if ff:
            first_failed_hist[min(ff, K)] += 1
        total_m_sum += tm
        accepted += 1
    pa = n_ok_a / n_trials
    pb_ = n_ok_b / n_trials
    ci = 1.96 * (max(pa, pb_) * (1 - max(pa, pb_)) / n_trials) ** 0.5
    return {
        "axis": axis, "level": level, "K": K,
        "recovery_A": pa, "recovery_B": pb_,
        "ci": ci, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "first_failed_A_hist": first_failed_hist,
        "mean_total_m": total_m_sum / n_trials,
    }


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    grid = ([(a, l) for l in PHI_LEVELS for a in ("phi",)] +
            [(a, l) for l in AMP_LEVELS for a in ("amp",)] +
            [(a, l) for l in DET_LEVELS for a in ("det",)])
    results = []
    for axis, level in grid:
        for K in KS:
            c = cell(axis, level, K, N_TRIALS)
            results.append(c)
            print("  %-3s %9g K=%-2d  A=%.4f  B=%.4f  rej=%.3f  m=%.1f"
                  % (axis, level, K, c["recovery_A"], c["recovery_B"],
                     c["rejection"], c["mean_total_m"]), flush=True)
            with open(OUT, "w") as f:
                json.dump({
                    "experiment": "photonic_envelope",
                    "contract": "contract_photonics_backend_2026-08-20.md",
                    "description": ("Declared regeneration envelope: P_A/P_B vs "
                                    "K x noise axis (frozen E6/E7 levels)"),
                    "seed": SEED, "n_trials_per_cell": N_TRIALS,
                    "band": list(BAND), "M_K": M_K, "deltaT_K": 2.0,
                    "axes": {"phi_deg": PHI_LEVELS, "amp": AMP_LEVELS,
                             "det": DET_LEVELS},
                    "cells": results,
                }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
