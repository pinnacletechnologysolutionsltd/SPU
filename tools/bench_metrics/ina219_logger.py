# ina219_logger.py — MicroPython INA219 sampler for Raspberry Pi Pico / Pico 2
#
# Copy to the Pico as main.py (Thonny/mpremote). Streams CSV over USB CDC:
#
#   # ina219_logger v1 hz=100 rshunt_mohm=100 addr=0x40
#   t_ms,bus_mV,shunt_uV,current_uA
#   1023,5012,10230,102300
#   ...
#
# Wiring (matches hardware/pcb/bench_adapter/bench_adapter_spec.md §2.5,
# identical on a breadboard):
#   INA219 SDA -> GP8   INA219 SCL -> GP9   VCC -> 3V3   GND -> GND
#   VIN+ -> 5V supply side, VIN- -> target board side (high-side sensing)
#
# All arithmetic is integer. With the stock 0.1 ohm shunt:
#   shunt_uV   = raw * 10        (INA219 shunt LSB = 10 uV)
#   current_uA = shunt_uV * 10   (I = V / 0.1)
# The calibration register is deliberately unused: raw shunt microvolts are
# exact and auditable; scaling happens in plain sight.

import time
from machine import I2C, Pin

I2C_ID = 0
SDA_PIN = 8
SCL_PIN = 9
ADDR = 0x40
RSHUNT_MOHM = 100      # stock module shunt, milliohms
SAMPLE_HZ = 100

REG_CONFIG = 0x00
REG_SHUNT = 0x01
REG_BUS = 0x02

# 32V bus range, PGA /8 (+/-320mV), 12-bit shunt+bus, continuous conversion.
# This is also the INA219 power-on default; written explicitly anyway.
CONFIG = 0x399F


def read16(i2c, reg):
    b = i2c.readfrom_mem(ADDR, reg, 2)
    return (b[0] << 8) | b[1]


def s16(v):
    return v - 65536 if v & 0x8000 else v


def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400_000)
    i2c.writeto_mem(ADDR, REG_CONFIG, bytes([CONFIG >> 8, CONFIG & 0xFF]))

    print("# ina219_logger v1 hz=%d rshunt_mohm=%d addr=0x%02X"
          % (SAMPLE_HZ, RSHUNT_MOHM, ADDR))
    print("t_ms,bus_mV,shunt_uV,current_uA")

    period_ms = 1000 // SAMPLE_HZ
    next_t = time.ticks_ms()
    while True:
        next_t = time.ticks_add(next_t, period_ms)

        shunt_uV = s16(read16(i2c, REG_SHUNT)) * 10
        bus_raw = read16(i2c, REG_BUS)
        bus_mV = (bus_raw >> 3) * 4
        # I = V / R, integer: uA = uV * 1000 / mohm
        current_uA = shunt_uV * 1000 // RSHUNT_MOHM

        print("%d,%d,%d,%d"
              % (time.ticks_ms(), bus_mV, shunt_uV, current_uA))

        delay = time.ticks_diff(next_t, time.ticks_ms())
        if delay > 0:
            time.sleep_ms(delay)


main()
