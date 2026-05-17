#!/usr/bin/env python3
"""Load the Tang Primer 25K RPLU probe and verify SPI/RPLU UART telemetry."""

import argparse
import os
import re
import select
import subprocess
import sys
import termios
import time
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BITSTREAM = ROOT / "build" / "tang_primer_25k_spu13_rplu_probe.fs"
DEFAULT_PORTS = [
    "/dev/serial/by-id/usb-SIPEED_USB_Debugger_2025030317-if01-port0",
    "/dev/ttyUSB1",
    "/dev/serial/by-id/usb-SIPEED_USB_Debugger_2025030317-if00-port0",
    "/dev/ttyUSB0",
]

JEDEC_RE = re.compile(r"B:([0-9A-Fa-f]{8}) A:([0-9A-Fa-f])")
RPLU_RE = re.compile(r"R:([0-9A-Fa-f]{8}) A:([0-9A-Fa-f])")


def parse_u32(text):
    return int(text, 0)


def resolve_port(port):
    if port != "auto":
        return port
    for candidate in DEFAULT_PORTS:
        if os.path.exists(candidate):
            return candidate
    raise SystemExit("No Sipeed FTDI UART port found")


def configure_tty(fd, baud):
    if baud != 115200:
        raise SystemExit("Only 115200 baud is currently supported")

    attrs = termios.tcgetattr(fd)
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR | termios.IGNCR |
                  termios.ICRNL | termios.IXON | termios.IXOFF)
    attrs[1] &= ~termios.OPOST
    attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
    if hasattr(termios, "CRTSCTS"):
        attrs[2] &= ~termios.CRTSCTS
    attrs[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                  termios.ISIG | termios.IEXTEN)
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)


def load_bitstream(bitstream):
    if not bitstream.exists():
        raise SystemExit(f"Missing bitstream: {bitstream}")
    cmd = ["openFPGALoader", "-b", "tangprimer25k", str(bitstream)]
    subprocess.run(cmd, cwd=ROOT, check=True)


def capture_uart(port, seconds, baud, verbose, stop_when=None):
    fd = os.open(port, os.O_RDONLY | os.O_NONBLOCK)
    try:
        configure_tty(fd, baud)
        return capture_uart_fd(fd, seconds, verbose, stop_when)
    finally:
        os.close(fd)


def capture_uart_fd(fd, seconds, verbose, stop_when=None):
    deadline = time.monotonic() + seconds
    chunks = []
    text_so_far = ""
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.25)
        if not ready:
            continue
        data = os.read(fd, 4096)
        if not data:
            continue
        text = data.decode("ascii", errors="ignore")
        chunks.append(text)
        if verbose:
            sys.stdout.write(text)
            sys.stdout.flush()
        text_so_far = "".join(chunks)
        if stop_when is not None and stop_when(text_so_far):
            return text_so_far
    return text_so_far


def decode_rplu(value):
    return {
        "marker": (value >> 23) & 0x1FF,
        "mask": (value >> 10) & 0x1FFF,
        "addr": value & 0x3FF,
    }


def load_expected_checksum(value):
    if value != "auto":
        return parse_u32(value)

    summary = ROOT / "build" / "rplu_metrics" / "rplu_metric_summary.json"
    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8"))
        checksum = data.get("flash", {}).get("rtl_checksum")
        if checksum:
            return int(checksum, 16)

    payload = ROOT / "build" / "rplu_boot_chords.bin"
    if payload.exists():
        data = payload.read_bytes()
        if len(data) % 16 != 0:
            raise SystemExit(f"{payload} length is not a multiple of 16 bytes")
        total = 0
        for offset in range(0, len(data), 16):
            header = int.from_bytes(data[offset:offset + 8], "big")
            chord_data = int.from_bytes(data[offset + 8:offset + 16], "big")
            total = (
                total
                + ((header >> 32) & 0xFFFFFFFF)
                + (header & 0xFFFFFFFF)
                + ((chord_data >> 32) & 0xFFFFFFFF)
                + (chord_data & 0xFFFFFFFF)
            ) & 0xFFFFFFFF
        return total

    return None


def find_capture_matches(
    text,
    expected_jedec,
    expected_marker,
    expected_mask,
    expected_addr,
    expected_loaded,
    expected_checksum,
):
    jedec_match = None
    for match in JEDEC_RE.finditer(text):
        value = int(match.group(1), 16)
        if (value & 0x00FFFFFF) == expected_jedec:
            jedec_match = match.group(0)
            break

    rplu_match = None
    rplu_decoded = None
    loaded_match = None
    checksum_match = None
    for match in RPLU_RE.finditer(text):
        value = int(match.group(1), 16)
        axis = int(match.group(2), 16)
        if axis == 0xE and expected_loaded is not None and (value & 0xFFFF) == expected_loaded:
            loaded_match = match.group(0)
            continue
        if axis == 0xF and expected_checksum is not None and value == expected_checksum:
            checksum_match = match.group(0)
            continue
        if axis != 0xD:
            continue
        decoded = decode_rplu(value)
        if (decoded["marker"] == expected_marker and
                decoded["mask"] == expected_mask and
                decoded["addr"] == expected_addr):
            rplu_match = match.group(0)
            rplu_decoded = decoded

    loaded_ok = expected_loaded is None or loaded_match is not None
    checksum_ok = expected_checksum is None or checksum_match is not None

    return {
        "jedec_match": jedec_match,
        "rplu_match": rplu_match,
        "rplu_decoded": rplu_decoded,
        "loaded_match": loaded_match,
        "checksum_match": checksum_match,
        "loaded_ok": loaded_ok,
        "checksum_ok": checksum_ok,
    }


def capture_matches_ok(matches):
    return (
        matches["jedec_match"] is not None and
        matches["rplu_match"] is not None and
        matches["loaded_ok"] and
        matches["checksum_ok"]
    )


def capture_satisfies(
    text,
    expected_jedec,
    expected_marker,
    expected_mask,
    expected_addr,
    expected_loaded,
    expected_checksum,
):
    return capture_matches_ok(find_capture_matches(
        text,
        expected_jedec,
        expected_marker,
        expected_mask,
        expected_addr,
        expected_loaded,
        expected_checksum,
    ))


def check_capture(
    text,
    expected_jedec,
    expected_marker,
    expected_mask,
    expected_addr,
    expected_loaded,
    expected_checksum,
):
    matches = find_capture_matches(
        text,
        expected_jedec,
        expected_marker,
        expected_mask,
        expected_addr,
        expected_loaded,
        expected_checksum,
    )

    if capture_matches_ok(matches):
        rplu_decoded = matches["rplu_decoded"]
        print(f"SPI JEDEC: {matches['jedec_match']}")
        print(
            "RPLU: "
            f"{matches['rplu_match']} "
            f"marker=0x{rplu_decoded['marker']:03X} "
            f"mask=0x{rplu_decoded['mask']:04X} "
            f"addr=0x{rplu_decoded['addr']:03X}"
        )
        if matches["loaded_match"]:
            print(f"RPLU loaded: {matches['loaded_match']} count={expected_loaded}")
        if matches["checksum_match"]:
            print(f"RPLU checksum: {matches['checksum_match']} checksum=0x{expected_checksum:08X}")
        print("RPLU hardware probe PASS")
        return 0

    print("RPLU hardware probe FAIL")
    if not matches["jedec_match"]:
        print(f"Missing JEDEC marker for 0x{expected_jedec:06X}")
    if not matches["rplu_match"]:
        print(
            "Missing RPLU marker "
            f"marker=0x{expected_marker:03X} "
            f"mask=0x{expected_mask:04X} "
            f"addr=0x{expected_addr:03X}"
        )
    if not matches["loaded_ok"]:
        print(f"Missing RPLU loaded count {expected_loaded}")
    if not matches["checksum_ok"]:
        print(f"Missing RPLU checksum 0x{expected_checksum:08X}")
    lines = [line for line in text.splitlines() if line.strip()]
    if lines:
        print("Last telemetry lines:")
        for line in lines[-40:]:
            print(line)
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bitstream", type=Path, default=DEFAULT_BITSTREAM)
    parser.add_argument("--port", default="auto")
    parser.add_argument("--seconds", type=float, default=45.0)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--no-load", action="store_true")
    parser.add_argument("--settle", type=float, default=0.25)
    parser.add_argument("--expected-jedec", type=parse_u32, default=0xEF4018)
    parser.add_argument("--expected-rplu-marker", type=parse_u32, default=0x1A5)
    parser.add_argument("--expected-rplu-mask", type=parse_u32, default=0x0000)
    parser.add_argument("--expected-rplu-addr", type=parse_u32, default=0x3FF)
    parser.add_argument("--expected-rplu-loaded", type=parse_u32, default=2051)
    parser.add_argument("--expected-rplu-checksum", default="auto")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    port = resolve_port(args.port)
    expected_checksum = load_expected_checksum(args.expected_rplu_checksum)
    stop_when = lambda text: capture_satisfies(
        text,
        args.expected_jedec,
        args.expected_rplu_marker,
        args.expected_rplu_mask,
        args.expected_rplu_addr,
        args.expected_rplu_loaded,
        expected_checksum,
    )
    if not args.no_load:
        load_bitstream(args.bitstream)
        time.sleep(args.settle)
        text = capture_uart(port, args.seconds, args.baud, args.verbose, stop_when)
    else:
        text = capture_uart(port, args.seconds, args.baud, args.verbose, stop_when)
    return check_capture(
        text,
        args.expected_jedec,
        args.expected_rplu_marker,
        args.expected_rplu_mask,
        args.expected_rplu_addr,
        args.expected_rplu_loaded,
        expected_checksum,
    )


if __name__ == "__main__":
    raise SystemExit(main())
