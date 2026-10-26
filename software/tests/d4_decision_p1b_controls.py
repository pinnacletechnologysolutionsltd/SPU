"""Observed-input controls and collision limits, with explicit evaluation weights."""

from collections import Counter
from fractions import Fraction

from d4_canonical_exact import norm
from d4_decision_p1_data import task_label
from d4_decision_p1_metrics import rational


def controls(reps, folds, orbits, observations):
    fold_of = {reps.index(rep): fold for fold, values in enumerate(folds) for rep in values}
    coordinates = {}
    profile_rows = []
    for profile in range(2):
        q_errors = noisy_errors = q_weighted = noisy_weighted = 0
        for rank, rep in enumerate(reps):
            truth, orbit_weight = task_label(rep), len(orbits[rep])
            for z, q in observations[rank, profile]:
                observed_norm = norm(z)
                noisy_label = 0 if observed_norm <= 12 * 256 else 1 if observed_norm <= 30 * 256 else 2
                q_errors += task_label(q) != truth
                noisy_errors += noisy_label != truth
                q_weighted += (task_label(q) != truth) * orbit_weight
                noisy_weighted += (noisy_label != truth) * orbit_weight
                counts = coordinates.setdefault(q, {"labels": Counter(), "weighted_labels": Counter(),
                                                    "folds": set(), "bases": set()})
                counts["labels"][truth] += 1
                counts["weighted_labels"][truth] += orbit_weight
                counts["folds"].add(fold_of[rank])
                counts["bases"].add(rank)
        profile_rows.append({"profile": profile, "quantized_norm_rule": rational(Fraction(q_errors, 10944)),
                             "noisy_norm_rule": rational(Fraction(noisy_errors, 10944)),
                             "quantized_norm_orbit_weighted": rational(Fraction(q_weighted, 192 * 3281)),
                             "noisy_norm_orbit_weighted": rational(Fraction(noisy_weighted, 192 * 3281))})
    errors = sum(sum(c["labels"].values()) - max(c["labels"].values()) for c in coordinates.values())
    weighted_errors = sum(sum(c["weighted_labels"].values()) - max(c["weighted_labels"].values())
                          for c in coordinates.values())
    conflicts = [{"q": q, "counts": dict(c["labels"]), "orbit_weighted_counts": dict(c["weighted_labels"]),
                  "folds": sorted(c["folds"]), "bases": sorted(c["bases"])}
                 for q, c in sorted(coordinates.items()) if len(c["labels"]) > 1]
    split_collisions = []
    for fold in range(5):
        shared = [c for c in coordinates.values() if fold in c["folds"] and len(c["folds"]) > 1]
        split_collisions.append({"fold": fold, "shared_train_test_projected_coordinates": len(shared),
                                 "shared_conflicting_coordinates": sum(len(c["labels"]) > 1 for c in shared)})
    assert errors > 0 and all(r["quantized_norm_rule"]["numerator"] > 0 for r in profile_rows[1:])
    return {"profiles": profile_rows, "latent_label_reference": rational(Fraction()),
            "empirical_quantized_input_majority_error": rational(Fraction(errors, 21888)),
            "empirical_quantized_input_orbit_weighted_majority_error": rational(Fraction(weighted_errors, 384 * 3281)),
            "majority_error_count": errors, "conflicting_coordinates": conflicts,
            "distinct_projected_coordinates": len(coordinates), "split_collisions": split_collisions,
            "equal_profile_mean": {key: rational(sum((Fraction(**p[key]) for p in profile_rows), Fraction()) / 2)
                                   for key in ("quantized_norm_rule", "noisy_norm_rule")}}
