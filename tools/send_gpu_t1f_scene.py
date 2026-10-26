#!/usr/bin/env python3
"""Send the one frozen T1f four-primitive wire transaction exactly once."""

import argparse
import hashlib
import json
import os
import termios
import time
from pathlib import Path


EXPECTED_SHA256 = (
    "78820c1f6da055a3c51eb9ec3709fe027cd1b0a2772093c6e8618a5c300dbe5f"
)
EXPECTED_LENGTH = 127
EXPECTED_START = 0xA5


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument(
        "--fixture",
        default="fixtures/gpu_t1f_scene_wire_127b.hex",
    )
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    return parser.parse_args()


def configure(fd, baud):
    if baud != 115200:
        raise ValueError("T1f freezes 115200 baud")
    attrs = termios.tcgetattr(fd)
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR | termios.IGNCR |
                  termios.ICRNL | termios.IXON)
    attrs[1] &= ~termios.OPOST
    attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] |= termios.CS8 | termios.CLOCAL | termios.CREAD
    attrs[3] &= ~(termios.ECHONL | termios.ICANON | termios.ISIG | termios.IEXTEN)
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


def load_fixture(path):
    payload = bytes.fromhex(path.read_text())
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != EXPECTED_LENGTH:
        raise SystemExit(f"fixture length {len(payload)} != {EXPECTED_LENGTH}")
    if payload[0] != EXPECTED_START:
        raise SystemExit(f"fixture start 0x{payload[0]:02X} != 0x{EXPECTED_START:02X}")
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"fixture SHA-256 {digest} != frozen {EXPECTED_SHA256}")
    return payload, digest


def main():
    args = parse_args()
    fixture = Path(args.fixture)
    transcript = Path(args.transcript)
    payload, digest = load_fixture(fixture)

    fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    try:
        configure(fd, args.baud)
        started = time.time_ns()
        written = os.write(fd, payload)
        if written != len(payload):
            raise RuntimeError(f"short write: {written}/{len(payload)}")
        termios.tcdrain(fd)
        drained = time.time_ns()
    finally:
        os.close(fd)

    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(json.dumps({
        "format": "SPU_GPU_T1F_UART_TRANSMIT_V1",
        "port": args.port,
        "baud": args.baud,
        "framing": "8N1",
        "fixture": str(fixture),
        "length": len(payload),
        "sha256": digest,
        "written": written,
        "tcdrain_completed": True,
        "write_start_unix_ns": started,
        "drain_complete_unix_ns": drained,
    }, indent=2) + "\n")
    print(f"sent {written} bytes; tcdrain complete; transcript={transcript}")


if __name__ == "__main__":
    main()
