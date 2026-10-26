"""Run the frozen Soul-0 held-out regime and out-of-range transient fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from .counted import CountedRollingMean, CountedSoul0, CountedStateless, as_reference_soul


ROOT = Path(__file__).resolve().parent
FIXTURE_PATH = ROOT / "heldout_fixtures_v1.json"
MANIFEST_PATH = ROOT / "heldout_manifest_v1.json"
PHASE_ORDER = ("regime_a", "regime_b", "regime_c", "regime_a_return", "regime_b_return")
STATE_CEILING = 32


def load_frozen_inputs() -> tuple[dict, str, str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="ascii"))
    for relative, expected in manifest["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen source hash mismatch: {relative}")
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()
    fixture = json.loads(fixture_bytes)
    manifest_hash = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    return fixture, fixture_hash, manifest_hash


def _validate_transient_envelopes(fixture: dict) -> dict[str, dict[str, int]]:
    threshold = fixture["threshold"]
    noise = fixture["noise_cycle"]
    bound = fixture["prototype_center_noise_bound"]
    envelopes = {}
    for name, phase in fixture["phases"].items():
        center = phase["nominal_center"]
        possible_faults = [center + n + phase["fault_offset"] for n in noise]
        minimum_distance = min(
            abs(fault - (prototype + center_error))
            for fault in possible_faults
            for prototype in fixture["prototype_centers"]
            for center_error in range(-bound, bound + 1)
        )
        envelopes[name] = {
            "minimum_distance": minimum_distance,
            "threshold": threshold,
            "margin": minimum_distance - threshold,
        }
        if minimum_distance <= threshold:
            raise ValueError(f"transient overlaps a normal acceptance region: {name}")
    return envelopes


def _phase_metrics(model, phase: dict) -> dict:
    values = phase["values"]
    fault_index = phase["fault_index"]
    healthy_alerts = fault_detected = operations = 0
    decisions: list[bool] = []
    latencies: list[int] = []
    for index, value in enumerate(values):
        started = time.perf_counter_ns()
        alert, op_count = model.observe(value)
        latencies.append(time.perf_counter_ns() - started)
        operations += op_count
        decisions.append(alert)
        if index == fault_index:
            fault_detected += int(alert)
        else:
            healthy_alerts += int(alert)
    ordered = sorted(latencies)
    return {
        "healthy_alerts": healthy_alerts,
        "fault_detected": fault_detected,
        "operations": operations,
        "latency_ns_median": (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) // 2,
        "latency_ns_p95": ordered[(95 * len(ordered) + 99) // 100 - 1],
        "decisions": decisions,
    }


def _run_once(fixture: dict, fixture_hash: str, manifest_hash: str) -> dict:
    training = fixture["training"]
    threshold = fixture["threshold"]
    seed_center = sum(training) // len(training)
    stateless = CountedStateless(seed_center, threshold)
    rolling = CountedRollingMean(training, threshold, window=8)
    soul = CountedSoul0([(seed_center, len(training))], threshold=threshold, capacity=3)
    models = {"stateless": stateless, "rolling_mean": rolling, "soul0": soul}
    results = {name: {"phases": {}} for name in models}
    for phase_name in PHASE_ORDER[:3]:
        phase = fixture["phases"][phase_name]
        for model_name, model in models.items():
            results[model_name]["phases"][phase_name] = _phase_metrics(model, phase)

    checkpoint_after_c = as_reference_soul(soul).to_bytes()
    resumed = CountedSoul0.from_bytes(checkpoint_after_c)
    reference_trace = []
    resumed_trace = []
    for phase_name in ("regime_a_return", "regime_b_return"):
        phase = fixture["phases"][phase_name]
        for model_name in ("stateless", "rolling_mean"):
            results[model_name]["phases"][phase_name] = _phase_metrics(models[model_name], phase)
        reference_result = _phase_metrics(soul, phase)
        resumed_result = _phase_metrics(resumed, phase)
        results["soul0"]["phases"][phase_name] = reference_result
        reference_trace.extend(reference_result["decisions"])
        resumed_trace.extend(resumed_result["decisions"])
    persistence = (
        reference_trace == resumed_trace
        and as_reference_soul(soul).to_bytes() == as_reference_soul(resumed).to_bytes()
    )

    recovery = CountedSoul0([(180, 2)], threshold=threshold, capacity=3)
    recovery_alerts = 0
    recovery_values = [
        fixture["phases"]["regime_b"]["nominal_center"] + fixture["noise_cycle"][index % 5]
        for index in range(16)
    ]
    for value in recovery_values:
        alert, _ = recovery.observe(value)
        recovery_alerts += int(alert)
    recovery_center = recovery.profiles[0].center

    gates = {
        "heldout_adaptation": (
            results["soul0"]["phases"]["regime_b"]["healthy_alerts"] <= 4
            and results["soul0"]["phases"]["regime_b"]["healthy_alerts"]
            < results["rolling_mean"]["phases"]["regime_b"]["healthy_alerts"]
        ),
        "capacity_adaptation": (
            results["soul0"]["phases"]["regime_c"]["healthy_alerts"] <= 4
            and len(soul.profiles) <= 3
        ),
        "retention": (
            results["soul0"]["phases"]["regime_a_return"]["healthy_alerts"] <= 1
            and results["rolling_mean"]["phases"]["regime_a_return"]["healthy_alerts"]
            >= results["soul0"]["phases"]["regime_a_return"]["healthy_alerts"] + 3
        ),
        "second_return": results["soul0"]["phases"]["regime_b_return"]["healthy_alerts"] <= 1,
        "transient_detection": all(
            results[model_name]["phases"][phase_name]["fault_detected"] == 1
            for model_name in models
            for phase_name in PHASE_ORDER
        ),
        "seeded_profile_stall_regression": (
            recovery_center == 193
            and abs(recovery_center - 200) > 5
            and len(recovery.profiles) == 1
        ),
        "memory": max(model.logical_state_bytes for model in models.values()) <= STATE_CEILING,
        "checkpoint_replay": persistence,
        "transient_outside_all_prototypes": all(
            envelope["minimum_distance"] > envelope["threshold"]
            for envelope in _validate_transient_envelopes(fixture).values()
        ),
    }
    for model_name, model in models.items():
        results[model_name]["logical_state_bytes"] = model.logical_state_bytes
    results["soul0"]["checkpoint_bytes_after_regime_c"] = len(checkpoint_after_c)
    return {
        "contract_id": "contract_soul0_heldout_2026-10-14.md",
        "experiment": "soul0_heldout_integer_sensor_v1",
        "evidence_scope": "synthetic out-of-range transient detection; cross-regime lookalikes not evaluated",
        "fixture_sha256": fixture_hash,
        "source_manifest_sha256": manifest_hash,
        "transient_envelopes": _validate_transient_envelopes(fixture),
        "seeded_profile_recovery": {
            "initial_center": 180,
            "initial_count": 2,
            "final_center": recovery_center,
            "target_center": 200,
            "center_error": abs(recovery_center - 200),
            "recovery_tolerance": 5,
            "recovery_succeeded": abs(recovery_center - 200) <= 5,
            "healthy_alerts": recovery_alerts,
            "profiles": len(recovery.profiles),
        },
        "models": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _without_latency(value):
    if isinstance(value, dict):
        return {key: _without_latency(item) for key, item in value.items() if not key.startswith("latency_")}
    if isinstance(value, list):
        return [_without_latency(item) for item in value]
    return value


def run_experiment() -> dict:
    fixture, fixture_hash, manifest_hash = load_frozen_inputs()
    first = _run_once(fixture, fixture_hash, manifest_hash)
    replay = _run_once(fixture, fixture_hash, manifest_hash)
    first["gates"]["deterministic_replay"] = _without_latency(first) == _without_latency(replay)
    first["passed"] = all(first["gates"].values())
    return first


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; must not exist")
    args = parser.parse_args()
    try:
        fixture, _, _ = load_frozen_inputs()
        envelopes = _validate_transient_envelopes(fixture)
        args.out.mkdir(parents=True, exist_ok=False)
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    result = run_experiment()
    (args.out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"SOUL0 HELD-OUT: {'PASS' if result['passed'] else 'FAIL'}")
    for name, passed in result["gates"].items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    for name, values in envelopes.items():
        print(f"  transient margin {name}: {values['margin']}")
    print(f"  evidence: {args.out / 'result.json'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
