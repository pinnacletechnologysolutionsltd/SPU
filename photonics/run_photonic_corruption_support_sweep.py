#!/usr/bin/env python3
"""run_photonic_corruption_support_sweep.py — E21 of
contract_photonics_corruption_support_2026-08-24.md: does corruption
*support* S_i = #{k in 0..3: rec_i[k]!=qr_i[k]} (how many lane-0
components deviate, not which one or by how much) stratify P(R_{i+1})
beyond m0_{i+1}, and does conditioning on it attenuate E20's small op_i
association (support-conditioned attenuation, not formal mediation --
op_i -> S_i -> R_{i+1} is not established as a causal chain)?

Deterministic replay of E18/E19/E20's exact 300,000 trials (same SEED,
sigma_det=3e-5, M=2). One additive instrumentation:
run_chain_boundary_noisy_m0trace_with_support extends E20's frozen
*_with_descriptor to also expose S and the corruption mask -- verified
equivalent to E20's (m0, g_ok, err, j, delta_j) sequence via a hard gate
before being trusted (contract SS4/SS7).

Gate 0 (m0_i confound check) and Gate 5 (S_i support-conditioned
attenuation) both use a pooled, stratified eta2 -- SS_between and
SS_total are summed ACROSS strata first, divided once at the end -- as
the "conditional eta2" for op_i. This is deliberately not an n-weighted
average of per-stratum eta2 values (a different, non-equivalent
estimator) and not a category-share-weighted average (that was E20
round 1's tautological A_D mistake). Both report an attenuation ratio =
conditional/marginal eta2 against E20's frozen per-cell op_i eta2,
restricted to E20's 7 omnibus-significant cells. Both are descriptive
conditional re-analyses of those already-frozen cells, not new
significance tests -- the 4/7 majority bars classify attenuation, they
are not p-value-based claims. Gate 0 is reported first and takes
explicit interpretive precedence over the S_i/Gate-5 conclusions: if
op_i's E20 association was itself substantially a m0_i confound, "S_i
mediates/explains op_i" would be the wrong headline.
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

from run_photonic_correlation_mechanism_sweep import (  # noqa: E402
    M2_BOUNDARIES, _bin_width2, _bin_width4,
)
from run_photonic_regen_boundary_placement_sweep import (  # noqa: E402
    gen_block, M_K, BAND, SEED,
)
from run_photonic_corrupted_state_sufficiency_sweep import (  # noqa: E402
    load_e18_material_cells,
)
from run_photonic_discrete_corruption_descriptor_sweep import (  # noqa: E402
    run_chain_boundary_noisy_m0trace_with_descriptor, op_type,
    chi2_sf, omnibus_chi2, analyze_descriptor,
)
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

SIGMA_DET = 3e-5
N_TRIALS = int(os.environ.get("PHOTONIC_TRIALS", "300000"))
N_MIN = 100
N_EQUIV_CHECK = 2000
E20_FROZEN = os.path.join(
    REPO, "results", "sweeps", "discrete_corruption_descriptor_sweep_frozen_v1_2026-08-24.json")


def run_chain_boundary_noisy_m0trace_with_support(pb, block, boundaries, sigma_det, rng):
    """Identical control flow to E20's *_with_descriptor, additionally
    returns S (support count) and the 4-component corruption mask.
    Returns [(m0, g_ok, err, j, delta_j, tie, S, mask), ...] per boundary."""
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
            mask = tuple(1 if d != 0 else 0 for d in devs)
            S = sum(mask)
            max_abs = max(absdevs)
            tie = sum(1 for a in absdevs if a == max_abs) > 1
            j = max(range(4), key=lambda k: (absdevs[k], -k))
            delta_j = devs[j]
            err = absdevs[j]
            trace.append((m0_here, g_ok, err, j, delta_j, tie, S, mask))
            for lane in range(13):
                le = pb._load_exp(rec[lane])
                f = pb.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            nd_last = None
    return trace


def equivalence_check(n_check=N_EQUIV_CHECK):
    """Hard gate: confirm (m0, g_ok, err, j, delta_j) from the new
    support-instrumented trace function is bit-identical to E20's frozen
    run_chain_boundary_noisy_m0trace_with_descriptor, on matched inputs."""
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
        trace_old = run_chain_boundary_noisy_m0trace_with_descriptor(
            pb, blk_old, M2_BOUNDARIES, SIGMA_DET, rng_old)
        trace_new = run_chain_boundary_noisy_m0trace_with_support(
            pb, blk_new, M2_BOUNDARIES, SIGMA_DET, rng_new)
        for (m0_o, ok_o, err_o, j_o, dj_o, _t_o), (m0_n, ok_n, err_n, j_n, dj_n, _t_n, S_n, mask_n) \
                in zip(trace_old, trace_new):
            if (m0_o, ok_o, err_o, j_o, dj_o) != (m0_n, ok_n, err_n, j_n, dj_n):
                mismatches += 1
            if S_n != sum(mask_n):
                mismatches += 1
        checked += 1
    return mismatches, checked


def collect_support_stratified(sigma_det, n_trials, master, target_cells):
    """Replays n_trials trials (same clean-arrival rule as E18-E20), and
    for each (pair_id, m0_ip1) in target_cells, among R_i=False
    observations, records the raw tuple (m0_i, op_i, S_i, mask_i, r_ip1)."""
    pb = PhotonicQuadrayBackend(deltaT=2.0)
    raw = defaultdict(list)
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, 16)
        if blk is None:
            continue
        trace = run_chain_boundary_noisy_m0trace_with_support(
            pb, blk, M2_BOUNDARIES, sigma_det, rng)
        clean = True
        n_pairs = len(trace) - 1
        for pair_id in range(n_pairs):
            if not clean:
                break
            m0_i, r_i, _err_i, _j_i, _dj_i, _tie_i, S_i, mask_i = trace[pair_id]
            m0_ip1, r_ip1 = trace[pair_id + 1][0], trace[pair_id + 1][1]
            key = (pair_id, m0_ip1)
            if not r_i and key in target_cells:
                op_i = op_type(blk, M2_BOUNDARIES[pair_id])
                raw[key].append((m0_i, op_i, S_i, mask_i, r_ip1))
            if not r_i:
                clean = False
        accepted += 1
    return raw


def load_e20_significant_cells():
    d = json.load(open(E20_FROZEN))
    cells = {}
    for c in d["analysis"]["op_i"]["cells"]:
        if not c.get("excluded") and c["omnibus_significant"]:
            cells[(c["pair_id"], c["bin"])] = c["eta2"]
    return cells


def load_e20_raw_op_sequences():
    """Amendment 5: E20's frozen raw_events, reduced to the ordered
    (op_i, r_ip1) sequence per cell -- for the strengthened replay
    fidelity check (element-wise, not just aggregate counts)."""
    d = json.load(open(E20_FROZEN))
    out = {}
    for key_str, events in d["raw_events"].items():
        pair_id, m0_ip1 = (int(x) for x in key_str.split(","))
        out[(pair_id, m0_ip1)] = [(op, bool(r)) for (_j, _dj, _err, op, r) in events]
    return out


def bin_m0_for_op_sufficiency(triples, n_min):
    """triples: (m0_i, op_i, r_ip1) for one cell. Deterministic hierarchy
    (contract SS3): exact -> width2 -> width4 -> exclude, decided ONLY by
    whether >=2 op_i categories clear n_min within the candidate bin --
    never by the outcome. Returns a list of bins, each a list of
    (op_i, r_ip1) pairs."""
    def cat_ok(items):
        counts = defaultdict(int)
        for op, _r in items:
            counts[op] += 1
        return sum(1 for n in counts.values() if n >= n_min) >= 2

    by_exact = defaultdict(list)
    for m0, op, r in triples:
        by_exact[m0].append((op, r))
    resolved = []
    seen = set()
    for m0 in sorted(by_exact):
        if cat_ok(by_exact[m0]):
            resolved.append(by_exact[m0])
            seen.add(m0)
    remaining = sorted(m for m in by_exact if m not in seen)
    w2_items = defaultdict(list)
    w2_members = defaultdict(list)
    for m in remaining:
        w2_items[_bin_width2(m)].extend(by_exact[m])
        w2_members[_bin_width2(m)].append(m)
    for b2, items in sorted(w2_items.items()):
        if cat_ok(items):
            resolved.append(items)
            seen.update(w2_members[b2])
    remaining2 = sorted(m for m in by_exact if m not in seen)
    w4_items = defaultdict(list)
    for m in remaining2:
        w4_items[_bin_width4(m)].extend(by_exact[m])
    for b4, items in sorted(w4_items.items()):
        if cat_ok(items):
            resolved.append(items)
        # else: excluded, per the frozen hierarchy -- not widened further
    return resolved


def pooled_eta2_op(strata, n_min):
    """strata: list of lists of (op_i, r_ip1). Pooled/partial eta2 for
    op_i, controlling for the stratifying variable: SS_between and
    SS_total are summed ACROSS strata before dividing (not an average of
    per-stratum eta2, and not a category-share-weighted mean -- avoids
    both E20 round 1's tautology and Simpson's-paradox-style bias)."""
    ss_between_tot = 0.0
    ss_total_tot = 0.0
    n_retained = 0
    n_strata_used = 0
    for items in strata:
        counts = defaultdict(lambda: [0, 0])
        for op, r in items:
            counts[op][1] += 1
            if r:
                counts[op][0] += 1
        included = {c: v for c, v in counts.items() if v[1] >= n_min}
        if len(included) < 2:
            continue
        n_s = sum(v[1] for v in included.values())
        cat_p = {c: v[0] / v[1] for c, v in included.items()}
        p_bar = sum((v[1] / n_s) * cat_p[c] for c, v in included.items())
        ss_between = sum(v[1] * (cat_p[c] - p_bar) ** 2 for c, v in included.items())
        ss_total = n_s * p_bar * (1 - p_bar)
        ss_between_tot += ss_between
        ss_total_tot += ss_total
        n_retained += n_s
        n_strata_used += 1
    eta2 = ss_between_tot / ss_total_tot if ss_total_tot > 0 else float("nan")
    return eta2, n_retained, n_strata_used


def gate0_confound_check(raw, sig_cells, n_min):
    results = []
    for key, marginal_eta2 in sig_cells.items():
        triples = [(m0_i, op_i, r) for (m0_i, op_i, _S, _mask, r) in raw.get(key, [])]
        bins = bin_m0_for_op_sufficiency(triples, n_min)
        cond_eta2, n_retained, n_bins = pooled_eta2_op(bins, n_min)
        ratio = cond_eta2 / marginal_eta2 if marginal_eta2 else float("nan")
        results.append({
            "pair_id": key[0], "bin": key[1], "marginal_eta2": marginal_eta2,
            "conditional_eta2": cond_eta2, "attenuation_ratio": ratio,
            "n_retained": n_retained, "n_bins_used": n_bins, "n_total": len(triples),
        })
    n_confound = sum(1 for r in results if r["attenuation_ratio"] < 0.3)
    n_survives = sum(1 for r in results if r["attenuation_ratio"] >= 0.7)
    if n_confound >= 4:
        verdict = "op_i association substantially accounted for by m0_i"
    elif n_survives >= 4:
        verdict = "op_i association survives m0_i conditioning"
    else:
        verdict = "mixed"
    return {"n_cells": len(sig_cells), "n_confound": n_confound,
            "n_survives": n_survives, "verdict": verdict, "cells": results}


def gate5_attenuation(raw, sig_cells, n_min):
    """Support-conditioned attenuation (Amendment 1 -- not formal
    mediation). Descriptive re-analysis of E20's already-frozen 7 cells
    (Amendment 3), not a new significance test."""
    results = []
    for key, marginal_eta2 in sig_cells.items():
        obs = raw.get(key, [])
        strata = [
            [(op_i, r) for (_m0, op_i, S, _mask, r) in obs if S == 1],
            [(op_i, r) for (_m0, op_i, S, _mask, r) in obs if S >= 2],
        ]
        cond_eta2, n_retained, n_strata = pooled_eta2_op(strata, n_min)
        ratio = cond_eta2 / marginal_eta2 if marginal_eta2 else float("nan")
        results.append({
            "pair_id": key[0], "bin": key[1], "marginal_eta2": marginal_eta2,
            "conditional_eta2": cond_eta2, "attenuation_ratio": ratio,
            "n_retained": n_retained, "n_strata_used": n_strata, "n_total": len(obs),
        })
    n_attenuated = sum(1 for r in results if r["attenuation_ratio"] < 0.3)
    n_survives = sum(1 for r in results if r["attenuation_ratio"] >= 0.7)
    if n_attenuated >= 4:
        verdict = "support accounts for most of the operation-type association"
    elif n_survives >= 4:
        verdict = "operation-type association survives support conditioning"
    else:
        verdict = "mixed"
    return {"n_cells": len(sig_cells), "n_attenuated": n_attenuated,
            "n_survives": n_survives, "verdict": verdict, "cells": results}


def combined_interpretation(s_primary, gate0, gate5):
    """Amendment 4: Gate 0 (the m0_i confound check) takes explicit
    interpretive precedence over outcomes 1-3."""
    s_tier = s_primary["tier"]
    s_substantial = "explains most" in s_tier
    s_negligible = "does not explain" in s_tier
    if gate0["verdict"] == "op_i association substantially accounted for by m0_i":
        return ("Precedence (outcome 0): E20's op_i association was substantially "
                "accounted for by m0_i (the pre-boundary state Gate 0 conditions on, "
                "not m0_{i+1}) -- outcomes 1-3 below are secondary/descriptive, not "
                "primary mechanistic conclusions.")
    if s_substantial and gate5["verdict"] == "support accounts for most of the operation-type association":
        return "op_i was exposing corruption spread (outcome 1)."
    if s_substantial and gate5["verdict"] == "operation-type association survives support conditioning":
        return ("Both corruption geometry and operation type contribute independently "
                "(outcome 2) -- motivates a future joint op_i x S_i model.")
    if s_negligible:
        return ("Spread hypothesis falsified: op_i's association is real but not explained "
                "by component count (outcome 3).")
    return "Mixed / inconclusive -- see per-gate verdicts."


OUT = os.path.join(REPO, "results", "sweeps", "corruption_support_sweep.json")


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
    sig_cells = load_e20_significant_cells()
    print("loaded %d E18 cells, %d E20 op_i-significant cells" % (len(e18_cells), len(sig_cells)))
    print("replaying %d trials at sigma_det=%g..." % (N_TRIALS, SIGMA_DET), flush=True)
    raw = collect_support_stratified(SIGMA_DET, N_TRIALS, master, set(e18_cells))

    fidelity_ok = True
    if N_TRIALS == 300000:
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

        # Amendment 5: strengthened check -- ordered (op_i, r_ip1) sequence
        # per cell must match E20's frozen raw_events element-wise, not
        # just in aggregate count (catches an ordering/indexing bug a
        # matching count alone would miss).
        e20_seqs = load_e20_raw_op_sequences()
        seq_ok = True
        for key in e18_cells:
            got_seq = [(op, bool(r)) for (_m0, op, _S, _mask, r) in raw.get(key, [])]
            expected_seq = e20_seqs.get(key, [])
            if got_seq != expected_seq:
                seq_ok = False
                first_diff = next((i for i in range(min(len(got_seq), len(expected_seq)))
                                    if got_seq[i] != expected_seq[i]), min(len(got_seq), len(expected_seq)))
                print("ORDERED-SEQUENCE MISMATCH: cell %s at index %d (len got=%d expected=%d)"
                      % (key, first_diff, len(got_seq), len(expected_seq)))
        if not seq_ok:
            print("HALT: ordered-sequence replay fidelity check FAILED")
            sys.exit(1)
        print("ordered-sequence replay fidelity check PASSED (%d cells match E20 element-wise)"
              % len(e18_cells))
    else:
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
        print("smoke proportionality check PASSED (%d cells within tolerance)" % len(e18_cells))

    s_primary = analyze_descriptor(raw, e18_cells, lambda t: "1" if t[2] == 1 else "2+", N_MIN, "S_primary")
    s_4way = analyze_descriptor(raw, e18_cells, lambda t: str(t[2]), N_MIN, "S_4way_diagnostic")
    print("S_primary: n_analyzed=%d n_excluded=%d n_substantial=%d n_negligible=%d tier=%s"
          % (s_primary["n_analyzed"], s_primary["n_excluded"],
             s_primary["n_substantial_explanation"], s_primary["n_negligible_explanation"],
             s_primary["tier"]))

    gate0 = gate0_confound_check(raw, sig_cells, N_MIN)
    print("Gate 0 (m0_i confound): n_confound=%d n_survives=%d verdict=%s"
          % (gate0["n_confound"], gate0["n_survives"], gate0["verdict"]))

    gate5 = gate5_attenuation(raw, sig_cells, N_MIN)
    print("Gate 5 (S_i support-conditioned attenuation): n_attenuated=%d n_survives=%d verdict=%s"
          % (gate5["n_attenuated"], gate5["n_survives"], gate5["verdict"]))

    interpretation = combined_interpretation(s_primary, gate0, gate5)
    print("Combined interpretation:", interpretation)

    raw_events = {
        "%d,%d" % key: [[m0, op, S, list(mask), bool(r)] for (m0, op, S, mask, r) in obs]
        for key, obs in raw.items()
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "experiment": "corruption_support_sweep",
            "contract": "contract_photonics_corruption_support_2026-08-24.md",
            "description": ("E21: does corruption support S_i (how many "
                             "lane-0 components deviate) stratify "
                             "P(R_{i+1}), and does conditioning on it "
                             "attenuate E20's op_i association (Gate 5, "
                             "support-conditioned attenuation, not formal "
                             "mediation), controlling for the m0_i confound "
                             "(Gate 0, given interpretive precedence)? "
                             "Deterministic replay of E18-E20's exact "
                             "300,000 trials."),
            "seed": SEED, "n_trials": N_TRIALS, "sigma_det": SIGMA_DET,
            "n_min": N_MIN, "band": list(BAND), "M_K16": M_K[16], "deltaT_K": 2.0, "K": 16,
            "equivalence_check": {"trials_checked": checked, "mismatches": mismatches},
            "s_primary": s_primary, "s_4way_diagnostic": s_4way,
            "gate0_m0i_confound": gate0, "gate5_support_conditioned_attenuation": gate5,
            "combined_interpretation": interpretation,
            "raw_events": raw_events,
        }, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
