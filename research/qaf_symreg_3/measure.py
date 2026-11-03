"""Same finite query set, 2/3 feasible branches, with separate setup and join costs."""
import gc
import statistics
import sys
import time
import tracemalloc

from research.qaf_symreg_1.model import Key
from research.qaf_symreg_3.model import BranchRoster, Join, bundle_nodes
from research.qaf_symreg_3.test_model import fixture


def once(three):
    gc.collect(); tracemalloc.start(); start = time.perf_counter()
    base, paths, goal = fixture(three=three)
    x, y, z, _ = base.reg[:4]
    candidates = (goal, Key("norm", x, z, 4), Key("value", x, y, 1, True), Key("value", x, z, 1))
    join = Join(BranchRoster(paths), candidates)
    setup = time.perf_counter()-start
    _, setup_peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    source_facts = sum(len(m.facts) for _, m in paths)
    intersection = set(paths[0][1].facts)
    for _, m in paths[1:]: intersection.intersection_update(m.facts)
    reads = base.domain.reads
    start = time.perf_counter(); syntactic = [join.syntactic(q) for q in candidates]
    syntactic_s = time.perf_counter()-start
    start = time.perf_counter()
    results = []; work = 0
    for q in candidates:
        results.append(join.prove(q)); work += join.work
    semantic_s = time.perf_counter()-start
    memory_join = Join(BranchRoster(paths), candidates)
    gc.collect(); tracemalloc.start()
    for q in candidates: memory_join.prove(q)
    _, proof_peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    proven = [p for result, p in results if result == "PROVEN"]
    start = time.perf_counter(); assert all(join.validate(p) for p in proven)
    validation_s = time.perf_counter()-start
    assert base.domain.reads == reads
    return (setup, syntactic_s, semantic_s, validation_s, setup_peak, proof_peak,
            source_facts, len(intersection), syntactic.count("PROVEN"), len(proven),
            sum(len(w.path) for p in proven for _, w in p.witnesses),
            sum(bundle_nodes(p.witnesses) for p in proven), work)


if __name__ == "__main__":
    print("python", sys.version.split()[0], "repetitions=30 candidates=4")
    for branches in (2, 3):
        rows = [once(branches == 3) for _ in range(30)]
        med = [statistics.median(row[i] for row in rows) for i in range(6)]
        print("branches", branches, "setup_s", f"{med[0]:.6f}", "syntactic_s", f"{med[1]:.6f}",
              "semantic_s", f"{med[2]:.6f}", "validate_s", f"{med[3]:.6f}",
              "setup_peak_bytes", int(med[4]), "query_peak_bytes", int(med[5]),
              "facts/common/syntactic_proven/semantic_proven/bundle_edges/bundle_nodes/edge_inspections", rows[0][6:],
              "query_numeric_reads", 0)
