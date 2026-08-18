#!/usr/bin/env python3
"""test_spu4_som_probe_client_parser.py — hardware-free test for
software/lib/spu4_som_probe_client.py: the pure encode/decode functions,
and ProbeTransport against a fake free-running serial port.

No hardware required. Run:
    python3 software/tests/test_spu4_som_probe_client_parser.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from software.lib.rational_som import RationalSurd
from software.lib.spu4_som_probe_client import (
    NUM_FEATURES,
    ProbeTransport,
    decode_result_line,
    encode_query,
)

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── encode_query ────────────────────────────────────────────────────────

# spu4_som_edge_full_chain_tb.v's "far from all nodes, mixed sign" query:
# f0=(-5,5) f1=(5,-5) f2=(-5,5) f3=(5,-5). Byte-for-byte expected line is
# the one traced by hand in the Track B design pass.
mixed_sign = [
    RationalSurd(-5, 5), RationalSurd(5, -5),
    RationalSurd(-5, 5), RationalSurd(5, -5),
]
check("encode_query: 'far from all nodes' query matches the hand-traced line",
      encode_query(mixed_sign) == b"QFFFB00050005FFFBFFFB00050005FFFB\n")

zeros = [RationalSurd(0, 0)] * NUM_FEATURES
check("encode_query: all-zero features",
      encode_query(zeros) == b"Q00000000000000000000000000000000\n")

max_pos = [RationalSurd(32767, 32767)] * NUM_FEATURES
check("encode_query: max positive value encodes as 7FFF",
      encode_query(max_pos) == b"Q" + b"7FFF" * 8 + b"\n")

min_neg = [RationalSurd(-32768, -32768)] * NUM_FEATURES
check("encode_query: most-negative value encodes as 8000 (two's complement)",
      encode_query(min_neg) == b"Q" + b"8000" * 8 + b"\n")

try:
    encode_query([RationalSurd(0, 0)] * 3)
    check("encode_query: wrong feature count raises ValueError", False)
except ValueError:
    check("encode_query: wrong feature count raises ValueError", True)


# ── decode_result_line: thin wrapper over the shared parser ────────────

decoded = decode_result_line("SOM:D N=1 Q=00001900 S=06 L=012 I=1120\r\n")
check("decode_result_line parses a valid line", decoded is not None)
check("decode_result_line: best_node", decoded.best_node == 1)
check("decode_result_line: best_quadrance", decoded.best_quadrance == 0x1900)
check("decode_result_line rejects malformed input",
      decode_result_line("garbage") is None)


# ── ProbeTransport against a fake free-running serial port ─────────────

class FakeSerial:
    def __init__(self, lines):
        self._lines = list(lines)
        self.reset_calls = 0
        self.written = []

    def reset_input_buffer(self):
        self.reset_calls += 1

    def readline(self):
        if not self._lines:
            return b""
        return self._lines.pop(0).encode("ascii")

    def write(self, data):
        self.written.append(bytes(data))


# Stray partial line dropped at construction, then a query round-trip:
# an idle line, then the done result.
fake = FakeSerial([
    "05 L=00",                                       # stray partial line
    "SOM:. N=0 Q=00000000 S=04 L=000 I=1120\r\n",     # idle, between queries
    "SOM:D N=1 Q=00001900 S=06 L=012 I=1120\r\n",     # the real answer
])
transport = ProbeTransport(fake)
check("ProbeTransport construction drops one stray line", fake.reset_calls == 1)

result = transport.classify(mixed_sign, timeout_s=0.5)
check("ProbeTransport.classify sent exactly one query", len(fake.written) == 1)
check("ProbeTransport.classify sent the correctly-encoded query",
      fake.written[0] == encode_query(mixed_sign))
check("ProbeTransport.classify skipped the idle line and returned the done result",
      result is not None and result.status_char == "D" and result.best_node == 1)

# Malformed-query response ('F') is also a terminal result, not skipped.
fake2 = FakeSerial(["", "SOM:F N=0 Q=00000000 S=00 L=000 I=1120\r\n"])
transport2 = ProbeTransport(fake2)
result2 = transport2.classify(mixed_sign, timeout_s=0.5)
check("ProbeTransport.classify returns an 'F' (malformed-query) terminal result",
      result2 is not None and result2.status_char == "F")

# Timeout: no terminal line ever arrives.
fake3 = FakeSerial(["", "SOM:. N=0 Q=00000000 S=04 L=000 I=1120\r\n"])
transport3 = ProbeTransport(fake3)
result3 = transport3.classify(mixed_sign, timeout_s=0.05)
check("ProbeTransport.classify returns None on timeout", result3 is None)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
