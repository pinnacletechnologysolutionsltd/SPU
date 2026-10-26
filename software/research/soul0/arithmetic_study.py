"""Evaluate the frozen Soul-0 arithmetic and memory-policy fixture."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from .arithmetic import ArithmeticModel, KINDS, SCALE, make_models


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "arithmetic_fixtures_v1.json"
MANIFEST = ROOT / "arithmetic_manifest_v1.json"
CONTRACT_ID = "contract_soul0_arithmetic_memory_2026-10-14.md"
ADAPTATION_ORDER = ("regime_b", "regime_c", "regime_a_return", "regime_b_return")
ALERT_ORDER = ("regime_a", "regime_b", "regime_c", "regime_a_return", "regime_b_return")
WIDTHS = {
    "input": {"signed_bits": 10},
    "A": {"center_signed_bits": 10, "count_unsigned_bits": 9, "center_times_count_signed_bits": 19, "update_numerator_signed_bits": 19, "residual_signed_bits": 11},
    "B": {"sum_signed_bits": 19, "count_unsigned_bits": 9, "value_times_count_signed_bits": 19, "residual_signed_bits": 20, "threshold_times_count_signed_bits": 14},
    "C": {"center_signed_bits": 10, "count_unsigned_bits": 9, "remainder_unsigned_bits": 9, "represented_sum_signed_bits": 19, "residual_signed_bits": 20},
    "D": {"qcenter_signed_bits": 18, "count_unsigned_bits": 9, "update_numerator_signed_bits": 27, "scaled_residual_signed_bits": 19},
    "E": {"window_value_signed_bits": 10, "window_sum_signed_bits": 13, "scaled_residual_signed_bits": 14},
    "F": {"qcenter_signed_bits": 18, "update_numerator_signed_bits": 21, "scaled_residual_signed_bits": 19},
}


def load_frozen() -> tuple[dict, str, str]:
    manifest = json.loads(MANIFEST.read_text(encoding="ascii"))
    for relative, expected in manifest["files"].items():
        path = ROOT.parents[2] / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen source hash mismatch: {relative}")
    fixture_bytes = FIXTURE.read_bytes()
    return (
        json.loads(fixture_bytes),
        hashlib.sha256(fixture_bytes).hexdigest(),
        hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
    )


def _center(model: ArithmeticModel) -> Fraction:
    numerator, denominator = model.exact_center_pair()
    return Fraction(numerator, denominator)


def _evaluate_phase(model: ArithmeticModel, values: list[int], target: int | None = None,
                    fault_index: int | None = None) -> dict:
    alerts: list[bool] = []
    errors: list[Fraction] = []
    operation_total = 0
    healthy_false_alerts = 0
    fault_detected = False
    detection_delay: int | None = None
    for index, value in enumerate(values):
        alert, operations = model.observe(value)
        alerts.append(alert)
        operation_total += operations
        if fault_index is not None and index == fault_index:
            fault_detected = alert
            if alert:
                detection_delay = 0
        elif fault_index is None or index != fault_index:
            healthy_false_alerts += int(alert)
        if fault_index is not None and index > fault_index and alert and detection_delay is None:
            detection_delay = index - fault_index
        if target is not None:
            errors.append(abs(_center(model) - target))

    lag = None
    if target is not None:
        for index in range(max(0, len(errors) - 2)):
            if all(error <= 5 for error in errors[index:index + 3]):
                lag = index
                break
    mean_error = None if not errors else sum(errors, Fraction(0)) / len(errors)
    return {
        "healthy_false_alerts": healthy_false_alerts,
        "fault_detected_at_arrival": fault_detected,
        "fault_missed_at_arrival": None if fault_index is None else not fault_detected,
        "fault_detection_delay": detection_delay,
        "adaptation_lag": lag,
        "center_error_numerator_last": None if not errors else errors[-1].numerator,
        "center_error_denominator_last": None if not errors else errors[-1].denominator,
        "center_error_mean_numerator": None if mean_error is None else mean_error.numerator,
        "center_error_mean_denominator": None if mean_error is None else mean_error.denominator,
        "operations": operation_total,
        "alerts": alerts,
    }


def _run(fixture: dict, fixture_hash: str, manifest_hash: str) -> dict:
    training = fixture["training"]
    models = make_models(training, fixture["threshold"])
    adaptation: dict[str, dict] = {kind: {} for kind in KINDS}
    for phase in ADAPTATION_ORDER:
        values = fixture["adaptation_phases"][phase]
        center = fixture["alert_phases"][phase]["nominal_center"]
        for kind, model in models.items():
            adaptation[kind][phase] = _evaluate_phase(model, values, target=center)

    adaptation_mae = {
        kind: sum(
            (Fraction(adaptation[kind][phase]["center_error_mean_numerator"],
                      adaptation[kind][phase]["center_error_mean_denominator"])
             for phase in ("regime_b", "regime_c")),
            Fraction(0),
        ) / 2
        for kind in KINDS
    }
    retention_mae = {
        kind: sum(
            (Fraction(adaptation[kind][phase]["center_error_mean_numerator"],
                      adaptation[kind][phase]["center_error_mean_denominator"])
             for phase in ("regime_a_return", "regime_b_return")),
            Fraction(0),
        ) / 2
        for kind in KINDS
    }

    alert_models = {kind: ArithmeticModel.from_bytes(model.to_bytes()) for kind, model in make_models(training, fixture["threshold"]).items()}
    alert_results: dict[str, dict] = {kind: {} for kind in KINDS}
    for phase in ALERT_ORDER:
        row = fixture["alert_phases"][phase]
        for kind, model in alert_models.items():
            alert_results[kind][phase] = _evaluate_phase(
                model, row["values"], fault_index=row["fault_index"]
            )

    regression = fixture["arithmetic_regression"]
    arithmetic_results = {}
    oracle_total = regression["initial_center"] * regression["initial_count"]
    oracle_count = regression["initial_count"]
    regression_models = {
        kind: ArithmeticModel(kind, [regression["initial_center"]] * regression["initial_count"], fixture["threshold"])
        for kind in ("A", "B", "C", "D")
    }
    regression_models["B"].total = oracle_total
    regression_models["B"].count = oracle_count
    regression_models["C"].center = regression["initial_center"]
    regression_models["C"].count = oracle_count
    regression_models["C"].remainder = 0
    regression_models["D"].qcenter = SCALE * regression["initial_center"]
    regression_models["D"].count = oracle_count
    for index, value in enumerate(regression["values"]):
        oracle_total += value
        oracle_count += 1
        exact = Fraction(oracle_total, oracle_count)
        for kind, model in regression_models.items():
            alert, operations = model.observe(value)
            numerator, denominator = model.exact_center_pair()
            oracle_error = abs(Fraction(numerator, denominator) - exact)
            arithmetic_results.setdefault(kind, []).append({
                "index": index,
                "center_numerator": numerator,
                "center_denominator": denominator,
                "oracle_numerator": exact.numerator,
                "oracle_denominator": exact.denominator,
                "oracle_error_numerator": oracle_error.numerator,
                "oracle_error_denominator": oracle_error.denominator,
                "exact_oracle_match": Fraction(numerator, denominator) == exact if kind in ("B", "C") else None,
                "alert": alert,
                "operations": operations,
            })

    persistence = {}
    for kind in KINDS:
        uninterrupted = make_models(training, fixture["threshold"])[kind]
        first_half = fixture["adaptation_phases"]["regime_b"][:32]
        second_half = fixture["adaptation_phases"]["regime_b"][32:]
        for value in first_half:
            uninterrupted.observe(value)
        resumed = ArithmeticModel.from_bytes(uninterrupted.to_bytes())
        trace_a, trace_b = [], []
        remaining = second_half + fixture["adaptation_phases"]["regime_c"]
        for value in remaining:
            trace_a.append(uninterrupted.observe(value)[0])
            trace_b.append(resumed.observe(value)[0])
        persistence[kind] = trace_a == trace_b and uninterrupted.to_bytes() == resumed.to_bytes()

    return {
        "contract_id": CONTRACT_ID,
        "experiment": "soul0_arithmetic_memory_v1",
        "evidence_scope": "synthetic arithmetic-regression, regime adaptation, and out-of-range transient characterization",
        "fixture_sha256": fixture_hash,
        "source_manifest_sha256": manifest_hash,
        "models": {
            kind: {
                "logical_state_bytes": make_models(training, fixture["threshold"])[kind].logical_state_bytes,
                "checkpoint_bytes_after_training": len(make_models(training, fixture["threshold"])[kind].to_bytes()),
                "adaptation": adaptation[kind],
                "alert_phases": alert_results[kind],
                "arithmetic_regression": arithmetic_results.get(kind),
                "replay_identical": persistence[kind],
            }
            for kind in KINDS
        },
        "integer_widths": WIDTHS,
        "verdicts": {
            "arithmetic_correction": all(row["exact_oracle_match"] for row in arithmetic_results["B"] + arithmetic_results["C"])
                and regression_models["A"].center != regression["target_center"],
            "adaptation_improvement": {
                "status": "PASS" if any(
                    adaptation_mae[kind] < adaptation_mae["E"]
                    and adaptation_mae[kind] < adaptation_mae["F"]
                    for kind in ("A", "B", "C", "D")
                ) else "FAIL",
                "metric": "strictly lower pooled mean absolute center error on B/C than both E and F",
                "comparators": ["E", "F"],
                "pooled_mean_absolute_center_error": {
                    kind: {"numerator": value.numerator, "denominator": value.denominator}
                    for kind, value in adaptation_mae.items()
                },
            },
            "retention": {
                "status": "REPORTED; no standalone pass threshold frozen",
                "pooled_mean_absolute_center_error": {
                    kind: {"numerator": value.numerator, "denominator": value.denominator}
                    for kind, value in retention_mae.items()
                },
            },
            "implementation_suitability": all(persistence.values()),
        },
    }


def _without_latency(value):
    if isinstance(value, dict):
        return {key: _without_latency(item) for key, item in value.items() if not key.startswith("latency_")}
    if isinstance(value, list):
        return [_without_latency(item) for item in value]
    return value


def run_study() -> dict:
    fixture, fixture_hash, manifest_hash = load_frozen()
    first = _run(fixture, fixture_hash, manifest_hash)
    second = _run(fixture, fixture_hash, manifest_hash)
    first["deterministic_output"] = _without_latency(first) == _without_latency(second)
    return first


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; must not exist")
    args = parser.parse_args()
    try:
        load_frozen()
        args.out.mkdir(parents=True, exist_ok=False)
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    result = run_study()
    (args.out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"SOUL0 ARITHMETIC/MEMORY: {'PASS' if result['deterministic_output'] else 'FAIL'}")
    print(f"  evidence: {args.out / 'result.json'}")
    return 0 if result["deterministic_output"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
