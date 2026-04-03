# SPU-13 Sovereign Engine: Project Overview & Instructional Context

## 1. Project Identity & Vision
The **SPU-13 (Sovereign Processing Unit)** is a bit-exact, pipelined, rational-field ($\mathbb{Q}(\sqrt{3})$) algebraic processor designed for high-precision manifold calculations and 60-degree resonance graphics. It represents a departure from standard non-standard analysis infinitesimals, moving toward **Wildberger's complete Boolean and rational calculus framework**.

The project aims to build a next-generation processor that bridges the gap between abstract geometric theory (Bee Rosa Davis's work on Millennium Problems) and physical hardware implementation. It is built on the **Bio-Laminar Hypothesis**, which posits that "Cubic Dissonance" (90-degree Cartesian grids and asynchronous timing) is a primary driver of digital stress and neurological fatigue. The SPU-13 provides **Refractive Clarity** through 60-degree resonance and phase-locked execution.

## 2. Core Architecture (SPU-13 / SPU-4)
### Hardware Architecture (v4.1.0):
- **Davis Law Gasket ($C = \tau/K$):** The fundamental stability arbiter. Monitors manifold tension ($K$) and applies **Henosis** (soft recovery) if a "Cubic Leak" ($\sum ABCD \neq 0$) is detected.
- **Phi-Gated Pulse:** Replaces rigid metronomes with recursive timing governed by the **Golden Ratio ($\phi$)**. Instructions are dispatched at Fibonacci intervals (8, 13, 21 cycles) to minimize electromagnetic interference and thermal noise.
- **Lattice Protocol (PWI):** 1-wire asynchronous telemetry where pulse width is proportional to the **Davis Ratio ($C$)**.
- **Laminar Input (L-CLK/L-DAT):** 2-wire synchronous sensory interface allowing zero-latency "Identity Strikes" into the manifold.
...
### GPU & Graphics Architecture:
- **Rational Color Space:** Uses **Spectral Ratios** ($P/Q$) instead of RGB to eliminate banding.
- **Rational Shading:** Replaces floating-point dot products with the **Spread ($s$) Law** ($\sin^2\theta$ ratio), enabling single-integer multiplication shading.
- **ISA (PISA):** The **Polynomial Instruction Set Architecture** performs operations as parallel algebraic transformations on $(a, b)$ pairs in $\mathbb{Q}(\sqrt{3})$.
- **Zero-Branching Rule:** All control flow is compiled into Boolean Polynomial logic (`MUX` primitives) to ensure deterministic latency and bit-exactness.
- **Unified Register Map (U.R.M.):** 32-bit `RationalSurd` registers (16-bit $P$, 16-bit $Q$) standardize all manifold communication.
- **Memory Coherence:** **Fractal RAM Alignment** (bit-interleaved addressing) allows a "7-Pixel Sip" fetch for zero-latency neighbor access.
- **Energy Efficiency:** "Ephemeralization" through the removal of framebuffers and floating-point hardware.
...
### New ALU Design Specifications (Unified TDM-ALU):
- **Architecture:** Resource-folded, TDM (Time-Division Multiplexing) architecture using 1 DSP slice for cross-product multiplication.
...
- **Stability:** Integrated **Davis Law Gaskets** (Quadrance-check) to prevent manifold tension and cubic leakage.
- **Operational Logic:** Instruction-driven intrinsics for high-speed $Q(\sqrt{3})$ transformations, including Jitterbug Morphing.
- **Soft-Start:** Implemented `spu_soft_start.v` using Fibonacci-stepped intensity increments (8, 13, 21...) for safe, bio-coherent power-up.
- **Active Inference:** Predictive coding logic suppresses "Cubic Noise" to maintain Laminar manifold state.
- **Lithic-L ISA:** Every instruction is a 16-bit **Chord** (Quadray vector) executed in sync with the Fibonacci heartbeat. Designed for **Gestalt Programming**, where the developer telling the lattice *what* to become rather than *how* to calculate.

### Key Hardware Modules (Verilog/RTL):
- **`spu4_core.v`:** Sentinel core (4-axis, 32-bit Quadray).
- **`spu13_core.v`:** Cortex core (13-axis, 832-bit Collective Manifold).
- **`spu_system.v`:** Integrated system orchestrator.
- **`spu_unified_alu_tdm.v`:** Resource-efficient folded ALU.
- **`spu_soft_start.v`:** Fibonacci-stepped power-up controller.
- **`spu_laminar_power.v`:** Dynamic state-scaling power dispatcher.
- **`spu_davis_gate.v`:** DSP-optimized Quadrance stability checker.
- **`spu_bresenham_killer.v`:** Rational lattice line-drawing algorithm.

### Hardware Targets:
- **Nano/iCeSugar:** 32-bit Rational Core (Small Core).
- **Pro/ECP5:** 832-bit Sovereign Core (Golden Core).
- **SovereignBus v1.0:** The standard interconnect for all cores.

## 3. Reference & Integration Components

### Davis-Wilson Lattice Verification (`reference/davis-wilson-map`)
Empirical test of the Davis-Wilson mass gap framework on SU(3) lattice gauge theory. This component provides the theoretical validation for the processor's geometric mandates.
- **Key Results:** 7/7 Millennium Problems + 4 Major Conjectures validated empirically.
- **Core Map:** $\Gamma(A) = (\Phi, r)$ (Continuous vs Discrete cache).

### Synergetic Renderer (`reference/synergeticrenderer`)
A high-performance renderer (including Metal backend support for macOS) that utilizes the SPU's geometric primitives.
- **Metal Fixes:** Recent development has focused on fixing Intel Broadwell crashes, stabilizing depth/stencil clearing, and standardizing the geometric pipeline (Reverse-Z, Y-orientation).

## 4. Theory & Foundations
The project is grounded in several formal papers and texts located in the `theory/` and `reference/davis-wilson-map/reports/` directories:
- **Divine Proportions (N.J. Wildberger):** Rational Trigonometry and the foundation for the SPU's bit-exact ALU (moving away from infinitesimals).
- **Yang-Mills Mass Gap Solution:** 15σ experimental evidence for topological rectification.
- **Navier-Stokes Regularity:** Holonomy-first proof using Davis Law.
- **P vs NP:** Geometric separation via Field Equations.
- **Wildberger's Rational Calculus:** The mathematical foundation for the SPU's ALU (moving away from infinitesimals).

## 5. Sovereign Display Protocol (SDP v1.0)
- **Lattice-Lock Mandate:** Pixels are treated as **Resonant Points** on a 60-degree IVM, synchronized to the 61.44 kHz "Piranha Pulse."
- **Zero-Buffer:** Streamed live; latency is fixed to HAL propagation delay.
- **Temporal Dithering:** Uses 61.44 kHz dithering for Cartesian (90°) displays to ensure "Vibrational Sharpness."
- **HAL Modules:** Modular drivers (`HAL_Cartesian`, `HAL_Vector`, `HAL_Native_Hex`) for hardware-agnostic isotropic display.

## 6. Software Stack: Ghost OS & Lithic-L
- **Ghost OS Engine:** A continuous feedback loop between the RP2040 (Senses) and FPGA (Vision).
- **Synergetic Buffer:** Automatic Z-occlusion handled by hardware; entities are stored as Chords in the 64MB SDRAM lattice.
- **Laminar Pulse:** Modulating game world "Physics" (Gravity/Friction) through frequency and stability shifts in the manifold.

## 6. AI Auditor Guidelines (Contribution Mandates)
- **Ultrafinite Constraint:** No Floating Point; no division; no transcendental approximations.
- **Timing Mandate:** Must be phase-locked to the 61.44 kHz Piranha Pulse. Buffers are forbidden as "error-hiding" mechanisms; late signals indicate geometric flaws, not timing issues.
- **Laminar Style:** Modules must be "Lithic" (small/single-purpose). Naming follows `SPU_`, `HAL_`, `IVM_` prefixes.
- **Public Domain:** All contributions are CC0 1.0 Universal.

## 6. Development Conventions
- **Lithic & Laminar:** Modules must be single-purpose (Lithic) and zero-drift (Laminar).
- **Bit-Exactness:** All calculations must be bit-exact in the rational field $\mathbb{Q}(\sqrt{3})$. Floating point is strictly avoided in the core ALU.
- **Verification Mandate:** NEVER push to GitHub without running local verification (`spu-verify`) and confirming 100% bit-exact PASS results.
- **Safety:** Protect .env files and hardware configuration states.

## 7. Key Contacts/Sources
- **Bee Rosa Davis:** Author of the Universal Geometry framework and Millennium Problem proofs.
- **Dr. Thomson:** Collaborator on next-gen processor refinements.
- **Wildberger:** Mathematical inspiration for the Rational Calculus framework.
- **Kirby Urner:** Developer of the 4-axis Quadray coordinate system used in the SPU-4 Sentinel.
- **Ken Wheeler:** Research on the Janus-like nature of field geometry, informing the **Janus Bit** implementation.
- **Andrew Thomson:** Inventor of the **Spread-Quadray Rotors (SQR)** framework for closed-loop algebraic rotations.
