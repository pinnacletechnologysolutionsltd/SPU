"""Exact held-out decision, confidence, and action metrics for D4 P1."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction

from d4_canonical_exact import GROUP, act
from d4_decision_p1 import MULTIPLIERS, winner
from d4_decision_p1_data import task_label


def rational(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def median(values):
    values = sorted(values)
    middle = len(values) // 2
    if len(values) % 2:
        return Fraction(values[middle])
    return Fraction(values[middle - 1] + values[middle], 2)


def evaluate(arm, prototypes, labels, test_reps, orbits, canon, transforms, inverses):
    canonical_arm = arm.startswith("canonical")
    representative_error = Fraction()
    wrong_states = 0
    wrong_actions = 0
    disagreement = 0
    state_count = 0
    zero_count = 0
    equivariance_checks = 0
    equivariance_failures = 0
    gaps = []
    confusion = [[0] * 3 for _ in range(3)]
    for rep in test_reps:
        orbit = orbits[rep]
        expected_class = task_label(rep)
        orbit_wrong = 0
        orbit_predictions = []
        orbit_actions = {}
        for state in orbit:
            point = canon[state] if canonical_arm else state
            best, distance, runner = winner(point, prototypes)
            predicted = labels[best]
            orbit_predictions.append(predicted)
            confusion[expected_class][predicted] += 1
            if runner is not None:
                gaps.append(runner - distance)
            wrong = predicted != expected_class
            orbit_wrong += wrong
            wrong_states += wrong
            state_count += 1
            zero_count += state == (0, 0, 0, 0)
            scale = MULTIPLIERS[predicted]
            if canonical_arm:
                canonical_action = tuple(scale * value for value in canon[state])
                action = act(inverses[transforms[state]], canonical_action)
                assert action == tuple(scale * value for value in state)
            else:
                action = tuple(scale * value for value in state)
            true_action = tuple(MULTIPLIERS[expected_class] * value for value in state)
            wrong_actions += action != true_action
            orbit_actions[state] = action
        representative_error += Fraction(orbit_wrong, len(orbit))
        disagreement += sum(value != orbit_predictions[0] for value in orbit_predictions)
        if canonical_arm:
            assert len(set(orbit_predictions)) == 1
        for state in orbit:
            for w in GROUP:
                equivariance_checks += 1
                equivariance_failures += orbit_actions[act(w, state)] != act(
                    w, orbit_actions[state])
        if canonical_arm:
            assert equivariance_failures == 0
    return {
        "representatives": len(test_reps), "states": state_count,
        "representative_error_sum": rational(representative_error),
        "state_error_count": wrong_states,
        "action_error_count": wrong_actions,
        "zero_state_count": zero_count,
        "orbit_disagreement_count": disagreement,
        "equivariance_checks": equivariance_checks,
        "equivariance_failures": equivariance_failures,
        "confusion": confusion,
        "inference_distance_evaluations": state_count * len(prototypes),
        "runner_gap_mean": rational(Fraction(sum(gaps), len(gaps))) if gaps else None,
        "runner_gap_median": rational(median(gaps)) if gaps else None,
        "runner_gap_histogram": dict(sorted(Counter(gaps).items())),
    }


def aggregate_rows(results, arms, capacities):
    rows = []
    for arm in arms:
        for capacity in capacities:
            subset = [row for row in results if row["arm"] == arm and
                      row["capacity"] == capacity]
            assert len(subset) == 5
            reps_count = sum(row["representatives"] for row in subset)
            states_count = sum(row["states"] for row in subset)
            assert reps_count == 57 and states_count == 3281
            error_sum = sum((Fraction(row["representative_error_sum"]["numerator"],
                                      row["representative_error_sum"]["denominator"])
                             for row in subset), Fraction())
            gap_histogram = Counter()
            for row in subset:
                gap_histogram.update({int(gap): count for gap, count in
                                      row["runner_gap_histogram"].items()})
            gap_count = sum(gap_histogram.values())
            gap_sum = sum(gap * count for gap, count in gap_histogram.items())
            confusion = [[sum(row["confusion"][true][predicted] for row in subset)
                          for predicted in range(3)] for true in range(3)]
            rows.append({
                "arm": arm, "capacity": capacity, "codebook_bits": 18 * capacity,
                "representative_error": rational(error_sum / reps_count),
                "state_error": rational(Fraction(sum(row["state_error_count"]
                                                     for row in subset), states_count)),
                "action_error_count": sum(row["action_error_count"] for row in subset),
                "orbit_disagreement_count": sum(row["orbit_disagreement_count"]
                                                for row in subset),
                "equivariance_checks": sum(row["equivariance_checks"] for row in subset),
                "equivariance_failures": sum(row["equivariance_failures"]
                                             for row in subset),
                "training_distance_evaluations": sum(
                    row["training_distance_evaluations"] for row in subset),
                "inference_distance_evaluations": sum(
                    row["inference_distance_evaluations"] for row in subset),
                "coordinate_updates": sum(row["coordinate_updates"] for row in subset),
                "confusion": confusion,
                "zero_state_count": sum(row["zero_state_count"] for row in subset),
                "runner_gap_mean": rational(Fraction(gap_sum, gap_count))
                if gap_count else None,
                "runner_gap_median": rational(median(
                    [gap for gap, count in gap_histogram.items() for _ in range(count)]))
                if gap_count else None,
            })
    return rows
