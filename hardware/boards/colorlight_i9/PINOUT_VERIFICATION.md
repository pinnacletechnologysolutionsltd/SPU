
# Historical Note

This file records an early pinout verification pass. For current status, use
`docs/COLORLIGHT_I9_PINOUT_VERIFIED.md`. The current LPF uses `clk_25m` on P3
and the RPLU2 probe has passed synthesis, P&R, and bitstream packaging.

# Colorlight i9 Pinout Verification — Current Mapping vs. Schematic

## Current Constraint File (colorlight_i9.lpf) — TENTATIVE

Based on ECP5U-45 caBGA-381 datasheet + community estimates:

| Signal | SODIMM Pin | ECP5U-45 Ball | DDR2 Function | Status |
|--------|------------|---------------|----------------|--------|
| `sys_clk` | 11 | A4 (PL11A) | Standard I/O | ⏳ VERIFY |
| `sys_clk_n` (opt) | 12 | A5 (PL11B) | Diff companion | ⏳ VERIFY |
| `rst_n` | 25 | B2 (PL23C) | Standard I/O | ⏳ VERIFY |
| `led[0]` | 27 | A2 (PL23A) | Standard I/O | ⏳ VERIFY |
| `led[1]` | 29 | B1 (PL23B) | Standard I/O | ⏳ VERIFY |
| `led[2]` | 31 | C2 (PL23D) | Standard I/O | ⏳ VERIFY |
| `uart_tx` | 33 | D1 (PL26B) | Standard I/O | ⏳ VERIFY |
| `uart_rx` (opt) | 35 | D2 (PL26C) | Standard I/O | ⏳ VERIFY |
| `spi_cs_n` (opt) | 36 | E2 (PL32D) | Standard I/O | ⏳ VERIFY |
| `spi_clk` (opt) | 37 | F2 (PL32C) | Standard I/O | ⏳ VERIFY |
| `spi_mosi` (opt) | 38 | E3 (PL20B) | Standard I/O | ⏳ VERIFY |
| `spi_miso` (opt) | 39 | F4 (PL20A) | Standard I/O | ⏳ VERIFY |

---

## What We Need from Colorlight i9 Schematic (i5-i9-extboard.pdf)

**For SPU-13 minimal spin, please identify in the schematic:**

### 1. System Clock Path
```
Question: Where does the 50 MHz crystal or oscillator connect?
  • Is it on SODIMM pin 11?
  • Or on a different pin?
  • Is it differential (pins 11 + 12)?
  • Or single-ended?

Expected in schematic:
  - Crystal symbol (or "OSC" label)
  - SODIMM connector pin number
  - Trace to FPGA ball
```

### 2. Reset Signal
```
Question: Is there a reset button or reset control line?
  • Which SODIMM pin?
  • Active high or active low?
  • Pull-up or pull-down?

Expected in schematic:
  - Reset button symbol (or "RST" label)
  - SODIMM connector pin
  - Any resistor/capacitor network (RC debounce)
```

### 3. LEDs (Status Indicators)
```
Question: How many LEDs, and where?
  • Are they on SODIMM pins 27, 29, 31?
  • Or different pins?
  • Active high or active low?

Expected in schematic:
  - 1–3 LED symbols
  - Series resistor (typically 1–2.2 kΩ)
  - Traces to SODIMM pins
  - SODIMM pins labeled
```

### 4. UART / Serial
```
Question: Is there a UART TX output available?
  • Which SODIMM pin?
  • 3.3V LVCMOS or level-shifted?
  • Any RS232 converter?

Expected in schematic:
  - UART TX net label
  - SODIMM connector pin
  - Optional level-shifter IC
```

### 5. SPI (Optional: Southbridge or Flash Control)
```
Question: Are SPI signals (CS, CLK, MOSI, MISO) accessible on SODIMM?
  • Which pins?
  • Or are they multiplexed with on-board flash?

Expected in schematic:
  - SPI bus traces
  - Connection to on-board flash (U3 typically W25Q128)
  - Optional routing to SODIMM pins
```

### 6. On-Board Flash (W25Q128 or similar)
```
Question: What flash chip is used, and which pins?
  • Part number (e.g., W25Q128JV)?
  • Connected directly to FPGA SPI pins?
  • Or through SODIMM connector?

Expected in schematic:
  - Flash IC symbol
  - Pin labels (CS#, SCK, MOSI, MISO, etc.)
  - Traces to FPGA balls
```

---

## Current Constraint Mapping Rationale

**Clock (Pins 11–12):**
- ECP5U-45 GPLL0 (global phase-locked loop) typically on banks 7 or 8
- PL11A (A4) is a GPLL input; PL11B (A5) is the differential companion
- SODIMM DDR2 pin 11 = standard I/O pad
- Assumption: Colorlight i9 routes crystal oscillator here

**Reset (Pin 25):**
- Typical DDR2 SODIMM positioning for control signals
- PL23C (B2) is a general-purpose I/O in bank 7
- Assumption: Reset button or control line here

**LEDs (Pins 27, 29, 31):**
- Consecutive DDR2 SODIMM positions
- Banks 7 I/O pins with minimal skew
- Assumption: Status LEDs on these pins

**UART (Pin 33):**
- Standard SODIMM positioning for serial
- PL26B (D1) is a general-purpose I/O output
- Assumption: UART TX available here

---

## How to Verify (Visual Schematic Inspection)

1. **Open i5-i9-extboard.pdf** in a PDF viewer
2. **Locate the SODIMM connector symbol** (labeled J1 or COJ1 in schematic)
3. **Trace each net from SODIMM pins to FPGA BGA balls:**
   - Note the net label (e.g., "CLK", "RST", "LED1", etc.)
   - Find the destination FPGA ball (e.g., "A4", "B2", etc.)
   - Record in the table below

4. **Fill in the verification table** and report back:

### Verification Template

```
From i5-i9-extboard.pdf visual inspection:

SODIMM Pin 11 (Clock):
  Schematic label: ________________
  Traces to FPGA ball: ________________
  Type (differential/single-ended): ________________

SODIMM Pin 25 (Reset):
  Schematic label: ________________
  Traces to FPGA ball: ________________
  Active high/low: ________________

SODIMM Pin 27 (LED 0):
  Schematic label: ________________
  Traces to FPGA ball: ________________

SODIMM Pin 29 (LED 1):
  Schematic label: ________________
  Traces to FPGA ball: ________________

SODIMM Pin 31 (LED 2):
  Schematic label: ________________
  Traces to FPGA ball: ________________

SODIMM Pin 33 (UART TX):
  Schematic label: ________________
  Traces to FPGA ball: ________________

SPI Signals (if available):
  CS#:   SODIMM pin ___ → FPGA ball ___
  SCK:   SODIMM pin ___ → FPGA ball ___
  MOSI:  SODIMM pin ___ → FPGA ball ___
  MISO:  SODIMM pin ___ → FPGA ball ___

On-Board Flash (W25Q128 or similar):
  Part number: ________________
  CS#:   FPGA ball ___
  SCK:   FPGA ball ___
  MOSI:  FPGA ball ___
  MISO:  FPGA ball ___
```

---

## Next Steps After Verification

1. **If all matches:** Update `.lpf` file with confirmed pins → run P&R ✓
2. **If some differ:** Correct constraint file → test P&R → flashable ✓
3. **If major differences:** Redesign board top module → full re-synthesis

---

## Alternative: Community Reverse-Engineering

If visual schematic inspection is tedious, check:
- **GitHub:** https://github.com/wuxx/Colorlight-FPGA-Projects
  - May have `.lpf` files for i5 v7.0 or i9
  - May have reverse-engineered SODIMM-to-BGA mappings
  - Community forum discussions on pinouts

- **KiCad Libraries:**
  - Colorlight FPGA community may publish KiCad project
  - Contains schematic symbols + pinout info in structured format

---

**Ready to verify?** This is historical. Use the docs listed at the top for
current measured status.
