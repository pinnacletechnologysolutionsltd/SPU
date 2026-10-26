#!/usr/bin/env python3
"""Build and score the leakage-safe Paderborn current-signature pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Sequence


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.paderborn_bearing import (  # noqa: E402
    PROFILE_FEATURE_NAMES,
    PROFILES,
    PaderbornDataError,
    extract_features,
    fit_scaler,
    load_current_recording,
    round_ratio_half_even,
)
from som_map import load_map, write_map  # noqa: E402
from som_trainer import build_map_document, squared_distance  # noqa: E402


DEFAULT_MANIFEST = REPO / "software" / "datasets" / "paderborn_current_pilot_v1.json"
CLASS_NAMES = ("healthy", "inner", "outer")


@dataclass(frozen=True)
class Sample:
    split: str
    bearing: str
    recording: str
    window: int
    features: tuple[int, ...]
    label: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("format") != "SPU_PADERBORN_CURRENT_PILOT_V1":
        raise PaderbornDataError("manifest has the wrong format")
    bearings = document.get("bearings")
    if not isinstance(bearings, list) or len(bearings) != 9:
        raise PaderbornDataError("pilot manifest must contain nine bearings")
    triples = Counter((item.get("class"), item.get("split")) for item in bearings)
    expected = Counter((label, split) for label in CLASS_NAMES for split in ("train", "validation", "test"))
    if triples != expected:
        raise PaderbornDataError("manifest must use one bearing per class and split")
    if any(
        not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64
        for item in bearings
    ):
        raise PaderbornDataError("every source archive requires a SHA-256 checksum")
    return document


def verify_archives(manifest: dict, archive_root: Path) -> None:
    for bearing in manifest["bearings"]:
        path = archive_root / bearing["archive"]
        if not path.is_file():
            raise PaderbornDataError(f"missing source archive {path}")
        expected = bearing.get("sha256")
        if _sha256(path) != expected:
            raise PaderbornDataError(f"source archive checksum mismatch: {path.name}")


def collect_samples(manifest: dict, mat_root: Path) -> dict[str, tuple[Sample, ...]]:
    """Load every MAT recording once and derive all pinned profiles."""
    samples: dict[str, list[Sample]] = {profile: [] for profile in PROFILES}
    for bearing in manifest["bearings"]:
        bearing_id = bearing["id"]
        paths = sorted(
            (mat_root / bearing_id).glob(f"N15_M07_F10_{bearing_id}_*.mat"),
            key=lambda path: int(path.stem.rsplit("_", 1)[1]),
        )
        expected = manifest["operating_condition"]["recordings_per_bearing"]
        if len(paths) != expected:
            raise PaderbornDataError(
                f"{bearing_id}: found {len(paths)} recordings, expected {expected}"
            )
        label = CLASS_NAMES.index(bearing["class"])
        split = bearing.get("split", "all")
        for path in paths:
            recording = load_current_recording(path)
            for profile in PROFILES:
                for window, features in enumerate(extract_features(recording, profile)):
                    samples[profile].append(Sample(
                        split, bearing_id, path.name, window, features, label
                    ))
    return {profile: tuple(rows) for profile, rows in samples.items()}


def normalize_samples(samples: Sequence[Sample], feature_names: Sequence[str]):
    scaler = fit_scaler(sample.features for sample in samples if sample.split == "train")
    normalized: list[Sample] = []
    unclamped: list[Sample] = []

    def empty_stats():
        return {
            "low_by_feature": [0] * len(feature_names),
            "high_by_feature": [0] * len(feature_names),
            "vectors_with_clipping": 0,
            "vectors_with_all_lanes_clipped": 0,
            "unclamped_values_outside_signed_p18": 0,
        }
    split_counts = {
        split: empty_stats() for split in sorted({sample.split for sample in samples})
    }
    bearing_counts = {
        bearing: empty_stats() for bearing in sorted({sample.bearing for sample in samples})
    }
    for sample in samples:
        features, direction = scaler.project(sample.features)
        projected, _ = scaler.project(sample.features, clamp=False)
        clipped = sum(item != 0 for item in direction)
        for stats in (split_counts[sample.split], bearing_counts[sample.bearing]):
            for index, item in enumerate(direction):
                if item < 0:
                    stats["low_by_feature"][index] += 1
                elif item > 0:
                    stats["high_by_feature"][index] += 1
            stats["vectors_with_clipping"] += clipped != 0
            stats["vectors_with_all_lanes_clipped"] += clipped == len(feature_names)
            stats["unclamped_values_outside_signed_p18"] += sum(
                not -(1 << 17) <= value < (1 << 17) for value in projected
            )
        normalized.append(Sample(
            sample.split, sample.bearing, sample.recording, sample.window,
            features, sample.label,
        ))
        unclamped.append(Sample(
            sample.split, sample.bearing, sample.recording, sample.window,
            projected, sample.label,
        ))
    for counts, attribute in ((split_counts, "split"), (bearing_counts, "bearing")):
        for name, stats in counts.items():
            raw_vectors = {
                sample.features for sample in samples if getattr(sample, attribute) == name
            }
            normalized_vectors = {
                sample.features for sample in normalized
                if getattr(sample, attribute) == name
            }
            stats["raw_unique_vectors"] = len(raw_vectors)
            stats["normalized_unique_vectors"] = len(normalized_vectors)
            stats["unique_vectors_lost"] = len(raw_vectors) - len(normalized_vectors)
            stats["clipped_feature_values"] = sum(stats["low_by_feature"]) + sum(
                stats["high_by_feature"]
            )
    return (
        tuple(normalized), tuple(unclamped), scaler,
        {"splits": split_counts, "bearings": bearing_counts},
    )


def csv_bytes(samples: Sequence[Sample], feature_names: Sequence[str]) -> bytes:
    lines = [",".join(("split", "bearing", "recording", "window", *feature_names, "state"))]
    for sample in samples:
        lines.append(",".join((
            sample.split, sample.bearing, sample.recording, str(sample.window),
            *map(str, sample.features), CLASS_NAMES[sample.label],
        )))
    return ("\n".join(lines) + "\n").encode("ascii")


def summarize_confusion(matrix: Sequence[Sequence[int]]) -> dict:
    class_count = len(matrix)
    if class_count == 0 or any(len(row) != class_count for row in matrix):
        raise PaderbornDataError("confusion matrix must be nonempty and square")
    correct = sum(matrix[index][index] for index in range(class_count))
    total = sum(map(sum, matrix))
    if total == 0 or any(sum(row) == 0 for row in matrix):
        raise PaderbornDataError("confusion matrix has an empty true class")
    recalls = tuple(
        Fraction(matrix[index][index], sum(matrix[index]))
        for index in range(class_count)
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
            max(sum(row) for row in matrix) * 1_000_000, total
        ),
        "confusion": [list(row) for row in matrix],
    }


def confusion(samples: Sequence[Sample], predict, class_count: int) -> dict:
    matrix = [[0 for _ in range(class_count)] for _ in range(class_count)]
    for sample in samples:
        matrix[sample.label][predict(sample.features)] += 1
    return summarize_confusion(matrix)


def fit_centroids(train: Sequence[Sample]) -> tuple[tuple[int, ...], ...]:
    centroids = []
    for label in range(len(CLASS_NAMES)):
        rows = [sample.features for sample in train if sample.label == label]
        if not rows:
            raise PaderbornDataError(f"training split has no {CLASS_NAMES[label]} rows")
        centroids.append(tuple(
            round_ratio_half_even(sum(row[index] for row in rows), len(rows))
            for index in range(len(train[0].features))
        ))
    return tuple(centroids)


def fit_threshold(train: Sequence[Sample], feature_names: Sequence[str]) -> dict:
    """Fit one auditable scalar threshold for healthy-vs-damaged detection."""
    best = None
    for feature_index in range(len(feature_names)):
        ordered = sorted(
            (sample.features[feature_index], int(sample.label != 0))
            for sample in train
        )
        total_damaged = sum(label for _, label in ordered)
        total_healthy = len(ordered) - total_damaged
        left_damaged = left_healthy = 0
        boundaries = [(2 * ordered[0][0] - 1, left_healthy, left_damaged)]
        index = 0
        while index < len(ordered):
            value = ordered[index][0]
            while index < len(ordered) and ordered[index][0] == value:
                if ordered[index][1]:
                    left_damaged += 1
                else:
                    left_healthy += 1
                index += 1
            if index < len(ordered):
                boundaries.append((value + ordered[index][0], left_healthy, left_damaged))
            else:
                boundaries.append((2 * value + 1, left_healthy, left_damaged))
        for twice_threshold, left_healthy, left_damaged in boundaries:
            for damaged_above in (False, True):
                right_healthy = total_healthy - left_healthy
                right_damaged = total_damaged - left_damaged
                errors = (
                    left_damaged + right_healthy if damaged_above
                    else left_healthy + right_damaged
                )
                candidate = (errors, feature_index, twice_threshold, damaged_above)
                if best is None or candidate < best:
                    best = candidate
    assert best is not None
    return {
        "training_errors": best[0],
        "feature_index": best[1],
        "feature_name": feature_names[best[1]],
        "twice_threshold": best[2],
        "damaged_above": best[3],
    }


def threshold_confusion(samples: Sequence[Sample], threshold: dict) -> dict:
    def predict(features):
        above = 2 * features[threshold["feature_index"]] > threshold["twice_threshold"]
        return int(above == threshold["damaged_above"])

    binary = [Sample(
        sample.split, sample.bearing, sample.recording, sample.window,
        sample.features, int(sample.label != 0),
    ) for sample in samples]
    return confusion(binary, predict, 2)


def evaluate(
    samples: Sequence[Sample], document: dict, profile: str,
    feature_names: Sequence[str],
) -> dict:
    train = tuple(sample for sample in samples if sample.split == "train")
    centroids = fit_centroids(train)
    threshold = fit_threshold(train, feature_names)
    nodes = sorted(document["nodes"], key=lambda node: node["id"])

    def centroid_predict(features):
        return min(range(len(centroids)), key=lambda label: (
            squared_distance(features, centroids[label]), label
        ))

    def som_predict(features):
        winner = min(nodes, key=lambda node: (
            squared_distance(features, tuple(item["p"] for item in node["weights"])),
            node["id"],
        ))
        return winner["class_label"]

    split_order = tuple(
        split for split in ("train", "validation", "test")
        if any(sample.split == split for sample in samples)
    )
    metrics = {"profile": profile, "threshold": threshold, "splits": {}}
    for split in split_order:
        rows = tuple(sample for sample in samples if sample.split == split)
        winners = [
            min(nodes, key=lambda node: (
                squared_distance(
                    sample.features,
                    tuple(item["p"] for item in node["weights"]),
                ),
                node["id"],
            ))
            for sample in rows
        ]
        by_bearing = {}
        for bearing in sorted({sample.bearing for sample in rows}):
            bearing_winners = [
                winner for sample, winner in zip(rows, winners)
                if sample.bearing == bearing
            ]
            by_bearing[bearing] = {
                "true_class": CLASS_NAMES[next(
                    sample.label for sample in rows if sample.bearing == bearing
                )],
                "winner_nodes": dict(sorted(Counter(
                    str(winner["id"]) for winner in bearing_winners
                ).items())),
                "winner_labels": dict(sorted(Counter(
                    CLASS_NAMES[winner["class_label"]] for winner in bearing_winners
                ).items())),
                "correct": sum(
                    winner["class_label"] == sample.label
                    for sample, winner in zip(rows, winners)
                    if sample.bearing == bearing
                ),
                "total": len(bearing_winners),
            }
            by_bearing[bearing]["accuracy_ppm"] = round_ratio_half_even(
                by_bearing[bearing]["correct"] * 1_000_000,
                by_bearing[bearing]["total"],
            )
        metrics["splits"][split] = {
            "bearing_ids": sorted({sample.bearing for sample in rows}),
            "samples": len(rows),
            "threshold_binary": threshold_confusion(rows, threshold),
            "centroid_three_class": confusion(rows, centroid_predict, 3),
            "som_three_class": confusion(rows, som_predict, 3),
            "som_winner_nodes": dict(sorted(Counter(
                str(winner["id"]) for winner in winners
            ).items())),
            "som_winner_labels": dict(sorted(Counter(
                CLASS_NAMES[winner["class_label"]] for winner in winners
            ).items())),
            "by_bearing": by_bearing,
        }
    return metrics


def inspect_file(path: Path) -> None:
    recording = load_current_recording(path)
    print(f"recording={recording.source} samples={len(recording.phase_1_uA)} hz=64000")
    for profile in PROFILES:
        rows = extract_features(recording, profile)
        print(f"{profile}: windows={len(rows)} first={rows[0]}")


def run_benchmark(args, manifest: dict) -> None:
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest_hash = hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest()
    all_results = {
        "format": "SPU_PADERBORN_BENCHMARK_V1",
        "manifest_sha256": manifest_hash,
        "class_names": list(CLASS_NAMES),
        "profiles": {},
    }
    profile_samples = collect_samples(manifest, Path(args.mat_root))
    for profile in PROFILES:
        feature_names = PROFILE_FEATURE_NAMES[profile]
        samples = profile_samples[profile]
        samples, unclamped, scaler, range_diagnostics = normalize_samples(
            samples, feature_names
        )
        features_path = output / f"paderborn_{profile}_features.csv"
        features = csv_bytes(samples, feature_names)
        features_path.write_bytes(features)
        train_samples = tuple(sample for sample in samples if sample.split == "train")
        train_features_path = output / f"paderborn_{profile}_train.csv"
        train_features = csv_bytes(train_samples, feature_names)
        train_features_path.write_bytes(train_features)
        train = tuple((sample.features, sample.label) for sample in train_samples)
        model_name = f"paderborn-current-{profile}-som-v1"
        document = build_map_document(
            train,
            model=model_name,
            dataset="Paderborn current-signature pilot, N15_M07_F10",
            dataset_path=train_features_path.name,
            dataset_sha256=hashlib.sha256(train_features).hexdigest(),
            scale=1,
            feature_names=feature_names,
            class_names=CLASS_NAMES,
        )
        model_path = output / f"{model_name}.json"
        write_map(model_path, document)
        load_map(model_path)
        result = evaluate(samples, document, profile, feature_names)
        unclamped_result = evaluate(unclamped, document, profile, feature_names)
        result.update({
            "feature_scaler": {
                "minima": list(scaler.minima), "maxima": list(scaler.maxima),
                "normalized_limit": scaler.limit,
            },
            "range_diagnostics": range_diagnostics,
            "unclamped_affine_splits": unclamped_result["splits"],
            "feature_csv_sha256": hashlib.sha256(features).hexdigest(),
            "training_feature_csv_sha256": hashlib.sha256(train_features).hexdigest(),
            "map_sha256": document["map_sha256"],
        })
        all_results["profiles"][profile] = result
        val = result["splits"]["validation"]
        test = result["splits"]["test"]
        print(
            f"{profile}: val threshold={val['threshold_binary']['accuracy_ppm']/10000:.2f}% "
            f"centroid={val['centroid_three_class']['accuracy_ppm']/10000:.2f}% "
            f"som={val['som_three_class']['accuracy_ppm']/10000:.2f}%"
        )
        print(
            f"{profile}: test threshold={test['threshold_binary']['accuracy_ppm']/10000:.2f}% "
            f"centroid={test['centroid_three_class']['accuracy_ppm']/10000:.2f}% "
            f"som={test['som_three_class']['accuracy_ppm']/10000:.2f}%"
        )
    result_path = output / "paderborn_benchmark_v1.json"
    result_path.write_text(json.dumps(all_results, indent=2) + "\n", encoding="utf-8")
    print(f"PADERBORN_BENCHMARK: PASS result={result_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("mat_file")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--archive-root", default="build/paderborn_raw")
    benchmark_parser = sub.add_parser("benchmark")
    benchmark_parser.add_argument("--mat-root", default="build/paderborn_raw/extracted")
    benchmark_parser.add_argument("--output", default="build/paderborn_benchmark")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(Path(args.manifest))
        if args.command == "inspect":
            inspect_file(Path(args.mat_file))
        elif args.command == "verify":
            verify_archives(manifest, Path(args.archive_root))
            print("PADERBORN_ARCHIVES: PASS")
        else:
            run_benchmark(args, manifest)
    except (OSError, PaderbornDataError, ValueError) as exc:
        print(f"PADERBORN_BENCHMARK: FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
