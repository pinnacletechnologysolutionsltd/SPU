#!/usr/bin/env python3
"""Capture the amended T1d D3 analyzer window in verified segments.

This is a host/analyzer procedure only.  It does not program the FPGA or
transmit UART data.  The fixed command is deliberately kept here so a D3 run
cannot silently fall back to the unreliable single 48M request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path


SEGMENT_COUNT = 12
SAMPLES_PER_SEGMENT = 4_000_000
TOTAL_SAMPLES = SEGMENT_COUNT * SAMPLES_PER_SEGMENT
SAMPLERATE = "24MHz"
CHANNELS = "D0"
OUTPUT_FORMAT = "srzip"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        text = archive.read("metadata").decode("utf-8")
    values: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values


def sample_count(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        return sum(
            len(archive.read(name))
            for name in archive.namelist()
            if name.startswith("logic-")
        )


def write_result(path: Path, result: dict) -> None:
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def command_for(artifact: Path, driver: str) -> list[str]:
    return [
        "sigrok-cli",
        "--driver",
        driver,
        "--config",
        f"samplerate={SAMPLERATE}",
        "--channels",
        CHANNELS,
        "--samples",
        str(SAMPLES_PER_SEGMENT),
        "--output-format",
        OUTPUT_FORMAT,
        "--output-file",
        str(artifact),
    ]


def capture(output_dir: Path, driver: str) -> int:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    result_path = output_dir / "result.json"
    result = {
        "format": "SPU_GPU_T1D_SEGMENTED_CAPTURE_V1",
        "status": "RUNNING",
        "started_at": now(),
        "driver": driver,
        "samplerate": SAMPLERATE,
        "channels": CHANNELS,
        "output_format": OUTPUT_FORMAT,
        "segment_count": SEGMENT_COUNT,
        "samples_per_segment": SAMPLES_PER_SEGMENT,
        "required_aggregate_samples": TOTAL_SAMPLES,
        "segments": [],
    }
    write_result(result_path, result)

    for ordinal in range(1, SEGMENT_COUNT + 1):
        artifact = output_dir / f"segment_{ordinal:02d}.srzip"
        command = command_for(artifact, driver)
        started = time.monotonic()
        completed = subprocess.run(command, text=True, capture_output=True)
        elapsed = time.monotonic() - started
        record: dict[str, object] = {
            "ordinal": ordinal,
            "artifact": artifact.name,
            "command": command,
            "returncode": completed.returncode,
            "elapsed_seconds": round(elapsed, 3),
            "status": "PASS" if completed.returncode == 0 else "FAIL",
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
        if artifact.exists():
            record["sha256"] = sha256(artifact)
            try:
                values = metadata(artifact)
                count = sample_count(artifact)
                record["metadata_samplerate"] = values.get("samplerate")
                record["metadata_probe1"] = values.get("probe1")
                record["sample_count"] = count
                metadata_ok = (
                    values.get("samplerate") == "24 MHz"
                    and values.get("probe1") == CHANNELS
                    and values.get("unitsize") == "1"
                )
                if completed.returncode != 0 or count != SAMPLES_PER_SEGMENT or not metadata_ok:
                    record["status"] = "FAIL"
            except (OSError, KeyError, ValueError, zipfile.BadZipFile) as exc:
                record["status"] = "FAIL"
                record["verification_error"] = str(exc)
        else:
            record["status"] = "FAIL"
            record["verification_error"] = "artifact_missing"
        result["segments"].append(record)
        write_result(result_path, result)
        print(json.dumps(record, sort_keys=True), flush=True)
        if record["status"] != "PASS":
            result["status"] = "HALT"
            result["ended_at"] = now()
            write_result(result_path, result)
            return 1

    result["aggregate_sample_count"] = sum(
        int(segment["sample_count"]) for segment in result["segments"]
    )
    result["status"] = (
        "PASS"
        if result["aggregate_sample_count"] == TOTAL_SAMPLES
        else "HALT"
    )
    result["ended_at"] = now()
    write_result(result_path, result)
    return 0 if result["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--connection", required=True, help="current fx2lafw bus.device identifier")
    args = parser.parse_args()
    try:
        return capture(args.output_dir, f"fx2lafw:conn={args.connection}")
    except FileExistsError:
        print(f"refusing to overwrite existing output directory: {args.output_dir}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"capture setup failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
