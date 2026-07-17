#!/usr/bin/env python3
"""Run five bearing-level folds over the Paderborn real-damage subset."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.paderborn_bearing import (  # noqa: E402
    PROFILE_FEATURE_NAMES,
    PROFILES,
    PaderbornDataError,
)
from paderborn_benchmark import (  # noqa: E402
    CLASS_NAMES,
    Sample,
    _sha256,
    collect_samples,
    csv_bytes,
    evaluate,
    normalize_samples,
    summarize_confusion,
)
from som_map import load_map, write_map  # noqa: E402
from som_trainer import build_map_document  # noqa: E402


DEFAULT_MANIFEST = REPO / "software" / "datasets" / "paderborn_current_cv_v1.json"
FOLD_COUNT = 5


def load_manifest(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("format") != "SPU_PADERBORN_CURRENT_CV_V1":
        raise PaderbornDataError("cross-validation manifest has the wrong format")
    bearings = document.get("bearings")
    if not isinstance(bearings, list) or len(bearings) != 15:
        raise PaderbornDataError("cross-validation manifest must contain 15 bearings")
    class_counts = Counter(item.get("class") for item in bearings)
    if class_counts != Counter({name: FOLD_COUNT for name in CLASS_NAMES}):
        raise PaderbornDataError("manifest must contain five bearings per class")
    fold_counts = Counter((item.get("class"), item.get("fold")) for item in bearings)
    expected = Counter((name, fold) for name in CLASS_NAMES for fold in range(FOLD_COUNT))
    if fold_counts != expected:
        raise PaderbornDataError("every fold requires one bearing from each class")
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
        if _sha256(path) != bearing["sha256"]:
            raise PaderbornDataError(f"source archive checksum mismatch: {path.name}")


def assign_fold(
    samples: tuple[Sample, ...], fold_by_bearing: dict[str, int], fold: int
) -> tuple[Sample, ...]:
    return tuple(
        Sample(
            "test" if fold_by_bearing[sample.bearing] == fold else "train",
            sample.bearing,
            sample.recording,
            sample.window,
            sample.features,
            sample.label,
        )
        for sample in samples
    )


def aggregate_confusions(folds: list[dict], metric: str, class_count: int) -> dict:
    matrix = [[0 for _ in range(class_count)] for _ in range(class_count)]
    for fold in folds:
        source = fold["clamped"]["splits"]["test"][metric]["confusion"]
        for truth in range(class_count):
            for prediction in range(class_count):
                matrix[truth][prediction] += source[truth][prediction]
    return summarize_confusion(matrix)


def run_cross_validation(args, manifest: dict) -> None:
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    fold_by_bearing = {item["id"]: item["fold"] for item in manifest["bearings"]}
    source_samples = collect_samples(manifest, Path(args.mat_root))
    result = {
        "format": "SPU_PADERBORN_CROSS_VALIDATION_V1",
        "manifest_sha256": hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),
        "class_names": list(CLASS_NAMES),
        "fold_count": FOLD_COUNT,
        "profiles": {},
    }

    for profile in PROFILES:
        feature_names = PROFILE_FEATURE_NAMES[profile]
        profile_result = {"feature_names": list(feature_names), "folds": []}
        profile_output = output / profile
        profile_output.mkdir(parents=True, exist_ok=True)
        for fold in range(FOLD_COUNT):
            fold_raw = assign_fold(source_samples[profile], fold_by_bearing, fold)
            samples, unclamped, scaler, range_diagnostics = normalize_samples(
                fold_raw, feature_names
            )
            train_samples = tuple(sample for sample in samples if sample.split == "train")
            all_features = csv_bytes(samples, feature_names)
            train_features = csv_bytes(train_samples, feature_names)
            all_path = profile_output / f"fold{fold}_features.csv"
            train_path = profile_output / f"fold{fold}_train.csv"
            all_path.write_bytes(all_features)
            train_path.write_bytes(train_features)

            model_name = f"paderborn-current-{profile}-fold{fold}-som-v1"
            document = build_map_document(
                tuple((sample.features, sample.label) for sample in train_samples),
                model=model_name,
                dataset="Paderborn current real-damage 15-bearing cross-validation",
                dataset_path=str(train_path.relative_to(output)),
                dataset_sha256=hashlib.sha256(train_features).hexdigest(),
                scale=1,
                feature_names=feature_names,
                class_names=CLASS_NAMES,
            )
            model_path = profile_output / f"fold{fold}_som_v1.json"
            write_map(model_path, document)
            load_map(model_path)
            clamped = evaluate(samples, document, profile, feature_names)
            unclamped_result = evaluate(unclamped, document, profile, feature_names)
            fold_result = {
                "fold": fold,
                "test_bearings": sorted(
                    sample.bearing for sample in samples
                    if sample.split == "test" and sample.window == 0
                    and sample.recording.endswith("_1.mat")
                ),
                "feature_scaler": {
                    "minima": list(scaler.minima),
                    "maxima": list(scaler.maxima),
                    "normalized_limit": scaler.limit,
                },
                "range_diagnostics": range_diagnostics,
                "clamped": clamped,
                "unclamped_affine_splits": unclamped_result["splits"],
                "feature_csv_sha256": hashlib.sha256(all_features).hexdigest(),
                "training_feature_csv_sha256": hashlib.sha256(train_features).hexdigest(),
                "map_sha256": document["map_sha256"],
            }
            profile_result["folds"].append(fold_result)
            test = clamped["splits"]["test"]
            print(
                f"{profile} fold={fold} "
                f"threshold={test['threshold_binary']['accuracy_ppm']/10000:.2f}% "
                f"centroid={test['centroid_three_class']['accuracy_ppm']/10000:.2f}% "
                f"som={test['som_three_class']['accuracy_ppm']/10000:.2f}%"
            )

        profile_result["aggregate"] = {
            "threshold_binary": aggregate_confusions(
                profile_result["folds"], "threshold_binary", 2
            ),
            "centroid_three_class": aggregate_confusions(
                profile_result["folds"], "centroid_three_class", 3
            ),
            "som_three_class": aggregate_confusions(
                profile_result["folds"], "som_three_class", 3
            ),
        }
        aggregate = profile_result["aggregate"]
        print(
            f"{profile} aggregate: "
            f"threshold={aggregate['threshold_binary']['accuracy_ppm']/10000:.2f}% "
            f"centroid={aggregate['centroid_three_class']['accuracy_ppm']/10000:.2f}% "
            f"som={aggregate['som_three_class']['accuracy_ppm']/10000:.2f}%"
        )
        result["profiles"][profile] = profile_result

    result_path = output / "paderborn_cross_validation_v1.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PADERBORN_CV: PASS result={result_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    sub = parser.add_subparsers(dest="command", required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--archive-root", default="build/paderborn_raw")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--mat-root", default="build/paderborn_raw/extracted")
    run_parser.add_argument("--output", default="build/paderborn_cross_validation")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(Path(args.manifest))
        if args.command == "verify":
            verify_archives(manifest, Path(args.archive_root))
            print("PADERBORN_CV_ARCHIVES: PASS")
        else:
            run_cross_validation(args, manifest)
    except (OSError, PaderbornDataError, ValueError) as exc:
        print(f"PADERBORN_CV: FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
