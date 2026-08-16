#!/usr/bin/env python3
"""Host-side tests for ina226_logger_v2 — no Pico, no encoder, no bench.

The point of writing the firmware early is to shorten the bench session when
the encoder arrives. That only works if the arithmetic and the edge accounting
are already known-good, so what remains at the bench is a confidence check
rather than debugging.

`machine` does not exist off-device, so it is stubbed below. The stub is
deliberately thin: it provides only what the module touches, so a future
change that reaches for more hardware will fail here loudly instead of
silently diverging from what runs on the Pico.

Run:  python3 tools/bench_metrics/test_ina226_logger_v2.py
"""

import sys
import types
from pathlib import Path

# ── Stub `machine` before importing the logger ───────────────────────


class _Pin:
    IN = "IN"
    OUT = "OUT"
    PULL_UP = "PULL_UP"
    IRQ_RISING = "IRQ_RISING"

    def __init__(self, *_args, **_kwargs):
        self._handler = None

    def irq(self, trigger=None, handler=None):
        self._handler = handler

    def fire(self):
        """Test-only: simulate one rising edge."""
        if self._handler:
            self._handler(self)


class _I2C:
    def __init__(self, *_args, **_kwargs):
        pass


_machine = types.ModuleType("machine")
_machine.Pin = _Pin
_machine.I2C = _I2C
_machine.disable_irq = lambda: 0
_machine.enable_irq = lambda _state: None
sys.modules["machine"] = _machine

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ina226_logger_v2 as lg          # noqa: E402


PASS = 0
FAIL = 0


def check(label, got, want):
    global PASS, FAIL
    if got == want:
        print(f"PASS: {label}")
        PASS += 1
    else:
        print(f"FAIL: {label} — got {got!r}, want {want!r}")
        FAIL += 1


# ── rpm_from_pulses ──────────────────────────────────────────────────

# A 20-slot wheel at 1000 rpm over the contract's 32-sample window (320 ms):
#   edges = 1000/60 rev/s * 20 slots * 0.320 s = 106.67 -> 106 whole edges
#   rpm   = 106 * 60000 // (20 * 320) = 6360000 // 6400 = 993
# ~0.7% low from truncation, which is the resolution argument for aggregating
# over the window rather than per sample.
check("1000 rpm, 20 ppr, 320 ms window", lg.rpm_from_pulses(106, 320, 20), 993)

# The same setup per 10 ms sample: 3 edges, and one edge is worth ~300 rpm.
check("per-sample resolution is coarse", lg.rpm_from_pulses(3, 10, 20), 900)
check("one more edge per sample jumps 300 rpm",
      lg.rpm_from_pulses(4, 10, 20) - lg.rpm_from_pulses(3, 10, 20), 300)

# Stall: the class the study most needs to identify.
check("zero pulses is zero rpm", lg.rpm_from_pulses(0, 320, 20), 0)

# Undefined conversions return 0 rather than raising, so a missing ppr cannot
# abort a capture mid-session.
check("ppr=0 returns 0, does not raise", lg.rpm_from_pulses(100, 320, 0), 0)
check("elapsed=0 returns 0, does not raise", lg.rpm_from_pulses(100, 0, 20), 0)
check("negative pulses returns 0", lg.rpm_from_pulses(-1, 320, 20), 0)

# Exactness: a whole number of revolutions must land exactly, no drift.
#   2 rev in 1000 ms = 120 rpm, with 20 ppr that is 40 edges
check("whole revolutions are exact", lg.rpm_from_pulses(40, 1000, 20), 120)


# ── EdgeCounter ──────────────────────────────────────────────────────

def new_counter(debounce_us=0):
    c = lg.EdgeCounter(lg.ENC_PIN, debounce_us)
    return c, c._pin


c, pin = new_counter()
check("fresh counter reads zero", c.read_and_clear(), 0)

for _ in range(7):
    pin.fire()
check("counts every edge", c.read_and_clear(), 7)

# Read-and-clear must be exactly that: the same edges must not be reported
# twice. A double-count would inflate rpm silently.
check("read clears the count", c.read_and_clear(), 0)

for _ in range(3):
    pin.fire()
check("counting resumes after a clear", c.read_and_clear(), 3)

# Edges must accumulate across many intervals without loss -- 128 rows is a
# whole capture session.
c, pin = new_counter()
total = 0
for interval in range(128):
    for _ in range(interval % 5):
        pin.fire()
    total += c.read_and_clear()
check("no edges lost across 128 intervals", total, sum(i % 5 for i in range(128)))


# ── Debounce ─────────────────────────────────────────────────────────
# Fake a monotonic microsecond clock so debouncing is testable off-device.

_now_us = [0]
lg.time.ticks_us = lambda: _now_us[0]
lg.time.ticks_diff = lambda a, b: a - b

c, pin = new_counter(debounce_us=200)
_now_us[0] = 10_000
pin.fire()                      # accepted: first edge
_now_us[0] = 10_050
pin.fire()                      # rejected: 50 us < 200 us
_now_us[0] = 10_100
pin.fire()                      # rejected: 100 us since the accepted edge
_now_us[0] = 10_300
pin.fire()                      # accepted: 300 us since the accepted edge
check("debounce rejects edges inside the window", c.read_and_clear(), 2)

# Debounce must not reject legitimately fast edges below the ceiling.
c, pin = new_counter(debounce_us=200)
for i in range(10):
    _now_us[0] = 20_000 + i * 250
    pin.fire()
check("debounce passes edges outside the window", c.read_and_clear(), 10)

# Documented ceiling: max_rpm = 60e6 / (debounce_us * ppr).
# 200 us with a 20-slot wheel caps at 15000 rpm.
check("documented debounce ceiling", 60_000_000 // (200 * 20), 15000)


# ── Negative control ─────────────────────────────────────────────────
# If the stub's `fire()` did nothing, every count above would read 0 and every
# check would pass vacuously. Prove an edge actually reaches the handler.
c, pin = new_counter()
before = c._count
pin.fire()
check("negative control — a simulated edge reaches the handler",
      c._count > before, True)

print(f"\n{PASS + FAIL} checks, {PASS} passed, {FAIL} failed")
print("PASS" if FAIL == 0 else "FAIL")
sys.exit(1 if FAIL else 0)
