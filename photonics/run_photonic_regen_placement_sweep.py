#!/usr/bin/env python3
"""run_photonic_regen_placement_sweep.py — E13 of
contract_photonics_regen_placement_2026-08-22.md: does regenerating more
frequently within a logical K=16 sequence restore recovery comparable to
K=8's own crossing (~5e-5), or does it stay near K=16's collapsed
crossing (~3-5e-9)? run_chain_noisy (used by E8/E9/E11/E12) has ZERO
intermediate-regeneration support -- confirmed by reading the code, not
assumed (contract SS2). run_chain_periodic_noisy is new: splits a flat
16-op gen_block sequence into groups of M ops, REGENerating (whole-state,
all 13 lanes -- required by contract_regen_isa_0x09_2026-08-20.md SS5,
not just convenient reuse) after each group.

M in {4, 8, 16}, all measured directly in this sweep -- M=16 is the
control anchor (no intermediate regen, should reproduce E9's Arm-B K=16
result). sigma_phi=sigma_amp=0 always (isolated detector axis).
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

from run_photonic_envelope_sweep import gen_block, M_K, BAND, SEED  # noqa: E402
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import (  # noqa: E402
    PhotonicQuadrayBackend, CLAMP, exact_qsub, exact_rotc,
)


def independent_oracle(block):
    """Standalone replay (not via _apply_op_field) -- the ground truth
    the noiseless gate checks run_chain_periodic_noisy against."""
    qr = [[0, 0, 0, 0] for _ in range(13)]
    for op in block:
        if op[0] == "QLDI":
            qr[op[1]] = list(op[2])
        elif op[0] == "QSUB":
            d, sa, sb = op[1], op[2], op[3]
            qr[d] = list(exact_qsub(qr[sa], qr[sb]))
        elif op[0] == "ROTC":
            dst, src, ang = op[1], op[2], op[3]
            qr[dst] = list(exact_rotc(qr[src], ang))
    return qr[0]


def run_chain_periodic_noisy(pb, block, M, sigma_det, rng):
    """Groups of M ops (contract SS3); whole-state REGEN after each group,
    scored against that group's exact oracle. Trial succeeds iff EVERY
    group's REGEN recovers exactly. Mirrors run_chain's per-block REGEN
    (test_regen_equivalence.py:264-278) + run_chain_noisy's per-op noise
    injection. Returns (all_ok, final_qr0)."""
    if hasattr(rng, "normal"):
        draw = lambda mu, sd: float(rng.normal(mu, sd))
    else:
        draw = lambda mu, sd: rng.gauss(mu, sd)
    fld = [[0j] * 4 for _ in range(13)]
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    angle = 0.0
    all_ok = True
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


def cell(M, level, n_trials, K=16):
    """One (M, det_level) cell: n_trials accepted, same convention as
    E8/E9/E11/E12's cell()."""
    master = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    n_ok = 0
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
        ok, _ = run_chain_periodic_noisy(pb, blk, M, level, rng)
        n_ok += 1 if ok else 0
        accepted += 1
    p = n_ok / n_trials
    ci = 1.96 * (p * (1 - p) / n_trials) ** 0.5
    return {
        "M": M, "level": level, "recovery": p, "ci": ci,
        "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
    }


# Locked grid (contract SS3, revised per review: M=16 measured directly in
# this sweep as the control anchor, not just referenced from E9 -- same
# harness, apples-to-apples). Grid locked from the smoke pass; not moved
# afterward regardless of what the full run shows.
DET_LEVELS = [1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 3e-7,
              1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4]
M_VALUES = [4, 8, 16]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "regen_placement_sweep.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cell_specs = [(M, level) for M in M_VALUES for level in DET_LEVELS]
    results = []
    total = len(cell_specs)
    for i, (M, level) in enumerate(cell_specs, 1):
        c = cell(M, level, N_TRIALS)
        results.append(c)
        print("  [%3d/%3d] M=%-2d det=%9g recovery=%.4f rej=%.3f"
              % (i, total, M, level, c["recovery"], c["rejection"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "regen_placement_sweep",
                "contract": "contract_photonics_regen_placement_2026-08-22.md",
                "description": ("Regeneration-frequency sweep at K=16: does "
                                 "regenerating every M ops restore recovery "
                                 "toward E9's K=8 territory (~5e-5) or stay "
                                 "near K=16's collapsed crossing (~3-5e-9)? "
                                 "M=16 measured directly as the control anchor."),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                "M_values": M_VALUES, "det_levels": DET_LEVELS,
                "reference_points": {
                    "E9_K8_99.9pct_bracket": [5.0e-5, 7.0e-5],
                    "E9_K16_99.9pct_bracket": [3.0e-9, 5.0e-9],
                },
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
