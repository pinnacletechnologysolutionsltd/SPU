# RPLU v2 Formal Specification — Split-Biquadratic Thimble-Padé Pipeline

**Version:** 1.0
**Date:** June 2026
**Status:** RTL testbench-verified, awaiting full place-and-route on Tang 25K

## 1. Overview

The RPLU v2 (Rational Processing and Logic Unit) is a 4-stage pipeline that evaluates
Lefschetz-style rational approximants over the M31 split-biquadratic algebra

$$A_{31} = \mathbb{F}_p[u,v] / (u^2 - 3,\; v^2 - 5), \quad p = 2^{31} - 1.$$

Elements are represented in the basis $[1, u, v, uv]$, historically named
`[1, √3, √5, √15]` in the RTL. This replaces the legacy Morse-potential
lookup table with deterministic modular arithmetic over a finite commutative
ring. It is not a field for M31: both 3 and 5 are quadratic non-residues, so
15 is a quadratic residue and the algebra has structural zero-divisors.

Pipeline stages:

```
Φ₁:  Kohonen SOM BMU  →  Φ₂: BTU spatial router  →  Φ₃: [4/4] Padé + A31 unit inverter  →  Φ₄: Output latch
```

### 1.1 Design Principles

1. **No floating-point.** All arithmetic is exact modular arithmetic in $A_{31}$.
2. **No division.** Unit inversion uses the conjugate reduction tower (fixed ~76 cycles).
3. **No runtime dynamic resolution.** Every pipeline path has deterministic latency.
4. **No silent failures.** Non-unit/zero-norm singularities assert FLAGS.V and cleanly trap.
5. **Bit-exact reproducibility.** Every result deterministically matches the Python/C++ oracle.

## 2. Finite Algebra Foundation

### 2.1 M31: The Mersenne Prime

$$p = 2^{31} - 1 = 2147483647$$

M31 enables fast bitwise reduction: $x \bmod p = x_{\text{lo}} + x_{\text{hi}}$ with
a single conditional subtract. This eliminates the need for costly Barrett or Montgomery
reduction circuits for operands ≤ 72 bits.

### 2.2 The Split Biquadratic Algebra A_{31}

Basis: $[1, u, v, uv]$ where:

$$
u^2 \equiv 3, \quad v^2 \equiv 5, \quad (uv)^2 \equiv 15 \pmod{p}
$$

Quadratic non-residue status verified via Euler's criterion: $3^{(p-1)/2} \equiv -1 \pmod{p}$,
$5^{(p-1)/2} \equiv -1 \pmod{p}$.

Because the product of two non-residues is a residue, $15^{(p-1)/2} \equiv 1
\pmod{p}$ for M31. Concretely, $1393679181^2 \equiv 15 \pmod{p}$. Therefore
the current basis is a split biquadratic ring, not $\mathbb{F}_{p^4}$. The
zero-norm detector is consequently a unit detector: elements with zero norm
are non-units and may be nonzero zero-divisors.

Multiplication rules (commutative):

| × | 1 | √3 | √5 | √15 |
|:---|:--|:---|:---|:----|
| 1 | 1 | √3 | √5 | √15 |
| √3 | √3 | 3 | √15 | 3√5 |
| √5 | √5 | √15 | 5 | 5√3 |
| √15 | √15 | 3√5 | 5√3 | 15 |

An element $Z \in A_{31}$ is represented as $(z_0, z_1, z_2, z_3)$ where
$Z = z_0 + z_1u + z_2v + z_3uv$ with all $z_i \in [0, p-1]$.

### 2.3 Nested Quadratic Extension Structure

$$ \mathbb{F}_p \subset \mathbb{F}_p[u]/(u^2-3) \subset A_{31} $$

Write $Z = A + Bv$ where $A = z_0 + z_1u$ and $B = z_2 + z_3u$
are elements of $\mathbb{F}_p[u]/(u^2-3)$.

The relative norm from $A_{31}$ to $\mathbb{F}_p[u]/(u^2-3)$ is:

$$ N_1(Z) = Z \cdot \sigma_v(Z) = A^2 - 5B^2 \in \mathbb{F}_p[u]/(u^2-3) $$

where $\sigma_v$ flips the sign of $v$ and $uv$.

The norm from $\mathbb{F}_p[u]/(u^2-3)$ to $\mathbb{F}_p$ is:

$$ N_2(W) = W \cdot \sigma_u(W) = w_0^2 - 3w_1^2 \in \mathbb{F}_p $$

The full algebra norm is $N(Z) = N_2(N_1(Z))$. $Z$ is a unit iff $N(Z) \ne 0$.

## 3. Arithmetic Pipeline

### 3.1 A_{31} Multiplier (`spu13_m31_multiplier.v`)

**Architecture:** 2-stage pipelined, 16 parallel 32×32 DSP products.

**Input:** Two $A_{31}$ elements A = (a₀, a₁, a₂, a₃), B = (b₀, b₁, b₂, b₃).

**Formula:**

$$
\begin{aligned}
r_0 &= a_0b_0 + 3a_1b_1 + 5a_2b_2 + 15a_3b_3 \pmod{p} \\
r_1 &= a_0b_1 + a_1b_0 + 5a_2b_3 + 5a_3b_2 \pmod{p} \\
r_2 &= a_0b_2 + 3a_1b_3 + a_2b_0 + 3a_3b_1 \pmod{p} \\
r_3 &= a_0b_3 + a_1b_2 + a_2b_1 + a_3b_0 \pmod{p}
\end{aligned}
$$

**Stage 1:** 16 parallel integer multiplier → 72-bit accumulator.
**Stage 2:** Fast Mersenne reduction: split 72-bit result into $x_{\text{hi}}$ (bits [71:31]) and
$x_{\text{lo}}$ (bits [30:0]), compute $x_{\text{lo}} + x_{\text{hi}}$, conditionally subtract $p$ if $\ge p$.

**Resource:** 16 DSP slices.

### 3.2 M31 Scalar Inverter (`spu13_m31_inverter.v`)

**Algorithm:** Binary Extended Euclidean Algorithm (BEEA).

**Operation:** Given $x \in [1, p-1]$, compute $x^{-1} \bmod p$ such that $x \cdot x^{-1} \equiv 1 \pmod{p}$.

**Implementation:** Zero divisions. Iterative shift-subtract loop with conditional P-add.
Terminates in ~30 cycles for worst-case inputs.

**Resource:** ~180 LUTs.

### 3.3 A_{31} Unit Inverter (`spu13_fp4_inverter.v`)

**Architecture:** 4-phase iterative tower: TWO conjugate collapses then Fermat reconstruction.

**Phase A — Relative Norm to F_{p^2}:**
1. $A = z_0 + z_1\sqrt{3}$, $B = z_2 + z_3\sqrt{3}$
2. $D = A^2 - 5B^2 = (d_0, d_1, 0, 0) \in \mathbb{F}_p[u]/(u^2-3)$

**Phase B — Norm to Scalar:**
3. $N = d_0^2 - 3d_1^2 \in \mathbb{F}_p$

**Phase C — Zero-Norm Detection:**
4. If $N \equiv 0 \pmod{p}$: assert FLAGS.V (non-unit/zero-divisor), bypass Fermat chain, output zero.
5. Otherwise: $N^{-1} = N^{p-2} \bmod p$ (Fermat chain, 30-step square-and-multiply).

**Phase D — Reconstruction:**
6. $Z^{-1} = (A - B\sqrt{5}) \cdot D^{-1}$ where $D^{-1} = (d_0 - d_1\sqrt{3}) \cdot N^{-1}$.

**Latency:** ~76 cycles (deterministic).
**Zero-norm trap:** Combinational zero-detect between Phase B and Phase C. No cycles wasted on
the Fermat chain when $N = 0$.

## 4. Pipeline Stages

### 4.1 Stage Φ₁ — Kohonen SOM BMU (`spu_som_node.v`, `spu_som_node_array.v`)

**Node architecture:** 3-stage parallel quadrance pipeline:
1. **Subtract:** Feature vector − weight vector (per dimension)
2. **Square:** Field-square each delta in Q(√3)
3. **Accumulate:** Weighted sum of squared deltas

**Node array:** 7-node parallel instantiation with combinational winner-take-all (WTA) tree.

**Outputs:**
- `best_node_id` — index of minimum-quadrance node
- `second_node_id` — runner-up (for confidence gap)
- `confidence_gap` — weighted quadrance difference (WTA margin)

**Training port:** 36-bit widened multiply (α·h neighborhood scaling). SOM_TRAIN (0x2B)
updates weights in-situ.

**Resource per node:** ~200 LUTs (quadrance) + ~100 LUTs (training).

### 4.2 Stage Φ₂ — BTU Spatial Router (`spu13_btu_core_top.v`)

**Function:** Kohonen BMU spatial index → $A_{31}$ element routing.

**Architecture:** 4-lane BRAM lookup + inter-lane combination.

**Collision Resolver (`spu_btu_collision_resolver.v`):**
- 64→6 priority encoder (selects lowest-index active neuron)
- Backlog queue for multi-hot wave interference
- Bubble stall: asserts `pipeline_stall` to upstream stage
- O(n) latency where n = number of simultaneous saddle-point activations

**BTU address space:** 64 neurons per cluster, 4 clusters per quadrant.

### 4.3 Stage Φ₃ — [4/4] Padé Rational Approximant (`rplu_thimble_pade.v`)

**Function:** Evaluate $R(x) = \frac{\sum_{i=0}^{4} p_i x^i}{\sum_{i=0}^{4} q_i x^i}$ via Horner's method.

**Architecture:**
- Numerator: Horner evaluation $(···(p_4·x + p_3)·x + ··· + p_0)$
- Denominator: Parallel Horner $(···(q_4·x + q_3)·x + ··· + q_0)$
- Unit inversion: $A_{31}$ conjugate reduction tower (Section 3.3) to compute $D^{-1}$, then multiply.

**Coefficient storage:** 2 × 5 × 32-bit BRAM (numerator + denominator coefficient banks).
Coefficients loaded at boot via config port.

**Latency:** 12 cycles (Horner) + ~76 cycles (inverter) = ~88 cycles total.

**Zero-norm handling:** If denominator evaluates to a non-unit in $A_{31}$ (norm = 0),
the Padé stage asserts FLAGS.V and bypasses the divider. This is the "singular absorber"
boundary condition — the hardware safely drops the done flag rather than hanging.

### 4.4 Stage Φ₄ — Output Latch

Final rational contribution latched into the 4R2W register file with write-forwarding bypass
(`spu13_multi_port_regfile.v`).

## 5. Lookahead Hazard Unit (LHU) Scoreboarding

The 4R2W register file supports concurrent single-cycle arithmetic alongside the multi-cycle
Conjugate Inversion Tower. The LHU tracks register scoreboard bits (RAW/WAW hazards).

**Rules:**
- Single-cycle ops (QADD, QMUL, QSUB): can issue every cycle
- Tower ops (PHSLK, INVJ, Padé eval): stall issue until tower done + writeback
- Write-forwarding: result available to next instruction on same cycle as writeback

**Scoreboard depth:** 2 outstanding writes (tower + single-cycle).

## 6. Verification

### 6.1 Three-Layer Verification Stack

| Layer | Language | Number | Role |
|:------|:---------|:-------|:-----|
| Behavioral oracle | Python | 24+ | BMU classification, weighted quadrance, stable tie-breaking |
| C++ oracle | C++17 | 24+ | Cycle-accurate parity with Python oracle |
| RTL simulation | Verilog (iverilog) | 17 | $A_{31}$ arithmetic, BTU collision, Padé evaluation |

**Cross-validation:** All three layers produce bit-identical results for the same test vectors.
The Python and C++ oracles directly mirror the clock-edge execution of the Verilog testbenches.

### 6.2 Test Vector Catalog

**A_{31} Multiplier** (9 vectors):
- Identity, scalar multiply, √3² = 3, √5² = 5, √15² = 15
- √3·√5 = √15, M31 edge case (P−1)×2, mixed (10,2,0,4)×(5,0,1,2), zero multiply

**A_{31} Unit Inverter** (6 vectors):
- Identity, scalar inv(2), pure √3 inv, pure √5 inv, zero-norm singularity, random self-consistency

**Singular Absorber** (5 scenarios):
- Valid inversion, zero → singularity trap, false positive guard (unity), clean re-arm after exception, post-exception valid operation

**BTU Collision Resolver** (4 scenarios):
- Single node dispatch, two-node serialization, three-node serialization, idle

**SOM BMU** (3 benchmarks):
- Integer BMU classification, surd BMU, stable tie-breaking with ambiguity

## 7. Resource Profile

| Resource | Legacy (Morse LUT) | RPLU v2 ($A_{31}$) | Trade |
|:---------|:-------------------|:------------------|:------|
| LUTs | ~1,100 | ~3,300 | +3× for 4× functional coverage |
| BRAMs | 6–8 | 8 | Parity |
| DSPs | 4 | 16 | +4× for exact modular algebra |
| Pipeline stages | 2 | 4 | Deeper but fixed-latency |

Target device: Gowin GW5A-25A (Tang Primer 25K, 8,256 LUT4s).
Total with rotor core + sequencer + VE init: ~5,500 LUTs (~67% utilization).

## 8. Instruction Interface

The RPLU is accessed through the SPU-13 ISA:

| Opcode | Mnemonic | Function |
|:-------|:---------|:---------|
| 0x2A | SOM | SOM BMU classification (Φ₁ → Φ₂) |
| 0x2B | SOM_TRAIN | SOM weight training update |
| 0x42 | PHSLK | Phase-lock via $A_{31}$ unit checks |
| 0x43 | INVJ | $A_{31}$ unit inverse |
| 0x20 | QADD | Quadrance addition (single-cycle) |
| 0x21 | QSUB | Quadrance subtraction |
| 0x22 | QMUL | Quadrance multiply ($A_{31}$ multiplier) |

## 9. References

1. Hung Son Nguyen, "Tolerance Rough Sets," Fundamenta Informaticae, 1999.
2. Wheeler & Feynman, "Interaction with the Absorber as the Mechanism of Radiation," Rev. Mod. Phys. 17, 1945.
3. Mersenne prime M31: $2^{31} - 1$ — fast reduction for finite modular arithmetic.
4. Padé, H., "Sur la représentation approchée d'une fonction par des fractions rationnelles," 1892.
5. Kohonen, T., "Self-Organizing Maps," Springer, 1995.

## Appendix A: Dual Formal-Jet Extension

### A.1 The Dual Ring $\mathbb{A}_{\text{SPU}} = A_{31}[\epsilon]/(\epsilon^2)$

The RPLU v2 architecture extends naturally to a dual-number quotient ring:

$$\mathbb{A}_{\text{SPU}} = A_{31}[\epsilon] / (\epsilon^2)$$

Here $\epsilon$ is a nilpotent formal generator of the quotient ring:
$\epsilon \neq 0$ and $\epsilon^2 = 0$. It is not an analytic infinitesimal
and does not refer to a limiting process.

An element $R \in \mathbb{A}_{\text{SPU}}$ is:

$$R = A + \epsilon B, \quad A, B \in A_{31}$$

- $A$ (the base part) encodes position / value
- $B$ (the $\epsilon$ coefficient) encodes the exact derivative / velocity

**Key property:** For any rational function $f$ defined over $A_{31}$ whose
required denominators are units,
$f(A + \epsilon B) = f(A) + \epsilon \cdot f'(A) \cdot B$ (automatic differentiation).

### A.2 Arithmetic Over A\_SPU

**Addition** (pairwise):

$$(A + \epsilon B) + (C + \epsilon D) = (A + C) + \epsilon(B + D)$$

Requires 2 × $A_{31}$ additions. Latency: 2 cycles (pipelined → 1 effective).

**Multiplication** (cross-term, $\epsilon^2 = 0$):

$$(A + \epsilon B)(C + \epsilon D) = AC + \epsilon(AD + BC)$$

Requires 3 × $A_{31}$ multiplications + 2 additions.
Latency: 3 multiplies cascaded → ~6 cycles (2-stage multiplier pipeline).

**Inversion** (dual-number inverse formula):

$$(A + \epsilon B)^{-1} = A^{-1} - \epsilon \cdot A^{-1} \cdot B \cdot A^{-1}$$

Requires 1 × tower unit inversion + 2 × multiplications.
Latency: ~80 cycles plus register-pair sequencing.

### A.3 Register-Pairing Multiplexer

The `spu13_nsa_regfile_wrapper.v` implements the dual-lane split:

```
Register layout (dual mode, 8 dual-number slots):
  Slot 0: Real → reg[0..3],   Epsilon → reg[4..7]
  Slot 1: Real → reg[8..11],  Epsilon → reg[12..15]
```

**Even-register writes** (via standard alpha port): Update real part $A$ only.
**Odd-register writes**: Update $\epsilon$ part $B$ only.
**Dual write** (`nsa_pair_write_en`): 8-cycle burst writes both $A$ and $B$
simultaneously, sequenced through the alpha write port.
**Dual read** (`nsa_pair_read_en`): 2-cycle burst read (4 regs/cycle using all
4 read ports), capturing both $A$ and $B$.

### A.4 Relationship to Wildberger Rational Trigonometry

The dual-ring extension gives a finite algebraic bridge between rational
trigonometry and automatic differentiation:

| Approach | Maps to | Computation |
|:---------|:--------|:------------|
| Wildberger rational trigonometry | Real part $A$ | Quadrance, spread (exact, no limits) |
| Dual formal-jet calculus | $\epsilon$ coefficient $B$ | Exact derivative (automatic differentiation) |

In the Wildberger framework, the derivative of a rational function $f$ is
obtained algebraically via the tangent construction (spread). In the dual-ring
framework, it is obtained via the $B$-coefficient of $f(A + \epsilon B)$.
These two formulations produce **identical integer results** over the
dual ring, confirming that the linear spread calculus of rational
trigonometry and formal dual arithmetic agree when restricted to rational
functions over the chosen finite algebra—no limits, no
$\delta$-$\epsilon$ arguments, no approximations.

### A.5 Dual QADD Opcode (Proposed)

**Opcode:** NSA_DQADD (0x46) — Dual quadrance addition over $\mathbb{A}_{\text{SPU}}$.

**Semantics:** Given dual numbers $R_A = A + \epsilon B$ (slot `ra`) and
$R_C = C + \epsilon D$ (slot `rb`), compute $R_A + R_C$ and store in
slot `rd`.

**Pipeline:**
1. Dual-read slot `ra`: capture $A$ and $B$ (2 cycles)
2. Dual-read slot `rb`: capture $C$ and $D$ (2 cycles)
3. $A + C$ → $A_{31}$ adder (1 cycle)
4. $B + D$ → $A_{31}$ adder (1 cycle, parallel to step 3)
5. Dual-write slot `rd`: burst write result $A+C + \epsilon(B+D)$ (8 cycles)

Total: ~14 cycles, fully pipelined.

### A.6 Dual QMUL Opcode (Proposed)

**Opcode:** NSA_DQMUL (0x47) — Dual quadrance multiply over $\mathbb{A}_{\text{SPU}}$.

**Semantics:** $(A + \epsilon B)(C + \epsilon D) = AC + \epsilon(AD + BC)$.

**Pipeline:**
1. Dual-read slot `ra` (2 cycles)
2. Dual-read slot `rb` (2 cycles)
3. $AC$ → $A_{31}$ multiplier (2 cycles, pipelined)
4. $AD$ → $A_{31}$ multiplier (2 cycles, parallel to step 3)
5. $BC$ → $A_{31}$ multiplier (2 cycles, parallel to step 3)
6. $AD + BC$ → $A_{31}$ adder (1 cycle)
7. Dual-write slot `rd`: burst write $AC + \epsilon(AD+BC)$ (8 cycles)

Total: ~17 cycles. The three multiplies in step 3-5 share the 16-DSP multiplier
via the TDM rotor core, serializing over 3 × 2 = 6 cycles.
With a second multiplier instance (requiring 16 more DSPs), this falls
to ~13 cycles.

## Appendix B: RPLU 2.0 — Truncated Jet Algebra $A_{31}[\varepsilon]/(\varepsilon^3)$

### B.1 Motivation

The dual-number ring $A_{31}[\varepsilon]/(\varepsilon^2)$ captures position and
first derivative (velocity). The truncated jet algebra $A_{31}[\varepsilon]/(\varepsilon^3)$
extends this to second derivatives (acceleration), enabling exact kinematic chains
(position, velocity, acceleration) in a single register triple — critical for robotic
forward/inverse kinematics, wave-boundary second-order conditions, and
momentum-informed SOM training.

The truncation is part of the algebra before evaluation, not an after-the-fact
approximation of an infinite Taylor series. RPLU operates in the quotient
$A_{31}[\varepsilon]/(\varepsilon^{N+1})$, so every term of degree greater than
$N$ is identically zero by definition. Cauchy products and rational Padé
blueprints are therefore finite polynomial/rational operations over $A_{31}$;
the only runtime trap is an attempted inversion of a non-unit base coefficient.

### B.2 The Jet Ring

$$\mathbb{A}_{\text{SPU}} = A_{31}[\varepsilon] / (\varepsilon^3), \quad \varepsilon^3 = 0$$

An element is a 3-tuple:

$$J = j_0 + j_1\varepsilon + j_2\varepsilon^2, \quad j_0, j_1, j_2 \in A_{31}$$

- $j_0$: position term ($\varepsilon^0$)
- $j_1$: velocity term ($\varepsilon^1$) — exact first derivative
- $j_2$: acceleration term ($\varepsilon^2$) — exact second derivative

### B.3 Arithmetic

**Addition** (3 pairwise $A_{31}$ adds, 3 cycles → 1 pipelined):

$$(j_0 + j_1\varepsilon + j_2\varepsilon^2) + (k_0 + k_1\varepsilon + k_2\varepsilon^2) = (j_0 + k_0) + (j_1 + k_1)\varepsilon + (j_2 + k_2)\varepsilon^2$$

**Multiplication** ($\varepsilon^3 = 0$ truncates all terms ≥ 3):

$$J \cdot K = j_0k_0 + (j_0k_1 + j_1k_0)\varepsilon + (j_0k_2 + j_1k_1 + j_2k_0)\varepsilon^2$$

Requires 6 $A_{31}$ multiplications + 4 additions. Single M31 multiplier: ~12 cycles.

**Inversion:** $J^{-1} = m_0 + m_1\varepsilon + m_2\varepsilon^2$.

- $m_0 = j_0^{-1}$ (76-cycle conjugate reduction tower, only if $j_0$ is a unit)
- $m_1 = -m_0 \cdot j_1 \cdot m_0$ (2 multiplies + 1 negate)
- $m_2 = j_1^2 \cdot m_0^3 - j_2 \cdot m_0^2$ (4 multiplies + 2 adds + 1 negate)

Total: 1 tower inversion + 6 multiplications + 3 additions. ~94 cycles.

**Invertibility condition:** $J$ is invertible iff $j_0 \in A_{31}^{\times}$.
Equivalently, the hardware norm of $j_0$ must be nonzero. If $j_0$ is a
non-unit, the element is trapped with `err_zero_divisor`/FLAGS.V and routed to
the absorbing boundary.

### B.4 Register Layout (Triple-Lane)

With 16 × 32-bit registers, each jet occupies 12 registers (3 $A_{31}$ elements × 4 coefficients):

```
Slot 0: j0 → reg[0..3], j1 → reg[4..7], j2 → reg[8..11]
Slot 1: j0 → reg[12..15] — only 1 jet slot fits in 16 registers
```

For Wukong (larger register file), expand to 32 registers for 2 full jet slots.

### B.5 Relationship to Dual Numbers

| Feature | Dual ($\varepsilon^2=0$) | Jet ($\varepsilon^3=0$) |
|:--------|:------------------------|:------------------------|
| Terms | 2 (position, velocity) | 3 (position, velocity, acceleration) |
| Multiply ops | 3 $A_{31}$ | 6 $A_{31}$ |
| Inverse tower runs | 1 (for A⁻¹) | 1 (for j₀⁻¹) |
| Zero-divisor check | A is a unit | j₀ is a unit |
| Max jet depth | 1st derivative | 2nd derivative |
| Registers per slot | 8 | 12 |

The $\varepsilon^3=0$ ring strictly contains the $\varepsilon^2=0$ ring (set $j_2=0$).
