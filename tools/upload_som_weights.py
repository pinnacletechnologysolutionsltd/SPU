#!/usr/bin/env python3
"""
Upload trained SOM weights to FPGA via RP2350 diag console.

Usage:
  python3 tools/upload_som_weights.py [--port /dev/ttyACM0] <weight_file.py>

The weight file must contain a `SOM_WEIGHTS` dict with node_id -> [4 x hex64] entries.
Use --export-py from iris_som_baseline.py to generate the weight file.
"""

import argparse
import re
import sys
import time

import serial


def load_weights(path):
    """Load SOM_WEIGHTS dict from a Python file."""
    ns = {}
    with open(path) as f:
        code = f.read()
    exec(compile(code, path, "exec"), ns)
    w = ns.get("SOM_WEIGHTS")
    if w is None:
        print(f"ERROR: {path} must define SOM_WEIGHTS dict")
        print(f"  Found symbols: {[k for k in ns if not k.startswith('_')]}")
        sys.exit(1)
    return w


def main():
    parser = argparse.ArgumentParser(description="Upload SOM weights to FPGA")
    parser.add_argument("--port", "-p", default="/dev/ttyACM0",
                        help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument("--baud", "-b", type=int, default=115200,
                        help="Baud rate (default: 115200)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Print commands without sending")
    parser.add_argument("weight_file", help="Python file with SOM_WEIGHTS dict")
    args = parser.parse_args()

    weights = load_weights(args.weight_file)
    n_nodes = max(weights.keys()) + 1
    n_feats = 4
    print(f"Loaded {n_nodes} nodes, {n_feats} features each")

    total = 0
    if args.dry_run:
        for node in sorted(weights):
            for feat, val in enumerate(weights[node]):
                if val != 0:
                    print(f"  somwrite {node} {feat} {val:016X}")
                    total += 1
        print(f"\nDry run: {total} non-zero features to upload")
        return

    ser = serial.Serial(args.port, args.baud, timeout=5)
    time.sleep(0.5)
    ser.reset_input_buffer()

    # Wait for prompt
    buf = b""
    deadline = time.time() + 5
    while time.time() < deadline:
        buf += ser.read(ser.in_waiting or 1)
        if b"> " in buf or b"OK" in buf:
            break

    sent = 0
    errors = 0
    for node in sorted(weights):
        for feat, val in enumerate(weights[node]):
            cmd = f"somwrite {node} {feat} {val:016X}\r\n"
            ser.write(cmd.encode())
            sent += 1
            # Wait for OK or ERR
            resp = b""
            deadline = time.time() + 2
            while time.time() < deadline:
                resp += ser.read(ser.in_waiting or 1)
                if b"OK" in resp or b"ERR" in resp:
                    break
            if b"ERR" in resp:
                print(f"  ERROR node={node} feat={feat}: {resp.decode().strip()}")
                errors += 1
            if sent % 64 == 0:
                print(f"  {sent}/{n_nodes * n_feats} written...")

    print(f"\nDone: {sent} writes, {errors} errors")
    ser.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
