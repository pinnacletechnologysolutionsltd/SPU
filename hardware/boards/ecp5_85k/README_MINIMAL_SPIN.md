# ECP5-85K Minimal Spin (SPU-13 + RPLU 2.0)

**Status:** Synthesis verified ✓ | P&R pending | Hardware testing pending

## Overview

This is a minimal evaluation board configuration targeting the **ECP5-85F** FPGA. It includes:
- **SPU-13 Core** (13-axis rational field processor)
- **RPLU v2.0** (Thimble-Padé rational approximant engine)

Deliberately excluded for this spin:
- **Lucas MAC** (specialist Phinary arithmetic)
- **SU(3) extensions** (specialist unitary operations)
- **Jet MAC** and PHSLK (complex SystemVerilog, not needed for eval board)
- **SOM Classify** (classifier, deferred)

## Build Instructions

### Prerequisites
- Yosys (from OSS CAD Suite)
- Nextpnr (with ECP5 support)
- Ecppack
- openFPGALoader (for hardware programming)

### Step 1: Synthesis
```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh synth
```
Output: `build/spu_ecp5_top.json`

Expected warnings:
- Undriven wires (ALU control signals are tied off in spu_ecp5_top placeholder)
- No module redefinitions or SV parse errors

### Step 2: Place & Route
```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh pnr
```
Output: `build/spu_ecp5_top_out.config`

### Step 3: Bitstream Generation
```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh all
```
Output: `build/spu_ecp5_top.bit`

## Curated Source List

The build uses an **explicit, minimal source list** (no glob wildcards):

```
hardware/boards/ecp5_85k/spu_ecp5_top.v           (top-level)
hardware/rtl/core/spu13/spu13_top.v               (core)
hardware/rtl/top/spu_laminar_boot.v               (SPI boot controller)
hardware/rtl/peripherals/io/spu_node_link.v       (SPU-4 link)
hardware/rtl/core/shared/spu_rotor_vault.v        (Pell rotor state)
hardware/rtl/core/shared/spu_unified_alu_tdm.v    (TDM ALU)
hardware/rtl/core/spu13/spu13_berry_gate.v        (geometric transform)
hardware/rtl/core/spu13/spu13_janus_mirror.v      (dual-polarity reflection)
hardware/rtl/arch/spu_optional_stubs.v            (optional stubs)
```

This approach:
- ✓ Avoids module redefinitions (no optional stub + core definition conflicts)
- ✓ Prevents vendor prim conflicts (no Gowin/Xilinx/ECP5 prim symbol clashes)
- ✓ Enables Verilog-2005 parsing (all modules SV-free)
- ✓ Keeps Artix-7 RPLU2LIVE unaffected

See `docs/ecp5_85k_curated_source_strategy.md` for detailed rationale.

## I/O Pinout

See `spu_ecp5_85k.cst` for complete CABGA381 constraints.

Key signals:
- **Clock:** 50 MHz on pin E2 (PULL_MODE=NONE required)
- **Reset:** Pin R1 (active high, internal pull-up)
- **LEDs:** L6, E8, D7 (active low)
  - LED0: uart_tx (boot/ALU telemetry)
  - LED1: piranha_pulse (clock/heartbeat)
  - LED2: alu_done (computation done flag)
- **Telemetry UART:** Pin B11 @ 115,200 baud
- **Host UART:** Pin C3 (RP2350 interface, placeholder)
- **SPI Flash:** J4 bottom row (CS=G10, SCK=D10, MOSI=C10, MISO=B10)

## spu_ecp5_top.v Status

**Current:** Placeholder integration
- Instantiates spu13_top
- Clock divider: simple /4 to 12.5 MHz (TODO: proper PLL)
- Southbridge SPI/PIO: tied off (TODO: implement RP2350 interface)
- ALU control: tied off (TODO: wire from southbridge)

**To finish ECP5 board:**
1. Implement clock PLL for 12 MHz
2. Implement RP2350 SPI southbridge protocol
3. Wire ALU start/opcode/alu_done from southbridge to spu13_top
4. Implement UART mux (select between boot telemetry and user streams)

## Testing Strategy

See `hardware/boards/ecp5_85k/SMOKE_TESTS.md` for:
- Simulation-based smoke tests (boot SPI, ALU functional vectors, rotor handshake)
- Hardware smoke test plan (LED blink, UART readback, flash readback)
- Expected results

## Performance Targets

- **Clock frequency:** 50 MHz (ECP5 timing-grade 8)
- **Target density:** ~40% LUT utilization (minimal spin should be ~30K LUTs)
- **Rotor vault latency:** 6 cycles (rotation pipeline)
- **ALU TDM cycle time:** 6-8 cycles per operation

## Next Steps

1. **P&R:** Run nextpnr, resolve any timing/routing issues
2. **Simulation:** Run smoke testbenches (spu_laminar_boot_tb, spu_unified_alu_tdm_tb)
3. **Bitstream:** Generate .bit file
4. **Hardware validation:** Flash ECP5, verify LEDs, UART, SPI flash readback
5. **Functional tests:** Run full ISA testbenches on hardware (if UART/debugger available)

## References

- `docs/ecp5_85k_report.md` — Initial ECP5 board assessment
- `docs/ecp5_85k_curated_source_strategy.md` — Build strategy and dependency analysis
- `hardware/boards/artix7/synth_a7.ys` — Artix-7 curated source list (similar pattern)
- `knowledge/isa_reference.md` — Full SPU-13 ISA

---

**Last updated:** 2026-07-05
**Author:** Copilot CLI (SPU-13 team)
