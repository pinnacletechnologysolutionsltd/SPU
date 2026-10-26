#!/usr/bin/env python3
"""Truth gate for synthetic current traces through temporal features and SOM1."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.som_current_monitor import (
    CLASS_NAMES,
    REPLAY_CASES_PER_CLASS,
    WINDOW_SAMPLES,
    extract_current_features,
    feature_csv_bytes,
    generate_current_window,
    generated_feature_rows,
    replay_current_windows,
    round_ratio_half_even,
)
from som_map import load_map
from som_sensor_replay import DATASET, MODEL, build_document, run_replay


DATASET_SHA256 = "4ed7e02b19c9e6b67116faa3f0d421b3958d3dc4a0098eee304550c44d0fe1ef"
MAP_SHA256 = "66bc408abd8111684c039378d4882aebdd77974e272717556c790eb6d8df2614"
checks = 0


def check(name: str, condition: bool) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(name)


def main() -> None:
    check("half-even rounds down to even", round_ratio_half_even(5, 2) == 2)
    check("half-even rounds up to even", round_ratio_half_even(7, 2) == 4)
    check(
        "constant window feature vector",
        extract_current_features((1_000_000,) * WINDOW_SAMPLES) == (1000, 0, 0, 0),
    )

    for class_name in CLASS_NAMES:
        window = generate_current_window(class_name, 100)
        check(f"{class_name} window length", len(window) == WINDOW_SAMPLES)
        check(f"{class_name} window is integer", all(isinstance(v, int) for v in window))

    generated_csv = feature_csv_bytes()
    check("checked feature CSV regenerates", DATASET.read_bytes() == generated_csv)
    check(
        "dataset SHA-256 pinned",
        hashlib.sha256(generated_csv).hexdigest() == DATASET_SHA256,
    )

    regenerated = build_document()
    checked = load_map(MODEL)
    check("checked map regenerates", regenerated == checked)
    check("map SHA-256 pinned", checked["map_sha256"] == MAP_SHA256)

    rows = generated_feature_rows(first_case=100, cases_per_class=REPLAY_CASES_PER_CLASS)
    replay_a = replay_current_windows(checked, rows)
    replay_b = replay_current_windows(checked, rows)
    check("18 holdout windows", len(replay_a) == 18)
    check("bit-exact replay", replay_a == replay_b)
    check("all frames fixed length", all(len(item.frame) == 52 for item in replay_a))
    check(
        "result generations consecutive",
        [item.parsed.result_generation for item in replay_a] == list(range(1, 19)),
    )
    check("map generation pinned", all(item.parsed.map_generation == 1 for item in replay_a))
    check("no ambiguous holdout", not any(item.parsed.ambiguous for item in replay_a))
    check(
        "semantic labels exact",
        all(item.parsed.label == item.true_label for item in replay_a),
    )

    confusion, exact, ambiguous = run_replay(checked)
    check("perfect holdout confusion", confusion == [[6, 0, 0], [0, 6, 0], [0, 0, 6]])
    check("perfect holdout total", exact == 18 and ambiguous == 0)

    print(f"PASS: synthetic current SOM1 replay ({checks} checks)")


if __name__ == "__main__":
    main()
