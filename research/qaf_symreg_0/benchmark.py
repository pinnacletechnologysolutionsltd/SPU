"""Deterministic observational workload; timings include Python overhead."""
import gc
import sys
import time
import tracemalloc
from fractions import Fraction

from research.qaf_symreg_0.model import Model
from software.experiments.surd_register_exact import R
from research.qaf_symreg_0.test_model import oracle

COUNT = 10000
R0 = R(1, 2, 3)
R1 = R(2, 4, 6)


def baseline():
    out = []
    for i in range(COUNT):
        r = R0 if i % 2 == 0 else R1
        out.append(Fraction(r.a*r.a - 3*r.b*r.b, r.d*r.d))
    return out, {"norm_evaluations": COUNT, "norm_reuses": 0, "bookkeeping": 0}


def hoisted():
    # Workload-specific manually optimized baseline: equality known at design time.
    value = Fraction(R0.a*R0.a - 3*R0.b*R0.b, R0.d*R0.d)
    return [value for _ in range(COUNT)], {"norm_evaluations": 1, "norm_reuses": COUNT - 1, "bookkeeping": 0}


def shadow():
    m = Model()
    assert m.load(0, R0) == "OK" and m.load(1, R1) == "OK"
    assert m.prove_equal(0, 1)
    values = [m.norm(i % 2) for i in range(COUNT)]
    return values, m.stats


def measure(fn):
    gc.collect()
    start = time.perf_counter()
    values, stats = fn()
    elapsed = time.perf_counter() - start
    reference = oracle(R0)
    mismatches = sum(v != reference for v in values)
    del values
    gc.collect()
    tracemalloc.start()
    values, _ = fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return stats, elapsed, peak, mismatches


if __name__ == "__main__":
    assert oracle(R0) == oracle(R1)
    print("python", sys.version.split()[0], "queries", COUNT)
    for name, fn in (("numerical", baseline), ("manual_hoist", hoisted), ("shadow", shadow)):
        stats, elapsed, peak, errors = measure(fn)
        print(name, stats, "seconds", f"{elapsed:.6f}", "peak_bytes", peak, "mismatches", errors)
