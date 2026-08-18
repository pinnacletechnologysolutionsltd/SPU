#!/usr/bin/env python3
"""test_spu4_som_edge_cross_validate.py — hardware-free regression for
tools/spu4_som_edge_cross_validate.py.

No hardware required. Run:
    python3 software/tests/test_spu4_som_edge_cross_validate.py
"""

import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import spu4_som_edge_cross_validate as cv  # noqa: E402
import spu4_som_edge_trainer as trainer  # noqa: E402

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── assign_folds: stratified, deterministic, correct counts ───────────

samples = [((i, 0, 0, 0), label) for label in range(3) for i in range(12)]
fold_of = cv.assign_folds(samples, k=4, seed="test-seed")
check("assign_folds: every sample gets a fold in range", all(0 <= f < 4 for f in fold_of))

from collections import Counter  # noqa: E402
per_fold_per_class = Counter()
for (features, label), fold in zip(samples, fold_of):
    per_fold_per_class[(fold, label)] += 1
check("assign_folds: perfectly stratified on evenly-divisible input "
      "(3 samples per class per fold)",
      all(v == 3 for v in per_fold_per_class.values()) and len(per_fold_per_class) == 12)

fold_of_again = cv.assign_folds(samples, k=4, seed="test-seed")
check("assign_folds: deterministic (same seed -> identical assignment)",
      fold_of == fold_of_again)

fold_of_diff_seed = cv.assign_folds(samples, k=4, seed="different-seed")
check("assign_folds: a different seed changes the assignment",
      fold_of != fold_of_diff_seed)

try:
    cv.assign_folds(samples, k=20, seed="s")
    check("assign_folds: k larger than class size raises", False)
except trainer.Spu4SomTrainingError:
    check("assign_folds: k larger than class size raises", True)


# ── balanced_accuracy ───────────────────────────────────────────────────

check("balanced_accuracy: perfect classification -> 1.0",
      cv.balanced_accuracy({0: 10, 1: 10}, {0: 10, 1: 10}, 2) == 1.0)
check("balanced_accuracy: all wrong -> 0.0",
      cv.balanced_accuracy({0: 10, 1: 10}, {0: 0, 1: 0}, 2) == 0.0)
# Imbalanced counts: 9/10 on a big class and 1/1 on a tiny class should
# average the two RECALLS (0.9, 1.0), not weight by sample count.
check("balanced_accuracy: averages per-class recall, not weighted by count",
      abs(cv.balanced_accuracy({0: 10, 1: 1}, {0: 9, 1: 1}, 2) - 0.95) < 1e-9)
check("balanced_accuracy: a class absent from the test set is excluded, "
      "not scored as 0",
      cv.balanced_accuracy({0: 10}, {0: 10}, 3) == 1.0)


# ── End-to-end: well-separated synthetic data must generalize (high
# held-out accuracy), proving this is a genuine test and not just an
# elaborate way to reproduce training accuracy ─────────────────────────

def jittered_cluster(center, label, n=20, spread=3, seed=0):
    rows = []
    for i in range(n):
        jitter = [((seed + i) * (17 + f) % (2 * spread + 1)) - spread for f in range(4)]
        rows.append((tuple(c + j for c, j in zip(center, jitter)), label))
    return rows

centers = {
    0: (1000, 1000, 1000, 1000),
    1: (-1000, 1000, -1000, 1000),
    2: (1000, -1000, -1000, 1000),
}
separable_samples = []
for label, center in centers.items():
    separable_samples.extend(jittered_cluster(center, label, n=20, seed=label * 100))

result = cv.cross_validate(
    separable_samples, class_names=["A", "B", "C"], k=5, model="test-cv-separable"
)
check("cross_validate: runs all k folds", len(result["folds"]) == 5)
check("cross_validate: well-separated data generalizes near-perfectly on "
      "genuinely held-out folds",
      result["aggregate_balanced_accuracy"] > 0.95)
check("cross_validate: worst fold is also strong, not hiding one bad fold "
      "behind a good average",
      result["worst_fold_balanced_accuracy"] > 0.8)

# Determinism of the full pipeline.
result_again = cv.cross_validate(
    separable_samples, class_names=["A", "B", "C"], k=5, model="test-cv-separable"
)
check("cross_validate: fully deterministic end to end (identical rerun)",
      result["aggregate_balanced_accuracy"] == result_again["aggregate_balanced_accuracy"]
      and result["folds"] == result_again["folds"])

# A genuinely inseparable dataset (all classes drawn from the SAME
# distribution) must NOT generalize well -- proves the harness can also
# report a negative, not just confirm whatever it's pointed at.
import random  # noqa: E402
rng = random.Random(12345)
inseparable_samples = [
    ((rng.randint(-10, 10), rng.randint(-10, 10), rng.randint(-10, 10), rng.randint(-10, 10)),
     label)
    for label in range(3) for _ in range(20)
]
result_bad = cv.cross_validate(
    inseparable_samples, class_names=["A", "B", "C"], k=5, model="test-cv-inseparable"
)
check("cross_validate: indistinguishable classes score near chance "
      "(~1/3), not near-perfect",
      result_bad["aggregate_balanced_accuracy"] < 0.6)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
