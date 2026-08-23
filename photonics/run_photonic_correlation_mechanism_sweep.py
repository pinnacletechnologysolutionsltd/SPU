#!/usr/bin/env python3
"""run_photonic_correlation_mechanism_sweep.py — E18 of
contract_photonics_correlation_mechanism_2026-08-23.md: does event i's
outcome (R_i) predict event i+1's outcome beyond what m0_{i+1} alone
predicts, at fixed M=2 placement, under the real simulator?

Reuses run_chain_boundary_noisy_m0trace (E16, frozen) verbatim -- no new
simulation code. The only new logic is (a) the "clean arrival up to i"
pair-collection rule (contract SS4), (b) the deterministic m0 binning
hierarchy (contract SS4, decided by sample count only, never by
significance), and (c) the operating-point search with its own disjoint
RNG namespace, kept separate from the inferential run's (contract SS3
amendment A).
"""
import itertools
import json
import math
import os
import sys
from collections import defaultdict
from math import comb  # noqa: F401  (kept for parity with sibling drivers)
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_m0_dynamic_range_sweep import (  # noqa: E402
    run_chain_boundary_noisy_m0trace,
)
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend  # noqa: E402

M2_BOUNDARIES = [2, 4, 6, 8, 10, 12, 14, 16]
N_PAIRS = len(M2_BOUNDARIES) - 1  # 7 adjacent pairs
N_MIN = 200
CANDIDATE_SIGMAS = [1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4]
SEARCH_TRIAL_OFFSET = 100_000_000  # disjoint from the main run's trial indices
MIN_ELIGIBLE_CELLS = 20
MIN_PAIRS_REPRESENTED = 5


def collect_pair_histogram(sigma_det, n_trials, master, trial_offset=0):
    """Runs n_trials accepted blocks starting at trial index
    `trial_offset`; for each, walks the M=2 group sequence applying the
    "clean arrival up to i" rule (contract SS4): for pair (i, i+1),
    record (m0_{i+1}, R_i) -> R_{i+1} only while groups 1..i-1 have all
    succeeded (R_i itself may be True or False -- it's the variable
    under study; stop after the first False). Returns a raw,
    exact-integer-m0 histogram: {(pair_id, m0_ip1, R_i): [n_ok, n_tot]}.
    """
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    hist = defaultdict(lambda: [0, 0])
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial_offset + trial)
        trial += 1
        blk = gen_block(rng, 16)
        if blk is None:
            continue
        trace = run_chain_boundary_noisy_m0trace(pb, blk, M2_BOUNDARIES, sigma_det, rng)
        clean = True
        for pair_id in range(N_PAIRS):
            if not clean:
                break
            m0_i, r_i = trace[pair_id]
            m0_ip1, r_ip1 = trace[pair_id + 1]
            key = (pair_id, m0_ip1, r_i)
            hist[key][1] += 1
            if r_ip1:
                hist[key][0] += 1
            if not r_i:
                clean = False
        accepted += 1
    return hist


def _bin_width2(m0):
    return 2 * (m0 // 2)


def _bin_width4(m0):
    return 4 * (m0 // 4)


def apply_binning_hierarchy(raw_hist, n_min=N_MIN):
    """Deterministic hierarchy (contract SS4): exact integer -> width-2
    -> width-4 -> exclude, decided by sample count only. Returns a list
    of resolved cells: {"pair_id", "bin", "resolution", "n_ok_true",
    "n_tot_true", "n_ok_false", "n_tot_false"}."""
    by_pair_true = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    by_pair_false = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for (pair_id, m0, r_i), (n_ok, n_tot) in raw_hist.items():
        target = by_pair_true if r_i else by_pair_false
        target[pair_id][m0][0] += n_ok
        target[pair_id][m0][1] += n_tot

    all_pairs = set(by_pair_true) | set(by_pair_false)
    resolved = []
    for pair_id in sorted(all_pairs):
        exact_m0s = set(by_pair_true[pair_id]) | set(by_pair_false[pair_id])
        seen_m0 = set()
        for m0 in sorted(exact_m0s):
            if m0 in seen_m0:
                continue
            t = by_pair_true[pair_id].get(m0, [0, 0])
            f = by_pair_false[pair_id].get(m0, [0, 0])
            if t[1] >= n_min and f[1] >= n_min:
                resolved.append({"pair_id": pair_id, "bin": m0, "resolution": "exact",
                                  "n_ok_true": t[0], "n_tot_true": t[1],
                                  "n_ok_false": f[0], "n_tot_false": f[1]})
                seen_m0.add(m0)
        # width-2 pass over remaining (unresolved) exact m0 values
        remaining = sorted(m for m in exact_m0s if m not in seen_m0)
        w2_groups = defaultdict(list)
        for m in remaining:
            w2_groups[_bin_width2(m)].append(m)
        for b2, members in sorted(w2_groups.items()):
            t = [sum(by_pair_true[pair_id].get(m, [0, 0])[0] for m in members),
                 sum(by_pair_true[pair_id].get(m, [0, 0])[1] for m in members)]
            f = [sum(by_pair_false[pair_id].get(m, [0, 0])[0] for m in members),
                 sum(by_pair_false[pair_id].get(m, [0, 0])[1] for m in members)]
            if t[1] >= n_min and f[1] >= n_min:
                resolved.append({"pair_id": pair_id, "bin": b2, "resolution": "width2",
                                  "n_ok_true": t[0], "n_tot_true": t[1],
                                  "n_ok_false": f[0], "n_tot_false": f[1]})
                seen_m0.update(members)
        # width-4 pass over what's still unresolved
        remaining2 = sorted(m for m in exact_m0s if m not in seen_m0)
        w4_groups = defaultdict(list)
        for m in remaining2:
            w4_groups[_bin_width4(m)].append(m)
        for b4, members in sorted(w4_groups.items()):
            t = [sum(by_pair_true[pair_id].get(m, [0, 0])[0] for m in members),
                 sum(by_pair_true[pair_id].get(m, [0, 0])[1] for m in members)]
            f = [sum(by_pair_false[pair_id].get(m, [0, 0])[0] for m in members),
                 sum(by_pair_false[pair_id].get(m, [0, 0])[1] for m in members)]
            if t[1] >= n_min and f[1] >= n_min:
                resolved.append({"pair_id": pair_id, "bin": b4, "resolution": "width4",
                                  "n_ok_true": t[0], "n_tot_true": t[1],
                                  "n_ok_false": f[0], "n_tot_false": f[1]})
            # else: excluded, per the frozen hierarchy -- not widened further
    return resolved


def search_operating_point(candidate_sigmas, master, n_search_trials):
    """Gate 0 (contract SS3/SS4/SS7): search RNG namespace only, trials
    discarded afterward -- never reused in the inferential run."""
    report = []
    for sigma_det in candidate_sigmas:
        raw = collect_pair_histogram(sigma_det, n_search_trials, master,
                                      trial_offset=SEARCH_TRIAL_OFFSET)
        resolved = apply_binning_hierarchy(raw, n_min=N_MIN)
        n_eligible = len(resolved)
        pairs_represented = len({c["pair_id"] for c in resolved})
        clears_bar = (n_eligible >= MIN_ELIGIBLE_CELLS and
                      pairs_represented >= MIN_PAIRS_REPRESENTED)
        report.append({"sigma_det": sigma_det, "n_eligible_cells": n_eligible,
                        "pairs_represented": pairs_represented,
                        "clears_bar": clears_bar})
        print("  [search] sigma_det=%9g  eligible_cells=%3d  pairs_represented=%d/%d  clears_bar=%s"
              % (sigma_det, n_eligible, pairs_represented, N_PAIRS, clears_bar), flush=True)
    candidates_clearing = [r for r in report if r["clears_bar"]]
    chosen = None
    if candidates_clearing:
        chosen = max(candidates_clearing, key=lambda r: r["n_eligible_cells"])
    return chosen, report


def z_test(ok1, n1, ok2, n2):
    p1, p2 = ok1 / n1, ok2 / n2
    p_pool = (ok1 + ok2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if 0 < p_pool < 1 else 0.0
    z = (p1 - p2) / se if se > 0 else 0.0
    return z, p1 - p2


def analyze(resolved_cells):
    n_tests = len(resolved_cells)
    if n_tests == 0:
        return {"n_tests": 0, "cells": []}
    alpha_bonf = 0.05 / n_tests
    z_crit = abs(NormalDist(0, 1).inv_cdf(alpha_bonf / 2))
    se_z = 1.96 / z_crit if z_crit > 0 else 1.96  # scale factor for a Bonferroni-adjusted 95% CI
    out = []
    for c in resolved_cells:
        z, diff = z_test(c["n_ok_true"], c["n_tot_true"], c["n_ok_false"], c["n_tot_false"])
        p1, p2 = c["n_ok_true"] / c["n_tot_true"], c["n_ok_false"] / c["n_tot_false"]
        p_pool = (c["n_ok_true"] + c["n_ok_false"]) / (c["n_tot_true"] + c["n_tot_false"])
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / c["n_tot_true"] + 1 / c["n_tot_false"])) \
            if 0 < p_pool < 1 else 0.0
        ci_half = z_crit * se
        ci_lo, ci_hi = diff - ci_half, diff + ci_half
        statistically_dependent = not (ci_lo <= 0 <= ci_hi)
        materially_dependent = statistically_dependent and abs(diff) > 0.05
        out.append(dict(c, p_true=p1, p_false=p2, diff=diff, z=z,
                         ci_lo=ci_lo, ci_hi=ci_hi,
                         statistically_dependent=statistically_dependent,
                         materially_dependent=materially_dependent))
    n_stat = sum(1 for c in out if c["statistically_dependent"])
    n_material = sum(1 for c in out if c["materially_dependent"])
    if n_stat / n_tests < 0.05 and n_material == 0:
        tier = "Independence (Confirmed)"
    elif n_stat / n_tests >= 0.05 or n_material > 0:
        tier = "Real dependence found"
    else:
        tier = "Mixed/inconclusive"
    return {"n_tests": n_tests, "z_crit_bonferroni": z_crit,
            "n_statistically_dependent": n_stat, "n_materially_dependent": n_material,
            "tier": tier, "cells": out}


N_SEARCH_TRIALS = int(os.environ.get("PHOTONIC_SEARCH_TRIALS", "20000"))
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "300000"))
SEARCH_OUT = os.path.join(REPO, "results", "sweeps", "correlation_mechanism_search.json")
OUT = os.path.join(REPO, "results", "sweeps", "correlation_mechanism_sweep.json")


def main():
    search_only = "--search-only" in sys.argv
    master = make_master_rng(SEED)

    chosen, report = search_operating_point(CANDIDATE_SIGMAS, master, N_SEARCH_TRIALS)
    os.makedirs(os.path.dirname(SEARCH_OUT), exist_ok=True)
    with open(SEARCH_OUT, "w") as f:
        json.dump({
            "experiment": "correlation_mechanism_search",
            "contract": "contract_photonics_correlation_mechanism_2026-08-23.md",
            "candidate_sigmas": CANDIDATE_SIGMAS, "n_search_trials": N_SEARCH_TRIALS,
            "min_eligible_cells": MIN_ELIGIBLE_CELLS,
            "min_pairs_represented": MIN_PAIRS_REPRESENTED,
            "report": report, "chosen": chosen,
        }, f, indent=1)
    print("search report written:", SEARCH_OUT)

    if chosen is None:
        print("HALT: no candidate sigma_det clears the eligibility bar "
              "(>=%d cells, >=%d/%d pairs represented). Full table in %s. Not proceeding."
              % (MIN_ELIGIBLE_CELLS, MIN_PAIRS_REPRESENTED, N_PAIRS, SEARCH_OUT))
        return
    print("chosen sigma_det=%g (eligible_cells=%d, pairs_represented=%d/%d)"
          % (chosen["sigma_det"], chosen["n_eligible_cells"],
             chosen["pairs_represented"], N_PAIRS))

    if search_only:
        print("--search-only: stopping after gate 0.")
        return

    sigma_det = chosen["sigma_det"]
    print("collecting %d fresh inferential trials at sigma_det=%g..."
          % (N_TRIALS, sigma_det), flush=True)
    raw = collect_pair_histogram(sigma_det, N_TRIALS, master, trial_offset=0)
    resolved = apply_binning_hierarchy(raw, n_min=N_MIN)
    analysis = analyze(resolved)

    print("n_tests=%d  statistically_dependent=%d  materially_dependent=%d  tier=%s"
          % (analysis["n_tests"], analysis["n_statistically_dependent"],
             analysis["n_materially_dependent"], analysis["tier"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "experiment": "correlation_mechanism_sweep",
            "contract": "contract_photonics_correlation_mechanism_2026-08-23.md",
            "description": ("E18: does R_i predict R_{i+1} beyond m0_{i+1} "
                             "alone, at fixed M=2 placement? Search and "
                             "inference use disjoint RNG namespaces/trials."),
            "seed": SEED, "n_trials": N_TRIALS, "n_min": N_MIN,
            "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
            "sigma_det_locked": sigma_det,
            "operating_point_search_summary": chosen,
            "analysis": analysis,
        }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
