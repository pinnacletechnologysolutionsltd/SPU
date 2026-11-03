"""Descriptive certificate size and independent-checker cost."""
import gc
import statistics
import sys
import time
import tracemalloc

from research.qaf_symreg_4.checker import verify
from research.qaf_symreg_4.examples import build_example


if __name__ == "__main__":
    print("python", sys.version.split()[0], "repetitions=30")
    for number in (1, 2, 3):
        context, certificate = build_example(number)
        times = []
        for _ in range(30):
            start = time.perf_counter(); result = verify(certificate, context); times.append(time.perf_counter()-start)
            assert result["status"] == "VERIFIED"
        gc.collect(); tracemalloc.start()
        checked = verify(certificate, context)
        _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
        print("example", number, "certificate_bytes", len(certificate), "context_bytes", len(context),
              "steps", checked["steps"], "premises", checked["premises"], "depth", checked["depth"],
              "branches", checked["branches"], "median_check_s", f"{statistics.median(times):.6f}",
              "check_peak_python_bytes", peak)
