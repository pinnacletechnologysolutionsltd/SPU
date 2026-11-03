"""Small deterministic cost observations, not a performance benchmark claim."""
import gc
import sys
import time
import tracemalloc

from research.qaf_symreg_1.model import Machine


def build(n):
    m = Machine(); ids = []
    for _ in range(n):
        m.write(0, 1, 2); ids.append(m.reg[0])
    for x in ids:
        for y in ids:
            m.admit_value(x, y)
    return m


def peak_growth(n):
    gc.collect(); tracemalloc.start()
    m = build(n)
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    return len(m.facts), peak


def timing():
    m = Machine(); m.write(0, 1, 2); m.write(1, 1, 2)
    fact = m.admit_value(m.reg[0], m.reg[1]); m.project_norm(fact); m.inferences = 0
    count = 10000
    before = m.domain.reads
    start = time.perf_counter()
    for _ in range(count):
        assert m.query(0, 1, "norm")[0] == "PROVEN"
    symbolic = time.perf_counter() - start
    reads = m.domain.reads - before
    start = time.perf_counter()
    for _ in range(count):
        a, b = m.domain.values[m.reg[0]]
        c, d = m.domain.values[m.reg[1]]
        assert a*a-3*b*b == c*c-3*d*d
    direct = time.perf_counter() - start
    start = time.perf_counter()
    known = True
    for _ in range(count):
        assert known
    manual = time.perf_counter() - start
    print("queries", count, "symbolic_seconds", f"{symbolic:.6f}",
          "direct_seconds", f"{direct:.6f}", "manual_seconds", f"{manual:.6f}",
          "symbolic_numeric_reads", reads, "symbolic_fact_inspections", m.inferences,
          "direct_norm_evaluations", 2*count)


def chain(length):
    m = Machine(); m.write(0, 1, 2); first = m.reg[0]
    previous, accumulated = first, None
    reads_before_composition = 0
    for _ in range(length):
        m.write(0, 1, 2); current = m.reg[0]
        edge = m.admit_value(previous, current)
        before = m.domain.reads
        accumulated = edge if accumulated is None else m.compose(accumulated, edge)
        reads_before_composition += m.domain.reads - before
        previous = current
    def depth(fact):
        return 1 + max((depth(p) for p in fact.parents), default=0)
    print("chain_edges", length, "stored_facts", len(m.facts),
          "derivation_depth", depth(accumulated), "composition_numeric_reads", reads_before_composition)


if __name__ == "__main__":
    print("python", sys.version.split()[0])
    for size in (4, 8, 12, 16):
        count, peak = peak_growth(size)
        print("identities", size, "ordered_equal_facts", count, "peak_python_bytes", peak)
    timing()
    for size in (1, 4, 8, 16):
        chain(size)
