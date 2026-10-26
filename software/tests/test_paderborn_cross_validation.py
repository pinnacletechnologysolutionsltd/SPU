#!/usr/bin/env python3
"""Offline truth gates for the 15-bearing Paderborn fold contract."""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from paderborn_benchmark import Sample  # noqa: E402
from paderborn_cross_validate import (  # noqa: E402
    DEFAULT_MANIFEST,
    aggregate_confusions,
    assign_fold,
    load_manifest,
)


def main() -> None:
    checks = 0

    def check(name: str, condition: bool) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(name)

    manifest = load_manifest(DEFAULT_MANIFEST)
    check("15 source bearings", len(manifest["bearings"]) == 15)
    check(
        "five identities per class",
        all(
            sum(item["class"] == name for item in manifest["bearings"]) == 5
            for name in ("healthy", "inner", "outer")
        ),
    )
    check(
        "one identity per class per fold",
        all(
            sum(
                item["class"] == name and item["fold"] == fold
                for item in manifest["bearings"]
            ) == 1
            for name in ("healthy", "inner", "outer") for fold in range(5)
        ),
    )
    check(
        "checksums frozen",
        all(len(item["sha256"]) == 64 for item in manifest["bearings"]),
    )

    fold_by_bearing = {item["id"]: item["fold"] for item in manifest["bearings"]}
    rows = tuple(
        Sample("all", item["id"], "recording", 0, (1, 2, 3, 4), index // 5)
        for index, item in enumerate(manifest["bearings"])
    )
    assigned = assign_fold(rows, fold_by_bearing, 2)
    check("fold has three test identities", sum(row.split == "test" for row in assigned) == 3)
    check("fold has twelve train identities", sum(row.split == "train" for row in assigned) == 12)

    folds = [{
        "clamped": {"splits": {"test": {
            "threshold_binary": {"confusion": [[0, 2], [0, 4]]},
        }}},
    } for _ in range(5)]
    aggregate = aggregate_confusions(folds, "threshold_binary", 2)
    check("aggregate confusion", aggregate["confusion"] == [[0, 10], [0, 20]])
    check(
        "aggregate balanced baseline",
        aggregate["accuracy_ppm"] == 666_667
        and aggregate["balanced_accuracy_ppm"] == 500_000,
    )

    print(f"PASS: Paderborn cross-validation contract ({checks} checks)")


if __name__ == "__main__":
    main()
