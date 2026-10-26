"""Frozen noisy observations, exact projections, and weighted training inputs."""

from collections import Counter

from d4_canonical_exact import GROUP, GENERATORS, IDENTITY, act, compose
from d4_decision_p1_data import dataset, task_label
from d4_decision_p1b_quantize import exhaustive, parity_oracle, negative_controls

PROFILES = ((1, 2, 3, 4), (11, 10, 3, 1))
ARMS = ("canonical_q_som", "canonical_q_codebook", "raw_q_som", "raw_q_codebook",
        "raw_q_augmented_som", "raw_q_augmented_codebook",
        "raw_noisy_codebook", "raw_noisy_augmented_codebook")


def prepare():
    reps, folds, orbits, canon, transforms = dataset()
    observations, seeds = {}, []
    inverses = {w: next(v for v in GROUP if compose(w, v) == IDENTITY and
                         compose(v, w) == IDENTITY) for w in GROUP}
    projection_checks = generator_checks = 0
    for rank, rep in enumerate(reps):
        for profile, delta in enumerate(PROFILES):
            seed = tuple(16 * value + noise for value, noise in zip(rep, delta))
            q, distance = exhaustive(seed)
            assert parity_oracle(seed) == (q, distance)
            for generator in GENERATORS:
                assert exhaustive(act(generator, seed)) == (act(generator, q), distance)
                generator_checks += 1
            records = tuple((act(w, seed), act(w, q)) for w in GROUP)
            assert len(set(z for z, _ in records)) == 192
            for z, image in records:
                assert parity_oracle(z) == (image, distance)
                assert all(-128 <= value <= 127 for value in z)
                projection_checks += 1
            observations[rank, profile] = records
            seeds.append({"base": rank, "profile": profile, "z": seed, "q": q,
                          "distance_squared_numerator": distance,
                          "true_action_displacement_numerators_scale16": tuple(
                              (task_label(rep) + 1) * (16 * a - b) for a, b in zip(q, seed)),
                          "label": task_label(rep), "projected_label": task_label(q)})
    changed = [sum(s["q"] != reps[s["base"]] for s in seeds if s["profile"] == j)
               for j in range(2)]
    crossings = [sum(s["label"] != s["projected_label"] for s in seeds if s["profile"] == j)
                 for j in range(2)]
    assert changed == [0, 28] and crossings == [0, 16]
    points = [set(s["q"] for s in seeds if s["profile"] == j) for j in range(2)]
    collisions = {}
    for s in seeds:
        collisions.setdefault(s["q"], Counter())[s["label"]] += 1
    conflicts = sum(len(counts) > 1 for counts in collisions.values())
    majority_errors = sum(sum(c.values()) - max(c.values()) for c in collisions.values())
    assert (len(collisions), len(points[0] & points[1]), conflicts, majority_errors) == (57, 41, 16, 16)
    assert sum(len(records) for records in observations.values()) == 21888
    assert sum(map(len, folds)) == len(set(rep for fold in folds for rep in fold)) == 57
    report = {"verdict": "PASS", "observations": 21888, "unique_seed_minima": 114,
              "equivariance_checks": projection_checks, "generator_exhaustive_checks": generator_checks,
              "projection_changes": changed, "norm_label_crossings": crossings,
              "seed_distinct_projections": 57, "seed_shared_projections": 41,
              "seed_conflicting_coordinates": conflicts, "seed_majority_errors": majority_errors,
              "fold_sizes": list(map(len, folds)), "projections": seeds,
              "distance_distribution": [dict(sorted(Counter(s["distance_squared_numerator"]
                  for s in seeds if s["profile"] == j).items())) for j in range(2)],
              "negative_controls": negative_controls()}
    return reps, folds, orbits, canon, transforms, inverses, observations, report


def point_for(arm, z, q, canon):
    return canon[q] if arm.startswith("canonical") else z if "noisy" in arm else q


def samples(arm, ranks, observations, canon):
    records = []
    for rank, rep in ranks:
        for profile in range(2):
            expanded = observations[rank, profile]
            if arm.startswith("canonical"):
                selected, weight = expanded[:1], 192
            elif "augmented" in arm:
                selected, weight = expanded, 1
            else:
                selected, weight = (expanded[(37 * rank + 11) % 192],), 192
            records.extend((point_for(arm, z, q, canon), task_label(rep), weight)
                           for z, q in selected)
    assert sum(weight for _, _, weight in records) == 384 * len(ranks)
    # Exact merging is permitted; differing labels at a shared point stay separate.
    counts = Counter()
    for point, label, weight in records:
        counts[point, label] += weight
    return tuple(sorted((point, label, weight) for (point, label), weight in counts.items()))
