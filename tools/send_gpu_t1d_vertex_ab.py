#!/usr/bin/env python3
"""Send exactly one frozen A or B T1d vertex diagnostic scene."""

import argparse
import hashlib
import json
import os
import sys
import termios
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
EVIDENCE = Path("build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_01")
START_BYTE = 0xA5
LENGTH = 64
BAUD = 115200
SCENES = {
    "A": {
        "packet": Path("build/gpu_evaluation/s1_t1d_scene_20261004/run_01/scene_packet.bin"),
        "sha256": "aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee",
        "transcript": EVIDENCE / "uart_a.json",
    },
    "B": {
        "packet": Path("build/gpu_evaluation/t1d_vertex_ab_20261004/scene_b_01/scene_packet.bin"),
        "sha256": "156ab65f14559c350bc602d4a48ee441cc2b145bfaee1a7775cde067e395a61d",
        "transcript": EVIDENCE / "uart_b.json",
    },
}


def prepare(scene, port, transcript, root=ROOT):
    if scene not in SCENES:
        raise ValueError("scene must be A or B")
    if port != PORT:
        raise ValueError(f"port must be the frozen by-id endpoint {PORT}")

    spec = SCENES[scene]
    root = Path(root).resolve()
    expected_transcript = root / spec["transcript"]
    requested_transcript = Path(transcript)
    if not requested_transcript.is_absolute():
        requested_transcript = root / requested_transcript
    if requested_transcript.resolve(strict=False) != expected_transcript.resolve(strict=False):
        raise ValueError(f"transcript must be {spec['transcript']}")
    if expected_transcript.exists() or expected_transcript.is_symlink():
        raise FileExistsError(f"refusing existing transcript: {expected_transcript}")
    if not expected_transcript.parent.is_dir():
        raise FileNotFoundError(f"evidence directory is missing: {expected_transcript.parent}")

    packet_path = root / spec["packet"]
    payload = packet_path.read_bytes()
    if len(payload) != LENGTH:
        raise ValueError(f"packet length {len(payload)} != {LENGTH}")
    if payload[0] != START_BYTE:
        raise ValueError(f"packet start 0x{payload[0]:02X} != 0x{START_BYTE:02X}")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"packet SHA-256 {digest} != frozen {spec['sha256']}")
    return packet_path, payload, digest, expected_transcript


def configure_port(fd):
    attrs = termios.tcgetattr(fd)
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR | termios.IGNCR |
                  termios.ICRNL | termios.IXON)
    attrs[1] &= ~termios.OPOST
    attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] |= termios.CS8 | termios.CLOCAL | termios.CREAD
    attrs[3] &= ~(termios.ECHONL | termios.ICANON | termios.ISIG |
                  termios.IEXTEN)
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


def send_once(scene, port, transcript, root=ROOT):
    packet_path, payload, digest, transcript_path = prepare(
        scene, port, transcript, root
    )
    started_ns = time.time_ns()
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    written = None
    drained_ns = None
    drain_completed = False
    status = "FAILED"
    error = None
    try:
        configure_port(fd)
        written = os.write(fd, payload)
        if written != LENGTH:
            status = "SHORT_WRITE"
            error = f"short write: {written}/{LENGTH}"
        if written > 0:
            termios.tcdrain(fd)
            drained_ns = time.time_ns()
            drain_completed = True
            time.sleep(0.1)
        if written == LENGTH:
            status = "TRANSMISSION_COMPLETE"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            os.close(fd)
        except Exception as exc:
            status = "FAILED"
            error = f"close: {type(exc).__name__}: {exc}"

    record = {
        "format": "SPU_GPU_T1D_VERTEX_AB_UART_V1",
        "scene": scene,
        "port": port,
        "baud": BAUD,
        "framing": "8N1",
        "packet": str(packet_path.relative_to(Path(root).resolve())),
        "length": len(payload),
        "sha256": digest,
        "written": written,
        "tcdrain_completed": drain_completed,
        "post_drain_wait_ms": 100 if drain_completed else 0,
        "write_start_unix_ns": started_ns,
        "drain_complete_unix_ns": drained_ns,
        "status": status,
        "error": error,
    }
    with transcript_path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    if status != "TRANSMISSION_COMPLETE":
        raise RuntimeError(error or status)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=("A", "B"), required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--transcript", required=True)
    args = parser.parse_args(argv)
    try:
        result = send_once(args.scene, args.port, args.transcript)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"sent {result['written']} bytes; tcdrain complete; transcript={args.transcript}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
