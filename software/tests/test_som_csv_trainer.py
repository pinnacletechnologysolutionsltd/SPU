#!/usr/bin/env python3
"""Truth-gate tests for the generalized CSV-to-SOM-map trainer."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from som_map import SomMapError, load_map, validate_map, write_map
from som_trainer import (
    SomTrainingError,
    build_map_document,
    load_csv_dataset,
    parse_scaled_decimal,
)


CSV_TEXT = """current,ripple,slope,variance,state
1.00,0.10,0.00,0.04,normal
1.05,0.12,0.01,0.05,normal
0.96,0.09,-0.01,0.03,normal
1.80,0.40,0.30,0.20,drag
1.75,0.38,0.28,0.18,drag
1.88,0.43,0.35,0.22,drag
0.20,0.85,-0.50,0.70,stall
0.24,0.80,-0.45,0.65,stall
0.18,0.90,-0.55,0.75,stall
"""


checks = 0


def check(name: str, condition: bool) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(name)


def expect_training_error(name: str, function) -> None:
    try:
        function()
    except SomTrainingError:
        check(name, True)
    else:
        raise AssertionError(name)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="spu-som-csv-") as directory:
        root = Path(directory)
        csv_path = root / "motor.csv"
        map_a = root / "motor-a.json"
        map_b = root / "motor-b.json"
        csv_path.write_text(CSV_TEXT, encoding="utf-8")

        dataset = load_csv_dataset(
            csv_path,
            feature_columns=("current", "ripple", "slope", "variance"),
            label_column="state",
            has_header=True,
            scale=100,
        )
        check("nine rows loaded", len(dataset.samples) == 9)
        check("header feature names", dataset.feature_names == (
            "current", "ripple", "slope", "variance"
        ))
        check("labels sorted deterministically", dataset.class_names == (
            "drag", "normal", "stall"
        ))
        check("exact negative decimal", dataset.samples[6][0][2] == -50)

        kwargs = dict(
            model="motor-current-som-v1",
            dataset="synthetic motor current",
            dataset_path=csv_path.name,
            dataset_sha256=dataset.sha256,
            scale=100,
            feature_names=dataset.feature_names,
            class_names=dataset.class_names,
        )
        document_a = build_map_document(dataset.samples, **kwargs)
        document_b = build_map_document(dataset.samples, **kwargs)
        check("bit-exact deterministic training", document_a == document_b)
        write_map(map_a, document_a)
        check("written artifact validates", load_map(map_a) == document_a)

        command = [
            sys.executable,
            str(REPO / "tools" / "train_som_csv.py"),
            str(csv_path),
            "--output",
            str(map_b),
            "--header",
            "--features",
            "current,ripple,slope,variance",
            "--label",
            "state",
            "--scale",
            "100",
            "--model",
            "motor-current-som-v1",
            "--dataset-name",
            "synthetic motor current",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        check("CLI reports pass", result.returncode == 0 and "SOM_CSV_TRAIN: PASS" in result.stdout)
        check("CLI artifact matches API", load_map(map_b) == document_a)

        check("scale parser is exact", parse_scaled_decimal("-1.20", 100) == -120)
        expect_training_error(
            "inexact decimals rejected", lambda: parse_scaled_decimal("1.234", 100)
        )

        tampered = copy.deepcopy(document_a)
        tampered["trainer"]["order_seed"] += 1
        try:
            validate_map(tampered, require_checksum=False)
        except SomMapError:
            check("unpinned schedule rejected", True)
        else:
            raise AssertionError("unpinned schedule rejected")

        eight_class_path = root / "eight.csv"
        eight_class_path.write_text(
            "\n".join(f"{i},0,0,0,class-{i}" for i in range(8)) + "\n",
            encoding="utf-8",
        )
        expect_training_error(
            "more classes than nodes rejected",
            lambda: load_csv_dataset(eight_class_path, scale=1),
        )

    print(f"PASS: generalized SOM CSV trainer ({checks} checks)")


if __name__ == "__main__":
    main()
