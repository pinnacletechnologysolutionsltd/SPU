#!/usr/bin/env python3
"""Upload a validated SPU_SOM_MAP_V1 JSON artifact through the RP2350 console."""

from __future__ import annotations

import argparse
import sys

from som_map import DiagConsole, PosixSerial, SomMapError, iter_weight_commands, load_map


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_file", help="validated SPU_SOM_MAP_V1 JSON file")
    parser.add_argument("--port", "-p", default="/dev/ttyACM0")
    parser.add_argument("--baud", "-b", type=int, default=115200)
    parser.add_argument("--dry-run", "-n", action="store_true")
    args = parser.parse_args()

    try:
        document = load_map(args.map_file)
    except SomMapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    commands = list(iter_weight_commands(document))
    print(
        f"Validated {document['model']}: {document['node_count']} nodes, "
        f"{len(commands)} prototype writes, SHA-256 {document['map_sha256']}"
    )
    if args.dry_run:
        print("\n".join(commands))
        return 0

    with PosixSerial(args.port, args.baud) as serial_port:
        console = DiagConsole(serial_port)
        for index, command in enumerate(commands, 1):
            console.command(command)
            if index % 7 == 0:
                print(f"  {index}/28 writes accepted")
    print("Upload complete: 28/28 writes accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
