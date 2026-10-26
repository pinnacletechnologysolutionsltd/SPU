"""Single-operation DAG state for the SPU-FABRIC-0 schedule model."""
from __future__ import annotations


CLIENTS = ("surd_w32", "surd_w64", "som")
SURD_PRODUCTS = ("aa", "bb", "ab", "ba", "dd")


def new_job(record: dict, candidate: str, accepted: int,
            intrinsic_cycles: int | None = None) -> dict:
    client = record["client"]
    products = (SURD_PRODUCTS if client.startswith("surd_") else
                tuple(f"{kind}_{node}_{feature}"
                      for node in range(4) for feature in range(4)
                      for kind in ("p", "q")) if client == "som" else ())
    adds = []
    if client.startswith("surd_") and candidate == "B":
        adds = [("three_bb", ("bb",)), ("raw_a", ("aa", "three_bb")),
                ("raw_b", ("ab", "ba"))]
    if client == "som" and candidate == "B":
        for node in range(4):
            for feature in range(4):
                adds += [(f"three_q_{node}_{feature}", (f"q_{node}_{feature}",)),
                         (f"feature_{node}_{feature}",
                          (f"p_{node}_{feature}", f"three_q_{node}_{feature}"))]
            adds += [(f"reduce_{node}_0", (f"feature_{node}_0", f"feature_{node}_1")),
                     (f"reduce_{node}_1", (f"reduce_{node}_0", f"feature_{node}_2")),
                     (f"reduce_{node}_2", (f"reduce_{node}_1", f"feature_{node}_3"))]
    return {"record": record, "client": client, "candidate": candidate,
            "accepted": accepted, "intrinsic": intrinsic_cycles,
            "products": products, "product_ready": {}, "product_issued": set(),
            "adds": adds, "add_ready": {}, "add_issued": set(),
            "reducer_issued": False, "som_next_node": 0,
            "compare_next_node": 0, "reducer_done_edge": None,
            "raw_ready_edge": None, "complete_edge": None,
            "completion_recorded": False}


def ready_products(job: dict, edge: int) -> list[str]:
    return [name for name in job["products"]
            if name not in job["product_issued"]]


def mark_products(job: dict, names: list[str], edge: int) -> None:
    for name in names:
        job["product_issued"].add(name)
        job["product_ready"][name] = edge + 1


def ready_adds(job: dict, edge: int) -> list[str]:
    ready = []
    for name, dependencies in job["adds"]:
        if name in job["add_issued"]:
            continue
        if all(job["product_ready"].get(dep, edge + 1) <= edge or
               job["add_ready"].get(dep, edge + 1) <= edge
               for dep in dependencies):
            ready.append(name)
    return ready


def mark_add(job: dict, name: str, edge: int) -> None:
    job["add_issued"].add(name)
    job["add_ready"][name] = edge + 1


def products_available(job: dict, names: tuple[str, ...], edge: int) -> bool:
    return all(job["product_ready"].get(name, edge + 1) <= edge for name in names)


def surd_raw_ready(job: dict, edge: int) -> bool:
    if job["candidate"] == "B":
        return (job["add_ready"].get("raw_a", edge + 1) <= edge and
                job["add_ready"].get("raw_b", edge + 1) <= edge and
                products_available(job, ("dd",), edge))
    if job["candidate"] == "C":
        return (job["reducer_done_edge"] is not None and
                job["reducer_done_edge"] <= edge)
    return False


def som_node_products_ready(job: dict, node: int, edge: int) -> bool:
    names = tuple(f"{kind}_{node}_{feature}" for feature in range(4)
                  for kind in ("p", "q"))
    return products_available(job, names, edge)


def surd_product_rank(name: str) -> int:
    return SURD_PRODUCTS.index(name)


def som_product_rank(name: str) -> tuple[int, int, int]:
    _, node, feature = name.split("_")
    kind = name[0]
    return int(node), int(feature), 0 if kind == "p" else 1


def add_rank(job: dict, name: str) -> int:
    return next(i for i, task in enumerate(job["adds"]) if task[0] == name)
