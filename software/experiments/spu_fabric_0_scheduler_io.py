"""Frozen input validation and canonical serialization for FABRIC-0."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ("isolated", "burst_synthetic", "steady_synthetic")
CLIENTS = ("surd_w32", "surd_w64", "som", "d4")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_profile(manifest_path: Path, profile: str, table_path: Path) -> tuple[list[dict], dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    table = json.loads(table_path.read_text(encoding="utf-8"))
    if table.get("schema") != "spu-fabric-0-phase1b-intrinsic-timing-v1":
        raise ValueError("unsupported timing table schema")
    if table["manifest_sha256"] != digest(manifest_path):
        raise ValueError("timing table manifest identity mismatch")
    timing_source = ROOT / "software/experiments/spu_fabric_0_timing_reference.py"
    if table["timing_reference_sha256"] != digest(timing_source):
        raise ValueError("timing reference identity mismatch")
    info = manifest["traces"][profile]
    trace_path = manifest_path.parent / info["path"]
    if digest(trace_path) != info["sha256"] or table["trace_sha256"][profile] != info["sha256"]:
        raise ValueError(f"frozen trace hash mismatch: {profile}")
    records, seen, last_key = [], set(), (-1, -1, -1)
    oracle_hash = hashlib.sha256()
    last_order = {client: -1 for client in CLIENTS}
    last_offer_by_client = {client: -1 for client in CLIENTS}
    with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            client, opid = row.get("client"), row.get("operation_id")
            if client not in CLIENTS or opid in seen:
                raise ValueError(f"invalid or duplicate trace operation: {opid}")
            if (not isinstance(opid, str) or not isinstance(row.get("offered_cycle"), int) or
                    not isinstance(row.get("client_order"), int) or row["offered_cycle"] < 0):
                raise ValueError("malformed operation identity or offer cycle")
            key = (row.get("offered_cycle", -1), CLIENTS.index(client),
                   row.get("client_order", -1))
            if row.get("profile") != profile or key < last_key:
                raise ValueError("profile or global offered order mismatch")
            if row.get("client_order", -1) != last_order[client] + 1:
                raise ValueError(f"source order mismatch for {client}")
            if row["offered_cycle"] == last_offer_by_client[client]:
                raise ValueError(f"more than one offered operation per client-cycle: {client}")
            predecessors = row.get("predecessors")
            if not isinstance(predecessors, list) or any(pred not in seen for pred in predecessors):
                raise ValueError(f"missing or forward predecessor reference: {opid}")
            expected_row = row.get("expected", {})
            if not isinstance(expected_row.get("invalid"), bool) or not isinstance(expected_row.get("result_defined"), bool):
                raise ValueError(f"malformed output validity contract: {opid}")
            if expected_row["result_defined"] is False and expected_row.get("result") is not None:
                raise ValueError(f"undefined result has asserted bits: {opid}")
            if expected_row["result_defined"] is True and "result" not in expected_row:
                raise ValueError(f"defined result is missing: {opid}")
            expected = dict(expected_row)
            if expected.get("result_defined") is False:
                expected.pop("result", None)
            oracle_hash.update(canonical_bytes({"operation_id": opid,
                                                "expected": expected}))
            last_key, last_order[client] = key, row["client_order"]
            last_offer_by_client[client] = row["offered_cycle"]
            seen.add(opid)
            records.append(row)
    if len(records) != sum(info["client_counts"].values()):
        raise ValueError("incomplete frozen trace")
    if oracle_hash.hexdigest() != info["expected_digest_sha256"]:
        raise ValueError("frozen expected-value digest mismatch")
    for client in CLIENTS:
        if last_order[client] + 1 != info["client_counts"][client]:
            raise ValueError(f"incomplete client trace: {client}")
    if table["operation_count"] != len(records):
        raise ValueError("timing table operation count mismatch")
    intrinsic = {}
    for row in records:
        entry = table["entries"].get(row["operation_id"])
        if entry:
            intrinsic[row["operation_id"]] = entry["cycles"]
        elif row["client"] == "som":
            intrinsic[row["operation_id"]] = table["client_constants"]["som_cycles"]
        elif row["client"] == "d4":
            intrinsic[row["operation_id"]] = table["client_constants"]["d4_cycles"]
        else:
            raise ValueError(f"missing intrinsic timing: {row['operation_id']}")
    return records, {"manifest": manifest, "table": table,
                     "trace_sha256": info["sha256"], "intrinsic": intrinsic}


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False) + "\n").encode("utf-8")
