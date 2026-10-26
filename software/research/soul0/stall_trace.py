"""Trace the existing center-180/count-2 regression without changing Soul-0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .heldout_experiment import load_frozen_inputs
from .model import RollingMeanBaseline, Soul0


def build_stall_trace() -> dict:
    fixture, fixture_hash, manifest_hash = load_frozen_inputs()
    threshold = fixture["threshold"]
    phase = fixture["phases"]["regime_b"]
    values = [phase["nominal_center"] + fixture["noise_cycle"][i % 5] for i in range(16)]
    soul = Soul0([(180, 2)], threshold=threshold, capacity=3)
    baseline = RollingMeanBaseline(fixture["training"], threshold, window=8)
    rows = []
    first_stall_index = None

    for index, observation in enumerate(values):
        prototypes_before = [
            {"regime": f"R{profile_index}", "center": profile.center, "count": profile.count}
            for profile_index, profile in enumerate(soul.profiles)
        ]
        distances = [abs(observation - profile.center) for profile in soul.profiles]
        selected = min(range(len(distances)), key=lambda i: (distances[i], i))
        profile = soul.profiles[selected]
        selected_center = profile.center
        residual = abs(observation - selected_center)
        accepted = residual <= threshold
        numerator = profile.center * profile.count + observation
        denominator = profile.count + 1
        predicted_center_after = numerator // denominator
        count_after = profile.count + 1
        baseline_prediction = sum(baseline.values) // len(baseline.values)
        baseline_alert = abs(observation - baseline_prediction) > threshold

        alert, _ = soul.observe(observation)
        if alert != (not accepted):
            raise RuntimeError("trace decision disagrees with the frozen Soul-0 model")
        if accepted and profile.center != predicted_center_after:
            raise RuntimeError("trace running-mean prediction disagrees with Soul-0 state")
        if profile.count != count_after:
            raise RuntimeError("trace count prediction disagrees with Soul-0 state")
        if profile.center == selected_center and first_stall_index is None:
            first_stall_index = index

        rows.append({
            "sample_index": index,
            "observation": observation,
            "prototypes_before": prototypes_before,
            "distances": distances,
            "selected_regime": f"R{selected}",
            "soul_prediction": selected_center,
            "soul_residual": residual,
            "accepted_by_threshold": accepted,
            "soul_alert": alert,
            "mean_numerator": numerator,
            "mean_denominator": denominator,
            "predicted_center_after": predicted_center_after,
            "stored_center_after": profile.center,
            "stored_count_after": profile.count,
            "center_changed": profile.center != selected_center,
            "baseline_prediction": baseline_prediction,
            "baseline_residual": abs(observation - baseline_prediction),
            "baseline_alert": baseline_alert,
        })
        baseline.observe(observation)

    final_profile = soul.profiles[0]
    future_values = [phase["nominal_center"] + noise for noise in fixture["noise_cycle"]]
    center_stays_fixed = all(
        value - final_profile.center < final_profile.count + 1
        and value - final_profile.center >= 0
        for value in future_values
    )
    return {
        "diagnostic": "soul0_integer_mean_stall_trace_v1",
        "scope": "16 healthy B observations from the frozen fixture; diagnostic only, not a new adaptation evaluation",
        "fixture_sha256": fixture_hash,
        "source_manifest_sha256": manifest_hash,
        "threshold": threshold,
        "initial_profile": {"center": 180, "count": 2},
        "baseline": "8-sample rolling mean seeded with frozen regime-A training values",
        "steps": rows,
        "summary": {
            "final_center": final_profile.center,
            "final_count": final_profile.count,
            "target_center": phase["nominal_center"],
            "center_error": abs(final_profile.center - phase["nominal_center"]),
            "soul_alerts": sum(int(row["soul_alert"]) for row in rows),
            "baseline_alerts": sum(int(row["baseline_alert"]) for row in rows),
            "first_center_stall_index": first_stall_index,
            "center_fixed_for_all_next_noise_values": center_stays_fixed,
            "profiles_after_trace": [
                {"center": p.center, "count": p.count} for p in soul.profiles
            ],
            "interpretation": (
                "floor division creates a center fixed point once each positive residual "
                "is smaller than the running count denominator; the profile remains quiet "
                "but seven units below the target"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new diagnostic output directory")
    args = parser.parse_args()
    result = build_stall_trace()
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"output directory already exists: {args.out}")
    output = args.out / "trace.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print("idx obs proto selected residual accepted update baseline_pred baseline_alert")
    for row in result["steps"]:
        before = row["prototypes_before"][0]
        update = (
            f"mean-updated {before['center']}->{row['stored_center_after']}"
            if row["center_changed"]
            else f"mean-stalled at {row['stored_center_after']}"
        )
        print(
            f"{row['sample_index']:>3} {row['observation']:>3} "
            f"{before['center']:>5}/{before['count']:<2} {row['selected_regime']:<8} "
            f"{row['soul_residual']:>3} {str(row['accepted_by_threshold']):<8} {update:<24} "
            f"{row['baseline_prediction']:>6} {row['baseline_alert']}"
        )
    print(json.dumps(result["summary"], sort_keys=True))
    print(f"trace: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
