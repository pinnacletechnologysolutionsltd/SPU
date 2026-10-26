#!/usr/bin/env python3
"""Five-fold exact D4 canonical decision comparison, with durable evidence."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

from d4_canonical_exact import GROUP, IDENTITY, STATES, act, compose
from d4_decision_p1 import CAPACITIES, MULTIPLIERS, train
from d4_decision_p1_data import dataset, samples, task_label
from d4_decision_p1_metrics import aggregate_rows, evaluate, rational


ARMS = (
    "canonical_som", "canonical_codebook",
    "raw_som", "raw_augmented_som",
    "raw_codebook", "raw_augmented_codebook",
)


def exact_controls(reps):
    label_checks = 0
    stabilizer_checks = 0
    for x in STATES:
        for w in GROUP:
            assert task_label(act(w, x)) == task_label(x)
            label_checks += 1
    for rep in reps:
        for multiplier in MULTIPLIERS:
            action = tuple(multiplier * value for value in rep)
            for w in GROUP:
                if act(w, rep) == rep:
                    assert act(w, action) == action
                    stabilizer_checks += 1
    assert label_checks == 629952
    inverses = {w: next(v for v in GROUP if compose(w, v) == IDENTITY and
                         compose(v, w) == IDENTITY) for w in GROUP}
    return inverses, label_checks, stabilizer_checks


def run():
    reps, folds, orbits, canon, transforms = dataset()
    inverses, label_checks, stabilizer_checks = exact_controls(reps)
    assert all(act(inverses[transforms[x]], canon[x]) == x for x in STATES)
    results = []
    for fold_index, held_out in enumerate(folds):
        train_reps = tuple(rep for rep in reps if rep not in set(held_out))
        assert len(train_reps) + len(held_out) == 57
        for arm in ARMS:
            training = samples(arm, train_reps, reps, orbits)
            assert sum(weight for _, _, weight in training) == 192 * len(train_reps)
            held_out_states = {state for rep in held_out for state in orbits[rep]}
            assert not held_out_states.intersection(point for point, _, _ in training)
            for capacity in CAPACITIES:
                prototypes, labels, training_evals, updates = train(
                    training, capacity, arm.endswith("som"))
                observed = evaluate(arm, prototypes, labels, held_out,
                                    orbits, canon, transforms, inverses)
                observed.update({
                    "fold": fold_index, "arm": arm, "capacity": capacity,
                    "codebook_bits": 18 * capacity,
                    "training_distance_evaluations": training_evals,
                    "coordinate_updates": updates,
                    "prototypes": prototypes, "node_labels": labels,
                })
                results.append(observed)

    aggregate = aggregate_rows(results, ARMS, CAPACITIES)
    assert len(results) == 180 and len(aggregate) == 36
    assert all(row["orbit_disagreement_count"] == 0 for row in aggregate
               if row["arm"].startswith("canonical"))
    return {
        "verdict": "PASS", "domain_count": len(STATES), "group_count": len(GROUP),
        "representative_count": len(reps), "fold_sizes": tuple(map(len, folds)),
        "held_out_state_count": 3281, "label_invariance_checks": label_checks,
        "stabilizer_action_checks": stabilizer_checks,
        "capacity_axis": CAPACITIES, "arms": ARMS,
        "configuration": {
            "label_norm_ranges": ((0, 12), (14, 30), (32, 64)),
            "train_epochs": 12, "som_ring_radii": (2, 1, 0),
            "prototype_bits": 16, "class_bits": 2,
            "augmented_orbit_total_weight": 192,
            "rounding": "nearest_integer_ties_to_even_after_exact_weighted_sum",
        },
        "direct_norm_rule": {"prototypes": 0, "decision_error": rational(Fraction()),
                             "operations_per_input": {"square": 4, "add": 3,
                                                      "compare": 2}},
        "fold_results": results, "aggregate": aggregate,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        print(f"FAIL: evidence exists: {args.output}", file=sys.stderr)
        return 1
    try:
        result = run()
        result["source_revision"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip()
        result["source_dirty"] = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True).strip())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except (AssertionError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: D4 canonical decision P1: {error}", file=sys.stderr)
        return 1
    print("PASS: D4 P1 exact five-fold comparison; 3281 held-out states, "
          "six arms, six capacities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
