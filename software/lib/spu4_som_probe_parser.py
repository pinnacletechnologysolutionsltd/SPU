"""spu4_som_probe_parser.py — pure parser for the SPU-4 SOM edge probes'
UART result line.

Shared line grammar between the fixed self-test probe
(hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_probe.v,
header comment + `msg_byte()`, lines 34-48/190-240) and the interactive
probe (hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v):

    SOM:<ch> N=<h> Q=<hhhhhhhh> S=<hh> L=<hhh> I=<hhhh>\r\n

<ch> is a single status character (fixed probe: '.' running, 'P' pass,
'F' fail; interactive probe: '.' idle, 'D' done, 'F' malformed query) —
parsed generically rather than restricted to one probe's alphabet, so this
module serves both.

No pyserial dependency: this only turns a decoded text line into a
dataclass, so it is importable and testable without a serial port.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_LINE_RE = re.compile(
    r"^SOM:(?P<ch>\S)\s+"
    r"N=(?P<n>[0-9A-Fa-f])\s+"
    r"Q=(?P<q>[0-9A-Fa-f]{8})\s+"
    r"S=(?P<s>[0-9A-Fa-f]{2})\s+"
    r"L=(?P<l>[0-9A-Fa-f]{3})\s+"
    r"I=(?P<i>[0-9A-Fa-f]{4})$"
)

# status[7:0]: {0000, start_ignored, hydrated, done, busy} — spu4_som_edge_wrapper.v
_STATUS_BUSY = 0x01
_STATUS_DONE = 0x02
_STATUS_HYDRATED = 0x04
_STATUS_START_IGNORED = 0x08


@dataclass(frozen=True)
class SomProbeLine:
    status_char: str
    best_node: int
    best_quadrance: int
    status: int
    latency: int
    id: int

    @property
    def busy(self) -> bool:
        return bool(self.status & _STATUS_BUSY)

    @property
    def done(self) -> bool:
        return bool(self.status & _STATUS_DONE)

    @property
    def hydrated(self) -> bool:
        return bool(self.status & _STATUS_HYDRATED)

    @property
    def start_ignored(self) -> bool:
        return bool(self.status & _STATUS_START_IGNORED)


def parse_line(line: str) -> SomProbeLine | None:
    """Parse one `SOM:...` result line. Returns None if malformed/unrelated
    (e.g. blank lines, boot-banner noise, a partial line from a buffer that
    was already mid-stream when the host attached)."""

    if not line:
        return None
    m = _LINE_RE.match(line.strip())
    if not m:
        return None
    return SomProbeLine(
        status_char=m.group("ch"),
        best_node=int(m.group("n"), 16),
        best_quadrance=int(m.group("q"), 16),
        status=int(m.group("s"), 16),
        latency=int(m.group("l"), 16),
        id=int(m.group("i"), 16),
    )
