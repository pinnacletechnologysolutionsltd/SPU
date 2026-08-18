#!/usr/bin/env python3
"""spu4_som_edge_smoketest.py — bench smoke test for the SPU-4 SOM edge
classifier's fixed self-test probe (already silicon-proven,
docs/hardware_evidence.md §3.2j.7).

The probe (hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_probe.v)
drives one hard-coded feature vector through the real
spu4_som_edge_wrapper.v once, then repeats a UART result line forever. This
script reads that line and checks it against the known-correct answer for
that fixture, so a bench session can confirm "the classifier still works on
real silicon" with one command instead of eyeballing a terminal.

This is a smoke test against a FIXED query, not a general classification
demo — it can only ever report the same PASS/FAIL for the one query baked
into the probe. For submitting arbitrary feature vectors, see the
interactive probe and tools/spu4_som_edge_demo.py (Phase B1).

Wiring: the probe's `uart_tx` is the Tang Primer 25K dock's own host-bound
USB-CDC UART (pin C3, "Host-bound TX" in tang_primer_25k.cst) — no RP2350
southbridge involved. Board must be flashed with the SOM edge probe
bitstream, and the PMOD J4 SPI flash must carry the oracle_fixture boot
image first — see build_25k_spu4_som_edge_probe.sh's header for the exact
commands.

Usage:
    python3 tools/spu4_som_edge_smoketest.py --port /dev/ttyACM0
"""

import argparse
import os
import sys
import time
import types

try:
    import serial
except ImportError:
    # Deferred, same rationale as tools/robotics_demo.py: pyserial is a real
    # runtime dependency for talking to hardware, but the parsing/checking
    # logic below has no need for it and should stay importable without it.
    serial = types.ModuleType("serial")
    serial.Serial = None

sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])
from software.lib.spu4_som_probe_parser import parse_line

# The fixed probe's known-correct answer for its one baked-in query (the
# oracle_fixture's "far from all nodes, mixed sign" vector) — see the
# probe's own header comment and build_25k_spu4_som_edge_probe.sh.
EXPECTED_NODE = 1
EXPECTED_QUADRANCE = 0x1900
EXPECTED_ID = 0x1020

READ_TIMEOUT_S = 5.0


def read_terminal_line(ser, timeout_s=READ_TIMEOUT_S):
    """Read lines until a PASS/FAIL (terminal) result line arrives, or
    timeout. The probe free-runs, so the OS buffer may hold a stray
    partial line from before this script attached -- drop it first, same
    rationale as tools/bench_metrics/power_log.py's ser.readline() drop."""

    ser.reset_input_buffer()
    ser.readline()

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        raw = ser.readline().decode("ascii", "replace")
        parsed = parse_line(raw)
        if parsed is None:
            continue
        if parsed.status_char in ("P", "F"):
            return parsed
    return None


def check_result(result):
    """Returns (ok, reasons) -- reasons lists every mismatch, not just the
    first, so a bad run reports everything wrong in one shot."""

    if result is None:
        return False, ["no terminal (P/F) result line arrived before timeout"]

    reasons = []
    if result.status_char != "P":
        reasons.append(f"probe itself reported FAIL (status_char={result.status_char!r})")
    if result.best_node != EXPECTED_NODE:
        reasons.append(f"best_node: expected {EXPECTED_NODE}, got {result.best_node}")
    if result.best_quadrance != EXPECTED_QUADRANCE:
        reasons.append(
            f"best_quadrance: expected 0x{EXPECTED_QUADRANCE:X}, "
            f"got 0x{result.best_quadrance:X}"
        )
    if result.id != EXPECTED_ID:
        reasons.append(f"id: expected 0x{EXPECTED_ID:04X}, got 0x{result.id:04X}")
    if not result.hydrated:
        reasons.append("status: hydrated bit not set")
    if not result.done:
        reasons.append("status: done bit not set")
    if result.busy:
        reasons.append("status: busy bit unexpectedly set")
    if result.start_ignored:
        reasons.append("status: start_ignored bit unexpectedly set (handshake misuse)")
    return not reasons, reasons


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True, help="e.g. /dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=READ_TIMEOUT_S)
    ns = ap.parse_args(argv)

    if serial.Serial is None:
        print("ERROR: pyserial is not installed (pip install pyserial).", file=sys.stderr)
        return 1

    print("SPU-4 SOM edge classifier -- fixed-probe smoke test")
    print("(demo/synthetic weights until the INA226 capture campaign lands "
          "real ones -- see docs, this is not a validated anomaly result)")
    print("=" * 72)

    ser = serial.Serial(ns.port, ns.baud, timeout=1)
    try:
        result = read_terminal_line(ser, timeout_s=ns.timeout)
    finally:
        ser.close()

    ok, reasons = check_result(result)
    if result is not None:
        print(f"  received: SOM:{result.status_char} N={result.best_node:X} "
              f"Q={result.best_quadrance:08X} S={result.status:02X} "
              f"L={result.latency:03X} I={result.id:04X}")
    print("=" * 72)

    if ok:
        print("PASS: real silicon classified the fixed fixture correctly.")
        return 0

    print("FAIL:")
    for reason in reasons:
        print(f"  - {reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
