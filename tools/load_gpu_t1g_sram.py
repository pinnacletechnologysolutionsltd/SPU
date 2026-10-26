#!/usr/bin/env python3
"""Load the frozen T1G bitstream to Wukong SRAM with durable terminal evidence."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit"
EXPECTED_SHA256 = "e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5"
EXPECTED_IDCODE = "0x3631093"
TERMINALS = ("COMPLETE", "FAILED", "TIMEOUT")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_boot_id():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def atomic_json(path, value):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=path.name + ".", suffix=".tmp",
                                     delete=False) as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def command_result(command, runner):
    started_monotonic_ns = time.monotonic_ns()
    started = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    try:
        result = runner(command, cwd=ROOT, capture_output=True, text=True,
                        check=False)
        record = {"command": command, "started_utc": started,
                  "started_monotonic_ns": started_monotonic_ns,
                  "finished_utc": utc_now(),
                  "finished_monotonic_ns": time.monotonic_ns(),
                  "exit_status": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr}
        return record
    except BaseException as exc:
        return {"command": command, "started_utc": started,
                "started_monotonic_ns": started_monotonic_ns,
                "finished_utc": utc_now(),
                "finished_monotonic_ns": time.monotonic_ns(),
                "exit_status": None,
                "stdout": "", "stderr": repr(exc), "exception": repr(exc)}


def has_expected_idcode(output):
    values = re.findall(r"\b0x0*([0-9a-fA-F]+)\b", output)
    return any(value.lower() == EXPECTED_IDCODE[2:] for value in values)


def has_done_flags(output):
    normalized = output.lower()
    return (re.search(r"\bisc[_ ]done\s*[:=]?\s*1\b", normalized) and
            re.search(r"\binit\s*[:=]?\s*1\b", normalized) and
            re.search(r"(?<!isc )\bdone\s*[:=]?\s*1\b", normalized))


def set_terminal(evidence, manifest, status, detail=None):
    if status not in TERMINALS:
        raise ValueError(f"invalid terminal status: {status}")
    manifest["status"] = status
    manifest["finished_utc"] = utc_now()
    if detail:
        manifest["detail"] = detail
    atomic_json(evidence / "result.json", manifest)
    for marker in TERMINALS:
        marker_path = evidence / marker
        if marker == status:
            marker_path.write_text(status + "\n")
        elif marker_path.exists():
            marker_path.unlink()
    return status


def run_load(evidence, attempt, runner=subprocess.run,
             attempt_limit_seconds=900):
    if type(attempt_limit_seconds) is not int or attempt_limit_seconds < 76:
        raise ValueError("attempt limit must be an integer of at least 76 seconds")
    evidence = Path(evidence).resolve()
    build_root = (ROOT / "build").resolve()
    if build_root not in evidence.parents:
        raise ValueError("evidence directory must be a new child of build/")
    evidence.mkdir(parents=True, exist_ok=False)
    manifest = {"format": "SPU_GPU_T1G_SRAM_LOAD_V1", "attempt": attempt,
                "status": "RUNNING", "artifact": str(ARTIFACT.relative_to(ROOT)),
                "expected_artifact_sha256": EXPECTED_SHA256,
                "expected_idcode": EXPECTED_IDCODE,
                "sram_only": True, "flash_write": False,
                "attempt_limit_seconds": attempt_limit_seconds,
                "host_boot_id": current_boot_id(),
                "started_utc": utc_now(), "commands": []}
    atomic_json(evidence / "result.json", manifest)

    try:
        if not ARTIFACT.is_file():
            return set_terminal(evidence, manifest, "FAILED",
                                f"artifact missing: {ARTIFACT}")
        actual_hash = sha256(ARTIFACT)
        manifest["artifact_sha256"] = actual_hash
        atomic_json(evidence / "result.json", manifest)
        if actual_hash != EXPECTED_SHA256:
            return set_terminal(evidence, manifest, "FAILED",
                                "frozen artifact SHA-256 mismatch")

        detect = ["timeout", "15s", "openFPGALoader", "-c", "dirtyJtag",
                  "--freq", "1000000", "--detect"]
        detected = command_result(detect, runner)
        manifest["attempt_started_monotonic_ns"] = detected[
            "started_monotonic_ns"]
        manifest["attempt_deadline_monotonic_ns"] = (
            detected["started_monotonic_ns"] +
            attempt_limit_seconds * 1_000_000_000)
        attempt_start_utc = datetime.fromisoformat(
            detected["started_utc"].replace("Z", "+00:00"))
        manifest["attempt_deadline_utc"] = datetime.fromtimestamp(
            attempt_start_utc.timestamp() + attempt_limit_seconds,
            timezone.utc).isoformat(timespec="seconds")
        manifest["commands"].append(detected)
        atomic_json(evidence / "result.json", manifest)
        if detected["exit_status"] == 124:
            return set_terminal(evidence, manifest, "TIMEOUT",
                                "JTAG detect exceeded frozen 15-second limit")
        if detected["exit_status"] != 0 or not has_expected_idcode(
                detected["stdout"] + "\n" + detected["stderr"]):
            return set_terminal(evidence, manifest, "FAILED",
                                "JTAG detect failed or expected IDCODE absent")

        load = ["timeout", "60s", "openFPGALoader", "-c", "dirtyJtag",
                "--freq", "1000000", str(ARTIFACT.relative_to(ROOT))]
        loaded = command_result(load, runner)
        manifest["commands"].append(loaded)
        atomic_json(evidence / "result.json", manifest)
        output = loaded["stdout"] + "\n" + loaded["stderr"]
        if loaded["exit_status"] == 124:
            return set_terminal(evidence, manifest, "TIMEOUT",
                                "SRAM load exceeded frozen 60-second limit")
        if loaded["exit_status"] != 0 or not has_done_flags(output):
            return set_terminal(evidence, manifest, "FAILED",
                                "SRAM load failed or DONE flags were incomplete")
        return set_terminal(evidence, manifest, "COMPLETE")
    except BaseException as exc:
        return set_terminal(evidence, manifest, "FAILED", repr(exc))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int)
    parser.add_argument("--attempt-limit-seconds", type=int, default=900)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    status = run_load(args.evidence_dir, args.attempt,
                      attempt_limit_seconds=args.attempt_limit_seconds)
    print(f"T1G SRAM load {status}; evidence={args.evidence_dir}")
    return 0 if status == "COMPLETE" else (124 if status == "TIMEOUT" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
