# Tang Primer 25K Build Guide

Target: **Sipeed Tang Primer 25K** (GW5A-LV25MG121C1/I0)

---

## RTL → Binary: What Each Step Produces

```
Verilog source (.v)
        │
        ▼  SYNTHESIS  (gowinsynthesis / Yosys)
        │  • Parses HDL, infers LUTs/FFs/DSP/BRAM
        │  • Maps to GOWIN primitives (rPLL, MULT18, BSRAM...)
        │  • Optimises combinatorial logic
        ▼
   Gate-level netlist
        │
        ▼  PLACE & ROUTE  (GOWIN P&R)
        │  • Assigns each LUT/FF to a physical cell on the GW5A die
        │  • Routes copper between cells
        │  • Runs Static Timing Analysis — must close at 24 MHz
        │  • Reports worst-case slack (positive = good)
        ▼
   Placed/routed database
        │
        ▼  BITSTREAM GENERATION
        │  • Packs P&R result into GOWIN configuration bitstream
        ▼
   spu13_25k.fs          ← THIS is what you flash to the board
        │
        ▼  PROGRAMMING
        │  openFPGALoader (Linux) or GOWIN Programmer (Windows)
        ▼
   FPGA configured  🟢
```

The `.fs` file is a binary blob that configures the FPGA's internal SRAM.
It is volatile — lost on power-off unless written to the onboard SPI flash.
Use "Embedded Flash" mode in GOWIN Programmer to make it permanent.

---

## Windows: Full Build (headless, no IDE)

### 1. Install GOWIN EDA
Download from https://www.gowinsemi.com/en/support/download_eda/
Choose "GOWIN EDA Education" (free).
Install to e.g. `C:\Gowin\Gowin_V1.9.x\`

### 2. One-time: Generate the real rPLL IP
```bat
cd C:\path\to\SPU
"C:\Gowin\Gowin_V1.9.x\IDE\bin\gw_sh.exe" hardware/boards/tang_primer_25k/gen_pll.tcl
```
This writes `pll_gowin.v`. Add it to `build.tcl` and remove `pll_gowin_stub.v`.

### 3. Full synthesis → bitstream
```bat
"C:\Gowin\Gowin_V1.9.x\IDE\bin\gw_sh.exe" hardware/boards/tang_primer_25k/build.tcl
```
Output: `build/tang_primer_25k/spu13_25k.fs`

### 4. Flash (Windows)
```bat
openFPGALoader -b tangprimer25k build/tang_primer_25k/spu13_25k.fs
```
Or use GOWIN Programmer GUI → Embedded Flash → select spu13_25k.fs → Program.

---

## Linux: Resource Counting (Yosys only, no P&R)

```bash
# From repo root:
yosys hardware/boards/tang_primer_25k/synth_gowin_25k.ys
```
Produces `tang_primer_25k.json` + resource report.
Does NOT produce a flashable bitstream (P&R requires GOWIN EDA or nextpnr-gowin).

---

## Linux: Flash after copying .fs from Windows

```bash
# Copy spu13_25k.fs to Linux (USB stick / git, do NOT commit .fs)
openFPGALoader -b tangprimer25k build/tang_primer_25k/spu13_25k.fs

# Verify board responds (should see PLL-lock LED within 100 ms)
```

### T48 Programmer note
The T48 universal programmer is for socketed ICs (EPROM, MCU flash).
It is NOT used for the Tang Primer 25K FPGA itself.
The Tang board has a built-in USB-C programmer (onboard FTDI).
Use the T48 for: RP2350/RP2040 SPI flash chips if direct USB DFU isn't available,
or for any socketed flash/EEPROM ICs in your hardware stack.

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `build.tcl` | **Main build script** — run with `gw_sh` on Windows |
| `gen_pll.tcl` | One-time rPLL IP generation |
| `spu_tang_top.v` | Board top module (rPLL, PSRAM×2, UART, Whisper TX) |
| `pll_gowin_stub.v` | Yosys blackbox stub for rPLL (synthesis/resource count only) |
| `synth_gowin_25k.ys` | Yosys-only synthesis script (Linux resource counting) |
| `tang_primer_25k.cst` | Physical constraints — ⚠️ verify pins vs Sipeed schematic |

---

## Pin Verification Checklist (before first flash)

⚠️ Verify `tang_primer_25k.cst` against:
https://dl.sipeed.com/shareURL/TANG/Primer_25K

Known issue to check:
- `sdram_cke` and `sdram_addr[0]` — possible A10 conflict in current draft
- PMOD-A / PMOD-B connector pinout (PSRAM CS/CLK/IO lines)
