#!/usr/bin/env python3
"""Run the Phase-3 tensegrity A/B simulation matrix and emit cycle JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "zphi_karatsuba_phase3_cycles.json"
LOG_DIR = ROOT / "build" / "zphi_karatsuba_phase3"

REFERENCE = "hardware/rtl/core/spu13/spu13_zphi_mul_serial.v"
CANDIDATE = "hardware/rtl/core/spu13/spu13_zphi_mul_serial_karatsuba.v"
INTERSECTION = "hardware/rtl/core/spu13/spu13_tensegrity_intersection.v"
GUARD = "hardware/rtl/core/spu13/spu13_tensegrity_guard.v"
SIDECAR = "hardware/rtl/core/spu13/spu13_tensegrity_sidecar.v"
SPI_SLAVE = "hardware/rtl/peripherals/io/spu_spi_slave.v"
PROBE_TOP = "hardware/boards/artix7/spu_a7_tensegrity_probe_top.v"

TESTS = (
    {
        "name": "intersection",
        "top": "spu13_tensegrity_intersection_tb",
        "sources": (REFERENCE, CANDIDATE, INTERSECTION,
                    "hardware/tests/spu13/spu13_tensegrity_intersection_tb.v"),
        "pass": "SPU13_TENSEGRITY_INTERSECTION_TB: PASS",
    },
    {
        "name": "guard",
        "top": "spu13_tensegrity_guard_tb",
        "sources": (REFERENCE, CANDIDATE, INTERSECTION, GUARD,
                    "hardware/tests/spu13/spu13_tensegrity_guard_tb.v"),
        "pass": "SPU13_TENSEGRITY_GUARD_TB: PASS",
    },
    {
        "name": "probe",
        "top": "spu_a7_tensegrity_probe_tb",
        "sources": (REFERENCE, CANDIDATE, INTERSECTION, GUARD, PROBE_TOP,
                    "hardware/tests/spu13/spu_a7_tensegrity_probe_tb.v"),
        "pass": "SPU_A7_TENSEGRITY_PROBE_TB: PASS",
    },
    {
        "name": "sidecar",
        "top": "spu13_tensegrity_sidecar_tb",
        "sources": (REFERENCE, CANDIDATE, INTERSECTION, GUARD, SIDECAR,
                    "hardware/tests/spu13/spu13_tensegrity_sidecar_tb.v"),
        "pass": "SPU13_TENSEGRITY_SIDECAR_TB: PASS",
    },
    {
        "name": "transport",
        "top": "spu13_tensegrity_transport_tb",
        "sources": (SPI_SLAVE, REFERENCE, CANDIDATE, INTERSECTION, GUARD,
                    SIDECAR,
                    "hardware/tests/spu13/spu13_tensegrity_transport_tb.v"),
        "pass": "SPU13_TENSEGRITY_TRANSPORT_TB: PASS",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_cycle_records(output: str, expected_mode: int) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line in output.splitlines():
        if not line.startswith("ZPHI_CYCLE "):
            continue
        fields: dict[str, str] = {}
        for token in line.removeprefix("ZPHI_CYCLE ").split():
            if "=" not in token:
                raise RuntimeError(f"malformed cycle token: {token!r}")
            key, value = token.split("=", 1)
            fields[key] = value
        required = {"kind", "fixture", "mode", "cycles", "decision"}
        if set(fields) != required:
            raise RuntimeError(f"malformed cycle record: {line}")
        mode = int(fields["mode"])
        cycles = int(fields["cycles"])
        if mode != expected_mode:
            raise RuntimeError(
                f"cycle record mode {mode} does not match run mode {expected_mode}"
            )
        if cycles < 0:
            raise RuntimeError(f"negative cycle count: {line}")
        records.append(
            {
                "kind": fields["kind"],
                "fixture": fields["fixture"],
                "cycles": cycles,
                "decision": fields["decision"],
            }
        )
    return records


def run_test(test: dict[str, object], mode: int) -> tuple[dict[str, object], list[dict[str, object]]]:
    name = str(test["name"])
    top = str(test["top"])
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    vvp_path = LOG_DIR / f"{name}_zk{mode}.vvp"
    log_path = LOG_DIR / f"{name}_zk{mode}.log"
    compile_command = [
        "iverilog", "-g2012", "-I", "hardware/rtl/arch", "-s", top,
        "-P", f"{top}.USE_ZPHI_KARATSUBA={mode}", "-o", str(vvp_path),
        *[str(source) for source in test["sources"]],
    ]
    compile_run = subprocess.run(
        compile_command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    compile_text = compile_run.stdout + compile_run.stderr
    if compile_run.returncode != 0:
        log_path.write_text(compile_text, encoding="utf-8")
        raise RuntimeError(
            f"{name} mode {mode} compile failed; see {log_path.relative_to(ROOT)}"
        )

    try:
        simulation = subprocess.run(
            ["vvp", str(vvp_path)], cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=180,
        )
    except subprocess.TimeoutExpired as error:
        log_path.write_text(compile_text + str(error), encoding="utf-8")
        raise RuntimeError(f"{name} mode {mode} timed out") from error

    combined = compile_text + simulation.stdout + simulation.stderr
    log_path.write_text(combined, encoding="utf-8")
    if simulation.returncode != 0 or str(test["pass"]) not in combined:
        raise RuntimeError(
            f"{name} mode {mode} failed; see {log_path.relative_to(ROOT)}"
        )

    result = {
        "test": name,
        "top": top,
        "status": "PASS",
        "log": str(log_path.relative_to(ROOT)),
        "log_sha256": sha256(log_path),
    }
    return result, parse_cycle_records(combined, mode)


def keyed(records: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for record in records:
        key = f"{record['kind']}:{record['fixture']}"
        if key in result:
            raise RuntimeError(f"duplicate cycle record: {key}")
        result[key] = record
    return result


def verify_coverage(records: dict[str, dict[str, object]]) -> None:
    intersection = {key for key in records if key.startswith("intersection:")}
    probe = {key for key in records if key.startswith("probe:")}
    required_guard = {
        "guard:canonical", "guard:strut_collision", "guard:cable_slack",
        "guard:grid_mismatch", "guard:disconnected_topology",
        "guard:strut_intersection", "guard:not_in_equilibrium",
    }
    required_sidecar = {
        "sidecar:valid_admission", "sidecar:mechanical_negative_admission",
        "sidecar:corrupt_payload_rollback", "sidecar:timeout_recovery",
        "sidecar:reset_recovery",
    }
    if len(intersection) != 8:
        raise RuntimeError(f"expected 8 intersection cycle records, found {len(intersection)}")
    if probe != {f"probe:{index}" for index in range(7)}:
        raise RuntimeError(f"probe cycle coverage mismatch: {sorted(probe)}")
    missing = (required_guard | required_sidecar | {"transport:valid_admission"}) - set(records)
    if missing:
        raise RuntimeError(f"missing required cycle records: {sorted(missing)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_path = args.output if args.output.is_absolute() else ROOT / args.output

    report: dict[str, object] = {
        "schema": "spu13.zphi_karatsuba.phase3_cycles.v1",
        "selector": "USE_ZPHI_KARATSUBA",
        "measurement_windows": {
            "intersection_guard_probe": "accepted_start_to_done",
            "sidecar_transport": "transaction_start_to_terminal_idle",
        },
        "modes": {},
        "comparison": [],
    }
    mode_records: dict[int, dict[str, dict[str, object]]] = {}

    for mode in (0, 1):
        test_results: list[dict[str, object]] = []
        cycle_records: list[dict[str, object]] = []
        for test in TESTS:
            test_result, records = run_test(test, mode)
            test_results.append(test_result)
            cycle_records.extend(records)
            print(f"PASS mode={mode} test={test['name']}")
        mode_records[mode] = keyed(cycle_records)
        verify_coverage(mode_records[mode])
        report["modes"][str(mode)] = {
            "implementation": "reference" if mode == 0 else "three_product_candidate",
            "tests": test_results,
            "cycles": [mode_records[mode][key] for key in sorted(mode_records[mode])],
        }

    if set(mode_records[0]) != set(mode_records[1]):
        raise RuntimeError("reference/candidate cycle-record key sets differ")

    comparison: list[dict[str, object]] = []
    for key in sorted(mode_records[0]):
        reference = mode_records[0][key]
        candidate = mode_records[1][key]
        if reference["decision"] != candidate["decision"]:
            raise RuntimeError(
                f"decision mismatch for {key}: {reference['decision']} vs {candidate['decision']}"
            )
        ref_cycles = int(reference["cycles"])
        candidate_cycles = int(candidate["cycles"])
        row = {
            "key": key,
            "decision": reference["decision"],
            "reference_cycles": ref_cycles,
            "candidate_cycles": candidate_cycles,
            "delta_cycles": candidate_cycles - ref_cycles,
        }
        comparison.append(row)
        print(
            f"CYCLE {key} reference={ref_cycles} candidate={candidate_cycles} "
            f"delta={candidate_cycles - ref_cycles} decision={reference['decision']}"
        )
    report["comparison"] = comparison

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PHASE3: PASS report={output_path.relative_to(ROOT)} records={len(comparison)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"PHASE3: FAIL {error}", file=sys.stderr)
        sys.exit(1)
