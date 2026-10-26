#!/usr/bin/env python3
"""Capture GPIO-free MCU preflight; retain raw device output, not host timing."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from rp2040_flash_pmod import PosixSerial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--elf", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("refusing to overwrite evidence")
    captures = []
    serial = PosixSerial(args.port, timeout=1)
    try:
        time.sleep(1)
        for run in range(3):
            serial.reset_input_buffer()
            serial.write(b"R")
            lines = []
            deadline = time.monotonic()+15
            while time.monotonic() < deadline:
                line = serial.readline().decode("ascii", errors="replace").strip()
                if line:
                    lines.append(line)
                if line.startswith("END,"):
                    break
            captures.append(lines)
    finally:
        serial.close()
    artifact = dict(scope="RP2350 SRAM kernel preflight only; not stream/offload benchmark",
                    elf_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),
                    runs=captures)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(artifact, stream, indent=2)
        stream.write("\n")
    for lines in captures:
        if not lines or lines[-1] != "END,120,120":
            raise ValueError("incomplete/failed hardware parity; raw evidence retained")
        cases = [line.split(",") for line in lines if line.startswith("CASE,")]
        if len(cases) != 120 or [int(row[1]) for row in cases] != list(range(120)):
            raise ValueError("missing/duplicate records")
        for row in cases:
            if int(row[3]) <= 0 or row[-1] != "1":
                raise ValueError("invalid timer or parity")
        print(lines[0])
        for column, name in ((2,"preprocessing"),(3,"classifier"),(4,"pipeline")):
            values = sorted(int(row[column]) for row in cases)
            print(name, "cycles min/median/p99/max", values[0], values[60], values[118], values[-1])


if __name__ == "__main__":
    main()
