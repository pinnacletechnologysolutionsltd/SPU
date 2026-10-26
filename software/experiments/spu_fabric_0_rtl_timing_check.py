#!/usr/bin/env python3
"""Check selected frozen FABRIC-0 Surd timings against the existing RTL harness."""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.spu_fabric_0_timing_reference import (  # noqa: E402
    MANIFEST, PROFILES, RTL_SHA256, operation_latency,
)

HARNESS = ROOT / "hardware/tests/math/surd_mul_normalizer_vectors_harness.v"
TIMING_REFERENCE = ROOT / "software/experiments/spu_fabric_0_timing_reference.py"
TIMING_REFERENCE_SHA256 = "80b753da559a19b4a3fc3dada6829806846b74449513040bc52adfdc516a603d"
MANIFEST_SHA256 = "24e7e35204baa8ee1e44a1cb09f788073a2bf721045190acb2a120ad1081ca13"
TRACE_SHA256 = {
    "isolated": "18585af72c7f65b4767e0526890424e56218af9eb20a6dbf90d943bf30c8a440",
    "burst_synthetic": "4db6e7458794b4a36f07d2cfd29a135f4301fb1a9e46ec73f77dc7f5b1060067",
    "steady_synthetic": "64359fdf2079299bbc1bfe95fe1b439f601084be288b62c9ace234dd5c4f3844",
}
HARNESS_SHA256 = "31ce5470a8b8f565e607b3452123e4f04ff927773970fa7a73a51880c6a4eaa0"
RTL = [
    ROOT / "hardware/rtl/math/surd_smul_unit.v",
    ROOT / "hardware/rtl/math/surd_binary_gcd3.v",
    ROOT / "hardware/rtl/math/surd_exact_quotient.v",
    ROOT / "hardware/rtl/math/surd_normalize_unit.v",
    HARNESS,
]
SELECTED = {
    32: (
        "surd_w32:min_negation_overflow",
        "surd_w32:random_0046",
        "surd_w32:zero_denominator_a",
        "surd_w32:zero_overflow_canonical_rescue",
        "surd_w32:unsigned_denominator_max_fit",
    ),
    64: (
        "surd_w64:min_negation_overflow",
        "surd_w64:random_0137",
        "surd_w64:zero_denominator_a",
        "surd_w64:zero_overflow_canonical_rescue",
        "surd_w64:unsigned_denominator_max_fit",
    ),
}
HARNESS_SEED_OPERANDS = [17, -19, 23, 1, 0, 1]
HARNESS_SEED_RESULT = [17, -19, 23]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hx(value: int, width: int) -> str:
    return f"{value & ((1 << width) - 1):0{(width + 3) // 4}x}"


def vector_line(record: dict, width: int) -> str:
    a, b, d, c, e, f = record["operands"]
    expected = record["expected"]
    raw = expected["raw"] or (0, 0, 0)
    reduced = expected["reduced"] or (0, 0, 0)
    out_a, out_b, out_d = expected["result"]
    nbits = 2 * width + 2
    fields = [
        hx(a, width), hx(b, width), hx(d, width), hx(c, width), hx(e, width), hx(f, width),
        hx(raw[0], nbits), hx(raw[1], nbits), hx(raw[2], 2 * width),
        hx(reduced[0], nbits), hx(reduced[1], nbits), hx(reduced[2], nbits),
        hx(out_a, width), hx(out_b, width), hx(out_d, width),
        str(int(expected["request_normalization"])), str(int(expected["invalid"])),
        str(int(expected["overflow"])),
    ]
    return " ".join(fields) + "\n"


def read_frozen_rows() -> tuple[dict[str, dict], dict[str, str]]:
    if sha256(MANIFEST) != MANIFEST_SHA256:
        raise SystemExit("frozen trace manifest hash mismatch")
    manifest = json.loads(MANIFEST.read_text())
    by_profile: dict[str, dict[str, dict]] = {}
    trace_hashes = {}
    for profile in PROFILES:
        trace_info = manifest["traces"][profile]
        trace_path = MANIFEST.parent / trace_info["path"]
        actual_hash = sha256(trace_path)
        if actual_hash != trace_info["sha256"] or actual_hash != TRACE_SHA256[profile]:
            raise SystemExit(f"frozen {profile} trace hash mismatch")
        trace_hashes[profile] = actual_hash
        rows = {}
        with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                if row["client"] in ("surd_w32", "surd_w64"):
                    rows[row["operation_id"]] = row
        by_profile[profile] = rows

    selected = {}
    for width, operation_ids in SELECTED.items():
        all_width_rows = [
            row for row in by_profile[PROFILES[0]].values()
            if row["client"] == f"surd_w{width}"
        ]
        computed_max = max(
            (operation_latency(row, width)[0], row["operation_id"])
            for row in all_width_rows
        )
        selected_max = max(
            (operation_latency(by_profile[PROFILES[0]][op_id], width)[0], op_id)
            for op_id in operation_ids
        )
        if computed_max != selected_max:
            raise SystemExit(f"W{width} selected maximum does not match full fixture maximum")
        for operation_id in operation_ids:
            row = by_profile[PROFILES[0]].get(operation_id)
            if row is None:
                raise SystemExit(f"missing frozen case: {operation_id}")
            if row["initial_state"]["destination"] != HARNESS_SEED_RESULT:
                raise SystemExit(
                    f"harness seed does not match frozen initial destination: {operation_id}"
                )
            expected = row["expected"]
            if (expected["invalid"] or expected["overflow"]) and (
                expected["result"] != row["initial_state"]["destination"]
            ):
                raise SystemExit(
                    f"invalid/overflow case does not preserve initial destination: {operation_id}"
                )
            signature = (row["client"], row["operands"], row["initial_state"], row["expected"])
            for profile in PROFILES[1:]:
                peer = by_profile[profile].get(operation_id)
                if peer is None or signature != (
                    peer["client"], peer["operands"], peer["initial_state"], peer["expected"]
                ):
                    raise SystemExit(f"profile mismatch for {operation_id} in {profile}")
            selected[operation_id] = row
    return selected, trace_hashes


def save_result(path: Path, result: dict) -> None:
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run_logged(
    command: list[str], cwd: Path, log_prefix: Path,
    result: dict, result_path: Path,
) -> subprocess.CompletedProcess:
    command_record = {
        "label": log_prefix.name,
        "command_file": log_prefix.name + ".command.txt",
        "stdout_file": log_prefix.name + ".stdout.txt",
        "stderr_file": log_prefix.name + ".stderr.txt",
        "status_file": log_prefix.name + ".status.json",
        "returncode": None,
    }
    result["commands"].append(command_record)
    save_result(result_path, result)
    (log_prefix.with_suffix(".command.txt")).write_text(
        shlex.join(command) + "\n", encoding="utf-8"
    )
    try:
        completed = subprocess.run(
            command, cwd=cwd, check=False, text=True, capture_output=True
        )
        stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
    except OSError as error:
        stdout, stderr, returncode = "", f"{type(error).__name__}: {error}\n", None
    log_prefix.with_suffix(".stdout.txt").write_text(stdout, encoding="utf-8")
    log_prefix.with_suffix(".stderr.txt").write_text(stderr, encoding="utf-8")
    log_prefix.with_suffix(".status.json").write_text(
        json.dumps({"returncode": returncode}, sort_keys=True) + "\n", encoding="utf-8"
    )
    command_record["returncode"] = returncode
    save_result(result_path, result)
    if returncode != 0:
        raise RuntimeError(f"{log_prefix.name} failed with return code {returncode}")
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if output.exists():
        raise SystemExit(f"refusing pre-existing output directory: {output}")
    for relative, expected in RTL_SHA256.items():
        if sha256(ROOT / relative) != expected:
            raise SystemExit(f"RTL source hash mismatch: {relative}")
    if sha256(HARNESS) != HARNESS_SHA256:
        raise SystemExit("frozen RTL harness hash mismatch")
    if sha256(TIMING_REFERENCE) != TIMING_REFERENCE_SHA256:
        raise SystemExit("source timing reference hash mismatch")
    rows, trace_hashes = read_frozen_rows()
    output.mkdir(parents=True)

    result = {
        "status": "RUNNING",
        "rtl_sha256": {name: sha256(ROOT / name) for name in RTL_SHA256},
        "harness_sha256": sha256(HARNESS),
        "trace_sha256": trace_hashes,
        "profiles": list(PROFILES),
        "lanes": 5,
        "destination_seed": {
            "harness_seed_operands_a_b_d_c_e_f": HARNESS_SEED_OPERANDS,
            "harness_seed_result": HARNESS_SEED_RESULT,
            "required_frozen_initial_destination": HARNESS_SEED_RESULT,
            "invalid_or_overflow_expected_result_must_equal_initial_destination": True,
        },
        "commands": [],
        "selected": [],
    }
    result_path = output / "result.json"
    save_result(result_path, result)
    summary_re = re.compile(
        r"fit=(\d+) latency\[min/avg/max\]=([0-9xX]+)/([0-9xX]+)/([0-9xX]+) "
        r"norm=(\d+) latency\[min/avg/max\]=([0-9xX]+)/([0-9xX]+)/([0-9xX]+) "
        r"invalid=(\d+)"
    )
    try:
        for width, operation_ids in SELECTED.items():
            image = output / f"w{width}.vvp"
            compile_cmd = [
                "iverilog", "-g2012", "-s", "surd_mul_normalizer_vectors_tb",
                "-P", f"surd_mul_normalizer_vectors_tb.W={width}",
                "-P", "surd_mul_normalizer_vectors_tb.LANES=5",
                "-o", str(image), *map(str, RTL),
            ]
            compile_prefix = output / f"w{width}_compile"
            run_logged(compile_cmd, ROOT, compile_prefix, result, result_path)
            for index, operation_id in enumerate(operation_ids):
                row = rows[operation_id]
                vector_path = output / f"w{width}_{index}.vectors.txt"
                vector_path.write_text(vector_line(row, width), encoding="ascii")
                run_cmd = ["vvp", str(image), f"+VECTORS={vector_path}"]
                run_prefix = output / f"w{width}_{index}_vvp"
                completed = run_logged(run_cmd, ROOT, run_prefix, result, result_path)
                match = summary_re.search(completed.stdout)
                if match is None:
                    raise RuntimeError(f"could not parse RTL harness summary for {operation_id}")
                (fit_n_text, fit_min_text, _, fit_max_text, norm_n_text,
                 norm_min_text, _, norm_max_text, invalid_n_text) = match.groups()
                fit_n, norm_n, invalid_n = map(
                    int, (fit_n_text, norm_n_text, invalid_n_text)
                )
                expected = row["expected"]
                expected_latency, _ = operation_latency(row, width)
                observed_latency = None
                if expected["invalid"]:
                    if invalid_n != 1 or fit_n != 0 or norm_n != 0:
                        raise RuntimeError(f"RTL invalid-path status mismatch: {operation_id}")
                elif expected["request_normalization"]:
                    if (norm_n != 1 or fit_n != 0
                            or not norm_min_text.isdecimal()
                            or not norm_max_text.isdecimal()
                            or norm_min_text != norm_max_text):
                        raise RuntimeError(f"RTL normalized-path report mismatch: {operation_id}")
                    observed_latency = int(norm_max_text)
                else:
                    if (fit_n != 1 or norm_n != 0
                            or not fit_min_text.isdecimal()
                            or not fit_max_text.isdecimal()
                            or fit_min_text != fit_max_text):
                        raise RuntimeError(f"RTL raw-fit-path report mismatch: {operation_id}")
                    observed_latency = int(fit_max_text)
                if observed_latency is not None and observed_latency != expected_latency:
                    raise RuntimeError(
                        f"RTL/source latency mismatch for {operation_id}: "
                        f"{observed_latency} != {expected_latency}"
                    )
                result["selected"].append({
                    "operation_id": operation_id,
                    "width": width,
                    "initial_destination": row["initial_state"]["destination"],
                    "expected_result": expected["result"],
                    "invalid": expected["invalid"],
                    "request_normalization": expected["request_normalization"],
                    "source_derived_latency_cycles": expected_latency,
                    "rtl_observed_latency_cycles": observed_latency,
                })
                save_result(result_path, result)
        result["status"] = "PASS"
        save_result(result_path, result)
    except BaseException as error:
        result["status"] = "FAILED"
        result["failure"] = f"{type(error).__name__}: {error}"
        save_result(result_path, result)
        raise
    print(json.dumps({"status": result["status"], "result": str(result_path),
                      "cases": len(result["selected"])}, sort_keys=True))


if __name__ == "__main__":
    main()
