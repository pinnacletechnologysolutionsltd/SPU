#!/usr/bin/env python3
"""spu4_som_edge_cross_validate.py — held-out-fold evaluation for
tools/spu4_som_edge_trainer.py.

The trainer's own --output is a deployable artifact; this is a SEPARATE
evaluation-only tool that never produces one, matching this repo's
existing split between a case study (evaluation) and its trainer
(deployment) -- see docs/HYDRAULIC_PUMP_SOM_CASE_STUDY.md /
docs/PADERBORN_CURRENT_CROSS_VALIDATION.md for the precedent this copies.

Method: stratified K-fold. Samples are grouped by class, each class's
samples are ordered by SHA256(seed:class:index) (deterministic, not
CSV-row-order-dependent -- same discipline as the trainer's own
epoch_order), then round-robin assigned to K folds so every fold gets a
proportional share of every class. For each fold: train on the other K-1
folds only, derive node majority labels from ONLY that training data
(never the held-out fold -- labeling from held-out data would leak test
information into the "ground truth" the test samples are scored against),
then classify the held-out fold and record per-class hits/misses.

Reports both plain accuracy and balanced accuracy (the mean of each
class's own recall) per fold, since a class-imbalanced dataset can make
plain accuracy look better than it is -- same metric the hydraulic-pump
case study reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from typing import Sequence

REPO_ROOT = __file__.rsplit("/tools/", 1)[0]
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import spu4_som_edge_trainer as trainer
from software.lib.spu4_som_edge_oracle import find_bmu_edge

DEFAULT_FOLDS = 5


def assign_folds(
    samples: Sequence[tuple[Sequence[int], int]], k: int, seed: str
) -> list[int]:
    """Per-sample fold id (0..k-1), stratified within class and
    deterministic -- no dependence on CSV row order or a stdlib RNG."""

    if k < 2:
        raise trainer.Spu4SomTrainingError("k must be at least 2")
    by_class: dict[int, list[int]] = {}
    for index, (_, label) in enumerate(samples):
        by_class.setdefault(label, []).append(index)

    fold_of = [-1] * len(samples)
    for label, indices in by_class.items():
        if len(indices) < k:
            raise trainer.Spu4SomTrainingError(
                f"class {label} has only {len(indices)} samples, fewer than k={k} folds"
            )
        ordered = sorted(
            indices,
            key=lambda i: hashlib.sha256(f"{seed}:{label}:{i}".encode("utf-8")).digest(),
        )
        for position, sample_index in enumerate(ordered):
            fold_of[sample_index] = position % k
    return fold_of


def evaluate_fold(
    train_samples: Sequence[tuple[Sequence[int], int]],
    test_samples: Sequence[tuple[Sequence[int], int]],
    *,
    model: str,
    epochs: int,
    order_seed: int,
) -> dict:
    """Train on train_samples only, label nodes from train_samples only,
    then classify test_samples (never seen during training or labeling)."""

    weights, labels, _ = trainer.train_nodes(
        train_samples, model=model, epochs=epochs, order_seed=order_seed
    )

    per_class_total: Counter = Counter()
    per_class_correct: Counter = Counter()
    confusion: Counter = Counter()  # (true_label, predicted_label) -> count
    for features, true_label in test_samples:
        best, _ = find_bmu_edge(trainer._as_surds(features), weights)
        predicted_label = labels[best]
        per_class_total[true_label] += 1
        if predicted_label == true_label:
            per_class_correct[true_label] += 1
        confusion[(true_label, predicted_label)] += 1

    return {
        "test_count": len(test_samples),
        "correct": sum(per_class_correct.values()),
        "per_class_total": dict(per_class_total),
        "per_class_correct": dict(per_class_correct),
        "confusion": {f"{t}->{p}": c for (t, p), c in confusion.items()},
    }


def balanced_accuracy(per_class_total: dict, per_class_correct: dict, num_classes: int) -> float:
    """Mean per-class recall. Classes absent from a fold's test set (an
    edge case with very small datasets/high k) are excluded from the mean
    rather than silently counted as 0, which would understate performance
    for a fold that simply had no test examples of that class."""

    recalls = []
    for label in range(num_classes):
        total = per_class_total.get(label, 0)
        if total == 0:
            continue
        recalls.append(per_class_correct.get(label, 0) / total)
    return sum(recalls) / len(recalls) if recalls else 0.0


def cross_validate(
    samples: Sequence[tuple[Sequence[int], int]],
    *,
    class_names: Sequence[str],
    k: int = DEFAULT_FOLDS,
    fold_seed: str = "spu4-som-edge-cv-v1",
    model: str = "spu4-som-edge-cv",
    epochs: int = trainer.DEFAULT_EPOCHS,
    order_seed: int = trainer.DEFAULT_ORDER_SEED,
) -> dict:
    fold_of = assign_folds(samples, k, fold_seed)
    folds = []
    for fold_id in range(k):
        train_samples = [s for s, f in zip(samples, fold_of) if f != fold_id]
        test_samples = [s for s, f in zip(samples, fold_of) if f == fold_id]
        result = evaluate_fold(
            train_samples, test_samples, model=f"{model}-fold{fold_id}",
            epochs=epochs, order_seed=order_seed,
        )
        result["fold_id"] = fold_id
        result["accuracy"] = result["correct"] / result["test_count"] if result["test_count"] else 0.0
        result["balanced_accuracy"] = balanced_accuracy(
            result["per_class_total"], result["per_class_correct"], len(class_names)
        )
        folds.append(result)

    aggregate_balanced = sum(f["balanced_accuracy"] for f in folds) / len(folds)
    worst_fold_balanced = min(f["balanced_accuracy"] for f in folds)
    aggregate_plain = sum(f["correct"] for f in folds) / sum(f["test_count"] for f in folds)

    return {
        "format": "SPU4_SOM_EDGE_CROSS_VALIDATION_V1",
        "k": k,
        "fold_seed": fold_seed,
        "model": model,
        "class_names": list(class_names),
        "sample_count": len(samples),
        "folds": folds,
        "aggregate_plain_accuracy": aggregate_plain,
        "aggregate_balanced_accuracy": aggregate_balanced,
        "worst_fold_balanced_accuracy": worst_fold_balanced,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--feature-count", type=int, default=trainer.DEFAULT_FEATURE_COUNT)
    ap.add_argument("--label-column", default=str(trainer.DEFAULT_FEATURE_COUNT))
    ap.add_argument("--has-header", action="store_true")
    ap.add_argument("--k", type=int, default=DEFAULT_FOLDS)
    ap.add_argument("--model", default="spu4-som-edge-cv")
    ap.add_argument("--epochs", type=int, default=trainer.DEFAULT_EPOCHS)
    ap.add_argument("--order-seed", type=int, default=trainer.DEFAULT_ORDER_SEED)
    ap.add_argument("--report", help="output JSON path (optional; prints a summary either way)")
    ns = ap.parse_args(argv)

    dataset = trainer.load_csv_dataset(
        ns.csv, feature_count=ns.feature_count, label_column=ns.label_column,
        has_header=ns.has_header,
    )
    result = cross_validate(
        dataset.samples, class_names=dataset.class_names, k=ns.k, model=ns.model,
        epochs=ns.epochs, order_seed=ns.order_seed,
    )

    print(f"{ns.k}-fold cross-validation, {len(dataset.samples)} samples, "
          f"classes={list(dataset.class_names)}")
    for fold in result["folds"]:
        print(f"  fold {fold['fold_id']}: {fold['correct']}/{fold['test_count']} "
              f"plain={fold['accuracy']:.1%} balanced={fold['balanced_accuracy']:.1%}")
    print(f"aggregate plain accuracy:    {result['aggregate_plain_accuracy']:.1%}")
    print(f"aggregate balanced accuracy: {result['aggregate_balanced_accuracy']:.1%}")
    print(f"worst-fold balanced accuracy: {result['worst_fold_balanced_accuracy']:.1%}")

    if ns.report:
        os.makedirs(os.path.dirname(os.path.abspath(ns.report)) or ".", exist_ok=True)
        with open(ns.report, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        print(f"report written: {ns.report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
