#!/usr/bin/env python3
"""run_photonic_compiler_montecarlo_lesssaturated_sweep.py — E17 Part 4
of contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md:
repeats E17 Part 3's Monte-Carlo closeness-to-optimum test at a
deliberately located, less-saturated operating point (target: a
substantial fraction of sampled blocks with dp_recovery_mc in
[0.2, 0.8], not the near-ceiling regime E17 Part 3 tested).

Reuses E17 Part 3's CRN/scoring/statistics machinery verbatim (already
gated there -- not re-verified here, contract SS4/SS8). The only new
code is the operating-point search (SS4), using an RNG namespace
disjoint from the main run's (SEARCH_BLOCK_ID_OFFSET) so search-step
noise draws never collide with the main run's nd_table derivation.
"""
import json
import os
import sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_compiler_montecarlo_optimum_sweep import (  # noqa: E402
    build_nd_table, score_schedule_addressable, evaluate_block,
    INTERIOR_POSITIONS, CANDIDATE_CAP,
)
from run_photonic_compiler_optimal_placement_sweep import (  # noqa: E402
    precompute_qr_traj, optimal_placement,
)
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    gen_block, M_K, BAND, SEED,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend  # noqa: E402

LAMBDA = 0.01
# Widened by explicit amendment after the first search pass (contract
# SS3): the original grid's best candidate (5e-5) landed at 9/20, one
# block short of the >=10/20 bar. Added 4.5e-5/5.5e-5/6e-5 to bracket
# the observed non-monotonic peak rather than silently lowering the bar.
CANDIDATE_SIGMAS = [1.5e-5, 2e-5, 2.5e-5, 3e-5, 4e-5, 4.5e-5, 5e-5,
                    5.5e-5, 6e-5, 7e-5, 1e-4]
N_SEARCH_BLOCKS = 20
N_SEARCH_REPEATS = 1000
IN_BAND_THRESHOLD = 10  # of 20, per contract SS3
SEARCH_BLOCK_ID_OFFSET = 1_000_000  # disjoint RNG namespace from the main run
N_BLOCKS = int(os.environ.get("PHOTONIC_MC_BLOCKS", "20"))
N_REPEATS = int(os.environ.get("PHOTONIC_MC_REPEATS", "2000"))


def estimate_dp_recovery(block, block_id, sigma_det, lam, master, n_repeats,
                          block_id_offset=0):
    """Lightweight search-step estimator: DP's own schedule only, no
    alternative enumeration -- just enough to classify a block in/out of
    the target band. Uses block_id_offset to keep its nd_table draws in
    a disjoint RNG namespace from the main run's (contract SS4)."""
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    qr_traj = precompute_qr_traj(block)
    dp_boundaries, _, _ = optimal_placement(block, qr_traj, sigma_det, lam)
    n_ok = 0
    for repeat in range(n_repeats):
        table = build_nd_table(master, block_id + block_id_offset, repeat, sigma_det)
        ok, _ = score_schedule_addressable(pb, block, dp_boundaries, table)
        n_ok += 1 if ok else 0
    return n_ok / n_repeats, len(dp_boundaries)


def gather_blocks(master, n_blocks):
    blocks = []
    trial = 0
    while len(blocks) < n_blocks:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, 16)
        if blk is None:
            continue
        blocks.append(blk)
    return blocks


def search_operating_point(candidate_sigmas, lam, master, blocks,
                            n_search_repeats=N_SEARCH_REPEATS):
    """Gate 0c (contract SS4): locating procedure, not an inferential
    test. For each candidate sigma_det, count how many of `blocks` land
    in [0.2, 0.8] at n_search_repeats precision -- the SAME band the
    main experiment targets (not a coarser proxy)."""
    report = []
    for sigma_det in candidate_sigmas:
        in_band = 0
        per_block = []
        for block_id, blk in enumerate(blocks):
            p, n_boundaries = estimate_dp_recovery(
                blk, block_id, sigma_det, lam, master, n_search_repeats,
                block_id_offset=SEARCH_BLOCK_ID_OFFSET)
            landed = 0.2 <= p <= 0.8
            in_band += 1 if landed else 0
            per_block.append({"block_id": block_id, "dp_recovery_est": p,
                               "n_boundaries": n_boundaries, "in_band": landed})
        report.append({"sigma_det": sigma_det, "in_band_count": in_band,
                        "n_blocks": len(blocks), "per_block": per_block})
        print("  [search] sigma_det=%9g  in_band=%2d/%2d"
              % (sigma_det, in_band, len(blocks)), flush=True)
    best = max(report, key=lambda r: r["in_band_count"])
    return best, report


SEARCH_OUT = os.path.join(REPO, "results", "sweeps",
                           "compiler_montecarlo_lesssaturated_search.json")
OUT = os.path.join(REPO, "results", "sweeps",
                    "compiler_montecarlo_lesssaturated_sweep.json")


def main():
    search_only = "--search-only" in sys.argv
    master = make_master_rng(SEED)
    blocks = gather_blocks(master, N_SEARCH_BLOCKS)

    best, report = search_operating_point(CANDIDATE_SIGMAS, LAMBDA, master, blocks)
    os.makedirs(os.path.dirname(SEARCH_OUT), exist_ok=True)
    with open(SEARCH_OUT, "w") as f:
        json.dump({
            "experiment": "compiler_montecarlo_lesssaturated_search",
            "contract": "contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md",
            "candidate_sigmas": CANDIDATE_SIGMAS, "lambda": LAMBDA,
            "n_search_blocks": N_SEARCH_BLOCKS, "n_search_repeats": N_SEARCH_REPEATS,
            "in_band_threshold": IN_BAND_THRESHOLD,
            "report": report, "chosen": best,
        }, f, indent=1)
    print("search report written:", SEARCH_OUT)
    print("chosen sigma_det=%g with in_band=%d/%d"
          % (best["sigma_det"], best["in_band_count"], len(blocks)))

    if best["in_band_count"] < IN_BAND_THRESHOLD:
        print("HALT: no candidate sigma_det clears the >=%d/%d in-band bar. "
              "Full per-candidate table is in %s. Not proceeding."
              % (IN_BAND_THRESHOLD, len(blocks), SEARCH_OUT))
        return

    if search_only:
        print("--search-only: stopping after gate 0c.")
        return

    sigma_det = best["sigma_det"]
    results = []
    for block_id in range(N_BLOCKS):
        blk = blocks[block_id] if block_id < len(blocks) else None
        if blk is None:
            # N_BLOCKS > N_SEARCH_BLOCKS is not expected (both locked to 20),
            # but guard explicitly rather than silently reusing a stale block.
            raise RuntimeError("N_BLOCKS exceeds the pre-gathered search block set")
        r = evaluate_block(blk, block_id, sigma_det, LAMBDA, master,
                            N_REPEATS, CANDIDATE_CAP)
        results.append(r)
        print("  [%3d/%3d] sigma=%9g block=%2d n_boundaries=%d "
              "n_evaluated=%4d (%s) rank=%3d dp_mc=%.4f best_mc=%.4f "
              "best_beats_dp=%s"
              % (block_id + 1, N_BLOCKS, sigma_det, block_id, r["n_boundaries"],
                 r["n_evaluated_schedules"], r["enumeration_mode"],
                 r["rank_among_evaluated"], r["dp_recovery_mc"],
                 r["best_recovery_mc"], r["best_beats_dp_ci"]), flush=True)
        n_in_band = sum(1 for x in results if 0.2 <= x["dp_recovery_mc"] <= 0.8)
        with open(OUT, "w") as f:
            json.dump({
                "experiment": "compiler_montecarlo_lesssaturated_sweep",
                "contract": "contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md",
                "description": ("E17 Part 4: repeats E17 Part 3's Monte-Carlo "
                                 "closeness-to-optimum test at a deliberately "
                                 "located, less-saturated sigma_det. Result is "
                                 "conditional on the searched-and-locked "
                                 "operating point (gate 0c)."),
                "seed": SEED, "n_blocks": N_BLOCKS, "n_repeats": N_REPEATS,
                "candidate_cap": CANDIDATE_CAP,
                "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
                "lambda": LAMBDA, "sigma_det_locked": sigma_det,
                "operating_point_search_summary": {
                    "candidate_sigmas": CANDIDATE_SIGMAS,
                    "chosen_sigma_det": sigma_det,
                    "search_in_band_count": best["in_band_count"],
                    "search_n_blocks": len(blocks),
                },
                "main_run_in_band_count_so_far": n_in_band,
                "blocks": results,
            }, f, indent=1)
    print("wrote", OUT)
    n_in_band_final = sum(1 for x in results if 0.2 <= x["dp_recovery_mc"] <= 0.8)
    print("main run in-band (full precision): %d/%d" % (n_in_band_final, N_BLOCKS))


if __name__ == "__main__":
    main()
