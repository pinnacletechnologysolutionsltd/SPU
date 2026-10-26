"""Exact held-out metrics with equal-base and base-orbit weights kept separate."""

from collections import Counter
from fractions import Fraction

from d4_canonical_exact import GROUP, act
from d4_decision_p1 import MULTIPLIERS, winner
from d4_decision_p1_data import task_label
from d4_decision_p1_metrics import rational, median
from d4_decision_p1b_data import point_for


def evaluate(arm, prototypes, labels, ranks, orbits, canon, transforms, inverses, observations):
    profiles = []
    for profile in range(2):
        confusion = [[0] * 3 for _ in range(3)]
        errors, gaps = [], Counter()
        disagreements = action_errors = checks = weighted_wrong = total_weight = 0
        displacement = 0
        for rank, rep in ranks:
            truth = task_label(rep)
            predictions, wrong = [], 0
            seed_action = None
            for orientation, (z, q) in enumerate(observations[rank, profile]):
                point = point_for(arm, z, q, canon)
                best, distance, runner = winner(point, prototypes)
                predicted = labels[best]
                confusion[truth][predicted] += 1
                predictions.append(predicted)
                wrong += predicted != truth
                if runner is not None:
                    gaps[runner - distance] += 1
                action = tuple(MULTIPLIERS[predicted] * value for value in q)
                true_action = tuple(MULTIPLIERS[truth] * value for value in q)
                action_errors += action != true_action
                displacement += sum((MULTIPLIERS[truth] * (16 * a - b)) ** 2
                                    for a, b in zip(q, z))
                if arm.startswith("canonical"):
                    recovered = act(inverses[transforms[q]], tuple(
                        MULTIPLIERS[predicted] * v for v in canon[q]))
                    assert recovered == action
                    if seed_action is None:
                        seed_action = action
                    assert action == act(GROUP[orientation], seed_action)
                    checks += 1
            errors.append({"base": rank, "wrong": wrong, "orbit_weight": len(orbits[rep])})
            weighted_wrong += wrong * len(orbits[rep])
            total_weight += 192 * len(orbits[rep])
            disagreements += sum(p != predictions[0] for p in predictions)
            if arm.startswith("canonical"):
                assert len(set(predictions)) == 1
        count = 192 * len(ranks)
        profiles.append({"profile": profile, "observations": count, "base_errors": errors,
                         "confusion": confusion, "equal_base_error": rational(Fraction(
                             sum(e["wrong"] for e in errors), count)),
                         "base_orbit_weighted_error": rational(Fraction(weighted_wrong, total_weight)),
                         "orbit_disagreement_count": disagreements,
                         "action_class_error_count": sum(e["wrong"] for e in errors),
                         "quantized_action_error_count": action_errors,
                         "true_action_quantization_squared_displacement_sum": rational(Fraction(displacement, 256)),
                         "canonical_action_equivariance_checks": checks,
                         "inference_distance_evaluations": count * len(prototypes),
                         "runner_gap_histogram": dict(sorted(gaps.items())),
                         "runner_gap_mean": rational(Fraction(sum(g * n for g, n in gaps.items()),
                                                               sum(gaps.values()))) if gaps else None,
                         "runner_gap_median": rational(median(list(gaps.elements()))) if gaps else None})
    return profiles


def aggregate(results, arms, capacities):
    rows = []
    for arm in arms:
        for capacity in capacities:
            subset = [r for r in results if r["arm"] == arm and r["capacity"] == capacity]
            assert len(subset) == 5
            profiles = []
            for profile in range(2):
                observations = [r["profiles"][profile] for r in subset]
                errors = [e for o in observations for e in o["base_errors"]]
                assert len(errors) == len({e["base"] for e in errors}) == 57
                gaps = Counter()
                for o in observations:
                    gaps.update(o["runner_gap_histogram"])
                profiles.append({"profile": profile, "observations": 10944,
                    "equal_base_error": rational(Fraction(sum(e["wrong"] for e in errors), 10944)),
                    "base_orbit_weighted_error": rational(Fraction(
                        sum(e["wrong"] * e["orbit_weight"] for e in errors), 192 * 3281)),
                    "confusion": [[sum(o["confusion"][t][p] for o in observations)
                                   for p in range(3)] for t in range(3)],
                    "runner_gap_histogram": dict(sorted(gaps.items())),
                    "runner_gap_mean": rational(Fraction(sum(g * n for g, n in gaps.items()),
                                                          sum(gaps.values()))) if gaps else None,
                    "runner_gap_median": rational(median(list(gaps.elements()))) if gaps else None,
                    **{key: sum(o[key] for o in observations) for key in (
                        "orbit_disagreement_count", "action_class_error_count", "quantized_action_error_count",
                        "canonical_action_equivariance_checks", "inference_distance_evaluations")},
                    "true_action_quantization_squared_displacement_sum": rational(sum((Fraction(
                        **o["true_action_quantization_squared_displacement_sum"]) for o in observations), Fraction()))})
            means = {key: rational(sum((Fraction(**p[key]) for p in profiles), Fraction()) / 2)
                     for key in ("equal_base_error", "base_orbit_weighted_error")}
            rows.append({"arm": arm, "capacity": capacity,
                         "codebook_bits": (34 if "noisy" in arm else 18) * capacity,
                         "profiles": profiles, "equal_profile_mean": means,
                         **{key: sum(r[key] for r in subset) for key in (
                             "training_distance_evaluations", "coordinate_updates", "training_records")}})
    return rows
