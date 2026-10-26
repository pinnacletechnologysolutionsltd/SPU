# ECP5-85K Curated Source Strategy

**Date:** 2026-07-06
**Status:** Synthesis, P&R, and bitstream packaging verified for the current
minimal placeholder target.

## Problem Statement

The original ECP5 build script (`build_ecp5_85k.sh`) pulled the entire `hardware/rtl/` tree via recursive `find`, which created:
1. **Module redefinitions** — same module defined in multiple places (optional stubs + core definitions)
2. **Vendor primitive conflicts** — Gowin/Xilinx/ECP5 prims all defining the same symbols
3. **SystemVerilog parse errors** — Yosys read_verilog rejecting SV syntax (jets, phslk, som_classify)

## Solution: Minimal Curated Source List

Instead of globbing the entire RTL forest, define **exactly which modules the board actually needs** via dependency tracing.

### Dependency Tree Analysis

**spu_ecp5_top** → instantiates → **spu13_top**

**spu13_top** → instantiates:
- `spu_laminar_boot` (SPI boot controller)
- `spu_node_link` (SPU-4 satellite link)
- `spu_rotor_vault` (Pell rotor state machine)
- `spu_unified_alu_tdm` (TDM ALU core)
- `spu13_berry_gate` (geometric transform)
- `spu13_janus_mirror` (dual-polarity reflection)

### Curated Source List (8 files)

```verilog
// Board top-level
hardware/boards/ecp5_85k/spu_ecp5_top.v

// SPU-13 core
hardware/rtl/core/spu13/spu13_top.v

// Direct dependencies
hardware/rtl/top/spu_laminar_boot.v
hardware/rtl/peripherals/io/spu_node_link.v
hardware/rtl/core/shared/spu_rotor_vault.v
hardware/rtl/core/shared/spu_unified_alu_tdm.v
hardware/rtl/core/spu13/spu13_berry_gate.v
hardware/rtl/core/spu13/spu13_janus_mirror.v

// Architecture
hardware/rtl/arch/spu_optional_stubs.v
```

### Verilog-2005 Compatibility Check

All 8 files are **Verilog-2005 compatible** (no unpacked arrays, logic keyword, or SV literals):
- ✓ spu_ecp5_top.v
- ✓ spu13_top.v
- ✓ spu_laminar_boot.v
- ✓ spu_node_link.v
- ✓ spu_rotor_vault.v
- ✓ spu_unified_alu_tdm.v
- ✓ spu13_berry_gate.v
- ✓ spu13_janus_mirror.v

This eliminates the need for SV-heavy modules (spu13_jet_mac, spu13_phslk_core, spu13_som_classify), which are not instantiated by the minimal ECP5 tree.

## New Build Script

**File:** `hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh`

**Features:**
- Explicit source list (no globs or recursive finds)
- Supports three steps: `synth`, `pnr`, `all`
- No vendor prim conflicts
- No module redefinitions

**Usage:**
```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh synth  # Yosys only
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh pnr    # Nextpnr only
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh all    # Full build
```

## Build Results

The curated placeholder target now completes the full open ECP5 flow:

```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh synth
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh pnr
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh bitstream
```

Measured on 2026-07-06:

| Resource | Result |
|---|---:|
| Total LUT4 before packing | 293 / 83,640 |
| Logic LUT4 | 261 |
| Carry LUT4 | 32 |
| TRELLIS_FF | 97 / 83,640 |
| DP16KD BRAM | 0 / 208 |
| MULT18X18D DSP | 0 / 156 |
| Timing | 273.00 MHz max on `$glbnet$clk_12mhz_int`, PASS at 50 MHz |
| Packaged bitstream | `build/spu_ecp5_top.bit` (278 KiB) |

Warnings observed and accepted for this placeholder target:

- Undriven ALU wires inside the tied-off placeholder integration path.
- `flash_clk_o` is unconstrained for P&R metrics because the dedicated
  CCLK-style path needs a proper ECP5 configuration-clock/USRMCLK treatment.
- No "Re-definition" errors.
- No SV parse failures.

## Artix-7 Independence

This ECP5 strategy does **not affect** the existing Artix-7 build:
- Artix flow (`hardware/boards/artix7/synth_a7.ys`) already uses a curated source list
- Both flows now follow the same principle: explicit module declaration per target

## Next Steps

1. **Functional completion:** Add missing ECP5 I/O logic (PIO, SPI
   southbridge) to `spu_ecp5_top.v`.
2. **RPLU2 migration:** Decide whether the ECP5-85F target should use the i9
   RPLU2 probe source list or remain a minimal placeholder until hardware
   exists.
3. **Flash-clock hardening:** Replace unconstrained CCLK-style flash clock
   placeholders with a proper ECP5 configuration/user-clock strategy.
4. **Cross-validation:** Confirm the Artix-7 RPLU2PADE and SU3SHARE flows
   still synthesize from clean source after ECP5 changes.

---

**Key Takeaway:** Curated source lists (not recursive globs) prevent redefinitions, vendor conflicts, and unnecessary SV parsing. This is the scalable approach for multi-board RTL projects.
