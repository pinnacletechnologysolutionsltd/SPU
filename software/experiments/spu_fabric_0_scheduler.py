#!/usr/bin/env python3
"""Run the frozen A/B/C schedule comparison; this is not an RTL model."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.spu_fabric_0_scheduler_engine import simulate
from software.experiments.spu_fabric_0_scheduler_io import (
    PROFILES, canonical_bytes, digest, load_profile,
)
from software.experiments.spu_fabric_0_scheduler_preflight import (
    SERVICE as SERVICE_TABLE, TIMING as TABLE, MANIFEST, load_service_table, preflight,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--preflight", action="store_true",
                        help="validate pinned traces and timing tables; do not schedule")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps({"status": "PREFLIGHT_PASS", **preflight()}, sort_keys=True))
        return 0
    if args.output_dir is None:
        parser.error("--output-dir is required unless --preflight is used")
    destination = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    staging = destination.with_name(destination.name + ".staging")
    failed = destination.with_name(destination.name + ".failed")
    if destination.exists() or staging.exists() or failed.exists():
        raise SystemExit("refusing existing destination/staging/failure path")
    staging.mkdir(parents=True)
    result = {"schema": "spu-fabric-0-phase1b-scheduler-v1", "status": "RUNNING",
              "inputs": {"manifest_sha256": digest(MANIFEST),
                         "timing_table_sha256": digest(TABLE),
                         "candidate_service_table_sha256": digest(SERVICE_TABLE)},
              "runs": []}
    result_path = staging / "result.json"
    try:
        preflight_result = preflight()
        service_table = load_service_table()
        result["preflight"] = preflight_result
        for profile in PROFILES:
            records, refs = load_profile(MANIFEST, profile, TABLE)
            profile_digests = set()
            expected_ids = {row["operation_id"] for row in records}
            for candidate in ("A", "B", "C"):
                candidate_service = service_table["entries"][candidate]
                non_d4 = {row["operation_id"] for row in records if row["client"] != "d4"}
                if set(candidate_service) != non_d4:
                    raise ValueError(f"{candidate} service table operation set mismatch")
                service_by_id = dict(candidate_service)
                service_by_id.update({row["operation_id"]: service_table["client_constants"]["d4_cycles"]
                                      for row in records if row["client"] == "d4"})
                run = simulate(candidate, profile, records, refs["intrinsic"],
                               minimum_service=service_by_id)
                run["trace_sha256"] = refs["trace_sha256"]
                profile_digests.add(run["completed_expected_digest_sha256"])
                result["runs"].append(run)
                result["status"] = "RUNNING"
                result_path.write_bytes(canonical_bytes(result))
            if len(profile_digests) != 1:
                raise ValueError(f"candidate oracle output digests differ in {profile}")
        run_index = {(run["candidate"], run["profile"]): run for run in result["runs"]}
        gate_rows = []
        for profile in PROFILES:
            base, hybrid = run_index[("A", profile)]["clients"], run_index[("C", profile)]["clients"]
            for client in ("surd_w32", "surd_w64", "som", "d4"):
                reference = base[client]["completed_throughput_per_cycle"]
                observed = hybrid[client]["completed_throughput_per_cycle"]
                ratio = observed / reference if reference else 0.0
                gate_rows.append({"profile": profile, "client": client,
                                  "candidate_c_over_a": ratio, "minimum": 0.90,
                                  "pass": ratio >= 0.90})
        result["candidate_c_throughput_gate"] = {
            "status": "PASS" if all(row["pass"] for row in gate_rows) else "FAIL",
            "per_workload": gate_rows,
        }
        result["status"] = "PASS"
        result_path.write_bytes(canonical_bytes(result))
        os.replace(staging, destination)
        print(json.dumps({"status": "PASS", "output": str(destination),
                          "runs": len(result["runs"])}, sort_keys=True))
        return 0
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        result_path.write_bytes(canonical_bytes(result))
        os.replace(staging, failed)
        print(json.dumps({"status": "FAILED", "output": str(failed),
                          "error": result["error"]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
