#!/usr/bin/env python3
"""test_spu4_som_edge_trainer.py — hardware-free regression for
tools/spu4_som_edge_trainer.py.

Checks CSV loading, deterministic training convergence on a synthetic
separable dataset (both a clean 4-class case and a realistic 3-class/
4-node case, since spu4_som_edge has 4 nodes but the INA226 contract has
3 classes), determinism (same input -> byte-identical output), and that
the trainer's weights JSON round-trips through
tools/gen_spu4_som_boot_image.py's loader without error -- the actual
integration point that matters.

No hardware required. Run: python3 software/tests/test_spu4_som_edge_trainer.py
"""

import json
import os
import sys
import tempfile

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import spu4_som_edge_trainer as trainer  # noqa: E402
import gen_spu4_som_boot_image as image_gen  # noqa: E402
from software.lib.rational_som import RationalSurd  # noqa: E402
from software.lib.spu4_som_edge_oracle import find_bmu_edge  # noqa: E402

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


def write_csv(rows, header=None):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", newline="") as f:
        if header:
            f.write(",".join(header) + "\n")
        for row in rows:
            f.write(",".join(str(v) for v in row) + "\n")
    return path


# ── Part 1: CSV loading ────────────────────────────────────────────────

good_rows = [
    (100, 0, 0, 0, "normal"),
    (100, 0, 0, 1, "normal"),
    (0, 100, 0, 0, "elevated_load"),
    (0, 100, 0, 1, "elevated_load"),
    (0, 0, 100, 0, "stall"),
    (0, 0, 100, 1, "stall"),
]
csv_path = write_csv(good_rows)
dataset = trainer.load_csv_dataset(csv_path, feature_count=4, label_column="4")
check("load_csv_dataset: correct sample count", len(dataset.samples) == 6)
check("load_csv_dataset: correct class set",
      dataset.class_names == ("elevated_load", "normal", "stall"))
check("load_csv_dataset: features parsed as plain ints",
      dataset.samples[0][0] == (100, 0, 0, 0))

try:
    trainer.load_csv_dataset(write_csv([(1, 2, 3, "x")]), feature_count=4, label_column="4")
    check("load_csv_dataset: too-few-columns row rejected", False)
except trainer.Spu4SomTrainingError:
    check("load_csv_dataset: too-few-columns row rejected", True)

try:
    five_classes = [(i, 0, 0, 0, f"class{i}") for i in range(5)] * 2
    trainer.load_csv_dataset(write_csv(five_classes), feature_count=4, label_column="4")
    check("load_csv_dataset: more classes than nodes rejected", False)
except trainer.Spu4SomTrainingError:
    check("load_csv_dataset: more classes than nodes rejected", True)


# ── Part 2: winner_shift schedule ──────────────────────────────────────

check("winner_shift(0) == 3", trainer.winner_shift(0) == 3)
check("winner_shift(9) == 3", trainer.winner_shift(9) == 3)
check("winner_shift(10) == 4", trainer.winner_shift(10) == 4)
check("winner_shift(24) == 4", trainer.winner_shift(24) == 4)
check("winner_shift(25) == 5", trainer.winner_shift(25) == 5)
check("winner_shift(39) == 5", trainer.winner_shift(39) == 5)
try:
    trainer.winner_shift(40)
    check("winner_shift(40) raises (outside schedule)", False)
except trainer.Spu4SomTrainingError:
    check("winner_shift(40) raises (outside schedule)", True)


# ── Part 3: training converges on a well-separated synthetic dataset,
# 4 classes / 4 nodes (clean 1:1 case) ─────────────────────────────────

def jittered_cluster(center, label, n=8, spread=3, seed=0):
    rows = []
    for i in range(n):
        # Deterministic small jitter, no RNG dependency in the test itself.
        jitter = [((seed + i) * (17 + f) % (2 * spread + 1)) - spread for f in range(4)]
        rows.append(tuple(c + j for c, j in zip(center, jitter)) + (label,))
    return rows

centers_4class = {
    "A": (1000, 1000, 1000, 1000),
    "B": (-1000, 1000, -1000, 1000),
    "C": (1000, -1000, -1000, 1000),
    "D": (-1000, -1000, 1000, -1000),
}
rows_4class = []
for i, (label, center) in enumerate(centers_4class.items()):
    rows_4class.extend(jittered_cluster(center, label, seed=i * 100))

csv_4class = write_csv(rows_4class)
dataset_4class = trainer.load_csv_dataset(csv_4class, feature_count=4, label_column="4")
weights_4class, labels_4class, chosen_4class = trainer.train_nodes(
    dataset_4class.samples, model="test-4class"
)
check("train_nodes (4-class): produces NODE_COUNT weight vectors",
      len(weights_4class) == trainer.NODE_COUNT)
check("train_nodes (4-class): every node gets a distinct majority label "
      "(well-separated clusters, one node per cluster)",
      len(set(labels_4class)) == 4)

# Every training sample should classify to a node whose majority label
# matches its own true label -- the whole point of well-separated data.
misclassified = 0
for features, true_label in dataset_4class.samples:
    best, _ = find_bmu_edge(trainer._as_surds(features), weights_4class)
    if labels_4class[best] != true_label:
        misclassified += 1
check("train_nodes (4-class): all training samples correctly classified "
      "by their node's majority label",
      misclassified == 0)


# ── Part 4: realistic case -- 3 classes, 4 nodes (INA226 shape) ───────

centers_3class = {
    "normal": (500, 500, 500, 500),
    "elevated_load": (-500, 500, -500, 500),
    "current_limited_stall": (500, -500, -500, 500),
}
rows_3class = []
for i, (label, center) in enumerate(centers_3class.items()):
    rows_3class.extend(jittered_cluster(center, label, n=10, seed=i * 50))

csv_3class = write_csv(rows_3class)
dataset_3class = trainer.load_csv_dataset(csv_3class, feature_count=4, label_column="4")
check("load_csv_dataset (3-class): 3 classes accepted with NODE_COUNT=4",
      len(dataset_3class.class_names) == 3)
weights_3class, labels_3class, _ = trainer.train_nodes(
    dataset_3class.samples, model="test-3class"
)
check("train_nodes (3-class/4-node): produces NODE_COUNT weight vectors",
      len(weights_3class) == trainer.NODE_COUNT)
check("train_nodes (3-class/4-node): every present class is the majority "
      "label of at least one node (no class silently dropped)",
      set(labels_3class) >= set(range(len(dataset_3class.class_names))))


# ── Part 5: determinism -- same input, byte-identical output ──────────

weights_again, labels_again, chosen_again = trainer.train_nodes(
    dataset_4class.samples, model="test-4class"
)
check("train_nodes is deterministic: identical weights on a repeat run",
      weights_again == weights_4class)
check("train_nodes is deterministic: identical labels on a repeat run",
      labels_again == labels_4class)


# ── Part 6: weights JSON round-trips through gen_spu4_som_boot_image.py ─

doc = trainer.build_weights_document(weights_4class, feature_count=4)
check("build_weights_document: correct format tag",
      doc["format"] == "SPU4_SOM_BOOT_IMAGE_V1")
check("build_weights_document: correct node_count", doc["node_count"] == 4)

fd, weights_path = tempfile.mkstemp(suffix=".json")
with os.fdopen(fd, "w") as f:
    json.dump(doc, f)

feature_count, node_weights = image_gen.load_weights(weights_path)
check("gen_spu4_som_boot_image.load_weights accepts the trainer's output "
      "with no errors", feature_count == 4 and len(node_weights) == 4)

image_bytes = image_gen.build_image(feature_count, node_weights)
check("gen_spu4_som_boot_image.build_image produces the expected byte count "
      "(4 nodes x 4 features x 4 bytes)", len(image_bytes) == 64)

# The image's packed (p, q) pairs must match the trainer's own weights
# exactly -- not just "no exception", genuinely round-trip identical.
import struct  # noqa: E402
reparsed = [
    struct.unpack(">hh", image_bytes[(n * 4 + f) * 4:(n * 4 + f) * 4 + 4])
    for n in range(4) for f in range(4)
]
expected = [
    (w.p, w.q) for node_weights_list in weights_4class for w in node_weights_list
]
check("packed boot image matches the trainer's weights exactly, "
      "component-for-component", reparsed == expected)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
