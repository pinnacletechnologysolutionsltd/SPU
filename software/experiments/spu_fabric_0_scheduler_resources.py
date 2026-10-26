"""Resource arbitration and dedicated stages for the FABRIC-0 candidates."""
from __future__ import annotations

from software.experiments.spu_fabric_0_scheduler_ops import (
    CLIENTS, mark_add, mark_products, products_available, ready_adds,
    ready_products, som_node_products_ready, som_product_rank,
    surd_product_rank, surd_raw_ready,
)


def grant_products(active: dict, candidate: str, edge: int,
                   pointer: int, stats: dict) -> int:
    ready = {}
    for client in CLIENTS:
        job = active.get(client)
        if job:
            names = ready_products(job, edge)
            if names:
                key = surd_product_rank if client.startswith("surd_") else som_product_rank
                ready[client] = sorted(names, key=key)
    lanes = 1 if candidate == "B" else 2
    order, granted = list(CLIENTS), []
    for step in range(len(order)):
        client = order[(pointer + step) % len(order)]
        if client in ready:
            granted.append(client)
            if len(granted) == lanes:
                break
    for lane, client in enumerate(granted):
        mark_products(active[client], [ready[client][0]], edge)
        stats[f"product_lane_{lane}_busy_cycles"] += 1
    if granted:
        pointer = (order.index(granted[-1]) + 1) % len(order)
    for client in ready:
        if client not in granted:
            stats[f"{client}_product_arbitration_stall_cycles"] += 1
    return pointer


def issue_shared_add(active: dict, edge: int, pointer: int, stats: dict) -> int:
    ready = {}
    for client in CLIENTS:
        job = active.get(client)
        if job:
            tasks = ready_adds(job, edge)
            if tasks:
                ready[client] = min(tasks, key=lambda name: next(
                    i for i, task in enumerate(job["adds"]) if task[0] == name))
    order = list(CLIENTS)
    chosen = next((order[(pointer + i) % len(order)] for i in range(len(order))
                   if order[(pointer + i) % len(order)] in ready), None)
    if chosen is not None:
        mark_add(active[chosen], ready[chosen], edge)
        stats["shared_add_lane_busy_cycles"] += 1
        pointer = (order.index(chosen) + 1) % len(order)
    for client in ready:
        if client != chosen:
            stats[f"{client}_add_arbitration_stall_cycles"] += 1
    return pointer


def issue_dedicated_stages(active: dict, candidate: str, edge: int,
                           stats: dict) -> None:
    for client, job in active.items():
        if client.startswith("surd_") and candidate == "C" and not job["reducer_issued"]:
            if products_available(job, ("aa", "bb", "ab", "ba", "dd"), edge):
                job["reducer_issued"] = True
                job["reducer_done_edge"] = edge + 1
                stats[f"{client}_reducer_busy_cycles"] += 1
        elif client == "som" and candidate == "C" and job["som_next_node"] < 4:
            node = job["som_next_node"]
            if som_node_products_ready(job, node, edge):
                job["som_next_node"] += 1
                stats["som_node_reducer_busy_cycles"] += 1
                if node == 3:
                    job["complete_edge"] = edge + 1
        elif client == "som" and candidate == "B" and job["compare_next_node"] < 4:
            node = job["compare_next_node"]
            if job["add_ready"].get(f"reduce_{node}_2", edge + 1) <= edge:
                job["compare_next_node"] += 1
                stats["som_winner_compare_busy_cycles"] += 1
                if node == 3:
                    job["complete_edge"] = edge + 1


def set_raw_completions(active: dict, candidate: str, edge: int,
                        stats: dict) -> None:
    for client, job in active.items():
        if not client.startswith("surd_") or job["raw_ready_edge"] is not None:
            continue
        ready = surd_raw_ready(job, edge) if candidate == "C" else (
            job["add_ready"].get("raw_a", edge + 1) <= edge and
            job["add_ready"].get("raw_b", edge + 1) <= edge and
            products_available(job, ("dd",), edge))
        if ready:
            job["raw_ready_edge"] = edge
            if job["record"]["expected"]["request_normalization"]:
                job["complete_edge"] = edge + job["intrinsic"] - 1
                stats[f"{client}_normalizer_busy_cycles"] += max(0, job["intrinsic"] - 3)
            else:
                job["complete_edge"] = edge
