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
and, from an ina226_logger_v2 stream, a trailing `pulses`. The header is
chosen from the first data row rather than assumed, so the file always
matches its own rows.
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
# ina226_logger_v2 appends `pulses`. The header must match the rows actually
# written, or the file is malformed in a way the validator reports only at
# seal time. It is chosen from the first accepted row rather than assumed.
HEADER_V2 = HEADER + ",pulses"


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
    # The logger free-runs, so the OS buffer holds rows captured before this
    # invocation. Reading them replays old device timestamps and then jumps to
    # the present, and that discontinuity trips the validator's 8..12 ms
    # cadence gate (software/lib/ina226_capture.py:308-313) — rejecting the
    # session at seal, long after the bench work is done. Flush, then drop one
    # possibly-partial line so capture starts on a row boundary.
    ser.reset_input_buffer()
    ser.readline()
    phase = args.label
    t_end = time.monotonic() + args.seconds if args.seconds else None
    interactive = sys.stdin.isatty() and not args.seconds
    n = 0
    prev_t = None
    anomalies = []

    with open(args.out, "w") as out:
        # Written lazily, once the first data row reveals the logger's width.
        header_written = False
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
                # v1 loggers emit 4 fields; ina226_logger_v2 appends `pulses`.
                # This was `!= 4`, which SILENTLY dropped every row from a v2
                # logger -- `continue`, not an error, so a whole session would
                # capture zero samples and only announce it at seal time.
                # Accept both widths and reject anything else.
                if len(parts) not in (4, 5):
                    continue
                try:
                    [int(p) for p in parts]
                except ValueError:
                    continue
                # Motor brush noise can split a CDC line and rejoin it mid-field,
                # producing a row that still parses as four integers but carries a
                # corrupted t_ms (e.g. "1894" prepended to "18947855"). That trips
                # the validator's 8..12 ms cadence gate at seal, long after the
                # bench session is over. Flag it here instead, while the condition
                # can still be re-run.
                t_ms = int(parts[0])
                if prev_t is not None and not 5 <= t_ms - prev_t <= 20:
                    anomalies.append((n + 1, prev_t, t_ms))
                prev_t = t_ms

                if not header_written:
                    out.write((HEADER_V2 if len(parts) == 5 else HEADER) + "\n")
                    header_written = True

                iso = datetime.datetime.now().isoformat(timespec="milliseconds")
                out.write(f"{iso},{args.probe},{phase},{line}\n")
                n += 1
        except KeyboardInterrupt:
            pass

    if not header_written:
        # No row ever arrived. Emit the v1 header so the file is well-formed
        # and obviously empty, rather than zero bytes that look like a missing
        # capture instead of a silent logger.
        with open(args.out, "a") as out:
            out.write(HEADER + "\n")

    print(f"done: {n} samples -> {args.out}")
    if anomalies:
        print(f"WARNING: {len(anomalies)} corrupted timestamp(s) -- this session "
              f"would be REJECTED at seal. Re-run the capture.")
        for row, before, after in anomalies[:5]:
            print(f"  row {row}: t_ms {before} -> {after} (gap {after - before})")
        sys.exit(1)


if __name__ == "__main__":
    main()
