#!/usr/bin/env python3
"""Verify and run the predeclared UCI hydraulic pump SOM truth gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Callable, Iterable, Sequence


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.hydraulic_pump import (  # noqa: E402
    CLASS_NAMES,
    FEATURE_NAMES,
    FOLD_COUNT,
    HydraulicDataError,
    HydraulicWindow,
    assign_group_folds,
    fit_scaler,
    iter_stable_windows,
    round_ratio_half_even,
)
from lib.som_current_monitor import replay_current_windows  # noqa: E402
from som_map import load_map, write_map  # noqa: E402
from som_trainer import build_map_document, squared_distance  # noqa: E402


DEFAULT_MANIFEST = REPO / "software" / "datasets" / "hydraulic_pump_som_v1.json"
EXPECTED_CYCLES = 1_449
EXPECTED_WINDOWS = 23_184
EXPECTED_GROUPS = 48


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> dict:
    path = Path(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("format") != "SPU_HYDRAULIC_PUMP_SOM_V1":
        raise HydraulicDataError("hydraulic manifest has the wrong format")
    source = document.get("source", {})
    if source.get("license") != "CC BY 4.0":
        raise HydraulicDataError("hydraulic source licence is not pinned")
    if source.get("doi") != "10.24432/C5CW21":
        raise HydraulicDataError("hydraulic source DOI is not pinned")
    for field in ("archive_sha256",):
        if not isinstance(source.get(field), str) or len(source[field]) != 64:
            raise HydraulicDataError(f"manifest {field} is not a SHA-256")
    files = source.get("files")
    if set(files or {}) != {"EPS1.txt", "profile.txt"} or any(
        not isinstance(value, str) or len(value) != 64
        for value in files.values()
    ):
        raise HydraulicDataError("manifest source-file hashes are incomplete")
    if tuple(document.get("features", ())) != FEATURE_NAMES:
        raise HydraulicDataError("manifest feature contract differs from code")
    if tuple(document.get("task", {}).get("class_names", ())) != CLASS_NAMES:
        raise HydraulicDataError("manifest class contract differs from code")
    if document.get("validation", {}).get("folds") != FOLD_COUNT:
        raise HydraulicDataError("manifest fold count differs from code")
    return document


def verify_archive(manifest: dict, archive_root: Path) -> Path:
    source = manifest["source"]
    archive = archive_root / source["archive"]
    if not archive.is_file():
        raise HydraulicDataError(f"missing source archive {archive}")
    if sha256_path(archive) != source["archive_sha256"]:
        raise HydraulicDataError("hydraulic source archive checksum mismatch")
    return archive


def verify_source_files(manifest: dict, source_root: Path) -> None:
    for name, expected in manifest["source"]["files"].items():
        path = source_root / name
        if not path.is_file():
            raise HydraulicDataError(f"missing extracted source file {path}")
        if sha256_path(path) != expected:
            raise HydraulicDataError(f"source checksum mismatch: {name}")


def extract_sources(manifest: dict, archive_root: Path, source_root: Path) -> None:
    archive = verify_archive(manifest, archive_root)
    source_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        for name in manifest["source"]["files"]:
            if name not in names:
                raise HydraulicDataError(f"archive is missing {name}")
            destination = source_root / name
            destination.write_bytes(bundle.read(name))
    verify_source_files(manifest, source_root)


def summarize_confusion(matrix: Sequence[Sequence[int]]) -> dict:
    class_count = len(matrix)
    if class_count == 0 or any(len(row) != class_count for row in matrix):
        raise HydraulicDataError("confusion matrix must be nonempty and square")
    totals = [sum(row) for row in matrix]
    if any(total == 0 for total in totals):
        raise HydraulicDataError("confusion matrix has an empty true class")
    correct = sum(matrix[index][index] for index in range(class_count))
    total = sum(totals)
    recalls = tuple(
        Fraction(matrix[index][index], totals[index]) for index in range(class_count)
    )
    balanced = sum(recalls, Fraction()) / class_count
    return {
        "correct": correct,
        "total": total,
        "accuracy_ppm": round_ratio_half_even(correct * 1_000_000, total),
        "balanced_accuracy_ppm": round_ratio_half_even(
            balanced.numerator * 1_000_000, balanced.denominator
        ),
        "per_class_recall_ppm": [
            round_ratio_half_even(value.numerator * 1_000_000, value.denominator)
            for value in recalls
        ],
        "majority_class_baseline_ppm": round_ratio_half_even(
            max(totals) * 1_000_000, total
        ),
        "confusion": [list(row) for row in matrix],
    }


def confusion_from_pairs(
    pairs: Iterable[tuple[int, int]], class_count: int
) -> dict:
    matrix = [[0 for _ in range(class_count)] for _ in range(class_count)]
    for truth, prediction in pairs:
        matrix[truth][prediction] += 1
    return summarize_confusion(matrix)


def plurality(values: Sequence[int], class_count: int) -> int:
    counts = Counter(values)
    return min(range(class_count), key=lambda label: (-counts[label], label))


def cycle_pairs(
    rows: Sequence[HydraulicWindow],
    predict: Callable[[Sequence[int]], int],
    class_count: int,
    *,
    binary_truth: bool = False,
) -> tuple[tuple[int, int], ...]:
    predictions: dict[int, list[int]] = defaultdict(list)
    truths: dict[int, int] = {}
    for row in rows:
        truth = int(row.label != 0) if binary_truth else row.label
        if row.cycle in truths and truths[row.cycle] != truth:
            raise HydraulicDataError("one cycle has multiple truth labels")
        truths[row.cycle] = truth
        predictions[row.cycle].append(predict(row.features))
    if any(len(items) != 16 for items in predictions.values()):
        raise HydraulicDataError("cycle decision does not contain 16 windows")
    return tuple(
        (truths[cycle], plurality(predictions[cycle], class_count))
        for cycle in sorted(predictions)
    )


def fit_threshold(train: Sequence[HydraulicWindow]) -> dict:
    """Fit one scalar no-leakage/leakage threshold with stable tie breaks."""
    best = None
    for feature_index in range(len(FEATURE_NAMES)):
        ordered = sorted(
            (row.features[feature_index], int(row.label != 0)) for row in train
        )
        total_positive = sum(label for _, label in ordered)
        total_negative = len(ordered) - total_positive
        left_positive = left_negative = 0
        boundaries = [(2 * ordered[0][0] - 1, 0, 0)]
        index = 0
        while index < len(ordered):
            value = ordered[index][0]
            while index < len(ordered) and ordered[index][0] == value:
                if ordered[index][1]:
                    left_positive += 1
                else:
                    left_negative += 1
                index += 1
            boundary = value + ordered[index][0] if index < len(ordered) else 2 * value + 1
            boundaries.append((boundary, left_negative, left_positive))
        for twice_threshold, left_negative, left_positive in boundaries:
            for positive_above in (False, True):
                right_negative = total_negative - left_negative
                right_positive = total_positive - left_positive
                errors = (
                    left_positive + right_negative
                    if positive_above else left_negative + right_positive
                )
                candidate = (errors, feature_index, twice_threshold, positive_above)
                if best is None or candidate < best:
                    best = candidate
    assert best is not None
    return {
        "training_window_errors": best[0],
        "feature_index": best[1],
        "feature_name": FEATURE_NAMES[best[1]],
        "twice_threshold": best[2],
        "leakage_above": best[3],
    }


def threshold_predictor(threshold: dict) -> Callable[[Sequence[int]], int]:
    def predict(features: Sequence[int]) -> int:
        above = 2 * features[threshold["feature_index"]] > threshold["twice_threshold"]
        return int(above == threshold["leakage_above"])

    return predict


def fit_centroids(train: Sequence[HydraulicWindow]) -> tuple[tuple[int, ...], ...]:
    centroids = []
    for label in range(len(CLASS_NAMES)):
        rows = [row.features for row in train if row.label == label]
        if not rows:
            raise HydraulicDataError(f"training fold has no {CLASS_NAMES[label]} rows")
        centroids.append(tuple(
            round_ratio_half_even(sum(row[index] for row in rows), len(rows))
            for index in range(len(FEATURE_NAMES))
        ))
    return tuple(centroids)


def centroid_predictor(
    centroids: Sequence[Sequence[int]],
) -> Callable[[Sequence[int]], int]:
    return lambda features: min(
        range(len(centroids)),
        key=lambda label: (squared_distance(features, centroids[label]), label),
    )


def som_predictor(document: dict) -> Callable[[Sequence[int]], int]:
    nodes = sorted(document["nodes"], key=lambda node: node["id"])

    def predict(features: Sequence[int]) -> int:
        winner = min(nodes, key=lambda node: (
            squared_distance(features, tuple(value["p"] for value in node["weights"])),
            node["id"],
        ))
        return winner["class_label"]

    return predict


def normalize_fold(
    rows: Sequence[HydraulicWindow], fold_by_group: dict, fold: int
) -> tuple[tuple[HydraulicWindow, ...], tuple[HydraulicWindow, ...], object, dict]:
    raw_train = tuple(row for row in rows if fold_by_group[row.nuisance_group] != fold)
    raw_test = tuple(row for row in rows if fold_by_group[row.nuisance_group] == fold)
    scaler = fit_scaler(row.features for row in raw_train)
    normalized: dict[str, list[HydraulicWindow]] = {"train": [], "test": []}
    diagnostics = {}
    for split, source in (("train", raw_train), ("test", raw_test)):
        low = [0] * len(FEATURE_NAMES)
        high = [0] * len(FEATURE_NAMES)
        any_clamped = all_clamped = 0
        for row in source:
            features, direction = scaler.project(row.features)
            normalized[split].append(replace(row, features=features))
            clamped = sum(value != 0 for value in direction)
            any_clamped += clamped != 0
            all_clamped += clamped == len(FEATURE_NAMES)
            for index, value in enumerate(direction):
                low[index] += value < 0
                high[index] += value > 0
        raw_unique = len({row.features for row in source})
        normalized_unique = len({row.features for row in normalized[split]})
        diagnostics[split] = {
            "low_by_feature": low,
            "high_by_feature": high,
            "windows_with_clamping": any_clamped,
            "windows_with_all_features_clamped": all_clamped,
            "raw_unique_vectors": raw_unique,
            "normalized_unique_vectors": normalized_unique,
            "unique_vectors_lost": raw_unique - normalized_unique,
        }
    return (
        tuple(normalized["train"]), tuple(normalized["test"]), scaler, diagnostics
    )


def feature_csv_bytes(rows: Sequence[HydraulicWindow]) -> bytes:
    lines = [",".join((
        "cycle", "cooler", "valve", "accumulator", "window",
        *FEATURE_NAMES, "state",
    ))]
    for row in rows:
        cooler, valve, accumulator = row.nuisance_group
        lines.append(",".join((
            str(row.cycle), str(cooler), str(valve), str(accumulator),
            str(row.window), *map(str, row.features), CLASS_NAMES[row.label],
        )))
    return ("\n".join(lines) + "\n").encode("ascii")


def class_cycle_counts(rows: Sequence[HydraulicWindow]) -> list[int]:
    labels = {row.cycle: row.label for row in rows}
    return [sum(label == wanted for label in labels.values()) for wanted in range(3)]


def add_matrix(target: list[list[int]], source: Sequence[Sequence[int]]) -> None:
    for row in range(len(target)):
        for column in range(len(target)):
            target[row][column] += source[row][column]


def run_case_study(manifest_path: Path, source_root: Path, output: Path) -> dict:
    manifest = load_manifest(manifest_path)
    verify_source_files(manifest, source_root)
    rows = tuple(iter_stable_windows(source_root / "EPS1.txt", source_root / "profile.txt"))
    cycles = {row.cycle for row in rows}
    groups = {row.nuisance_group for row in rows}
    if len(rows) != EXPECTED_WINDOWS or len(cycles) != EXPECTED_CYCLES:
        raise HydraulicDataError(
            f"stable source shape is {len(cycles)} cycles/{len(rows)} windows"
        )
    if len(groups) != EXPECTED_GROUPS:
        raise HydraulicDataError(f"source has {len(groups)} nuisance groups")
    if class_cycle_counts(rows) != [489, 480, 480]:
        raise HydraulicDataError("stable pump class counts changed")
    fold_by_group = assign_group_folds(groups)
    if Counter(fold_by_group.values()) != Counter({0: 10, 1: 10, 2: 10, 3: 9, 4: 9}):
        raise HydraulicDataError("nuisance-group fold balance changed")

    output.mkdir(parents=True, exist_ok=True)
    aggregate_matrices = {
        "majority_three_class": [[0] * 3 for _ in range(3)],
        "centroid_three_class": [[0] * 3 for _ in range(3)],
        "som_three_class": [[0] * 3 for _ in range(3)],
        "threshold_binary": [[0] * 2 for _ in range(2)],
        "som_binary": [[0] * 2 for _ in range(2)],
    }
    report = {
        "format": "SPU_HYDRAULIC_PUMP_SOM_RESULT_V1",
        "manifest_sha256": sha256_path(manifest_path),
        "source_archive_sha256": manifest["source"]["archive_sha256"],
        "class_names": list(CLASS_NAMES),
        "feature_names": list(FEATURE_NAMES),
        "stable_cycles": len(cycles),
        "windows": len(rows),
        "nuisance_groups": len(groups),
        "folds": [],
    }

    for fold in range(FOLD_COUNT):
        train, test, scaler, diagnostics = normalize_fold(rows, fold_by_group, fold)
        train_bytes = feature_csv_bytes(train)
        test_bytes = feature_csv_bytes(test)
        train_name = f"fold{fold}_train.csv"
        test_name = f"fold{fold}_test.csv"
        (output / train_name).write_bytes(train_bytes)
        (output / test_name).write_bytes(test_bytes)
        model_name = f"hydraulic-pump-fold{fold}-som-v1"
        document = build_map_document(
            tuple((row.features, row.label) for row in train),
            model=model_name,
            dataset="UCI hydraulic stable pump-leakage training fold",
            dataset_path=train_name,
            dataset_sha256=hashlib.sha256(train_bytes).hexdigest(),
            scale=1,
            feature_names=FEATURE_NAMES,
            class_names=CLASS_NAMES,
        )
        map_name = f"fold{fold}_som_v1.json"
        write_map(output / map_name, document)
        load_map(output / map_name)

        train_cycle_labels = {row.cycle: row.label for row in train}
        majority_label = min(range(3), key=lambda label: (
            -sum(value == label for value in train_cycle_labels.values()), label
        ))
        threshold = fit_threshold(train)
        threshold_predict = threshold_predictor(threshold)
        centroids = fit_centroids(train)
        centroid_predict = centroid_predictor(centroids)
        som_predict = som_predictor(document)

        metric_pairs = {
            "majority_three_class": cycle_pairs(test, lambda _: majority_label, 3),
            "centroid_three_class": cycle_pairs(test, centroid_predict, 3),
            "som_three_class": cycle_pairs(test, som_predict, 3),
            "threshold_binary": cycle_pairs(
                test, threshold_predict, 2, binary_truth=True
            ),
            "som_binary": cycle_pairs(
                test, lambda features: int(som_predict(features) != 0), 2,
                binary_truth=True,
            ),
        }
        metrics = {
            name: confusion_from_pairs(pairs, 2 if name.endswith("binary") else 3)
            for name, pairs in metric_pairs.items()
        }
        for name, metric in metrics.items():
            add_matrix(aggregate_matrices[name], metric["confusion"])

        evidence = replay_current_windows(
            document, ((row.features, row.label) for row in test)
        )
        manual_labels = [som_predict(row.features) for row in test]
        if any(item.parsed.label != label for item, label in zip(evidence, manual_labels)):
            raise HydraulicDataError("SOM1 oracle and cycle evaluator disagree")
        exact_ties = sum(item.parsed.ambiguous for item in evidence)
        test_groups = sorted(
            (group for group, assigned in fold_by_group.items() if assigned == fold)
        )
        fold_report = {
            "fold": fold,
            "test_nuisance_groups": [list(group) for group in test_groups],
            "training_cycles_by_class": class_cycle_counts(train),
            "test_cycles_by_class": class_cycle_counts(test),
            "training_windows": len(train),
            "test_windows": len(test),
            "feature_scaler": {
                "minima": list(scaler.minima),
                "maxima": list(scaler.maxima),
                "normalized_limit": scaler.limit,
            },
            "range_diagnostics": diagnostics,
            "threshold": threshold,
            "centroids": [list(row) for row in centroids],
            "training_feature_sha256": hashlib.sha256(train_bytes).hexdigest(),
            "test_feature_sha256": hashlib.sha256(test_bytes).hexdigest(),
            "map_sha256": document["map_sha256"],
            "som1_records_verified": len(evidence),
            "exact_tie_windows": exact_ties,
            "metrics": metrics,
        }
        report["folds"].append(fold_report)
        print(
            f"fold={fold} cycles={sum(class_cycle_counts(test))} "
            f"threshold={metrics['threshold_binary']['balanced_accuracy_ppm']/10000:.2f}% "
            f"centroid={metrics['centroid_three_class']['balanced_accuracy_ppm']/10000:.2f}% "
            f"som={metrics['som_three_class']['balanced_accuracy_ppm']/10000:.2f}% "
            f"ties={exact_ties}"
        )

    aggregate = {
        name: summarize_confusion(matrix) for name, matrix in aggregate_matrices.items()
    }
    worst_som = min(
        fold["metrics"]["som_three_class"]["balanced_accuracy_ppm"]
        for fold in report["folds"]
    )
    gates = manifest["gates"]
    replay_gate = gates["hardware_replay_eligible"]
    replay_eligible = (
        aggregate["som_three_class"]["balanced_accuracy_ppm"]
        >= replay_gate["aggregate_three_class_som_balanced_accuracy_ppm_min"]
        and worst_som
        >= replay_gate["worst_fold_three_class_som_balanced_accuracy_ppm_min"]
    )
    superiority = (
        aggregate["som_three_class"]["balanced_accuracy_ppm"]
        > aggregate["centroid_three_class"]["balanced_accuracy_ppm"]
        and aggregate["som_binary"]["balanced_accuracy_ppm"]
        > aggregate["threshold_binary"]["balanced_accuracy_ppm"]
    )
    report["aggregate"] = aggregate
    report["gate_result"] = {
        "worst_fold_three_class_som_balanced_accuracy_ppm": worst_som,
        "hardware_replay_eligible": replay_eligible,
        "baseline_superiority": superiority,
    }
    result_path = output / "hydraulic_pump_som_result_v1.json"
    result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "aggregate "
        f"threshold={aggregate['threshold_binary']['balanced_accuracy_ppm']/10000:.2f}% "
        f"centroid={aggregate['centroid_three_class']['balanced_accuracy_ppm']/10000:.2f}% "
        f"som={aggregate['som_three_class']['balanced_accuracy_ppm']/10000:.2f}% "
        f"som_binary={aggregate['som_binary']['balanced_accuracy_ppm']/10000:.2f}%"
    )
    print(
        f"HYDRAULIC_SOM: PASS replay_eligible={int(replay_eligible)} "
        f"baseline_superiority={int(superiority)} result={result_path}"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    sub = parser.add_subparsers(dest="command", required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--archive-root", default="build/hydraulic_raw")
    verify_parser.add_argument(
        "--source-root", default="build/hydraulic_raw/extracted"
    )
    extract_parser = sub.add_parser("extract")
    extract_parser.add_argument("--archive-root", default="build/hydraulic_raw")
    extract_parser.add_argument(
        "--source-root", default="build/hydraulic_raw/extracted"
    )
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--source-root", default="build/hydraulic_raw/extracted")
    run_parser.add_argument("--output", default="build/hydraulic_pump_som")
    args = parser.parse_args(argv)

    try:
        manifest_path = Path(args.manifest)
        manifest = load_manifest(manifest_path)
        if args.command == "verify":
            verify_archive(manifest, Path(args.archive_root))
            verify_source_files(manifest, Path(args.source_root))
            print("HYDRAULIC_SOURCES: PASS")
        elif args.command == "extract":
            extract_sources(manifest, Path(args.archive_root), Path(args.source_root))
            print("HYDRAULIC_EXTRACT: PASS")
        else:
            run_case_study(
                manifest_path, Path(args.source_root), Path(args.output)
            )
    except (OSError, json.JSONDecodeError, zipfile.BadZipFile, HydraulicDataError, ValueError) as exc:
        print(f"HYDRAULIC_SOM: FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
