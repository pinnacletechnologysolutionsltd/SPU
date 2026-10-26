#!/usr/bin/env python3
"""Frozen P1b preflight and bounded exact noisy-decision comparison."""

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from d4_decision_p1 import CAPACITIES, train
from d4_decision_p1b_data import ARMS, PROFILES, prepare, samples
from d4_decision_p1b_controls import controls
from d4_decision_p1b_metrics import evaluate, aggregate
from d4_decision_p1b_audit import check_row, check_aggregate, check_controls
from d4_decision_p1b_preflight import check

ROOT = Path(__file__).resolve().parents[2]


def sources():
    files = sorted(Path(__file__).parent.glob("d4_decision_p1*.py"))
    files += [Path(__file__), Path(__file__).with_name("d4_canonical_exact.py")]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def run(preflight, old_learner, checkpoint=None):
    before = sources()
    prepared = prepare()
    reps, folds, orbits, canon, transforms, inverses, observations, projection_report = prepared
    preflight_report = check(prepared, old_learner)
    result = {"verdict": "PASS_PREFLIGHT" if preflight else "PASS_SOFTWARE_EXPERIMENT",
              "projection": projection_report, "preflight": preflight_report,
              "controls": controls(reps, folds, orbits, observations),
              "configuration": {"profiles_numerators": PROFILES, "fixed_point_scale": 16,
                  "arms": ARMS, "capacities": CAPACITIES, "epochs": 12,
                  "som_ring_radii": [2, 1, 0], "equal_base_profile_total_weight": 384,
                  "rounding": "nearest_ties_to_even", "quantized_bits_per_node": 18,
                  "noisy_bits_per_node": 34, "primary": "equal_base_equal_profile",
                  "secondary": "P1_base_orbit_weight", "folds": folds,
                  "latent_label": "P1_norm_bands_12_30", "canonicalizer_cost": "unmeasured",
                  "quantizer_cost": "unmeasured", "runner_gap_units": "squared_arm_integer_units",
                  "training_workspace_cost": "unmeasured", "rtl_or_silicon_claim": False},
              "source_hashes": before}
    result["control_audit"] = check_controls(result["controls"], reps, observations, orbits)
    if not preflight:
        rows, prediction_checks = [], 0
        for fold, held_out in enumerate(folds):
            training_ranks = tuple((rank, rep) for rank, rep in enumerate(reps) if rep not in held_out)
            test_ranks = tuple((rank, rep) for rank, rep in enumerate(reps) if rep in held_out)
            assert set(r for r, _ in training_ranks).isdisjoint(r for r, _ in test_ranks)
            for arm in ARMS:
                training = samples(arm, training_ranks, observations, canon)
                bounds = (-128, 127) if "noisy" in arm else (-4, 4)
                for capacity in CAPACITIES:
                    prototypes, labels, evaluations, updates = train(
                        training, capacity, arm.endswith("som"), bounds, "noisy" not in arm)
                    row = {"fold": fold, "arm": arm, "capacity": capacity,
                           "codebook_bits": capacity * (34 if "noisy" in arm else 18),
                           "prototypes": prototypes, "node_labels": labels,
                           "training_records": len(training), "training_total_weight": 384 * len(training_ranks),
                           "training_records_before_exact_merge": len(training_ranks) * (384 if "augmented" in arm else 2),
                           "training_distance_evaluations": evaluations, "coordinate_updates": updates,
                           "profiles": evaluate(arm, prototypes, labels, test_ranks, orbits, canon,
                                                transforms, inverses, observations)}
                    prediction_checks += check_row(row, reps, observations, canon, orbits)
                    rows.append(row)
                    if checkpoint is not None:
                        checkpoint.write(json.dumps(row, sort_keys=True) + "\n")
                        checkpoint.flush()
                print(f"fold={fold} arm={arm} complete", flush=True)
        totals = aggregate(rows, ARMS, CAPACITIES)
        assert len(rows) == 240 and len(totals) == 48
        result.update({"fold_results": rows, "aggregate": totals,
                       "independent_audit": {"predictions_recomputed": prediction_checks,
                                             **check_aggregate(rows, totals)}})
    assert before == sources(), "source drift during experiment"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--p1-before", type=Path, default=ROOT / "build/d4_canonical_decision_p1b/preparation_01/before/software/tests/d4_decision_p1.py")
    args = parser.parse_args()
    partial = args.output.with_suffix(".partial.jsonl")
    if args.output.exists() or (not args.preflight and partial.exists()):
        print(f"FAIL: evidence exists: {args.output}", file=sys.stderr)
        return 1
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with nullcontext(None) if args.preflight else partial.open("x") as checkpoint:
            result = run(args.preflight, args.p1_before, checkpoint)
        result["source_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        result["source_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except (AssertionError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL D4 P1b: {error}", file=sys.stderr)
        return 1
    print(result["verdict"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
