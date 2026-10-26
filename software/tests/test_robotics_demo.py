#!/usr/bin/env python3
"""test_robotics_demo.py — hardware-free regression for tools/robotics_demo.py.

Two things get checked without a board attached:
1. Instruction encoding (QLDI/ROTC/QSUB bit packing) matches
   hardware/rp2350/rp2350_spu_arithmetic_test.c's C macros exactly, since
   that firmware is the proven-in-silicon reference for this exact
   six-step closure sequence (`ARITHMETIC_BLAZE: PASS`).
2. The demo script's full flow (chord writes, qr_commit reads, real/surd
   decode, pass/fail detection) runs correctly against a fake serial port
   shaped like the real console, for both a closing (all-zero) and a
   non-closing (nonzero) final QSUB result.

No hardware required. Run: python3 software/tests/test_robotics_demo.py
"""

import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import robotics_demo as rd  # noqa: E402

BANNER = b"\r\nSPU RP diagnostic console ready\r\nType 'help' for commands.\r\n> "

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── Part 1: instruction encoding matches the C reference exactly ──────────

def c_qldi(lane, a, b, c, d):
    u8 = lambda v: v & 0xFF
    return (0x1D << 56) | (u8(lane) << 48) | (u8(a) << 32) | (u8(b) << 24) | (u8(c) << 16) | (u8(d) << 8)


def c_qsub(dst, lhs, rhs):
    return (0x1B << 56) | ((dst & 0xFF) << 48) | ((lhs & 0xFF) << 40) | ((rhs & 0xFF) << 8)


def c_rotc(dst, src, angle):
    return (0x1C << 56) | ((dst & 0xFF) << 48) | ((src & 0xFF) << 40) | ((angle & 0xFF) << 24)


for case in [(0, 3, 0, 0, 0), (1, 1, 0, 0, 0), (4, -5, -3, 7, -1), (0, 1, 2, 3, 4)]:
    check(f"inst_qldi{case} matches C macro", rd.inst_qldi(*case) == c_qldi(*case))

for case in [(2, 0, 1), (3, 1, 0), (5, 4, 4), (7, 6, 0)]:
    check(f"inst_qsub{case} matches C macro", rd.inst_qsub(*case) == c_qsub(*case))

for case in [(1, 0, 1), (2, 1, 1), (3, 2, 1), (4, 3, 1), (5, 4, 1), (6, 5, 1)]:
    check(f"inst_rotc{case} matches C macro", rd.inst_rotc(*case) == c_rotc(*case))

# Confirm this script drives the exact same 8-word sequence as
# rp2350_spu_arithmetic_test.c's test case [12] (six-step closure).
reference_words = [
    c_qldi(0, 1, 2, 3, 4),
    c_rotc(1, 0, 1), c_rotc(2, 1, 1), c_rotc(3, 2, 1),
    c_rotc(4, 3, 1), c_rotc(5, 4, 1), c_rotc(6, 5, 1),
    c_qsub(7, 6, 0),
]
script_words = [rd.inst_qldi(0, 1, 2, 3, 4)]
src = 0
for dst in rd.QR_STEPS:
    script_words.append(rd.inst_rotc(dst, src, rd.ROTATE_ANGLE))
    src = dst
script_words.append(rd.inst_qsub(rd.QR_DIFF, src, rd.QR_START))
check("script's 8-word sequence matches the proven-in-silicon C test case [12]",
      script_words == reference_words)

# ── Part 2: real/surd decode ───────────────────────────────────────────────

def pack(real, surd):
    return ((surd & 0xFFFFFFFF) << 32) | (real & 0xFFFFFFFF)


check("decode_component: positive real, negative surd",
      rd.decode_component(pack(5, -1)) == (5, -1))
check("decode_component: negative real, positive surd",
      rd.decode_component(pack(-2, 3)) == (-2, 3))
check("decode_component: exact zero",
      rd.decode_component(pack(0, 0)) == (0, 0))


# ── Part 3: full script flow against a fake serial port ───────────────────

class FakeSerial:
    def __init__(self, qr_queue):
        self._out = bytearray(BANNER)
        self._qr_queue = list(qr_queue)
        self.chord_calls = []

    @property
    def in_waiting(self):
        return len(self._out)

    def read(self, n):
        chunk = bytes(self._out[:n])
        del self._out[:n]
        return chunk

    def write(self, data):
        cmd = data.decode("ascii").rstrip("\r\n")
        echo = data.replace(b"\n", b"\r\n")
        if cmd == "qr":
            lines = [self._qr_queue.pop(0)]
        elif cmd.startswith("chord "):
            self.chord_calls.append(cmd)
            lines = ["OK " + cmd]
        else:
            lines = ["ERR unknown command: " + cmd]
        body = ("\r\n".join(lines) + "\r\n").encode("ascii")
        self._out += echo + body + b"> "

    def close(self):
        pass


def qr_line(lane, a, b, c, d):
    return "OK qr valid=1 lane=%d A=0x%016X B=0x%016X C=0x%016X D=0x%016X" % (
        lane, pack(*a), pack(*b), pack(*c), pack(*d)
    )


def make_qr_queue(final_zero):
    q = [qr_line(0, (1, 0), (2, 0), (3, 0), (4, 0))]
    for i, dst in enumerate(rd.QR_STEPS, start=1):
        q.append(qr_line(dst, (i, 1), (i, -1), (i, 2), (i, -2)))
    q.append(qr_line(rd.QR_DIFF, (0, 0), (0, 0), (0, 0), (0, 0)) if final_zero
              else qr_line(rd.QR_DIFF, (1, 0), (0, 0), (0, 0), (0, 0)))
    return q


def run_script(final_zero):
    ser = FakeSerial(make_qr_queue(final_zero))
    rd.SETTLE_S = 0
    real_serial_ctor = rd.serial.Serial
    rd.serial.Serial = lambda *a, **k: ser
    try:
        rc = rd.main(["--port", "/dev/fake"])
    finally:
        rd.serial.Serial = real_serial_ctor
    return rc, ser


rc, ser = run_script(final_zero=True)
check("closing sequence (all-zero diff) returns exit code 0", rc == 0)
check("exactly 8 chord writes sent", len(ser.chord_calls) == 8)

rc2, ser2 = run_script(final_zero=False)
check("non-closing sequence (nonzero diff) returns exit code 1", rc2 == 1)
check("still exactly 8 chord writes sent on the failing case", len(ser2.chord_calls) == 8)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
