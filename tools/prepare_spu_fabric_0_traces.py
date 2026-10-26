#!/usr/bin/env python3
"""Prepare and atomically publish the frozen SPU-FABRIC-0 Phase 1A traces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_fabric_0_trace_io as trace_io
from software.experiments import spu_fabric_0_trace_manifest as manifest_data

FIXTURE_DIR = ROOT / "fixtures/spu_fabric_0"
MANIFEST_PATH = ROOT / "fixtures/spu_fabric_0_trace_manifest.json"


def write_json(path, value):
    with path.open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def cleanup(paths):
    for path in reversed(paths):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence_dir if args.evidence_dir.is_absolute() else ROOT / args.evidence_dir
    fixture_parent = FIXTURE_DIR.parent
    for final in (FIXTURE_DIR, MANIFEST_PATH, evidence):
        if final.exists():
            raise SystemExit(f"refusing pre-existing output: {final}")
    (ROOT / "build/spu_fabric").mkdir(parents=True, exist_ok=True)
    fixture_stage = Path(tempfile.mkdtemp(prefix=".spu_fabric_0.stage.", dir=fixture_parent))
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence_stage = Path(tempfile.mkdtemp(prefix=".tracefreeze.stage.", dir=evidence.parent))
    published = []
    temp_manifest = None
    stage = "preparing private staging"
    stage_started = time.monotonic()
    stage_seconds = {}
    active_profile = None
    profile_seconds = {}

    def enter_stage(name):
        nonlocal stage, stage_started
        stage_seconds[stage] = round(time.monotonic() - stage_started, 3)
        stage = name
        stage_started = time.monotonic()

    def timing_snapshot():
        current = dict(stage_seconds)
        current[stage] = round(time.monotonic() - stage_started, 3)
        return current

    def timeout_handler(_signum, _frame):
        raise TimeoutError(f"Phase 1A execution timeout during {stage}")

    signal.signal(signal.SIGTERM, timeout_handler)
    try:
        enter_stage("source oracle extraction and validation")
        (fixture_stage / "traces").mkdir()
        before = trace_io.source_hashes()
        source_stage = fixture_stage / "source_rows"
        source_counts = trace_io.write_source_spools(source_stage)
        enter_stage("profile trace serialization and readback")
        traces = {}
        for profile in ("isolated", "burst_synthetic", "steady_synthetic"):
            active_profile = profile
            profile_started = time.monotonic()
            path = fixture_stage / "traces" / f"{profile}.jsonl.gz"
            traces[profile] = trace_io.write_trace(path, profile, source_stage)
            profile_seconds[profile] = round(time.monotonic() - profile_started, 3)
        shutil.rmtree(source_stage)
        enter_stage("source recheck and manifest verification")
        if before != trace_io.source_hashes():
            raise ValueError("source hashes changed during trace preparation")
        manifest = manifest_data.build_manifest(
            before, traces, sys.version, zlib.ZLIB_VERSION)
        manifest["source_spool_counts"] = source_counts
        manifest["compression"] = {"format": "gzip", "level": 1,
                                    "mtime": 0, "embedded_filename": ""}
        manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
        (fixture_stage / "manifest.json").write_bytes(manifest_bytes)
        if json.loads(manifest_bytes) != manifest:
            raise ValueError("manifest serialization round-trip mismatch")
        for summary in traces.values():
            trace_path = fixture_stage / summary["path"]
            if trace_io.file_hash(trace_path) != summary["sha256"]:
                raise ValueError("manifest references a trace with a mismatched hash")
        result = {
            "terminal": "COMPLETE", "exit_status": 0,
            "command_argv": ["python3", "-B", *sys.argv],
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "source_sha256": before, "trace_count_per_profile": 288_794,
            "profile_count": len(traces), "stage_seconds": timing_snapshot(),
            "profile_seconds": profile_seconds,
        }
        write_json(evidence_stage / "result.json", result)
        os.rename(fixture_stage, FIXTURE_DIR)
        published.append(FIXTURE_DIR)
        fd, temp_name = tempfile.mkstemp(prefix=".spu_fabric_0_manifest.", dir=fixture_parent)
        temp_manifest = Path(temp_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(manifest_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temp_manifest, MANIFEST_PATH)
        temp_manifest = None
        published.append(MANIFEST_PATH)
        os.rename(evidence_stage, evidence)
        published.append(evidence)
        print(json.dumps(result, sort_keys=True))
        return 0
    except BaseException as error:
        cleanup(published)
        timed_out = isinstance(error, TimeoutError)
        if evidence_stage.exists():
            result_path = evidence_stage / "result.json"
            if result_path.exists():
                result_path.unlink()
            failure = {
                "terminal": "TIMEOUT" if timed_out else "FAILED",
                "exit_status": 124 if timed_out else 1,
                "command_argv": ["python3", "-B", *sys.argv],
                "stage": stage, "active_profile": active_profile,
                "profile_seconds": profile_seconds,
                "stage_seconds": timing_snapshot(),
                "error": repr(error),
            }
            write_json(result_path, failure)
            os.rename(evidence_stage, evidence)
        if timed_out:
            return 124
        raise
    finally:
        if temp_manifest and temp_manifest.exists():
            temp_manifest.unlink()
        if fixture_stage.exists():
            shutil.rmtree(fixture_stage)
        if evidence_stage.exists():
            shutil.rmtree(evidence_stage)


if __name__ == "__main__":
    raise SystemExit(main())
