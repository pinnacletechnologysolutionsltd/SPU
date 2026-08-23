#!/usr/bin/env python3
"""run_photonic_corrupted_state_sufficiency_sweep.py — E19 of
contract_photonics_corrupted_state_sufficiency_2026-08-23.md: within the
R_i=False subpopulation E18 already characterized, does the magnitude of
event i's recovery error (err_i) further stratify P(R_{i+1}), and how
much of E18's gap does it explain (attenuation metric A)?

Deterministic replay of E18's exact 300,000 trials (same SEED, same
sigma_det=3e-5, same M=2 boundaries) with one additive instrumentation:
run_chain_boundary_noisy_m0trace_with_error also exposes err = max
per-component |rec[0]-qr[0]| at each boundary, extending E16's frozen
run_chain_boundary_noisy_m0trace (verified equivalent via a hard gate
before being trusted, contract SS4/SS7).
"""
import cmath
import json
import math
import os
import sys
from collections import defaultdict
from statistics import NormalDist, median

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_correlation_mechanism_sweep import M2_BOUNDARIES  # noqa: E402
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

SIGMA_DET = 3e-5  # E18's locked operating point, reused exactly
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "300000"))
N_MIN_HALF = 100
E18_FROZEN = os.path.join(
    REPO, "results", "sweeps", "correlation_mechanism_sweep_frozen_v1_2026-08-23.json")


def run_chain_boundary_noisy_m0trace_with_error(pb, block, boundaries, sigma_det, rng):
    """Identical control flow to E16's run_chain_boundary_noisy_m0trace,
    additionally computing err = max_k |rec[0][k]-qr[0][k]| at each
    boundary. Returns [(m0, g_ok, err), ...] per boundary."""
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
    trace = []
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
            err = max(abs(rec[0][k] - qr[0][k]) for k in range(4))
            trace.append((m0_here, g_ok, err))
            for lane in range(13):
                le = pb._load_exp(rec[lane])
                f = pb.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            nd_last = None
    return trace


def load_e18_material_cells():
    d = json.load(open(E18_FROZEN))
    cells = {}
    for c in d["analysis"]["cells"]:
        if c["materially_dependent"]:
            cells[(c["pair_id"], c["bin"])] = {
                "p_true": c["p_true"], "p_false": c["p_false"],
                "n_tot_true": c["n_tot_true"], "n_tot_false": c["n_tot_false"],
            }
    return cells


def collect_err_data(sigma_det, n_trials, master, target_cells):
    """Replays n_trials trials (same clean-arrival rule as E18), and for
    each (pair_id, m0_ip1) in target_cells, among R_i=False observations,
    records err_i alongside R_{i+1}."""
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    # per-cell: list of (err_i, r_ip1)
    raw = defaultdict(list)
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, 16)
        if blk is None:
            continue
        trace = run_chain_boundary_noisy_m0trace_with_error(
            pb, blk, M2_BOUNDARIES, sigma_det, rng)
        clean = True
        n_pairs = len(trace) - 1
        for pair_id in range(n_pairs):
            if not clean:
                break
            m0_i, r_i, err_i = trace[pair_id]
            m0_ip1, r_ip1, _ = trace[pair_id + 1]
            key = (pair_id, m0_ip1)
            if not r_i and key in target_cells:
                raw[key].append((err_i, r_ip1))
            if not r_i:
                clean = False
        accepted += 1
    return raw


def z_ci(ok1, n1, ok2, n2, z_crit):
    p1, p2 = ok1 / n1, ok2 / n2
    diff = p1 - p2
    p_pool = (ok1 + ok2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if 0 < p_pool < 1 else 0.0
    z = diff / se if se > 0 else 0.0
    ci_lo, ci_hi = diff - z_crit * se, diff + z_crit * se
    return p1, p2, diff, z, ci_lo, ci_hi, se


def analyze(raw, e18_cells):
    n_tests = len(raw)
    z_crit = abs(NormalDist(0, 1).inv_cdf((0.05 / max(n_tests, 1)) / 2)) if n_tests else 0.0
    results = []
    for key, obs in raw.items():
        pair_id, m0_ip1 = key
        e18 = e18_cells[key]
        errs = sorted(o[0] for o in obs)
        med = median(errs)
        small = [o for o in obs if o[0] <= med]
        large = [o for o in obs if o[0] > med]
        n_small, n_large = len(small), len(large)
        if n_small < N_MIN_HALF or n_large < N_MIN_HALF:
            results.append({"pair_id": pair_id, "bin": m0_ip1, "excluded": True,
                             "n_small": n_small, "n_large": n_large, "median_err": med})
            continue
        ok_small = sum(1 for o in small if o[1])
        ok_large = sum(1 for o in large if o[1])
        p_s, p_l, diff_sl, z_sl, ci_lo_sl, ci_hi_sl, se_sl = z_ci(
            ok_small, n_small, ok_large, n_large, z_crit)
        p_true, p_false = e18["p_true"], e18["p_false"]
        gap = p_true - p_false
        a = (p_s - p_false) / gap if gap != 0 else float("nan")
        # propagate SE for A: A = 1 - (p_true - p_s)/gap ; treat p_true,
        # gap as fixed (from E18, large n); dominant uncertainty is p_s
        se_p_s = math.sqrt(p_s * (1 - p_s) / n_small) if 0 < p_s < 1 else 0.0
        se_a = se_p_s / abs(gap) if gap != 0 else float("nan")
        a_ci_lo, a_ci_hi = a - 1.96 * se_a, a + 1.96 * se_a
        # err distribution diagnostic
        err_counts = defaultdict(lambda: [0, 0])
        for e, r in obs:
            err_counts[e][1] += 1
            if r:
                err_counts[e][0] += 1
        err_curve = {str(e): {"n_ok": v[0], "n_tot": v[1], "p": v[0] / v[1]}
                     for e, v in sorted(err_counts.items()) if v[1] >= 20}
        results.append({
            "pair_id": pair_id, "bin": m0_ip1, "excluded": False,
            "median_err": med, "n_small": n_small, "n_large": n_large,
            "p_true": p_true, "p_false": p_false, "gap": gap,
            "p_small": p_s, "p_large": p_l,
            "stratify_diff": diff_sl, "stratify_z": z_sl,
            "stratify_ci_lo": ci_lo_sl, "stratify_ci_hi": ci_hi_sl,
            "statistically_stratified": not (ci_lo_sl <= 0 <= ci_hi_sl),
            "A": a, "A_ci_lo": a_ci_lo, "A_ci_hi": a_ci_hi,
            "substantial_explanation": a_ci_lo >= 0.5,
            "negligible_explanation": a_ci_hi < 0.25,
            "err_curve": err_curve,
        })
    n_analyzed = sum(1 for r in results if not r["excluded"])
    n_substantial = sum(1 for r in results if not r["excluded"] and r["substantial_explanation"])
    n_negligible = sum(1 for r in results if not r["excluded"] and r["negligible_explanation"])
    if n_substantial >= 12:
        tier = "err_i explains most of the gap"
    elif n_negligible >= 12:
        tier = "err_i does not explain the gap"
    else:
        tier = "Mixed"
    return {
        "n_cells_total": len(e18_cells), "n_analyzed": n_analyzed,
        "n_excluded": len(results) - n_analyzed,
        "z_crit_bonferroni": z_crit,
        "n_substantial_explanation": n_substantial,
        "n_negligible_explanation": n_negligible,
        "tier": tier, "cells": results,
    }


OUT = os.path.join(REPO, "results", "sweeps", "corrupted_state_sufficiency_sweep.json")


def main():
    master = make_master_rng(SEED)
    e18_cells = load_e18_material_cells()
    print("loaded %d E18 materially-dependent cells" % len(e18_cells))
    print("replaying %d trials at sigma_det=%g..." % (N_TRIALS, SIGMA_DET), flush=True)
    raw = collect_err_data(SIGMA_DET, N_TRIALS, master, set(e18_cells))
    analysis = analyze(raw, e18_cells)
    print("n_analyzed=%d n_excluded=%d n_substantial=%d n_negligible=%d tier=%s"
          % (analysis["n_analyzed"], analysis["n_excluded"],
             analysis["n_substantial_explanation"], analysis["n_negligible_explanation"],
             analysis["tier"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "experiment": "corrupted_state_sufficiency_sweep",
            "contract": "contract_photonics_corrupted_state_sufficiency_2026-08-23.md",
            "description": ("E19: within E18's R_i=False cells, does err_i "
                             "(error-magnitude descriptor) stratify "
                             "P(R_{i+1}), and how much of E18's gap does it "
                             "explain (attenuation metric A)? Deterministic "
                             "replay of E18's exact 300,000 trials."),
            "seed": SEED, "n_trials": N_TRIALS, "sigma_det": SIGMA_DET,
            "n_min_half": N_MIN_HALF,
            "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
            "analysis": analysis,
        }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
