"""Request admission and immutable expected-result accounting."""
from __future__ import annotations

from hashlib import sha256
import json

from software.experiments.spu_fabric_0_scheduler_ops import new_job


def digest_expected(record: dict) -> str:
    expected = dict(record["expected"])
    if expected.get("result_defined") is False:
        expected.pop("result", None)
    raw = json.dumps({"operation_id": record["operation_id"], "expected": expected},
                     sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256((raw + "\n").encode()).hexdigest()


def accept(record: dict, candidate: str, edge: int, intrinsic: dict,
           stats: dict, minimum_service: dict[str, int] | None = None) -> dict | None:
    client, operation_id = record["client"], record["operation_id"]
    stats[f"{client}_accepted"] += 1
    stats[f"{client}_expected_digest"].append(digest_expected(record))
    stats[f"{client}_accepted_ids"].append(operation_id)
    stats[f"{client}_accepted_edges"].append((operation_id, edge))
    stats[f"{client}_queue_wait_cycles"].append(edge - record["offered_cycle"])
    if record["expected"].get("invalid") and client != "d4":
        if minimum_service is not None and minimum_service[operation_id] != 0:
            raise RuntimeError("zero-cycle invalid completion disagrees with service table")
        stats[f"{client}_completed"] += 1
        stats[f"{client}_completion_edges"].append(edge)
        stats[f"{client}_response_cycles"].append(edge - record["offered_cycle"])
        stats[f"{client}_completed_ids"].append(operation_id)
        stats[f"{client}_completion_by_id"].append((operation_id, edge))
        return None
    if candidate == "A":
        latency = intrinsic[operation_id]
        job = {"record": record, "client": client, "accepted": edge,
               "complete_edge": edge + latency}
        if client == "d4":
            stats["d4_path_busy_cycles"] += 1
        elif client == "som":
            stats["som_scan_busy_cycles"] += 4
        elif record["expected"].get("request_normalization"):
            stats[f"{client}_product_lanes_busy_cycles"] += 5
            stats[f"{client}_normalizer_busy_cycles"] += max(0, latency - 3)
        else:
            stats[f"{client}_product_lanes_busy_cycles"] += 5
        return job
    job = new_job(record, candidate, edge, intrinsic.get(operation_id))
    if client == "d4":
        job["complete_edge"] = edge + 1
        stats["d4_path_busy_cycles"] += 1
    return job
