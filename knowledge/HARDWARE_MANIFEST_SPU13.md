# SPU-13 Hardware Manifest (v4.1.0)

> **STALE — verified 2026-07-16, do not use as a current source of truth.**
> Last substantive edit was 2026-04-07; the active tree has diverged
> significantly since. Specifically verified wrong or nonexistent as of
> this note: the board tier table (§3) describes a 6-tier ladder (Tang
> Nano 1K, iCESugar, Tang Nano 9K, Tang Primer 20K, Tang 25K, Gowin Mega)
> against build scripts/directories that don't exist anywhere in the repo
> (`build_gw1n1.sh`, `build_icesugar.sh`, `build_25k.sh`,
> `hardware/boards/tang_nano_9k/`, `hardware/boards/tang_primer_20k/`,
> `hardware/boards/gowin_mega/`) — the current board set is only
> `hardware/boards/{artix7,colorlight_i9,ecp5_85k,tang_primer_25k}/`, and
> the Tang 25K path is now many narrowly-scoped `build_25k_spu13_*_probe.sh`
> scripts, not one monolithic full-core build. The "post-route Fmax
> 140.83 MHz" full-core figure (§3, target ladder row 5) appears nowhere
> else in the repository. §4's `tools/lattice_listener.py` and
> `tools/laminar_audit.py` do not exist. For current board roles and
> capability, see `AGENTS.md` and `docs/SPIN_CATALOG.md`. §1-2's
> unprovable physics/biology claims (Navier-Stokes leak-proofing, heat/EMI
> reduction via "phase conjugation", "bio-coherence") were removed
> 2026-07-16 per John's direction — the Davis Gate and Fibonacci-dispatch
> mechanisms themselves are real and documented accurately elsewhere
> (`AGENTS.md`, `CLAUDE.md`), only the unfounded framing was cut. §§4-5
> (Lattice Whisper telemetry, sensory interface) have not been
> re-verified either way and are left as-is pending a decision on
> rewrite scope.

## Objective: Geometric Determinism in Silicon

The SPU-13 (Synergetic Processing Unit) is a hardware implementation of Deterministic Quadratic Field Arithmetic (DQFA). It replaces legacy floating-point approximations with bit-locked isotropic transformations.

## 1. The Davis Law Gasket (Sanity Guard)

The Davis Law ($C = \tau/K$) is the fundamental stability arbiter of the SPU-13.
- **Quadrance Audit (K):** Dedicated DSP slices (UP5K) or bit-serial multipliers (LP1K) monitor manifold tension.
- **Henosis (Soft Recovery):** If a "Cubic Leak" is detected ($\sum ABCD \neq 0$), a symmetric correction is applied automatically in a single clock cycle.
- **Result:** An exact zero-test on $\sum ABCD$ every cycle — not an epsilon
  comparison — so a nonzero sum is caught and corrected the same cycle it
  occurs, rather than being allowed to accumulate.

## 2. Fibonacci-Gated Dispatch (Phi-Gated Pulse)

The SPU-13 replaces rigid "Cubic" metronomes with dispatch timing governed by the **Golden Ratio ($\phi$)**.
- **Fibonacci Timing:** Instructions are dispatched at intervals of 8, 13, and 21 clock cycles. This is a deliberate design constraint on instruction cadence, not an optimization target.

(Earlier drafts of this section claimed heat/EMI reduction via "phase
conjugation" and a "bio-coherence" effect aligning "silicon metabolism"
with biological rhythms. Neither claim has ever been measured or tested,
and both are removed as of 2026-07-16 — see `docs/SPU13_IDENTITY_AND_BOUNDARIES.md`'s
caution against claiming exact continuous-physics or biological effects
without evidence.)

## 3. Hardware Tiers & Parity (`spu13_pins.vh`)

The SPU-13 utilises a **Hardware Abstraction Layer (HAL)** for bit-exact parity across different FPGA families.

| Tier | FPGA Hardware | Memory | Capability |
| :--- | :--- | :--- | :--- |
| **Sentinel** | iCE40 LP1K | PSRAM (2×8 Mb) | 4-Axis 32-bit Quadray. |
| **Cortex** | iCE40 UP5K | PSRAM (2×8 Mb) | 13-Axis Hub with 128KB Fractal Memory. |
| **Tang 25K** | GW5A-25 | W9825G6KH-6 SDR-SDRAM (32 MB) | 832-bit Sovereign Bus; `spu_mem_bridge_sdram.v` live. |
| **Tang 20K** | GW2A-18 | DDR3 128 MB (onboard) | DDR3 bridge planned (`spu_mem_bridge_ddr3.v`). |
| **Golden Core** | ECP5-85F | External DDR3 | Scale-ready node for 13-core collective manifolds. |

### Target ladder

| Tier | Board | Chip | LUT | DSP | Build script | Status | Notes |
| :---: | :--- | :--- | ---: | ---: | :--- | :---: | :--- |
| 1 Micro | Tang Nano 1K | GW1NZ-1 | 1,152 | 0 | `build_gw1n1.sh` | ✅ bitstream | Whisper Beacon — `spu4_euclidean_alu` + BSRAM seed; **~206 LUT (18%)** |
| 2 Small | iCESugar v1.5 | iCE40UP5K | 5,280 | 8 | `build_icesugar.sh` | ✅ bitstream | SPU-4 Sentinel (2-stage pipeline); **4,026 LUT, 48 MHz** |
| 3 Mid-Small | Tang Nano 9K | GW1N-9C | 8,640 | 20 | `hardware/boards/tang_nano_9k/synth_gowin_9k.ys` | ✅ synth | SPU-4 core; **671 LUT + 1636 ALU (26.9%), 5/20 DSP** |
| 4 Mid | Tang Primer 20K | GW2A-18 | 18,432 | 48 | `hardware/boards/tang_primer_20k/synth_gowin_20k.ys` | ✅ synth | SPU-13 capable; **28.7% LUT, 14/48 DSP**; DDR3 bridge TBD |
| 5 Large | Tang Primer 25K | GW5A-25A | 20,736 | 54 | `build_25k.sh` | ✅ bitstream | SPU-13 full core; **post-route Fmax 140.83 MHz** |
| 5b RPLUv2 | Tang Primer 25K | GW5A-25A | 20,736 | 54 | `build_25k.sh --rplu2` | 🔲 planned | SPU-13 + RPLU v2 pipeline; **est. ~10,600 LUT + 41 DSP** |
| 6 Mega | Gowin Mega | GW5AST-138C | ~138K | 340 | `hardware/boards/gowin_mega/synth_gowin_mega.ys` | 🏗 stub | 8× SPU-13 cluster planned; `spu_mega_top.v` placeholder |

### Resource budget detail

| Board | LUT (actual) | DSP used | Core path | Fmax | Memory |
| :--- | ---: | ---: | :--- | ---: | :--- |
| GW1NZ-1 | **~206** of 1,152 (18%) | 0 | `spu4_euclidean_alu` bit-serial | +31 ns slack at 27 MHz | 72KB BSRAM onboard |
| GW1N-9C | **671 LUT + 1636 ALU** of 8,640 (26.9%) | 5/20 | `spu4_core` + sentinel | — (PnR TBD) | 8MB PSRAM onboard |
| GW2A-18 | **~5,300** of 18,432 (28.7%) | 14/48 | `spu13_top` full core | — (PnR TBD) | 128MB DDR3 onboard |
| iCE40UP5K | **4,026** of 5,280 (76%) | 8 SB_MAC16 | `spu4_sentinel` v1.3 (2-stage pipe) | **48 MHz** | QSPI PSRAM (PMOD) |
| GW5A-25A | **~8,500** of 20,736 (41%) | 29 | `spu13_top` full core | **140.83 MHz** | 64MB XSDS SDRAM |
| GW5AST-138C | ~1 (stub) | 0 | Placeholder | — | — |

### SPU-4 topology: nano sentinel vs. cluster co-processor

The SPU-4 has two distinct deployment roles, each with its own arithmetic path:

| Property | Nano / Standalone | Cluster Co-processor |
| :--- | :--- | :--- |
| Module | `spu4_euclidean_alu.v` | `spu4_sentinel.v` |
| Arithmetic | Bit-serial, 1 DSP, ~150 LUTs | Combinatorial, 11 DSPs, ~48-bit intermediates |
| Fixed-point | Q8.8 (16-bit) | Q12 (16-bit) |
| Overflow guard | **Phi-fold** — 18-bit accumulator; if sum overflows 16 bits, arithmetic `>>1` or `>>2` (Fibonacci descent). `henosis_pulse` output. | **Davis Law Henosis** — when `nQ > 2 × quadrance_seed` (true runaway, not drift), fold B/C/D axes via signed `>>>1`. `henosis_pulse` output. |
| Drift monitor | n/a (single-shot circulant) | `janus_stable` (±4 LSB quadrance), separate from fold threshold |
| Topology | Standalone sensory unit; no SPU-13 dependency | Rotation fidelity tester; feeds manifold to SPU-13 |
| Target boards | GW1NZ-1 (Tang Nano 1K), iCE40UP5K (iCESugar), GW1N-9C (Tang 9K) | Tang 25K, Tang 20K alongside SPU-13 |

**Why two thresholds in the sentinel?**
`janus_stable` (±4 LSB) is a *precision monitor* — it reports whether the rational rotation is bit-exact. Henosis (2× seed) is a *safety net* — it fires only if the manifold has genuinely grown out of range (e.g., coefficient overflow). The tight monitor should not trigger fold, as that would corrupt the rotation sequence.

### Toolchain

**Verified with oss-cad-suite 2026-04-06** (yosys 0.63+190, nextpnr 0.10-25-g25482d99, apycula with GW5A-25A.msgpack.xz).  YRabbit's GW5A additions (HCLK system, CLKDIV, IDES4/OSER4 deserializers) are all present.

### Portability rules

- **`hardware/common/rtl/`** compiles with `DEVICE="SIM"` on any toolchain — no vendor files required.
- **`hardware/vendor/gowin/`** — Gowin DSP/BSRAM opt-ins; not in the critical path.
- **iCE40 boards** must pass `.DEVICE("SIM")` to `spu13_core` so `davis_gate_dsp` uses inferred multiply (Yosys-compatible). The iCESugar top does this correctly.
- **Wearable/LP1K designs** must use `spu4_euclidean_alu` (bit-serial, 0 DSPs) not `spu4_sentinel` (11 inferred mults, DSP-hungry).

### RPLU v2 — Thimble-Padé Pipeline (A₃₁ over M31)

The RPLU has been redesigned from Morse-potential lookup tables to a full A₃₁
rational arithmetic pipeline over the Mersenne prime M31 (p = 2^31−1).

| Module | Function | LUTs (est) | DSPs |
|:---|:---|:---|:---|
| `spu13_m31_multiplier.v` | A₃₁ multiplier, 16 parallel 32×32→DSP, fast Mersenne reduction | ~600 | 16 |
| `spu13_m31_inverter.v` | BEEA scalar modular inverter, division-free | ~200 | 0 |
| `spu13_fp4_inverter.v` | Conjugate reduction tower, ~76-cycle A₃₁ inversion | ~400 | 0 |
| `spu_btu_collision_resolver.v` | 64→6 priority encoder + backlog queue | ~180 | 0 |
| `spu13_btu_core_top.v` | BTU spatial→A₃₁ router, 4-lane BRAM | ~50 | 0 |
| `rplu_thimble_pade.v` | [4/4] Padé Horner evaluator + coefficient storage | ~350 | 0 |
| `spu_som_node.v` ×7 | Individual SOM node, 3-stage quadrance pipeline | ~700 | 0 |
| `spu_som_node_array.v` | Parallel array with WTA comparator tree | ~250 | 0 |
| `spu13_multi_port_regfile.v` | 4R2W register file with write-forwarding bypass | ~400 | 0 |
| `rplu_pipeline.v` | 4-stage pipeline top | ~100 | 0 |
| **Total** | | **~3,230** | **16** |

Resource comparison with legacy RPLU (Morse potential, `rplu_exp.v` + `rplu_skel.v`):
- LUTs: 3,230 vs ~1,100 (+2,130) — trades area for deterministic field arithmetic + parallel SOM
- BRAMs: 8 vs 6–8 (parity — Morse tables become BTU lanes + Padé coeffs)
- DSPs: 16 vs 4 (+12) — the A₃₁ multiplier's 16 parallel products dominate

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
