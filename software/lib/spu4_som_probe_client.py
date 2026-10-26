"""spu4_som_probe_client.py — host-side client for the SPU-4 SOM edge
interactive bench probe
(hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v).

Pure encode/decode functions have zero pyserial dependency, so they're
testable and reusable without a serial port. `ProbeTransport` is the thin
serial-I/O layer, shaped after tools/bench_metrics/power_log.py's
free-running-UART-reader pattern (open, reset input buffer, drop a
possibly-stray partial line, read-loop tolerant of malformed/blank lines)
adapted for a probe that is now also host-triggerable.
"""
from __future__ import annotations

import time
from typing import Optional, Sequence

from .rational_som import RationalSurd
from .spu4_som_probe_parser import SomProbeLine, parse_line

NUM_FEATURES = 4


def _h16(v: int) -> str:
    """Two's-complement 16-bit value as 4 uppercase hex digits."""
    return f"{v & 0xFFFF:04X}"


def encode_query(features: Sequence[RationalSurd]) -> bytes:
    """Encode a 4-feature vector as the interactive probe's query line:
    'Q' + 8 fields of 4 hex digits + '\\n'. Field order matches
    spu4_som_edge_full_chain_tb.v's `pack4` argument order:
    f0P f0Q f1P f1Q f2P f2Q f3P f3Q (feature 0 first)."""

    if len(features) != NUM_FEATURES:
        raise ValueError(f"expected {NUM_FEATURES} features, got {len(features)}")
    fields = []
    for f in features:
        fields.append(_h16(f.p))
        fields.append(_h16(f.q))
    return ("Q" + "".join(fields) + "\n").encode("ascii")


def decode_result_line(line: str) -> Optional[SomProbeLine]:
    """Decode a probe result line. Thin wrapper over
    spu4_som_probe_parser.parse_line -- the interactive and fixed probes
    share the same result-line grammar, see that module's docstring."""

    return parse_line(line)


class ProbeTransport:
    """Serial transport for the interactive probe: send a query, read the
    matching result line. Free-running-tolerant (a stray partial/idle
    line from before this script attached is skipped rather than
    mis-parsed as the answer) -- same discipline as
    tools/bench_metrics/power_log.py's read loop."""

    def __init__(self, ser):
        self._ser = ser
        self._ser.reset_input_buffer()
        self._ser.readline()  # drop a possibly-stray partial line

    def send_query(self, features: Sequence[RationalSurd]) -> None:
        self._ser.write(encode_query(features))

    def read_result(self, timeout_s: float = 5.0) -> Optional[SomProbeLine]:
        """Read lines until a terminal ('D' done or 'F' malformed-query)
        result arrives, or timeout. Idle ('.') / hydration ('H') lines
        are skipped."""

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            raw = self._ser.readline().decode("ascii", "replace")
            parsed = decode_result_line(raw)
            if parsed is None:
                continue
            if parsed.status_char in ("D", "F"):
                return parsed
        return None

    def classify(
        self, features: Sequence[RationalSurd], timeout_s: float = 5.0
    ) -> Optional[SomProbeLine]:
        self.send_query(features)
        return self.read_result(timeout_s=timeout_s)
