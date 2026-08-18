#!/usr/bin/env python3
"""test_spu4_som_edge_demo.py — hardware-free regression for
tools/spu4_som_edge_demo.py.

Checks the demo's query set is oracle-consistent, and the full script
flow (boot-line drop, per-query send/receive, PASS/FAIL detection) against
a fake serial port shaped like the interactive probe's UART output.

No hardware required. Run: python3 software/tests/test_spu4_som_edge_demo.py
"""

import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import spu4_som_edge_demo as sed  # noqa: E402
from software.lib.spu4_som_edge_oracle import find_bmu_edge  # noqa: E402

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── Part 1: query set is internally oracle-consistent ─────────────────

nodes = sed.node_weights_as_surds("oracle_fixture")
queries = sed.build_demo_queries(nodes)
check("build_demo_queries returns 5 queries (4 exact-match + 1 midpoint)",
      len(queries) == 5)

for i, (label, features) in enumerate(queries[:4]):
    oracle_node, oracle_q = find_bmu_edge(features, nodes)
    check(f"'{label}' oracle verdict is exactly its own node, Q=0",
          oracle_node == i and oracle_q == 0)


def result_line(ch, node, quad, status=0x06, latency=0x001, rid=0x1120):
    return f"SOM:{ch} N={node:X} Q={quad:08X} S={status:02X} L={latency:03X} I={rid:04X}\r\n"


# ── Part 2: full script flow against a fake serial port ───────────────

class FakeSerial:
    def __init__(self, lines):
        self._lines = list(lines)
        self.written = []
        self.reset_calls = 0

    def reset_input_buffer(self):
        self.reset_calls += 1

    def readline(self):
        if not self._lines:
            return b""
        return self._lines.pop(0).encode("ascii")

    def write(self, data):
        self.written.append(bytes(data))

    def close(self):
        pass


def expected_lines_for(query_list):
    """The oracle-correct response line for every query, in order --
    matches what real (working) hardware would send back."""
    lines = []
    for _, features in query_list:
        node, quad = find_bmu_edge(features, nodes)
        lines.append(result_line("D", node, quad))
    return lines


def run_script(response_lines, extra_argv=None):
    fake = FakeSerial(["stray partial line"] + response_lines)
    real_serial_ctor = sed.serial.Serial
    sed.serial.Serial = lambda *a, **k: fake
    try:
        argv = ["--port", "/dev/fake"] + (extra_argv or [])
        rc = sed.main(argv)
    finally:
        sed.serial.Serial = real_serial_ctor
    return rc, fake


# All-correct hardware responses -> PASS.
rc, fake = run_script(expected_lines_for(queries))
check("all-correct hardware responses: exit code 0", rc == 0)
check("all-correct hardware responses: sent exactly 5 queries",
      len(fake.written) == 5)
check("all-correct hardware responses: dropped one stray partial line",
      fake.reset_calls == 1)

# The first query's encoded bytes match ProbeTransport.encode_query exactly.
from software.lib.spu4_som_probe_client import encode_query  # noqa: E402
check("first query sent matches encode_query(nodes[0]) exactly",
      fake.written[0] == encode_query(queries[0][1]))

# One wrong response (bad quadrance) -> FAIL, but the script still completes
# and reports all 5 queries (doesn't abort early on a mismatch).
bad_lines = expected_lines_for(queries)
bad_lines[2] = result_line("D", 2, 9999)  # correct node, wrong quadrance
rc2, fake2 = run_script(bad_lines)
check("one mismatched quadrance: exit code 1", rc2 == 1)
check("one mismatched quadrance: still sent all 5 queries",
      len(fake2.written) == 5)

# A malformed-query ('F') response counts as a failure, not a crash.
f_lines = expected_lines_for(queries)
f_lines[1] = result_line("F", 0, 0)
rc3, _ = run_script(f_lines)
check("'F' (malformed-query) response: exit code 1", rc3 == 1)

# Timeout on the LAST query (no terminal line ever arrives for it, and
# nothing queued after it either) -> FAIL, and the script doesn't hang
# past --timeout. Replacing anything but the last query would shift every
# later query's canned response out of alignment against the flat queue,
# which is a queue-bookkeeping artifact of this fake, not something worth
# testing here.
timeout_lines = expected_lines_for(queries)[:-1]
timeout_lines.append("SOM:. N=0 Q=00000000 S=04 L=000 I=1120\r\n")  # idle only
rc4, fake4 = run_script(timeout_lines, extra_argv=["--timeout", "0.05"])
check("no terminal line for the last query: exit code 1", rc4 == 1)
check("no terminal line for the last query: still sent all 5 queries",
      len(fake4.written) == 5)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
