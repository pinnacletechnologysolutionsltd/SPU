# SPU-13: A Deterministic Geometric Computer Using Rational Quadray Arithmetic

**Authors:** John G. [Last Name], SPU-13 Project
**Submitted to:** arXiv.org — cs.AR (Computer Architecture)

## Abstract (150 words)
Standard CPUs use IEEE-754 floating-point and Cartesian coordinates. This paper presents SPU-13, a geometric computer that replaces both with exact rational arithmetic in Q(√3) and 4D quadray coordinates. The architecture implements a Wheeler-Feynman retrocausal handshake as a first-class instruction (PHSLK), performing Offer/Confirmation cross-multiplication in a single cycle. The twine-register file stores both forward-propagating (Offer) and backward-propagating (Confirmation) wave states. A 4-stage pipeline sequences fetch, decode, execute, and writeback. The design is verified across three independent implementations (Python, C++, Verilog) with 76 simulation tests, and synthesized on a Gowin GW5A-25 FPGA at 11,125 LUTs (46% of device). We demonstrate that deterministic boundary-value computation—replacing iterative approximation with single-cycle hardware resolution—is feasible in silicon.

## 1. Introduction (2 pages)

### 1.1 The Problem
- IEEE-754 floating-point: rounding errors accumulate in geometric computation
- Cartesian coordinates: sqrt, sin, cos require approximation
- Iterative solvers: gradient descent, PDE integration are power-hungry
- Von Neumann bottleneck: sequential execution vs geometric parallelism

### 1.2 Related Work
- Rational arithmetic CPUs (academic only, never commercialized)
- Buckminster Fuller's quadray coordinates (never in silicon)
- Wheeler-Feynman absorber theory (EM simulation software only)
- Connection Machine, ILLIAC IV, CELL (parallel but not geometric)

### 1.3 Contribution
- First silicon implementation of quadray rational arithmetic
- First hardware Wheeler-Feynman handshake instruction (PHSLK)
- Twine-register architecture encoding bidirectional wave propagation
- Open-source RTL, verified across three simulation layers

## 2. Mathematical Foundation (3 pages)

### 2.1 Q(√3) Rational Field
- Field definition: p + q·√3 where p,q are integers
- Closure under addition and multiplication
- Norm N = p² − 3q² (integer, not floating-point)
- Pell orbit: r = 2 + √3, norm N(r) = 1 (exact integer preserve)

### 2.2 Quadray Coordinates
- 4D barycentric basis (a,b,c,d) spanning 3D space
- Constraint: a + b + c + d = 0
- Quadrance Q = a² + b² + c² + d² replaces Euclidean distance
- Spread S replaces angle (rational, no sin/cos)
- Metric tensor M = 4I − J

### 2.3 Wheeler-Feynman Absorber Theory
- Retarded wave: forward-propagating from emitter
- Advanced wave: backward-propagating from absorber
- Offer/Confirmation handshake: constructive interference
- Application to computation: boundary-value solve instead of timestep iteration

## 3. Instruction Set Architecture (3 pages)

### 3.1 Twine-Register File
- 32 entries, each with Offer (64-bit) and Confirmation (64-bit) slot
- Dual-port read: port A = Offer .O, port B = Confirmation .C
- SPU-4 sentinel mode: only banks 0-7 active

### 3.2 Opcode Map
- Temporal opcodes: OFFR (0x40), CNFM (0x41), PHSLK (0x42), INVJ (0x43)
- Quadrance arithmetic: QADD, QMUL, QCMP (0x20-0x25)
- Geometric: SPRD, ROTR, CROSS, DOT, TNSR (0x30-0x35)
- Data movement: LOAD, STORE, MOV, MOVI (0x10-0x15)
- Telemetry: MFOLD, STAT, HEX (0x70-0x74)

### 3.3 Instruction Formats
- 64-bit wide, 6 formats: R (register), L (load/store), I (immediate)
- U (unary/conditional), B (branch), X (system)

### 3.4 Pipeline
- 4-stage: Fetch → Decode/Read → Execute (RAU) → Writeback/Telemetry
- RAU reads Offer + Confirmation in same cycle (dual-port)
- No hazard detection: RP2350 at ~1 kHz, FPGA at 6.25 MHz

## 4. Implementation (3 pages)

### 4.1 Hardware Stack
```
SD Card → RP2350 (RISC-V host) → SPI → Tang 25K FPGA (SPU-13 core)
```
- RP2350: Southbridge (boot, filesystem, telemetry)
- Tang 25K: SPU-13 compute core (rational ALU, twine-registers, RPLU)

### 4.2 RTL Modules
| Module | Lines | Function |
|--------|-------|----------|
| spu_isa_decoder | 350 | 64-bit instruction decode |
| spu_twin_regfile | 120 | 32 × dual-port register file |
| spu_rau | 230 | Rational arithmetic unit |
| spu_pipeline_ctrl | 240 | 4-stage pipeline sequencer |
| spu_isa_defines.vh | — | Opcode constants |

### 4.3 Synthesis Results
| Metric | Value |
|--------|-------|
| Target | GW5A-LV25MG121NES |
| LUTs | 11,125 (46%) |
| FFs | 4,493 (9%) |
| Clock | 6.25 MHz (core), 50 MHz (SPI) |
| Power | ~100 mW (estimated) |

## 5. Verification (2 pages)

### 5.1 Simulation Stack
| Layer | Language | Tests | Coverage |
|-------|----------|-------|----------|
| Behavioral | Python (spu13_arch_sim.py) | 35 | Temporal ops, RAU, RPLU |
| C++ model | C++17 (spu13_arch.h) | 40 | Cycle-accurate, cross-validated |
| RTL | Verilog (iverilog) | 76 | Pipeline, decoder, register file |

### 5.2 Cross-Validation
- Same 64-bit encoding across all three layers
- PHSLK cross-multiplication produces identical results
- Phase-lock coherent/non-coherent flags match

### 5.3 Test Cases
- PHSLK coherent: matching Offer/Confirmation → FLAGS.C=1
- PHSLK non-coherent: mismatch → FLAGS.C=0
- OFFR/CNFM: RPLU material table → register slots
- INVJ: quadrance preserved, sign flipped
- QADD/QCMP/TNSR: exact rational results

## 6. Results and Discussion (2 pages)

### 6.1 Performance Characteristics
- PHSLK: single-cycle boundary-value resolution
- QADD/QCMP: single-cycle exact rational arithmetic
- ROTR: 6-cycle Pell orbit rotation (TDM DSP)

### 6.2 Comparison to Standard Approaches
| Problem | Standard | SPU-13 |
|---------|----------|--------|
| Path coherence | N iterations (loop) | 1 PHSLK instruction |
| Quadrance comparison | 2 FMUL + 1 FADD (approx) | 1 QADD (exact) |
| Rotation | sin/cos LUT (±1 LSB error) | Remexact Pell orbit |

### 6.3 Applications
- Physics-informed AI: prediction as geometric routing
- Molecular simulation: Morse potential boundary-checking
- Robotics: trajectory validation without iteration

## 7. Conclusion and Future Work (1 page)

### 7.1 Summary
We have designed, simulated, and synthesized a deterministic geometric computer using rational quadray arithmetic. The SPU-13 replaces floating-point approximation and iterative solvers with exact integer cross-multiplication and bidirectional boundary-value resolution.

### 7.2 Future Work
- Full RPLU pipeline with SDRAM (Padé exponential evaluation)
- Wukong (Artix-7) port with GPU visualization and HDMI
- Cluster communication via Artery links
- Custom PCB integrating RP2350 + FPGA on single board

### 7.3 Open Source
All RTL, software, and documentation are available at:
github.com/spu13/hardware | software | docs

## References
1. N.J. Wildberger, *Divine Proportions: Rational Trigonometry to Universal Geometry*
2. D.G. Fuller, *Synergetics: Explorations in the Geometry of Thinking*
3. J.A. Wheeler, R.P. Feynman, "Interaction with the Absorber as the Mechanism of Radiation" (1945)
4. A. Thomson, *Quantify Everything: A Dream of Scalar Physics and Quadray Coordinates*
5. P. Benioff, "The computer as a physical system" (1980)
