#!/usr/bin/env python3
"""test_lucas_demo.py — hardware-free regression for tools/lucas_demo.py.

Checks, without a board attached:
1. Instruction packing reproduces the four golden words from
   hardware/rp2350/rp2350_lucas_j11_smoke.c bit-for-bit (the silicon-proven
   `LUCAS_J11: PASS` vectors).
2. The inline Z[phi]/L_521 oracle reproduces the four golden results, and
   PINV is a true inverse (PMUL of a value with its PINV gives 1 + 0*phi)
   across a sweep of operands.
3. The full script flow runs against a fake serial port that emulates the
   Lucas sidecar: the pass path (faithful sidecar), and the fail path (a
   sidecar that returns one wrong value mid-loop) both exit correctly.
4. The float64 leg of the drift race diverges at step 79 -- pinned so the
   demo's printed claim ("float64 fails around step 79") can't silently
   drift out of sync with reality.

No hardware required. Run: python3 software/tests/test_lucas_demo.py
"""

import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import lucas_demo as ld  # noqa: E402

BANNER = b"\r\nSPU RP diagnostic console ready\r\nType 'help' for commands.\r\n> "

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── Part 1: golden instruction words (from the silicon-proven smoke test) ──

check("PSCALE golden word",
      ld.inst_lucas(ld.OP_PSCALE, 2, 3, 5) == 0xD0200C0500000000)
check("PCHIRAL golden word",
      ld.inst_lucas(ld.OP_PCHIRAL, 12, 3, 5) == 0xD1C00C0500000000)
check("PMUL golden word",
      ld.inst_lucas(ld.OP_PMUL, 3, 3, 5, 2, 7) == 0xD2300C0500807000)
check("PINV golden word",
      ld.inst_lucas(ld.OP_PINV, 4, 3, 5) == 0xD3400C0500000000)


# ── Part 2: oracle vs golden results + PINV inverse property ──────────────

def from_golden(g):
    """expected_a from the smoke firmware, decoded as A = {b, a}."""
    return g & 0xFFFFFFFF, g >> 32


check("oracle PSCALE matches silicon golden",
      ld.oracle_pscale(3, 5) == from_golden(0x0000000800000005))
check("oracle PCHIRAL matches silicon golden",
      ld.oracle_pchiral(3, 5) == from_golden(0x0000020400000008))
check("oracle PMUL matches silicon golden",
      ld.oracle_pmul(3, 5, 2, 7) == from_golden(0x0000004200000029))
check("oracle PINV matches silicon golden",
      ld.oracle_pinv(3, 5) == from_golden(0x0000000500000201))

inverse_ok = True
for a in range(0, 40):
    for b in range(0, 40):
        if (a * a + a * b - b * b) % ld.L_P == 0:
            continue  # zero-norm elements have no inverse
        ia, ib = ld.oracle_pinv(a, b)
        if ld.oracle_pmul(a, b, ia, ib) != (1, 0):
            inverse_ok = False
check("PINV is a true inverse across a 40x40 operand sweep", inverse_ok)


# ── Part 3: full script flow against a sidecar-emulating fake serial ──────

class FakeLucasSerial:
    """Emulates the diag console + Lucas sidecar: decodes each chord word
    and answers the following 'qr' with the oracle-computed result, packed
    exactly the way cmd_qr() prints it."""

    def __init__(self, corrupt_at_chord=None):
        self._out = bytearray(BANNER)
        self._pending = None  # (lane, a, b) awaiting the next 'qr' read
        self._chord_count = 0
        self._corrupt_at = corrupt_at_chord

    @property
    def in_waiting(self):
        return len(self._out)

    def read(self, n):
        chunk = bytes(self._out[:n])
        del self._out[:n]
        return chunk

    def _execute(self, word):
        op = (word >> 56) & 0xFF
        lane = (word >> 52) & 0xF
        a = (word >> 42) & 0x3FF
        b = (word >> 32) & 0x3FF
        c = (word >> 22) & 0x3FF
        d = (word >> 12) & 0x3FF
        if op == ld.OP_PSCALE:
            res = ld.oracle_pscale(a, b)
        elif op == ld.OP_PCHIRAL:
            res = ld.oracle_pchiral(a, b)
        elif op == ld.OP_PMUL:
            res = ld.oracle_pmul(a, b, c, d)
        elif op == ld.OP_PINV:
            res = ld.oracle_pinv(a, b)
        else:
            res = (0, 0)
        self._chord_count += 1
        if self._corrupt_at is not None and self._chord_count == self._corrupt_at:
            res = ((res[0] + 1) % ld.L_P, res[1])  # single flipped result
        self._pending = (lane, res)

    def write(self, data):
        cmd = data.decode("ascii").rstrip("\r\n")
        echo = data.replace(b"\n", b"\r\n")
        if cmd.startswith("chord "):
            self._execute(int(cmd.split()[1], 16))
            lines = ["OK " + cmd]
        elif cmd == "qr":
            lane, (ra, rb) = self._pending
            a_field = (rb << 32) | ra  # A = {b[31:0], a[31:0]}
            lines = ["OK qr valid=1 lane=%d A=0x%016X B=0x%016X C=0x%016X D=0x%016X"
                     % (lane, a_field, 0, 0, 0)]
        else:
            lines = ["ERR unknown command: " + cmd]
        self._out += echo + ("\r\n".join(lines) + "\r\n").encode("ascii") + b"> "

    def close(self):
        pass


def run_script(steps, corrupt_at_chord=None):
    ser = FakeLucasSerial(corrupt_at_chord)
    for op in ld.SETTLE_S:
        ld.SETTLE_S[op] = 0
    real_ctor = ld.serial.Serial
    ld.serial.Serial = lambda *a, **k: ser
    try:
        rc = ld.main(["--port", "/dev/fake", "--steps", str(steps)])
    finally:
        ld.serial.Serial = real_ctor
    return rc, ser


rc, ser = run_script(steps=120)
check("faithful sidecar over 120 steps (past float64 divergence) exits 0", rc == 0)
check("chord count = 4 proven ops + 120 loop steps", ser._chord_count == 124)

rc2, _ = run_script(steps=30, corrupt_at_chord=20)  # corrupt one mid-loop step
check("sidecar returning one wrong mid-loop value exits 1", rc2 == 1)

rc3, _ = run_script(steps=10, corrupt_at_chord=3)  # corrupt a proven-op result
check("sidecar failing a proven-op vector exits 1", rc3 == 1)


# ── Part 4: pin the float64 divergence step ───────────────────────────────

ea, eb, fa, fb = 1, 0, 1.0, 0.0
diverge = None
for step in range(1, 200):
    ea, eb = eb, ea + eb
    fa, fb = fb, fa + fb
    if (round(fa) % ld.L_P, round(fb) % ld.L_P) != (ea % ld.L_P, eb % ld.L_P):
        diverge = step
        break
check("float64 leg diverges at step 79 exactly (2^53 Fibonacci boundary)",
      diverge == 79)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
