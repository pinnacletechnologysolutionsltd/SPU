# SU(3) Matrix Arithmetic over A₃₁[i]: A Deterministic Unitary Coprocessor Extension

**Authors:** John Curley

**Affiliation:** Independent Researcher, SPU-13 Project

**Date:** July 2026

**Status:** Preprint draft — RTL complete, oracle and multiplier/sidecar
testbenches verified in simulation. Wukong Artix-7 SU3 and SU3SHARE spins
`synth_xilinx` check clean, route at the 2 MHz bring-up target, emit bitstreams,
and configure over DirtyJTAG. Functional SU3 SPI readback over Wukong J11 is now
silicon-proven with all nine dense-matrix QR commit checks on the
shared-multiplier SU3SHARE image, which also preserves the RPLU2 config/QR
regression.

**Implementation state:** Standalone SU3 uses a dedicated M31 multiplier
instance; integrated SU3SHARE uses a top-level shared instance. Artix-7
synthesis maps the logical 16-product M31 datapath to 64 DSP48E1 slices. The
Wukong SU3/SU3SHARE spins use a streaming SPI sidecar over CMD `0xB1`:
`EA` starts and selects one result element, `E8/E9` stream A/B chunks, and
`EB` commits the captured 256-bit result through QR A/B/C/D. A 3×3 multiply
is ~224 compute cycles, with result pulses emitted as each C element
completes. Python oracle: 20 checks, all PASS. Verilog testbenches:
multiplier and sidecar protocol, both PASS. Current sidecar-only Artix
synthesis: ~8.2k estimated LCs for the SU3 spin, 64 DSP48E1. Current shared
Artix integration snapshot (`SU3SHARE`): 60,837 LUTX cells, 16,478 FFX cells,
64 DSP48E1, `A7_CLK_DIV_LOG2=6`, post-route `clk_fast` max 3.67 MHz with PASS
at the 2 MHz route target, and SHA-256
`4dff1a6e5fbbfc2f10afca0afd5ff08846727a6b0b3571eb76deb755aafb80ed`.

---

## Abstract

We present an extension of the A₃₁ split biquadratic algebra over the
Mersenne prime M31 (2³¹−1) to the degree-8 complex algebra A₃₁[i],
enabling deterministic 3×3 unitary matrix arithmetic with zero
floating-point operations. The design reuses the existing M31 multiplier
design through a 4-phase time-division multiplexing scheme. It can run either
as a dedicated standalone sidecar instance or as an integrated sidecar borrowing
a top-level shared instance. On Artix-7, standalone synthesis maps
this logical 16-product M31 datapath to 64 DSP48E1 slices. The FSM
sequences 27 complex A₃₁[i] multiplies to complete a full 3×3 matrix
product in approximately 224 compute cycles, with row-major result elements
emitted as their accumulators complete. A Python oracle (20 checks) plus
multiplier and sidecar Verilog testbenches verify bit-exact correctness of
the arithmetic, the Gell-Mann structure constants, the conjugate transpose,
determinant checks, and the SPI-visible streaming protocol. The RTL module
is open-source (CC0) and has been added to the Artix-7 SU3 and SU3SHARE spins;
this draft reports simulation, synthesis, Wukong Artix-7 2 MHz
route/bitstream results, JTAG configuration, and first functional SPI/QR
silicon verification over the Wukong J11 header.

---

## 1. Introduction

### 1.1 Motivation

Special unitary groups SU(N) underpin much of modern physics — lattice
QCD, topological quantum computing, anyonic braid models, and
fibre-bundle gauge theories. In all of these applications, the core
computational primitives are matrix multiplication and coherence checks
over the group. Standard implementations use IEEE-754 floating-point
arithmetic, which accumulates rounding error over long unitary evolution
sequences. For simulations requiring millions of steps — or for
real-time control of topological quantum systems — this drift can
destroy the structural invariants that define the group.

### 1.2 Approach

We extend the existing A₃₁ split biquadratic algebra over the
Mersenne prime M31 (2³¹−1) by adjoining √−1, giving the degree-8
algebra A₃₁[i]. This field contains both √3 (from A₃₁) and √−1
(the complex unit), enabling exact representation of the SU(3)
generators as matrices over A₃₁[i]. All arithmetic is exact modular
arithmetic — no floating point, no rounding, no division in hot paths.

The design instantiates or borrows the same `spu13_m31_multiplier` module used
by the RPLU v2 pipeline, sequencing 4 A₃₁ base products per complex multiply
through a 4-phase time-division multiplexer. A full 3×3 matrix product
completes in approximately 224 compute cycles, emitting row-major result
elements as each C[i][j] accumulator completes. The standalone module can keep
its own M31 multiplier instance; the `SU3SHARE` Artix spin instead muxes a
top-level shared instance so the integrated image does not add a second 64-DSP
M31 block.

### 1.3 What This Paper Is and Is Not

This paper reports the RTL design, mathematical foundation, and
simulation verification of an SU(3) matrix multiply unit over A₃₁[i].
The RTL has been compiled under Icarus Verilog and passes all test
cases. The Wukong Artix-7 SU3 and SU3SHARE spins also synthesize cleanly with
the streaming sidecar and have produced routed 2 MHz bring-up bitstreams that
configure over DirtyJTAG. The SU3 SPI protocol has now been functionally tested
on FPGA hardware: an RP2350 streamed the dense A/B fixture over Wukong J11 and
read exact QR commits for three selected result elements on the standalone
sidecar proof, then for all nine result elements on the SU3SHARE image. The
SU3SHARE image then passed the RPLU2 config/QR regression on the same FPGA
bitstream.

---

## 2. Mathematical Foundation

### 2.1 A₃₁: The Split Biquadratic Algebra over M31

The base field is the Mersenne prime field
$\mathbb{F}_p$ where $p = 2^{31} - 1 = 2147483647$ (M31). The
characteristic $p \equiv 3 \pmod 4$ means $x^2 + 1$ is irreducible
— $\sqrt{-1}$ does not exist in the base field. However, both
$3^{(p-1)/2} \equiv -1$ and $5^{(p-1)/2} \equiv -1$, so $\sqrt{3}$
and $\sqrt{5}$ exist in $\mathbb{F}_{p^2}$.

The split biquadratic algebra $A_{31}$ is defined as:

$$A_{31} = \mathbb{F}_p[u,v] / (u^2 - 3, v^2 - 5)$$

with basis $[1, u, v, uv]$ representing elements as 4-tuples
$(c_0, c_1, c_2, c_3) \in [0, p-1]^4$. Multiplication follows
the cross-product rules shown in Table 1. The algebra is "split"
because $15$ is a quadratic residue: $\sqrt{15}$ exists in
$\mathbb{F}_p$, so the extension contains zero-divisors. The
conjugate reduction tower [RPLU2] inverts units in approximately
76 cycles and traps zero-norm elements via FLAGS.V.

### 2.2 Complex Extension: A₃₁[i]

We adjoin $i = \sqrt{-1}$ to $A_{31}$:

$$A_{31}[i] = A_{31}[x] / (x^2 + 1)$$

An element of $A_{31}[i]$ is a pair $(r, s)$ where $r, s \in A_{31}$,
representing $r + i\cdot s$. The degree-8 basis over $\mathbb{F}_p$ is:

$$[1, u, v, uv, i, iu, iv, iuv]$$

Multiplication follows the complex rule:

$$(r_1 + i s_1)(r_2 + i s_2) = (r_1 r_2 - s_1 s_2) + i(r_1 s_2 + s_1 r_2)$$

Each complex multiply therefore requires 4 $A_{31}$ base products
($r_1 r_2$, $s_1 s_2$, $r_1 s_2$, $s_1 r_2$).

The conjugate reduction tower generalises to three stages
($\mathbb{F}_p \to \mathbb{F}_p(\sqrt{3}) \to \mathbb{F}_p(\sqrt{3},
\sqrt{5}) \to \mathbb{F}_p(\sqrt{3}, \sqrt{5}, \sqrt{-1})$), giving
an inversion latency of approximately 114 cycles for $A_{31}[i]$.

### 2.3 SU(3) Structure Constants in A₃₁[i]

The eight Gell-Mann matrices $\lambda_1$ through $\lambda_8$ generate
$\mathfrak{su}(3)$, the Lie algebra of SU(3). They contain entries
in $\{0, \pm 1, \pm \frac{1}{2}, \pm \frac{\sqrt{3}}{2}\}$. In
$A_{31}[i]$:

- $\pm 1$ and $\pm \frac{1}{2}$ are field elements ($2^{-1}$ exists
  in M31: $2^{-1} = 1073741824$)
- $\sqrt{3}$ exists natively as $u \in A_{31}[i]$
- $\pm \frac{\sqrt{3}}{2} = \pm \frac{1}{2} \cdot \sqrt{3}$ is a
  single A₃₁ multiplication
- $i$ is the complex unit, present as the imaginary basis element

The Gell-Mann matrices extend to SU(3) via exponentiation. For the
purpose of this work, we verify that:

- $\lambda_1^2 = \operatorname{diag}(1, 1, 0)$
- $\lambda_3$ is diagonal with entries $(1, -1, 0)$
- $\lambda_8$ contains the $\sqrt{3}$ dependence correctly
- Matrix multiplication over $A_{31}[i]$ is closed for 3×3 matrices

The determinant of every SU(3) element equals $1 + 0i$ in $A_{31}[i]$.

---

## 3. RTL Design

### 3.1 Multiplier Topography

The `spu13_su3_mult` module instantiates a dedicated
`spu13_m31_multiplier` — the same 2-stage pipelined multiplier design
used by the RPLU v2 pipeline. Each $A_{31}$ product (4 components,
16 logical parallel 32×32 integer products) completes with 2-cycle
throughput. In Artix-7 synthesis, those logical products map to 64 DSP48E1
slices.

A complex $A_{31}[i]$ multiply is sequenced as 4 phases through this
multiplier:

| Phase | Operation | Description |
|:---|:---|---:|
| 0 | RR = real(A) · real(B) | 2 cycles |
| 1 | II = imag(A) · imag(B) | 2 cycles |
| 2 | RI = real(A) · imag(B) | 2 cycles |
| 3 | IR = imag(A) · real(B) | 2 cycles |

After all 4 phases, the accumulators are updated:

$$c_{\text{real}} \mathrel{+}= RR - II \quad (\text{A₃₁ subtraction})$$
$$c_{\text{imag}} \mathrel{+}= RI + IR \quad (\text{A₃₁ addition})$$

Each complex multiply takes 8 cycles total (4 phases × 2 cycles
throughput, fully pipelined). The multiplier starts a new $A_{31}$
product every 2 cycles while the previous result is being accumulated.

### 3.2 3×3 Matrix Multiply FSM

The FSM implements the triple-nested loop:

$$C[i][j] = \sum_{k=0}^{2} A[i][k] \cdot B[k][j] \quad
i,j \in \{0, 1, 2\}$$

The interface uses element-wise loading: the host writes 9 elements
(256 bits each) into matrix A via `load_a` strobes, then 9 elements
into matrix B via `load_b` strobes. Each element is a 256-bit word
packed as:

```
{imag_c3[31:0], imag_c2[31:0], imag_c1[31:0], imag_c0[31:0],
 real_c3[31:0], real_c2[31:0], real_c1[31:0], real_c0[31:0]}
```

The FSM then sequences 27 complex multiplies (3 i × 3 j × 3 k) in
row-major order. Each result element is emitted as soon as its three
k-terms are accumulated, so the result stream is part of the compute
schedule rather than a separate C-matrix drain stage. Total latency is
approximately 224 compute cycles.

### 3.3 Resource Estimate

| Resource | Estimate | Notes |
|:---|---|:---|
| DSP slices | 64 DSP48E1 on Artix-7 | 16 logical 32×32 products; each maps to 4 DSP48E1 |
| Estimated LCs | ~6.2k multiplier, ~8.2k Wukong SU3 sidecar spin | Sidecar-only spin: SPI, UART stub, SU3 sidecar |
| Packed FFs | 9,488 in Wukong SU3 spin snapshot | A/B matrix storage retained; C matrix storage removed |
| Packed LUT cells | 21,092 in Wukong SU3 spin snapshot | 16% of XC7A100T LUT capacity |
| Clocking | `A7_CLK_DIV_LOG2=6` | 50 MHz oscillator divided to ~781 kHz `clk_fast` for first smoke |
| Post-route timing | 51.58 MHz max for `clk_div[5]` | PASS at 2 MHz route target |
| Cycles per 3×3 multiply | ~224 | Result pulses integrated into compute completion |
| Time at 200 MHz | ~1.2 µs | Projection from cycle count |
| Time at 4.11 MHz | ~57 µs | Projection from cycle count |

The standalone module currently instantiates its own multiplier. Sharing
the RPLU v2 multiplier is an integration option, not an implemented
property of this module.

---

### 3.4 Worked Example: λ₁ × λ₁

To illustrate the arithmetic concretely, consider the Gell-Mann
generator λ₁ multiplied by itself:

$$\lambda_1 = \begin{pmatrix}
0 & 1 & 0 \\
1 & 0 & 0 \\
0 & 0 & 0
\end{pmatrix},
\quad
\lambda_1^2 = \begin{pmatrix}
1 & 0 & 0 \\
0 & 1 & 0 \\
0 & 0 & 0
\end{pmatrix}$$

Each matrix element is an $A_{31}[i]$ value: a pair of 4-tuples
(real, imag) over M31. In this case, all values are real and
contain only $c_0$ components equal to 0 or 1, with $c_1 = c_2 =
c_3 = 0$ in both real and imaginary parts. The complex unit $i$
appears only in the off-diagonal generators ($\lambda_2$,
$\lambda_4$, $\lambda_5$, $\lambda_6$, $\lambda_7$).

The computation $C[0][0] = A[0][0] \cdot B[0][0] + A[0][1] \cdot
B[1][0] + A[0][2] \cdot B[2][0]$ evaluates to:

$$0 \cdot 0 + 1 \cdot 1 + 0 \cdot 0 = 1$$

The middle term $1 \cdot 1$ requires a full $A_{31}[i]$ multiply:
both operands are $(1, 0, 0, 0)$ in the real part with zero
imaginary part. The 4-phase TDM sequence produces $RR = 1$,
$II = 0$, $RI = 0$, $IR = 0$, giving $c_{\text{real}} = 1$ and
$c_{\text{imag}} = 0$. All other terms produce zero, so
$C[0][0] = (1, 0, 0, 0)$.

This example is verified by both the Python oracle and the Verilog
testbench. The oracle output for this exact computation is available
in `software/tests/test_su3_oracle.py` (test case `λ₁²[0][0] = 1`).

## 4. Verification

### 4.1 Python Oracle

The oracle (`test_su3_oracle.py`) implements $A_{31}[i]$ arithmetic,
the Gell-Mann matrices, 3×3 matrix multiplication, the conjugate
transpose, determinant, and coherence checks. 20 checks verify:

- **A₃₁ arithmetic** (3 checks): $1 \cdot x = x$, tuple shape,
  product reduction modulo M31
- **A₃₁[i] arithmetic** (2 checks): $i^2 = -1$,
  $1 \cdot (2 + 3i) = 2 + 3i$
- **Matrix multiply** (2 checks): identity closure, SU(3) closure for
  identity
- **Dense matrix product** (1 check): packed A₃₁[i] constants used by
  the RTL testbench match the oracle
- **Gell-Mann structure** (8 checks): $\lambda_1^2 = \operatorname{diag}
  (1, 1, 0)$, $\lambda_3$ diagonal, $\lambda_2$ non-unitary without
  exponentiation, $\lambda_8$ basis encoding
- **Product closure** (1 check): product of two generator matrices
  remains a 3×3 matrix over A₃₁[i]
- **Coherence check** (1 check): $\lambda_1 \cdot \lambda_1^\dagger =
  \lambda_1^2$ (self-adjoint)
- **Determinant check** (2 checks): determinant of identity equals 1

All 20 checks pass. The oracle uses standard Python integers reduced
modulo M31 — no floating point, no external libraries.

### 4.2 RTL Testbench

The Verilog testbench (`spu13_su3_mult_tb.v`) instantiates the SU(3)
multiply module, loads test matrices via the element-wise interface,
and asserts bit-exact output against the public result stream. Four test
cases:

1. **Identity × Identity = Identity**: verifies that the unit matrix
   is preserved under multiplication
2. **$\lambda_1 \times \lambda_1 = \lambda_1^2$**: verifies
   $\operatorname{diag}(1, 1, 0)$ — a non-trivial multiplication with
   cancellation
3. **Identity × $\lambda_1$ = $\lambda_1$**: verifies right-hand
   operand preservation through the public interface
4. **Zero × Identity = Zero**: verifies accumulator clearing and zero
   propagation
5. **Dense A₃₁[i] matrix product**: verifies all A₃₁ lanes, real/imaginary
   terms, and three-term accumulation with oracle-derived packed constants

All test cases pass under Icarus Verilog. The testbench is
auto-discovered by the project's `run_all_tests.py` regression suite.

### 4.3 Bit-Exact Parity

The Python oracle and the Verilog testbench produce identical results
for all test cases. The Python oracle serves as the golden reference;
the Verilog RTL is verified against it. This mirrors the verification
methodology used for the Lucas MAC and RPLU v2 pipelines [LUCAS, RPLU2].

### 4.4 Wukong Artix-7 Silicon Smoke

On 2026-07-04, the Wukong Artix-7 SU3 sidecar-only bitstream
`build/spu_a7_100t_SU3.bit` was SRAM-loaded through RP2040 DirtyJTAG at
1 MHz. The RP2350 J11 smoke firmware
`build/rp2350_arithmetic/rp2350_su3_j11_smoke.uf2` then streamed the dense
A/B matrix fixture over the existing SPI `0xB1` path at 100 kHz with 20 us
CS setup, read turnaround, CRC hold, and CS recovery delays. The link layer
supports per-link timing overrides, so these shorter timings are scoped to the
SU3 smoke app. The host checker polls per-chunk debug status and treats final
`LOAD_B` completion as `SIDE_IDLE + result_ready`, since the internal
`SIDE_WAIT` state can complete before a host status read observes it.

Three independent result elements were selected and read back through the QR
commit path:

| Result | QR lane | A | B | C | D |
|---:|---:|---|---|---|---|
| 0 | 2 | `0x7FFE271F7FFC43EF` | `0x7FFF6B677FFED36F` | `0x00021510000446A0` | `0x0000A30000014F30` |
| 4 | 5 | `0x7FFD2A6B7FFA47FF` | `0x7FFF196B7FFE2E9F` | `0x00034B480006BAA8` | `0x00010678000218A8` |
| 8 | 8 | `0x7FFBF6DF7FF7DE5F` | `0x7FFEB5277FFD653F` | `0x0004CAA00009C0F0` | `0x00018250000312E0` |

The initial firmware reported exact matches for all three cases and ended with
`SU3_J11: PASS`. A 40-second capture at 100 kHz and 20 us guards showed
thirteen complete three-case passes before timing out mid-run 13. A 5 us
guard-delay probe produced an intermittent invalid QR read, so 20 us is the
current practical margin setting.

On 2026-07-06, the SU3SHARE smoke was expanded to all nine dense-product
result elements, read through QR lanes 0 through 8. Two complete capture loops
reported exact matches for every element and ended with `SU3_J11: PASS`.

---

## 5. Integration Path

### 5.1 Spin Ladder Integration

The SU(3) module has been added to the Artix-7 synthesis script
(`synth_a7.ys`). It will be compiled as part of every future build,
but Yosys prunes unused modules during hierarchy optimisation — the
SU(3) module adds zero cost until it is instantiated at the top level.

### 5.2 Host Interface

The element-wise load interface is compatible with the existing SPI
command path (CMD 0xB1, used by the Lucas MAC sidecar). Each 256-bit
element is loaded as eight 32-bit chunk writes. A full 3×3 multiply
requires 144 chunk writes (9 elements for A, 9 for B), one start command,
and one read command for the selected result element.

### 5.3 Larger Moduli

The module is parametrised on L_P and L_P_BITS for Lucas prime
moduli, supporting any Lucas prime up to L₁₉ = 9349 (14-bit operands)
with zero RTL changes. The multiplier handles this natively since
the M31 multiplier operates on fixed 32-bit words regardless of the
effective modulus precision.

---

## 6. Discussion

### 6.1 Applications

The primary application is not large-scale lattice QCD — the 32-bit
M31 field is too small for double-precision physics. The natural
niche is topological and Fibonacci anyon models [FREEDMAN] where:

- The algebra is naturally small-domain (φ-period 26 for L₁₃)
- Exactness matters more than precision
- The SU(3) structure maps directly to anyon fusion rules

A secondary application is exact unitary benchmarking: verifying that
a sequence of unitary operations closes to identity within a finite
field, without floating-point drift.

### 6.2 Limitations

- **Guarded bring-up link**: The functional silicon proof currently uses a
  100 kHz SPI stream with 20 us guard delays. A 5 us probe showed intermittent
  QR read invalidity, so further host-link tuning should raise SPI speed from
  the 20 us baseline rather than treating 5 us as stable.
- **Small field**: M31 is a 32-bit prime. SU(3) operations over this
  field are exact but low-precision. Larger applications require
  multiple residues or larger Mersenne primes.
- **Only multiplication**: Group exponentiation, logarithm, and
  generator decomposition are not implemented. These are FSM
  extensions but represent additional engineering effort.
- **No exponential map**: The matrix exponential $\exp(X)$ for
  $X \in \mathfrak{su}(3)$ is not implemented. The paper works
  entirely in the group domain via direct matrix multiplication,
  as $\exp(X)$ involves factorials that are not well-defined in
  finite characteristic.

### 6.3 Future Work

- Generator exponentiation via repeated squaring
- SU(N) generalization for N > 3
- Integration with the Lucas MAC for combined φ + unitary arithmetic
- Standalone SU(3) probe on Tang 25K (following the PHSLK microprobe
  pattern)
- Multi-residue extension using Chinese Remainder Theorem for
  higher-precision unitary arithmetic

---

## References

1. Lucas, E. "Theorie des Fonctions Numeriques Simplement
   Periodiques." 1878.
2. Crandall, R.E. & Pomerance, C. "Prime Numbers: A Computational
   Perspective." Springer, 2nd ed., 2005.
3. Freedman, M., Larsen, M., Wang, Z. "A modular functor which is
   universal for quantum computation." arXiv:quant-ph/0001108, 2000.
4. Gell-Mann, M. "Symmetries of Baryons and Mesons." Phys. Rev. 125,
   1067 (1962).
5. [LUCAS] Curley, J. "Zero-Drift Lucas-Prime Phinary Arithmetic for
   Exact Quantum Phase Coherence on FPGA." 2026.
6. [RPLU2] Curley, J. "A Hardware Jet Algebra Coprocessor over a
   Split M31 Biquadratic Algebra." 2026.
7. SPU-13 Project. Open-source RTL and oracles. CC0 1.0 Universal.
   https://github.com/pinnacletechnologysolutionsltd/SPU

---

## Appendix A: Python Oracle (Abridged)

```python
P = 2147483647  # M31

def a31_mul(a, b):
    """A₃₁ multiplication. 16 parallel products reduced mod M31."""
    c0, c1, c2, c3 = a; d0, d1, d2, d3 = b
    return (
        (c0*d0 + 3*c1*d1 + 5*c2*d2 + 15*c3*d3) % P,
        (c0*d1 + c1*d0 + 5*c2*d3 + 5*c3*d2) % P,
        (c0*d2 + c2*d0 + 3*c1*d3 + 3*c3*d1) % P,
        (c0*d3 + c1*d2 + c2*d1 + c3*d0) % P,
    )

def ca_mul(r1, s1, r2, s2):
    """A₃₁[i] multiply: (r1 + i s1)(r2 + i s2)."""
    rr = a31_mul(r1, r2); ss = a31_mul(s1, s2)
    rs = a31_mul(r1, s2); sr = a31_mul(s1, r2)
    return (a31_sub(rr, ss), a31_add(rs, sr))  # real, imag

def mat_mul(A, B):
    """3×3 matrix multiply over A₃₁[i]. 27 complex multiplies."""
    C = [[ca_zero() for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for k in range(3):
            for j in range(3):
                C[i][j] = ca_add(C[i][j], ca_mul(A[i][k], B[k][j]))
    return C
```

Full oracle with 20 checks and Gell-Mann matrix definitions:
`software/tests/test_su3_oracle.py`
