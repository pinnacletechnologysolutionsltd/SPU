"""Completion accounting and per-client schedule result reporting."""
from __future__ import annotations

from hashlib import sha256

from software.experiments.spu_fabric_0_scheduler_ops import CLIENTS

ALL_CLIENTS = (*CLIENTS, "d4")


def build_report(candidate: str, profile: str, records: list[dict], stats: dict,
                 metrics: dict, edge: int, last_offer: int, complete_count: int,
                 include_operation_rows: bool = False) -> dict:
    for client in ALL_CLIENTS:
        expected_ids = [row["operation_id"] for row in records if row["client"] == client]
        if (sorted(stats[f"{client}_accepted_ids"]) != sorted(expected_ids) or
                sorted(stats[f"{client}_completed_ids"]) != sorted(expected_ids)):
            raise RuntimeError(f"{client} acceptance/completion identity mismatch")
    elapsed = edge + 1
    resources = {key: value for key, value in stats.items() if isinstance(value, int)}
    output = {"candidate": candidate, "profile": profile,
              "offered_operations": len(records), "completed_operations": complete_count,
              "elapsed_cycles": elapsed, "drain_cycles": max(0, edge - last_offer),
              "resources": dict(sorted(resources.items())),
              "ingress": {client: {"max_occupancy": metrics[f"{client}_max_ingress"],
                                   "occupancy_cycles": metrics[f"{client}_ingress_occupancy_cycles"]}
                          for client in ALL_CLIENTS}}
    utilization = {}
    for name, busy in resources.items():
        if not name.endswith("_busy_cycles"):
            continue
        lanes = 5 if name.endswith("_product_lanes_busy_cycles") else 1
        utilization[name.removesuffix("_busy_cycles")] = busy / (lanes * elapsed)
    output["resource_utilization_fraction"] = dict(sorted(utilization.items()))
    per_client = {}
    for client in ALL_CLIENTS:
        offered = [row for row in records if row["client"] == client]
        done_edges, responses = (stats[f"{client}_completion_edges"],
                                 stats[f"{client}_response_cycles"])
        if not offered:
            continue
        first, last = offered[0]["offered_cycle"], offered[-1]["offered_cycle"]
        completion_end = max(done_edges, default=first)
        waits = stats[f"{client}_queue_wait_cycles"]
        per_client[client] = {
            "offered": len(offered), "accepted": stats[f"{client}_accepted"],
            "completed": stats[f"{client}_completed"],
            "offered_throughput_per_cycle": len(offered) / (last - first + 1),
            "completed_throughput_per_cycle": len(done_edges) / (completion_end - first + 1),
            "max_response_cycles": max(responses, default=0),
            "mean_response_cycles": sum(responses) / len(responses) if responses else 0,
            "max_queue_wait_cycles": max(waits, default=0),
            "mean_queue_wait_cycles": sum(waits) / len(waits) if waits else 0,
            "backpressure_cycles": stats[f"{client}_backpressure_cycles"],
        }
    output["clients"] = per_client
    digests = [item for client in ALL_CLIENTS for item in stats[f"{client}_expected_digest"]]
    output["completed_expected_digest_sha256"] = sha256("".join(sorted(digests)).encode()).hexdigest()
    if include_operation_rows:
        accepted = {opid: cycle for client in ALL_CLIENTS
                    for opid, cycle in stats[f"{client}_accepted_edges"]}
        completed = {opid: cycle for client in ALL_CLIENTS
                     for opid, cycle in stats[f"{client}_completion_by_id"]}
        output["operation_rows"] = {
            opid: {"accepted_edge": accepted[opid], "completion_edge": completed[opid],
                   "service_cycles": completed[opid] - accepted[opid]}
            for opid in accepted
        }
    return output
