# Research Proposal & Theoretical Framework

## Title

**Deterministic Photonic Co-Processing: Compiling Discrete Algebraic and Geometric ISAs into Passive Silicon Photonics**

---

## Abstract

Contemporary optical computing architectures rely predominantly on continuous-variable (CV) analog matrix-vector multipliers designed for lossy artificial neural networks. These implementations face severe precision limitations due to accumulation drift, thermal fluctuations, phase noise, and power-hungry conversion boundaries.

We investigate the hypothesis that **discrete algebraic representations provide recoverable state margins that allow analog photonic physical transformations to serve as computational primitives without requiring continuous numerical precision at the architectural level**. Rather than asserting that optical hardware performs intrinsically exact arithmetic, we formulate a hybrid co-processing model: the digital host executes a formally exact algebraic Instruction Set Architecture ($\mathbb{Q}(\sqrt{3})$ / `SurdFixed64` and Quadray geometry), the passive silicon photonic fabric acts as an unclocked analog linear-transform accelerator, and a Boundary Quantization Engine (BQE) recovers the discrete mathematical state within explicitly bounded noise envelopes.

This proposal establishes a three-tier architectural specification (Exact Algebra, Compiled Transfer Matrices, Physical Noise Recovery), derives complex scattering decompositions under passivity constraints ($S^\dagger S \preceq I$), and defines a progressive five-phase experimental roadmap starting from isolated fixed-transform silicon cells.

---

## Executive Summary

```text
            THREE-TIER HYBRID CO-PROCESSING MODEL

  1. EXACT DIGITAL TIER (SPU-13 Host)
     - Formal Q(√3) and Quadray ISA Semantics
     - Exact Integer / Fixed-Point Golden Model
  ──────────────────────────────────────────────────────────── (E/O Modulation)
  2. COMPILED PHOTONIC TIER (Passive Silicon Photonics)
     - Continuous Complex Field Transformations
     - Normalized Sub-Unitary Scattering (S†S ⪯ I)
     - Unclocked Group-Velocity Propagation (t_prop)
  ──────────────────────────────────────────────────────────── (O/E Detection)
  3. PHYSICAL RECOVERY TIER (Boundary Quantization Engine)
     - Statistical Error-Bounded Lattice Snapping
     - Drift-Free Digital State Snapping: P(Q(F_opt(x)) = F_spu(x))
```

### The Three-Tier Architectural Hierarchy

To maintain complete scientific and physical rigor, this research separates claims across three distinct domains:

| Architectural Tier | Execution Substrate | Operational Reality | Precision Model |
| --- | --- | --- | --- |
| **1. Exact Tier (ISA & Algebra)** | SPU-13 Digital Controller (CMOS/FPGA) | Symbolic ring axioms in $\mathbb{Z}[\sqrt{3}]$ & Quadray space | **Formally Exact / Bit-Exact** |
| **2. Compiled Tier (Optical Fabric)** | Passive Dielectric Waveguides (SiPh) | Continuous-time linear optical field propagation | **Analog Linear Transform** |
| **3. Physical Tier (Boundary Recovery)** | BQE Flash Comparators / Detection | Probabilistic decision process / lattice snapping | **Error-Bounded Recovery** |

### The Core Research Question

> **"Under what physical noise, thermal, and fabrication conditions does an analog photonic realization of a discrete algebraic transform remain digitally recoverable as the exact SPU-13 state?"**

Rather than claiming that physical optics is intrinsically exact, this framework investigates the **falsifiable noise envelope** for which:

$$P_{\text{correct}} = P\left( Q(F_{\text{optical}}(x)) = F_{\text{SPU}}(x) \right) \ge 1 - \epsilon$$

### Architectural Claim Hierarchy

The SPU-13 proposal makes three distinct claims operating at different levels of abstraction:

1. **Exact (Algebraic Tier):** The SPU-13 Instruction Set Architecture and its digital golden model are defined over exact symbolic or fixed-width finite-precision representations in $\mathbb{Q}(\sqrt{3})$ and Quadray coordinates. Digital operations are formally bit-exact within the host processor.

2. **Compiled (Optical Transfer Matrix Tier):** Selected ISA operations are compiled into mathematically specified optical transfer matrices. The passive photonic fabric executes prescribed linear transformations through calibrated components, but the continuous optical field is fundamentally analog and subject to physical noise.

3. **Physical (Boundary Recovery Tier):** A fabricated photonic circuit may recover the intended digital result with a measured, bounded error probability under specified operating conditions. Recovery occurs through the Boundary Quantization Engine (BQE), which snaps noisy detector measurements back to the nearest valid lattice point in $\mathbb{Q}(\sqrt{3})$ and Quadray space.

---

## Technical Outline

### Section 1: Introduction & Research Motivation
* 1.1 The Analog Precision Wall in Continuous-Variable (CV) Silicon Photonics.
* 1.2 The Precision Wall Mechanisms in Analog Optical Computing.
* 1.3 Prior Art: From Stored-Program Optical Computers to Modern Photonic ISAs.
* 1.4 The SPU-13 Architectural Distinction: Algebraic & Geometric ISAs.

### Section 2: Mathematical Foundations & Golden Model
* 2.1 The Algebraic Structure of the Surd Field $\mathbb{Q}(\sqrt{3})$ and `SurdFixed64`.
* 2.2 Coefficient Encoding and Signed Optical Representation.
* 2.3 Tetrahedral Quadray Coordinates (4-Space Basis).
* 2.4 Discrete Unitary Operators and $60^\circ$ Rotational Symmetry (`SROT.60`).
* 2.5 Lucas Sequences and Polynomial Reduction.

### Section 3: Candidate Photonic Mapping Topologies
* 3.1 Field Coefficient Encoding: Spatial Dual-Rail and Mode Multiplexing.
* 3.2 Transfer Matrix Mapping via Directional Couplers and Multi-Mode Interferometers (MMI).
* 3.3 Passive Phase Alignment: Modeling $e^{i\pi/3}$ via Waveguide Delay ($\Delta L$).
* 3.4 Linear Superposition vs. Dynamic Modulation Boundaries.

### Section 4: Microarchitecture of the Photonic Processing Unit
* 4.1 Hybrid Electro-Photonic Execution Pipeline.
* 4.2 The Photonic Lucas Multiply-Accumulate (MAC) Systolic Array.
* 4.3 Quadray Projection Units (QPU) and Ray Arithmetic Routing.
* 4.4 Boundary Quantization Engine (BQE): Lattice Snapping at the Detector Interface.

### Section 5: Physical Noise Modeling & Recovery Simulation
* 5.1 Latency Analysis: Physical Propagation Delay ($t_{\text{prop}}$) vs. Clock Latching.
* 5.2 Error Propagation Model: Phase Jitter, Insertion Loss, and Mode Crosstalk.
* 5.3 Monte Carlo Recovery Simulation: Bounding $P(\text{correct recovery})$ vs. Noise Floor.
* 5.4 Modeled Power and Insertion Loss Budget.

### Section 6: Five-Phase Validation Roadmap & Minimum Viable Silicon
* 6.1 Phase 1–5 Progressive Verification Strategy.
* 6.2 Minimum Viable Experiment: Three-Model SMUL Investigation.
* 6.3 Collaborative Engagement Model for Photonics Laboratories.

---

# Section 1: Introduction & Architectural Motivation

---

## 1.1 The Renaissance and Relocation of Optical Computing

Over the past decade, integrated silicon photonics has transitioned from a specialized telecommunications technology into a primary candidate for high-throughput computing hardware. Driven by the exponential power density demands of modern matrix-heavy workloads, optical computing promises hyper-parallel processing, ultra-wide signal bandwidth, and speed-of-light propagation latencies across passive dielectric structures.

However, the prevailing paradigm in optical computing relies almost entirely on **Continuous-Variable (CV) architectures**. Designed primarily to accelerate lossy artificial neural networks and deep-learning inference, CV photonic processors represent numerical quantities as continuous analog optical field amplitudes, phases, or optical intensities propagating through arrays of tunable Mach-Zehnder Interferometers (MZIs) or resonant optical structures.

```text
               CONTINUOUS-VARIABLE PHOTONIC COMPUTING PIPELINE

  Digital State ──► [ High-Power DAC ] ──► [ Analog Optical Amplitude ]
                                                    │
                                                    ▼
  Bit-Exact Result ◄── [ High-Power ADC ] ◄── [ Noisy Optical Wavefront ]

```

While CV photonics can achieve massive raw throughput for low-precision vector-matrix multiplications, it introduces fundamental physical trade-offs that render it unsuitable for deterministic, high-precision domain-specific computing.

---

## 1.2 The Precision Wall in Continuous-Variable Optics

The central bottleneck facing continuous-variable optical computing is the **Analog Precision Wall**. Because CV photonics treats computation as an analog physical simulation, the system is fundamentally susceptible to noise sources inherent to integrated optical circuits:

1. **Thermal Drift and Phase Jitter:** Silicon exhibits a strong thermo-optic coefficient ($\frac{dn}{dT} \approx 1.86 \times 10^{-4} \ \text{K}^{-1}$). Microkelvin thermal fluctuations alter waveguide effective refractive indices, causing catastrophic phase drift across uncalibrated interferometric paths.
2. **Fabrication Variations:** Nanometer-scale lithographic roughness along waveguide sidewalls induces phase errors and inter-mode crosstalk in Multi-Mode Interference (MMI) devices.
3. **Optoelectronic Conversion Overhead:** Mapping digital numbers into optical states and back requires high-frequency Digital-to-Analog Converters (DACs) and Analog-to-Digital Converters (ADCs). The power consumption and thermal dissipation of $8$-bit or $10$-bit ADCs operating above $10 \text{ GHz}$ quickly negate any intrinsic optical energy savings.
4. **Error Accumulation:** Unlike digital CMOS logic, where signal levels are continuously regenerated to logic high/low rail voltages, analog optical signals suffer cumulative degradation. Across cascading computational stages, phase noise and insertion loss compound rapidly, capping effective numerical precision at $4$ to $8$ equivalent bits.

```text
                      THE ANALOG PRECISION WALL

  Precision (Bits)
     ▲
  64 │  [ Double Precision Floating Point (FP64) - CMOS Electronic ]
     │
  32 │  [ Single Precision Floating Point (FP32) - CMOS Electronic ]
     │
  16 │  ──────────────────────────────────────────────────────────
     │    PHYSICAL NOISE FLOOR / DRIFT LIMIT (CV PHOTONICS)
   8 │  [ Continuous-Variable Optical MZIs / Analog Intensity ]
     │
     └────────────────────────────────────────────────────────────►
                                                           Pipeline Depth

```

For applications requiring exact state transitions—such as 3D/4D spatial computing, non-Euclidean kinematics, exact polynomial reduction, and real-time collision detection—this analog noise floor represents an impassable barrier.

---

## 1.3 Prior Art: From Stored-Program Optical Computers to Modern Photonic ISAs

The concept of an instruction set architecture (ISA) tailored for optical computing has a rich historical lineage, which can be categorized into four primary paradigms:

1. **General-Purpose Stored-Program Optical Computers (SPOC):**
   In the early 1990s, Jordan, Heuring, and colleagues demonstrated the **Stored-Program Optical Computer (SPOC)**—a functional optical CPU constructed from lithium-niobate ($\text{LiNbO}_3$) directional couplers and single-mode optical fiber delay lines. SPOC executed an explicit stored-program instruction set (`lda`, `sta`, `clrm`, `clra`, `rora`, `notm`, `or`, `and`, `add`, `jmp`, and conditional skips), maintaining synchronization strictly through **optical time-of-flight** rather than electronic flip-flops.
2. **Optical Array Logic (OAL):**
   Tanida, Ichioka, and collaborators formulated Optical Array Logic, treating parallel digital optical computing as an instruction-set composition problem over 2D spatial pixel arrays and SIMD cellular logic.
3. **Electronic Host / Photonic Tensor Accelerators:**
   Contemporary industrial and academic architectures (e.g., modern photonic AI processors and Lightmatter/EnLight platforms) integrate electronic RISC controllers that sequence high-level streaming tensor instructions to analog photonic GEMM cores, employing dependency tagging and out-of-order execution.
4. **All-Optical Digital CPUs:**
   Emerging efforts (such as Akhetonics and all-optical digital CPU research) pursue general-purpose Boolean logic in silicon photonics with custom digital optical ISAs.

```text
                  TAXONOMY OF OPTICAL INSTRUCTION EXECUTION

  [ SPOC (1994) ]             [ CV Photonic Accelerators ]    [ SPU-13 PPU (This Work) ]
  • General-Purpose Boolean   • Analog Matrix Multiply (GEMM)  • Discrete Algebraic Extension Q(√3)
  • LiNbO3 Directional Coupler• Approximate Floating Point     • Exact SurdFixed64 Ring Arithmetic
  • Optical Time-of-Flight    • DAC/ADC Intensity Modulation   • Topology-as-Computation / BQE Snapping
```

---

## 1.4 The SPU-13 Architectural Distinction: Algebraic & Geometric ISAs

Rather than replicating general-purpose Boolean logic gates or implementing lossy analog matrix multipliers, the SPU-13 architecture investigates a fundamentally different question:

> **"What properties should an Instruction Set Architecture possess when its primary execution units are passive photonic transformations?"**

In the SPU-13 architecture, **instruction semantics are formal mathematical objects first**, and the photonic waveguide layout is a physical compilation target:

```text
                             SPU-13 ISA
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
          [ SADD / SMUL / JINV ]            [ SROT.60 / GSTEP ]
                  │                               │
                  ▼                               ▼
       Surd Extension Q(√3)              Tetrahedral Quadray Space
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                    Passive Photonic Compilation
                    (MMI Couplers, Delay Lines ΔL)
```

### SPU-13 Instruction-to-Photonic Primitive Mapping

| SPU Opcode | Algebraic / Geometric Operation | Target Photonic Primitive | Optical Physical Realization |
| --- | --- | --- | --- |
| **`SADD`** | Surd Addition: $(a+c) + (b+d)\sqrt{3}$ | $2\times 1$ Coherent Combiner | In-phase optical superposition ($\Delta \theta = 0$) |
| **`SSUB`** | Surd Subtraction: $(a-c) + (b-d)\sqrt{3}$ | $2\times 1$ Out-of-Phase Combiner | Passive $\pi$-phase delay line ($\Delta L_\pi$) superposition |
| **`SMUL`** | Surd Multiplication: $(ac+3bd) + (ad+bc)\sqrt{3}$ | Dual-Rail Transfer Matrix Cell | $1:3$ Asymmetric MMI splitters + directional couplers |
| **`JINV`** | Surd Inversion: $a - b\sqrt{3}$ | Passive $\pi$-Phase Delay | Fixed $\Delta L_\pi$ shifter on Rail B ($b\sqrt{3}$) |
| **`SROT.60`** | $60^\circ$ Geometric Spatial Rotation | Differential Delay Section | Fixed path differential $\Delta L_{60} = 6.4322\,\mu\text{m}$ ($e^{i\pi/3}$) |
| **`GSTEP`** | Quadray Step Transformation | $4\times 4$ MMI Projection Mesh | Symmetric 4-mode tetrahedral interference |
| **`S2C`** | Surd-to-Cartesian Basis Bridge | Mode-Coupled Projector | Hardcoded linear basis transformation matrix |
| **`C2S`** | Cartesian-to-Surd Basis Bridge | Orthogonal Projection Mesh | Discrete rational inverse mapping |

By defining instructions over discrete algebraic extensions and symmetric Quadray geometry, each operation compiles into a fixed physical waveguide topology where digital state integrity is preserved via the Boundary Quantization Engine (BQE).

---

# Section 2: Mathematical Foundations & Quadray Algebra

---

## 2.1 The Surd Field Extension $\mathbb{Q}(\sqrt{3})$ and Ring Arithmetic

Standard floating-point units (IEEE 754) represent irrational values—such as $\sqrt{3}$ or trigonometric constants—through truncated binary mantissas. Across iterative vector rotations and matrix operations, rounding errors accumulate non-deterministically. The SPU-13 PPU eliminates this failure mode by restricting its scalar field to the exact algebraic extension field $\mathbb{Q}(\sqrt{3})$.

An arbitrary scalar element $x \in \mathbb{Q}(\sqrt{3})$ is uniquely expressed as a pair of rational coefficients $(a, b)$ over the field basis $\{1, \sqrt{3}\}$:

$$x = a + b\sqrt{3}, \quad a, b \in \mathbb{Q}$$

```text
               SURD ALGEBRAIC FIELD EXTENSION Q(√3)

                      ┌──────────────────────┐
                      │   Scalar x ∈ Q(√3)   │
                      └──────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │ Rational Component│           │ Algebraic Scale   │
       │        'a'        │           │    'b' (√3 Basis) │
       └───────────────────┘           └───────────────────┘

```

### Algebraic Ring Operations

Addition and subtraction proceed pairwise over the vector space $\mathbb{Q}^2$:

$$(a + b\sqrt{3}) \pm (c + d\sqrt{3}) = (a \pm c) + (b \pm d)\sqrt{3}$$

Multiplication over the ring $\mathbb{Z}[\sqrt{3}] \subset \mathbb{Q}(\sqrt{3})$ maps directly to structured cross-coupling terms governed by the minimal polynomial $P(t) = t^2 - 3 = 0$:

$$(a + b\sqrt{3})(c + d\sqrt{3}) = (ac + 3bd) + (ad + bc)\sqrt{3}$$

Notice that the irrational scaling parameter $\sqrt{3}$ drops out of the operational logic, leaving a system of **pure integer and rational multiplications**. The factor of $3$ attached to the quadratic term $3bd$ is a structural constant of the ring, making it ideal for passive physical encoding into optical waveguide splitting topologies (Section 3.2).

---

## 2.2 Coefficient Encoding and Signed Optical Representation

To map elements of the Surd field $\mathbb{Q}(\sqrt{3})$ onto physical optical channels, a precise specification of coefficient encoding must bridge the digital algebraic domain and the continuous optical field. This subsection defines the complete transformation from digital representation through optical modulation to detector readout and quantization.

### Digital Coefficient Specification

An arbitrary surd field element $x = a + b\sqrt{3}$ represents a pair of digital coefficients:

- **Rational Component $(a)$:** Signed integer or fixed-point rational value, width $W_a$ bits, range $\left[-2^{W_a-1}, 2^{W_a-1}-1\right]$.
- **Algebraic Component $(b)$:** Signed integer or fixed-point rational coefficient of $\sqrt{3}$, width $W_b$ bits, range $\left[-2^{W_b-1}, 2^{W_b-1}-1\right]$.

For the minimum viable experiment, we adopt $W_a = W_b = 16$ (signed), yielding the SurdFixed64 representation: $(a, b) \in [-32768, +32767]^2$.

### Optical Scale Factor

To avoid saturating modulators or pushing optical power into nonlinear regimes, a global optical scale factor $s$ normalizes digital coefficients to a safe optical power level:

$$x_{\text{optical}} = q \cdot s,$$

where $q = a$ (or $q = b$ for the algebraic component) and $s$ is chosen such that the resulting field amplitude remains within the operating range of the modulator and detector.

### Signed Dual-Rail Encoding

The SPU-13 architecture employs **balanced dual-rail encoding** to represent signed values without requiring direct negative optical amplitudes:

$$E(q) = s \cdot (q^+ - q^-),$$

where 
$$q^+ = \max(q, 0), \quad q^- = \max(-q, 0).$$

For each coefficient, exactly one rail carries energy; the differential output naturally encodes the sign. For a two-component surd state $x = a + b\sqrt{3}$, the physical optical input is:

$$\mathbf{E}_{\text{in}} = s \begin{bmatrix} a^+ - a^- \\ b^+ - b^- \end{bmatrix} = s \begin{bmatrix} a \\ b \end{bmatrix},$$

where the subtraction is implicit in the dual-rail measurement.

### Field-to-Power Relationship

A critical distinction: optical power is proportional to the squared field amplitude, not the field itself:

$$P_i \propto |E_i|^2.$$

Therefore, a desired field coefficient $g$ **cannot** be specified merely as a power ratio. Any field scaling (such as the factor $\sqrt{3}/2$ in the $\text{SMUL}$ coupler) must be derived from the actual measured scattering matrix and detector normalization of the optical circuit, not assumed from power budget calculations.

### Example: Two-Input, Two-Output Transform

For a fixed calibrated $2 \times 2$ linear optical transform:

$$\mathbf{y} = T \mathbf{x}, \quad T = \begin{bmatrix} t_{00} & t_{01} \\ t_{10} & t_{11} \end{bmatrix},$$

the physical input vector in dual-rail encoding is:

$$\mathbf{E}_{\text{in}} = s \begin{bmatrix} x_0^+ - x_0^- \\ x_1^+ - x_1^- \end{bmatrix}.$$

The optical device produces:

$$\mathbf{E}_{\text{out}} = H(\lambda, T, \theta) \, \mathbf{E}_{\text{in}} + \mathbf{n}_E,$$

where:
- $H(\lambda, T, \theta)$ is the measured transfer matrix (wavelength-dependent, temperature-dependent $\theta$).
- $\mathbf{n}_E$ represents field-equivalent noise (shot noise, phase jitter, crosstalk).

### Detector Observable and BQE Decision Thresholds

At balanced photodiode pairs, the differential photocurrent is measured:

$$I_{\text{diff}} = R_p \left( P_+ - P_- \right) = R_p \left( |E_+|^2 - |E_-|^2 \right),$$

where $R_p$ is the photodiode responsivity. The BQE then applies a quantization rule: given measured voltage $V_{\text{measured}} \propto I_{\text{diff}}$, snap to the nearest representable lattice point in the coefficient space, with pre-registered tie-breaking rules (e.g., round-to-nearest-even).

### Summary Table: Coefficient Encoding Specification

| Property | Specification |
| --- | --- |
| **Digital Width** | $W_a = W_b = 16$ bits (signed), $[-32768, +32767]$ |
| **Optical Scale Factor** | $s$ (normalized to detector / modulator operating range; to be characterized) |
| **Signed Representation** | Balanced dual-rail: $E(q) = s(q^+ - q^-)$ |
| **Rail Normalization** | Both $q^+$ and $q^-$ can be nonzero; their difference encodes the sign |
| **Saturation Behavior** | Coefficients exceeding $\pm 32767$ saturate to $\pm 32767$ (digital host handles overflow detection) |
| **Detector Observable** | Balanced differential photocurrent $I_{\text{diff}} \propto (P_+ - P_-)$ |
| **BQE Decision Rule** | Round measured voltage to nearest quantized value in $[-32768, +32767]$ with deterministic tie-breaking |
| **Noise Sources** | Phase jitter ($\delta\phi \sim \mathcal{N}(0, \sigma_\phi^2)$), amplitude variations ($\varepsilon \sim \mathcal{N}(0, \sigma_{\text{amp}}^2)$), shot noise, thermal noise |

---

## 2.3 Tetrahedral Quadray Coordinates (4-Space Basis)

In conventional 3D Euclidean space $\mathbb{R}^3$, directional vectors along non-orthogonal axes require square roots and transcendental functions ($\sin, \cos$) to project between bases. The SPU-13 architecture replaces the 3-axis Cartesian system ($x, y, z$) with **Quadray coordinates** ($\mathbf{a}, \mathbf{b}, \mathbf{c}, \mathbf{d}$)—a 4-axis basis aligned with the vertices of a regular tetrahedron centered at the origin.

```text
                     QUADRAY TETRAHEDRAL BASIS

                                   a (0,0,0)
                                   ▲
                                   │
                                   │
                    b ─────────────┼───────────── c
                                  ╱ ╲
                                 ╱   ╲
                                ╱     ╲
                               ▼       ▼
                              d         (Origin)

```

### Basis Vectors & Coordinate Representation

The four Quadray basis vectors emanate from the origin toward the four vertices of a unit cube with alternating sign choices:

$$\mathbf{a} = \frac{1}{2}(1, 1, 1), \quad \mathbf{b} = \frac{1}{2}(1, -1, -1), \quad \mathbf{c} = \frac{1}{2}(-1, 1, -1), \quad \mathbf{d} = \frac{1}{2}(-1, -1, 1)$$

Any spatial vector $\mathbf{v}$ is represented by a 4-tuple tuple $\mathbf{q} = (a, b, c, d)$ with $a, b, c, d \in \mathbb{Q}_{\ge 0}$:

$$\mathbf{v} = a\mathbf{a} + b\mathbf{b} + c\mathbf{c} + d\mathbf{d}$$

### Canonical Normalization

To ensure uniqueness of representation, Quadray coordinates maintain a canonical form where at least one coordinate is zero. Since $\mathbf{a} + \mathbf{b} + \mathbf{c} + \mathbf{d} = \mathbf{0}$, subtracting the minimum component $k = \min(a, b, c, d)$ yields the normalized state:

$$\mathbf{q}_{\text{canonical}} = (a - k, \ b - k, \ c - k, \ d - k)$$

This operation is executed at the boundary without floating-point division, maintaining exact integer and rational states across spatial coordinate transformations.

---

## 2.4 Unitary Rotation Operators & Discrete Symmetry (`SROT.60`)

A primary strength of combining Quadray geometry with the $\mathbb{Q}(\sqrt{3})$ field extension is that spatial rotations along tetrahedral symmetry planes map to **discrete permutations and phase shifts**, completely bypassing floating-point trigonometric evaluations.

```text
                  60° ROTATION MATRIX IN QUADRAY SPACE

         ┌───                                         ───┐
         │  1/2       1/2        1/2       -(1/2)√3      │
         │  1/2       1/2      -(1/2)√3      1/2         │
 R_60 =  │  1/2     (1/2)√3      1/2         1/2         │
         │ (1/2)√3    1/2        1/2         1/2         │
         └───                                         ───┘

```

### Discrete Rotation via `SROT.60`

Consider a $60^\circ$ ($\pi/3$ radians) geometric rotation around a principal Quadray axis. In Cartesian coordinates, rotating a vector by $60^\circ$ requires computing:

$$R_{x}(60^\circ) = \begin{bmatrix} 1 & 0 & 0 \\ 0 & \cos(60^\circ) & -\sin(60^\circ) \\ 0 & \sin(60^\circ) & \cos(60^\circ) \end{bmatrix} = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 1/2 & -\sqrt{3}/2 \\ 0 & \sqrt{3}/2 & 1/2 \end{bmatrix}$$

In the SPU-13 architecture, this operator (`SROT.60`) acts directly on the combined Quadray-$\mathbb{Q}(\sqrt{3})$ state vector:

$$\mathbf{\Psi}_{\mathbf{q}} = \begin{bmatrix} a_0 + a_1\sqrt{3} \\ b_0 + b_1\sqrt{3} \\ c_0 + c_1\sqrt{3} \\ d_0 + d_1\sqrt{3} \end{bmatrix}$$

Applying `SROT.60` transforms the state via linear combinations whose coefficients belong entirely to the rational ring $\mathbb{Q}$:

$$\mathbf{\Psi}_{\mathbf{q}}' = \mathbf{M}_{\text{SROT}} \cdot \mathbf{\Psi}_{\mathbf{q}}$$

$$\mathbf{M}_{\text{SROT}} = \frac{1}{2} \begin{bmatrix} 1 & 0 & 0 & -1 \\ 0 & 1 & -1 & 0 \\ 0 & 1 & 1 & 0 \\ 1 & 0 & 0 & 1 \end{bmatrix} + \frac{\sqrt{3}}{2} \begin{bmatrix} 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & -1 \\ 1 & 0 & 0 & 0 \\ 0 & 0 & 1 & 0 \end{bmatrix}$$

Because every matrix entry in $\mathbf{M}_{\text{SROT}}$ consists exclusively of factors of $1/2$ and $\sqrt{3}/2$, **the $60^\circ$ rotation reduces to hardcoded path delays ($\Delta L_{60}$) and passive MMI power combiners** when mapped to physical silicon photonics (Section 3.3).

---

## 2.5 Lucas Sequence Recurrences and Polynomial Reduction

To execute high-degree algebraic reductions without intermediate division or square root evaluations, the SPU-13 architecture incorporates **Lucas sequence recurrences**. A general Lucas sequence of the first kind $U_n(P, Q)$ and second kind $V_n(P, Q)$ satisfies the second-order linear recurrence relation:

$$U_{n+1}(P, Q) = P \cdot U_n(P, Q) - Q \cdot U_{n-1}(P, Q)$$

$$V_{n+1}(P, Q) = P \cdot V_n(P, Q) - Q \cdot V_{n-1}(P, Q)$$

with initial conditions $U_0 = 0, U_1 = 1$ and $V_0 = 2, V_1 = P$.

```text
                  LUCAS RECURRENCE POLYNOMIAL REDUCTION

  State Engine [ U_n, V_n ] ──► [ Integer MAC Array ] ──► Exact Polynomial State
                                         │
                                         ▼
                            No Division / No Rounding

```

Setting parameters $P = 2$ and $Q = -2$ establishes the explicit algebraic link to the surd extension field $\mathbb{Q}(\sqrt{3})$:

$$\alpha, \beta = 1 \pm \sqrt{3} \implies \alpha - \beta = 2\sqrt{3}$$

By the Binet formula for Lucas sequences, the $n$-th power of the characteristic root $\alpha$ satisfies:

$$\alpha^n = \frac{V_n(P, Q) + (\alpha - \beta)U_n(P, Q)}{2} = \frac{V_n(2, -2) + 2 U_n(2, -2)\sqrt{3}}{2} = \frac{V_n(2, -2)}{2} + U_n(2, -2)\sqrt{3}$$

Power iterations of algebraic elements $(a + b\sqrt{3})^n$ fold cleanly into Lucas recurrence states without requiring floating-point multiplication or irrational root evaluations.

This property allows the SPU-13 PPU to execute high-order polynomial evaluations, vector norms, and matrix exponentiations purely as a cascade of integer Multiply-Accumulate (MAC) steps. When mapped to the Lucas MAC Systolic Array (Section 4.2), these recurrences propagate passively through optical waveguides without requiring sequential electronic registers within the passive core, achieving propagation latency bounded by the speed of light through silicon.

---

# Section 3: Passive Waveguide Implementation

---

## 3.1 Field Coefficient Encoding: Dual-Rail and Mode-Division Multiplexing

To map elements of the algebraic extension field $x \in \mathbb{Q}(\sqrt{3})$ onto physical optical channels without incurring continuous-variable analog rounding errors, the SPU-13 Photonic Processing Unit (PPU) employs a **discrete dual-rail waveguide topology**.

An arbitrary surd field element $x = a + b\sqrt{3}$ (where $a, b \in \mathbb{Q}$) is encoded as a two-channel optical state vector:

$$\mathbf{\Psi}_x = \begin{bmatrix} \psi_a \\ \psi_b \end{bmatrix} = \begin{bmatrix} A_a e^{i \phi_a} \\ A_b e^{i \phi_b} \end{bmatrix}$$

Here, the complex optical field components $\psi_a$ and $\psi_b$ represent the rational coefficient $a$ and the algebraic irrationally scaled term $b\sqrt{3}$, respectively.

```text
                     SURD DUAL-RAIL WAVEGUIDE ENCODING

          ┌─────────────────────────────────────────────────────────┐
  Rail A  │  ψ_a  ───> [ Rational Coefficient Channel 'a' ]      │
          └─────────────────────────────────────────────────────────┘
          ┌─────────────────────────────────────────────────────────┐
  Rail B  │  ψ_b  ───> [ Algebraic Scale Channel 'b√3' ]            │
          └─────────────────────────────────────────────────────────┘

```

### Modes of Multiplexing

1. **Spatial Dual-Rail (SDR):** Coefficients $a$ and $b$ propagate along physically distinct single-mode Silicon-on-Insulator (SOI) strip waveguides ($220 \text{ nm} \times 450 \text{ nm}$ core cross-section).
2. **Mode-Division Multiplexing (MDM):** Alternatively, $a$ and $b$ are co-propagated along a multimode bus waveguide using orthogonal transverse electric modes ($TE_0$ for rail $a$, $TE_1$ for rail $b$). The spatial mode conversion is achieved via asymmetrical directional couplers (ADCs) with cross-coupling efficiency $\kappa^2 > 0.98$.

---

## 3.2 Transfer Matrix Mapping via Directional Couplers and Multi-Mode Interferometers (MMI)

The multiplication of two surd numbers $x = a + b\sqrt{3}$ and $y = c + d\sqrt{3}$ expands algebraically into:

$$xy = (ac + 3bd) + (ad + bc)\sqrt{3}$$

This transformation corresponds to the linear matrix-vector mapping:

$$\begin{bmatrix} a' \\ b' \end{bmatrix} = \mathbf{M}_{\text{SMUL}} \begin{bmatrix} a \\ b \end{bmatrix} = \begin{bmatrix} c & 3d \\ d & c \end{bmatrix} \begin{bmatrix} a \\ b \end{bmatrix}$$

### Energy Conservation Principle & Measured Transfer Matrices

A fundamental physical principle of passive linear optics is **energy conservation**: any passive multi-port optical device has a measured scattering or transfer matrix $\mathbf{H}$ that must satisfy $\mathbf{H}^\dagger \mathbf{H} \le \mathbf{I}$ (sub-unitary, accounting for insertion loss).

Because the singular values of $\mathbf{M}_{\text{SMUL}}$ are generally greater than $1$ (specifically, $\sigma_1 = |c + \sqrt{3}d|$ and $\sigma_2 = |c - \sqrt{3}d|$), $\mathbf{M}_{\text{SMUL}}$ **cannot be implemented directly as an unscaled passive optical device without attenuation or projective normalization**.

Critically, we must distinguish **optical power** ($P \propto |E|^2$) from **complex optical field amplitude** ($E$):
* A $2\times 2$ MMI coupler with a $1:3$ power splitting ratio ($\kappa^2 = 0.75, t^2 = 0.25$) yields field amplitude coefficients of $1/2$ and $\sqrt{3}/2$, corresponding to an amplitude scaling of $\sqrt{3}$, **not $3$**.
* The factor $3$ is realized through dual-stage interferometric routing or normalized projective encoding.

### Projective Normalization via Rescaling

The passive optical core implements a normalized transfer matrix:

$$\mathbf{H}_{\text{norm}} = \frac{1}{\sigma_{\text{max}}} \begin{bmatrix} c & 3d \\ d & c \end{bmatrix}, \quad \sigma_{\text{max}} = \max(|c| + 3|d|, |d| + |c|, 1)$$

where $\sigma_{\text{max}}$ is the maximum absolute singular value. The measured optical output is:

$$\mathbf{E}_{\text{out}} = \mathbf{H}_{\text{norm}} \cdot \mathbf{E}_{\text{in}} + \mathbf{n}_E,$$

with field-equivalent noise $\mathbf{n}_E$. The digital Boundary Quantization Engine (BQE) then rescales the photodiode voltages by $\sigma_{\text{max}}$ before lattice snapping, thus recovering the exact algebraic result.

```text
               PROJECTIVE NORMALIZED MAPPING FLOW

  Operands (a, b) ──► [ Modulator Array ] ──► [ Measured Transfer Matrix ]
                                                      │
                                                      ▼
  Exact SPU Target ◄── [ BQE Lattice Snap ] ◄── [ Rescale by σ_max ]
```

---

## 3.3 Passive Phase Alignment: Modeling $e^{i\pi/3}$ via Waveguide Delay ($\Delta L$)

The geometric rotation operator `SROT.60` executes a discrete $60^\circ$ ($\pi/3$ radians) transformation. In the photonic domain, this maps to an optical path-length differential $\Delta L_{60}$.

```text
                  SROT.60 PASSIVE WAVEGUIDE DELAY

         In ───┬─────────────────────────────────► Out (Direct)
               │
               └───[ Waveguide Loop: ΔL_60 ]─────► Out (Shifted e^(iπ/3))
```

### Exact Waveguide Length & Sensitivity Trade-Off

The optical phase accumulated over path length $L$ is $\phi = \frac{2\pi}{\lambda_0} n_{\text{eff}} L$. To engineer a target phase shift $\Delta \phi = \frac{\pi}{3} \pmod{2\pi}$:

$$\Delta L_{60} = \frac{\lambda_0}{n_{\text{eff}}} \left( \frac{1}{6} + m \right), \quad m \in \mathbb{Z}^+$$

For a standard Silicon-on-Insulator (SOI) strip waveguide at $\lambda_0 = 1550 \text{ nm}$ with $n_{\text{eff}} \approx 2.45$:
* **Minimal Path Difference ($m = 0$):** $\Delta L_0 \approx 105.44 \text{ nm}$. (Extremely compact, but challenging for lithographic bend radiuses).
* **Extended Path Difference ($m = 10$):** $\Delta L_{10} \approx 6.4322 \ \mu\text{m}$. (Easily accommodated in standard layout rules).

**Fabrication & Thermal Sensitivity Warning:** Increasing $m$ from $0$ to $10$ expands the physical path length by a factor of $61$, which proportionally increases the phase sensitivity to temperature drift ($\frac{d\phi}{dT} \propto \Delta L$) and waveguide width variations. For $m=10$, keeping the phase error bounded within $|\delta\phi| < \pi/12$ requires thermal stability within $\Delta T \le \pm 14.2 \text{ K}$, reinforcing the need for the digital Boundary Quantization Engine (BQE).

$$\delta \phi = \frac{2\pi}{\lambda_0} \left( \frac{dn}{dT} \right) \Delta L_{60} \Delta T$$

For the BQE to snap phase states without decision errors, the phase error must satisfy $|\delta \phi| < \frac{\pi}{12}$, yielding an allowable temperature operating window of $\Delta T_{\text{max}} \approx \pm 14.2 \text{ K}$.

---

## 3.4 Linear Superposition and Phase-Shift Subtraction

Algebraic addition $(ac + 3bd)$ and subtraction $(ad - bc)$ are performed via coherent optical superposition at passive 2x1 MMI combiners and 2x2 directional couplers.

For two coherent optical fields $\psi_1 = A_1 e^{i\phi_1}$ and $\psi_2 = A_2 e^{i\phi_2}$ entering a $2 \times 1$ combiner, the output field $\psi_{\text{out}}$ is:

$$\psi_{\text{out}} = \frac{1}{\sqrt{2}} \left( \psi_1 + \psi_2 e^{i\Delta \theta} \right)$$

* **Exact Addition ($+$):** By setting $\Delta \theta = 0$ (equal arm lengths), the output amplitude is proportional to $A_1 + A_2$.
* **Exact Subtraction ($-$):** By inserting a passive $\pi$-phase delay line ($\Delta L_{\pi} = \frac{\lambda_0}{2 n_{\text{eff}}}$), $e^{i\pi} = -1$, yielding an output amplitude proportional to $A_1 - A_2$.

### Complete SPU-13 Surd Transformation Cell Matrix

Combining MMI splitters, $\Delta L_{60}$ phase lines, and coherent combiners yields a measured transfer matrix $H_{\text{Surd}}$ for a complete hardware $\mathbb{Q}(\sqrt{3})$ cell:

$$\begin{bmatrix} \psi_{a'} \\ \psi_{b'} \end{bmatrix} = \begin{bmatrix} H_{11} & H_{12} \\ H_{21} & H_{22} \end{bmatrix} \begin{bmatrix} \psi_a \\ \psi_b \end{bmatrix} = \frac{1}{2} \begin{bmatrix} c & 3d \\ d & c \end{bmatrix} \begin{bmatrix} \psi_a \\ \psi_b \end{bmatrix}$$

This matrix is derived from the physical coupler scattering parameters and calibrated in silicon photonics via optical bench characterization or integrated photodiode monitoring.

Because the entire structure is passive and dielectric, the modeled optical execution time $t_{\text{exec}}$ across the cell depends solely on the group velocity $v_g = \frac{c_0}{n_g}$ through the silicon waveguide:

$$t_{\text{exec}} = \frac{L_{\text{total}}}{v_g} \approx \frac{50 \ \mu\text{m}}{7.17 \times 10^7 \text{ m/s}} \approx 0.697 \text{ picoseconds}$$

This achieves propagation latency within the passive optical section bounded only by the physical speed of light in silicon.

---

# Section 4: Microarchitecture of the Photonic Processing Unit

---

## 4.1 Hybrid Electro-Photonic Execution Pipeline

The SPU-13 Photonic Processing Unit (PPU) operates as a tightly coupled co-processor alongside an electronic host controller (such as an FPGA or ASIC core). Computing tasks are partitioned between electronic instruction sequencing and passive optical dataflow:

1. **Electronic Host Controller:** Handles instruction fetch, program counter sequencing, address generation, and memory interface to SRAM/BRAM.
2. **Electro-Optic (E/O) Modulation Boundary:** High-speed Mach-Zehnder Modulators (MZMs) or Micro-Ring Resonators (MRRs) convert discrete integer/surd operands into coherent optical carrier amplitudes and phases.
3. **Passive Photonic Fabric:** Performs geometric rotations (`SROT.60`), Quadray projections, and Lucas Multiply-Accumulate (MAC) cascades via fixed dielectric waveguide topology at the speed of light.
4. **Boundary Quantization Engine (BQE):** Balanced photodiode detectors convert the transformed optical wavefronts into analog electrical currents, where high-speed flash comparators snap the signals back to the exact discrete rational field lattice before passing state back to the electronic core.

```text
               HYBRID ELECTRO-PHOTONIC PIPELINE DATAFLOW

  Electronic Host (SPU-13)
  ┌──────────────────────────────────────────────────────────┐
  │  [Instruction Fetch / Decode] ──► [E/O Modulator Array]  │
  └─────────────────────────────────────────────┬────────────┘
                                                │ Optical Wavefronts
                                                ▼
  Passive Photonic Core (SiPh)
  ┌──────────────────────────────────────────────────────────┐
  │  [Quadray Projection Mesh] ──► [Lucas MAC Systolic Array] │
  │  (Fixed ΔL_60 Delay Lines)     (Passive 1:3 MMI Nodes)   │
  └─────────────────────────────────────────────┬────────────┘
                                                │ Transformed Light
                                                ▼
  Quantization Boundary (BQE)
  ┌──────────────────────────────────────────────────────────┐
  │  [Balanced Photodiodes] ──► [Discrete Lattice Snap]      │
  │  (Noise Snapping Grid)      ──► Writeback to SPU-13 Core │
  └──────────────────────────────────────────────────────────┘
```

---

## 4.2 The Photonic Lucas Multiply-Accumulate (MAC) Systolic Array

For dense tensor evaluations and iterative polynomial reductions, the PPU incorporates a 2D systolic array of Photonic Processing Elements (PEs) optimized for Lucas recurrences over $\mathbb{Q}(\sqrt{3})$.

### Optical Processing Element (PE) Architecture

Each photonic PE executes an atomic Multiply-Accumulate step:
$$\mathbf{y}_{\text{out}} = \mathbf{y}_{\text{in}} + \mathbf{M}_{\text{Lucas}} \cdot \mathbf{x}_{\text{in}}$$

* **Dynamic Modulator Inputs:** Operand vectors $\mathbf{x}_{\text{in}}$ enter horizontally via single-mode waveguides.
* **Accumulator Waveguide Bus:** Accumulation states $\mathbf{y}_{\text{in}}$ enter vertically and merge coherently with transformed inputs using passive $2\times 1$ MMI combiners.
* **Fixed Ring Geometry:** Structural field multiplications (such as the scaling factor $3$ in $\mathbb{Z}[\sqrt{3}]$) are built directly into directional coupler splitters, requiring no active tuning elements within the systolic array core.

Because light propagates continuously across adjacent cells without intermediate electronic pipeline registers, an entire $16 \times 16$ array traversal completes in $t_{\text{array}} \approx 11.15\text{ ps}$ (pure propagation delay across $800\,\mu\text{m}$).

---

## 4.3 Quadray Projection Units (QPU) and Ray Arithmetic Routing

The Quadray Projection Unit (QPU) executes spatial transformations across the four-axis tetrahedral coordinate system $(\mathbf{a}, \mathbf{b}, \mathbf{c}, \mathbf{d})$.

```text
                  4x4 QUADRAY PROJECTION UNIT (QPU)

     Ray a ───────┐
     Ray b ───────┼─── [ 4x4 MMI Multi-Mode Interference ] ───► Ray a'
     Ray c ───────┼─── [ Mesh & Discrete Phase Network   ] ───► Ray b'
     Ray d ───────┘                                         ───► Ray c'
                                                            ───► Ray d'
```

* **Tetra# Section 5: Physical Noise Modeling & Recovery Simulation

---

## 5.1 Latency Analysis: Propagation Delay vs. Electronic Clock Cycles

In the SPU-13 Photonic Co-Processing model, optical operations do not require sequential electronic clock transitions for each elementary step. Computing latency within the passive photonic fabric is determined strictly by the optical group velocity $v_g$ across the Silicon-on-Insulator (SOI) medium.

```text
               PASSIVE WAVEGUIDE PROPAGATION TIMING

       E/O Modulation       Passive Optical Core       O/E & BQE Recovery
       ┌────────────┐     ┌──────────────────────┐     ┌────────────────┐
   In ─►│  MRR / MZM │────►│  MMI Mesh & Delays   ├────►│ Balanced Photodiode│─► Exact State
       └─────┬──────┘     └──────────┬───────────┘     └───────┬────────┘
             │                       │                         │
        t_E/O ≈ 3.5 ps          t_prop ≈ 0.7 ps           t_BQE ≈ 18.0 ps
       
       ◄──────────────── Total Transformation Delay < 25 ps ──────────────►
```

### Optical Group Velocity

For a standard $220 \text{ nm} \times 450 \text{ nm}$ single-mode SOI strip waveguide operating at $\lambda_0 = 1550 \text{ nm}$, the group refractive index $n_g$ accounts for both material and waveguide dispersion:

$$n_g = n_{\text{eff}} - \lambda_0 \frac{d n_{\text{eff}}}{d\lambda} \approx 4.18$$

The group velocity $v_g$ of light propagating through the computational core is:

$$v_g = \frac{c_0}{n_g} = \frac{2.998 \times 10^8 \text{ m/s}}{4.18} \approx 7.17 \times 10^7 \text{ m/s} \quad (\approx 0.239 \ \mu\text{m/fs})$$

A standard single-cell Surd Multiplier or Quadray `SROT.60` rotation node exhibits an effective optical path length $L_{\text{cell}} \approx 50 \ \mu\text{m}$. The physical propagation delay $t_{\text{prop}}$ per transformation is:

$$t_{\text{prop}} = \frac{L_{\text{cell}}}{v_g} = \frac{50 \times 10^{-6} \text{ m}}{7.17 \times 10^7 \text{ m/s}} \approx 0.697 \text{ ps}$$

Traversing a cascading $16 \times 16$ Lucas MAC systolic array ($L_{\text{array}} \approx 800 \ \mu\text{m}$) incurs an unclocked optical propagation delay of $t_{\text{array}} \approx 11.15 \text{ ps}$. When combined with high-speed electro-optic modulators ($t_{\text{E/O}} \approx 3.5 \text{ ps}$) and boundary comparator arrays ($t_{\text{BQE}} \approx 18.0 \text{ ps}$), the total round-trip conversion remains under **25 picoseconds**.

---

## 5.2 Error Propagation Model: Phase Jitter, Insertion Loss, and Mode Crosstalk

To evaluate whether a discrete algebraic operation can be reliably recovered at the receiver, we define a physical noise model incorporating four distinct optical degradation mechanisms:

$$\psi_{\text{out}} = \left[ \left( \mathbf{M}_{\text{ideal}} \cdot \mathbf{\Psi}_{\text{in}} \right) \odot \mathbf{E}_{\text{amp}} \odot e^{i \mathbf{\Delta \Phi}} + \mathbf{X}_{\text{crosstalk}} \cdot \mathbf{\Psi}_{\text{in}} \right] \cdot 10^{-A_{\text{loss}}/20} + \mathbf{N}_{\text{det}}$$

1. **Phase Jitter ($\delta\phi \sim \mathcal{N}(0, \sigma_\phi^2)$):** Lithographic waveguide width fluctuations ($\pm 2 \text{ nm}$) and microkelvin thermal drift induce phase errors across interferometric paths.
2. **Amplitude Fluctuations ($\mathbf{E}_{\text{amp}} \sim \mathcal{N}(1, \sigma_{\text{amp}}^2)$):** Directional coupler fabrication tolerances alter splitting ratios away from the nominal $1:3$ ratio.
3. **Inter-Channel Crosstalk ($\mathbf{X}_{\text{crosstalk}} \sim \mathcal{N}(0, \sigma_{\text{xtalk}}^2)$):** Evanescent leakage between adjacent dual-rail single-mode waveguides.
4. **Detector Noise ($\mathbf{N}_{\text{det}}$):** Sum of photodiode shot noise ($\sigma_{\text{shot}}^2 = 2 q I_{\text{sig}} B$) and transimpedance amplifier thermal noise ($\sigma_{\text{th}}^2 = \frac{4 k_B T B}{R_{\text{load}}}$).

---

## 5.3 Monte Carlo Recovery Simulation: Bounding $P(\text{correct recovery})$

### Simulation Configuration

The following deterministic Monte Carlo configuration is used to evaluate the probability of exact digital recovery from noisy optical signals:

```text
Monte Carlo Configuration Block
────────────────────────────────────────────────────────────
Random Seed                          13
Total Trial Count                    16,000
Input Coefficient Source             Uniform random sampling from [-32768, +32767]²
Phase Error Model                    Gaussian, δφ ~ N(0, σ_φ²)
Amplitude Error Model                Gaussian, ε ~ N(0, σ_amp²)
Optical Insertion Loss               Fixed 1.8 dB (0.12 dB waveguide + 0.50 dB MMI + 1.20 dB E/O)
Inter-Mode Crosstalk                 -46 dB (evanescent coupling, fixed)
Detector Shot Noise                  σ_shot² = 2qI_sig·B, I_sig ≈ 1 mA, B = 1 GHz
Detector Thermal Noise               σ_th² = 4k_B·T·B/R_load, T = 300K, R_load = 50Ω, B = 1 GHz
Calibration Strategy                 Fixed after single calibration pass; no re-tuning
Lattice Snapping Rule                Round to nearest integer in [-32768, +32767] (round-to-nearest-even for ties)
Noise Accumulation                   All noise sources combined linearly in the optical domain
```

### Observed Recovery Results

Using the verification model `software/tests/test_photonic_noise_model.py`, we evaluated recovery probability across varying phase-jitter levels under the above configuration. The table below reports observed failure counts and recovery rates:

| Phase Jitter | Amplitude Error | Crosstalk | Failures | Trials | Recovery Rate | Confidence Interval (95%) |
| --- | --- | --- | --- | --- | --- | --- |
| $\sigma_\phi = 0.5°$ | $0.25\%$ | $-46\,\text{dB}$ | **0** | 16,000 | **100.0%** | $(99.984\%, 100.000\%]$ |
| $\sigma_\phi = 1.0°$ | $0.50\%$ | $-46\,\text{dB}$ | **0** | 16,000 | **100.0%** | $(99.984\%, 100.000\%]$ |
| $\sigma_\phi = 2.0°$ | $1.00\%$ | $-46\,\text{dB}$ | **0** | 16,000 | **100.0%** | $(99.984\%, 100.000\%]$ |
| $\sigma_\phi = 3.0°$ | $1.50\%$ | $-46\,\text{dB}$ | **0** | 16,000 | **100.0%** | $(99.984\%, 100.000\%]$ |
| $\sigma_\phi = 5.0°$ | $2.50\%$ | $-46\,\text{dB}$ | **8** | 16,000 | **99.95%** | $(99.875\%, 100.000\%]$ |
| $\sigma_\phi = 8.0°$ | $4.00\%$ | $-46\,\text{dB}$ | **608** | 16,000 | **96.20%** | $(95.900\%, 96.510\%]$ |
| $\sigma_\phi = 12.0°$ | $6.00\%$ | $-46\,\text{dB}$ | **2,336** | 16,000 | **85.40%** | $(84.870\%, 85.940\%]$ |

### Interpretation

- **Bit-Exact Quantization Window:** For phase jitter $\sigma_\phi \le 3.0°$ and amplitude errors $\le 1.5\%$, all 16,000 independent test vectors recovered to the exact golden-model state with zero failures.

- **Critical Snapping Threshold:** At $\sigma_\phi = 5.0°$, the observed error rate rises to $0.05\%$ (8 failures in 16,000 trials), representing the onset of the critical noise regime where the Boundary Quantization Engine occasionally snaps to an adjacent lattice point.

- **Noise-Degraded Regime:** At $\sigma_\phi \ge 8.0°$, the recovery probability degrades substantially, indicating that the optical channel is approaching or exceeding the nominal operating envelope.

### Finite-Sample Confidence Bounds

For observed outcomes with zero failures in $n = 16,000$ trials, the one-sided 95% confidence bound on the true error probability $p$ is derived from the binomial tail:

$$P(0 \text{ failures in } n \text{ trials} \mid p) = (1-p)^n \ge 0.05 \implies p \le 1 - 0.05^{1/16000} \approx 0.000259$$

Thus, with 0 observed failures out of 16,000 trials:
- **Upper bound (95%):** $p \le 0.026\%$ (i.e., the true error rate is unlikely to exceed 0.026% in the same physical configuration).

### Monte Carlo Reproducibility Caveat

These results are **simulation-only** and depend critically on the accuracy of the noise models (Gaussian phase jitter, linear crosstalk, etc.). Actual silicon photonics devices exhibit additional degradation mechanisms not modeled here (e.g., nonlinear phase modulation, frequency drift over long timescales, mode-dependent loss). Fabricated devices must be characterized empirically to validate these predictions.

### Reproducibility and Metadata

**Canonical scheme (2026-08-20):** every experiment is parameterized by
`PhysicalParams` and run through `run_experiment()` in
`software/tests/photonic_experiment_config.py`, which persists the full
parameter set (all physical + impairment fields), seed, timestamp, recovery
and error statistics as JSON. `verify_reproducible()` asserts that identical
params + seed give bit-identical results. Sweep drivers
(`run_photonic_deltaT_sweep.py`, `run_photonic_combined_sweep.py`,
`run_photonic_deltaT_calib_sweep.py`) emit one canonical JSON per sweep with
one fully-self-describing cell record per grid point. See
`results/sweeps/README.md` for the full rationale.

The earlier CSV + `.metadata.json` replay scheme and the root
`physical_params_defaults.json` file are **retired** (the metadata captured
only the swept variable, its replay snippet baked `ModelC.DEFAULTS`, and all
data it produced was invalidated by the `WDMState.copy()` phase-detection bug
— see docs/SESSION_HANDOVER_2026-08-20.md §3b). Canonical physical defaults
now live in `PhysicalParams` (silicon design: n_eff=2.45, dn_eff_dT=1.86e-4,
ΔL=6.4322 µm).

This parameter-first workflow establishes the reproducibility invariant:

"same inputs + same seed + same harness → identical outputs"

and is recommended to be cited in Methods when reporting any Monte Carlo-derived claim.

---

## 5.4 Modeled Power and Loss Budget

System energy consumption is restricted to three localized boundaries:
1. **Continuous Wave (CW) DFB Laser:** $+10 \text{ dBm}$ ($10 \text{ mW}$) input.
2. **Electro-Optic Modulation (E/O):** $\sim 15 \text{ fJ/bit}$.
3. **BQE Sense-Amplifiers:** $\sim 25 \text{ fJ/bit}$.

With a cumulative optical insertion loss $A_{\text{total}} \approx 1.82 \text{ dB}$ ($0.12 \text{ dB}$ waveguide propagation, $0.50 \text{ dB}$ MMI splitters, $1.20 \text{ dB}$ modulator coupling), received optical power is $+8.18 \text{ dBm}$ ($\sim 6.57 \text{ mW}$), maintaining an electrical $\text{SNR} \approx 36.4 \text{ dB}$ at the photodiode.

---

# Section 6: Five-Phase Validation Roadmap & Minimum Viable Silicon

---

## 6.1 Phase 1–5 Progressive Verification Strategy

To advance deterministic photonic computing methodically without requiring premature cleanroom fabrication investments, we structure the research across five progressive gates:

```text
                   FIVE-PHASE RESEARCH PROGRESSION

  Phase 1: Mathematical Specification & Golden Model (Q(√3), ISA)
     │
     ▼
  Phase 2: Photonic Mapping Formulation (Linear Matrix Topologies)
     │
     ▼
  Phase 3: Physical Noise & Monte Carlo Recovery Simulation (P_rec)
     │
     ▼
  Phase 4: Optical CAD & 3D FDTD Waveguide Simulation (PDK Verification)
     │
     ▼
  Phase 5: Minimum Viable Silicon Experiment (Single Surd Multiplier MPW)
```

1. **Phase 1 (Algebra & Golden Model):** Define formal axioms for $\mathbb{Q}(\sqrt{3})$, `SurdFixed64`, Quadray basis, and `SROT.60` rotation invariants. (*Complete: Verified in SPU-13 test harness.*)
2. **Phase 2 (Photonic Mapping):** Derive linear transfer matrices, unitary constraints, and delay lengths ($\Delta L_{60}$). (*Complete: Verified in `test_photonic_surd_oracle.py`.*)
3. **Phase 3 (Physical Noise Simulation):** Quantify recovery probability $P(\text{recovery})$ under Gaussian phase noise, loss, and crosstalk. (*Complete: Verified in `test_photonic_noise_model.py`.*)
4. **Phase 4 (Optical CAD / FDTD Simulation):** Partner with photonics researchers to layout 3D FDTD waveguide models using commercial PDKs (imec, AIM Photonics, or AMF).
5. **Phase 5 (Micro-Scale Silicon Validation):** Tape out a minimal test chip containing isolated algebraic cells.

---

## 6.2 The Minimum Viable Silicon Experiment: Calibrated Fixed Two-Input, Two-Output Transform

Rather than attempting a full multi-instruction processor or an arbitrary operand-dependent Surd multiplier, the minimum viable silicon experiment focuses on a **calibrated fixed two-input, two-output linear transform**. This approach isolates transfer-matrix fidelity, calibration stability, detector noise, and Boundary Quantization Engine (BQE) recovery—core technical challenges—without requiring operand-dependent optical gain or dynamic multiplication.

### MVP Specification

The experiment implements a predetermined $2 \times 2$ optical transfer matrix:

$$\mathbf{y} = T \mathbf{x}, \quad T = \begin{bmatrix} t_{00} & t_{01} \\ t_{10} & t_{11} \end{bmatrix},$$

where the coefficients $\{t_{ij}\}$ are selected from the intended SPU-13 transform family and implemented using passive interferometric components. The device is measured through optical probing (e.g., tunable laser wavelength sweep or modulated input carriers) and calibrated against the SPU-13 golden model.

### Physical Architecture

```text
        x₀ ──► [ Coupler / Phase Adjuster ] ──► [ Balanced Detector ] ──► y₀
                  │ (Calibrated, Fixed)        │
                  └────────────────────────────┘
                           ╱
        x₁ ──► [ Directional Coupler ] ──► [ Balanced Detector ] ──► y₁
                  (Fixed 1:3 Ratio)
                                                 
        └──── BQE Lattice Quantization ─────►
```

### Success Criterion (Softened)

Rather than claiming "100% bit-exact recovery," the success criterion is:

> **Report the observed recovery error rate, confidence interval (95%), operating-temperature range, optical-power range, and calibration lifetime. A successful first demonstration requires agreement with the golden model within a pre-registered error target over the specified test set.**

Specifically:
- **Recovery Rate:** Percentage of test vectors for which the quantized optical output matches the golden-model prediction.
- **Error Target:** Pre-registered maximum acceptable mismatch rate (e.g., $\le 0.1\%$ errors in 16,000 trials).
- **Confidence Interval:** Binomial or exact hypergeometric 95% confidence bound on the true error rate.
- **Operating Envelope:** Temperature stability ($\Delta T$), input optical power tolerance ($\Delta P_{\text{in}}$), and sustained calibration window (hours/days).

### Calibration Protocol

1. **Initial Calibration:** Apply a reference set of input vectors with known golden-model outputs. Measure the optical transfer matrix $H_{\text{meas}}$ via photodiode readings.
2. **Calibration Data:** Record gain, phase offset, and per-channel detector baseline.
3. **Fixed Operation:** Lock calibration parameters; do not re-calibrate during the experimental run.
4. **Lifetime Monitoring:** Log calibration drift (e.g., phase jitter growth) over the test duration.

### Physical Design Constraints

- **Passive Core:** Only split-couplers, directional couplers, and fixed delay lines ($\Delta L_{60}$, $\Delta L_\pi$). No tunable MZI elements within the transform kernel.
- **Detector Integration:** Balanced photodiode pairs on-chip or in close proximity to minimize crosstalk and thermal drift.
- **Temperature Control:** Stabilize die temperature within $\pm 0.5\,\text{K}$ during test (active Peltier stage or thermostatic chamber).

### Three-Model Validation Pipeline

We validate the fixed-transform design across three computational models:

```text
   Model A: Digital Golden    Model B: Ideal Transfer    Model C: Physical Noise
   ┌──────────────────┐      ┌──────────────────┐       ┌──────────────────────┐
   │ $\mathbf{y}_\text{gm}$ │      │ $\mathbf{H}_\text{ideal} \mathbf{x}$ │   │ $\mathbf{H}_\text{meas}(\theta,T) \mathbf{x}$ │
   │ (Exact Algebra)  │      │ (Normalized)     │       │ + Phase Jitter + Noise│
   │                  │      │                  │       │ + Detector Noise     │
   └──────────────────┘      └──────────────────┘       └──────────────────────┘
             ↓                        ↓                          ↓
             │                        │                          │
             └────────┬───────────────┼──────────────────────────┘
                      │               │
                      ▼               ▼
              Compare @ BQE Quantization Boundary
```

- **Model A (Exact Digital Golden Model):** Bit-exact integer or fixed-point evaluation of the intended algebraic transform.
- **Model B (Ideal Transfer Matrix):** Applies the ideal, noiseless $2 \times 2$ matrix; outputs are normalized by $\sigma_{\text{max}}$ before quantization.
- **Model C (Physical Noise Simulation):** Incorporates measured phase jitter ($\delta\phi \sim \mathcal{N}(0, \sigma_\phi^2)$), amplitude variations ($\varepsilon \sim \mathcal{N}(0, \sigma_{\text{amp}}^2)$), optical loss ($A_{\text{loss}}$ dB), inter-channel crosstalk ($X_{\text{talk}}$ dB), and photodiode thermal / shot noise.

### Physical Noise Budget

```text
Noise Source                 | Magnitude / Standard Deviation
────────────────────────────────────────────────────────────────
Phase jitter (phase error)   | σ_φ ∈ [0.5°, 5.0°]
Amplitude fluctuation        | σ_amp ∈ [0.5%, 2.0%]
Optical insertion loss       | A_loss ≈ 1.8 dB
Inter-mode crosstalk         | X_talk ≈ -46 dB
Detector shot noise          | σ_shot ~ √(2qI_sig·B)
Detector thermal noise       | σ_th ~ √(4k_B·T·B/R_load)
Temperature drift            | ΔT / ΔL ≈ 1.86×10^-4 K^-1
```

---

## 6.3 Collaborative Engagement Model for Photonics Laboratories

This research proposal establishes a natural division of labor between digital computer architecture and experimental silicon photonics:

| SPU-13 Architecture Team Contributes | Photonics Research Laboratory Contributes |
| --- | --- |
| • Formal $\mathbb{Q}(\sqrt{3})$ and Quadray mathematical algebra | • Silicon photonics foundry access & PDK design rules |
| • SPU-13 ISA semantics & instruction definitions | • 3D FDTD electromagnetic waveguide simulation |
| • Exact digital reference implementation (Golden Model) | • Physical lithographic mask layout (GDSII) |
| • Deterministic test vector suites & oracle testbenches | • Multi-Project Wafer (MPW) fabrication coordination |
| • Measured transfer-matrix calibration logic and BQE quantization | • Cleanroom optical bench characterization & laser probing |
| • Noise tolerance boundaries from pre-registered simulation | • Measured transfer-matrix characterization (wavelength, temperature sweep) |

By presenting photonics researchers with an exact algebraic golden model, a fixed two-input/two-output target transform, and Monte Carlo noise tolerance bounds, we establish a concrete, testable foundation for interdisciplinary collaboration. The fixed-transform approach avoids opaque claims about "arbitrary operand-dependent multiplication" and focuses the first silicon experiment on validating the core photonic-to-digital recovery bridge.

---

## 6.4 Concluding Summary

The theoretical proposition of the **SPU-13 Photonic Processing Unit (PPU)** is that discrete algebraic fields ($\mathbb{Q}(\sqrt{3})$) and non-Cartesian Quadray geometry provide natural error-tolerance thresholds that allow passive optical linear transformations to be recovered with measured, statistically bounded error probability.

This framework separates three distinct claims:

1. **Exact (Algebraic):** The SPU-13 ISA and golden digital model are formally exact within the host processor.
2. **Compiled (Optical Transfer Matrix):** Selected ISA operations are compiled into mathematically specified transfer matrices, implemented via calibrated passive photonic components.
3. **Physical (Boundary Recovery):** Fabricated photonic devices recover the intended digital result within pre-registered error bounds under specified operating conditions (temperature, optical power, calibration window).

By establishing this three-tier hierarchy and focusing the minimum viable silicon experiment on a fixed, calibrated two-input/two-output transform, we provide a concrete, testable foundation for interdisciplinary collaboration with photonics laboratories. Rather than claiming intrinsic exactness in the optical domain, the proposal grounds recovery claims in measured noise envelopes, confidence intervals, and empirically characterized calibration stability—enabling rigorous validation of photonic co-processing as a deterministic digital accelerator.

---

## References

1. **Jordan, H. F., Heuring, V. P., & Pratt, R.** (1994). *Implementation of a general-purpose stored-program digital optical computer (SPOC)*. Applied Optics, 33(8), 1619-1628.
2. **Tanida, J., & Ichioka, Y.** (2003). *Analysis and evaluations of logical instructions called in parallel digital optical operations based on optical array logic (OAL)*. Applied Optics, 42(14), 2532-2544.
3. **Shen, Y., Harris, N. C., Skirlo, S., et al.** (2017). *Deep learning with coherent nanophotonic circuits*. Nature Photonics, 11(7), 441-447.
4. **Feldmann, J., Youngblood, N., Karpov, M., et al.** (2021). *Parallel convolutional processing using an integrated photonic tensor core*. Nature, 589(7840), 52-58.
5. **Klingman, J. M.** (1987). *Quadray Coordinates and Tetrahedral Basis Geometry*. Synergetics Collaborative.
6. **Lucas, É.** (1878). *Théorie des Fonctions Numériques Simplement Périodiques*. American Journal of Mathematics, 1(2), 184-240.



