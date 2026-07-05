# Lucas Phinary MAC — Architecture Note

**Date:** 2026-06-30
**Status:** RTL sidecar plus Wukong routed/packed bring-up image; hardware load pending
**Dependency:** None (scoped addition, no existing RTL changes)

## 1. Motivation

The SPU-13 core operates over the Mersenne prime M₃₁ = 2³¹−1 with fast
bit-wrap modular reduction.  This ring handles high-density A₃₁ rational
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
A₃₁ pipeline.  The rings must remain isolated — connected only through
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
       │ Functions: A₃₁ Padé  │       │ Functions: chirality,   │
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
| PHSLK | Phase coherence check | Cross-multiply rational encodings; no inverse |

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

The Artix-7 sidecar proof uses temporary top-level probe opcodes delivered via
SPI `CMD 0xB1`, avoiding the existing RPLU config range at `0x50`-`0x5F`:

- PSCALE (`0xD0`): phi-scale `a+bφ`
- PCHIRAL (`0xD1`): chirality/conjugation transform
- PMUL (`0xD2`): full product `(a+bφ)(c+dφ)`
- PINV (`0xD3`): algebraic inverse `(a+bφ)^-1`
- PHSLK load/exec (`0xD4`/`0xD5`): two-word rational coherence check
  `n1*d2 == n2*d1`

These are temporary sidecar probe opcodes delivered through SPI `CMD 0xB1`;
the long-term ISA map for PWAVE and permanent phinary operations remains open
until the RPLU config opcodes are moved behind a prefix or otherwise retired.

## 6. Resource Budget

| Component | LUTs | DFFs | DSPs | Notes |
|---|---|---|---|---|
| φ-adder (chiral) | ~80 | ~40 | 0 | SPU-4 proven, port to GW5A |
| PSCALE/PCHIRAL fast paths | Included in MAC | synthesis-mapped | 0 | Shift-add only |
| Tang `FAST_ONLY=1` probe | 696 LUT4 | 216 | 0 | Silicon-verified with UART `LUCAS:P` |
| Full Lucas MAC | 588 LCs | synthesis-mapped | 40 | Artix-7 proof with Barrett reducer |
| SPI sidecar + MAC | 641 LCs | synthesis-mapped | 40 | D0-D3 Artix-7 sidecar proof |
| Tang PHSLK microprobe | 293 LUT4 | 146 | 0 | Post-route 200.40 MHz, 4.99 ns critical path; SRAM UART `PHSLK:P` |
| BTU lane routing | ~50 | ~20 | 0 | Additional lane mux |
| **Current LUCAS spin** | **4,521 LCs** | **routed + packed** | **40** | Whole SPI-visible Wukong profile at `A7_FREQ=2` |

As of 2026-06-30, the current Wukong V02 `LUCAS` spin routes and packs into
`build/spu_a7_100t_LUCAS.bit`. The routed max frequency is 4.11 MHz, so the
2 MHz image is a bench bring-up artifact for JTAG, reset, UART, and SPI proof.
It is not a final timing-closed Lucas datapath.

The full Lucas MAC now fits comfortably on Artix-7. The Tang 25K should still
use PSCALE/PCHIRAL slice probes by default. The current `FAST_ONLY=1` Tang
probe has been SRAM-loaded and reports `LUCAS:P` over UART, proving PSCALE,
PCHIRAL, and a 100-period PSCALE zero-drift marathon in silicon with no DSPs.
A dedicated Tang PMUL/PINV probe is worth keeping as future work, but the
current open Gowin flow does not yet infer the expected multiplier primitives
for the full `FAST_ONLY=0` MAC. The June 2026 standalone Tang full-MAC synthesis
reached nextpnr utilization with about 5,359 LUT4, 1,334 ALU cells, 351 DFFs,
and zero `MULT12X12`/`MULTALU27X18`/`MULTADDALU12X12` blocks inferred before
placement was stopped. Treat Tang full-PMUL as a measurement-driven
optimization target, not as assumed spare capacity.

For the Tang path, the next clean experiment is a small PMUL-only profile:
register four 10x10 products, reduce two outputs modulo 521, and either guide
inference into Gowin multiplier primitives or instantiate the GW5A multiply
blocks explicitly. If that routes cleanly, it becomes a useful SPU-4/Lucas
coprocessor demo. If it does not, Tang remains the zero-DSP chirality probe and
Artix-7 remains the full Lucas MAC target.

## 7. PHSLK as Anyon-Capture Predicate

PHSLK is the hardware primitive; "anyon capture" is the application-level
interpretation when an upstream braid, fusion, or syndrome compiler represents
an observed topological phase and a candidate template as rational elements of
ℤ[φ]/L₅₂₁.

The predicate is:

```
coherent, zero_divisor = PHSLK(observed_n, observed_d,
                              template_n, template_d)
valid_capture = coherent && !zero_divisor
```

This is intentionally not a claim that the FPGA directly observes physical
anyons. The FPGA receives reduced rational phase encodings and answers a
bounded algebraic question: whether the two encodings project to the same
phase without requiring denominator inversion. A zero-divisor denominator is
not a capture; it is an ambiguous or singular encoding that should be rejected
or routed to a slower diagnostic path.

## 8. Prior Art in the Tree

- `hardware/rtl/core/spu4/chiral_phinary_adder_param.v` — SPU-4 satellite
  φ-adder, proven in simulation
- `knowledge/NGUYEN_WEIGHT_PARTITIONING.md` — laminar weight partitioning,
  compatible with φ-weighted SOM updates
- SPI southbridge protocol — already handles multi-target routing via 0xA5
  selector fields (selectors 0–7, currently using 1–6)

## 9. References

1. Lucas, E., "Theorie des Fonctions Numeriques Simplement Periodiques," 1878.
2. Fibonacci Quarterly — Lucas prime tables.
3. `knowledge/rplu_formal_spec.md` — M31 arithmetic foundation.
4. SPU-4 chiral phinary adder: `hardware/rtl/core/spu4/chiral_phinary_adder_param.v`
