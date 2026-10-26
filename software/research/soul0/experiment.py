"""Run the frozen Soul-0 synthetic regime-change experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time

from .model import (
    DeviceCalibration,
    RollingMeanBaseline,
    Soul0,
    STATE_BUDGET_BYTES,
    StatelessBaseline,
)


THRESHOLD = 20
NOISE = (-2, -1, 0, 1, 2)
TRAINING_COUNT = 8


def _normal_values(center: int, start: int, count: int, fault_index: int | None) -> list[int]:
    values = [center + NOISE[(start + index) % len(NOISE)] for index in range(count)]
    if fault_index is not None:
        values[fault_index] += 60
    return values


def _phase_metrics(model, values: list[int], fault_index: int | None) -> dict:
    healthy_alerts = 0
    fault_detected = 0
    operations = 0
    latencies: list[int] = []
    decisions: list[bool] = []
    for index, value in enumerate(values):
        start_ns = time.perf_counter_ns()
        alert, op_count = model.observe(value)
        latencies.append(time.perf_counter_ns() - start_ns)
        operations += op_count
        decisions.append(alert)
        if index == fault_index:
            fault_detected += int(alert)
        else:
            healthy_alerts += int(alert)
    return {
        "healthy_alerts": healthy_alerts,
        "fault_detected": fault_detected,
        "operations": operations,
        "operations_per_update": operations / len(values),
        "latency_ns_median": int(statistics.median(latencies)),
        "latency_ns_p95": sorted(latencies)[max(0, (95 * len(latencies) + 99) // 100 - 1)],
        "decisions": decisions,
    }


def _model_report(phases: dict[str, dict], logical_state_bytes: int) -> dict:
    report = {
        "logical_state_bytes": logical_state_bytes,
        "phases": {},
    }
    for name, phase in phases.items():
        report["phases"][name] = {key: value for key, value in phase.items() if key != "decisions"}
    return report


def run_experiment() -> dict:
    training = _normal_values(100, 0, TRAINING_COUNT, None)
    phase_a = _normal_values(100, 8, 8, 3)
    phase_b = _normal_values(200, 16, 16, 10)
    phase_a_return = _normal_values(100, 32, 16, 7)

    stateless = StatelessBaseline(sum(training) // len(training), THRESHOLD)
    rolling = RollingMeanBaseline(training, THRESHOLD, window=8)
    soul = Soul0.seeded(training, threshold=THRESHOLD)

    stateless_phases: dict[str, dict] = {}
    rolling_phases: dict[str, dict] = {}
    soul_phases: dict[str, dict] = {}

    stateless_phases["regime_a"] = _phase_metrics(stateless, phase_a, 3)
    rolling_phases["regime_a"] = _phase_metrics(rolling, phase_a, 3)
    soul_phases["regime_a"] = _phase_metrics(soul, phase_a, 3)
    profiles_after_transient = len(soul.profiles)

    stateless_phases["regime_b"] = _phase_metrics(stateless, phase_b, 10)
    rolling_phases["regime_b"] = _phase_metrics(rolling, phase_b, 10)
    soul_phases["regime_b"] = _phase_metrics(soul, phase_b, 10)

    profiles_before_return = len(soul.profiles)
    checkpoint_after_b = soul.to_bytes()
    uninterrupted_phase = _phase_metrics(soul, phase_a_return, 7)
    restored = Soul0.from_bytes(checkpoint_after_b)
    restored_phase = _phase_metrics(restored, phase_a_return, 7)

    # Device-specific calibration is separate from portable learned state.
    source_calibration = DeviceCalibration(gain=2, offset=10)
    target_calibration = DeviceCalibration(gain=3, offset=-7)
    migrated = Soul0.from_bytes(checkpoint_after_b)
    migrated_values = [
        target_calibration.normalize(target_calibration.encode(value))
        for value in phase_a_return
    ]
    migrated_phase = _phase_metrics(migrated, migrated_values, 7)
    source_values = [
        source_calibration.normalize(source_calibration.encode(value))
        for value in phase_a_return
    ]
    calibration_exact = source_values == migrated_values == phase_a_return
    persistence_exact = (
        uninterrupted_phase["decisions"] == restored_phase["decisions"]
        and soul.to_bytes() == restored.to_bytes()
    )
    migration_exact = (
        calibration_exact
        and uninterrupted_phase["decisions"] == migrated_phase["decisions"]
        and soul.to_bytes() == migrated.to_bytes()
    )

    stateless_phases["regime_a_return"] = _phase_metrics(stateless, phase_a_return, 7)
    rolling_phases["regime_a_return"] = _phase_metrics(rolling, phase_a_return, 7)
    soul_phases["regime_a_return"] = uninterrupted_phase

    soul_b_alerts = soul_phases["regime_b"]["healthy_alerts"]
    rolling_b_alerts = rolling_phases["regime_b"]["healthy_alerts"]
    soul_return_alerts = soul_phases["regime_a_return"]["healthy_alerts"]
    rolling_return_alerts = rolling_phases["regime_a_return"]["healthy_alerts"]

    gates = {
        "persistence": persistence_exact,
        "adaptation": soul_b_alerts <= 4 and soul_b_alerts < rolling_b_alerts,
        "retention": soul_return_alerts <= 1 and rolling_return_alerts >= soul_return_alerts + 3,
        "migration": migration_exact,
        "bad_association_control": profiles_after_transient == 1,
        "memory_budget": max(
            stateless.logical_state_bytes,
            rolling.logical_state_bytes,
            soul.logical_state_bytes,
        ) <= STATE_BUDGET_BYTES,
    }

    return {
        "contract_id": "contract_soul0_2026-10-14.md",
        "experiment": "soul0_two_regime_integer_sensor_v1",
        "synthetic_only": True,
        "parameters": {
            "threshold": THRESHOLD,
            "regime_a_center": 100,
            "regime_b_center": 200,
            "noise_cycle": list(NOISE),
            "training_samples": TRAINING_COUNT,
            "phase_lengths": {"regime_a": 8, "regime_b": 16, "regime_a_return": 16},
            "fault_magnitude": 60,
            "logical_state_budget_bytes": STATE_BUDGET_BYTES,
        },
        "calibration": {
            "source": {"gain": source_calibration.gain, "offset": source_calibration.offset},
            "target": {"gain": target_calibration.gain, "offset": target_calibration.offset},
            "included_in_checkpoint": False,
        },
        "models": {
            "stateless": _model_report(stateless_phases, stateless.logical_state_bytes),
            "rolling_mean": _model_report(rolling_phases, rolling.logical_state_bytes),
            "soul0": _model_report(soul_phases, soul.logical_state_bytes),
        },
        "soul0_checkpoint_bytes_after_regime_b": len(checkpoint_after_b),
        "soul0_checkpoint_sha256_after_regime_b": hashlib.sha256(checkpoint_after_b).hexdigest(),
        "soul0_profiles_after_transient": profiles_after_transient,
        "soul0_profiles_after_regime_b": profiles_before_return,
        "gates": gates,
        "passed": all(gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; must not exist")
    args = parser.parse_args()
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"output directory already exists: {args.out}")
    result = run_experiment()
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (args.out / "result.json").write_bytes(encoded)
    print(f"SOUL0: {'PASS' if result['passed'] else 'FAIL'}")
    for name, passed in result["gates"].items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    print(f"  evidence: {args.out / 'result.json'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
