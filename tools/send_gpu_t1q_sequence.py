#!/usr/bin/env python3
"""Preflight or send the frozen T1q A/B/C/return-A UART sequence."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import termios
import time


FIXTURE = Path("fixtures/gpu_t1i_scene_a_wire_175b.hex")
FIXTURE_SHA256 = "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"
BITSTREAM = Path("build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit")
BITSTREAM_SHA256 = "c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d"
SELECTORS = bytes((0xCC, 0xCC, 0xCC, 0xCC))
SCENES = (
    ("A", bytes((0x00, 0x00, 0x00, 0x00))),
    ("B", bytes((0x0F, 0x0F, 0x0F, 0x0F))),
    ("C", bytes((0x06, 0x06, 0x06, 0x06))),
    ("return_A", bytes((0x00, 0x00, 0x00, 0x00))),
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def packets():
    source = bytes.fromhex(FIXTURE.read_text())
    if len(source) != 175 or source[0] != 0xA5 or sha256(source) != FIXTURE_SHA256:
        raise ValueError("frozen T1i fixture framing, length, or hash changed")
    if sha256(BITSTREAM.read_bytes()) != BITSTREAM_SHA256:
        raise ValueError("frozen T1q bitstream hash changed")
    result = []
    for name, tables in SCENES:
        packet = source + tables + SELECTORS
        if len(packet) != 183 or packet[175:179] != tables or packet[179:183] != SELECTORS:
            raise ValueError(f"invalid T1q packet layout for {name}")
        if any(table & 0xF0 for table in packet[175:179]):
            raise ValueError(f"nonzero truth-table high nibble in {name}")
        result.append((name, tables, packet))
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


def save_transcript(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


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
        for name, tables, packet in sequence:
            print(f"{name}: {len(packet)} bytes; tables={tables.hex().upper()}; "
                  f"selectors={SELECTORS.hex().upper()}; sha256={sha256(packet)}")
        print("PASS: frozen T1q 183-byte A/B/C/return-A packet preflight")
        return 0

    transcript = {"format": "SPU_GPU_T1Q_UART_SEQUENCE_V1", "port": args.port,
                  "baud": 115200, "framing": "8N1", "source_fixture": str(FIXTURE),
                  "source_wire_sha256": FIXTURE_SHA256,
                  "bitstream_sha256": BITSTREAM_SHA256,
                  "post_drain_wait_ms": args.dwell_seconds * 1000,
                  "status": "failed", "transmissions": []}
    fd = None
    try:
        fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
        configure(fd)
        for index, (name, tables, packet) in enumerate(sequence):
            started_ns = time.monotonic_ns()
            written = os.write(fd, packet)
            record = {"scene": name, "tables": tables.hex().upper(),
                      "selectors": SELECTORS.hex().upper(), "wire_bytes": len(packet),
                      "wire_sha256": sha256(packet), "bytes_written": written,
                      "tcdrain_completed": False,
                      "write_start_monotonic_ns": started_ns}
            transcript["transmissions"].append(record)
            if written != len(packet):
                raise RuntimeError(f"{name}: short write {written}/{len(packet)}")
            termios.tcdrain(fd)
            record["drain_complete_monotonic_ns"] = time.monotonic_ns()
            record["tcdrain_completed"] = True
            print(f"sent {name}: {written} bytes; tcdrain complete", flush=True)
            if index + 1 < len(sequence):
                time.sleep(args.dwell_seconds)
        transcript["status"] = "complete"
        return 0
    except Exception as error:
        transcript["error"] = f"{type(error).__name__}: {error}"
        print(transcript["error"])
        return 1
    finally:
        if fd is not None:
            os.close(fd)
        if args.transcript is not None:
            save_transcript(args.transcript, transcript)


if __name__ == "__main__":
    raise SystemExit(main())
