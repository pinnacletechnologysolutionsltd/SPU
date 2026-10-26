#!/usr/bin/env python3
"""SRAM-load timing-closed Tang bench profile; passively capture boot UART."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from rp2040_flash_pmod import PosixSerial


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", required=True)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--build-dir", type=Path,
                   default=Path("build/spu4_ina226_benchmark/bench25"))
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("refusing to overwrite capture")
    root = Path(__file__).resolve().parents[1]
    build = args.build_dir if args.build_dir.is_absolute() else root / args.build_dir
    timing = (build / "pnr.log").read_text()
    if ("ERROR:" in timing or "PASS at 25.00 MHz" not in timing or
            "Program finished normally" not in timing):
        raise ValueError("timing preflight not passed")
    bitstream = build / "probe.fs"
    if bitstream.stat().st_mtime_ns < (build / "pnr.log").stat().st_mtime_ns:
        raise ValueError("bitstream predates timing log")
    serial = PosixSerial(args.port, timeout=0.5)
    try:
        serial.reset_input_buffer()
        load = subprocess.run(["openFPGALoader", "-b", "tangprimer25k", str(bitstream)],
                              capture_output=True, timeout=60)
        lines = []
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            line = serial.readline()
            if line:
                lines.append(line.hex())
    finally:
        serial.close()
    record = dict(scope="SRAM load and passive boot capture; not model parity or latency",
                  bitstream_sha256=hashlib.sha256(bitstream.read_bytes()).hexdigest(),
                  pnr_sha256=hashlib.sha256((build / "pnr.log").read_bytes()).hexdigest(),
                  baud=115200, uart_lines_hex=lines, loader_exit=load.returncode,
                  loader_stdout=load.stdout.decode(errors="replace"),
                  loader_stderr=load.stderr.decode(errors="replace"))
    with args.output.open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    if load.returncode:
        raise ValueError("SRAM load failed; raw record saved")
    for line in lines:
        print(bytes.fromhex(line).decode(errors="replace").strip())
    # The BL616 CDC bridge can prefix the first post-programming line with a
    # NUL while the endpoint settles. Preserve that byte in raw evidence but
    # do not mistake it for a missing hydration record.
    if not any(bytes.fromhex(line).lstrip(b"\0").startswith(b"SOM:H")
               for line in lines):
        raise ValueError("no boot hydration line; do not accept hardware preflight")


if __name__ == "__main__":
    main()
