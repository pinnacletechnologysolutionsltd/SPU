#!/usr/bin/env python3
"""Regenerate and replay the synthetic current-signature SOM1 demo."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.som_current_monitor import (
    CLASS_NAMES,
    FEATURE_NAMES,
    REPLAY_CASES_PER_CLASS,
    generated_feature_rows,
    feature_csv_bytes,
    pack_quadrance,
    replay_current_windows,
)
from som_map import load_map, write_map
from som_trainer import build_map_document, load_csv_dataset


DATASET = REPO / "software" / "tests" / "data" / "synthetic_current_v1.csv"
MODEL = REPO / "software" / "models" / "synthetic_current_som_v1.json"
MODEL_NAME = "synthetic-current-som-v1"
DATASET_NAME = "Deterministic synthetic 100 Hz current-signature windows"
DATASET_PATH = "software/tests/data/synthetic_current_v1.csv"


def build_document(csv_path: Path = DATASET) -> dict:
    dataset = load_csv_dataset(
        csv_path,
        feature_columns=FEATURE_NAMES,
        label_column="state",
        has_header=True,
        scale=1,
    )
    if dataset.class_names != CLASS_NAMES:
        raise ValueError(
            f"current class order changed: {dataset.class_names!r} != {CLASS_NAMES!r}"
        )
    return build_map_document(
        dataset.samples,
        model=MODEL_NAME,
        dataset=DATASET_NAME,
        dataset_path=DATASET_PATH,
        dataset_sha256=dataset.sha256,
        scale=1,
        feature_names=dataset.feature_names,
        class_names=dataset.class_names,
    )


def emit_checked_artifacts() -> dict:
    DATASET.parent.mkdir(parents=True, exist_ok=True)
    DATASET.write_bytes(feature_csv_bytes())
    document = build_document()
    write_map(MODEL, document)
    return document


def run_replay(document: dict) -> tuple[list[list[int]], int, int]:
    rows = generated_feature_rows(first_case=100, cases_per_class=REPLAY_CASES_PER_CLASS)
    evidence = replay_current_windows(document, rows)
    confusion = [[0 for _ in CLASS_NAMES] for _ in CLASS_NAMES]
    exact = 0
    ambiguous = 0
    for generation, item in enumerate(evidence, 1):
        parsed = item.parsed
        if not (
            parsed.valid
            and not parsed.busy
            and parsed.has_second
            and parsed.map_valid
            and parsed.error == 0
            and parsed.map_generation == 1
            and parsed.result_generation == generation
            and parsed.winner == item.oracle.best_node_id
            and parsed.runner_up == item.oracle.second_node_id
            and parsed.label == item.oracle.cluster_label
            and parsed.best_q == pack_quadrance(item.oracle.best_q)
            and parsed.second_q == pack_quadrance(item.oracle.second_q)
            and parsed.confidence_gap == pack_quadrance(item.oracle.confidence_gap)
            and parsed.ambiguous == item.oracle.ambiguous
        ):
            raise RuntimeError(f"invalid SOM1 evidence at generation {generation}: {parsed}")
        confusion[item.true_label][parsed.label] += 1
        exact += parsed.label == item.true_label
        ambiguous += parsed.ambiguous
    return confusion, exact, ambiguous


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit", action="store_true", help="regenerate the checked CSV and map"
    )
    args = parser.parse_args(argv)

    try:
        generated_csv = feature_csv_bytes()
        if args.emit:
            document = emit_checked_artifacts()
            print(f"Wrote {DATASET}")
            print(f"Wrote {MODEL}")
        else:
            if DATASET.read_bytes() != generated_csv:
                raise RuntimeError("checked synthetic feature CSV differs from regeneration")
            document = build_document()
            checked = load_map(MODEL)
            if checked != document:
                raise RuntimeError("checked synthetic map differs from regeneration")

        confusion, exact, ambiguous = run_replay(document)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"SENSOR_REPLAY: FAIL {exc}", file=sys.stderr)
        return 1

    count = len(CLASS_NAMES) * REPLAY_CASES_PER_CLASS
    if exact != count or ambiguous:
        print(
            f"SENSOR_REPLAY: FAIL exact={exact}/{count} ambiguous={ambiguous} "
            f"confusion={confusion}",
            file=sys.stderr,
        )
        return 1
    dataset_hash = hashlib.sha256(generated_csv).hexdigest()
    print(f"Current replay confusion: {confusion}")
    print(
        f"SENSOR_REPLAY: PASS windows={count} exact={exact}/{count} "
        f"ambiguous={ambiguous} dataset={dataset_hash} map={document['map_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
