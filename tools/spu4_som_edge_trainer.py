#!/usr/bin/env python3
"""spu4_som_edge_trainer.py — deterministic trainer for spu4_som_edge's
4-node edge classifier.

This did not exist before: `som_trainer.py` trains the unrelated SPU-13
seven-node hex SOM (a topological map with neighbor diffusion, plain
scaled-decimal features). spu4_som_edge has no topology (four independent
nodes, winner-take-all only) and its distance metric is a RationalSurd
scalar quadrance, not a plain squared difference -- see
software/lib/spu4_som_edge_oracle.py. This trainer is built for that
target specifically, reusing som_trainer.py's proven *algorithm shape*
(exact-integer dyadic competitive learning, farthest-point
initialization, SHA256-seeded deterministic epoch order) without its
hex-neighbor machinery, which does not apply here.

Feature convention: real scalar sensor features (e.g. INA226
mean_current_mA) have no natural surd component, so they are represented
as RationalSurd(value, 0) -- matching this repo's own convention that Q=0
means "an ordinary integer" (CLAUDE.md: identity = P=1,Q=0). The dyadic
update is applied to P and Q independently, so weights trained purely on
real (Q=0) data converge with Q staying at/near 0, and the same code path
still works correctly on synthetic fixtures that do carry a nonzero Q.

BMU selection during training calls software/lib/spu4_som_edge_oracle.py's
find_bmu_edge() directly -- not a reimplementation -- so "which node wins"
during training is bit-identical to what the RTL will compute, by
construction rather than by hoping two formulas stay in sync.

Output is two separate artifacts, deliberately not one:
- A weights JSON matching tools/gen_spu4_som_boot_image.py's WeightsError
  schema exactly (format SPU4_SOM_BOOT_IMAGE_V1) -- feeds that script
  directly via --weights.
- A training report (node -> majority class label, vote counts, dataset
  provenance, training parameters) as a SEPARATE file. It is not folded
  into the weights JSON on purpose: spu4_som_edge_wrapper.v's own header
  explicitly excludes a node -> semantic label mapper from its v1
  contract ("deployment-specific... hard-coding one now would be guessing
  at a downstream application this repo doesn't have yet"). The report is
  for humans and offline pipelines, not for the boot image.

Usage:
    python3 tools/spu4_som_edge_trainer.py --csv captures.csv \
        --output tools/build/spu4_som_edge_weights.json \
        --report tools/build/spu4_som_edge_training_report.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REPO_ROOT = __file__.rsplit("/tools/", 1)[0]
sys.path.insert(0, REPO_ROOT)

from software.lib.rational_som import RationalSurd
from software.lib.spu4_som_edge_oracle import find_bmu_edge

NODE_COUNT = 4
DEFAULT_FEATURE_COUNT = 4
DEFAULT_EPOCHS = 40
DEFAULT_ORDER_SEED = 188
DEFAULT_WINNER_SHIFT_SCHEDULE = ((0, 10, 3), (10, 25, 4), (25, 40, 5))


class Spu4SomTrainingError(ValueError):
    """Raised when a dataset or training contract is invalid."""


@dataclass(frozen=True)
class CsvDataset:
    samples: tuple[tuple[tuple[int, ...], int], ...]
    feature_names: tuple[str, ...]
    class_names: tuple[str, ...]
    sha256: str


def _resolve_column(token: str, header: Sequence[str] | None) -> int:
    if token.isdigit():
        return int(token)
    if header is None:
        raise Spu4SomTrainingError(
            f"named column {token!r} requires a CSV header and --has-header"
        )
    matches = [index for index, name in enumerate(header) if name == token]
    if len(matches) != 1:
        raise Spu4SomTrainingError(f"column name {token!r} must occur exactly once")
    return matches[0]


def load_csv_dataset(
    path: str | Path,
    *,
    feature_count: int = DEFAULT_FEATURE_COUNT,
    feature_columns: Sequence[str] | None = None,
    label_column: str = "4",
    has_header: bool = False,
    feature_names: Sequence[str] | None = None,
) -> CsvDataset:
    """Load `feature_count` exact-integer features and one categorical
    label per row. Unlike som_trainer.py's loader, features are plain
    integers (real INA226-derived values), not scaled decimals -- there
    is no natural decimal point in a microamp/milliamp count."""

    if feature_columns is None:
        feature_columns = tuple(str(i) for i in range(feature_count))
    if len(feature_columns) != feature_count:
        raise Spu4SomTrainingError(f"exactly {feature_count} feature columns are required")

    path = Path(path)
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Spu4SomTrainingError(f"CSV must be UTF-8: {exc}") from exc

    rows = [row for row in csv.reader(io.StringIO(text, newline="")) if row]
    if not rows:
        raise Spu4SomTrainingError("CSV contains no rows")
    header = tuple(cell.strip() for cell in rows.pop(0)) if has_header else None

    feature_indices = tuple(_resolve_column(str(token), header) for token in feature_columns)
    label_index = _resolve_column(str(label_column), header)
    if len(set(feature_indices)) != feature_count:
        raise Spu4SomTrainingError("feature columns must be distinct")
    if label_index in feature_indices:
        raise Spu4SomTrainingError("label column must be distinct from feature columns")
    maximum_index = max((*feature_indices, label_index))

    parsed: list[tuple[tuple[int, ...], str]] = []
    for row_number, row in enumerate(rows, 2 if has_header else 1):
        if len(row) <= maximum_index:
            raise Spu4SomTrainingError(
                f"CSV row {row_number} has {len(row)} columns; need index {maximum_index}"
            )
        label = row[label_index].strip()
        if not label:
            raise Spu4SomTrainingError(f"CSV row {row_number} has an empty label")
        try:
            features = tuple(int(row[index].strip()) for index in feature_indices)
        except ValueError as exc:
            raise Spu4SomTrainingError(
                f"CSV row {row_number}: features must be exact integers ({exc})"
            ) from exc
        parsed.append((features, label))

    if len(parsed) < NODE_COUNT:
        raise Spu4SomTrainingError(f"CSV requires at least {NODE_COUNT} samples")
    classes = tuple(sorted({label for _, label in parsed}))
    if not 1 <= len(classes) <= NODE_COUNT:
        raise Spu4SomTrainingError(
            f"CSV must contain between 1 and {NODE_COUNT} classes (got {len(classes)})"
        )
    label_ids = {name: index for index, name in enumerate(classes)}
    samples = tuple((features, label_ids[label]) for features, label in parsed)

    if feature_names is not None:
        if len(feature_names) != feature_count or any(not name for name in feature_names):
            raise Spu4SomTrainingError(
                f"feature_names must contain {feature_count} nonempty names"
            )
        names = tuple(feature_names)
    elif header is not None:
        names = tuple(header[index] for index in feature_indices)
    else:
        names = tuple(f"feature_{index}" for index in range(feature_count))

    return CsvDataset(
        samples=samples,
        feature_names=names,
        class_names=classes,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _as_surds(features: Sequence[int]) -> tuple[RationalSurd, ...]:
    """Real scalar features have no surd component -- see module docstring."""
    return tuple(RationalSurd(value, 0) for value in features)


def initial_indices(samples: Sequence[tuple[Sequence[int], int]]) -> list[int]:
    """Farthest-point initialization: nearest-to-mean first, then repeatedly
    the sample farthest (by quadrance) from every already-chosen node --
    same shape as som_trainer.py's initial_indices, using the RationalSurd
    scalar quadrance instead of a plain squared difference."""

    if len(samples) < NODE_COUNT:
        raise Spu4SomTrainingError(f"training requires at least {NODE_COUNT} samples")
    feature_count = len(samples[0][0])
    features = [sample[0] for sample in samples]
    mean = tuple(
        sum(row[i] for row in features) // len(features) for i in range(feature_count)
    )
    mean_surds = _as_surds(mean)

    def quadrance_to(row: Sequence[int], target: Sequence[RationalSurd]) -> int:
        _, q = find_bmu_edge(_as_surds(row), [target])
        return q

    indices = [
        min(range(len(features)), key=lambda i: (quadrance_to(features[i], mean_surds), i))
    ]
    while len(indices) < NODE_COUNT:
        candidates = (i for i in range(len(features)) if i not in indices)
        indices.append(
            max(
                candidates,
                key=lambda i: (
                    min(
                        quadrance_to(features[i], _as_surds(features[chosen]))
                        for chosen in indices
                    ),
                    -i,
                ),
            )
        )
    return indices


def epoch_order(epoch: int, count: int, model: str, order_seed: int) -> list[int]:
    return sorted(
        range(count),
        key=lambda index: hashlib.sha256(
            f"{model}:{order_seed}:{epoch}:{index}".encode("utf-8")
        ).digest(),
    )


def winner_shift(
    epoch: int, schedule: Sequence[tuple[int, int, int]] = DEFAULT_WINNER_SHIFT_SCHEDULE
) -> int:
    for first, last, shift in schedule:
        if first <= epoch < last:
            return shift
    raise Spu4SomTrainingError(f"epoch {epoch} is outside the winner shift schedule")


def train_nodes(
    samples: Sequence[tuple[Sequence[int], int]],
    *,
    model: str,
    epochs: int = DEFAULT_EPOCHS,
    order_seed: int = DEFAULT_ORDER_SEED,
    winner_shift_schedule: Sequence[tuple[int, int, int]] = DEFAULT_WINNER_SHIFT_SCHEDULE,
) -> tuple[list[list[RationalSurd]], list[int], list[int]]:
    """Train 4 independent node prototypes with a fixed replayable dyadic
    schedule -- winner-take-all only, no neighbor diffusion (spu4_som_edge
    has no topology). Returns (weights, majority-vote node labels, the
    initial sample indices chosen)."""

    if not model or not isinstance(model, str):
        raise Spu4SomTrainingError("model must be a nonempty string")
    feature_count = len(samples[0][0])
    if any(len(row) != feature_count for row, _ in samples):
        raise Spu4SomTrainingError("every sample must have the same feature count")
    if any(not isinstance(label, int) or label < 0 for _, label in samples):
        raise Spu4SomTrainingError("class labels must be non-negative integers")

    chosen = initial_indices(samples)
    weights: list[list[RationalSurd]] = [list(_as_surds(samples[i][0])) for i in chosen]

    for epoch in range(epochs):
        shift = winner_shift(epoch, winner_shift_schedule)
        for sample_index in epoch_order(epoch, len(samples), model, order_seed):
            feature = _as_surds(samples[sample_index][0])
            best, _ = find_bmu_edge(feature, weights)
            weights[best] = [
                RationalSurd(
                    w.p + ((f.p - w.p) >> shift),
                    w.q + ((f.q - w.q) >> shift),
                )
                for f, w in zip(feature, weights[best])
            ]

    votes = [Counter() for _ in range(NODE_COUNT)]
    for row, true_label in samples:
        best, _ = find_bmu_edge(_as_surds(row), weights)
        votes[best][true_label] += 1
    labels = [
        min(counts, key=lambda label: (-counts[label], label)) if counts else 0
        for counts in votes
    ]
    return weights, labels, chosen


def build_weights_document(weights: Sequence[Sequence[RationalSurd]], feature_count: int) -> dict:
    """Exactly tools/gen_spu4_som_boot_image.py's WeightsError schema --
    feeds that script directly via --weights."""

    return {
        "format": "SPU4_SOM_BOOT_IMAGE_V1",
        "node_count": NODE_COUNT,
        "feature_count": feature_count,
        "nodes": [
            {
                "id": node_id,
                "weights": [{"p": w.p, "q": w.q} for w in node_weights],
            }
            for node_id, node_weights in enumerate(weights)
        ],
    }


def build_report_document(
    *,
    model: str,
    dataset_path: str,
    dataset_sha256: str,
    feature_names: Sequence[str],
    class_names: Sequence[str],
    labels: Sequence[int],
    chosen: Sequence[int],
    epochs: int,
    order_seed: int,
    winner_shift_schedule: Sequence[tuple[int, int, int]],
    sample_count: int,
) -> dict:
    """Human/pipeline-facing training diagnostics -- NOT fed into the boot
    image, see module docstring."""

    return {
        "format": "SPU4_SOM_TRAINING_REPORT_V1",
        "model": model,
        "dataset_path": dataset_path,
        "dataset_sha256": dataset_sha256,
        "sample_count": sample_count,
        "feature_names": list(feature_names),
        "class_names": list(class_names),
        "node_majority_labels": [
            {"node_id": node_id, "class_name": class_names[label], "class_label": label}
            for node_id, label in enumerate(labels)
        ],
        "trainer": {
            "kind": "deterministic-winner-take-all-quadrance-som",
            "epochs": epochs,
            "order": "sha256",
            "order_seed": order_seed,
            "initialization": "mean-nearest-then-farthest-first",
            "initial_sample_indices": list(chosen),
            "winner_shift_schedule": [list(item) for item in winner_shift_schedule],
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True, help="labeled feature CSV")
    ap.add_argument("--feature-count", type=int, default=DEFAULT_FEATURE_COUNT)
    ap.add_argument("--feature-columns", nargs="+", default=None,
                     help="column indices or names (default: 0..feature_count-1)")
    ap.add_argument("--label-column", default=str(DEFAULT_FEATURE_COUNT),
                     help="column index or name for the class label")
    ap.add_argument("--has-header", action="store_true")
    ap.add_argument("--model", default="spu4_som_edge-v1")
    ap.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    ap.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    ap.add_argument("--output", required=True, help="weights JSON path")
    ap.add_argument("--report", help="training report JSON path (optional)")
    ns = ap.parse_args(argv)

    dataset = load_csv_dataset(
        ns.csv,
        feature_count=ns.feature_count,
        feature_columns=ns.feature_columns,
        label_column=ns.label_column,
        has_header=ns.has_header,
    )
    weights, labels, chosen = train_nodes(
        dataset.samples, model=ns.model, epochs=ns.epochs, order_seed=ns.order_seed
    )

    weights_doc = build_weights_document(weights, ns.feature_count)
    os.makedirs(os.path.dirname(os.path.abspath(ns.output)) or ".", exist_ok=True)
    with open(ns.output, "w", encoding="utf-8") as f:
        json.dump(weights_doc, f, indent=2)
        f.write("\n")
    print(f"weights written: {ns.output}")
    print(f"  node majority labels: "
          f"{[dataset.class_names[label] for label in labels]}")

    if ns.report:
        report_doc = build_report_document(
            model=ns.model,
            dataset_path=str(ns.csv),
            dataset_sha256=dataset.sha256,
            feature_names=dataset.feature_names,
            class_names=dataset.class_names,
            labels=labels,
            chosen=chosen,
            epochs=ns.epochs,
            order_seed=ns.order_seed,
            winner_shift_schedule=DEFAULT_WINNER_SHIFT_SCHEDULE,
            sample_count=len(dataset.samples),
        )
        os.makedirs(os.path.dirname(os.path.abspath(ns.report)) or ".", exist_ok=True)
        with open(ns.report, "w", encoding="utf-8") as f:
            json.dump(report_doc, f, indent=2)
            f.write("\n")
        print(f"report written: {ns.report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
