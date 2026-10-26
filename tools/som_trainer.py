#!/usr/bin/env python3
"""Reusable deterministic trainer for the seven-node SPU SOM v1 sidecar."""

from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from som_map import compute_map_sha256, validate_map


NODE_COUNT = 7
FEATURE_COUNT = 4
DEFAULT_SCALE = 1000
DEFAULT_EPOCHS = 40
DEFAULT_ORDER_SEED = 188
DEFAULT_NEIGHBOR_EPOCHS = 5
DEFAULT_NEIGHBOR_SHIFT = 3
DEFAULT_WINNER_SHIFT_SCHEDULE = ((0, 10, 3), (10, 25, 4), (25, 40, 5))
AXIAL_COORDS = (
    (0, 0),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)
HEX_DELTAS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


class SomTrainingError(ValueError):
    """Raised when a dataset or deterministic training contract is invalid."""


@dataclass(frozen=True)
class CsvDataset:
    samples: tuple[tuple[tuple[int, ...], int], ...]
    feature_names: tuple[str, ...]
    class_names: tuple[str, ...]
    sha256: str


def _decimal_places(scale: int) -> int:
    if not isinstance(scale, int) or scale <= 0:
        raise SomTrainingError("scale must be a positive power of ten")
    value = scale
    places = 0
    while value > 1 and value % 10 == 0:
        value //= 10
        places += 1
    if value != 1:
        raise SomTrainingError("scale must be a positive power of ten")
    return places


def parse_scaled_decimal(text: str, scale: int = DEFAULT_SCALE) -> int:
    """Parse a decimal exactly; reject values not representable at ``scale``."""
    places = _decimal_places(scale)
    value = text.strip()
    if not value:
        raise SomTrainingError("empty numeric value")
    sign = -1 if value.startswith("-") else 1
    value = value.lstrip("+-")
    if not value or value.count(".") > 1:
        raise SomTrainingError(f"invalid decimal {text!r}")
    whole, dot, fractional = value.partition(".")
    if not whole:
        whole = "0"
    if not whole.isdigit() or (dot and fractional and not fractional.isdigit()):
        raise SomTrainingError(f"invalid decimal {text!r}")
    if len(fractional) > places and any(ch != "0" for ch in fractional[places:]):
        raise SomTrainingError(
            f"decimal {text!r} is not exactly representable at scale {scale}"
        )
    scaled_fraction = int((fractional + ("0" * places))[:places] or "0")
    return sign * (int(whole) * scale + scaled_fraction)


def _resolve_column(token: str, header: Sequence[str] | None) -> int:
    if token.isdigit():
        return int(token)
    if header is None:
        raise SomTrainingError(
            f"named column {token!r} requires a CSV header and --header"
        )
    matches = [index for index, name in enumerate(header) if name == token]
    if len(matches) != 1:
        raise SomTrainingError(f"column name {token!r} must occur exactly once")
    return matches[0]


def load_csv_dataset(
    path: str | Path,
    *,
    feature_columns: Sequence[str] = ("0", "1", "2", "3"),
    label_column: str = "4",
    has_header: bool = False,
    scale: int = DEFAULT_SCALE,
    feature_names: Sequence[str] | None = None,
) -> CsvDataset:
    """Load four exact numeric features and one categorical label from CSV."""
    path = Path(path)
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SomTrainingError(f"CSV must be UTF-8: {exc}") from exc

    rows = [row for row in csv.reader(io.StringIO(text, newline="")) if row]
    if not rows:
        raise SomTrainingError("CSV contains no rows")
    header = tuple(cell.strip() for cell in rows.pop(0)) if has_header else None
    if len(feature_columns) != FEATURE_COUNT:
        raise SomTrainingError(f"exactly {FEATURE_COUNT} feature columns are required")
    feature_indices = tuple(_resolve_column(str(token), header) for token in feature_columns)
    label_index = _resolve_column(str(label_column), header)
    if len(set(feature_indices)) != FEATURE_COUNT:
        raise SomTrainingError("feature columns must be distinct")
    if label_index in feature_indices:
        raise SomTrainingError("label column must be distinct from feature columns")
    maximum_index = max((*feature_indices, label_index))

    parsed: list[tuple[tuple[int, ...], str]] = []
    for row_number, row in enumerate(rows, 2 if has_header else 1):
        if len(row) <= maximum_index:
            raise SomTrainingError(
                f"CSV row {row_number} has {len(row)} columns; need index {maximum_index}"
            )
        label = row[label_index].strip()
        if not label:
            raise SomTrainingError(f"CSV row {row_number} has an empty label")
        try:
            features = tuple(
                parse_scaled_decimal(row[index], scale) for index in feature_indices
            )
        except SomTrainingError as exc:
            raise SomTrainingError(f"CSV row {row_number}: {exc}") from exc
        parsed.append((features, label))

    if len(parsed) < NODE_COUNT:
        raise SomTrainingError(f"CSV requires at least {NODE_COUNT} samples")
    classes = tuple(sorted({label for _, label in parsed}))
    if not 1 <= len(classes) <= NODE_COUNT:
        raise SomTrainingError(f"CSV must contain between 1 and {NODE_COUNT} classes")
    label_ids = {name: index for index, name in enumerate(classes)}
    samples = tuple((features, label_ids[label]) for features, label in parsed)

    if feature_names is not None:
        if len(feature_names) != FEATURE_COUNT or any(not name for name in feature_names):
            raise SomTrainingError(
                f"feature_names must contain {FEATURE_COUNT} nonempty names"
            )
        names = tuple(feature_names)
    elif header is not None:
        names = tuple(header[index] for index in feature_indices)
    else:
        names = tuple(f"feature_{index}" for index in range(FEATURE_COUNT))

    return CsvDataset(
        samples=samples,
        feature_names=names,
        class_names=classes,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def squared_distance(lhs: Sequence[int], rhs: Sequence[int]) -> int:
    if len(lhs) != FEATURE_COUNT or len(rhs) != FEATURE_COUNT:
        raise SomTrainingError(f"distance operands must have {FEATURE_COUNT} features")
    return sum((a - b) * (a - b) for a, b in zip(lhs, rhs))


def initial_indices(samples: Sequence[tuple[Sequence[int], int]]) -> list[int]:
    if len(samples) < NODE_COUNT:
        raise SomTrainingError(f"training requires at least {NODE_COUNT} samples")
    features = [sample[0] for sample in samples]
    mean = tuple(
        sum(row[feature] for row in features) // len(features)
        for feature in range(FEATURE_COUNT)
    )
    indices = [
        min(
            range(len(features)),
            key=lambda index: (squared_distance(features[index], mean), index),
        )
    ]
    while len(indices) < NODE_COUNT:
        candidates = (index for index in range(len(features)) if index not in indices)
        indices.append(
            max(
                candidates,
                key=lambda index: (
                    min(
                        squared_distance(features[index], features[chosen])
                        for chosen in indices
                    ),
                    -index,
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
    epoch: int,
    schedule: Sequence[tuple[int, int, int]] = DEFAULT_WINNER_SHIFT_SCHEDULE,
) -> int:
    for first, last, shift in schedule:
        if first <= epoch < last:
            return shift
    raise SomTrainingError(f"epoch {epoch} is outside the winner shift schedule")


def train_map(
    samples: Sequence[tuple[Sequence[int], int]],
    *,
    model: str,
    epochs: int = DEFAULT_EPOCHS,
    order_seed: int = DEFAULT_ORDER_SEED,
    neighbor_epochs: int = DEFAULT_NEIGHBOR_EPOCHS,
    neighbor_shift: int = DEFAULT_NEIGHBOR_SHIFT,
    winner_shift_schedule: Sequence[
        tuple[int, int, int]
    ] = DEFAULT_WINNER_SHIFT_SCHEDULE,
) -> tuple[list[list[int]], list[int], list[int]]:
    """Train integer prototypes with a fixed replayable dyadic schedule."""
    if not model or not isinstance(model, str):
        raise SomTrainingError("model must be a nonempty string")
    if epochs != DEFAULT_EPOCHS or tuple(winner_shift_schedule) != (
        DEFAULT_WINNER_SHIFT_SCHEDULE
    ):
        raise SomTrainingError("SOM map v1 is pinned to the published 40-epoch schedule")
    features = [tuple(sample[0]) for sample in samples]
    if any(len(row) != FEATURE_COUNT for row in features):
        raise SomTrainingError(f"every sample must have {FEATURE_COUNT} features")
    if any(not isinstance(label, int) or label < 0 for _, label in samples):
        raise SomTrainingError("class labels must be non-negative integers")

    chosen = initial_indices(samples)
    weights = [list(features[index]) for index in chosen]
    for epoch in range(epochs):
        for sample_index in epoch_order(epoch, len(samples), model, order_seed):
            feature = features[sample_index]
            best = min(
                range(NODE_COUNT),
                key=lambda node: (squared_distance(feature, weights[node]), node),
            )
            targets = [(best, winner_shift(epoch, winner_shift_schedule))]
            if epoch < neighbor_epochs:
                q, r = AXIAL_COORDS[best]
                for dq, dr in HEX_DELTAS:
                    coordinate = (q + dq, r + dr)
                    if coordinate in AXIAL_COORDS:
                        targets.append((AXIAL_COORDS.index(coordinate), neighbor_shift))
            for node, shift in targets:
                for feature_index in range(FEATURE_COUNT):
                    delta = feature[feature_index] - weights[node][feature_index]
                    weights[node][feature_index] += delta >> shift

    votes = [Counter() for _ in range(NODE_COUNT)]
    for feature, true_label in samples:
        best = min(
            range(NODE_COUNT),
            key=lambda node: (squared_distance(feature, weights[node]), node),
        )
        votes[best][true_label] += 1
    labels = [
        min(counts, key=lambda label: (-counts[label], label)) if counts else 0
        for counts in votes
    ]
    return weights, labels, chosen


def build_map_document(
    samples: Sequence[tuple[Sequence[int], int]],
    *,
    model: str,
    dataset: str,
    dataset_path: str,
    dataset_sha256: str,
    scale: int,
    feature_names: Sequence[str],
    class_names: Sequence[str],
) -> dict:
    """Train and return a checksum-complete SPU_SOM_MAP_V1 document."""
    _decimal_places(scale)
    if len(feature_names) != FEATURE_COUNT:
        raise SomTrainingError(f"exactly {FEATURE_COUNT} feature names are required")
    if not 1 <= len(class_names) <= NODE_COUNT:
        raise SomTrainingError(f"between 1 and {NODE_COUNT} class names are required")
    if any(label >= len(class_names) for _, label in samples):
        raise SomTrainingError("sample label is outside class_names")

    weights, labels, chosen = train_map(samples, model=model)
    document = {
        "format": "SPU_SOM_MAP_V1",
        "model": model,
        "dataset": dataset,
        "dataset_path": dataset_path,
        "dataset_sha256": dataset_sha256,
        "node_count": NODE_COUNT,
        "feature_count": FEATURE_COUNT,
        "coefficient_bits": 18,
        "scale": scale,
        "feature_names": list(feature_names),
        "feature_weights": [{"p": 1, "q": 0} for _ in range(FEATURE_COUNT)],
        "class_names": list(class_names),
        "trainer": {
            "kind": "deterministic-online-hex-som",
            "epochs": DEFAULT_EPOCHS,
            "order": "sha256",
            "order_seed": DEFAULT_ORDER_SEED,
            "initialization": "mean-nearest-then-farthest-first",
            "initial_sample_indices": chosen,
            "neighbor_epochs": DEFAULT_NEIGHBOR_EPOCHS,
            "neighbor_shift": DEFAULT_NEIGHBOR_SHIFT,
            "winner_shift_schedule": [
                list(item) for item in DEFAULT_WINNER_SHIFT_SCHEDULE
            ],
        },
        "nodes": [
            {
                "id": node,
                "axial": list(AXIAL_COORDS[node]),
                "class_label": labels[node],
                "weights": [{"p": value, "q": 0} for value in weights[node]],
            }
            for node in range(NODE_COUNT)
        ],
    }
    document["map_sha256"] = compute_map_sha256(document)
    validate_map(document)
    return document
