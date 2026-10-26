#!/usr/bin/env python3
"""TENSEGRITYLINK four-act campaign driver.

Repeats the admission / mechanical-negative / corrupt-payload-rollback /
recovery sequence N times over the RP2350 diagnostic console, comparing every
tgrstatus field against the expected tuple and logging raw console output.

Criterion 5 of docs/ZPHI_KARATSUBA_SWAP_CRITERIA.md. Acts 2 and 3 are the
internal positive control: if act 2 stops returning state=8 fault=5, or act 3
stops returning error=7, the rig is not discriminating and passes are
meaningless -- so those are checked as hard as the passes.

Usage: tgr_four_act.py --port /dev/serial/by-id/... [--runs 10] [--out LOG]
"""
import argparse
import re
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial required: source .venv/bin/activate")

CANON = "TGR/00_canonical_balanced.tgr"
FAULT = "TGR/06_fault_not_in_equilibrium.tgr"

# (label, command, expected tgrstatus fields)
ACTS = [
    ("1 admission", f"tgrload {CANON} 0",
     dict(state=2, fault=0, stage=8, vector=0, flags=0x08, error=0)),
    ("2 mechanical-negative", f"tgrload {FAULT} 6",
     dict(state=8, fault=5, stage=8, vector=6, flags=0x08, error=0)),
    ("3 corrupt-payload", f"tgrloadbadcrc {FAULT} 6",
     dict(state=8, fault=5, stage=0, vector=6, flags=0x09, error=7)),
    ("4 recovery", f"tgrload {CANON} 0",
     dict(state=2, fault=0, stage=8, vector=0, flags=0x08, error=0)),
]
# Invariant across every act.
COMMON = dict(nodes=12, edges=30, received=468, expected=468)

FIELD = re.compile(r"(\w+)=(0x[0-9A-Fa-f]+|\d+)")


def parse_status(line):
    if "tgrstatus" not in line:
        return None
    out = {}
    for k, v in FIELD.findall(line):
        out[k] = int(v, 16) if v.startswith("0x") else int(v)
    return out or None


def send(ser, cmd, log, settle=0.35):
    ser.reset_input_buffer()
    ser.write((cmd + "\r\n").encode())
    ser.flush()
    time.sleep(settle)
    lines, t0 = [], time.time()
    while time.time() - t0 < 3.0:
        raw = ser.readline()
        if not raw:
            if lines:
                break
            continue
        text = raw.decode("ascii", "replace").rstrip()
        if text:
            lines.append(text)
            log.write(text + "\n")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--out", default="build/tgr_four_act/campaign.log")
    a = ap.parse_args()

    import os
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    ser = serial.Serial(a.port, 115200, timeout=0.4)
    time.sleep(0.3)

    passes = failures = 0
    with open(a.out, "w") as log:
        log.write(f"# TENSEGRITYLINK four-act campaign  port={a.port} "
                  f"runs={a.runs}  started={time.strftime('%FT%T%z')}\n")
        for run in range(1, a.runs + 1):
            print(f"--- run {run}/{a.runs} ---")
            log.write(f"\n=== run {run} ===\n")
            run_ok = True
            for label, cmd, want in ACTS:
                log.write(f"> {cmd}\n")
                send(ser, cmd, log)
                log.write("> tgrstatus\n")
                got = None
                for line in send(ser, "tgrstatus", log):
                    got = parse_status(line) or got
                if got is None:
                    print(f"  act {label}: NO STATUS RESPONSE")
                    log.write("!! no tgrstatus response\n")
                    run_ok = False
                    break
                bad = {k: (v, got.get(k)) for k, v in {**want, **COMMON}.items()
                       if got.get(k) != v}
                if bad:
                    run_ok = False
                    print(f"  act {label}: MISMATCH {bad}")
                    log.write(f"!! mismatch {bad}\n")
                    break
                print(f"  act {label}: ok")
            if run_ok:
                passes += 1
            else:
                failures += 1
                print(f"STOPPING at run {run} -- a deviation is the finding; "
                      f"do not re-run until it looks clean.")
                log.write(f"!! campaign stopped at run {run}\n")
                break
        log.write(f"\n# passes={passes} failures={failures}\n")

    print(f"\npasses={passes} failures={failures}  log={a.out}")
    return 0 if failures == 0 and passes >= a.runs else 1


if __name__ == "__main__":
    sys.exit(main())
