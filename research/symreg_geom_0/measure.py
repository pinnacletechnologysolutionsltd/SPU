import statistics
import time
import tracemalloc
from research.symreg_geom_0.checker import check
from research.symreg_geom_0.model import QUARTER, certificate

cert = certificate([QUARTER]*8)
times = []
for _ in range(30):
    start = time.perf_counter()
    result = check(cert)
    times.append(time.perf_counter()-start)
tracemalloc.start()
check(cert)
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print("bytes", len(cert), "steps", 8, "median_s", round(statistics.median(times), 6),
      "peak_python_bytes", peak, "result", result)
