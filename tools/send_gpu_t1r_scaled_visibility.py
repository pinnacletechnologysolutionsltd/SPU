#!/usr/bin/env python3
"""Oracle-check or send the frozen T1r 4x-scaled A/B/C/A sequence."""

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
FIXTURE_FILE_SHA256 = "079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143"
FIXTURE_WIRE_SHA256 = "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"
BITSTREAM = ROOT / "build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit"
BITSTREAM_SHA256 = "5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7"
WIRE_SHA256 = "1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df"
TABLES = tuple(bytes((value,) * 4) for value in (0x00, 0x0F, 0x06, 0x00))
SELECTORS = bytes((0xCC,) * 4)
PALETTES = bytes((0x1C, 0x2A, 0x31, 0x07))
NAMES = ("A", "B", "C", "return_A")
EXPECTED_PACKETS = (
    "3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58",
    "43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2",
    "71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37",
    "3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58",
)
EXPECTED_LANES = [11964, 11723, 7635, 7239]
EXPECTED_CHANGES = [38561, 11389, 27172]
EXPECTED_RGB = (
    {1: 7635, 2: 11723, 4: 11964, 7: 7239},
    {0: 7239, 3: 11964, 5: 11723, 6: 7635},
    {0: 652, 1: 651, 2: 1957, 3: 9770,
     4: 2194, 5: 9766, 6: 6984, 7: 6587},
)
sys.path.insert(0, str(ROOT / "software/tests"))
from test_gpu_t1i_uv import decode, oracle  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def scaled_wire():
    fixture_text = FIXTURE.read_bytes()
    source = bytes.fromhex(fixture_text.decode())
    if sha256(fixture_text) != FIXTURE_FILE_SHA256:
        raise ValueError("frozen geometry fixture file hash changed")
    if len(source) != 175 or source[0] != 0xA5 or sha256(source) != FIXTURE_WIRE_SHA256:
        raise ValueError("frozen geometry fixture framing, length, or hash changed")
    if sha256(BITSTREAM.read_bytes()) != BITSTREAM_SHA256:
        raise ValueError("frozen T1r bitstream hash changed")
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
        raise ValueError("scaled T1r geometry wire hash mismatch")
    return wire


def make_packets(wire):
    lanes = decode(int.from_bytes(wire[1:], "little"))
    winner_counts, outcomes = [0] * 4, [set() for _ in range(4)]
    rgb_counts = [dict() for _ in range(3)]
    changed, bounds = [0] * 3, [640, -1, 480, -1]
    overlap_pixels = uncovered_pixels = 0
    for y in range(480):
        for x in range(640):
            coverage = sum(all(a * x + b * y + c >= 0 for a, b, c in edges)
                           for edges, _uv, _u, _v, _depth in lanes)
            overlap_pixels += coverage > 1
            uncovered_pixels += coverage == 0
            valid, lane, u, v = oracle(lanes, x, y)
            if not valid:
                continue
            winner_counts[lane] += 1
            bounds = [min(bounds[0], x), max(bounds[1], x),
                      min(bounds[2], y), max(bounds[3], y)]
            pair = (((u >> 12) & 1) << 1) | ((v >> 12) & 1)
            values = [(table[lane] >> pair) & 1 for table in TABLES]
            outcomes[lane].add(values[2])
            colors = [(PALETTES[lane] >> (3 * value)) & 7 for value in values]
            for state, color in enumerate(colors[:3]):
                rgb_counts[state][color] = rgb_counts[state].get(color, 0) + 1
            for i, (a, b) in enumerate(((0, 1), (1, 2), (2, 3))):
                changed[i] += colors[a] != colors[b]
    if winner_counts != EXPECTED_LANES or bounds != [40, 280, 40, 360]:
        raise ValueError(f"coverage mismatch: lanes={winner_counts}, bounds={bounds}")
    if any(values != {0, 1} for values in outcomes):
        raise ValueError(f"XOR does not force both outcomes per lane: {outcomes}")
    if overlap_pixels != 38561 or uncovered_pixels != 268639:
        raise ValueError(f"overlap/uncovered mismatch: {overlap_pixels}/{uncovered_pixels}")
    if changed != EXPECTED_CHANGES or tuple(rgb_counts) != EXPECTED_RGB:
        raise ValueError(f"palette oracle mismatch: changes={changed}, rgb={rgb_counts}")
    packets = [wire + table + SELECTORS + PALETTES for table in TABLES]
    hashes = [sha256(packet) for packet in packets]
    if hashes != list(EXPECTED_PACKETS) or any(len(packet) != 187 for packet in packets):
        raise ValueError("T1r packet length or frozen packet hash mismatch")
    if packets[0] != packets[-1]:
        raise ValueError("return-A packet differs from initial A")
    record = {
        "valid_pixels": sum(winner_counts), "winner_pixels_by_lane": winner_counts,
        "xor_outcomes_by_lane": [sorted(values) for values in outcomes],
        "overlap_pixels": overlap_pixels, "uncovered_pixels": uncovered_pixels,
        "bounds_xyxy": bounds, "changed_pixels_ab_bc_ca": changed,
        "rgb_code_counts_by_state": [dict(sorted(row.items())) for row in rgb_counts],
        "derived_wire_sha256": sha256(wire), "wire_bytes": [len(p) for p in packets],
        "packet_sha256": hashes,
    }
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
        print("PASS: frozen T1r 4x-scaled palette A/B/C/return-A preflight")
        return 0

    transcript = {"format": "SPU_GPU_T1R_SCALED_VISIBILITY_V1",
                  "port": args.port, "baud": 115200, "framing": "8N1",
                  "bitstream_sha256": BITSTREAM_SHA256,
                  "source_fixture_file_sha256": FIXTURE_FILE_SHA256,
                  "source_fixture_wire_sha256": FIXTURE_WIRE_SHA256,
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
                    "wire_hex": packet.hex(), "wire_sha256": sha256(packet),
                    "bytes_written": written, "tcdrain_completed": False,
                    "write_start_monotonic_ns": started}
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
        with args.transcript.open("x") as stream:
            json.dump(transcript, stream, indent=2)
            stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
