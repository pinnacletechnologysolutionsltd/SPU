# Lucas Phinary MAC — Architecture Note

**Date:** 2026-06-29
**Status:** Design strategy — future co-processor for SPU-13
**Dependency:** None (scoped addition, no existing RTL changes)

## 1. Motivation

The SPU-13 core operates over the Mersenne prime M₃₁ = 2³¹−1 with fast
bit-wrap modular reduction.  This ring handles high-density F_{p⁴} rational
function evaluation exactly.  However, certain geometric operations — 
chirality transforms, irrational ratio scaling by φ, √5, and wave
interference patterns — are naturally expressed in base-φ (phinary)
arithmetic over a Lucas prime modulus.

Rather than contaminate the proven M₃₁ pipeline, the Phinary MAC is a
dedicated co-processor that speaks its own ring: ℤ[φ] / Lₚ .

## 2. Mathematical Foundation

### 2.1 The Golden Ring ℤ[φ]

φ = (1+√5)/2 is a root of x² − x − 1 = 0, giving the identity φ² = φ + 1.
Numbers in ℤ[φ] are of the form a + bφ with a,b ∈ ℤ.

### 2.2 Lucas Primes as Moduli

The Lucas sequence Lₙ = φⁿ + (−1)ⁿφ⁻ⁿ provides the phinary analogue of
Mersenne numbers.  When p is prime and Lₚ is prime, Lₚ is a *Lucas prime*.

| p | Lₚ | Prime? |
|---|-----|--------|
| 3 | 4   | No     |
| 5 | 11  | Yes    |
| 7 | 29  | Yes    |
| 11| 199 | Yes    |
| 13| 521 | Yes    |

Just as M₃₁ = 2³¹−1 enables fast bit-wrap reduction (2³¹ ≡ 1 mod M₃₁),
a Lucas modulus Lₚ enables fast shift-wrap reduction: φᵖ ≡ ±1 mod Lₚ.

### 2.3 Why Not Merge Rings

Primes in ℤ split in ℤ[φ]:
```
11 = (3+φ)(4−φ)       ← 11 is prime in ℤ, composite in ℤ[φ]
```

Merging the M₃₁ and ℤ[φ] rings would introduce zero-divisors into the
F_{p⁴} pipeline.  The rings must remain isolated — connected only through
the BTU spatial router which passes discrete binary result pairs.

## 3. Co-Processor Topology

```
                 ┌──────────────────────────────────────┐
                 │         RP2350B DMA Stream           │
                 └──────────────────┬───────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │   BTU Spatial Router    │
                       └───────┬───────────┬─────┘
                               │           │
       ┌───────────────────────┴─┐       ┌─┴───────────────────────┐
       │    M31 BINARY CORE      │       │   PHINARY MAC (LUCAS)   │
       ├─────────────────────────┤       ├─────────────────────────┤
       │ Ring:  ℤ / M₃₁          │       │ Ring:  ℤ[φ] / Lₚ        │
       │ Fast reduction: 2³¹≡1   │       │ Fast reduction: φᵖ≡±1  │
       │ Pipeline: 76-cycle      │       │ Pipeline: φ-shift-add   │
       │ Inverter: Fermat chain  │       │ Inverter: Lucas inverse  │
       │ Multiplier: 16 DSP      │       │ Multiplier: φ-MAC       │
       │ Functions: F_{p⁴} Padé  │       │ Functions: chirality,   │
       │   rational evaluation   │       │   ratio scaling, wave   │
       └─────────────────────────┘       └─────────────────────────┘
```

## 4. Phinary MAC Operation Set

| Operation | Description | Phinary Advantage |
|---|---|---|
| PSCALE | Scale by φⁿ | Single shift-add (φ² = φ+1) |
| PCHIRAL | Chirality transform | Exact left↔right coordinate map |
| PWAVE | Wave interference | Deterministic φ-phase accumulation |
| PINV | Lucas inverse | Extended Euclidean over ℤ[φ] |
| PMUL | Full φ-multiply | Shift-add MAC, no DSP |

### 4.1 PSCALE — The Killer Feature

In binary, scaling by an irrational ratio requires floating-point.
In phinary, φ·(a + bφ) = b + (a+b)φ — a single shift-and-add.  No
multiplier, no DSP, no approximation.  This is the exact analogue of
the M₃₁ bit-wrap: structural efficiency from algebraic structure.

### 4.2 PCHIRAL — Chirality Transform

The SPU-4 `chiral_phinary_adder_param.v` already proves phinary chirality
in silicon.  The transform maps between left-handed and right-handed
coordinate representations using φ-conjugation: conj(a + bφ) = (a+b) − bφ.

## 5. Integration Points

### 5.1 BTU Spatial Router

The BTU already routes between the SOM BMU and the RPLU2 Padé evaluator.
Adding a phinary lane means the BTU gains a third routing target:
- Lane 0: M31 binary core (existing)
- Lane 1: RPLU2 Padé evaluator (existing)
- Lane 2: Phinary MAC (future)

The BTU's 64→6 priority encoder and backlog queue handle the arbitration.

### 5.2 QR Register File

Phinary results arrive as discrete binary pairs (a, b) representing
a + bφ.  These pack into the existing 64-bit RationalSurd register layout
without modification — the register file is agnostic to the ring semantics.

### 5.3 Instruction Encoding

New opcodes in the 0x50–0x5F range (currently unused):
- PSCALE (0x50): φ-scale with shift count
- PCHIRAL (0x51): chirality transform
- PWAVE (0x52): φ-phase accumulation
- PINV (0x53): Lucas inverse
- PMUL (0x54): full φ-multiply

## 6. Resource Budget

| Component | LUTs | DFFs | DSPs | Notes |
|---|---|---|---|---|
| φ-adder (chiral) | ~80 | ~40 | 0 | SPU-4 proven, port to GW5A |
| φ-multiply MAC | ~200 | ~100 | 0 | Shift-add cascade |
| Lucas inverse | ~300 | ~150 | 0 | Extended Euclidean variant |
| BTU lane routing | ~50 | ~20 | 0 | Additional lane mux |
| **Total** | **~630** | **~310** | **0** | |

With 7,800 LUTs free on the current southbridge build (66% utilization),
the Phinary MAC fits comfortably.

## 7. Prior Art in the Tree

- `hardware/rtl/core/spu4/chiral_phinary_adder_param.v` — SPU-4 satellite
  φ-adder, proven in simulation
- `knowledge/NGUYEN_WEIGHT_PARTITIONING.md` — laminar weight partitioning,
  compatible with φ-weighted SOM updates
- SPI southbridge protocol — already handles multi-target routing via 0xA5
  selector fields (selectors 0–7, currently using 1–6)

## 8. References

1. Lucas, E., "Theorie des Fonctions Numeriques Simplement Periodiques," 1878.
2. Fibonacci Quarterly — Lucas prime tables.
3. `knowledge/rplu_formal_spec.md` — M31 arithmetic foundation.
4. SPU-4 chiral phinary adder: `hardware/rtl/core/spu4/chiral_phinary_adder_param.v`
