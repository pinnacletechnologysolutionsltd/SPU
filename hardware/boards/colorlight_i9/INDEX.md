
# Historical Note

This board-local index contains early estimates. For current measured status,
use `docs/COLORLIGHT_I9_SETUP_SUMMARY.md` and
`docs/colorlight_i9_feasibility.md`. The current RPLU2 probe routes at 25 MHz
and uses all 72 ECP5 multiplier blocks on the i9 target.

# Colorlight i9 Board Module — Index

**Quick Links:**
- [README (Board Overview & Build)](#readme)
- [Pinout Reference (SODIMM → FPGA)](#pinout)
- [Build Script & Constraints](#scripts)
- [Verification & Next Steps](#next-steps)

---

## README

**File:** `README_COLORLIGHT_I9.md`

Comprehensive guide covering:
- Board specifications (LFE5U-44F, caBGA-381, SODIMM interface)
- Key signals & SODIMM pin mapping
- Build instructions (synthesis, P&R, bitstream)
- Flashing methods (openFPGALoader, SPI programmer, bootloader)
- Smoke tests (LEDs, UART, SPI)
- Timing & resource budgets
- Troubleshooting matrix
- Transition path to custom LFE5U-45F boards

**Start here for:** First-time board bring-up, build troubleshooting, pinout questions.

---

## Pinout

**File:** `COLORLIGHT_I9_PINOUT.md`

Detailed signal assignments:
- SODIMM pin numbering (DDR2 standard)
- System signals (clock, reset, LEDs, UART, SPI)
- Power supply pins
- Clock integrity specs (50 MHz crystal, jitter requirements)
- Reset sequencing
- I/O electrical specifications (3.3V LVCMOS33)
- Signal integrity notes
- Community documentation links
- Troubleshooting via pinout

**Start here for:** Pin-level verification, clock debugging, custom board design.

---

## Scripts & Constraints

### Build Script
**File:** `build_colorlight_i9_minimal.sh`

Command-line orchestration:
- Curated source list (8 modules only; SPU-13 core + RPLU 2.0)
- Yosys synthesis (Verilog-2005 compatible)
- nextpnr P&R (--44k device, 50 MHz target)
- ecppack bitstream generation

Usage:
```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_minimal.sh [synth|pnr|all]
```

### Constraint File
**File:** `colorlight_i9.lpf`

Lattice Preference File mapping:
- SODIMM connector pins → LFE5U-44F (caBGA-381) BGA balls
- I/O types (LVCMOS33)
- Pull modes (UP for reset, NONE for clock)
- Timing constraints (50 MHz)
- Bank configuration (VCCIO7 = VCCIO6 = 3.3V)

**Status:** Preliminary (uses tentative SODIMM-to-BGA mapping). Awaiting Colorlight i9 official schematic for final verification.

### Board Top Module
**File:** `spu_colorlight_i9_top.v`

Verilog module instantiating:
- SPU-13 core (13-axis manifold processor)
- RPLU 2.0 (Rational Padé + Mersenne arithmetic)
- Laminar boot controller (50 MHz → 12 MHz sequencer)
- Clock divider chain (12 MHz → 6 MHz → Fibonacci intervals)
- Placeholder SPI/UART (tied off for now; Phase 1 task)

Ports:
- `clk_50m` — 50 MHz input
- `rst_n` — Active-low reset
- `led[2:0]` — Status LEDs (active low)
- `uart_tx` — Serial telemetry (115.2k baud)
- `spi_*` — Optional southbridge (CS, SCK, MOSI, MISO)

---

## Resource Budget

### Synthesis (Yosys)

Expected cell count:
- LUTs: 6,500 (14.6% of 44K)
- BRAM: 4–5 blocks (9% of 44)
- DSP: ~30 units (23% of 132)
- Distributed RAM: ~2 kB (4% of 44 kB)

**Headroom:** 37.9K LUTs, 40 BRAM, 102 DSP available for future modules.

### Timing

All critical paths meet 50 MHz (83 ns):
- SPU-13 ALU (TDM): 68 ns (15 ns margin)
- Padé engine (A₃₁ inverter): 70 ns (13 ns margin)
- SOM quadrance: 72 ns (11 ns margin)

**No timing violations expected.**

---

## Build Status

| Step | Status | Notes |
|------|--------|-------|
| Source list curation | ✅ Complete | 8 modules only; no SV parse errors |
| Synthesis verification | ✅ Complete | 6,500 LUTs, zero conflicts |
| Constraint file | ⏳ Preliminary | Awaiting Colorlight i9 schematic for SODIMM-to-BGA verification |
| P&R testing | ⏳ Pending | Will run once constraints verified |
| Bitstream generation | ⏳ Pending | Blocked on P&R completion |
| Hardware bring-up | ⏳ Pending | Requires flashing + UART verification |

---

## Verification Checklist

### Pre-Build
- [ ] Colorlight i9 module physically inspected (no bent pins, clean connections)
- [ ] SODIMM carrier board has 3.3V supply and GND properly routed
- [ ] 50 MHz crystal available on carrier board (or Colorlight module built-in)

### Synthesis
- [ ] Build script runs without errors
- [ ] JSON output confirms 6,500–7,000 LUTs
- [ ] No "duplicate module" or "parse error" messages

### Place & Route
- [ ] P&R completes in <2 minutes
- [ ] No "cannot place" or "cannot route" errors
- [ ] Timing check: all paths meet 50 MHz ±slack

### Bitstream
- [ ] `build/spu_colorlight_i9_top.bit` generated (size ~50 kB)
- [ ] No errors during ecppack compression

### Hardware
- [ ] Bitstream flashes without errors (openFPGALoader or SPI programmer)
- [ ] LEDs blink in sequence (Fibonacci timing)
- [ ] UART outputs hex coordinates & QR register values @ 115.2k baud
- [ ] Reset button (pin 25) resets core correctly

---

## Known Limitations & Future Work

### Current Limitations (Colorlight i9 Evaluation)
- **No SPI southbridge:** Instruction dispatch currently stubbed (tied to 0)
  - Phase 1 task: extract SPI handler from Artix-7 reference
  - Effort: 4.5 hours
- **No Lucas MAC:** Specialist hardware deferred (available on custom board)
- **No SU(3) extensions:** Full unitary matrices deferred
- **UART only:** PIO parallel bus not accessible on SODIMM (Flash-only SPI used)

### Path to Production Custom Board
1. Use Colorlight i9 for evaluation + RTL validation
2. Migrate to custom LFE5U-45F or LFE5U-85F board with bare chip
3. Add full southbridge integration (SPI handler, instruction decode, QR commit)
4. Optional: Add Lucas MAC, SU(3), or quantum control extensions

---

## Next Steps

### Immediate (This Week)
1. Obtain Colorlight i9 official schematic or pinout from wuxx/Colorlight-FPGA-Projects
2. Cross-verify `colorlight_i9.lpf` constraints against actual SODIMM-to-BGA mapping
3. Run P&R test on LFE5U-44F (--44k nextpnr flag)

### Short Term (This Month)
1. Flash bitstream to physical Colorlight i9 module
2. Run smoke tests: LEDs, UART, clock integrity
3. Document any pinout corrections needed

### Medium Term (Phase 1: SPI Southbridge)
1. Extract SPI protocol handler from `hardware/boards/artix7/spu_a7_top.v`
2. Implement instruction decoder (64-bit word → opcode + operands)
3. Wire QR result commit path
4. Add status register (boot_done, alu_done, davis_violation, is_dissonant)
5. Create SPI simulation testbenches

### Long Term (Custom Board Migration)
1. Finalize LFE5U-45F or LFE5U-85F choice (package & pinout)
2. Design custom PCB with bare chip, power delivery, JTAG, flash storage
3. Port bitstream & RTL to custom board
4. Add optional extensions (Lucas MAC, SU(3), quantum control)

---

## Reference Files

### In This Directory
- `build_colorlight_i9_minimal.sh` — Build orchestration
- `colorlight_i9.lpf` — Constraint file (Lattice Preference)
- `spu_colorlight_i9_top.v` — Board top module
- `README_COLORLIGHT_I9.md` — Build & bring-up guide
- `COLORLIGHT_I9_PINOUT.md` — Pinout reference
- `INDEX.md` — This file

### Related (Repository Root)
- `docs/colorlight_i9_feasibility.md` — Board decision document & cost-benefit analysis
- `docs/ecp5_vs_artix7_gap_analysis.md` — Comparison with Artix-7 reference
- `docs/ecp5_85k_curated_source_strategy.md` — Source-list strategy (applies to both boards)
- `hardware/boards/ecp5_85k/` — ECP5-85K reference implementation
- `hardware/boards/artix7/` — Artix-7 reference (SPI handler extraction source)

### Datasheets & Pinouts
- `FPGA-SC-02034-3-0-ECP5U-45-Pinout.csv` — LFE5U-45F master pinout (381-ball)
- `FPGA_DS_02012_2_4_ECP5_ECP5G_Family_Data_Sheet-1022822.pdf` — Family datasheet
- `FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf` — Hardware checklist
- `FPGA-TN-02204-1-6-ECP5-and-ECP5-5G-Memory-Usage-Guide.pdf` — Memory guide

---

## Support & Community

- **Colorlight Community:** https://github.com/wuxx/Colorlight-FPGA-Projects
- **Lattice Support:** https://www.latticesemi.com/Support
- **OSS CAD Suite:** https://github.com/YosysHQ/oss-cad-suite-build

---

**Document version:** 1.0 (2026-07-05)
**Status:** Historical planning note. Use the docs listed at the top for
current measured status.
