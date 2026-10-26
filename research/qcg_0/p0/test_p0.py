"""Development tests for the QCG-0 P0 code. Run: python3 -B -I test_p0.py (under the dev limits)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_lu, test_cells, test_misc, test_orch  # noqa: F401  (importing registers their tests)
from test_lu import test, TESTS


def main():
    bad = 0
    for f in TESTS:
        try:
            f()
            print("PASS", f.__name__)
        except Exception as e:  # noqa: BLE001
            import traceback
            bad += 1
            print("FAIL", f.__name__, repr(e))
            traceback.print_exc()
    print("RESULT", "FAIL" if bad else "PASS", "%d/%d" % (len(TESTS) - bad, len(TESTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
