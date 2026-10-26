"""Deterministic edge scheduler for one frozen SPU-FABRIC-0 profile."""
from __future__ import annotations

from collections import defaultdict, deque
from software.experiments.spu_fabric_0_scheduler_ops import (
    CLIENTS,
)
from software.experiments.spu_fabric_0_scheduler_accept import accept
from software.experiments.spu_fabric_0_scheduler_resources import (
    grant_products, issue_dedicated_stages, issue_shared_add, set_raw_completions,
)
from software.experiments.spu_fabric_0_scheduler_report import build_report

ALL_CLIENTS = (*CLIENTS, "d4")


def simulate(candidate: str, profile: str, records: list[dict],
              intrinsic: dict[str, int], queue_capacity: int = 4,
              max_cycles: int | None = None,
              include_operation_rows: bool = False,
              minimum_service: dict[str, int] | None = None) -> dict:
    """Run one deterministic profile; caller must validate frozen inputs first."""
    if candidate not in ("A", "B", "C"):
        raise ValueError("candidate must be A, B, or C")
    by_client = defaultdict(list)
    for row in records:
        by_client[row["client"]].append(row)
    for rows in by_client.values():
        rows.sort(key=lambda row: (row["offered_cycle"], row["client_order"]))
    index = {client: 0 for client in ALL_CLIENTS}
    pending = {client: deque() for client in ALL_CLIENTS}
    ingress = {client: deque() for client in ALL_CLIENTS}
    active = {}
    ready_edge = {client: 0 for client in ALL_CLIENTS}
    completed_operation_ids = set()
    metrics = defaultdict(int)
    stats = defaultdict(int)
    for client in ALL_CLIENTS:
        stats[f"{client}_completion_edges"] = []
        stats[f"{client}_response_cycles"] = []
        stats[f"{client}_expected_digest"] = []
        stats[f"{client}_accepted_ids"] = []
        stats[f"{client}_completed_ids"] = []
        stats[f"{client}_accepted_edges"] = []
        stats[f"{client}_completion_by_id"] = []
        stats[f"{client}_queue_wait_cycles"] = []
    product_pointer, add_pointer = 0, 0
    edge = 0
    last_offer = max((r["offered_cycle"] for r in records), default=-1)
    limit = max_cycles or (last_offer + 1_000_000)
    while edge <= limit:
        if candidate in ("B", "C"):
            set_raw_completions(active, candidate, edge, stats)
        retired = set()
        for client, job in list(active.items()):
            if job["complete_edge"] is not None and job["complete_edge"] <= edge:
                observed_service = edge - job["accepted"]
                if minimum_service is not None:
                    minimum = minimum_service[job["record"]["operation_id"]]
                    if observed_service < minimum or (candidate == "A" and observed_service != minimum):
                        raise RuntimeError(f"service timing mismatch: {job['record']['operation_id']}")
                stats[f"{client}_completed"] += 1
                stats[f"{client}_completion_edges"].append(edge)
                stats[f"{client}_response_cycles"].append(edge - job["record"]["offered_cycle"])
                stats[f"{client}_completed_ids"].append(job["record"]["operation_id"])
                stats[f"{client}_completion_by_id"].append((job["record"]["operation_id"], edge))
                completed_operation_ids.add(job["record"]["operation_id"])
                active.pop(client)
                retired.add(client)
                ready_edge[client] = edge if client == "d4" else edge + 1
        for client in ALL_CLIENTS:
            rows = by_client[client]
            while index[client] < len(rows) and rows[index[client]]["offered_cycle"] <= edge:
                pending[client].append(rows[index[client]])
                index[client] += 1
            can_accept = (client not in active and edge >= ready_edge[client] and
                          (client == "d4" or client not in retired) and
                          (not ingress[client] or
                           set(ingress[client][0].get("predecessors", [])) <= completed_operation_ids))
            if can_accept and ingress[client]:
                record = ingress[client].popleft()
                job = accept(record, candidate, edge, intrinsic, stats, minimum_service)
                if job is not None:
                    active[client] = job
                    if candidate == "A":
                        if client == "som":
                            ready_edge[client] = edge + 6
                        else:
                            ready_edge[client] = job["complete_edge"] + 1
                    elif client == "d4":
                        ready_edge[client] = edge + 1
                else:
                    completed_operation_ids.add(record["operation_id"])
            if pending[client]:
                if len(ingress[client]) < queue_capacity:
                    ingress[client].append(pending[client].popleft())
                if pending[client]:
                    stats[f"{client}_backpressure_cycles"] += 1
            metrics[f"{client}_max_ingress"] = max(
                metrics[f"{client}_max_ingress"], len(ingress[client]))
            metrics[f"{client}_ingress_occupancy_cycles"] += len(ingress[client])
        if candidate in ("B", "C"):
            product_pointer = grant_products(active, candidate, edge,
                                             product_pointer, stats)
            if candidate == "B":
                add_pointer = issue_shared_add(active, edge, add_pointer, stats)
            issue_dedicated_stages(active, candidate, edge, stats)
        complete_count = sum(stats[f"{client}_completed"] for client in ALL_CLIENTS)
        total = len(records)
        if complete_count == total and not active and all(not q for q in ingress.values()) and all(not q for q in pending.values()):
            break
        edge += 1
    else:
        raise RuntimeError(f"scheduler deadlock/watchdog at edge {edge}; completed={complete_count}/{len(records)}")
    return build_report(candidate, profile, records, stats, metrics, edge,
                        last_offer, complete_count, include_operation_rows)
