# ina226_logger.py — MicroPython INA226 sampler for Raspberry Pi Pico / Pico 2
#
# Copy to the Pico as main.py (Thonny/mpremote). Streams CSV over USB CDC:
#
#   # ina226_logger v1 hz=100 rshunt_mohm=100 addr=0x40 avg=4 ct_us=588
#   t_ms,bus_mV,shunt_uV,current_uA
#   1023,5012,10230,102300
#   ...
#
# Wiring (matches hardware/pcb/bench_adapter/bench_adapter_spec.md §2.5,
# identical on a breadboard):
#   INA226 SDA -> GP8   INA226 SCL -> GP9   VCC -> 3V3   GND -> GND
#   ALERT -> GP15 (reserved; v1 polls and leaves it unconfigured)
#   VIN+ -> 5V supply side, VIN- -> target board side (high-side sensing)
#
# All arithmetic is integer. With the stock 0.1 ohm (R100) shunt:
#   shunt LSB = 2.5 uV  ->  shunt_uV   = raw * 5 // 2   (<=0.5 uV truncation)
#                           current_uA = raw * 25       (exact: 2.5uV / 0.1R)
#   bus LSB   = 1.25 mV ->  bus_mV     = raw * 5 // 4   (<=0.75 mV truncation)
# The calibration/current/power registers are deliberately unused: raw shunt
# counts are exact and auditable; scaling happens in plain sight.
#
# CSV columns are identical to ina219_logger.py so power_log.py /
# power_table.py consume either logger unchanged.

import time
from machine import I2C, Pin

I2C_ID = 0
SDA_PIN = 8
SCL_PIN = 9
ADDR = 0x40
RSHUNT_MOHM = 100      # stock module shunt, milliohms (R100 — verify marking)
SAMPLE_HZ = 100

REG_CONFIG = 0x00
REG_SHUNT = 0x01
REG_BUS = 0x02
REG_MFG_ID = 0xFE      # reads 0x5449 ("TI")
REG_DIE_ID = 0xFF      # reads 0x2260

# AVG = 4 samples, VBUSCT = VSHCT = 588 us, shunt+bus continuous.
# One averaged result every ~4.7 ms — comfortably fresh at 100 Hz polling,
# with 4x hardware averaging the INA219 could not do.
#   [11:9] AVG  = 001 (4)
#   [8:6] VBUSCT = 011 (588 us)
#   [5:3] VSHCT  = 011 (588 us)
#   [2:0] MODE   = 111 (shunt + bus, continuous)
CONFIG = 0x02DF

MFG_ID_EXPECT = 0x5449
DIE_ID_EXPECT = 0x2260


def read16(i2c, reg):
    b = i2c.readfrom_mem(ADDR, reg, 2)
    return (b[0] << 8) | b[1]


def s16(v):
    return v - 65536 if v & 0x8000 else v


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

    print("# ina226_logger v1 hz=%d rshunt_mohm=%d addr=0x%02X avg=4 ct_us=588"
          % (SAMPLE_HZ, RSHUNT_MOHM, ADDR))
    print("t_ms,bus_mV,shunt_uV,current_uA")

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

        print("%d,%d,%d,%d"
              % (time.ticks_ms(), bus_mV, shunt_uV, current_uA))

        delay = time.ticks_diff(next_t, time.ticks_ms())
        if delay > 0:
            time.sleep_ms(delay)


main()
