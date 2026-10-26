#!/usr/bin/env python3
"""Materialize the frozen Candidate A intrinsic timing input table."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.spu_fabric_0_timing_reference import operation_latency

MANIFEST = ROOT / "fixtures/spu_fabric_0/manifest.json"
PROFILES = ("isolated", "burst_synthetic", "steady_synthetic")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def build_table() -> dict:
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    baseline_digests = None
    timing = {}
    counts = {"surd_w32": 0, "surd_w64": 0, "som": 0, "d4": 0}
    for profile_index, profile in enumerate(PROFILES):
        info = manifest["traces"][profile]
        path = MANIFEST.parent / info["path"]
        digest = file_hash(path)
        if digest != info["sha256"]:
            raise ValueError(f"frozen trace hash mismatch: {profile}")
        current_digests = {"surd_w32": [], "surd_w64": [], "som": [], "d4": []}
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                client, opid = row["client"], row["operation_id"]
                if client not in counts:
                    raise ValueError(f"unknown client: {client}")
                if row["client_order"] != counts[client]:
                    raise ValueError(f"non-source order or duplicate operation in {profile}: {opid}")
                semantic = {"operation_id": opid, "client": client,
                            "operands": row["operands"], "expected": row["expected"],
                            "initial_state": row["initial_state"],
                            "predecessors": row["predecessors"]}
                signature = hashlib.sha256(canonical(semantic)).digest()
                current_digests[client].append(signature)
                if profile_index == 0:
                    if client.startswith("surd_w"):
                        width = int(client.removeprefix("surd_w"))
                        cycles, gcd_cycles = operation_latency(row, width)
                        timing[opid] = {"client": client, "cycles": cycles,
                                        "gcd_cycles": gcd_cycles,
                                        "kind": "source_derived_surd_operator"}
                    elif client == "som":
                        timing[opid] = {"client": client, "cycles": 4,
                                        "kind": "source_derived_sequential_scan"}
                    # D4 and SOM use the explicit client constants below.
                counts[client] += 1
        observed = {client: len(rows) for client, rows in current_digests.items()}
        wanted = info["client_counts"]
        if observed != wanted:
            raise ValueError(f"client count mismatch in {profile}: {observed}")
        if baseline_digests is None:
            baseline_digests = current_digests
        elif current_digests != baseline_digests:
            raise ValueError(f"operation semantics/order differ in {profile}")
        counts = {"surd_w32": 0, "surd_w64": 0, "som": 0, "d4": 0}
    return {
        "schema": "spu-fabric-0-phase1b-intrinsic-timing-v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "timing_reference_sha256": file_hash(ROOT / "software/experiments/spu_fabric_0_timing_reference.py"),
        "trace_sha256": {p: manifest["traces"][p]["sha256"] for p in PROFILES},
        "operation_count": sum(manifest["source_case_counts"].values()),
        "client_constants": {"som_cycles": 4, "d4_cycles": 1},
        "surd_domain_upper_bounds": {"W32": 343, "W64": 663},
        "fixture_maxima": {"W32": 237, "W64": 467},
        "entries": timing,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    table = build_table()
    payload = canonical(table)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"output": str(args.output), "sha256": hashlib.sha256(payload).hexdigest(),
                      "operation_count": table["operation_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
