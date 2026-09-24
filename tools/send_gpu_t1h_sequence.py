#!/usr/bin/env python3
"""Send the frozen T1h A/B/C/A sequence with conservative UART pacing."""

import argparse
import hashlib
import json
import os
import termios
import time
from pathlib import Path


FIXTURES = {
    "A": ("fixtures/gpu_t1h_scene_a_wire_151b.hex",
          "656e4583753bd86d37b9fe0480cf6fa493e4f475232fb89271ae4bf5559ad3e3"),
    "B": ("fixtures/gpu_t1h_scene_b_wire_151b.hex",
          "3858256dd7999634cf997afdf40318c16bf4d87a731b340148b31d1c49aed70a"),
    "C": ("fixtures/gpu_t1h_scene_c_wire_151b.hex",
          "f9415dcf3143604e25fa4591e49646d9cb446e28e81f87a1f3d771869cfb27d9"),
}
MIN_POST_DRAIN_SECONDS = 0.020


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


def load_scene(name):
    fixture_name, expected_sha256 = FIXTURES[name]
    wire = bytes.fromhex(Path(fixture_name).read_text())
    digest = hashlib.sha256(wire).hexdigest()
    if len(wire) != 151 or wire[0] != 0xA5:
        raise SystemExit(f"Scene {name}: expected 151 bytes beginning with A5")
    if digest != expected_sha256:
        raise SystemExit(f"Scene {name}: SHA-256 {digest} != frozen {expected_sha256}")
    return fixture_name, wire, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--dwell-seconds", type=float, default=3.0)
    parser.add_argument("--sequence", default="A,B,C,A")
    args = parser.parse_args()
    sequence = args.sequence.split(",")
    if not sequence or any(name not in FIXTURES for name in sequence):
        raise SystemExit("sequence must contain only comma-separated A, B, and C")
    if args.dwell_seconds < MIN_POST_DRAIN_SECONDS:
        raise SystemExit("dwell must be at least the frozen 20 ms post-drain wait")

    loaded = {name: load_scene(name) for name in set(sequence)}
    fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    records = []
    try:
        configure(fd)
        for index, name in enumerate(sequence):
            fixture_name, wire, digest = loaded[name]
            started_ns = time.time_ns()
            written = os.write(fd, wire)
            if written != len(wire):
                raise RuntimeError(f"Scene {name}: short write {written}/{len(wire)}")
            termios.tcdrain(fd)
            drained_ns = time.time_ns()
            record = {
                "index": index,
                "scene": name,
                "fixture": fixture_name,
                "length": len(wire),
                "sha256": digest,
                "written": written,
                "tcdrain_completed": True,
                "write_start_unix_ns": started_ns,
                "drain_complete_unix_ns": drained_ns,
            }
            records.append(record)
            print(f"sent scene {name}: 151 bytes; tcdrain complete", flush=True)
            if index + 1 < len(sequence):
                time.sleep(args.dwell_seconds)
    finally:
        os.close(fd)

    for current, following in zip(records, records[1:]):
        current["next_scene_start_gap_ms"] = (
            following["write_start_unix_ns"] - current["write_start_unix_ns"]
        ) / 1_000_000
    transcript = Path(args.transcript)
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(json.dumps({
        "format": "SPU_GPU_T1H_UART_SEQUENCE_V1",
        "port": args.port,
        "baud": 115200,
        "framing": "8N1",
        "post_drain_minimum_ms": MIN_POST_DRAIN_SECONDS * 1000,
        "dwell_seconds": args.dwell_seconds,
        "sequence": sequence,
        "transmissions": records,
    }, indent=2) + "\n")
    print(f"sequence complete; transcript={transcript}")


if __name__ == "__main__":
    main()
