
# Historical Note

This file contains early Colorlight i9 pinout assumptions. For current measured
status, use `docs/COLORLIGHT_I9_PINOUT_VERIFIED.md`. The current probe uses the
25 MHz oscillator on FPGA ball P3 as `clk_25m`; the old 50 MHz SODIMM clock
assumption is stale.

# Colorlight i9 SODIMM Pinout Reference

## Overview

The Colorlight i9 evaluation module uses a **DDR2 SODIMM edge connector** (200-pin standard) as its primary interface. This document maps SODIMM pins to LFE5U-44F (caBGA-381 package) FPGA balls for the SPU-13 minimal evaluation spin.

---

## SODIMM Pin Numbering

**DDR2 SODIMM:**
- **200 pins** (100 on each edge)
- **Pin 1 & 2:** Ground
- **Pin 3 & 4:** Power (V+)
- **Pins 5–100:** Signal rows (alternating left/right)

Standard DDR2 SODIMM pinout: [https://en.wikipedia.org/wiki/SODIMM](https://en.wikipedia.org/wiki/SODIMM)

---

## SPU-13 Minimal Spin Signal Assignments

### System Signals

| SODIMM Pin | Signal | Direction | ECP5U-45 Ball | Bank | I/O Type | Notes |
|------------|--------|-----------|-----------------|------|----------|-------|
| **11** | `sys_clk` | IN | A4 (PL11A) | 7 | LVCMOS33 | 50 MHz crystal; PULL_MODE=NONE |
| **12** | `sys_clk_n` (opt) | IN | A5 (PL11B) | 7 | LVCMOS33 (diff) | Companion diff pair for low jitter |
| **25** | `rst_n` | IN | B2 (PL23C) | 7 | LVCMOS33 | Active-low reset; internal pull-up |

### Status LEDs (3× Active-Low)

| SODIMM Pin | Signal | Direction | ECP5U-45 Ball | Bank | I/O Type | Notes |
|------------|--------|-----------|-----------------|------|----------|-------|
| **27** | `led[0]` | OUT | A2 (PL23A) | 7 | LVCMOS33 | LED 0 (Red or general status) |
| **29** | `led[1]` | OUT | B1 (PL23B) | 7 | LVCMOS33 | LED 1 (Green or status 1) |
| **31** | `led[2]` | OUT | C2 (PL23D) | 7 | LVCMOS33 | LED 2 (Blue or status 2) |

### Serial Communication

| SODIMM Pin | Signal | Direction | ECP5U-45 Ball | Bank | I/O Type | Baud | Notes |
|------------|--------|-----------|-----------------|------|----------|------|-------|
| **33** | `uart_tx` | OUT | D1 (PL26B) | 7 | LVCMOS33 | 115.2k | Open-drain or push-pull (verify board) |
| **35** (opt) | `uart_rx` | IN | D2 (PL26C) | 7 | LVCMOS33 | 115.2k | Optional; for bidirectional telemetry |

### SPI Interface (Optional: Southbridge or Flash Control)

| SODIMM Pin | Signal | Direction | ECP5U-45 Ball | Bank | I/O Type | Notes |
|------------|--------|-----------|-----------------|------|----------|-------|
| **36** (opt) | `spi_cs_n` | IN | E2 (PL32D) | 7 | LVCMOS33 | Chip Select (active low) |
| **37** (opt) | `spi_clk` | IN | F2 (PL32C) | 7 | LVCMOS33 | Serial Clock (CPHA=0, CPOL=0) |
| **38** (opt) | `spi_mosi` | IN | E3 (PL20B) or F3 (PL32B) | 7 | LVCMOS33 | Master-Out, Slave-In |
| **39** (opt) | `spi_miso` | OUT | F4 (PL20A) | 7 | LVCMOS33 | Master-In, Slave-Out (open-drain) |

---

## Extended I/O (Available for Future Expansion)

The Colorlight i9 SODIMM exposes additional pins in GPIO headers (typically dual 30-pin PMOD-compatible blocks). These are available for:
- Sensory inputs (gyroscope, accelerometer, quantum control lines)
- Second UART
- Experimental interfaces

**Bank 6 & 7 remaining pins:** See `FPGA-SC-02034-3-0-ECP5U-45-Pinout.csv` for full roster.

---

## Power Supply Pins (SODIMM)

| SODIMM Pin | Signal | Voltage | Notes |
|------------|--------|---------|-------|
| **1, 2** | GND | 0V | Ground plane |
| **3, 4, 53, 54** | VCC | +3.3V | 3.3V rail (I/O banks) |

**Internal power (managed on Colorlight i9 module):**
- **VCC (core):** 1.1V (LDO-regulated on-module)
- **VCCAUX:** 2.5V (LDO-regulated on-module)
- **VCCIO7, VCCIO6:** 3.3V (from SODIMM VCC rail)

---

## Clock Integrity

### Crystal Specification

- **Frequency:** 50.0 MHz ±20 ppm
- **Load capacitance:** 10–18 pF (typical)
- **ESR:** <60 Ω
- **Jitter:** <5 ps RMS (recommended for SPU-13 timing predictability)

### Recommended Crystal Part Numbers
- **Abracon ABM8-50.000MHZ-B2-T** (50 MHz, ±20 ppm, 18 pF load)
- **SiTime SiT1533** (programmable, <3 ps jitter)

### Clock Path on Colorlight i9

1. **50 MHz crystal** → SODIMM pin 11 (on-module connector)
2. **Crystal buffer** (typically on Colorlight module) → filters jitter
3. **FPGA input** → PL11A (caBGA-381 pin A4) with pull-up termination removed

**For low-jitter applications:** Use differential pair (PL11A + PL11B) with matched trace lengths.

---

## Reset Sequencing

### Power-Up Reset

1. Power supplies stabilize (typically 1–10 ms)
2. Colorlight module asserts `rst_n` LOW
3. FPGA initialization begins (configuration EEPROM loaded)
4. `rst_n` released HIGH after ~100 ms

### Manual Reset (Pushbutton or External Control)

- Press to hold `rst_n` LOW for ≥1 ms
- Release to trigger SPU-13 core reset sequence
- Fibonacci sequencer re-initializes; Davis Law monitor armed

---

## SODIMM Orientation & Mechanical

- **Connector type:** DDR2 SODIMM (not DDR3)
- **Keying:** 1 notch in center (not compatible with DDR3 modules)
- **Mounting:** Dual retention clips at each end
- **Dimensions:** 67.6 mm × 30 mm × 4 mm (approx)

**Correct insertion:**
- Align module so notch matches slot on carrier board
- Push down evenly until both retention clips snap into place
- Verify no bent pins or misalignment before powering on

---

## Colorlight i9 Reference Documentation

### Community Resources
- **GitHub:** https://github.com/wuxx/Colorlight-FPGA-Projects
  - Reverse-engineered schematics
  - Pre-made constraint files (.lpf, .cst)
  - Example Verilog designs for i5/i9 variants

- **Telegram/Discord:** Colorlight FPGA community
  - Pinout clarifications
  - Hardware bring-up troubleshooting
  - Alternative constraint file sharing

### Manufacturer (Colorlight)
- Official site: https://www.colorlight.com/
- Datasheets often NDA-protected; refer to community repos
- Support via email (inquire at Colorlight)

### Lattice Documentation
- **ECP5U-45 Pinout CSV:** `FPGA-SC-02034-3-0-ECP5U-45-Pinout.csv`
- **Family datasheet:** `FPGA_DS_02012_2_4_ECP5_ECP5G_Family_Data_Sheet-1022822.pdf`
- **Hardware checklist:** `FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf`

---

## Verification Checklist

Before powering on the Colorlight i9 with SPU-13 bitstream:

- [ ] SODIMM module fully inserted; retention clips seated
- [ ] Power supply (3.3V on VCC pins) measured with multimeter
- [ ] No visible solder bridges or damaged pins
- [ ] 50 MHz clock signal verified with oscilloscope (if test point accessible)
- [ ] Reset button functional (rst_n toggles between 0V and 3.3V)
- [ ] UART TX pin produces 3.3V or TTL-level signal (use scope/logic analyzer)
- [ ] LED indicator pins respond to test pulses (software or manual GPIO toggle)
- [ ] No FPGA overheating (touch FPGA package; should be lukewarm, not hot)

---

## Common Pinout Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| Clock pin not differential | Jitter >10 ps, timing failures | Route both PL11A + PL11B as diff pair; use GND return paths |
| Reset inverted | Core never enters normal operation, stuck in boot | Verify `rst_n` is active-LOW; add inverter if hardware tied wrong |
| UART TX floating | No serial output, but core running (LEDs on) | Check pin 33 connection; ensure UART buffer enabled in top module |
| SPI CS# not toggled | SPI slave never responds to commands | Verify CS# is active-LOW; add pull-up if missing |
| Power rail glitch | Intermittent FPGA resets or configuration loss | Add 100 nF bypass capacitors on each VCC pin; use low-ESR caps |

---

## Signal Integrity Notes

### 3.3V LVCMOS33 Specifications

- **Output high:** 2.4 V (min) → 3.3 V (max)
- **Output low:** 0 V (min) → 0.4 V (max)
- **Input high:** 2.0 V (min)
- **Input low:** 0.8 V (max)
- **Drive strength:** 8 mA (typical for SPU-13 design)

### Trace Routing on Colorlight i9 Module

- **Clock (50 MHz):** Length-matched diff pair from crystal to FPGA; ~100 mils max length
- **Reset (1 MHz → DC):** Non-critical; standard signal integrity
- **UART TX (115.2k):** Standard CMOS levels; <1 meter cable recommended for noise immunity
- **SPI (25 MHz typical):** Standard I²C/SPI signal integrity; clock skew <2 ns

---

## Troubleshooting via Pinout

If your Colorlight i9 doesn't respond as expected:

1. **Verify clock:**
   - Pin 11 oscilloscope reading: should see clean 50 MHz sine or square wave
   - If no signal: check crystal connections, buffer output

2. **Check reset:**
   - Pin 25 multimeter reading: should be 3.3V (released) or 0V (pressed)
   - If stuck at 0V: reset circuit may be broken; check capacitors

3. **Test LEDs:**
   - Manually short LED pins to GND with 10 kΩ resistor (test point)
   - LEDs should illuminate; if not, check on-board resistor values

4. **Measure UART:**
   - Connect USB-to-serial converter; listen on pin 33
   - If no data: verify UART is compiled into bitstream; check baud rate

---

## Next Steps

1. **Obtain Colorlight i9 official schematic** or link from community (wuxx GitHub)
2. **Verify all pin mappings** in `colorlight_i9.lpf` against actual schematic
3. **Build bitstream:** `bash build_colorlight_i9_minimal.sh all`
4. **Flash to Colorlight i9** using openFPGALoader or RP2040 SPI programmer
5. **Run smoke tests:** Verify LEDs, UART, clock integrity

---

**Document version:** 1.0 (2026-07-05)
**Last verified:** Preliminary pinout based on ECP5U-45 datasheet + community reverse-engineering
**Status:** Historical planning note. Use the docs listed at the top for
current measured status.
