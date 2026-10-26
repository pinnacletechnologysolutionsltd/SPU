#!/usr/bin/env python3
"""Offline truth gates for the predeclared hydraulic pump SOM study."""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.hydraulic_pump import (  # noqa: E402
    FEATURE_NAMES,
    HydraulicDataError,
    HydraulicProfile,
    HydraulicWindow,
    assign_group_folds,
    cycle_windows,
    extract_power_features,
    fit_scaler,
    fixed_window_starts,
    parse_deciwatts,
    parse_profile_line,
    round_ratio_half_even,
)
from hydraulic_som_case_study import (  # noqa: E402
    DEFAULT_MANIFEST,
    confusion_from_pairs,
    cycle_pairs,
    feature_csv_bytes,
    fit_threshold,
    load_manifest,
    plurality,
    threshold_predictor,
)


def main() -> None:
    checks = 0

    def check(name: str, condition: bool) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(name)

    check("half-even lower", round_ratio_half_even(1, 2) == 0)
    check("half-even upper", round_ratio_half_even(3, 2) == 2)
    check("exact integer watts", parse_deciwatts("2411") == 24_110)
    check("exact decimal watts", parse_deciwatts("2411.6") == 24_116)
    check("redundant zero decimals", parse_deciwatts("-1.00") == -10)
    try:
        parse_deciwatts("1.25")
    except HydraulicDataError:
        pass
    else:
        raise AssertionError("non-deciwatt source accepted")
    checks += 1

    profile = parse_profile_line("20 90 2 115 0", 7)
    check("profile fields", profile == HydraulicProfile(20, 90, 2, 115, 0))
    check("nuisance excludes pump", profile.nuisance_group == (20, 90, 115))

    starts = fixed_window_starts()
    check("sixteen fixed windows", len(starts) == 16)
    check("window endpoints", starts[0] == 0 and starts[-1] == 5968)
    check("windows do not overlap", all(b - a >= 32 for a, b in zip(starts, starts[1:])))

    check(
        "constant features",
        extract_power_features((100,) * 32) == (100, 0, 0, 0),
    )
    check(
        "ramp features",
        extract_power_features(tuple(range(32))) == (16, 31, 1, 8),
    )
    windows = cycle_windows(9, profile, tuple(range(6000)))
    check("cycle creates sixteen rows", len(windows) == 16)
    check(
        "cycle metadata preserved",
        windows[0].cycle == 9
        and windows[0].window == 0
        and windows[0].label == 2
        and windows[-1].window == 15,
    )

    groups = tuple((index, 100, 130) for index in range(10))
    assignments = assign_group_folds(groups)
    check("all groups assigned", set(assignments) == set(groups))
    check(
        "round-robin fold balance",
        sorted(assignments.values()).count(0) == 2
        and all(list(assignments.values()).count(fold) == 2 for fold in range(5)),
    )
    check("fold assignment deterministic", assign_group_folds(reversed(groups)) == assignments)

    scaler = fit_scaler(((0, 10, 20, 30), (100, 110, 120, 130)))
    projected, direction = scaler.project((50, -10, 120, 80))
    check("training affine projection", projected == (15_000, 0, 30_000, 15_000))
    check("range directions", direction == (0, -1, 0, 0))

    manifest = load_manifest(DEFAULT_MANIFEST)
    check("manifest DOI", manifest["source"]["doi"] == "10.24432/C5CW21")
    check("manifest licence", manifest["source"]["license"] == "CC BY 4.0")
    check("manifest features", tuple(manifest["features"]) == FEATURE_NAMES)

    check("plurality", plurality((2, 2, 1, 1), 3) == 1)
    matrix = confusion_from_pairs(((0, 0), (1, 1), (2, 1)), 3)
    check(
        "confusion summary",
        matrix["correct"] == 2
        and matrix["total"] == 3
        and matrix["balanced_accuracy_ppm"] == 666_667,
    )

    rows = tuple(
        HydraulicWindow(
            cycle=cycle,
            nuisance_group=(100, 100, 130),
            window=window,
            features=(cycle * 100,) * 4,
            label=cycle,
        )
        for cycle in range(3) for window in range(16)
    )
    pairs = cycle_pairs(rows, lambda features: min(features[0] // 100, 2), 3)
    check("cycle plurality truth", pairs == ((0, 0), (1, 1), (2, 2)))

    threshold = fit_threshold(rows)
    threshold_pairs = cycle_pairs(
        rows, threshold_predictor(threshold), 2, binary_truth=True
    )
    check("threshold separates leakage", threshold_pairs == ((0, 0), (1, 1), (1, 1)))

    csv_data = feature_csv_bytes(rows[:2])
    check("feature CSV header", csv_data.startswith(b"cycle,cooler,valve,accumulator,window,"))
    check("feature CSV deterministic", csv_data == feature_csv_bytes(rows[:2]))

    print(f"PASS: hydraulic pump SOM contract ({checks} checks)")


if __name__ == "__main__":
    main()
