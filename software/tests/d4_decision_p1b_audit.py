"""Recompute predictions and metrics without the learner's winner/evaluation helpers."""

from collections import Counter
from fractions import Fraction


def check_gaps(gaps, reported):
    count = sum(gaps.values())
    if not count:
        assert reported["runner_gap_mean"] is None and reported["runner_gap_median"] is None
        return
    assert Fraction(**reported["runner_gap_mean"]) == Fraction(sum(g * n for g, n in gaps.items()), count)
    positions, middle, seen = ((count - 1) // 2, count // 2), [], 0
    for gap, frequency in sorted(gaps.items()):
        middle.extend(gap for position in positions if seen <= position < seen + frequency)
        seen += frequency
    assert len(middle) == 2 and Fraction(**reported["runner_gap_median"]) == Fraction(sum(middle), 2)


def check_row(row, reps, observations, canon, orbits):
    predictions_checked = 0
    low, high = (-128, 127) if "noisy" in row["arm"] else (-4, 4)
    assert len(row["prototypes"]) == len(row["node_labels"]) == row["capacity"]
    assert all(low <= value <= high for p in row["prototypes"] for value in p)
    for profile in range(2):
        reported = row["profiles"][profile]
        confusion = [[0] * 3 for _ in range(3)]
        errors, gaps = [], Counter()
        disagreement = action_wrong = displacement = 0
        for entry in reported["base_errors"]:
            rank = entry["base"]
            rep = reps[rank]
            energy = sum(v * v for v in rep)
            truth = 0 if energy <= 12 else 1 if energy <= 30 else 2
            predictions = []
            for z, q in observations[rank, profile]:
                point = canon[q] if row["arm"].startswith("canonical") else z if "noisy" in row["arm"] else q
                distances = [(point[0] - p[0]) ** 2 + (point[1] - p[1]) ** 2 +
                             (point[2] - p[2]) ** 2 + (point[3] - p[3]) ** 2 for p in row["prototypes"]]
                best = distances.index(min(distances))
                predicted = row["node_labels"][best]
                predictions.append(predicted)
                confusion[truth][predicted] += 1
                predictions_checked += 1
                if len(distances) > 1:
                    ordered = sorted(distances)
                    gaps[ordered[1] - ordered[0]] += 1
                action_wrong += predicted != truth and any(q)
                displacement += (truth + 1) ** 2 * sum((16 * a - b) ** 2 for a, b in zip(q, z))
            wrong = sum(p != truth for p in predictions)
            assert wrong == entry["wrong"] and entry["orbit_weight"] == len(orbits[rep])
            errors.append((wrong, len(orbits[rep])))
            disagreement += sum(p != predictions[0] for p in predictions)
        assert confusion == reported["confusion"] and dict(gaps) == reported["runner_gap_histogram"]
        check_gaps(gaps, reported)
        assert Fraction(**reported["equal_base_error"]) == Fraction(sum(e for e, _ in errors), 192 * len(errors))
        assert Fraction(**reported["base_orbit_weighted_error"]) == Fraction(
            sum(e * w for e, w in errors), 192 * sum(w for _, w in errors))
        assert disagreement == reported["orbit_disagreement_count"]
        assert sum(e for e, _ in errors) == reported["action_class_error_count"]
        assert action_wrong == reported["quantized_action_error_count"]
        assert Fraction(**reported["true_action_quantization_squared_displacement_sum"]) == Fraction(displacement, 256)
        assert reported["inference_distance_evaluations"] == len(errors) * 192 * row["capacity"]
        assert reported["canonical_action_equivariance_checks"] == (192 * len(errors) if row["arm"].startswith("canonical") else 0)
    return predictions_checked


def check_aggregate(results, aggregate):
    for total in aggregate:
        rows = [r for r in results if (r["arm"], r["capacity"]) == (total["arm"], total["capacity"])]
        assert len(rows) == 5
        for j, profile in enumerate(total["profiles"]):
            entries = [e for r in rows for e in r["profiles"][j]["base_errors"]]
            assert len(entries) == len({e["base"] for e in entries}) == 57
            assert Fraction(**profile["equal_base_error"]) == Fraction(sum(e["wrong"] for e in entries), 10944)
            assert Fraction(**profile["base_orbit_weighted_error"]) == Fraction(
                sum(e["wrong"] * e["orbit_weight"] for e in entries), 192 * 3281)
            assert profile["confusion"] == [[sum(r["profiles"][j]["confusion"][a][b] for r in rows)
                                              for b in range(3)] for a in range(3)]
            gaps = Counter()
            for r in rows:
                gaps.update(r["profiles"][j]["runner_gap_histogram"])
            assert dict(gaps) == profile["runner_gap_histogram"]
            check_gaps(gaps, profile)
            for key in ("orbit_disagreement_count", "action_class_error_count", "quantized_action_error_count",
                        "canonical_action_equivariance_checks", "inference_distance_evaluations"):
                assert profile[key] == sum(r["profiles"][j][key] for r in rows)
            key = "true_action_quantization_squared_displacement_sum"
            assert Fraction(**profile[key]) == sum((Fraction(**r["profiles"][j][key]) for r in rows), Fraction())
        for key in ("equal_base_error", "base_orbit_weighted_error"):
            assert Fraction(**total["equal_profile_mean"][key]) == sum(
                (Fraction(**p[key]) for p in total["profiles"]), Fraction()) / 2
        assert total["codebook_bits"] == total["capacity"] * (34 if "noisy" in total["arm"] else 18)
        for key in ("training_distance_evaluations", "coordinate_updates", "training_records"):
            assert total[key] == sum(r[key] for r in rows)
    return {"aggregate_rows_recomputed": len(aggregate), "profile_rows_recomputed": 2 * len(aggregate)}


def check_controls(report, reps, observations, orbits):
    """Independent label-count accumulation; no control implementation imports."""
    projected = {}
    for profile in range(2):
        quantized_wrong = noisy_wrong = weighted_q = weighted_z = 0
        for rank, rep in enumerate(reps):
            value = sum(v * v for v in rep)
            label = int(value > 12) + int(value > 30)
            weight = len(orbits[rep])
            for z, q in observations[rank, profile]:
                q_norm, z_norm = sum(v * v for v in q), sum(v * v for v in z)
                q_wrong = int(q_norm > 12) + int(q_norm > 30) != label
                z_wrong = int(z_norm > 3072) + int(z_norm > 7680) != label
                quantized_wrong += q_wrong
                noisy_wrong += z_wrong
                weighted_q += weight * q_wrong
                weighted_z += weight * z_wrong
                equal, weighted = projected.setdefault(q, ([0, 0, 0], [0, 0, 0]))
                equal[label] += 1
                weighted[label] += weight
        row = report["profiles"][profile]
        assert Fraction(**row["quantized_norm_rule"]) == Fraction(quantized_wrong, 10944)
        assert Fraction(**row["noisy_norm_rule"]) == Fraction(noisy_wrong, 10944)
        assert Fraction(**row["quantized_norm_orbit_weighted"]) == Fraction(weighted_q, 192 * 3281)
        assert Fraction(**row["noisy_norm_orbit_weighted"]) == Fraction(weighted_z, 192 * 3281)
    equal_errors = sum(sum(e) - max(e) for e, _ in projected.values())
    weighted_errors = sum(sum(w) - max(w) for _, w in projected.values())
    assert equal_errors == report["majority_error_count"]
    assert Fraction(**report["empirical_quantized_input_majority_error"]) == Fraction(equal_errors, 21888)
    assert Fraction(**report["empirical_quantized_input_orbit_weighted_majority_error"]) == Fraction(weighted_errors, 384 * 3281)
    return {"control_observations_recomputed": 21888, "projected_coordinates_recomputed": len(projected)}
