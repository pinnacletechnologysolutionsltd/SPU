#!/usr/bin/env python3
"""test_spu4_som_edge_smoketest.py — hardware-free regression for
tools/spu4_som_edge_smoketest.py.

Checks the golden-answer comparison logic directly, and the full script
flow (stray partial line, running lines, terminal line, exit code) against
a fake serial port shaped like the fixed probe's free-running UART output.

No hardware required. Run: python3 software/tests/test_spu4_som_edge_smoketest.py
"""

import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import spu4_som_edge_smoketest as st  # noqa: E402
from software.lib.spu4_som_probe_parser import parse_line  # noqa: E402

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── Part 1: check_result() reasons ──────────────────────────────────────

GOLDEN = "SOM:P N=1 Q=00001900 S=06 L=012 I=1020\r\n"  # S=06: silicon-verified, docs/hardware_evidence.md §3.2j.7

ok, reasons = st.check_result(parse_line(GOLDEN))
check("golden line: ok == True", ok is True)
check("golden line: no reasons", reasons == [])

ok, reasons = st.check_result(None)
check("no result: ok == False", ok is False)
check("no result: one reason (timeout)", len(reasons) == 1)

ok, reasons = st.check_result(parse_line("SOM:F N=0 Q=00000000 S=06 L=001 I=1020\r\n"))
check("FAIL-status line: ok == False", ok is False)
check("FAIL-status line: reports the probe's own FAIL",
      any("probe itself reported FAIL" in r for r in reasons))

wrong_node = parse_line("SOM:P N=2 Q=00001900 S=06 L=012 I=1020\r\n")
ok, reasons = st.check_result(wrong_node)
check("wrong node (probe says P but node mismatches): ok == False", ok is False)
check("wrong node: reason names best_node", any("best_node" in r for r in reasons))

wrong_q = parse_line("SOM:P N=1 Q=00000000 S=06 L=012 I=1020\r\n")
ok, reasons = st.check_result(wrong_q)
check("wrong quadrance: ok == False", ok is False)
check("wrong quadrance: reason names best_quadrance",
      any("best_quadrance" in r for r in reasons))

busy_set = parse_line("SOM:P N=1 Q=00001900 S=0F L=012 I=1020\r\n")
ok, reasons = st.check_result(busy_set)
check("busy bit set: ok == False", ok is False)
check("busy bit set: reason names busy", any("busy" in r for r in reasons))


# ── Part 2: full script flow against a fake free-running serial port ──────

class FakeSerial:
    """Plays back a canned sequence of lines, reproducing the probe's
    free-running (not request/response) UART shape."""

    def __init__(self, port, baud, timeout=1):
        self.port = port
        self.baud = baud
        self.reset_calls = 0

    def set_lines(self, lines):
        self._lines = list(lines)

    def reset_input_buffer(self):
        self.reset_calls += 1

    def readline(self):
        if not self._lines:
            return b""
        return self._lines.pop(0).encode("ascii")

    def close(self):
        pass


def run_script(lines, timeout=0.2):
    fake = FakeSerial("/dev/fake", 115200)
    fake.set_lines(lines)
    real_serial_ctor = st.serial.Serial
    st.serial.Serial = lambda *a, **k: fake
    try:
        rc = st.main(["--port", "/dev/fake", "--timeout", str(timeout)])
    finally:
        st.serial.Serial = real_serial_ctor
    return rc, fake


# Stray partial line (dropped by reset+first readline), then a couple of
# "still running" lines, then the golden terminal line.
rc, fake = run_script([
    "1900 S=07 L=00",  # partial line left over from before this script attached
    "SOM:. N=0 Q=00000000 S=05 L=000 I=1020\r\n",
    "SOM:. N=0 Q=00000000 S=05 L=004 I=1020\r\n",
    GOLDEN,
])
check("PASS scenario returns exit code 0", rc == 0)
check("PASS scenario called reset_input_buffer once", fake.reset_calls == 1)

rc2, _ = run_script(["SOM:F N=0 Q=00000000 S=06 L=001 I=1020\r\n"])
check("FAIL scenario returns exit code 1", rc2 == 1)

rc3, _ = run_script(["SOM:. N=0 Q=00000000 S=05 L=000 I=1020\r\n"])
check("timeout (no terminal line ever arrives) returns exit code 1", rc3 == 1)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
