"""Identical all-pairs workload for explicit, sparse and rooted representations."""
import gc
import statistics
import sys
import time
import tracemalloc

from research.qaf_symreg_1.model import Key, Machine
from research.qaf_symreg_2.model import Canonical, Proof, Sparse, validate


def setup(n, kind):
    m = Machine(); ids = []
    for _ in range(n):
        assert m.write(0, 1, 2) == "OK"
        ids.append(m.reg[0])
    if kind == "explicit":
        for x in ids:
            for y in ids:
                assert m.admit_value(x, y)
        rep = None
    else:
        edges = [m.admit_value(ids[i], ids[i+1]) for i in range(n-1)]
        rep = Sparse(m) if kind == "sparse" else Canonical(m, ids[0])
        if kind == "canonical":
            for edge in edges: assert rep.attach(edge) == "STORED"
    return m, ids, rep


def queries(m, ids, rep, kind):
    proven = work = proof_edges = 0
    proof_check_s = 0.0
    before = m.domain.reads
    for x in ids:
        for y in ids:
            if kind == "explicit":
                f = m.facts.get(Key("value", x, y, 1))
                result, proof = ("PROVEN", Proof(x, y, 1, False, (f,))) if f else ("UNKNOWN", None)
                work += 1
            else:
                result, proof = rep.prove(x, y)
                work += rep.work
            if result == "PROVEN":
                proof_start = time.perf_counter()
                assert validate(m, proof, x, y, 1)
                proof_check_s += time.perf_counter() - proof_start
                proven += 1; proof_edges += len(proof.path)
            else:
                assert result in ("UNKNOWN", "RESOURCE_LIMIT")
    assert m.domain.reads == before
    return proven, work, proof_edges, proof_check_s


def sample(n, kind):
    gc.collect(); tracemalloc.start(); start = time.perf_counter()
    m, ids, rep = setup(n, kind)
    setup_s = time.perf_counter()-start
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    reads_at_setup = m.domain.reads
    start = time.perf_counter(); counts = queries(m, ids, rep, kind)
    query_s = time.perf_counter()-start
    gc.collect(); tracemalloc.start()
    queries(m, ids, rep, kind)
    _, query_peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    return setup_s, query_s, peak, len(m.facts), len(rep.nodes) if kind == "canonical" else 0, reads_at_setup, counts, query_peak


if __name__ == "__main__":
    print("python", sys.version.split()[0], "repetitions 3; exact same concrete values and all ordered pairs")
    for n in (4, 8, 12, 16):
        for kind in ("explicit", "sparse", "canonical"):
            rows = [sample(n, kind) for _ in range(3)]
            setup_s = statistics.median(r[0] for r in rows)
            query_s = statistics.median(r[1] for r in rows)
            peak = int(statistics.median(r[2] for r in rows))
            _, _, _, facts, nodes, reads, (proven, work, proof_edges, _), _ = rows[0]
            check_s = statistics.median(r[6][3] for r in rows)
            query_peak = int(statistics.median(r[7] for r in rows))
            print(f"n={n} {kind} facts={facts} nodes={nodes} proven={proven}/{n*n} "
                  f"setup_reads={reads} query_reads=0 work={work} proof_edges={proof_edges} "
                  f"setup_s={setup_s:.6f} query_s={query_s:.6f} proof_recheck_s={check_s:.6f} "
                  f"setup_peak_bytes={peak} query_peak_bytes={query_peak}")
