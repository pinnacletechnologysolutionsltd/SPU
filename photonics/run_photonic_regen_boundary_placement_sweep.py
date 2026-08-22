#!/usr/bin/env python3
"""run_photonic_regen_boundary_placement_sweep.py — E15 of
contract_photonics_regen_boundary_placement_2026-08-22.md: does deferring
M=2's first REGEN boundary past exactly one combine op restore some or all
of the improvement M=2 failed to deliver in E14?

Pure M=2 (E14, frozen) groups at boundaries [2,4,6,8,10,12,14,16] -- group 1
is the two QLDIs only, zero combines before the first REGEN. M=2-shifted
moves every boundary by exactly +1 except the fixed endpoint 16:
[3,5,7,9,11,13,15,16] -- group 1 becomes 3 ops (2 QLDI + 1 combine), group 8
shrinks to 1 op to absorb the shift. REGEN-event count stays at 8 in both
cases -- this isolates "does the first boundary occur before any
computation" from "how often does regeneration happen" (contract SS2).

run_chain_boundary_noisy generalizes E13/E14's run_chain_periodic_noisy
from a uniform period M (`i % M == 0`) to an explicit boundary-position
list (`i in boundary_set`) -- pure M=2 and M=2-shifted are two boundary
lists through the same function (contract SS4).

M=2 (pure) and M=4 are E13/E14's frozen results, reused for reference only,
NOT rerun here (contract SS3).
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
    independent_oracle, gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

BOUNDARIES_M2_PURE = [2, 4, 6, 8, 10, 12, 14, 16]
BOUNDARIES_M2_SHIFTED = [3, 5, 7, 9, 11, 13, 15, 16]


def run_chain_boundary_noisy_diag(pb, block, boundaries, sigma_det, rng):
    """Generalizes E13/E14's run_chain_periodic_noisy[_diag] from a uniform
    period M to an explicit list of boundary positions (contract SS4):
    REGEN triggers on `i in boundary_set` instead of `i % M == 0`, all
    other logic (whole-state re-entry, _apply_op_field/_noise_per_op reuse)
    identical. Returns per-group diagnostics like E14's _diag function, for
    the equivalence gate (SS7 gate 0) and first-boundary state diagnostic
    (SS7 gate 0b)."""
    boundary_set = set(boundaries)
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
        if i in boundary_set:
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


def run_chain_boundary_noisy(pb, block, boundaries, sigma_det, rng):
    """Non-diagnostic entry point for the full sweep."""
    ok, _, _, _, qr0 = run_chain_boundary_noisy_diag(
        pb, block, boundaries, sigma_det, rng)
    return ok, qr0


def cell_boundary(boundaries, level, n_trials, K=16):
    """One (boundaries, det_level) cell -- same convention as E13/E14's
    cell()."""
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
        ok, _ = run_chain_boundary_noisy(pb, blk, boundaries, level, rng)
        n_ok += 1 if ok else 0
        accepted += 1
    p = n_ok / n_trials
    ci = 1.96 * (p * (1 - p) / n_trials) ** 0.5
    return {
        "boundaries": list(boundaries), "level": level, "recovery": p, "ci": ci,
        "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
    }


# Locked from the smoke pass (contract SS7 gate 2). Floor: pure M=2's
# 3.46e-6 crossing. Ceiling: native K=8's own crossing (5.92e-5), with the
# E13-scaling extrapolation reference (~5.48e-5) as an intermediate data
# point -- not a pass/fail threshold (contract SS3/SS6).
# Locked from the smoke pass (PHOTONIC_TRIALS=200, contract SS7 gate 2):
# recovery=1.0 at det<=3e-6, transition through 5e-6..3e-5, 0 by 7e-5 --
# dense around [5e-6, 3e-5], margin on both sides (floor near pure M=2's
# 3.46e-6 crossing, ceiling well past the E13-scaling extrapolation
# reference 5.48e-5 and native K=8's 5.92e-5). Not moved after this.
DET_LEVELS = [1e-6, 2e-6, 3e-6, 5e-6, 7e-6, 1e-5, 1.5e-5, 2e-5, 2.5e-5,
              3e-5, 4e-5, 5e-5, 7e-5, 1e-4, 2e-4, 3e-4]
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "30000"))
OUT = os.path.join(REPO, "results", "sweeps", "regen_boundary_placement_sweep.json")


def main():
    if DET_LEVELS is None:
        raise RuntimeError("DET_LEVELS must be locked from the smoke pass first")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    results = []
    total = len(DET_LEVELS)
    for i, level in enumerate(DET_LEVELS, 1):
        c = cell_boundary(BOUNDARIES_M2_SHIFTED, level, N_TRIALS)
        results.append(c)
        print("  [%3d/%3d] M2-shifted det=%9g recovery=%.4f rej=%.3f"
              % (i, total, level, c["recovery"], c["rejection"]), flush=True)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "regen_boundary_placement_sweep",
                "contract": "contract_photonics_regen_boundary_placement_2026-08-22.md",
                "description": ("E15: does deferring M=2's first REGEN boundary "
                                 "past exactly one combine op (boundaries "
                                 "[3,5,7,9,11,13,15,16] vs pure M=2's "
                                 "[2,4,6,8,10,12,14,16], same 8-event REGEN "
                                 "count) restore some of the improvement M=2 "
                                 "failed to deliver in E14?"),
                "seed": SEED, "n_trials_per_cell": N_TRIALS,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                "boundaries": BOUNDARIES_M2_SHIFTED, "det_levels": DET_LEVELS,
                "reference_points": {
                    "e14_frozen_m2_pure_999pct_geomean": 3.464e-6,
                    "e14_frozen_m2_pure_bracket_999pct": [3.0e-6, 4.0e-6],
                    "e13_frozen_m4_999pct_geomean": 1.732e-6,
                    "e9_k8_native_crossing_geomean": 5.92e-5,
                    "e13_scaling_extrapolation_reference": 5.48e-5,
                },
                "cells": results,
            }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
