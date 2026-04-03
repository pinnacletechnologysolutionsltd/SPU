# SPU-13 Sovereign Processing Unit — Hardware Platform Specification
## Tier Ladder v1.0

**License:** CC0 1.0 Universal (Public Domain)

---

## Overview

The SPU-13 is a bit-exact, rational-field **Q(√3)** algebraic co-processor designed for
high-precision manifold calculations and 60-degree resonance graphics. It is implemented
as a pipelined FPGA soft-core targeting Gowin devices.

This document defines the five-tier hardware deployment ladder from software simulation
to custom silicon, with board-specific constraints, capabilities, and status.

---

## The Five Tiers

### Tier 0 — Software VM *(Available Now)*
**Platform:** Any machine with Python 3.x  
**Core:** Pure-Python SPU-13 VM (`software/spu_vm.py`)  
**Purpose:** Community on-ramp, ISA development, algorithm verification

| Property | Value |
|----------|-------|
| ISA | v1.2 (all 23 opcodes) |
| Precision | Arbitrary (Python integers) |
| Assembler | `spu13_asm.py` v3.0 |
| Verification | 10/10 tests pass |
| Toolchain | Python ≥ 3.8, no dependencies |

**Status:** ✅ Production-ready. Runs all `.sas` programs including VE, Jitterbug, Pell sequences.

---

### Tier 1 — Tang Nano 9K *(First Silicon Target)*
**Device:** Gowin GW1NR-9 (9K LUT, iCE40-class density, 22nm)  
**Board:** Sipeed Tang Nano 9K (~$15 USD)  
**Core:** SPU-4 Sentinel (`spu_nano_core.v` / `spu_light_core.v`)

| Property | Value |
|----------|-------|
| Core width | 32-bit RationalSurd (16-bit P + 16-bit Q) |
| Registers | 4-axis Quadray (A,B,C,D) |
| On-board RAM | 4MB PSRAM (HAL_PSRAM already written) |
| Display | HDMI built-in (no PMOD needed) |
| Connectivity | USB-C, UART |
| Toolchain | nextpnr-gowin (OSS) or Gowin EDA Education Edition |
| Constraints | CST format (`hardware/boards/tang_nano_9k/tang_nano_9k.cst`) |

**Key modules:** `spu4_core.v`, `spu_unified_alu_tdm.v`, `spu_davis_gate.v`,
`spu_bresenham_killer.v`, `HAL_Native_Hex.v`, `spu_sdf_edge.v`

**Status:** 🔶 RTL ready. Awaiting board. First task: smoke ladder (blinky/UART/flash → SPU-4).

---

### Tier 2 — Tang Primer 20K *(SPU-13 with Integrated DDR3)*
**Device:** Gowin GW2A-18 (20K LUT, DSP blocks, 55nm)  
**Board:** Sipeed Tang Primer 20K (~$20 USD)  
**Core:** SPU-13 Cortex (`spu13_core.v`)

| Property | Value |
|----------|-------|
| Core width | 832-bit Collective Manifold (13 × 64-bit Quadray lanes) |
| Registers | 13-axis, 832-bit |
| On-board RAM | 128MB DDR3 (Winbond W9825G6KH) |
| Display | HDMI via PMOD |
| DSP | MULT18X18 / ALU54D (replaces SB_MAC16) |
| Toolchain | Gowin EDA (required for DSP primitive access) |

**Key modules:** `spu13_core.v`, `HAL_SDRAM_Winbond.v`, `spu_gpu_top.v`,
`spu_fragment_pipe.v`, `spu_rasterizer.v`, `spu_fluid_solver.v`

**Memory layout (128MB DDR3):**
- `0x00000000–0x00FFFFFF` — Pell/prime lookup tables (16MB)
- `0x01000000–0x03FFFFFF` — Synergetic Buffer / world geometry (48MB)
- `0x04000000–0x07FFFFFF` — Fractal-compressed manifold archive (64MB)

**Status:** 🔶 RTL ready. Awaiting board. DSP primitive rewrite (`gowin-dsp` todo) required for synthesis.

---

### Tier 3 — Tang Primer 25K *(Development Flagship)*
**Device:** Gowin GW5A-25 (25K LUT, 22nm, newest architecture)  
**Board:** Sipeed Tang Primer 25K (~$25 USD) + 64MB SDRAM PMOD  
**Core:** SPU-13 Cortex (`spu13_core.v`) — same RTL as Tier 2

| Property | Value |
|----------|-------|
| Core width | 832-bit (same as Tier 2) |
| External RAM | 64MB SDRAM via PMOD (`HAL_SDRAM_Winbond.v`) |
| PMODs | 3× available (SD card, display, expansion) |
| Process | 22nm — lowest power of the ladder |
| Toolchain | nextpnr-gowin (Apicula) + Gowin EDA |
| Scott Casper contact | GW5A-25 confirmed "fully in production" |

**Recommended use:** Primary development board. SDRAM PMOD provides equivalent
memory to Tier 2. Three PMODs allow simultaneous SD card + display + SPU bus.

**Status:** 🔶 Top file written (`spu_tang_top.v`). SDRAM bridge (`sdram-bridge` todo) required.
**Availability:** Edge Electronics, Future Electronics, Mouser (per Gowin rep Scott Casper).

---

### Tier 4 — Custom Silicon *(Future)*
**Target:** TSMC 22nm ULP or equivalent  
**Core:** SPU-13 hardened (remove FPGA scaffolding, fix DSP widths to exact Q(√3) needs)

| Property | Value |
|----------|-------|
| Target clock | 500 MHz+ (vs ~100 MHz FPGA) |
| Power | Sub-100mW (Ephemeralization — no framebuffers, no FPU) |
| ALU | True rational-field hardware multiplier, no DSP packing |
| Memory | On-die Laminar RAM (fractal addressing) |
| I/O | SovereignBus v1.0 hardened |

**Status:** 📋 Planned. RTL must be fully validated on Tier 1–3 before tapeout.

---

## Cross-Tier RTL Portability

All 113 `.v` modules in `hardware/common/rtl/` are verified **Gowin-portable**:

- ✅ Zero `SB_*` iCE40 primitives in synthesis path (3 files fixed/skipped)
- ✅ All rotors verified: SQR permutation, Thomson circulant, Cross-rotor, Phi-scaler
- ✅ Graphics pipeline verified: Bresenham Killer v2.0, HAL_Native_Hex v2.0, SDF Edge
- ✅ LatticeSnap parity confirmed: hardware ≡ Metal reference (8/8 tests)
- ⚠️ One DSP file pending: `spu_rational_mul.v` uses `SB_MAC16` — requires `MULT18X18` rewrite

## SovereignBus v1.0 Interconnect

All tiers share a common interconnect protocol:

```
Master (CPU/RP2040) → SPU via L-CLK / L-DAT (2-wire synchronous)
SPU telemetry      → Master via PWI (1-wire, pulse-width = Davis Ratio C)
Display            → HAL_Cartesian (ST7789 SPI) or HAL_Native_Hex (HDMI)
Storage            → HAL_SDCard_SPI (PMOD) or HAL_SDRAM_Winbond (direct)
```

## Timing Mandate

All tiers are phase-locked to the **61.44 kHz Piranha Pulse**:
- Display refresh rate: 61.44 kHz / (RES_X × RES_Y) pixels/sec
- Fibonacci soft-start: 8 → 13 → 21 → 34 cycles (`spu_soft_start.v`)
- Lattice snap cooling: 64-unit grid, convergence in ≤32 cycles at `temp_scale=1`

---

*SPU-13 Sovereign Processing Unit — CC0 1.0 Universal — Public Domain*
