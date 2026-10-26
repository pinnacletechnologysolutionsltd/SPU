#!/usr/bin/env python3
"""robotics_demo.py — first-hour demo for the ROBOTICS spin (Wukong Artix-7).

Drives six ROTC (60 degree Quadray rotation) steps in a row on real silicon
and proves the result returns to the *exact* starting Quadray coordinate --
zero accumulated error, not "close enough". This is the headline claim of
the whole platform made concrete: forward kinematics with no floating-point
drift, checked bit-for-bit on hardware you can hold, not simulated.

Wiring: RP2350 southbridge -> Wukong J11 (see AGENTS.md's J11 pin-damage
notes -- confirm the bottom-row remap before connecting). Board must be
flashed with the ROBOTICS spin: `bash hardware/boards/artix7/build_a7.sh
100t robotics synth/pnr/pack`, then SRAM-loaded.

Usage:
    python3 tools/robotics_demo.py --port /dev/ttyACM0

Instruction encoding and the six-step closure sequence itself are taken
directly from hardware/rp2350/rp2350_spu_arithmetic_test.c (test case
[12], the same golden vector already proven in silicon as
`ARITHMETIC_BLAZE: PASS` -- this script exercises the identical sequence
through the general-purpose spu_host client instead of a one-off firmware
build, so it doubles as a portable regression, not just a demo.
"""

import argparse
import sys
import time
import types

try:
    import serial
except ImportError:
    # Deferred: pyserial is a real runtime dependency for talking to actual
    # hardware, but the instruction-encoding/decoding logic below has no
    # need for it and should stay importable (for tests, or introspection)
    # on any Python, not just the one pyserial happens to be installed in.
    # main() raises a clear error if this stub is ever actually used to open
    # a port.
    serial = types.ModuleType("serial")
    serial.Serial = None

sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])
from software.spu_host import SPUHostClient, SPUProtocolError

# QR register lanes used by the sequence, matching the C firmware exactly.
QR_START = 0   # QLDI target: the initial Quadray vector
QR_STEPS = list(range(1, 7))  # QR1..QR6, one per 60-degree rotation
QR_DIFF = 7    # QSUB target: QR6 - QR0, must land on exact zero

ROTATE_ANGLE = 1  # ROTC angle code 1 == 60 degrees (thirds circulant, period 6)

# Post-write settle time. QSUB/ROTC are multi-cycle (serial QR-file reads);
# the reference firmware sleeps 5ms after every chord write before polling
# status. Same margin here, comfortably above what real hardware needs.
SETTLE_S = 0.02


def inst_qldi(lane, a, b, c, d):
    """QLDI QRd, A,B,C,D -- load an integer-only Quadray immediate."""
    def u8(v):
        return v & 0xFF
    return (
        (0x1D << 56)
        | (u8(lane) << 48)
        | (u8(a) << 32)
        | (u8(b) << 24)
        | (u8(c) << 16)
        | (u8(d) << 8)
    )


def inst_rotc(dst, src, angle):
    """ROTC QRd, QRs, angle -- Thomson circulant rotation."""
    return (0x1C << 56) | ((dst & 0xFF) << 48) | ((src & 0xFF) << 40) | ((angle & 0xFF) << 24)


def inst_qsub(dst, lhs, rhs):
    """QSUB QRd, QRa, QRb -- QR[d] = QR[a] - QR[b]."""
    return (0x1B << 56) | ((dst & 0xFF) << 48) | ((lhs & 0xFF) << 40) | ((rhs & 0xFF) << 8)


def decode_component(raw64):
    """Split a QR-commit A/B/C/D field into (real, surd) signed 32-bit ints.

    Wire layout (see hardware/rp2350/rp2350_spu_arithmetic_test.c's
    read_qr_commit): within each 64-bit component, the low 32 bits are the
    real (rational) part and the high 32 bits are the surd (sqrt3) part --
    the reverse of the packed 16+16 in-register RationalSurd convention.
    """
    real = raw64 & 0xFFFFFFFF
    surd = (raw64 >> 32) & 0xFFFFFFFF
    if real >= 0x80000000:
        real -= 0x100000000
    if surd >= 0x80000000:
        surd -= 0x100000000
    return real, surd


def format_quadray(commit):
    parts = []
    for name in ("A", "B", "C", "D"):
        real, surd = decode_component(commit[name])
        parts.append(f"{name}=({real:+d},{surd:+d}√3)")
    return " ".join(parts)


def run_step(client, word, label):
    client.write_chord(word)
    time.sleep(SETTLE_S)
    commit = client.qr_commit()
    print(f"  {label:<28} lane={commit['lane']}  {format_quadray(commit)}")
    return commit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", required=True, help="e.g. /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    ns = parser.parse_args(argv)

    if serial.Serial is None:
        print("ERROR: pyserial is not installed (pip install pyserial).", file=sys.stderr)
        return 1

    ser = serial.Serial(ns.port, ns.baud, timeout=0.05)
    client = SPUHostClient(ser)
    try:
        client.connect()

        print("ROBOTICS six-step closure -- exact 360 degree rotation, zero drift")
        print("=" * 72)

        start = run_step(client, inst_qldi(QR_START, 1, 2, 3, 4), "QLDI QR0 = (1,2,3,4)")

        src = QR_START
        for i, dst in enumerate(QR_STEPS, start=1):
            run_step(client, inst_rotc(dst, src, ROTATE_ANGLE), f"ROTC QR{dst} <- rotate(QR{src}) [{i}/6]")
            src = dst

        diff = run_step(client, inst_qsub(QR_DIFF, src, QR_START), f"QSUB QR{QR_DIFF} = QR{src} - QR0")

        print("=" * 72)
        exact_zero = all(diff[c] == 0 for c in ("A", "B", "C", "D"))
        if diff["lane"] == QR_DIFF and exact_zero:
            print("PASS: six 60-degree rotations returned to the exact starting")
            print("      coordinate -- bit-for-bit zero, not an epsilon comparison.")
            return 0
        print(f"FAIL: expected QR{QR_DIFF} == 0, got {format_quadray(diff)}")
        return 1
    except SPUProtocolError as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
