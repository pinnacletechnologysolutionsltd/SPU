# SPU v0.3 Architecture Proposal

**Status: PROVISIONAL.** This is a design exploration, not an accepted ISA or a frozen
architectural contract. Nothing here is implemented, simulated or measured.

> SPU v0.2 Gen-1 is frozen. This proposal describes possible v0.3 behaviour. It does not
> amend the [Gen-1 architectural contract](../GEN1_ARCHITECTURAL_CONTRACT.md), the RTL, the
> instruction encodings or the `gen1-surd` simulator profile.

This document is not part of the curated v0.2 release.

> **Status update (2026-11-11).** This proposal predates SIM-0. The experimental `programmable-surd`
> simulator profile now implements and tests the candidate instruction set over Q(√3) (`60a70357`,
> in the development gate since `98ed4612`). The later [ISA draft](SPU_V03_ISA_DRAFT.md) and the
> [SIM-0 discrepancy report](SPU_V03_SIM0_DISCREPANCY_REPORT.md) record the current experimental
> behaviour, including the answer to Q4 (recoverable OVERFLOW). This proposal remains provisional, is
> kept as historical design context, and is not the authoritative execution contract. One statement
> in §4 is corrected in place (marked).

## 1. Objective

v0.2 shows that the exact Surd arithmetic machine works: one register, four instruction
forms and a fixed ROM program. **v0.3 should show that it can run useful mathematical
programs**: complete algorithms with general register arithmetic, comparisons and
control flow, loaded at run time.

The finish line is programmability. Generalizing the domain (§4) is an experimental
extension, not a v0.3 requirement.

## 2. Architectural foundation

### 2.1 Unified Surd registers

There are eight architectural registers, S0–S7. Each holds one value

  x = (a + b√n) / d,  with a and b signed 64-bit, d unsigned 64-bit and d ≠ 0.

This is the same 192-bit tuple layout as Gen-1. Ordinary integers and rationals use the
same representation (b = 0). No separate integer register file is visible to the
programmer. Whether one is needed is an open question (§5, Q1).

### 2.2 Arithmetic and refusal

The starting point is Gen-1's finite-width semantics, extended from S0 to all registers
and to every arithmetic operation:

- A raw result that fits commits **unreduced**.
- Otherwise the result is normalized exactly by its gcd and committed if it fits.
- Otherwise the operation refuses (OVERFLOW) and the destination is unchanged.

Candidate operations are `SADD`, `SSUB` and `SMUL` on any registers. The core already
contains `SADD`, `SSUB`, `SNORM` and `SSTAT` hardware (0x74–0x77), which the Gen-1
frontend does not accept (contract §10). That hardware is a starting point, not an adopted
specification. It has not been shown to implement these semantics for addition and
subtraction. The v0.3 contract must define the complete behaviour of each operation,
including intermediate widths and noncanonical operands, and verify it against the RTL
separately.

### 2.3 Integers and canonical form

Instructions that need an integer (branch targets, loop counters, addresses, shift
amounts) require an **ordinary integer**: a value equal to (k, 0, 1).

Because raw-fit commits unreduced, an integer value can be held as, say, (6, 0, 2).
Before the integer rule can be frozen, one of two rules must be chosen (Q5):

- (a) such instructions refuse unless the bit pattern is exactly (k, 0, 1); or
- (b) they accept any tuple whose value is an integer and reduce it. For a valid tuple
  (n square-free, not a square), the value is an ordinary integer exactly when b = 0 and
  d divides a. That is an integer divisibility check, not a general normalization; its
  hardware cost is not established.

Rule (a) is cheaper and stricter. It would need an explicit `SNORM` before control use,
or a fast integer path that keeps d = 1.

"Ordinary integer" is not the same as "algebraic integer". In Q(√5) and Q(√−3),
algebraic integers include values with d = 2, such as φ = (1, 1, 2) and ω = (−1, 1, 2).
The ISA's integer rule refers only to ordinary integers.

## 3. Programmability

These are the candidate essential capabilities. Their encodings are not decided.

| Capability | Notes |
|---|---|
| General `SADD`, `SSUB`, `SMUL` on S0–S7 | Gen-1 refusal semantics (§2.2) |
| Register access | Load an immediate or tuple into any register; read any register out |
| Exact equality | Compares values, not bit patterns: (2,0,2) = (1,0,1). Defined in every domain |
| Ordered comparison (n > 0 only) | Sign of a + b√n, since d > 0. If a and b have opposite signs, compare a² with n·b². With \|b\| ≤ 2⁶³, n·b² ≤ n·2¹²⁶: this fits in 128 bits for n = 3 but needs 129 for n = 5. Comparing two tuples needs denominator cross-products and differences first, which need more width (Q7) |
| Conditional branch and jump | On a comparison result or status; targets are ordinary integers or immediates |
| Explicit termination | A `HALT` instruction, replacing Gen-1's fixed "HALT at PC 14" |
| Reusable program loading | Programs loaded at run time rather than built into the bitstream (Q2) |

**Opcode constraint.** Opcodes 0x70–0x73 currently carry two conflicting meanings
(contract discrepancy D1: telemetry names in `spu13_arch.h`, `spu_isa_defines.vh` and the
assembler). v0.3 must not quietly reuse either meaning. The conflict has to be resolved
explicitly, together with the question of compatibility with Gen-1 encodings (Q6),
before any opcode is allocated.

## 4. Quadratic domains

The architectural baseline remains **Q(√3)**. Multiplication generalizes as

  (a + b√n)(c + e√n) = (ac + n·be) + (ae + bc)√n,

so only the constant n in the product changes. Gen-1 hard-codes n = 3 in
`surd_cpu_products.v`.

Experimental build-time configurations:

| n | Field | Ordering | Typical use |
|---|---|---|---|
| 3 | Q(√3) | Yes | Baseline; Pell units; 30° geometry |
| 5 | Q(√5) | Yes | Golden ratio, pentagonal and icosahedral constructions |
| −1 | Q(i) | No | Gaussian arithmetic, square lattice |
| −3 | Q(√−3) | No | Eisenstein arithmetic, hexagonal lattice |

Provisional rules:

- **One domain per build.** The domain is a simulator profile parameter, and later a
  per-domain bitstream. There are no per-register domain tags and no runtime domain switching.
- **Ordering in real fields** (n > 0) uses the embedding with √n > 0.
- **Imaginary fields** (n < 0): ordered comparisons **refuse**, and equality remains
  available. The norm a² − n·b² is positive definite there. It is not an ordering and
  must not be used as one.
- **Rationals (b = 0) belong to every quadratic field.** With one domain per build, no
  cross-domain operation can occur, so this rule needs no runtime check in the first
  design. It matters only for a possible later tagged design. *(Corrected 2026-11-11: an
  earlier wording said the domain could be derived from the value rather than stored. That is
  wrong for irrational values: the tuple (1, 1, 2) is (1 + √3)/2 in Q(√3) and (1 + √5)/2 in
  Q(√5).)* In a tagged design a register must **store** its domain whenever b ≠ 0; when b = 0
  the value is domain-neutral. Whether a rational result clears a stored tag is a separate policy
  choice. Two non-rational operands from different domains would refuse. Tags do not make sums
  such as √3 + √5 representable; that needs a degree-4 field.
- **Hardware cost is unestablished.** With |n| ≤ 5, the term n·be needs up to 3 more bits
  than b·e (Gen-1 needs about 2 for ×3), plus one bit for the sum. Area, multiplexing and
  timing need synthesis evidence before any claim is made.
- These are fields over Q, so every nonzero value is invertible. A₃₁ (the split algebra
  modulo M31, which has zero divisors) is a separate structure and is out of scope here.

## 5. Open questions

| # | Question |
|---|---|
| Q1 | Register pressure: are eight registers enough without memory or spilling? (See §7.) Is a separate integer path or file warranted? |
| Q2 | Program storage and loading: instruction memory size; how programs are loaded (UART, as in H0, or otherwise); whether programs can read data memory |
| Q3 | Control-flow semantics: branch-offset form, PC width, and behaviour at the end of memory and on an invalid target |
| Q4 | Refusal inside a program: does OVERFLOW halt, trap or set a status that the program can branch on? Gen-1 always faults; a programmable machine probably needs status the program can inspect |
| Q5 | Integer canonical form: rule (a) or rule (b) in §2.3 |
| Q6 | Encoding compatibility with Gen-1 forms and resolution of D1 |
| Q7 | Determine the exact intermediate widths and refusal semantics for equality and ordered comparison of two finite-width Surd tuples. The sign test for a + b√n alone may need more than 128 bits (129 for n = 5) |
| Q8 | Fast path for b = 0, d = 1: Gen-1's `SADD` always runs the gcd aligner. The latency of integer loops depends on this |
| Q9 | Observation: the result and status output format beyond the Gen-1 33-byte frame |

## 6. Deliberately deferred

The following are **not** part of v0.3:

- RPLU2 integration;
- specialized rotor instructions;
- GPU integration;
- HEX-SOM hardware;
- runtime domain switching;
- per-register domain tags;
- degree-4 extensions such as Q(√3, √5).

Rational Calculus and quadray geometry are candidate **application workloads**, not
hardware subsystems. The research programme is not the minimum feature set of the next
processor.

## 7. Representative workload (pseudocode, hand liveness analysis)

The primary workload is an exact 2-D orientation predicate. Given points A, B and C with
coordinates in Q(√3), compute the sign of

  det = (bx − ax)(cy − ay) − (by − ay)(cx − ax).

```
; inputs: S0=ax S1=ay S2=bx S3=by S4=cx S5=cy      live: 6
SSUB S2, S2, S0     ; bx-ax                         live: 6
SSUB S4, S4, S0     ; cx-ax   (ax dead)             live: 5
SSUB S3, S3, S1     ; by-ay                         live: 5
SSUB S5, S5, S1     ; cy-ay   (ay dead)             live: 4
SMUL S0, S2, S5     ; (bx-ax)(cy-ay)                live: 3 (S0,S3,S4)
SMUL S1, S3, S4     ; (by-ay)(cx-ax)                live: 2
SSUB S0, S0, S1     ; det                           live: 1
SCMP S0, #0         ; ordered: needs n > 0
BLT  neg / BEQ zero / else pos
HALT
```

Hand liveness analysis gives a peak of **6 live registers**, at entry, when all inputs are
preloaded. This fits in eight registers. It uses three of the candidate capabilities (§3):
any-register `SSUB`/`SMUL`, an ordered comparison against zero, and a conditional branch.
Each `SSUB` and `SMUL` can refuse (Q4).

**Pressure indicator.** The analogous in-circle predicate takes four points (8 inputs) and
a 3×3 determinant of lifted coordinates. If all inputs are resident at once, they fill all
eight registers and leave none spare. Whether data memory is essential remains open (Q1, Q2):
streaming the inputs, recomputing intermediates or another evaluation schedule might
avoid it. This is a paper estimate, not a measurement.

The secondary workload is the Pell recurrence x ← (2 + √3)·x, repeated k times:

```
; S0=x  S1=(2,1,1)  S2=i=(0,0,1)  S3=one=(1,0,1)  S4=k
loop: SMUL S0, S0, S1
      SADD S2, S2, S3      ; integer increment: wants the b=0,d=1 fast path (Q8)
      SCMP S2, S4
      BLT  loop
      HALT
```

This uses 5 live registers. It exercises integer control in Surd registers (§2.3) and
OVERFLOW refusal once x grows beyond 64 bits (Q4).

## 8. Development sequence

1. Write and review this brief (now; documentation only).
2. Extend the representative workloads in §7 until they settle Q1–Q5.
3. Write the v0.3 architectural contract, frozen, with encodings.
4. Build an experimental simulator profile (`programmable-surd`, name provisional) with
   conformance fixtures. The `gen1-surd` profile stays unchanged.
5. Implement the RTL and match it to the simulator fixtures.
6. Run synthesis and timing.
7. Run on the board and record the results in the hardware evidence ledger.

Domain configurations other than n = 3 enter at step 4 as profile parameters, and enter
hardware only if the workloads show a need.
