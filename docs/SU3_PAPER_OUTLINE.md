# SU(3) Matrix Arithmetic over A₃₁[i]: A Deterministic Unitary Coprocessor Extension

**Target:** Short technical report / arXiv preprint (cs.AR, quant-ph)

**Status:** Outline — RTL complete, oracle and testbenches verified, Wukong Artix-7 SU3 sidecar synthesis/routing/bitstream/JTAG configuration checked, and J11 SPI/QR silicon smoke passing for three dense-matrix result elements

---

## Outline

### 1. Introduction
- **Problem:** SU(3) is central to lattice QCD, topological quantum computing,
  and anyonic braid models. Standard implementations use IEEE-754 floating point,
  accumulating rounding error over long unitary evolution sequences.
- **Approach:** Extend the existing A₃₁ split biquadratic algebra over M31
  (Mersenne prime 2³¹−1) with a complex extension i² = −1, giving the
  degree-8 algebra A₃₁[i]. All arithmetic is exact modular arithmetic —
  no floating point, no rounding, no division in hot paths.
- **What exists:** RTL module (`spu13_su3_mult.v`) implementing 3×3 matrix
  multiplication over A₃₁[i] via time-division multiplexing through a dedicated
  standalone `spu13_m31_multiplier` instance. Python oracle (20 checks) and
  Verilog testbench (5 public-output cases) verify bit-exact correctness.
  A SPI-visible Wukong Artix-7 sidecar (`spu13_su3_sidecar.v`) streams host
  chunks into the multiplier over the existing CMD `0xB1` instruction path.
- **What this paper is:** An architectural extension study with verified
  arithmetic and first silicon readback. The RTL and sidecar integration are
  simulation-verified. Wukong Artix-7 synthesis, 2 MHz routing, bitstream
  generation, DirtyJTAG configuration, and RP2350 J11 SPI/QR smoke testing are
  complete for the dense-matrix fixture.

### 2. Mathematical Foundation
- A₃₁ split biquadratic algebra over M31 (review)
  - Basis [1, √3, √5, √15], 4-tuple representation
  - Conjugate reduction tower for inversion (~76 cycles)
- Complex extension A₃₁[i]
  - i² = −1, degree-8 basis
  - Complex A₃₁ multiplication: 4 A₃₁ base products per complex multiply
  - Inversion via extended tower (~114 cycles)
- SU(3) structure constants in A₃₁[i]
  - Gell-Mann matrices λ₁−λ₈: entries in {0, ±1, ±½, ±√3/2}
  - ½ ≡ modular inverse of 2 in M31
  - √3 ∈ A₃₁ natively, √−1 ∈ A₃₁[i] natively
  - Determinant = 1 verified via oracle

### 3. RTL Design
- Multiplier topography
  - Dedicated standalone `spu13_m31_multiplier` instance
  - 16 logical parallel 32×32 products; standalone Artix-7 synthesis maps them to 64 DSP48E1
  - 4-phase TDM: RR → II → RI → IR for each complex A₃₁[i] multiply
  - ~8 cycles per complex multiply (4 A₃₁ products × 2-cycle throughput)
- 3×3 matrix multiply FSM
  - Element-wise load interface (9 × 256-bit elements per matrix)
  - Triple-nested loop: C[i][j] = Σₖ A[i][k] · B[k][j]
  - 27 complex multiplies × ~8 cycles ≈ 224 compute cycles
  - Current public interface streams row-major result elements as each C[i][j] completes
  - Pipeline diagram showing multiplier and accumulator stages
- Resource estimate
  - 64 DSP48E1 standalone on Artix-7
  - ~6.2k estimated LCs for the multiplier on Artix-7 after removing C-matrix storage
  - ~8.2k estimated LCs for the Wukong SU3 sidecar-only spin
  - 64 DSP48E1, 21.1k packed LUT cells, 9.5k packed FFs in the current SU3 spin snapshot
  - `A7_CLK_DIV_LOG2=6` for first smoke: 50 MHz oscillator -> ~781 kHz `clk_fast`
  - Post-route timing: 51.58 MHz max for `clk_div[5]`, PASS at the 2 MHz route target
  - ~224 cycles, with result pulses integrated into compute completion

### 4. Verification
- Python oracle (`test_su3_oracle.py`): 20 checks
  - A₃₁[i] arithmetic consistency (i² = −1)
  - 3×3 matrix multiply closure (I×I, λ₁×λ₁, λ₁×λ₃)
  - Dense A₃₁[i] packed matrix-product constants used by the RTL testbench
  - Gell-Mann structure constants (λ₁² = diag(1,1,0), λ₃ diagonal, λ₈ basis encoding)
  - Determinant verification (det(I) = 1)
  - Conjugate transpose correctness (self-adjoint check)
  - PHSLK-style coherence check (λ₁·λ₁† = λ₁²)
- Verilog testbench (`spu13_su3_mult_tb.v`): 5 public-output test cases
  - I × I = I (identity closure)
  - λ₁ × λ₁ = diag(1,1,0) (non-diagonal multiplication)
  - I × λ₁ = λ₁ (operand preservation)
  - Zero × I = Zero (zero propagation and accumulator clearing)
  - Dense A₃₁[i] matrix product (all lanes active)
  - All pass under Icarus Verilog
- Bit-exact parity between Python oracle and RTL simulation
- Wukong Artix-7 silicon smoke over RP2350 J11 SPI
  - Streams the dense A/B fixture at 100 kHz with 20 us per-link guards
  - Checks elem 0/lane 2, elem 4/lane 5, and elem 8/lane 8 through QR readback
  - All three exact 256-bit result commits match the oracle; firmware reports `SU3_J11: PASS`
  - A 40-second capture showed thirteen complete three-case passes before timing out mid-run 13
  - A 5 us guard probe produced an intermittent invalid QR read, so 20 us is the current margin setting

### 5. Integration Path
- Adding to the SPU-13 spin ladder
  - Source added to `synth_a7.ys` and `SPIN="SU3"` path in `spu_a7_top.v`
  - First P&R target met: Wukong Artix-7 100T at 2 MHz, bitstream emitted
  - Standalone SU(3) probe on Tang 25K remains possible, but Wukong is the priority target
- Interface with existing pipeline
  - SPI command 0xB1 instruction path (same physical southbridge path as Lucas MAC sidecar)
  - `EA/E8/E9/EB` sidecar opcodes: start, stream A, stream B, read captured result
  - QR commit path for 256-bit result readback as A/B/C/D lanes
  - PHSLK coherence check on unitary products
- Larger modulus options (L₁₇ = 3571, L₁₉ = 9349)

### 6. Discussion
- **Why this matters:** Exact SU(3) arithmetic enables drift-free simulation of
  unitary evolution over finite fields. The primary application is not
  large-scale lattice QCD (which needs larger fields) but topological/
  Fibonacci anyon models where the algebra is naturally small-domain.
- **Limitations:**
  - M31 is small (32-bit). Larger unitary groups or higher precision need
    multiple residues or larger Mersenne primes.
  - Only 3×3 multiply implemented. Group operations (exp, log, generator
    exponentiation) are FSM extensions, not fundamental changes.
  - The current silicon smoke uses 100 kHz SPI and 20 us guard delays.
    Higher SPI speed and higher clock targets remain future timing work.
- **Future work:**
  - Generator exponentiation via repeated squaring
  - SU(N) generalization for N > 3
  - Integration with the Lucas MAC for combined φ + unitary arithmetic

### References
- Same Lucas/Euler/Pell references as Lucas MAC paper [1-5]
- Gell-Mann matrices standard reference
- Freedman-Larsen-Wang for Fibonacci anyon connection [10 from Lucas paper]
- A₃₁ conjugate reduction tower [internal, from RPLU v2 pipeline]

---

**Current artifacts:**
- `hardware/rtl/core/spu13/spu13_su3_mult.v` — RTL module
- `hardware/rtl/core/spu13/spu13_su3_sidecar.v` — SPI-visible Wukong sidecar
- `hardware/tests/spu13/spu13_su3_mult_tb.v` — Verilog testbench
- `hardware/tests/spu13/spu13_su3_sidecar_tb.v` — sidecar protocol testbench
- `software/tests/test_su3_oracle.py` — Python oracle (20 checks)
- `docs/SU3_EXTENSION_PLAN.md` — Implementation notes
- `build/spu_a7_100t_SU3.bit` — Wukong Artix-7 100T SU3 bring-up bitstream
- `build/rp2350_arithmetic/rp2350_su3_j11_smoke.uf2` — RP2350/J11 dense-product smoke firmware
