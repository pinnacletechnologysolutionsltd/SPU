#!/usr/bin/env python3
"""power_log.py — host-side capture for ina219_logger.py streams.

Reads the Pico's USB CDC CSV stream and writes a phase-annotated CSV suitable
for power_table.py. Phases label what the target board was doing (idle,
active, probe name, ...) so one capture file can hold a whole session.

Scripted capture (one phase, fixed duration):

    python3 tools/bench_metrics/power_log.py --port /dev/ttyACM0 \
        --probe som_bmu_probe --label active --seconds 60 \
        --out build/metrics/som_bmu_active.csv

Interactive capture (type a new label + Enter to switch phase, Ctrl-C ends):

    python3 tools/bench_metrics/power_log.py --port /dev/ttyACM0 \
        --probe som_bmu_probe --out build/metrics/som_bmu.csv

Output columns: host_iso,probe,phase,t_ms,bus_mV,shunt_uV,current_uA
"""

import argparse
import datetime
import os
import select
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial required: source .venv/bin/activate && "
             "pip install -r requirements.txt")

HEADER = "host_iso,probe,phase,t_ms,bus_mV,shunt_uV,current_uA"


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", required=True, help="Pico USB CDC device")
    ap.add_argument("--baud", type=int, default=115200,
                    help="ignored by USB CDC but required by pyserial")
    ap.add_argument("--probe", default="unnamed",
                    help="probe/bitstream name for the table row")
    ap.add_argument("--label", default="unlabeled", help="initial phase label")
    ap.add_argument("--seconds", type=float, default=0,
                    help="stop after N seconds (0 = run until Ctrl-C)")
    ap.add_argument("--out", required=True, help="output CSV path")
    return ap.parse_args()


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    ser = serial.Serial(args.port, args.baud, timeout=1)
    phase = args.label
    t_end = time.monotonic() + args.seconds if args.seconds else None
    interactive = sys.stdin.isatty() and not args.seconds
    n = 0

    with open(args.out, "w") as out:
        out.write(HEADER + "\n")
        print(f"logging to {args.out}  probe={args.probe}  phase={phase}")
        if interactive:
            print("type a new phase label + Enter to switch; Ctrl-C to stop")
        try:
            while True:
                if t_end and time.monotonic() >= t_end:
                    break
                if interactive and select.select([sys.stdin], [], [], 0)[0]:
                    new = sys.stdin.readline().strip()
                    if new:
                        phase = new
                        print(f"-- phase: {phase} ({n} samples so far)")

                line = ser.readline().decode("ascii", "replace").strip()
                if not line or line.startswith("#") or line.startswith("t_ms"):
                    continue
                parts = line.split(",")
                if len(parts) != 4:
                    continue
                try:
                    [int(p) for p in parts]
                except ValueError:
                    continue
                iso = datetime.datetime.now().isoformat(timespec="milliseconds")
                out.write(f"{iso},{args.probe},{phase},{line}\n")
                n += 1
        except KeyboardInterrupt:
            pass

    print(f"done: {n} samples -> {args.out}")


if __name__ == "__main__":
    main()
