#!/usr/bin/env python3
"""Offline acceptance tests for INA226 capture ingestion and evaluation."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from ina226_capture_pipeline import run_study  # noqa: E402
from lib.ina226_capture import (  # noqa: E402
    ACCEPTED_ROWS,
    CLASS_NAMES,
    CaptureDataError,
    FeatureScaler,
    build_manifest,
    canonical_json_bytes,
    expected_class_order,
    feature_csv_bytes,
    load_manifest,
    manifest_windows,
    parse_capture_csv,
    seal_manifest,
    validate_manifest,
)
from som_map import load_map  # noqa: E402
from som_voronoi_explain import explain  # noqa: E402


CONTRACT = REPO / "software/datasets/ina226_coarse_monitor_v1.json"


def fixture_rows(class_name: str, block: int, probe: str = "dc_fan_v1") -> list[str]:
    label = CLASS_NAMES.index(class_name)
    lines = ["host_iso,probe,phase,t_ms,bus_mV,shunt_uV,current_uA"]
    bases = (4_000, 12_000, 24_000)
    amplitudes = (35, 110, 190)
    strides = (3, 5, 7)
    for index in range(ACCEPTED_ROWS + 4):
        raw = bases[label] + block * (17 + label * 3)
        raw += (((index * strides[label] + block) % 13) - 6) * (
            amplitudes[label] + block * 3
        )
        if label == 1 and (index + block) % 17 == 0:
            raw += 240 + block * 5
        if label == 2 and (index + block) % 8 in (0, 1):
            raw += 720 + block * 7
        current_uA = raw * 25
        shunt_uV = raw * 5 // 2
        lines.append(
            f"2026-07-19T12:00:{index // 100:02d}.{index % 100:03d},"
            f"{probe},{class_name},{1000 + index * 10},{5000 + (index % 3) - 1},"
            f"{shunt_uV},{current_uA}"
        )
    return lines


def write_fixture(path: Path, class_name: str, block: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fixture_rows(class_name, block)) + "\n", encoding="ascii")


def main() -> None:
    checks = 0

    def check(name: str, condition: bool) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(name)

    def rejects(name: str, action) -> None:
        nonlocal checks
        try:
            action()
        except CaptureDataError:
            checks += 1
        else:
            raise AssertionError(name)

    check("class rotation block zero", expected_class_order(0) == CLASS_NAMES)
    check(
        "class rotation block one",
        expected_class_order(1) == (CLASS_NAMES[1], CLASS_NAMES[2], CLASS_NAMES[0]),
    )
    check("class rotation cycles", expected_class_order(3) == CLASS_NAMES)
    rejects(
        "unsafe supply limit rejected",
        lambda: build_manifest(
            contract_path=CONTRACT,
            nominal_bus_mV=5000,
            probe="dc_fan_v1",
            actuator_model="unsafe-fixture",
            actuator_continuous_current_mA=1000,
            supply_current_limit_mA=800,
        ),
    )

    with tempfile.TemporaryDirectory() as temp_name:
        root = Path(temp_name)
        manifest_path = root / "capture_manifest.json"
        manifest = build_manifest(
            contract_path=CONTRACT,
            nominal_bus_mV=5000,
            probe="dc_fan_v1",
            actuator_model="synthetic-fixture-only",
            actuator_continuous_current_mA=700,
            supply_current_limit_mA=650,
        )
        check("manifest has 30 sessions", len(manifest["sessions"]) == 30)
        for session in manifest["sessions"]:
            write_fixture(
                root / session["csv_path"], session["class_name"], session["block"]
            )
        manifest = seal_manifest(manifest, manifest_path)
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        loaded = load_manifest(manifest_path)
        check("sealed manifest round trip", loaded == manifest)

        windows = manifest_windows(loaded, manifest_path)
        check("30 sessions become 120 windows", len(windows) == 120)
        check("whole sessions retain one fold", all(
            len({row.fold for row in windows if row.session_id == session["session_id"]}) == 1
            for session in manifest["sessions"]
        ))
        check("feature materialization deterministic", feature_csv_bytes(windows) == feature_csv_bytes(windows))
        check("features remain integer", all(
            all(isinstance(value, int) for value in row.features) for row in windows
        ))

        sample_session = manifest["sessions"][0]
        sample_path = root / sample_session["csv_path"]
        original = sample_path.read_text(encoding="ascii")

        def reject_mutation(mutator) -> None:
            lines = original.splitlines()
            mutator(lines)
            sample_path.write_text("\n".join(lines) + "\n", encoding="ascii")
            try:
                parse_capture_csv(
                    sample_path,
                    class_name=sample_session["class_name"],
                    probe="dc_fan_v1",
                    nominal_bus_mV=5000,
                )
            finally:
                sample_path.write_text(original, encoding="ascii")

        def duplicate_timestamp(lines: list[str]) -> None:
            row = lines[3].split(",")
            row[3] = lines[2].split(",")[3]
            lines[3] = ",".join(row)

        def cadence_gap(lines: list[str]) -> None:
            row = lines[3].split(",")
            row[3] = str(int(lines[2].split(",")[3]) + 20)
            lines[3] = ",".join(row)

        def wrong_phase(lines: list[str]) -> None:
            row = lines[2].split(",")
            row[2] = "elevated_load"
            lines[2] = ",".join(row)

        def shunt_mismatch(lines: list[str]) -> None:
            row = lines[2].split(",")
            row[5] = str(int(row[5]) + 2)
            lines[2] = ",".join(row)

        def saturation(lines: list[str]) -> None:
            row = lines[2].split(",")
            row[5] = "75001"
            row[6] = "750010"
            lines[2] = ",".join(row)

        def bus_out_of_range(lines: list[str]) -> None:
            row = lines[2].split(",")
            row[4] = "4000"
            lines[2] = ",".join(row)

        def malformed(lines: list[str]) -> None:
            lines[2] = ",".join(lines[2].split(",")[:-1])

        for name, mutator in (
            ("duplicate timestamp rejected", duplicate_timestamp),
            ("cadence gap rejected", cadence_gap),
            ("mixed phase rejected", wrong_phase),
            ("shunt mismatch rejected", shunt_mismatch),
            ("saturation rejected", saturation),
            ("bus excursion rejected", bus_out_of_range),
            ("malformed row rejected", malformed),
        ):
            rejects(name, lambda mutator=mutator: reject_mutation(mutator))

        short_path = root / "short.csv"
        short_path.write_text("\n".join(original.splitlines()[:100]) + "\n", encoding="ascii")
        rejects(
            "short session rejected",
            lambda: parse_capture_csv(
                short_path, class_name="normal", probe="dc_fan_v1", nominal_bus_mV=5000
            ),
        )

        unsealed = json.loads(json.dumps(manifest))
        unsealed["sessions"][0]["csv_sha256"] = None
        rejects("unsealed session rejected", lambda: manifest_windows(unsealed, manifest_path))
        reordered = json.loads(json.dumps(manifest))
        reordered["sessions"][0], reordered["sessions"][1] = (
            reordered["sessions"][1], reordered["sessions"][0]
        )
        rejects("capture order drift rejected", lambda: validate_manifest(reordered))

        out_a = root / "result_a"
        out_b = root / "result_b"
        result_a = run_study(manifest, manifest_path, out_a)
        result_b = run_study(manifest, manifest_path, out_b)
        check("synthetic study deterministic", canonical_json_bytes(result_a) == canonical_json_bytes(result_b))
        check("five complete folds", len(result_a["folds"]) == 5)
        check("all synthetic SOM1 records match", sum(
            fold["som_diagnostics"]["som1_oracle_matches"] for fold in result_a["folds"]
        ) == 120)
        check("synthetic fixture is not labelled physical", "synthetic fixtures" in result_a["evidence_scope"])

        map_document = load_map(out_a / "fold_0/map.json")
        first_test = next(row for row in windows if row.fold == 0)
        scaler = result_a["folds"][0]["scaler"]
        normalized, _directions = FeatureScaler(
            tuple(scaler["minima"]), tuple(scaler["maxima"])
        ).project(first_test.features)
        explanation = explain(map_document, normalized)
        check(
            "Voronoi slack equals quadrance gap",
            explanation["inequality"]["slack"]
            == explanation["second_quadrance"] - explanation["best_quadrance"],
        )
        check("Voronoi winner inequality holds", explanation["inequality"]["lhs"] <= explanation["inequality"]["rhs"])

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    check("contract format pinned", contract["format"] == "SPU_INA226_COARSE_MONITOR_V1")
    check("contract features pin implementation", tuple(contract["features"]) == (
        "mean_current_mA",
        "peak_to_peak_mA",
        "mean_abs_delta_mA",
        "mean_abs_deviation_mA",
    ))
    print(f"PASS: INA226 capture pipeline ({checks} checks)")


if __name__ == "__main__":
    main()
