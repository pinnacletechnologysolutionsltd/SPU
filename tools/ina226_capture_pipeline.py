#!/usr/bin/env python3
"""Prepare, validate, and score the frozen INA226 coarse-monitor capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Iterable, Sequence


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.ina226_capture import (  # noqa: E402
    CLASS_NAMES,
    FOLD_COUNT,
    CaptureDataError,
    CaptureWindow,
    build_manifest,
    canonical_json_bytes,
    feature_csv_bytes,
    fit_scaler,
    load_manifest,
    manifest_windows,
    seal_manifest,
)
from lib.som_current_monitor import replay_current_windows  # noqa: E402
from som_map import write_map  # noqa: E402
from som_trainer import build_map_document, squared_distance  # noqa: E402


DEFAULT_CONTRACT = REPO / "software/datasets/ina226_coarse_monitor_v1.json"


def round_ratio_half_even(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if remainder * 2 > denominator or (
        remainder * 2 == denominator and quotient & 1
    ):
        quotient += 1
    return sign * quotient


def plurality(labels: Iterable[int]) -> int:
    counts = Counter(labels)
    if not counts:
        raise CaptureDataError("cannot vote over an empty session")
    return min(counts, key=lambda label: (-counts[label], label))


def confusion_from_pairs(pairs: Iterable[tuple[int, int]], classes: int) -> dict:
    matrix = [[0] * classes for _ in range(classes)]
    for truth, predicted in pairs:
        matrix[truth][predicted] += 1
    total = sum(map(sum, matrix))
    correct = sum(matrix[index][index] for index in range(classes))
    recalls = []
    for index in range(classes):
        support = sum(matrix[index])
        recalls.append(
            round_ratio_half_even(matrix[index][index] * 1_000_000, support)
            if support else 0
        )
    return {
        "confusion": matrix,
        "correct": correct,
        "total": total,
        "accuracy_ppm": round_ratio_half_even(correct * 1_000_000, total),
        "balanced_accuracy_ppm": round_ratio_half_even(sum(recalls), classes),
        "per_class_recall_ppm": recalls,
    }


def aggregate_confusions(folds: Sequence[dict], key: str, classes: int) -> dict:
    matrix = [[0] * classes for _ in range(classes)]
    for fold in folds:
        for truth in range(classes):
            for predicted in range(classes):
                matrix[truth][predicted] += fold["metrics"][key]["confusion"][truth][predicted]
    pairs = []
    for truth in range(classes):
        for predicted in range(classes):
            pairs.extend([(truth, predicted)] * matrix[truth][predicted])
    return confusion_from_pairs(pairs, classes)


def session_pairs(
    rows: Sequence[CaptureWindow], predictor: Callable[[Sequence[int]], int],
    *, binary_truth: bool = False,
) -> tuple[tuple[int, int], ...]:
    grouped: dict[str, list[CaptureWindow]] = defaultdict(list)
    for row in rows:
        grouped[row.session_id].append(row)
    pairs = []
    for session_id in sorted(grouped):
        session = sorted(grouped[session_id], key=lambda row: row.window)
        if len(session) != 4:
            raise CaptureDataError(f"session {session_id} does not contain four windows")
        truths = {row.label for row in session}
        if len(truths) != 1:
            raise CaptureDataError(f"session {session_id} has mixed labels")
        truth = next(iter(truths))
        if binary_truth:
            truth = int(truth != 0)
        pairs.append((truth, plurality(predictor(row.features) for row in session)))
    return tuple(pairs)


def fit_centroids(rows: Sequence[tuple[tuple[int, ...], int]]) -> tuple[tuple[int, ...], ...]:
    centroids = []
    for label in range(len(CLASS_NAMES)):
        selected = [features for features, truth in rows if truth == label]
        if not selected:
            raise CaptureDataError(f"training fold has no {CLASS_NAMES[label]} rows")
        centroids.append(tuple(
            round_ratio_half_even(sum(row[lane] for row in selected), len(selected))
            for lane in range(4)
        ))
    return tuple(centroids)


def centroid_predictor(centroids: Sequence[Sequence[int]]) -> Callable[[Sequence[int]], int]:
    return lambda features: min(
        range(len(centroids)),
        key=lambda label: (squared_distance(features, centroids[label]), label),
    )


def fit_threshold(rows: Sequence[CaptureWindow]) -> dict:
    """Fit one scalar normal/anomaly threshold using training windows only."""
    best: tuple[int, int, int, bool] | None = None
    for feature_index in range(4):
        values = sorted({row.features[feature_index] for row in rows})
        boundaries = [2 * values[0] - 1]
        boundaries.extend(a + b for a, b in zip(values, values[1:]))
        boundaries.append(2 * values[-1] + 1)
        for twice_threshold in boundaries:
            for anomaly_above in (False, True):
                errors = 0
                for row in rows:
                    above = 2 * row.features[feature_index] > twice_threshold
                    predicted = int(above == anomaly_above)
                    errors += predicted != int(row.label != 0)
                candidate = (errors, feature_index, twice_threshold, anomaly_above)
                if best is None or candidate < best:
                    best = candidate
    assert best is not None
    return {
        "training_errors": best[0],
        "feature_index": best[1],
        "feature_name": (
            "mean_current_mA",
            "peak_to_peak_mA",
            "mean_abs_delta_mA",
            "mean_abs_deviation_mA",
        )[best[1]],
        "twice_threshold": best[2],
        "anomaly_above": best[3],
    }


def threshold_predictor(threshold: dict) -> Callable[[Sequence[int]], int]:
    def predict(features: Sequence[int]) -> int:
        above = 2 * features[threshold["feature_index"]] > threshold["twice_threshold"]
        return int(above == threshold["anomaly_above"])
    return predict


def normalized_rows(
    rows: Sequence[CaptureWindow], scaler,
) -> tuple[tuple[CaptureWindow, tuple[int, ...], tuple[int, ...]], ...]:
    return tuple((row, *scaler.project(row.features)) for row in rows)


def normalized_training_csv(
    rows: Sequence[tuple[CaptureWindow, tuple[int, ...], tuple[int, ...]]]
) -> bytes:
    lines = ["f0,f1,f2,f3,state"]
    for row, features, _directions in rows:
        lines.append(",".join((*map(str, features), CLASS_NAMES[row.label])))
    return ("\n".join(lines) + "\n").encode("ascii")


def _som_session_pairs(
    rows: Sequence[tuple[CaptureWindow, tuple[int, ...], tuple[int, ...]]], document: dict
) -> tuple[tuple[tuple[int, int], ...], dict]:
    evidence = replay_current_windows(
        document, ((features, row.label) for row, features, _ in rows)
    )
    grouped: dict[str, list[tuple[CaptureWindow, int]]] = defaultdict(list)
    gaps = []
    exact_ties = 0
    for (row, _features, _), item in zip(rows, evidence):
        if (
            item.parsed.winner != item.oracle.best_node_id
            or item.parsed.runner_up != item.oracle.second_node_id
            or item.parsed.label != item.oracle.cluster_label
        ):
            raise CaptureDataError("SOM1 parser disagrees with exact BMU oracle")
        grouped[row.session_id].append((row, item.parsed.label))
        gap = item.oracle.confidence_gap.p
        if item.oracle.confidence_gap.q != 0:
            raise CaptureDataError("integer capture unexpectedly produced a surd gap")
        gaps.append(gap)
        exact_ties += gap == 0
    pairs = []
    for session_id in sorted(grouped):
        session = sorted(grouped[session_id], key=lambda item: item[0].window)
        pairs.append((session[0][0].label, plurality(prediction for _, prediction in session)))
    ordered_gaps = sorted(gaps)
    return tuple(pairs), {
        "som1_records": len(evidence),
        "som1_oracle_matches": len(evidence),
        "exact_ties": exact_ties,
        "confidence_gap": {
            "min": ordered_gaps[0],
            "median_lower": ordered_gaps[(len(ordered_gaps) - 1) // 2],
            "max": ordered_gaps[-1],
        },
    }


def run_study(manifest: dict, manifest_path: Path, output_dir: Path) -> dict:
    if manifest["contract"]["sha256"] != hashlib.sha256(DEFAULT_CONTRACT.read_bytes()).hexdigest():
        raise CaptureDataError("manifest does not pin the checked-in frozen contract")
    windows = manifest_windows(manifest, manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "capture_features_v1.csv").write_bytes(feature_csv_bytes(windows))
    folds = []
    for fold_index in range(FOLD_COUNT):
        train = tuple(row for row in windows if row.fold != fold_index)
        test = tuple(row for row in windows if row.fold == fold_index)
        scaler = fit_scaler(row.features for row in train)
        train_norm = normalized_rows(train, scaler)
        test_norm = normalized_rows(test, scaler)
        train_csv = normalized_training_csv(train_norm)
        model = f"ina226-coarse-monitor-v1-fold-{fold_index}"
        document = build_map_document(
            [(features, row.label) for row, features, _ in train_norm],
            model=model,
            dataset="INA226 coarse monitor v1 physical capture",
            dataset_path=f"build/ina226_coarse_monitor/fold_{fold_index}_train.csv",
            dataset_sha256=hashlib.sha256(train_csv).hexdigest(),
            scale=1,
            feature_names=(
                "mean_current_mA",
                "peak_to_peak_mA",
                "mean_abs_delta_mA",
                "mean_abs_deviation_mA",
            ),
            class_names=CLASS_NAMES,
        )
        fold_dir = output_dir / f"fold_{fold_index}"
        fold_dir.mkdir(exist_ok=True)
        (fold_dir / "train.csv").write_bytes(train_csv)
        write_map(fold_dir / "map.json", document)

        centroids = fit_centroids([(features, row.label) for row, features, _ in train_norm])
        centroid_by_session: dict[str, list[tuple[CaptureWindow, tuple[int, ...]]]] = defaultdict(list)
        for row, features, _ in test_norm:
            centroid_by_session[row.session_id].append((row, features))
        centroid_pairs = []
        centroid_predict = centroid_predictor(centroids)
        for session_id in sorted(centroid_by_session):
            session = sorted(centroid_by_session[session_id], key=lambda item: item[0].window)
            centroid_pairs.append((
                session[0][0].label,
                plurality(centroid_predict(features) for _, features in session),
            ))

        majority = min(
            range(len(CLASS_NAMES)),
            key=lambda label: (-sum(row.label == label for row in train), label),
        )
        threshold = fit_threshold(train)
        threshold_pairs = session_pairs(
            test, threshold_predictor(threshold), binary_truth=True
        )
        som_pairs, som_diagnostics = _som_session_pairs(test_norm, document)
        binary_som_pairs = tuple((int(truth != 0), int(predicted != 0))
                                 for truth, predicted in som_pairs)
        clamp_counts = [0, 0, 0, 0]
        all_lane_clamps = 0
        for _row, _features, directions in test_norm:
            for lane, direction in enumerate(directions):
                clamp_counts[lane] += direction != 0
            all_lane_clamps += all(direction != 0 for direction in directions)

        metrics = {
            "majority_three_class": confusion_from_pairs(
                ((row.label, majority) for row in test if row.window == 0), 3
            ),
            "threshold_binary": confusion_from_pairs(threshold_pairs, 2),
            "centroid_three_class": confusion_from_pairs(centroid_pairs, 3),
            "som_three_class": confusion_from_pairs(som_pairs, 3),
            "som_binary": confusion_from_pairs(binary_som_pairs, 2),
        }
        folds.append({
            "fold": fold_index,
            "train_sessions": len({row.session_id for row in train}),
            "test_sessions": len({row.session_id for row in test}),
            "scaler": {"minima": list(scaler.minima), "maxima": list(scaler.maxima)},
            "threshold": threshold,
            "centroids": [list(row) for row in centroids],
            "map_sha256": document["map_sha256"],
            "heldout_clamp_counts": clamp_counts,
            "heldout_all_lane_clamps": all_lane_clamps,
            "som_diagnostics": som_diagnostics,
            "metrics": metrics,
        })

    aggregate = {
        "majority_three_class": aggregate_confusions(folds, "majority_three_class", 3),
        "threshold_binary": aggregate_confusions(folds, "threshold_binary", 2),
        "centroid_three_class": aggregate_confusions(folds, "centroid_three_class", 3),
        "som_three_class": aggregate_confusions(folds, "som_three_class", 3),
        "som_binary": aggregate_confusions(folds, "som_binary", 2),
    }
    replay_gate = (
        aggregate["som_three_class"]["balanced_accuracy_ppm"] >= 900_000
        and min(fold["metrics"]["som_three_class"]["balanced_accuracy_ppm"]
                for fold in folds) >= 800_000
        and min(aggregate["som_three_class"]["per_class_recall_ppm"]) >= 800_000
        and all(fold["som_diagnostics"]["som1_records"]
                == fold["som_diagnostics"]["som1_oracle_matches"] for fold in folds)
    )
    superiority_gate = (
        aggregate["som_three_class"]["balanced_accuracy_ppm"]
        > aggregate["centroid_three_class"]["balanced_accuracy_ppm"]
        and aggregate["som_binary"]["balanced_accuracy_ppm"]
        > aggregate["threshold_binary"]["balanced_accuracy_ppm"]
    )
    return {
        "format": "SPU_INA226_COARSE_MONITOR_RESULT_V1",
        "manifest_sha256": hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
        "sessions": len({row.session_id for row in windows}),
        "windows": len(windows),
        "folds": folds,
        "aggregate": aggregate,
        "gates": {
            "hardware_replay_eligible": replay_gate,
            "baseline_superiority_claim_authorized": superiority_gate and replay_gate,
            "literal_baseline_superiority_predicate": superiority_gate,
        },
        "evidence_scope": "physical only when the sealed CSVs are real captures; synthetic fixtures prove plumbing only",
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="write an unsealed 30-session manifest")
    init.add_argument("manifest")
    init.add_argument("--nominal-bus-mv", type=int, required=True)
    init.add_argument("--probe", required=True)
    init.add_argument("--actuator-model", required=True)
    init.add_argument("--actuator-continuous-ma", type=int, required=True)
    init.add_argument("--supply-limit-ma", type=int, required=True)
    seal = sub.add_parser("seal", help="pin all capture CSV SHA-256 values")
    seal.add_argument("manifest")
    verify = sub.add_parser("verify", help="validate a sealed capture without scoring")
    verify.add_argument("manifest")
    run = sub.add_parser("run", help="run the frozen five-fold evaluation")
    run.add_argument("manifest")
    run.add_argument("--output", default="build/ina226_coarse_monitor")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest_path = Path(args.manifest)
        if args.command == "init":
            document = build_manifest(
                contract_path=DEFAULT_CONTRACT,
                nominal_bus_mV=args.nominal_bus_mv,
                probe=args.probe,
                actuator_model=args.actuator_model,
                actuator_continuous_current_mA=args.actuator_continuous_ma,
                supply_current_limit_mA=args.supply_limit_ma,
            )
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_bytes(canonical_json_bytes(document))
            print(f"INA226_CAPTURE_INIT: PASS sessions=30 manifest={manifest_path}")
            return 0
        document = load_manifest(manifest_path)
        if document["contract"]["sha256"] != hashlib.sha256(DEFAULT_CONTRACT.read_bytes()).hexdigest():
            raise CaptureDataError("manifest does not pin the checked-in frozen contract")
        if args.command == "seal":
            document = seal_manifest(document, manifest_path)
            manifest_path.write_bytes(canonical_json_bytes(document))
            print(f"INA226_CAPTURE_SEAL: PASS sessions=30 manifest={manifest_path}")
            return 0
        windows = manifest_windows(document, manifest_path)
        if args.command == "verify":
            print(f"INA226_CAPTURE_VERIFY: PASS sessions=30 windows={len(windows)}")
            return 0
        result = run_study(document, manifest_path, Path(args.output))
        result_path = Path(args.output) / "ina226_coarse_monitor_result_v1.json"
        result_path.write_bytes(canonical_json_bytes(result))
        aggregate = result["aggregate"]["som_three_class"]
        print(
            "INA226_CAPTURE_RUN: PASS "
            f"sessions={result['sessions']} windows={result['windows']} "
            f"som_balanced={aggregate['balanced_accuracy_ppm']/10000:.2f}% "
            f"replay_eligible={result['gates']['hardware_replay_eligible']}"
        )
        print(f"Result SHA-256: {hashlib.sha256(result_path.read_bytes()).hexdigest()}")
        return 0
    except (CaptureDataError, OSError, ValueError) as exc:
        print(f"INA226_CAPTURE_{args.command.upper()}: FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
