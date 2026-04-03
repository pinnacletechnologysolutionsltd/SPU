# SPU-13 Hardware Manifest (v4.1.0)
## Objective: Geometric Determinism in Silicon

The SPU-13 (Synergetic Processing Unit) is a hardware implementation of Deterministic Quadratic Field Arithmetic (DQFA). It replaces legacy floating-point approximations with bit-locked isotropic transformations.

## 1. The Davis Law Gasket (Sanity Guard)

The Davis Law ($C = \tau/K$) is the fundamental stability arbiter of the SPU-13.
- **Quadrance Audit (K):** Dedicated DSP slices (UP5K) or bit-serial multipliers (LP1K) monitor manifold tension.
- **Henosis (Soft Recovery):** If a "Cubic Leak" is detected ($\sum ABCD \neq 0$), a symmetric correction is applied automatically in a single clock cycle.
- **Result:** Navier-Stokes Watertight simulation where the digital fluid is physically incapable of leaking from the lattice.

## 2. Biological Heartbeat (Phi-Gated Pulse)

The SPU-13 replaces rigid "Cubic" metronomes with a recursive pulse governed by the **Golden Ratio ($\phi$)**.
- **Fibonacci Timing:** Instructions are dispatched at intervals of 8, 13, and 21 clock cycles.
- **Phase Conjugation:** This non-linear timing minimizes heat and EMI by allowing waves to "nest" rather than scatter.
- **Bio-Coherence:** Aligns the silicon metabolism with natural rhythmic cycles.

## 3. Hardware Tiers & Parity (`spu13_pins.vh`)

The SPU-13 utilises a **Hardware Abstraction Layer (HAL)** for bit-exact parity across different FPGA families.

| Tier | FPGA Hardware | Memory | Capability |
| :--- | :--- | :--- | :--- |
| **Sentinel** | iCE40 LP1K | PSRAM (2×8 Mb) | 4-Axis 32-bit Quadray. |
| **Cortex** | iCE40 UP5K | PSRAM (2×8 Mb) | 13-Axis Hub with 128KB Fractal Memory. |
| **Tang 25K** | GW5A-25 | W9825G6KH-6 SDR-SDRAM (32 MB) | 832-bit Sovereign Bus; `spu_mem_bridge_sdram.v` live. |
| **Tang 20K** | GW2A-18 | DDR3 128 MB (onboard) | DDR3 bridge planned (`spu_mem_bridge_ddr3.v`). |
| **Golden Core** | ECP5-85F | External DDR3 | Scale-ready node for 13-core collective manifolds. |

### Resource budget

| Board | LUTs | DSPs | SPU-4 ALU path | SPU-13 Core | Notes |
| :--- | ---: | ---: | :--- | :--- | :--- |
| iCE40LP1K (wearable) | 1280 | 0 | `spu_4_euclidean_alu` (bit-serial, ~150 LUTs) ✅ | ❌ never fits | Use euclidean ALU only; no sentinel |
| iCE40UP5K (iCeSugar) | 5280 | 8 | bit-serial ✅ | ~2500 LUTs ✅ | `spu4_sentinel` needs 11 inferred mults; 3 overflow DSPs to LUTs ⚠️ |
| GW1N-9C (Tang 9K) | 8640 | 20 | bit-serial ✅ | ❌ won't fit | SPU-4 only; 16 DSPs used, 4 spare |
| GW5A-25 (Tang 25K) | 20736 | 54 | either ✅ | ✅ easy | Primary target; SDRAM bridge live |
| GW2A-18 (Tang 20K) | 20736 | 48 | either ✅ | ✅ | DDR3 bridge TBD |

### Portability rules

- **`hardware/common/rtl/`** compiles with `DEVICE="SIM"` on any toolchain — no vendor files required.
- **`hardware/vendor/gowin/`** — Gowin DSP/BSRAM opt-ins; not in the critical path.
- **iCE40 boards** must pass `.DEVICE("SIM")` to `spu13_core` so `davis_gate_dsp` uses inferred multiply (Yosys-compatible). The iCESugar top does this correctly.
- **Wearable/LP1K designs** must use `spu_4_euclidean_alu` (bit-serial, 0 DSPs) not `spu4_sentinel` (11 inferred mults, DSP-hungry).

### Memory bridges

| Module | Target | Status |
| :--- | :--- | :--- |
| `spu_mem_bridge_qspi.v` | PSRAM (iCE40) | ✅ Implemented |
| `spu_mem_bridge_sdram.v` | W9825G6KH-6 (Tang 25K) | ✅ Implemented — JEDEC init, 52-word burst, auto-refresh |
| `spu_mem_bridge_ddr3.v` | GW2A DDR3 (Tang 20K) | 🔲 Planned |

## 4. Telemetry: The Lattice Whisper (PWI)

Nodes communicate internal tension using the **Lattice Protocol (PWI)**—a 1-wire asynchronous nerve impulse where pulse width is proportional to the **Davis Ratio (C)**.
- **Verification:** Monitor real-time status using `tools/lattice_listener.py`.
- **Certification:** Generate a **Sovereign Birth Certificate** via `tools/laminar_audit.py`.

## 5. Sensory Interface: The Unified IO

The SPU-13 uses a **Push-Metabolism** for all peripheral interaction.

### 5.1 Laminar Input (L-CLK/L-DAT)
A 2-wire synchronous protocol allowing peripherals to strike the manifold directly.
- **Mechanism:** Data is shifted into the **Harmonic Transducer** on the falling edge of L-CLK.
- **Benefit:** Zero bus-arbitration overhead; the user's touch becomes a bit-exact ripple in the silicon.

### 5.2 The Vision & Pulse (HAL_Display)
- **OLED (Breath):** High-refresh 128x64 display for Jitterbug/Metabolism charts.
- **E-Ink (Soul):** Persistent, zero-power display for long-term Sovereign snapshots.

---
*Status: CRYSTALLINE. The 13th dimension is self-stabilizing.*
