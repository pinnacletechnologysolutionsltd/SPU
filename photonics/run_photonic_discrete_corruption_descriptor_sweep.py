#!/usr/bin/env python3
"""run_photonic_discrete_corruption_descriptor_sweep.py — E20 of
contract_photonics_discrete_corruption_descriptor_2026-08-24.md: within the
R_i=False subpopulation E18/E19 already characterized, do three discrete
properties of the corrupted lane-0 state at boundary i -- (a) which
component j in {0,1,2,3} carries the largest deviation, (b) sign(delta_j),
(c) the operation type active at boundary i (QSUB / ROTC_thirds /
ROTC_plain) -- stratify P(R_{i+1}) beyond m0_{i+1}, and how much of E18's
gap does each explain (descriptor-conditioned weighted metric A_D,
Amendment 1)?

Deterministic replay of E18/E19's exact 300,000 trials (same SEED, same
sigma_det=3e-5, same M=2 boundaries). One additive instrumentation:
run_chain_boundary_noisy_m0trace_with_descriptor extends E19's frozen
run_chain_boundary_noisy_m0trace_with_error to also expose j, delta_j
(signed deviation) and a tie flag per boundary -- verified equivalent to
E19's (m0, g_ok, err) sequence via a hard gate before being trusted
(contract SS4/SS7).

Tested as THREE SEPARATE univariate stratifications (j, sign, op_i), not
one joint model -- see contract SS1 for the post-hoc-fragmentation
rationale. Gap/effect size uses eta-squared (Amendment 5, round 2):
Amendment 1's weighted-average A_D was found to be mathematically
tautological (p_D = sum_c w_c*p_c collapses identically to p_false by the
law of total probability whenever no category is excluded) and was
replaced post-hoc -- pure re-analysis of the already-frozen raw_events, no
resimulation. Never a best-vs-worst single category's A_c (retained only
as a diagnostic, Amendment 2). Statistical family: 24 cell-level omnibus
(chi-square) tests per descriptor, Bonferroni-corrected within each
descriptor's own family (Amendment 3).

--reanalyze-only reads raw_events back out of an existing output JSON and
recomputes just the analysis block (used for the round-2 eta-squared
swap); default mode replays the simulator from scratch.
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

from run_photonic_correlation_mechanism_sweep import M2_BOUNDARIES  # noqa: E402
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    gen_block, M_K, BAND, SEED,
)
from run_photonic_corrupted_state_sufficiency_sweep import (  # noqa: E402
    run_chain_boundary_noisy_m0trace_with_error, load_e18_material_cells,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

SIGMA_DET = 3e-5  # E18/E19's locked operating point, reused exactly
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "300000"))
N_MIN = 100
N_EQUIV_CHECK = 2000

THIRDS_ANGLES = (1, 3, 4)   # exact-thirds division, E11
PLAIN_ANGLES = (0, 2, 5)    # identity / pure permutation, denominator 1


def run_chain_boundary_noisy_m0trace_with_descriptor(pb, block, boundaries, sigma_det, rng):
    """Identical control flow to E19's *_with_error, additionally returns j
    (argmax_k |rec[0][k]-qr[0][k]|, lowest index on ties), delta_j (signed
    rec[0][j]-qr[0][j]), and a tie diagnostic flag. Returns
    [(m0, g_ok, err, j, delta_j, tie), ...] per boundary."""
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
            devs = [rec[0][k] - qr[0][k] for k in range(4)]
            absdevs = [abs(d) for d in devs]
            max_abs = max(absdevs)
            tie = sum(1 for a in absdevs if a == max_abs) > 1
            j = max(range(4), key=lambda k: (absdevs[k], -k))
            delta_j = devs[j]
            err = absdevs[j]
            trace.append((m0_here, g_ok, err, j, delta_j, tie))
            for lane in range(13):
                le = pb._load_exp(rec[lane])
                f = pb.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            nd_last = None
    return trace


def op_type(block, boundary_pos):
    """Mechanical definition (contract SS2, no causal claim): the operation
    immediately preceding boundary boundary_pos (1-indexed op count),
    block[boundary_pos-1]."""
    op = block[boundary_pos - 1]
    kind = op[0]
    if kind == "QSUB":
        return "QSUB"
    if kind == "ROTC":
        ang = op[3]
        return "ROTC_thirds" if ang in THIRDS_ANGLES else "ROTC_plain"
    return kind  # QLDI: not expected for pair_id>=1 (E18/E19 scope), kept for robustness


def equivalence_check(n_check=N_EQUIV_CHECK):
    """Hard gate (contract SS4/SS7): confirm (m0, g_ok, err) from the new
    descriptor-instrumented trace function is bit-identical to E19's frozen
    run_chain_boundary_noisy_m0trace_with_error, on matched inputs. Also
    checks internal consistency: |delta_j| == err."""
    master_old = make_master_rng(SEED)
    master_new = make_master_rng(SEED)
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    trial = 0
    checked = 0
    mismatches = 0
    while checked < n_check:
        rng_old = trial_rng(master_old, trial)
        rng_new = trial_rng(master_new, trial)
        trial += 1
        blk_old = gen_block(rng_old, 16)
        blk_new = gen_block(rng_new, 16)
        if blk_old is None or blk_new is None:
            continue
        if blk_old != blk_new:
            mismatches += 1
            checked += 1
            continue
        trace_old = run_chain_boundary_noisy_m0trace_with_error(
            pb, blk_old, M2_BOUNDARIES, SIGMA_DET, rng_old)
        trace_new = run_chain_boundary_noisy_m0trace_with_descriptor(
            pb, blk_new, M2_BOUNDARIES, SIGMA_DET, rng_new)
        for (m0_o, ok_o, err_o), (m0_n, ok_n, err_n, j_n, dj_n, _tie) in zip(trace_old, trace_new):
            if (m0_o, ok_o, err_o) != (m0_n, ok_n, err_n):
                mismatches += 1
            if abs(dj_n) != err_n:
                mismatches += 1
        checked += 1
    return mismatches, checked


def collect_descriptor_stratified(sigma_det, n_trials, master, target_cells):
    """Replays n_trials trials (same clean-arrival rule, same generation
    order as E18/E19), and for each (pair_id, m0_ip1) in target_cells,
    among R_i=False observations, records the raw tuple
    (j, delta_j, err, op_i, r_ip1)."""
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    raw = defaultdict(list)
    n_ties_used = 0
    n_used_total = 0
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, 16)
        if blk is None:
            continue
        trace = run_chain_boundary_noisy_m0trace_with_descriptor(
            pb, blk, M2_BOUNDARIES, sigma_det, rng)
        clean = True
        n_pairs = len(trace) - 1
        for pair_id in range(n_pairs):
            if not clean:
                break
            m0_i, r_i, err_i, j_i, delta_j_i, tie_i = trace[pair_id]
            m0_ip1, r_ip1 = trace[pair_id + 1][0], trace[pair_id + 1][1]
            key = (pair_id, m0_ip1)
            if not r_i and key in target_cells:
                boundary_pos = M2_BOUNDARIES[pair_id]
                op_i = op_type(blk, boundary_pos)
                raw[key].append((j_i, delta_j_i, err_i, op_i, r_ip1))
                n_used_total += 1
                if tie_i:
                    n_ties_used += 1
            if not r_i:
                clean = False
        accepted += 1
    tie_stats = {"n_ties_among_used": n_ties_used, "n_used_total": n_used_total}
    return raw, tie_stats


def chi2_sf(x, dof):
    """Closed-form chi-square survival function for dof in {1,2,3}
    (sufficient for descriptors with up to 4 categories)."""
    if x <= 0:
        return 1.0
    if dof == 1:
        return math.erfc(math.sqrt(x / 2))
    if dof == 2:
        return math.exp(-x / 2)
    if dof == 3:
        return math.erfc(math.sqrt(x / 2)) + math.sqrt(2 * x / math.pi) * math.exp(-x / 2)
    raise ValueError("unsupported dof %d" % dof)


def omnibus_chi2(cat_counts):
    """cat_counts: {category: (n_ok, n_tot)}. Standard 2xk contingency
    chi-square statistic for homogeneity of recovery rate across
    categories. Returns (stat, dof)."""
    n_ok_tot = sum(v[0] for v in cat_counts.values())
    n_tot = sum(v[1] for v in cat_counts.values())
    p_pool = n_ok_tot / n_tot
    stat = 0.0
    for n_ok, n_tot_c in cat_counts.values():
        n_fail = n_tot_c - n_ok
        e_ok = n_tot_c * p_pool
        e_fail = n_tot_c * (1 - p_pool)
        if e_ok > 0:
            stat += (n_ok - e_ok) ** 2 / e_ok
        if e_fail > 0:
            stat += (n_fail - e_fail) ** 2 / e_fail
    dof = len(cat_counts) - 1
    return stat, dof


def analyze_descriptor(raw, e18_cells, category_fn, n_min, name):
    """Amendment 3: one omnibus test per cell, Bonferroni-corrected within
    this descriptor's own 24-cell family. Amendment 1: gap explanation via
    the descriptor-conditioned weighted rate A_D. Amendment 2: A_c retained
    as a per-category diagnostic only."""
    n_tests = len(raw)
    results = []
    for key, obs in raw.items():
        pair_id, m0_ip1 = key
        e18 = e18_cells[key]
        p_true, p_false = e18["p_true"], e18["p_false"]
        gap = p_true - p_false
        cat_counts = defaultdict(lambda: [0, 0])
        for entry in obs:
            c = category_fn(entry)
            cat_counts[c][1] += 1
            if entry[-1]:
                cat_counts[c][0] += 1
        included = {c: tuple(v) for c, v in cat_counts.items() if v[1] >= n_min}
        excluded_cats = {c: tuple(v) for c, v in cat_counts.items() if v[1] < n_min}
        if len(included) < 2:
            results.append({
                "pair_id": pair_id, "bin": m0_ip1, "excluded": True,
                "reason": "fewer than 2 categories with n>=n_min",
                "category_counts": {c: {"n_ok": v[0], "n_tot": v[1]} for c, v in cat_counts.items()},
            })
            continue
        stat, dof = omnibus_chi2(included)
        p_value = chi2_sf(stat, dof)
        alpha_corrected = 0.05 / max(n_tests, 1)
        omnibus_significant = p_value < alpha_corrected
        n_incl_tot = sum(v[1] for v in included.values())
        cat_p = {c: v[0] / v[1] for c, v in included.items()}
        # Amendment 5 (round 2): eta-squared replaces the tautological A_D
        # (p_D = sum_c w_c*p_c collapses identically to p_false by the law
        # of total probability -- see contract's round-2 finding).
        p_bar = sum((v[1] / n_incl_tot) * cat_p[c] for c, v in included.items())
        ss_between = sum(v[1] * (cat_p[c] - p_bar) ** 2 for c, v in included.items())
        ss_total = n_incl_tot * p_bar * (1 - p_bar)
        eta2 = ss_between / ss_total if ss_total > 0 else float("nan")
        cat_diag = {}
        for c, (n_ok, n_tot) in included.items():
            p_c = n_ok / n_tot
            se_p_c = math.sqrt(p_c * (1 - p_c) / n_tot) if 0 < p_c < 1 else 0.0
            A_c = (p_c - p_false) / gap if gap != 0 else float("nan")
            se_A_c = se_p_c / abs(gap) if gap != 0 else float("nan")
            cat_diag[c] = {
                "n_ok": n_ok, "n_tot": n_tot, "p": p_c, "A": A_c,
                "A_ci_lo": A_c - 1.96 * se_A_c, "A_ci_hi": A_c + 1.96 * se_A_c,
            }
        results.append({
            "pair_id": pair_id, "bin": m0_ip1, "excluded": False,
            "p_true": p_true, "p_false": p_false, "gap": gap,
            "n_categories_included": len(included), "n_categories_excluded": len(excluded_cats),
            "category_diagnostics": cat_diag,
            "excluded_categories": {c: {"n_ok": v[0], "n_tot": v[1]} for c, v in excluded_cats.items()},
            "omnibus_chi2": stat, "omnibus_dof": dof, "omnibus_p": p_value,
            "alpha_corrected": alpha_corrected, "omnibus_significant": omnibus_significant,
            "p_bar": p_bar, "eta2": eta2,
            "substantial_explanation": eta2 >= 0.14 and omnibus_significant,
            "negligible_explanation": eta2 < 0.01,
        })
    n_analyzed = sum(1 for r in results if not r["excluded"])
    n_substantial = sum(1 for r in results if not r["excluded"] and r["substantial_explanation"])
    n_negligible = sum(1 for r in results if not r["excluded"] and r["negligible_explanation"])
    n_omnibus_sig = sum(1 for r in results if not r["excluded"] and r["omnibus_significant"])
    if n_substantial >= 12:
        tier = "%s explains most of the gap" % name
    elif n_negligible >= 12:
        tier = "%s does not explain the gap" % name
    else:
        tier = "Mixed"
    return {
        "descriptor": name, "n_cells_total": len(e18_cells), "n_tests_family": n_tests,
        "n_analyzed": n_analyzed, "n_excluded": len(results) - n_analyzed,
        "n_omnibus_significant": n_omnibus_sig,
        "n_substantial_explanation": n_substantial, "n_negligible_explanation": n_negligible,
        "tier": tier, "cells": results,
    }


OUT = os.path.join(REPO, "results", "sweeps", "discrete_corruption_descriptor_sweep.json")


def main():
    print("running equivalence cross-check (%d trials)..." % N_EQUIV_CHECK, flush=True)
    mismatches, checked = equivalence_check(N_EQUIV_CHECK)
    print("equivalence check: %d trials checked, %d mismatches" % (checked, mismatches))
    if mismatches:
        print("HALT: equivalence check FAILED")
        sys.exit(1)
    print("equivalence check PASSED")

    master = make_master_rng(SEED)
    e18_cells = load_e18_material_cells()
    print("loaded %d E18 materially-dependent cells" % len(e18_cells))
    print("replaying %d trials at sigma_det=%g..." % (N_TRIALS, SIGMA_DET), flush=True)
    raw, tie_stats = collect_descriptor_stratified(SIGMA_DET, N_TRIALS, master, set(e18_cells))

    fidelity_ok = True
    if N_TRIALS == 300000:
        # full-scale run: raw counts must match E18/E19's frozen n_tot_false exactly.
        for key, cell in e18_cells.items():
            n_got = len(raw.get(key, []))
            n_expected = cell["n_tot_false"]
            if n_got != n_expected:
                fidelity_ok = False
                print("REPLAY FIDELITY MISMATCH: cell %s got %d expected %d" % (key, n_got, n_expected))
        if not fidelity_ok:
            print("HALT: replay fidelity check FAILED")
            sys.exit(1)
        print("replay fidelity check PASSED (%d cells match E18 exactly)" % len(e18_cells))
    else:
        # smoke scale: sanity-check proportionality against E18's 300,000-trial
        # counts (same design as E19's smoke-scale check), not exact match.
        ratio_expected = N_TRIALS / 300000
        for key, cell in e18_cells.items():
            n_got = len(raw.get(key, []))
            n_expected = cell["n_tot_false"]
            ratio_got = n_got / n_expected if n_expected else float("nan")
            if not (0.5 * ratio_expected <= ratio_got <= 1.5 * ratio_expected):
                fidelity_ok = False
                print("SMOKE PROPORTIONALITY MISMATCH: cell %s ratio=%.4f expected~%.4f"
                      % (key, ratio_got, ratio_expected))
        if not fidelity_ok:
            print("HALT: smoke proportionality check FAILED")
            sys.exit(1)
        print("smoke proportionality check PASSED (%d cells within tolerance of expected ratio)"
              % len(e18_cells))

    equivalence_meta = {"trials_checked": checked, "mismatches": mismatches}
    write_output(raw, e18_cells, equivalence_meta, tie_stats)


def analyze_and_report(raw, e18_cells):
    analysis_j = analyze_descriptor(raw, e18_cells, lambda t: str(t[0]), N_MIN, "j")
    analysis_sign = analyze_descriptor(raw, e18_cells, lambda t: "+" if t[1] > 0 else "-", N_MIN, "sign")
    analysis_op = analyze_descriptor(raw, e18_cells, lambda t: t[3], N_MIN, "op_i")
    for a in (analysis_j, analysis_sign, analysis_op):
        print("%s: n_analyzed=%d n_excluded=%d n_substantial=%d n_negligible=%d tier=%s"
              % (a["descriptor"], a["n_analyzed"], a["n_excluded"],
                 a["n_substantial_explanation"], a["n_negligible_explanation"], a["tier"]))
    return {"j": analysis_j, "sign": analysis_sign, "op_i": analysis_op}


def write_output(raw, e18_cells, equivalence_meta, tie_stats):
    analysis = analyze_and_report(raw, e18_cells)
    raw_events = {
        "%d,%d" % key: [[j, dj, err, op, bool(r)] for (j, dj, err, op, r) in obs]
        for key, obs in raw.items()
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "experiment": "discrete_corruption_descriptor_sweep",
            "contract": "contract_photonics_discrete_corruption_descriptor_2026-08-24.md",
            "description": ("E20: within E18's R_i=False cells, do j (which "
                             "lane-0 component deviates most), sign(delta_j), "
                             "or op_i (QSUB/ROTC_thirds/ROTC_plain) stratify "
                             "P(R_{i+1}), and how much of the outcome variance "
                             "does each explain (eta-squared, Amendment 5 round "
                             "2)? Deterministic replay of E18/E19's exact "
                             "300,000 trials. Three separate univariate "
                             "descriptors, not a joint model (contract SS1)."),
            "seed": SEED, "n_trials": N_TRIALS, "sigma_det": SIGMA_DET,
            "n_min": N_MIN, "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
            "equivalence_check": equivalence_meta,
            "tie_diagnostics": tie_stats,
            "analysis": analysis,
            "raw_events": raw_events,
        }, f, indent=1)
    print("wrote", OUT)


def reanalyze_only():
    """Amendment 5 (round 2): recompute the analysis block from the
    already-frozen raw_events in an existing output JSON -- no
    resimulation, no new equivalence/replay-fidelity check (those govern
    the simulation, which is unchanged)."""
    with open(OUT) as f:
        prev = json.load(f)
    e18_cells = load_e18_material_cells()
    raw = defaultdict(list)
    for key_str, events in prev["raw_events"].items():
        pair_id, m0_ip1 = (int(x) for x in key_str.split(","))
        raw[(pair_id, m0_ip1)] = [(j, dj, err, op, r) for j, dj, err, op, r in events]
    print("reanalyzing %d cells from frozen raw_events (eta-squared, round 2)..." % len(raw))
    write_output(raw, e18_cells, prev["equivalence_check"], prev["tie_diagnostics"])


if __name__ == "__main__":
    if "--reanalyze-only" in sys.argv:
        reanalyze_only()
    else:
        main()
