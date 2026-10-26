"""Contract §9 program order, stages 0-6: pins, conformance, EQ-3, cells under both views, Pareto, capability tasks, mutants."""
import hashlib
from pathlib import Path
import campaign, conform, gates, joins, mutants, mutants2, refs, test_lu
from account import Ledger
from events import P4096, W31

REPO = Path(__file__).resolve().parents[3]
CONV_A, CONV_B, CONV_S = ("B-", "E-"), ("B-", "E-"), ("Horner", "Bezier", "TS", "FD", "PH")   # sequential: exact names


def pins():
    """Stage 0: every reference pin (hash-verified on load) and, when present, every PINS.sha256 line."""
    for n in refs.PINS:
        refs.load(n)
    f = Path(__file__).resolve().parent / "PINS.sha256"
    if not f.exists():
        return {"references": "OK", "PINS.sha256": "ABSENT"}
    bad = [p for h, p in (ln.split("  ", 1) for ln in f.read_text().splitlines() if ln.strip())
           if hashlib.sha256((REPO / p.strip()).read_bytes()).hexdigest() != h]
    return {"references": "OK", "PINS.sha256": "OK" if not bad else "MISMATCH", "mismatched": bad}


def conformance():
    out = {}
    for f in test_lu.TESTS:
        try:
            f()
            out[f.__name__] = "PASS"
        except Exception as e:  # noqa: BLE001
            out[f.__name__] = "FAIL: %r" % (e,)
    return out


def is_conv(name, conv):
    """Entries ending in "-" are family prefixes (B-, E-); all others are exact arm names (PHFD is a control, not "PH")."""
    return any(name.startswith(c) if c.endswith("-") else name == c for c in conv)


def arms_view(rows, conv, status_key="statuses"):
    return {r["arm"]: {"total": r["total"], "all_ok": all(s == "OK" for s in r[status_key]) and r["prep"] is None,
                       "role": "conventional" if is_conv(r["arm"], conv) and r["statuses"] and r["statuses"][0] != "NOT_APPLICABLE"
                       else "other"} for r in rows}


def pareto(view, cands):
    return {"comparator": gates.comparator(view), "virtual_best": gates.virtual_best(view), "conventional_frontier": gates.frontier(view),
            "candidates": {c: gates.evaluate(view, c) for c in cands if c in view}}


def run_cells():
    R = {"pareto": {}, "equivalence": {}}
    for prof in (P4096, W31):
        a, _ = campaign.cell_a(prof)
        b, s = campaign.cell_b(prof), campaign.seq(prof)
        R[prof.name] = {"cell_a": a, "cell_b": b, "sequential": s}
        if prof is P4096:
            R["pareto"]["cell_a"] = pareto(arms_view(a, CONV_A), ("C1", "C2"))
            R["pareto"]["cell_b"] = pareto(arms_view(b, CONV_B), ("C1",))
            by = {r["arm"]: r for r in a}
            R["equivalence"]["EQ-1"] = by["C1"]["P"] == by["B-PH"]["P"] and by["C1"]["Q"] == by["B-PH"]["Q"] and by["C1"]["peaks"] == by["B-PH"]["peaks"]
            for curve in ("PH3", "PH5"):
                for tape in ("S1", "S2", "S3"):
                    rows = [r for r in s if r["curve"] == curve and r["tape"] == tape]
                    R["pareto"]["seq_%s_%s" % (curve, tape)] = pareto(arms_view(rows, CONV_S), ("C1", "C2"))
                    by = {r["arm"]: r for r in rows}
                    R["equivalence"]["EQ-2_%s_%s" % (curve, tape)] = all(by["C1"][k] == by["PHFD"][k] for k in ("P", "Q", "peaks", "attempt"))
    return R


def eq3(R):
    return sum(r["mismatches"] for k in ("cell_a", "cell_b", "sequential") for r in R[P4096.name][k])


def capability():
    cap = {n: getattr(joins, n)() for n in ("s4", "s5", "s6", "loops", "phi_bad")}
    cap["retiming"] = joins.retiming()
    cap["controls_e1_mismatches"] = conform.controls_e1()
    return {k: {a: b for a, b in v.items() if a not in ("ledger", "ledgers")} if isinstance(v, dict) else v for k, v in cap.items()}


# How each mutant is exercised: "patched" = the real implementation is altered at run time and the detector must fail;
# "state-perturbed" = real arm state altered; "check-only" = real code on a control, no altered code;
# "fixture-only" = the altered quantity is data or an oracle-side formula, so it validates the fixture, not implementation fault detection.
LEVEL = {"X-1": "patched", "X-2": "patched", "X-3": "fixture-only", "X-4": "fixture-only", "X-5": "check-only", "X-6": "fixture-only",
         "X-7": "patched", "X-8": "patched", "X-9": "patched", "X-10": "fixture-only", "X-11": "patched", "X-12": "patched",
         "X-13": "patched", "X-14": "check-only", "X-15": "patched", "X-16": "patched", "X-17": "check-only", "X-18": "check-only",
         "X-19": "fixture-only", "X-20": "check-only", "X-21": "state-perturbed", "X-22": "fixture-only", "X-23": "check-only",
         "X-24": "check-only"}


def mutant_suite():
    out = {}
    for k, f in list(mutants.MUTANTS.items()) + list(mutants2.MUTANTS2.items()):
        killed, det = f()
        out[k] = {"killed": bool(killed), "detector": det, "level": LEVEL[k]}
    return out


def build():
    R = {"stage0_pins": pins(), "stage1_conformance": conformance()}
    R["stage1_prep_targets_mismatch"] = None
    cells = run_cells()
    R.update(cells)
    R["stage1_prep_targets_mismatch"] = conform.prep_targets(cells[P4096.name]["cell_a"])
    R["stage1_q_division_free_violations"] = conform.q_division_free(cells[P4096.name]["cell_a"] + cells[P4096.name]["cell_b"])
    R["stage2_eq3_mismatches"] = eq3(cells)
    R["stage3_w31_cell_a_certified_mismatches"] = conform.w31_cell_a()
    R["stage5_capability"] = capability()
    R["stage6_mutants"] = mutant_suite()
    R["pending_acceptance_hooks"] = {
        "W31_sequential_stage_table": "PENDING_INDEPENDENT_DERIVATION; the W31 sequential observations above are uncertified outputs, not expectations",
        "W31_CellB_stage_table": "PENDING_INDEPENDENT_DERIVATION; the W31 Cell B observations above are uncertified outputs, not expectations"}
    R["counted_operations"] = Ledger.GRAND[0]
    return R


def verdict(R):
    ok = (all(v == "PASS" for v in R["stage1_conformance"].values()) and not R["stage1_prep_targets_mismatch"]
          and not R["stage1_q_division_free_violations"] and R["stage2_eq3_mismatches"] == 0
          and not R["stage3_w31_cell_a_certified_mismatches"] and R["stage0_pins"]["PINS.sha256"] == "OK"
          and R["equivalence"]["EQ-1"] and all(v for k, v in R["equivalence"].items() if k.startswith("EQ-2"))
          and all(m["killed"] for m in R["stage6_mutants"].values())
          and not any(v.get("mismatches") for v in R["stage5_capability"].values() if isinstance(v, dict))
          and not R["stage5_capability"]["controls_e1_mismatches"] and R["counted_operations"] <= 1000000)
    return bool(ok)
