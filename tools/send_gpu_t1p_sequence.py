#!/usr/bin/env python3
"""Check or send the frozen T1p fixed-geometry predicate sequence."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import termios
import time


FIXTURE = Path("fixtures/gpu_t1i_scene_a_wire_175b.hex")
FIXTURE_SHA256 = "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"
BITSTREAM = Path("build/spu_a7_100t_GPUVGA_T1P_PER_PRIMITIVE_PREDICATES_Q1.bit")
BITSTREAM_SHA256 = "fe351b04a9f2d2e8b00fe49b9f84c20231f2d905d9c6dcc746c0b7f0347798e9"
OPS = bytes((2, 2, 2, 2))
SEQUENCE = (
    ("A", bytes((0xCC, 0xCC, 0xCC, 0xCC))),
    ("B", bytes((0x89, 0x8E, 0xAA, 0xD9))),
    ("C", bytes((0xBD, 0xD8, 0x8E, 0xF8))),
    ("return_A", bytes((0xCC, 0xCC, 0xCC, 0xCC))),
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def packets():
    source = bytes.fromhex(FIXTURE.read_text())
    if len(source) != 175 or source[0] != 0xA5 or sha256(source) != FIXTURE_SHA256:
        raise ValueError("frozen Scene A fixture framing, length, or hash changed")
    if sha256(BITSTREAM.read_bytes()) != BITSTREAM_SHA256:
        raise ValueError("T1p bitstream hash changed")
    result = []
    for name, selectors in SEQUENCE:
        packet = source + OPS + selectors
        if len(packet) != 183 or packet[175:179] != OPS or packet[179:183] != selectors:
            raise ValueError(f"invalid T1p packet layout for {name}")
        result.append((name, selectors, packet))
    if result[0][2] != result[-1][2]:
        raise ValueError("return-A packet differs from initial A")
    return result


def configure(fd):
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


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--send", action="store_true")
    parser.add_argument("--port")
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--dwell-seconds", type=int, default=5)
    args = parser.parse_args()
    if args.send and (not args.port or not args.transcript):
        parser.error("--send requires --port and --transcript")
    if args.dwell_seconds < 1:
        parser.error("dwell must be at least one second")
    if args.transcript and args.transcript.exists():
        parser.error(f"refusing to overwrite transcript: {args.transcript}")
    sequence = packets()
    if args.dry_run:
        for name, selectors, packet in sequence:
            print(f"{name}: {len(packet)} bytes; selectors={selectors.hex().upper()}; "
                  f"sha256={sha256(packet)}")
        print("PASS: frozen T1p 183-byte A/B/C/return-A packet preflight")
        return
    records = []
    fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    try:
        configure(fd)
        for index, (name, selectors, packet) in enumerate(sequence):
            started_ns = time.time_ns()
            written = os.write(fd, packet)
            if written != len(packet):
                raise RuntimeError(f"{name}: short write {written}/{len(packet)}")
            termios.tcdrain(fd)
            drained_ns = time.time_ns()
            records.append({"scene": name, "selectors": selectors.hex().upper(),
                            "material_ops": list(OPS), "wire_bytes": len(packet),
                            "wire_sha256": sha256(packet), "bytes_written": written,
                            "tcdrain_completed": True, "write_start_unix_ns": started_ns,
                            "drain_complete_unix_ns": drained_ns})
            print(f"sent {name}: {len(packet)} bytes; tcdrain complete", flush=True)
            if index + 1 < len(sequence):
                time.sleep(args.dwell_seconds)
    finally:
        os.close(fd)
    for current, following in zip(records, records[1:]):
        current["next_packet_start_gap_ms"] = (
            following["write_start_unix_ns"] - current["write_start_unix_ns"]) / 1_000_000
    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    with args.transcript.open("x") as stream:
        json.dump({"format": "SPU_GPU_T1P_UART_SEQUENCE_V1", "port": args.port,
                   "baud": 115200, "framing": "8N1", "source_fixture": str(FIXTURE),
                   "source_t1i_wire_sha256": FIXTURE_SHA256,
                   "bitstream_sha256": BITSTREAM_SHA256,
                   "post_drain_wait_ms": args.dwell_seconds * 1000,
                   "transmissions": records}, stream, indent=2)
        stream.write("\n")
    print(f"sequence complete; transcript={args.transcript}")


if __name__ == "__main__":
    main()
