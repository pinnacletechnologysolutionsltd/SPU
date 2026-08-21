# ina226_logger_v2.py — INA226 + shaft-encoder sampler for Pico / Pico 2
#
# v2 adds one column, `pulses`, carrying the raw encoder edge count for that
# sample interval. Everything else is unchanged from ina226_logger.py.
#
#   # ina226_logger v2 hz=100 rshunt_mohm=100 addr=0x40 avg=4 ct_us=588 \
#   #   enc_pin=6 ppr=0 debounce_us=0
#   t_ms,bus_mV,shunt_uV,current_uA,pulses
#   1023,5012,10230,102300,3
#   ...
#
# ─────────────────────────────────────────────────────────────────────
# READY FOR CAPTURE — this is the v3/v4-contract logger
# ─────────────────────────────────────────────────────────────────────
# The `pulses` column is now part of the frozen schema. `pulses` was added
# to the capture contract in v3 (2026-08-16, `ina226_coarse_monitor_v3.json`,
# `sessions_sealed_when_amended: 0` at the time -- the only reason the
# amendment was legitimate) and carried unchanged into v4 (2026-08-18, which
# only added the spu4_som_edge gate alongside it, see
# docs/INA226_COARSE_MONITOR_CONTRACT.md). `software/lib/ina226_capture.py`'s
# CSV_HEADER and row parser both require `pulses` now, and
# `tools/bench_metrics/power_log.py` accepts both the 4- and 5-column widths
# (`HEADER_V2`). This file is the one to flash as `main.py` for every capture
# from here on -- do not use `ina226_logger.py` (v1, no `pulses` column).
#
# **`ENC_PPR` below is still 0 (uncalibrated).** Run the ENC_PPR calibration
# procedure in docs/INA226_CAPTURE_RUNBOOK.md §2 with the actual encoder in
# hand, set the measured value here, and re-flash before block 0. A capture
# taken with `ENC_PPR=0` still logs valid raw pulse counts (nothing is lost),
# but the host cannot convert them to rpm until this is set truthfully.
#
# ─────────────────────────────────────────────────────────────────────
# Wiring
# ─────────────────────────────────────────────────────────────────────
#   INA226 SDA -> GP8   SCL -> GP9   VCC -> 3V3   GND -> GND
#   ALERT      -> GP15 (reserved; still unconfigured)
#   VIN+ -> supply side, VIN- -> target side (high-side sensing)
#   ENCODER out -> GP6, with the internal pull-up enabled
#
# GP6 was chosen because it is unclaimed in
# hardware/pcb/bench_adapter/bench_adapter_spec.md: GP2-5 flash PMOD,
# GP8/9 I2C, GP10-13 microSD, GP14 ACT LED, GP15 ALERT, GP16-19 SPI.
# The pin map there is firmware-locked, so do not move this without
# updating that document.
#
# ─────────────────────────────────────────────────────────────────────
# Why raw counts and not RPM
# ─────────────────────────────────────────────────────────────────────
# Same reason the shunt registers are read raw: scaling happens in plain
# sight, on the host, where it is auditable and can be redone.
#
# It also happens to be the only sensible choice here. At 100 Hz each sample
# interval is 10 ms, so a 20-slot wheel at 1000 rpm yields ~3.3 edges per
# sample -- one edge is worth ~300 rpm, which is useless as a per-row figure.
# Aggregated over the contract's 32-sample window (320 ms) the same setup
# gives ~107 edges, roughly 1% resolution. So: log edges per sample, let the
# host sum them over whatever window it actually wants.
#
# `ppr` (pulses per revolution) is recorded in the header rather than applied,
# because a salvaged ball-mouse wheel and a bought encoder differ and a raw
# count is meaningless without it. SET IT before capturing.
#
# ─────────────────────────────────────────────────────────────────────
# Failure behaviour
# ─────────────────────────────────────────────────────────────────────
# With no encoder connected the pull-up holds GP6 high, no edges arrive, and
# `pulses` reads 0 for every row. That is indistinguishable from a stalled
# motor -- which is a real capture class -- so DO NOT infer "encoder absent"
# from zeros. Confirm the encoder counts before block 0.

import time
from machine import I2C, Pin

I2C_ID = 0
SDA_PIN = 8
SCL_PIN = 9
ADDR = 0x40
RSHUNT_MOHM = 100      # stock module shunt, milliohms (R100 — verify marking)
SAMPLE_HZ = 100

# ── Encoder ──────────────────────────────────────────────────────────
ENC_PIN = 6
# Pulses per revolution. 0 = "not declared". Raw counts are still logged;
# the host cannot convert to rpm until this is set truthfully.
ENC_PPR = 0
# Minimum microseconds between accepted edges. 0 disables debouncing.
# A nonzero value imposes a hard ceiling:
#     max_rpm = 60_000_000 / (debounce_us * ppr)
# e.g. 200 us with a 20-slot wheel caps at 15000 rpm. Brush noise is a
# documented problem on this bench (see power_log.py's CDC-splitting note),
# so a small value is reasonable -- but set it deliberately and record it.
ENC_DEBOUNCE_US = 0

REG_CONFIG = 0x00
REG_SHUNT = 0x01
REG_BUS = 0x02
REG_MFG_ID = 0xFE      # reads 0x5449 ("TI")
REG_DIE_ID = 0xFF      # reads 0x2260

CONFIG = 0x02DF        # AVG=4, VBUSCT=VSHCT=588 us, shunt+bus continuous

MFG_ID_EXPECT = 0x5449
DIE_ID_EXPECT = 0x2260


def read16(i2c, reg):
    b = i2c.readfrom_mem(ADDR, reg, 2)
    return (b[0] << 8) | b[1]


def s16(v):
    return v - 65536 if v & 0x8000 else v


def rpm_from_pulses(pulses, elapsed_ms, ppr):
    """Integer rpm from an edge count over an interval. Host-side helper.

    Truncating integer division, no floating point, consistent with the rest
    of the bench arithmetic. Returns 0 when the conversion is undefined
    rather than raising, so a missing `ppr` cannot abort a capture.

        rev     = pulses / ppr
        minutes = elapsed_ms / 60000
        rpm     = pulses * 60000 / (ppr * elapsed_ms)
    """
    if ppr <= 0 or elapsed_ms <= 0 or pulses < 0:
        return 0
    return pulses * 60000 // (ppr * elapsed_ms)


class EdgeCounter:
    """Counts rising edges on a pin; read-and-clear per sample interval.

    The count is cleared as it is read, under a disabled-IRQ window, so an
    edge landing during the read is attributed to exactly one interval --
    never dropped, never double-counted.
    """

    def __init__(self, pin_no, debounce_us=0):
        self._count = 0
        self._debounce_us = debounce_us
        self._last_us = 0
        self._pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)
        self._pin.irq(trigger=Pin.IRQ_RISING, handler=self._on_edge)

    def _on_edge(self, _pin):
        if self._debounce_us:
            now = time.ticks_us()
            if time.ticks_diff(now, self._last_us) < self._debounce_us:
                return
            self._last_us = now
        self._count += 1

    def read_and_clear(self):
        try:
            import machine
            state = machine.disable_irq()
        except (ImportError, AttributeError):       # host-side testing
            state = None
        n = self._count
        self._count = 0
        if state is not None:
            machine.enable_irq(state)
        return n


def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400_000)

    # Identity check: the INA219 has no ID registers, so a wrong module on
    # the socket fails here instead of producing plausible garbage.
    mfg = read16(i2c, REG_MFG_ID)
    die = read16(i2c, REG_DIE_ID)
    if mfg != MFG_ID_EXPECT or die != DIE_ID_EXPECT:
        print("# ina226_logger FAIL id mfg=0x%04X die=0x%04X "
              "(expect 0x%04X/0x%04X) — wrong module or wiring?"
              % (mfg, die, MFG_ID_EXPECT, DIE_ID_EXPECT))
        return

    i2c.writeto_mem(ADDR, REG_CONFIG, bytes([CONFIG >> 8, CONFIG & 0xFF]))

    encoder = EdgeCounter(ENC_PIN, ENC_DEBOUNCE_US)

    print("# ina226_logger v2 hz=%d rshunt_mohm=%d addr=0x%02X avg=4 ct_us=588 "
          "enc_pin=%d ppr=%d debounce_us=%d"
          % (SAMPLE_HZ, RSHUNT_MOHM, ADDR, ENC_PIN, ENC_PPR, ENC_DEBOUNCE_US))
    if ENC_PPR == 0:
        print("# WARNING ppr=0 — raw pulse counts only, rpm cannot be derived")
    print("t_ms,bus_mV,shunt_uV,current_uA,pulses")

    period_ms = 1000 // SAMPLE_HZ
    next_t = time.ticks_ms()
    while True:
        next_t = time.ticks_add(next_t, period_ms)

        shunt_raw = s16(read16(i2c, REG_SHUNT))
        bus_raw = read16(i2c, REG_BUS)
        shunt_uV = shunt_raw * 5 // 2
        bus_mV = bus_raw * 5 // 4
        # Exact with the R100 shunt: I = V/R = (raw * 2.5 uV) / 0.1 ohm
        current_uA = shunt_raw * 25
        pulses = encoder.read_and_clear()

        print("%d,%d,%d,%d,%d"
              % (time.ticks_ms(), bus_mV, shunt_uV, current_uA, pulses))

        delay = time.ticks_diff(next_t, time.ticks_ms())
        if delay > 0:
            time.sleep_ms(delay)


if __name__ == "__main__":
    main()
