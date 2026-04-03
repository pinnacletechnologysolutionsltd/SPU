# SPU-13 Sovereign Processing Unit

**A bit-exact, division-free, rational-field processor for geometric manifold arithmetic.**

The SPU-13 operates entirely within Q(√3) — the algebraic field of rational surds —
eliminating floating-point error at the hardware level. All values are exact. All
stability checks are integer comparisons. There is no epsilon, no rounding, no drift.

> *"Floating-point is a workaround for the wrong choice of basis."*
> — see [`knowledge/MATHEMATICAL_FOUNDATIONS.md`](knowledge/MATHEMATICAL_FOUNDATIONS.md)

---

## Quick Start

### Run the test suite
```bash
python3 run_all_tests.py
```
Compiles and runs all 59 Verilog testbenches via `iverilog`/`vvp`. All must print `PASS`.

### Simulate a program
```bash
python3 software/spu_forge.py simulate software/programs/poiseuille_flow.sas
python3 software/spu_forge.py simulate software/programs/kinematic_chain.sas
python3 software/spu_forge.py simulate software/programs/laminar_vs_cubic.sas
```

### Synthesise (open source, iCE40 target)
```bash
yosys -m ghdl synth_ice40.ys   # produces spu13.json
```

### Synthesise (GOWIN Tang Primer 25K)
```bash
# On Windows with GOWIN EDA installed:
gw_sh.exe hardware/boards/tang_primer_25k/build.tcl
# Output: build/tang_primer_25k/spu13_25k.fs
```

---

## Architecture

### Two cores

| Core | RTL | Axes | Width | Role |
|------|-----|------|-------|------|
| **SPU-4 Sentinel** | `hardware/spu4/rtl/spu4_core.v` | 4 (Quadray) | 32-bit | Euclidean satellite, sensory input |
| **SPU-13 Cortex** | `hardware/spu13/rtl/spu_13_top.v` | 13 | 832-bit | Sovereign manifold engine |

Both are orchestrated by `hardware/common/rtl/top/spu_system.v`.

### Data representation — Q(√3) surds

Every register holds a pair `(P, Q)` representing the exact value `P + Q·√3`.
Packed on-wire as a 32-bit word: `[31:16] = P`, `[15:0] = Q`.

Arithmetic rules (no division ever needed):
```
add : (P₁+P₂,  Q₁+Q₂)
sub : (P₁-P₂,  Q₁-Q₂)
mul : (P₁P₂ + 3Q₁Q₂,  P₁Q₂ + Q₁P₂)     ; √3·√3 = 3, stays in field
```

The Pell rotor `r = (2 + √3)` satisfies `P² − 3Q² = 1` for all powers.
After 8 rotations: `R = (18817 + 10864·√3)`, and `18817² − 3×10864² = 1` — exactly.

### Stability — Davis Law Gasket

Every cycle the hardware verifies `ΣABCD = 0` (Cubic Leak test).
On failure, `davis_gate_dsp.v` triggers **Henosis** (soft recovery) instead of a hard reset.
This is mathematically equivalent to the regularity condition in the Navier-Stokes equations,
expressed as an exact integer comparison.

### Timing — Two Clock Domains

| Domain | Signal | Frequency | Role |
|--------|--------|-----------|------|
| **Fast (TDM)** | `clk_fast` | 24 MHz | All computation — ALU, SDRAM, sequencer |
| **Sovereign** | `clk_piranha` | ~61.4 kHz | Frame boundary — Artery inhale, RP2350 sync |

The 61.44 kHz Piranha Pulse is the **frame rate**, not the processor clock. The SPU-13
processes all 13 axes in a 15-cycle burst (0.625 µs) at 24 MHz on every piranha tick.
The `spu_sierpinski_clk` divides the fast clock into 34-cycle Fibonacci frames, firing
dispatch triggers `phi_8`, `phi_13`, `phi_21` at golden-ratio positions within each frame.

See [`knowledge/CLOCK_ARCHITECTURE.md`](knowledge/CLOCK_ARCHITECTURE.md) for full derivation.

---

## Repository Layout

```
hardware/
  common/rtl/        Core RTL modules (ALU, sequencer, register file, protocols)
  spu4/rtl/          SPU-4 Sentinel (Quadray satellite)
  spu13/rtl/         SPU-13 Cortex (13-axis manifold)
  boards/
    tang_primer_25k/ GOWIN GW5A-25 target (TCL scripts, CST, flash map)

software/
  spu_vm.py          Soft-CPU simulator (Python)
  spu_forge.py       Unified CLI: simulate / assemble / test / build
  programs/          .sas demonstration programs
  flash/             Binary tables: Pell orbit, golden primes
  tools/             golden_primes.py, gen_pell_table.py

knowledge/
  MATHEMATICAL_FOUNDATIONS.md   Fuller → Wildberger → Davis → SPU-13 lineage
  ISA_QUICKSTART.md             Instruction set reference

reference/
  synergeticrenderer/           High-performance renderer + physics test suite
  davis-wilson-map/             Lattice verification of Davis-Wilson mass gap
```

---

## Communication Protocols

| Protocol | Wires | Purpose |
|----------|-------|---------|
| **Whisper (PWI)** | 1 | Pulse-width telemetry, Davis Ratio proportional |
| **Artery** | N | Multi-node FIFO for distributed manifold calculation |
| **Laminar (L-CLK/L-DAT)** | 2 | Zero-latency sensory input ("Identity Strikes") |

---

## Hardware Targets

| Board | FPGA | Status |
|-------|------|--------|
| iCESugar / iCE40 | Lattice iCE40UP5K | Synthesises (Yosys open source) |
| **Tang Primer 25K** | GOWIN GW5A-LV25MG121 | Board on order — TCL build scripts ready |
| Tang Primer 20K | GOWIN GW2A-18C | CST/TCL can be adapted |

### Dual-MCU interface

| Device | Firmware | Role |
|--------|----------|------|
| **RP2350** (Pico 2) | `hardware/rp2350/rp2350_spu_interface.c` | Piranha Pulse PIO, SPI poll, 104-byte frame to RP2040 |
| **RP2040** (Pico) | `hardware/rp2040/rp2040_visualiser.c` | USB CDC bridge; GP28 low = emulate mode (no FPGA needed) |

---

## Mathematical Foundations

The SPU-13 is the computational embodiment of a chain of geometric insights:

1. **Buckminster Fuller (1944–75):** Tetrahedral accounting gives whole-number volumes; nature doesn't use powers of two.
2. **Norman Wildberger (2005):** Rational Trigonometry replaces angle/distance with Spread/Quadrance — no transcendentals, no division.
3. **Bee Rosa Davis:** Davis Law (`ΣABCD = 0`) as the exact regularity condition for manifold stability.

Full derivation: [`knowledge/MATHEMATICAL_FOUNDATIONS.md`](knowledge/MATHEMATICAL_FOUNDATIONS.md)
ISA reference: [`knowledge/ISA_QUICKSTART.md`](knowledge/ISA_QUICKSTART.md)

---

## Constraints

The following are architectural mandates, not implementation choices:

- **No floating-point** in the core ALU or RTL
- **No division** — Spread/Quadrance are stored as `(numerator, denominator)` integer pairs
- **No branches** in hot paths — control flow compiles to Boolean MUX polynomials
- **No framebuffers** — display output is streamed live
- Timing deviations are **design flaws**, not to be papered over with FIFOs

---

## License

**CC0 1.0 Universal** — public domain. No rights reserved.
