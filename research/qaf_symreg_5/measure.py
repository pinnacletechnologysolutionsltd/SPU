"""Small descriptive measurement, including independent proof checking."""
import statistics
import time
import tracemalloc
from research.qaf_symreg_5.checker import assess
from research.qaf_symreg_5.test_context import fixture


def main():
    start = time.perf_counter()
    authority, _, _, _, _, envelope = fixture()
    view = authority.view()
    setup = time.perf_counter() - start
    samples = []
    for _ in range(30):
        start = time.perf_counter()
        result = assess(envelope, view)
        samples.append(time.perf_counter() - start)
    tracemalloc.start()
    assess(envelope, view)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print("envelope_bytes", len(envelope), "authority_view_bytes", len(view),
          "setup_s", round(setup, 6), "median_verify_s", round(statistics.median(samples), 6),
          "peak_verification_python_bytes", peak, "proof", result["math"])


if __name__ == "__main__":
    main()
