# gen1_reset_pulse: timed KEY0 reset pulses for the Wukong V3 (Raspberry Pi Pico 2)

Bench instrument for GEN1-RESET-EDGE-1. One Pico 2 GPIO pulls the Wukong KEY0 reset net low, and the timing comes from PIO
hardware: one instruction per 150 MHz cycle, so 6.67 ns resolution. Each sequence takes three values: pulse A, the gap, then pulse B.
All three are loaded before the sequence starts, so USB or CPU latency can delay the start but never change an interval.

It does **not** change the FPGA design: the reset path under test is the board's own KEY0 net (R37 4.7 kΩ pull-up to 3.3 V, switch SW2, FPGA ball H7).

## Builds
| Target | Use | Pin behaviour |
|---|---|---|
| `gen1_reset_pulse_od` | **GP2 wired directly to KEY0** (used for the recorded result) | Open drain: the output level is fixed LOW and only the direction toggles. Assert = drive LOW; idle = high-impedance. It **cannot drive HIGH**. Input buffer and pulls are disabled. |
| `gen1_reset_pulse` | GP2 → 4.7 kΩ → NPN base, collector on KEY0 | Push-pull. HIGH = assert, idles LOW. **Never connect this build directly to KEY0**: it would hold reset at idle and drive HIGH into the net. |

```bash
export PICO_SDK_PATH=/path/to/pico-sdk          # tested with SDK 2.3.1
cmake -S hardware/rp2350/gen1_reset_pulse -B build/rp2350_gen1_reset_pulse
cmake --build build/rp2350_gen1_reset_pulse --target gen1_reset_pulse_od
# Pico in BOOTSEL (hold BOOTSEL while plugging in USB), then:
picotool load -x build/rp2350_gen1_reset_pulse/gen1_reset_pulse_od.uf2
```
`STATUS` must report `mode=direct-od` before GP2 is connected to KEY0.

## Wiring (direct build)
| Pico 2 | Wukong V3 |
|---|---|
| pin 4 (GP2) | SW2 KEY0 leg: a switch leg reading ≈ 3.3 V with the Pico not connected |
| pin 3 (GND) | a SW2 leg reading 0 V, or J11 pin 5 |

Optionally, a logic analyser on the same KEY0 leg through a 1 kΩ series resistor, with its ground on the Pico GND.

## Commands (USB CDC, one per line)
| Command | Effect |
|---|---|
| `SEQ <a_ns> <gap_ns> <b_ns> <n> <period_ms>` | `n` sequences, `period_ms` apart. `b_ns 0` = no pulse B. Echoes the exact quantized times, then prints `TRIAL k t_us=…` per sequence and `DONE`. |
| `HOLD <ms>` | Assert continuously, 1–20000 ms. |
| `STATUS` | Mode, pin and clock. |

Limits: each value ≤ 20 s, total ≤ 25 s, `n` ≤ 100; `period_ms` must exceed the sequence length + 3 ms, so a UART record from the golden image can finish.

## Safety precautions
- **Use only the `gen1_reset_pulse_od` build on a direct connection.** Check `STATUS` first.
- Connect GND before GP2. Connect only to the SW2 switch legs, never to the FPGA package or to the 3.3 V end of R37.
- **Load the intended FPGA image before connecting.** The board may boot an unrelated flash design whose use of H7 is unknown.
- Electrical basis, from the RP2350 datasheet:
  - GPIO 0–25 are fault-tolerant pads. With IOVDD = 0 V they accept up to 3.63 V with negligible current, so an unpowered Pico on the powered 3.3 V KEY0 net is within rating.
  - Asserting sinks about 0.7 mA through R37.
  - Erratum RP2350-E9 cannot occur because the input buffer stays disabled.
- A watchdog reboot (e.g. `picotool load -f`) does not reset the pads. Reflash with the BOOTSEL button at power-up, or with the GP2 wire removed, so an asserted level cannot be held across a reboot.
- Pressing KEY0 while the Pico is connected is electrically harmless: both pull low. Results taken during a press are invalid.

## Measured behaviour (bench and Wukong, 2026-11-08; see `docs/hardware_evidence.md` §3.52 when accepted)
- Release through the 4.7 kΩ pull-up reaches a logic analyser's threshold about 0.2 µs after the commanded edge. Pulses therefore read about 0.2 µs long and gaps about 0.2 µs short.
- A commanded gap of 2.07 µs measured 1.75–2.00 µs on KEY0, at 4 MS/s.
- The cheap fx2lafw analyser streams reliably at 8 and 4 MS/s; at 24 and 12 MS/s it dropped out.
