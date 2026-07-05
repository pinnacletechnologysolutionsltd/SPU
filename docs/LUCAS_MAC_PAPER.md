# Zero-Drift Lucas-Prime Phinary Arithmetic for Exact Quantum Phase Coherence on FPGA

**Authors:** John Curley

**Affiliation:** Independent Researcher, SPU-13 Project

**Date:** July 2026

**Status:** Pre-release technical report; RTL/oracle verified, Tang 25K PHSLK microprobe measured, Artix-7 sidecar timing closure pending

**Implementation state:** Wukong Artix-7 sidecar profile: 4,521 estimated LCs, 40 DSP48E1 slices, routed max 4.11 MHz in the current 2 MHz bench image. Tang 25K PHSLK microprobe: 200.40 MHz post-route, UART-verified.

---

## Abstract

Traditional spatial transformations rely on transcendental approximations
(sin/cos, π, √5) that introduce floating-point drift, destroying structural
exactness over long runtimes.  We present a hardware co-processor operating
over the golden ring ℤ[φ] modulo a Lucas prime Lₚ that performs chiral
transformations and φ-scaling through integer shift-and-add operations —
zero floating-point, bit-exact closure. The PSCALE/PCHIRAL fast paths remain
zero-DSP shift-add transforms, while the current PMUL/PINV proof maps to
Artix-7 DSP48E1 slices through a bounded Barrett reducer. PSCALE achieves
single-cycle φ-multiplication via the identity φ·(a+bφ) = b + (a+b)φ. The
software oracle verifies exact period closure for PSCALE and an additional
mixed PSCALE/PMUL/PINV identity sequence over 166,666 identity macros
(999,996 primitive operations), with exact return at closure boundaries. The
`PHSLK` predicate checks rational phase coherence by cross multiplication and
reports zero-divisor denominators without invoking inversion.
Designed as a companion to the SPU-13 Mersenne-ring core, this work targets
deterministic exact arithmetic for geometric algebra. The quantum-control
scope is intentionally narrow: we discuss exact ℤ[φ] phase comparison
(`PHSLK`) as a potential preprocessing kernel for reduced rational templates
in Fibonacci-anyon and φ-weighted syndrome-matching applications, not as a
complete QEC decoder or photonic controller. The current Wukong image is a
low-MHz bring-up build pending timing closure; this paper does not claim
sub-100ns full-sidecar latency on current hardware.

---

## Notation

| Symbol | Meaning |
|---|---|
| ℤ[φ] | Golden ring {a + bφ \| a,b ∈ ℤ}, also written Z[phi] in code |
| Lₚ | General Lucas prime modulus (p prime, Lₚ prime) |
| L₁₃ = 521 | Concrete instantiated modulus in this co-processor |
| M31 | Mersenne prime 2³¹−1, base field of the SPU-13 binary core |
| BTU | Barycentric Transmutation Unit, bridges M31 ↔ ℤ[φ]/Lₚ |
| PSCALE | φ-multiply opcode (1 cycle, 0 DSP) |
| PCHIRAL | φ-conjugation opcode (1 cycle, 0 DSP) |
| PMUL | Full ℤ[φ] multiply (3 cycles, DSP) |
| PINV | ℤ[φ] inverse via norm-conjugation (bounded GCD) |
| PHSLK | Rational phase coherence predicate by cross multiplication |
| QR | Quadray register file (64-bit ring-agnostic pairs) |

---

## 1. Introduction

### 1.1 The Transcendental Drift Problem

Any computation involving irrational constants — π, √2, √5, the golden
ratio φ — must either approximate them as finite-precision floats or
work in an algebraic extension where they are native.  The former
accumulates error; the latter preserves exactness.  For applications
requiring millions of sequential geometric operations (robotics forward
kinematics, photonic quantum error correction, jitterbug transformations),
sub-ULP drift compounds into structural collapse.

### 1.2 The Phinary Solution

The golden ratio φ = (1+√5)/2 satisfies φ² = φ + 1.  In the ring
ℤ[φ] = {a + bφ | a,b ∈ ℤ}, multiplication by φ is a single shift-and-add:
no multiplier, no divider, no DSP.  Choosing a Lucas prime Lₚ as modulus
provides the phinary analogue of the Mersenne prime's fast bit-wrap
reduction: φᵖ ≡ ±1 (mod Lₚ) enables deterministic period closure.

### 1.3 Contributions

1. A Verilog RTL implementation of PSCALE/PCHIRAL/PMUL/PINV over ℤ[φ]/L₅₂₁,
   exposed as an Artix-7 sidecar.
2. Empirical proof of the zero-drift invariant: 38,461 PSCALE period
   boundaries and 166,666 mixed PSCALE/PMUL/PINV identity macros return to
   the exact starting bit pattern. Each identity macro is PSCALE, PINV(phi),
   PMUL by `phi^-1`, PMUL by `g`, PINV(g), and PMUL by `g^-1`, verifying
   `phi * phi^-1 * g * g^-1 = 1`.
3. A PHSLK coherence predicate that checks rational phase equality by
   cross multiplication, avoiding direct denominator inversion.
4. A physically mapped PMUL/PINV path using compile-time Barrett reduction,
   synthesized, routed, and packed in the Artix-7 LUCAS spin.

---

## 2. Mathematical Foundation

### 2.1 The Golden Ring ℤ[φ]

φ is a root of x² − x − 1 = 0, giving φ² = φ + 1.  Elements are a + bφ
with a,b ∈ ℤ.  Arithmetic:

```
Addition:    (a+bφ) + (c+dφ)  = (a+c) + (b+d)φ
PSCALE:      φ·(a+bφ)         = b + (a+b)φ          ← 0 multiplies!
PCHIRAL:     conj(a+bφ)       = (a+b) − bφ          ← 0 multiplies!
PMUL:        (a+bφ)(c+dφ)     = (ac+bd) + (ad+bc+bd)φ
Norm:        N(a+bφ)          = a² + ab − b²
PINV:        (a+bφ)⁻¹         = conj(a+bφ) · N(a+bφ)⁻¹
```

### 2.2 Lucas Primes as Moduli

The Lucas sequence Lₙ = φⁿ + (−1)ⁿφ⁻ⁿ.  When p is prime and Lₚ is prime:

| p | Lₚ | φ period mod Lₚ |
|---|-----|-----------------|
| 5 | 11  | 10              |
| 7 | 29  | 14              |
| 11| 199 | 22              |
| 13| 521 | 26              |
| 17| 3571| 34              |

This co-processor uses L₁₃ = 521 with φ period 26.  The period guarantees
that φ²⁶ ≡ 1 (mod 521), providing the zero-drift invariant (defined as exact
bit-match return to seed after a full orbit).

The period is also a real application constraint. L₁₃ is appropriate for a
small proof target and for validating the datapath, but it is not by itself a
claim that a 100- to 1000-node syndrome graph can be embedded without aliasing.
Larger Lucas moduli or residue-number tiling are required when the topology
being encoded needs a phase horizon longer than 26 φ-steps.

For PHSLK, the relevant constraint is whether reduced numerator/denominator
pairs alias inside this finite residue domain; the 26-step φ-period is a
warning sign for long braid, fusion, or syndrome histories.

### 2.3 PHSLK Without Denominator Inversion

Given two rational phase encodings over ℤ[φ]/L₅₂₁,

```
A = n1 / d1,   B = n2 / d2
```

PHSLK checks coherence with the cross product

```
n1*d2 == n2*d1
```

instead of computing `d1^-1` or `d2^-1`. This matters because 521 ≡ 1
(mod 5), so `x^2 - x - 1` splits modulo 521 and ℤ[φ]/L₅₂₁ contains
zero-divisors. Denominators with norm zero do not have a defined
multiplicative inverse. The RTL therefore reports a denominator
zero-divisor status bit alongside the coherence predicate rather than
treating it as a PINV failure.

Consider a concrete Fibonacci anyon fusion amplitude involving φ:
the F-symbol for the Fibonacci braid group is proportional to
φ^{-1} ≈ 0.618. Over ℤ[φ]/L₅₂₁, this becomes a rational pair
(1, φ)⁻¹. A template-matching PHSLK check comparing an observed phase

```
A = (3+5φ) / (2+3φ)    observed template
B = (1+0φ) / (1+0φ)    target identity
```

computes n1·d2 = (3+5φ)·1 = 3+5φ and n2·d1 = (1+0φ)·(2+3φ) = 2+3φ.
These are equal only if (3+5φ) = (2+3φ), which over ℤ[φ]/L₅₂₁ fails
unless 3≡2 and 5≡3 mod 521 — a contradiction. The non-match correctly
reports `coherent=0`. If instead the template genuinely matches,
n1·d2 = n2·d1 exactly and the cross product returns `coherent=1`
without ever needing φ⁻¹.

### 2.4 Why Not Merge with Mersenne Rings

Primes in ℤ do not stay prime in ℤ[φ].  For example, 11 = (3+φ)(4−φ)
in ℤ[φ].  Merging the M₃₁ binary ring with ℤ[φ] would introduce
zero-divisors.  The primary architectural driver for isolating the rings is
representation stability and pipeline execution semantics: preventing
data-type pollution in the deterministic M31 execution lanes.  While
both rings are algebraically sound in isolation, their operational
semantics benefit from clean separation at the BTU boundary.

---

## 3. Hardware Architecture & The Lucas Mapping

### 3.1 The Barycentric Transmutation Unit (BTU) Bridge

Data traversing the boundary from the M31 binary core (M31 = 2³¹−1)
to the ℤ[φ]/Lₚ co-processor must undergo an immediate dimensional and
bit-width down-sampling.  Elements exiting the primary core are bounded
by the Mersenne modulus (x ≤ 2³¹−2), whereas the Phinary execution path
requires inputs natively reduced to a chosen Lucas prime modulus Lₚ
(e.g., L₁₃ = 521).

In the SPU-13 pipeline, the BTU is a general-purpose router handling multiple
lanes: the same unit routes SOM/BMU spatial indices to the A₃₁ Padé evaluator
in the RPLU v2 pipeline, and M31 coefficients to the ℤ[φ] MAC here. The
routing topology is configurable per lane at synthesis time.

To keep the datapath compatible with future low-latency deterministic SPU-13
pipeline targets, this macro-modulo transformation must bypass both
iterative subtraction (which introduces non-deterministic execution
stalls up to thousands of cycles) and large combinational ROM lookups
(which exceed the block RAM allocation constraints of low-power edge
FPGAs).

#### 3.1.1 DSP-Shared Barrett Reduction Execution

The BTU implements a fixed-latency, 3-cycle pipelined **Barrett Reduction**
engine.  For a runtime-configured Lucas prime Lₚ, a constant scaling
multiplier mu is precomputed at system boot via the host microcontroller
(RP2350B) and committed to a localized configuration register via the
0xA5 interface path:

    mu = floor(2^k / L_p),  where k = 31

For L₁₃ = 521, mu = 4,121,849.  The hardware-native remainder calculation
executes entirely within the existing core DSP fabric via the following
sequence:

1. **Quotient Estimation (Cycle 1):** The 31-bit intermediate coefficient
   x is multiplied by the configuration constant mu and logically shifted
   to isolate the upper fractional bits:

       q = (x * mu) >> 31

2. **Remainder Evaluation (Cycle 2):** The estimated quotient is multiplied
   back by the operational Lucas modulus and subtracted from the original
   value:

       r = x - (q * L_p)

3. **Boundary Correction (Cycle 3):** Because q is an approximation
   (floor(x/L_p) <= q <= floor(x/L_p)+1), the intermediate remainder
   sits strictly within the interval [0, 2L_p-1].  A single-cycle
   combinational comparison handles the final boundary condition:

       if (r >= L_p)  r := r - L_p

This architecture consumes exactly two 31x31 bit multiplications, one
shift, and a maximum of two subtractors. The current Artix-7 proof maps the
full Lucas MAC, including PMUL/PINV reduction, to 40 DSP48E1 slices; a Tang
25K profile should keep only the PSCALE/PCHIRAL slice unless those DSP/routing
costs are explicitly acceptable.

By avoiding involvement of the Southbridge SPI bus for arithmetic casting,
the data transmutates entirely within the lane-routing fabric.  The SPU-13
maintains a perfectly flat, deterministic execution cost, transforming a
potentially devastating bottleneck into a clean, 3-cycle pipeline phase.

### 3.2 RTL Layout of the Phinary MAC and Chiral Wire-Swaps

The Phinary MAC co-processor (`spu13_lucas_mac.v`) is a self-contained
Verilog module operating over ℤ[φ]/L₅₂₁. Its PSCALE/PCHIRAL fast paths
occupy zero DSP slices; the full PMUL/PINV Artix-7 proof maps to 40 DSP48E1
slices and interfaces with the BTU bridge through a simple request/done
handshake.

    module spu13_lucas_mac #(L_P=521, L_P_BITS=10) (
        input clk, rst_n, start,
        input [2:0] opcode,     // 0=PSCALE 1=PCHIRAL 2=PMUL 3=PINV 4=PHSLK
        input [9:0] op_a, op_b, // operand a + b*phi
        input [9:0] op_c, op_d, // second operand or PHSLK d1
        input [9:0] phslk_n2_a, phslk_n2_b, phslk_d2_a, phslk_d2_b,
        output busy, done, error,
        output phslk_coherent, phslk_zero_divisor,
        output [9:0] result_a, result_b
    );

**PSCALE** -- the architectural centerpiece -- implements phi-multiplication
in a single clock cycle with zero DSP slices:

    // phi*(a + b*phi) = b + (a+b)*phi -- 1 cycle, 0 DSP
    wire ps_b = (op_a + op_b >= L_P) ? (op_a + op_b - L_P) : (op_a + op_b);
    // result: (op_b, ps_b) = (b, a+b mod L_P)

This is the phinary analogue of the Mersenne prime's 2^31=1 bit-wrap:
structural efficiency from algebraic structure.  No multiplier, no divider,
no lookup table -- one addition and one comparison.

**PCHIRAL** implements phi-conjugation with equal simplicity:

    // conj(a + b*phi) = (a+b) - b*phi -- 1 cycle, 0 DSP
    wire pc_a = (op_a + op_b >= L_P) ? (op_a + op_b - L_P) : (op_a + op_b);
    wire pc_b = (op_b == 0) ? 0 : (L_P - op_b);

Together, PSCALE and PCHIRAL form the chiral basis: spatial permutation
(via the existing JSCR opcode and janus_screw_lines topology) followed by
phi-conjugation and phi-scaling.  The entire chirality transform -- spatial
reordering + algebraic conjugation + geometric scaling -- executes in 3
cycles with zero DSP slices, compared to hundreds of cycles and multiple
DSP blocks for an equivalent floating-point quaternion operation.

#### 3.2.1 Operation Timing

| Opcode | Operation | Cycles | DSP | LUTs |
|---|---|---|---|---|
| PSCALE | phi-multiply | 1 | 0 | Included in full MAC |
| PCHIRAL | phi-conjugation | 1 | 0 | Included in full MAC |
| PMUL | Full multiply | 3 | Shared full-MAC DSPs | Artix synth proof |
| PINV | Lucas inverse | O(log Lₚ) | Shared full-MAC DSPs | Artix synth proof |
| PHSLK | Rational phase coherence | 1 | 0 on Tang 25K microprobe | 293 LUT4, post-route |

The current full MAC maps to 588 estimated LCs and 40 DSP48E1 slices inside
the Artix-7 LUCAS spin. PSCALE and PCHIRAL remain zero-multiplier paths inside
that MAC; PMUL/PINV intentionally use Artix DSPs in this proof.

Tang Primer 25K remains a useful Lucas probe target, but it should not be
described as a solved full-PMUL target until the Gowin mapping is measured
end-to-end. The `FAST_ONLY=1` Tang probe has been SRAM-loaded and verified in
silicon with UART `LUCAS:P`, covering PSCALE, PCHIRAL, and a 100-period PSCALE
zero-drift marathon. A separate June 2026 standalone `FAST_ONLY=0` synthesis
reached nextpnr utilization with approximately 5,359 LUT4, 1,334 ALU cells,
351 DFFs, and zero Gowin multiplier primitives inferred before placement was
stopped. This is a tool-flow and coding-style result, not a mathematical
limitation: a hand-scheduled or primitive-guided Tang PMUL profile may still be
practical, but it is a separate optimization task from the current Artix-7
proof.

#### 3.2.2 PINV: Algebraic Inverse

The inverse uses the norm-conjugation formula:
1. Compute norm N = a^2 + ab - b^2 mod Lₚ (combinational)
2. Find N^-1 via extended binary GCD over the prime field
3. Compute conjugate C = (a+b) - b*phi (combinational)
4. Multiply: result = C * N^-1 mod Lₚ

A watchdog counter bounds the GCD loop to 64 iterations, asserting error on
timeout (the worst-case path for L₁₃ = 521 completes in 23 cycles). The
post-inverse multiplication is split across two pipeline stages to avoid
a long combinational chain through the Barrett reducer.

For L₁₃ = 521, this keeps inversion bounded without a runtime divider or `%`
operator.

## 4. Integration with SPU-13

### 4.1 Co-Processor Topology

```
              BTU Spatial Router
               /                \
    M31 Binary Core        Lucas Phinary MAC
    (A₃₁/M31, DSP path)      (ℤ[φ]/L₅₂₁, 40 DSP proof)
              \                /
       Barrett Reduction (M31 -> Lₚ, 3c)
                    |
            QR Register File
         (agnostic 64-bit pairs)
```

### 4.2 Instruction Encoding

The current Artix-7 sidecar probe intentionally uses temporary top-level
opcodes so it does not collide with the existing RPLU configuration range
(`0x50`-`0x5F`):

- **PSCALE** (`0xD0`): phi scale, `phi * (a+b phi)` -- 1 cycle
- **PCHIRAL** (`0xD1`): conjugation, `conj(a+b phi)` -- 1 cycle
- **PMUL** (`0xD2`): product, `(a+b phi) * (c+d phi)` -- 3 cycles
- **PINV** (`0xD3`): inverse, `(a+b phi)^-1` -- bounded GCD sequence
- **PHSLK_LOAD** (`0xD4`): latch `(n1,d1)` for phase coherence check
- **PHSLK_EXEC** (`0xD5`): execute `n1*d2 == n2*d1`; status returns
  coherence and denominator zero-divisor flags

Probe instruction layout over SPI `CMD 0xB1`:

```
[63:56] opcode: D0=PSCALE, D1=PCHIRAL, D2=PMUL, D3=PINV,
        D4=PHSLK_LOAD, D5=PHSLK_EXEC
[55:52] destination QR lane
[51:42] coefficient a, reduced modulo L_p
[41:32] coefficient b, reduced modulo L_p
[31:22] coefficient c, reduced modulo L_p (PMUL or denominator a)
[21:12] coefficient d, reduced modulo L_p (PMUL or denominator b)
[11:0]  reserved
```

Future ISA allocation for **PWAVE** and permanent phinary opcodes should happen
after the RPLU config opcode map is retired or moved behind a prefix. The D0-D3
range is a sidecar probe allocation, not the final ISA namespace.

### 4.3 Register File Compatibility

Phinary results are returned as (a,b) integer pairs, packing directly
into the existing 64-bit QR register file layout alongside M31
RationalSurd values.  The register file is ring-agnostic.

---

## 5. Empirical Results

### 5.1 Zero-Drift Proof

In this paper, "zero drift" has a narrow empirical meaning: at a declared
algebraic closure boundary, the hardware/oracle state returns to the exact same
`(a,b)` bit pattern as the seed. It does not mean that arbitrary operation
sequences are periodic, and it does not claim that every possible workload has
a short orbit. The evidence below covers two closure tests: PSCALE period
closure and mixed PSCALE/PMUL/PINV identity-macro closure.

```
Test: 2,600 consecutive PSCALE operations from seed (3+5φ)
Period: 26 (φ²⁶ ≡ 1 mod 521)
Result: 100 periods completed, all 100 period boundaries
        returned exact bit-match to seed
Verdict: ZERO-DRIFT — PASS
```

This compact PSCALE trace is separate from the 1,000,000-step oracle marathon
cited in the contributions, which verifies 38,461 period boundaries over the
same 26-step cycle.

The current Python oracle also runs a mixed identity macro containing PSCALE,
PMUL, and PINV:

```
x <- PSCALE(x)
x <- x * PINV(phi)
x <- x * g
x <- x * PINV(g)
```

Expanded as hardware primitives, each macro is six operations: PSCALE,
PINV(phi), PMUL by `phi^-1`, PMUL by `g`, PINV(g), and PMUL by `g^-1`.
For L₁₃=521, this mixed sequence completed 166,666 identity macros
(999,996 primitive PSCALE/PMUL/PINV operations) with exact return to the seed
after every macro.

### 5.2 Operation Verification

| Test | Expected | Actual | Pass |
|---|---|---|---|
| φ·(3+5φ) | (5+8φ) | (5+8φ) | ✓ |
| φ·φ | (1+1φ) | (1+1φ) | ✓ |
| conj(3+5φ) | (8+516φ) | (8+516φ) | ✓ |
| (3+5φ)(2+7φ) | (41+66φ) | (41+66φ) | ✓ |
| 1⁻¹ | (1+0φ) | (1+0φ) | ✓ |
| (3+5φ)⁻¹ | (513+5φ) | (513+5φ) | ✓ |
| (3+5φ)·(3+5φ)⁻¹ | (1+0φ) | (1+0φ) | ✓ |
| Mixed PSCALE/PMUL/PINV identity macros | seed preserved | 166,666/166,666 closed | ✓ |
| PHSLK coherent fraction | coherent=1, zd=0 | coherent=1, zd=0 | ✓ |
| PHSLK singular denominator | coherent=0, zd=1 | coherent=0, zd=1 | ✓ |

The RTL-style PINV scalar inverse model was also exhaustively profiled for
L₁₃=521: 270,400 non-zero-norm elements, 1,041 zero-divisor elements, 520
unique non-zero norms, and 3/23/16.66 min/max/average busy-phase cycles for
the scalar binary-GCD path. These counts exclude the caller issue/accept
cycle and should be treated as an oracle-model latency profile until mirrored
by a Verilog latency histogram.

### 5.3 Resource and Timing Evidence

| Resource | Current mapped result | Notes |
|---|---|---|
| PSCALE/PCHIRAL fast paths | 0 DSP | Shift-add/conjugation paths inside the MAC |
| Tang 25K `FAST_ONLY=1` probe | 696 LUT4, 216 DFF, 0 DSP | Silicon-verified with UART `LUCAS:P`; PSCALE/PCHIRAL plus 100-period zero-drift |
| Tang 25K PHSLK microprobe | 293 LUT4, 146 DFF, 0 DSP | Post-route 200.40 MHz, 4.99 ns critical path; dynamic operands; SRAM UART `PHSLK:P` |
| Lucas MAC | 588 estimated LCs, 40 DSP48E1 | Full PMUL/PINV proof with Barrett reducer |
| SPI sidecar + MAC | 641 estimated LCs, 40 DSP48E1 | D0-D3 opcodes exposed through SPI `0xB1` |
| Whole Wukong `LUCAS` spin | 4,521 estimated LCs, 40 DSP48E1 | Includes top-level SPI/UART/LED shell |
| Current routed frequency | 4.11 MHz max | Packed at `A7_FREQ=2` for bench bring-up |
| Current SPI sidecar transport | 2 MHz bench path | 32 µs to clock 64 bits at 2 MHz SCK, before SPI framing and handshake |

The current Artix-7 bitstream is therefore a functional bring-up artifact, not
a real-time photonic-control result. A credible sub-100ns transform claim needs
the full sidecar clocked above 30 MHz for the 3-cycle fast chirality path, plus
separate ingress/egress accounting. The PHSLK Tang microprobe already exceeds
that frequency target as a standalone routed kernel; the integrated Wukong
sidecar does not yet.

---

## 6. Discussion

### 6.1 Why This Matters for Quantum Control

The quantum-control relevance of this block is narrow: it is not a complete
QEC decoder, and the current SPI sidecar is not a feedback-loop transport.
The useful kernel is PHSLK, which checks equality of two rational phase
encodings without denominator inversion:

```
valid_template_match = coherent && !zero_divisor
```

That maps cleanly to any control stack that first reduces an observed
topological or oscillator-code syndrome into rational phase templates. The
zero-divisor flag is not merely an error condition; it is useful status,
because a norm-zero denominator marks a singular phase representation that
should not be silently accepted as a valid template match.

The latency landscape is already aggressive. Recent preprints on
superconducting and FPGA control paths report sub-microsecond decode-feedback:
a distance-3 superconducting surface-code NN decoder reports 550 ns closed-loop
latency including 124 ns decoding [11]; an RFSoC QEC system reports 446 ns
decode-feedback latency for distance-3 [12]; and a quantum-LDPC/GARI FPGA decoder
case study reports 596 ns average latency per round for a [[144,12,12]]
bivariate-bicycle-code target [13]. This paper should therefore be read as a
candidate exact-arithmetic kernel study, not as a claim that the current
Wukong/SPI image is competitive with integrated QEC controllers.

These latency references are superconducting/RFSoC/LDPC controller benchmarks,
not photonic timing claims. Photonic architectures differ: optical path length,
detector integration, feed-forward topology, time-bin multiplexing, and fusion
network scheduling all change the latency budget. The comparison is included to
calibrate the general scale expected of real-time control hardware; a photonic
deployment would need architecture-specific ingress, detector, and feed-forward
accounting.

For bosonic QEC, the relevant prior art includes cat-code real-time feedback
and break-even experiments [6,9], binomial oscillator codes [7], and GKP
codes [8]. These families do not automatically require ℤ[φ] arithmetic. The
φ-specific case is strongest where the upstream model is genuinely
Fibonacci/topological: braid or fusion templates whose amplitudes, F-symbols,
or phase ratios naturally contain φ [10]. For ordinary surface-code MWPM,
floating-point drift is not the central problem; the decoder is combinatorial.
For φ-weighted braid/fusion or template-matching kernels, exact rational phase
comparison is the point, and PHSLK is the concrete primitive. At L₁₃=521, this
is evidence for small finite-domain template predicates, not evidence that full
large syndrome graphs or deep braid histories fit without aliasing.

### 6.1.1 Photonic Quantum Control Context

For photonic quantum computing, the relevant entry point is not general surface
code decoding. Linear-optical quantum computing and fusion-based quantum
computation are measurement-driven architectures: photons are prepared, routed
through interferometric/fusion networks, detected, and then classically
interpreted for feed-forward or Pauli-frame updates [14,15,16]. Photonic GKP
blueprints similarly reduce continuous-variable homodyne information into
discrete syndrome decisions over a scheduled optical network [17,18].

The Lucas MAC is not proposed as a photon detector, optical controller, or full
photonic decoder. Its specific role would be downstream of the photonic
front-end: once an upstream compiler or syndrome reducer has converted a
fusion, braid, or oscillator-code event into a reduced rational phase template,
PHSLK can test whether an observed template matches a target without computing
a denominator inverse. This is most compelling in φ-native cases, such as
Fibonacci/topological models whose F-symbols and fusion amplitudes contain φ,
but the present L₁₃ instance should be read as a small-domain preprocessing
kernel rather than a complete substrate for large code instances.

For GKP or fusion-network systems without intrinsic φ structure, the immediate
value is narrower: exact integer/rational bookkeeping can replace floating
threshold drift in selected preprocessing steps, but the paper does not claim
that ℤ[φ] is a universal decoder substrate for all photonic architectures. The
research question is whether a small exact-arithmetic phase predicate can reduce
ambiguous template matches before a larger decoder runs.

### 6.2 Non-Quantum Exact Geometry Baseline

The Jitterbug transformation (VE → octahedron collapse) requires
non-linear interpolation that, in Cartesian coordinates, demands
transcendental function evaluation.  In ℤ[φ] this reduces to exact
rational interpolation — a linear combination of φ-weighted endpoints.

This is the non-quantum baseline use case for the same MAC: deterministic
φ-scaling, conjugation, and rational phase comparison over finite algebraic
pairs. The benchmark evidence in this paper is intentionally at that kernel
level: PSCALE period closure, mixed PSCALE/PMUL/PINV identity closure, and
PHSLK template equality. An end-to-end geometric animation or robotics
benchmark would be a separate integration result, not something implied by the
current Lucas MAC numbers.

### 6.3 Limitations

- **Modulus configurability:** The Verilog module is parameterized on L_P and
  L_P_BITS, supporting any Lucas prime up to L₁₉ = 9349 (14-bit operands)
  with zero RTL changes.  Runtime configurability (changing L_P without
  resynthesis) requires a configurable Barrett μ register and wider
  reduction datapath — a straightforward extension of the existing 0xA5
  boot-config path.

  | Lucas prime | L_p | Bits | φ period | Scalar field size |
  |---|---|---|---|---|
  | L₅  | 11   | 4  | 10 | 11 |
  | L₇  | 29   | 5  | 14 | 29 |
  | L₁₁ | 199  | 8  | 22 | 199 |
  | L₁₃ | 521  | 10 | 26 | 521 |
  | L₁₇ | 3571 | 12 | 34 | 3,571 |
  | L₁₉ | 9349 | 14 | 38 | 9,349 |

- **PINV scalar inverse complexity:** The current RTL uses extended binary
  GCD on the scalar norm modulo Lₚ, avoiding exhaustive search and runtime
  division. For L₁₃=521, the current oracle model reports 3 to 23 busy-phase
  cycles over all non-zero-norm elements. A Verilog latency histogram should
  be added before citing this as measured RTL latency.

- **Finite φ-period and aliasing:** L₁₃ gives a φ-period of 26. This is enough
  to prove the datapath and small template predicates, but it is not enough to
  encode arbitrary long braid words or large syndrome graphs without careful
  phase-domain tiling. Larger Lucas moduli, multiple residues, or explicit
  topology indices are required for code distances that exceed the available
  period horizon.

- **Interface latency:** The 2 MHz SPI sidecar is a bench/control shell. A
  64-bit instruction payload takes 32 µs to clock at 2 MHz SCK before command
  framing, handshake, and result readback. Real-time quantum-control variants
  require a different ingress/egress path such as parallel GPIO, PIO/DMA lanes,
  LVDS, RFSoC fabric, or a directly coupled controller.

- **PMUL integer multiplication:** The current formula (a+bφ)(c+dφ) =
  (ac+bd) + (ad+bc+bd)φ uses four integer multiplies.  For modulus-sized
  operands (≤14 bits), this is optimal — the algebraically equivalent
  phinary shift-add decomposition requires the same number of multiply
  operations with added base-conversion overhead.  A true positional
  base-φ shift-add multiplier (using PSCALE as the shift primitive on
  Zeckendorf-encoded operands) would eliminate integer multiplies for
  large-operand cases and is noted as future work.

---

## 7. Conclusion

We have demonstrated a Lucas-prime phinary co-processor that performs
chiral transformations, φ-scaling, and spatial inversion in the golden
ring ℤ[φ]/L₅₂₁ with zero floating-point and bit-exact closure. The
PSCALE/PCHIRAL transforms are zero-multiplier fast paths; the current full
PMUL/PINV proof spends 40 Artix-7 DSP48E1 slices to preserve bounded,
synthesizable reduction. The PSCALE operation (φ-multiplication in a single
clock cycle with zero multipliers) is the phinary analogue of the Mersenne
prime's 2³¹≡1 bit-wrap: structural efficiency from algebraic structure.

The co-processor is oracle/testbench-proven with 100-period PSCALE closure and
with a mixed PSCALE/PMUL/PINV identity run of 166,666 macros, or 999,996
primitive operations.
It is synthesized, routed, and packed in the Wukong Artix-7 LUCAS profile for
bench bring-up, while PHSLK has a separate Tang 25K post-route microprobe at
200.40 MHz with SRAM-load UART proof. The next phase is silicon bring-up beside
the SPU-13 Mersenne core, followed by timing closure on the integrated
PMUL/PINV path and replacement of the SPI sidecar with a real-time
ingress/egress path if quantum-control latency is pursued.

---

## Published References

1. Lucas, E. "Theorie des Fonctions Numeriques Simplement Periodiques." 1878.
2. Nguyen, H.S. "Tolerance Rough Sets." Fundamenta Informaticae, 1999.
3. Kohonen, T. "Self-Organizing Maps." Springer, 1995.
4. Wheeler, J.A. & Feynman, R.P. "Interaction with the Absorber as the
   Mechanism of Radiation." Rev. Mod. Phys. 17, 1945.
5. Crandall, R.E. & Pomerance, C. "Prime Numbers: A Computational
   Perspective." Springer, 2nd ed., 2005.
6. Ofek, N. et al. "Extending the lifetime of a quantum bit with error
   correction in superconducting circuits." arXiv:1602.04768 / Nature 2016.
   https://arxiv.org/abs/1602.04768
7. Michael, M.H. et al. "New class of quantum error-correcting codes for a
   bosonic mode." arXiv:1602.00008 / Phys. Rev. X 2016.
   https://arxiv.org/abs/1602.00008
8. Gottesman, D., Kitaev, A., Preskill, J. "Encoding a qubit in an oscillator."
   arXiv:quant-ph/0008040 / Phys. Rev. A 2001.
   https://arxiv.org/abs/quant-ph/0008040
9. Putterman, H. et al. "Hardware-efficient quantum error correction using
   concatenated bosonic qubits." arXiv:2409.13025 / Nature 2025.
   https://arxiv.org/abs/2409.13025
10. Freedman, M., Larsen, M., Wang, Z. "A modular functor which is universal
    for quantum computation." arXiv:quant-ph/0001108 / Commun. Math. Phys.
    227, 605-622 (2002).
    https://arxiv.org/abs/quant-ph/0001108
11. Yang, X. et al. "Real-time Surface-Code Error Correction Using an
    FPGA-based Neural-Network Decoder." arXiv:2605.04892, 2026.
    https://arxiv.org/abs/2605.04892
12. Liu, J. et al. "A Scalable Open-Source QEC System with Sub-Microsecond
    Decoding-Feedback Latency." arXiv:2603.16203, 2026.
    https://arxiv.org/abs/2603.16203
13. Báscones, D. et al. "A Scalable FPGA Architecture for Real-Time Decoding
    of Quantum LDPC Codes Using GARI." arXiv:2605.01035, 2026.
    https://arxiv.org/abs/2605.01035
14. Knill, E., Laflamme, R., Milburn, G.J. "A scheme for efficient quantum
    computation with linear optics." Nature 409, 46-52 (2001).
    https://doi.org/10.1038/35051009
15. Bartolucci, S. et al. "Fusion-based quantum computation."
    arXiv:2101.09310, 2021.
    https://arxiv.org/abs/2101.09310
16. Kok, P. et al. "Linear optical quantum computing with photonic qubits."
    Rev. Mod. Phys. 79, 135-174 (2007). arXiv:quant-ph/0512071.
    https://arxiv.org/abs/quant-ph/0512071
17. Bourassa, J.E. et al. "Blueprint for a Scalable Photonic Fault-Tolerant
    Quantum Computer." arXiv:2010.02905 / Quantum 2021.
    https://arxiv.org/abs/2010.02905
18. Tzitrin, I. et al. "Fault-tolerant quantum computation with static linear
    optics." arXiv:2104.03241, 2021.
    https://arxiv.org/abs/2104.03241

## Internal Implementation References

I1. SPU-4 chiral phinary adder:
    `hardware/rtl/core/spu4/chiral_phinary_adder_param.v`

---

## Appendix A: Python Oracle

```python
def phi_mul(a, b, mod=521):
    return (b % mod, (a + b) % mod)

def phi_mul_full(a1, b1, a2, b2, mod=521):
    return ((a1*a2 + b1*b2) % mod,
            (a1*b2 + a2*b1 + b1*b2) % mod)

def zero_drift_test(mod=521, seed=(3,5), steps=1000000):
    period = phi_order(mod)  # 26 for L_521
    a, b = seed
    for step in range(1, steps + 1):
        a, b = phi_mul(a, b, mod)
        if step % period == 0: assert (a,b) == seed
    print(f"ZERO-DRIFT: PASS — {steps//period} periods, {steps} steps")

def composite_zero_drift_macro(x, g, mod=521):
    # Identity macro: PSCALE, PMUL with PINV(phi), PMUL with g, PMUL with PINV(g).
    a, b = phi_mul(x[0], x[1], mod)
    ia, ib = phi_inv(0, 1, mod)
    a, b = phi_mul_full(a, b, ia, ib, mod)
    a, b = phi_mul_full(a, b, g[0], g[1], mod)
    ga, gb = phi_inv(g[0], g[1], mod)
    a, b = phi_mul_full(a, b, ga, gb, mod)
    x = (a, b)
    return x
```

## Appendix B: Verilog PSCALE Core

```verilog
// φ·(a + bφ) = b + (a+b)φ — 1 cycle, 0 DSP
wire [L_P_BITS-1:0] ps_b = (op_a + op_b >= L_P) ? (op_a + op_b - L_P) : (op_a + op_b);
always @(posedge clk)
    if (start && opcode == OP_PSCALE) begin
        result_a <= op_b; result_b <= ps_b; done <= 1;
    end
```

## Appendix C: Proposed PHSLK Phase Coherence Test Primitive

### C.1 Architectural Role and Definition

The proposed phase-lock (`PHSLK`) primitive verifies the equivalence or
coherence of two rational phase encodings over the finite quotient ring
ℤ[φ]/L₅₂₁ without requiring direct modular inversion.

Given two rational elements represented as fractions of ring elements:

```
A = n1 / d1,   B = n2 / d2
```

where `n1`, `d1`, `n2`, and `d2` are in ℤ[φ]/L₅₂₁, a direct equality check
would traditionally require computing modular inverses of the denominators
through the `PINV` block. Because 521 ≡ 1 (mod 5), the characteristic
polynomial `x^2 - x - 1` splits modulo 521. Consequently, ℤ[φ]/L₅₂₁ contains
zero-divisors; elements with norm zero modulo L₅₂₁ do not have a defined
multiplicative inverse.

To bypass this constraint and eliminate the latency of a division pipeline,
`PHSLK` evaluates phase coherence by cross multiplication:

```
n1*d2 == n2*d1
```

### C.2 Circuit Topography and Implementation Status

The RTL datapath computes `(n1*d2) - (n2*d1)` as two Lucas-ring
multiplications followed by a registered equality/status stage. The current
MAC exposes `PHSLK` as opcode `4`; `result_a[0]` is the coherence bit and
`result_b[0]` is the denominator zero-divisor flag. The SPI sidecar uses a
two-word command: `D4` loads `(n1,d1)` and `D5` executes against `(n2,d2)`.

- **Simulated:** Python oracle and Verilog RTL testbenches cover coherent,
  mismatched, and zero-divisor-denominator cases.
- **Synthesized:** PSCALE/PCHIRAL remain confirmed zero-DSP. The Tang 25K
  PHSLK microprobe synthesizes with zero Gowin multiplier primitives inferred.
- **Placed/Routed:** The Tang 25K PHSLK dynamic microprobe routes at
  200.40 MHz post-route, corresponding to a 4.99 ns critical path, with
  reported utilization of 293 LUT4, 146 DFF, 182 ALU, 0 BSRAM, and 0 Gowin
  multiplier/DSP primitives. Artifact:
  `build/metrics/tang25k_lucas_phslk_probe.md`. This is a microprobe
  clock-closure result with live PHSLK operands folded into an observable
  result stream, not a full-sidecar timing closure claim.
- **Measured on FPGA:** The Tang 25K PHSLK microprobe SRAM-loads and emits
  repeated UART `PHSLK:P` on `/dev/ttyUSB2`, proving coherent, mismatched, and
  zero-divisor-denominator cases in silicon. Artix-7 full-sidecar validation
  remains future work.

### C.3 Potential Future Evaluation

The current execution framework is optimized for local SOM cluster training
and spatial robotics boundaries. The deterministic, zero-drift nature of the
cross-multiplication check also makes PHSLK a candidate preprocessing layer
for photonic control feedback and syndrome-like coherence predicates.

### C.4 Reduced Anyon-Template Matching Interpretation

PHSLK also provides the algebraic core for a reduced anyon-template predicate
when an upstream braid/fusion tracker represents both an observed phase ratio
and a candidate template as rational elements of ℤ[φ]/L₅₂₁:

```
observed = observed_n / observed_d
template = template_n / template_d

valid_template_match = PHSLK(observed, template).coherent &&
                       !PHSLK(observed, template).zero_divisor
```

This is a domain interpretation of the same cross-multiplication primitive, not
a new hardware block. The FPGA does not simulate the anyon category or claim
physical anyon detection; it only evaluates whether two reduced rational phase
ratios cohere without performing denominator inversion. Singular denominator
encodings are rejected through the zero-divisor status bit.

For the Fibonacci anyon category, the usual recoupling matrix for the
`tau tau tau -> tau` fusion space is:

```
F = [  phi^-1      phi^(-1/2) ]
    [  phi^(-1/2) -phi^-1    ]
```

Only part of this matrix is directly represented in ℤ[φ]: `phi^-1 = phi - 1`
is the ring element `(-1 + phi)`, while the off-diagonal square-root term is
not itself in ℤ[φ]. The present MAC therefore does not claim to simulate the
full complex or square-root amplitude model. The supported use is narrower:
template matching over rational phase ratios or squared-amplitude ratios whose
reduced values lie in Q(φ).

A simple template example is the ratio of squared diagonal to off-diagonal
F-symbol magnitudes:

```
|phi^-1|^2 / |phi^(-1/2)|^2 = phi^-1 = phi - 1.
```

If an upstream braid/fusion tracker reduces an observed ratio to
`(2*phi - 2) / 2` and a target template to `(phi - 1) / 1`, PHSLK checks:

```
observed_n = -2 + 2*phi   observed_d = 2
template_n = -1 + phi     template_d = 1

observed_n * template_d == template_n * observed_d
```

Modulo L₅₂₁, those are encoded as `(519,2)/(2,0)` and `(520,1)/(1,0)`.
The PHSLK predicate returns coherent with no denominator zero-divisor. This is
the intended template-matching semantics: a compiled rational template matches
the observed reduced phase ratio. Larger braid depths still require a larger
period horizon than L₁₃'s 26 φ-steps, residue tiling, or explicit topological
indices to prevent aliasing.

## Appendix D: Positional Phinary Substrate Note

While a positional base-φ representation, such as a Zeckendorf-encoded
bitstream, is theoretically elegant, implementing a native positional phinary
adder on modern FPGA fabric is a poor fit for the substrate. Standard FPGA
arithmetic is physically optimized around binary carry chains, while phinary
normalization needs bidirectional identities such as:

```
phi^n + phi^(n-1) = phi^(n+1)
2*phi^n = phi^(n+1) + phi^(n-2)
```

Emulating those carries in LUT fabric would require multi-cycle settling logic
or deep combinational networks. The `(a,b)` algebraic pair representation used
in this work is therefore the practical mapping for CMOS FPGA fabrics: it keeps
the exact ℤ[φ] semantics while using ordinary modular binary adders and
multipliers.

True positional phinary arithmetic is more naturally a topic for future
non-standard substrates, such as topological hardware where Fibonacci anyon
fusion rules natively expose φ, or analog networks where component ratios can
physically implement φ-weighted sums.
