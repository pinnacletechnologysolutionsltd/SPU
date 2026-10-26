#!/usr/bin/env python3
"""Oracle-check or send one frozen 4x-scaled T1q visibility sequence."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import termios
import time


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/gpu_t1i_scene_a_wire_175b.hex"
FIXTURE_SHA256 = "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"
BITSTREAM = ROOT / "build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit"
BITSTREAM_SHA256 = "c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d"
WIRE_SHA256 = "1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df"
TABLES = (bytes((0, 0, 0, 0)), bytes((15, 15, 15, 15)),
          bytes((6, 6, 6, 6)), bytes((0, 0, 0, 0)))
NAMES = ("A", "B", "C", "return_A")
SELECTORS = bytes((0xCC, 0xCC, 0xCC, 0xCC))
EXPECTED_PACKETS = (
    "3ef25319403e9d8a9f8f5dd3702377f96071a7b1a695833fe503dca45d66f44b",
    "009fe91ee376144fd6a64b143e84bd80a1ec317d5a9c622ff70906a05f882eb8",
    "69344794090086683633521df30e63f86423c4be60d15a9e05f6cbd6e591fad2",
    "3ef25319403e9d8a9f8f5dd3702377f96071a7b1a695833fe503dca45d66f44b",
)
EXPECTED_LANES = [11964, 11723, 7635, 7239]
EXPECTED_CHANGES = [38561, 11389, 27172]
sys.path.insert(0, str(ROOT / "software/tests"))
from test_gpu_t1i_uv import decode, oracle  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def scaled_wire():
    source = bytes.fromhex(FIXTURE.read_text())
    if len(source) != 175 or source[0] != 0xA5 or sha256(source) != FIXTURE_SHA256:
        raise ValueError("frozen geometry fixture framing, length, or hash changed")
    if sha256(BITSTREAM.read_bytes()) != BITSTREAM_SHA256:
        raise ValueError("frozen T1q bitstream hash changed")
    scene = int.from_bytes(source[1:], "little")
    for lane in range(4):
        for edge in range(3):
            bit = lane * 348 + edge * 64 + 32
            raw = (scene >> bit) & 0xFFFFFFFF
            signed = raw if raw < (1 << 31) else raw - (1 << 32)
            scaled = signed * 4
            if not -(1 << 31) <= scaled < (1 << 31):
                raise ValueError("scaled edge constant overflows signed 32-bit")
            scene = (scene & ~(0xFFFFFFFF << bit)) | ((scaled & 0xFFFFFFFF) << bit)
    wire = b"\xA5" + scene.to_bytes(174, "little")
    if len(wire) != 175 or sha256(wire) != WIRE_SHA256:
        raise ValueError("scaled geometry wire hash changed")
    return wire


def make_packets(wire):
    lanes = decode(int.from_bytes(wire[1:], "little"))
    counts, changed = [0] * 4, [0] * 3
    bounds = [640, -1, 480, -1]
    for y in range(480):
        for x in range(640):
            valid, lane, u, v = oracle(lanes, x, y)
            if not valid:
                continue
            counts[lane] += 1
            bounds = [min(bounds[0], x), max(bounds[1], x),
                      min(bounds[2], y), max(bounds[3], y)]
            pair = (((u >> 12) & 1) << 1) | ((v >> 12) & 1)
            values = [(table[lane] >> pair) & 1 for table in TABLES]
            changed = [count + (values[a] != values[b])
                       for count, a, b in zip(changed, (0, 1, 2), (1, 2, 0))]
    if counts != EXPECTED_LANES or changed != EXPECTED_CHANGES or bounds != [40, 280, 40, 360]:
        raise ValueError(f"scaled T1q oracle mismatch: lanes={counts}, changed={changed}, bounds={bounds}")
    packets = [wire + table + SELECTORS for table in TABLES]
    hashes = [sha256(packet) for packet in packets]
    if hashes != list(EXPECTED_PACKETS) or any(len(packet) != 183 for packet in packets):
        raise ValueError("scaled T1q packet length or frozen hash mismatch")
    if packets[0] != packets[-1]:
        raise ValueError("return-A packet differs from initial A")
    record = {"valid_pixels": sum(counts), "winner_pixels_by_lane": counts,
              "changed_pixels_ab_bc_ca": changed, "bounds_xyxy": bounds,
              "derived_wire_sha256": sha256(wire), "packet_sha256": hashes}
    return packets, record


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
    wire = scaled_wire()
    packets, oracle_record = make_packets(wire)
    if args.dry_run:
        print(json.dumps(oracle_record, sort_keys=True))
        print("PASS: frozen T1q 4x-scaled A/B/C/return-A preflight")
        return 0

    transcript = {"format": "SPU_GPU_T1Q_SCALED_VISIBILITY_V1",
                  "port": args.port, "baud": 115200, "framing": "8N1",
                  "bitstream_sha256": BITSTREAM_SHA256,
                  "source_fixture_sha256": FIXTURE_SHA256,
                  "derived_wire_hex": wire.hex(), "oracle": oracle_record,
                  "status": "failed", "transmissions": []}
    fd = None
    try:
        args.transcript.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
        configure(fd)
        for index, (name, packet) in enumerate(zip(NAMES, packets)):
            started = time.monotonic_ns()
            written = os.write(fd, packet)
            item = {"scene": name, "wire_bytes": len(packet),
                    "wire_sha256": sha256(packet), "bytes_written": written,
                    "tcdrain_completed": False, "write_start_monotonic_ns": started}
            transcript["transmissions"].append(item)
            if written != len(packet):
                raise RuntimeError(f"{name}: short write {written}/{len(packet)}")
            termios.tcdrain(fd)
            item["tcdrain_completed"] = True
            item["drain_complete_monotonic_ns"] = time.monotonic_ns()
            print(f"sent {name}: {written} bytes; tcdrain complete", flush=True)
            if index < len(packets) - 1:
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
            with args.transcript.open("x") as stream:
                json.dump(transcript, stream, indent=2)
                stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
