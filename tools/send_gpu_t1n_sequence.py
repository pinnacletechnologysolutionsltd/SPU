#!/usr/bin/env python3
"""Send the frozen T1n runtime-material A/B/C/A sequence over UART."""

import argparse
import hashlib
import json
import os
import termios
import time
from pathlib import Path


SCENES = {
    "A": ("fixtures/gpu_t1i_scene_a_wire_175b.hex", 0x00,
          "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"),
    "B": ("fixtures/gpu_t1i_scene_b_wire_175b.hex", 0x01,
          "f71ec97d18c37cdae7067accbc3b0100bad3689d4fcbc856f55efc11207525d1"),
    "C": ("fixtures/gpu_t1i_scene_c_wire_175b.hex", 0x02,
          "604fea47bee07549e28212b87bb5da18dbe6b72d32412ed57bddb6decb8cb89d"),
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


def load_packet(name, material_op=None):
    fixture, default_op, expected_sha256 = SCENES[name]
    if material_op is None:
        material_op = default_op
    source_wire = bytes.fromhex(Path(fixture).read_text())
    source_sha256 = hashlib.sha256(source_wire).hexdigest()
    if len(source_wire) != 175 or source_wire[0] != 0xA5:
        raise SystemExit(f"Scene {name}: expected 175 bytes beginning with A5")
    if source_sha256 != expected_sha256:
        raise SystemExit(
            f"Scene {name}: SHA-256 {source_sha256} != frozen {expected_sha256}")
    packet = source_wire + bytes((material_op,))
    return fixture, material_op, source_sha256, packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--dwell-seconds", type=float, default=3.0)
    parser.add_argument("--sequence", default="A,B,C,A")
    parser.add_argument("--opcodes",
                        help="comma-separated 0..5 overrides, one per scene")
    args = parser.parse_args()
    sequence = args.sequence.split(",")
    if not sequence or any(name not in SCENES for name in sequence):
        raise SystemExit("sequence must contain only comma-separated A, B, and C")
    if args.opcodes:
        try:
            opcodes = [int(value, 0) for value in args.opcodes.split(",")]
        except ValueError as exc:
            raise SystemExit(f"invalid opcode list: {exc}") from exc
        if len(opcodes) != len(sequence) or any(op < 0 or op > 5 for op in opcodes):
            raise SystemExit("opcodes must provide one value from 0 through 5 per scene")
    else:
        opcodes = [SCENES[name][1] for name in sequence]
    if args.dwell_seconds < MIN_POST_DRAIN_SECONDS:
        raise SystemExit("dwell must be at least the frozen 20 ms post-drain wait")
    if args.transcript.exists():
        raise SystemExit(f"refusing to overwrite transcript: {args.transcript}")

    fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    records = []
    try:
        configure(fd)
        for index, (name, material_op) in enumerate(zip(sequence, opcodes)):
            fixture, material_op, source_sha256, packet = load_packet(name, material_op)
            started_ns = time.time_ns()
            written = os.write(fd, packet)
            if written != len(packet):
                raise RuntimeError(f"Scene {name}: short write {written}/{len(packet)}")
            termios.tcdrain(fd)
            drained_ns = time.time_ns()
            records.append({
                "index": index, "scene": name, "material_op": material_op,
                "source_fixture": fixture,
                "source_t1i_wire_sha256": source_sha256,
                "wire_bytes": len(packet),
                "wire_sha256": hashlib.sha256(packet).hexdigest(),
                "bytes_written": written, "tcdrain_completed": True,
                "write_start_unix_ns": started_ns,
                "drain_complete_unix_ns": drained_ns,
            })
            print(f"sent scene {name}: {len(packet)} bytes; opcode={material_op}; tcdrain complete",
                  flush=True)
            if index + 1 < len(sequence):
                time.sleep(args.dwell_seconds)
    finally:
        os.close(fd)

    for current, following in zip(records, records[1:]):
        current["next_scene_start_gap_ms"] = (
            following["write_start_unix_ns"] - current["write_start_unix_ns"]
        ) / 1_000_000
    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    args.transcript.write_text(json.dumps({
        "format": "SPU_GPU_T1N_UART_SEQUENCE_V1", "port": args.port,
        "baud": 115200, "framing": "8N1",
        "post_drain_wait_ms": args.dwell_seconds * 1000,
        "sequence": sequence, "opcodes": opcodes, "transmissions": records,
    }, indent=2) + "\n")
    print(f"sequence complete; transcript={args.transcript}")


if __name__ == "__main__":
    main()
