#!/usr/bin/env python3
"""Oracle-check and send one scaled T1p predicate visibility sequence."""

import argparse
import json
import os
from pathlib import Path
import sys
import termios
import time

from send_gpu_t1p_sequence import (BITSTREAM, BITSTREAM_SHA256, FIXTURE,
                                    FIXTURE_SHA256, OPS, SEQUENCE, configure,
                                    sha256)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software/tests"))
from test_gpu_t1i_uv import decode, oracle  # noqa: E402
from test_gpu_t1p_predicate_bits import result  # noqa: E402

SCALE = 4
FRAME = (640, 480)


def derived_wire():
    source = bytes.fromhex(FIXTURE.read_text())
    if len(source) != 175 or source[0] != 0xA5 or sha256(source) != FIXTURE_SHA256:
        raise ValueError("source fixture changed")
    if sha256(BITSTREAM.read_bytes()) != BITSTREAM_SHA256:
        raise ValueError("loaded bitstream artifact changed")
    scene = int.from_bytes(source[1:], "little")
    for lane in range(4):
        for edge in range(3):
            bit = lane * 348 + edge * 64 + 32
            raw = (scene >> bit) & 0xFFFFFFFF
            signed = raw if raw < (1 << 31) else raw - (1 << 32)
            scaled = signed * SCALE
            if not -(1 << 31) <= scaled < (1 << 31):
                raise ValueError("scaled edge constant overflows signed 32-bit")
            scene = (scene & ~(0xFFFFFFFF << bit)) | ((scaled & 0xFFFFFFFF) << bit)
    return b"\xA5" + scene.to_bytes(174, "little")


def preflight(wire):
    lanes = decode(int.from_bytes(wire[1:], "little"))
    won = [0] * 4
    changed = [0] * 3
    limits = [640, -1, 480, -1]
    for y in range(FRAME[1]):
        for x in range(FRAME[0]):
            valid, lane, u, v = oracle(lanes, x, y)
            if not valid:
                continue
            won[lane] += 1
            limits = [min(limits[0], x), max(limits[1], x),
                      min(limits[2], y), max(limits[3], y)]
            bits = [result(2, selectors[lane], u, v) for _, selectors in SEQUENCE[:3]]
            changed = [count + (bits[a] != bits[b]) for count, a, b in
                       zip(changed, (0, 1, 2), (1, 2, 0))]
    if min(won) < 5000 or min(changed) < 10000 or sum(won) < 30000:
        raise ValueError(f"insufficient visibility: won={won} changed={changed}")
    if limits != [40, 280, 40, 360]:
        raise ValueError(f"unexpected scene bounds: {limits}")
    return {"winner_pixels_by_lane": won, "valid_pixels": sum(won),
            "changed_pixels_ab_bc_ca": changed, "bounds_xyxy": limits}


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--send", action="store_true")
    parser.add_argument("--port")
    parser.add_argument("--transcript", type=Path)
    args = parser.parse_args()
    if args.send and (not args.port or not args.transcript):
        parser.error("--send requires --port and --transcript")
    if args.transcript and args.transcript.exists():
        parser.error("refusing to overwrite transcript")
    wire = derived_wire()
    if len(wire) != 175:
        raise ValueError("derived geometry wire length changed")
    oracle_record = preflight(wire)
    packets = [(name, wire + OPS + selectors) for name, selectors in SEQUENCE]
    if any(len(packet) != 183 for _, packet in packets) or packets[0][1] != packets[-1][1]:
        raise ValueError("T1p packet layout or exact return-A failed")
    print(json.dumps({"derived_wire_sha256": sha256(wire),
                      "packets": {name: sha256(packet) for name, packet in packets},
                      "oracle": oracle_record}, sort_keys=True), flush=True)
    if args.dry_run:
        return
    records = []
    fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    try:
        configure(fd)
        for index, (name, packet) in enumerate(packets):
            started = time.time_ns()
            written = os.write(fd, packet)
            if written != len(packet):
                raise RuntimeError(f"{name}: short write {written}/{len(packet)}")
            termios.tcdrain(fd)
            records.append({"scene": name, "wire_sha256": sha256(packet),
                            "bytes_written": written, "tcdrain_completed": True,
                            "write_start_unix_ns": started,
                            "drain_complete_unix_ns": time.time_ns()})
            print(f"sent {name}: {written} bytes; tcdrain complete", flush=True)
            if index + 1 < len(packets):
                time.sleep(5)
    finally:
        os.close(fd)
    for current, following in zip(records, records[1:]):
        current["next_packet_start_gap_ms"] = (
            following["write_start_unix_ns"] - current["write_start_unix_ns"]) / 1_000_000
    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    with args.transcript.open("x") as output:
        json.dump({"format": "SPU_GPU_T1P_SCALED_VISIBILITY_V1", "scale": SCALE,
                   "port": args.port, "baud": 115200, "framing": "8N1",
                   "source_fixture_sha256": FIXTURE_SHA256,
                   "bitstream_sha256": BITSTREAM_SHA256,
                   "derived_wire_hex": wire.hex(), "oracle": oracle_record,
                   "transmissions": records}, output, indent=2)
        output.write("\n")
    print(f"sequence complete; transcript={args.transcript}")


if __name__ == "__main__":
    main()
