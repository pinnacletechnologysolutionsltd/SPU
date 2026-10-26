# SPU Glossary — Plain-English Terms & Conversions

This page is the on-ramp: what the words mean, how the numbers convert,
and where the ideas come from. It is deliberately informal. The normative
definitions (exact bit conventions, literature citations, divergence
notes) live in [`knowledge/SPU_LEXICON.md`](knowledge/SPU_LEXICON.md);
hardware status claims are governed by `AGENTS.md` and the
[hardware evidence ledger](hardware_evidence.md). If this page and the
lexicon ever disagree, the lexicon wins.

## The one-sentence version

The SPU is an FPGA coprocessor that does geometry with **exact arithmetic
instead of floating point** — so the same program produces bit-identical
results every run, on every board, from every vendor, forever.

## If you know floating point

Floating point approximates real numbers and accumulates rounding error;
every FP system needs epsilon comparisons, error analysis, and faith.
The SPU takes a different deal: restrict yourself to number systems where
the geometry you care about is *exactly* representable, and rounding error
ceases to exist. The price is that you can't compute arbitrary
transcendentals; the payoff is that equality tests are exact, results
replay bit-for-bit across the Python model, the C++ model, and silicon,
and a checker circuit can verify an algebraic invariant every clock cycle
with a zero test instead of a tolerance. No floating point, no division,
no data-dependent branches in hot paths — those aren't limitations that
were tolerated, they're the design.

## Terms, in plain English

**RationalSurd** — the basic number: `P + Q·√3`, stored as two signed
16-bit integers packed in one 32-bit word. Why √3? Because hexagonal/
tetrahedral geometry keeps producing cos 60° = 1/2 and sin 60° = √3/2, so
the smallest number system closed under that geometry is the rational
numbers extended with √3. Addition, subtraction, and multiplication
(√3·√3 = 3) never leave the system.

**Quadrance** — squared distance, used *instead of* distance. Distance
needs a square root (usually irrational); quadrance never does. Comparing
"which is closer" works identically with quadrance and stays exact.
From Wildberger's rational trigonometry.

**Spread** — the rational-trigonometry replacement for angle: the squared
sine of the angle between two lines, a number from 0 (parallel) to 1
(perpendicular). Rational inputs give rational spreads — no π, no radians,
no trig tables. See the conversion table below.

**Quadray coordinates** — four axes pointing at the vertices of a
tetrahedron, instead of three at right angles. Every displacement is a
4-tuple (A, B, C, D) with A+B+C+D = 0. Redundant? Yes, by one axis — and
that redundancy is the point: the sum is an always-on integrity check
(see Davis Gate). From Kirby Urner's development of Buckminster Fuller's
synergetics; basis matrix by Tom Ace.

**IROTC / conjugate catalog** — the icosahedral extension of ROTC (the
Quadray rotation catalog): the 60 rotations of the icosahedral symmetry
group, exact in `½Z[φ]` rather than plain `Z[φ]`. The "conjugate catalog"
is the Galois-dual table needed alongside the main one because the
icosahedral basis isn't self-conjugate the way the tetrahedral one is.
Verified VM-through-silicon (Tang Primer 25K).

**IVM / Vector Equilibrium** — the isotropic vector matrix is Fuller's
name for the densest packing of spheres (crystallographers say CCP/FCC);
the cuboctahedron ("vector equilibrium") is one sphere and its 12
touching neighbors. Those 12 directions + the center give the 13 axes of
the SPU-13's register manifold.

**Davis Gate / cubic leak / Henosis** — every clock cycle, hardware checks
that the Quadray components sum to zero — exactly, not "within epsilon."
The math guarantees correct execution preserves the sum (all the rotation
matrices have coefficient sum 1), so a nonzero result — a *cubic leak* —
can only mean corruption, overflow, or a bad load. The response is
*Henosis*: a one-cycle soft recovery instead of a hard reset. Think of it
as a parity check that falls out of the geometry instead of being bolted
on.

**Tensegrity guard / force-density** — an admission check for structural
configurations (nodes/edges/struts), same family as the Davis Gate but for
whole structures instead of one register: given cable/strut force-density
ratios, check exact equilibrium and topology (no illegal intersections)
before committing a configuration as valid, and reject or roll back
otherwise. Silicon-proven (`TENSEGRITYLINK`) for bounded admission and
transactional table loading; the active controller that proposes *what*
structural change to try next is still open work.

**Dissonance** — the 8-bit "how broken is it" number a satellite node
reports upward: the leftover deviation *after* local recovery was
attempted. Zero means healthy; the supervisor never sees raw state, only
unrecovered trouble.

**Whisper** — the liveness-plus-sanity beacon: a node periodically says
"I am coherent" over UART; silence means incoherent or dead. Unlike an
ordinary heartbeat, whispering is gated on the node actually passing its
own algebraic checks. Frame format: `docs/WHISPER_V1_SPEC.md`.

**SPU-4 Sentinel / SPU-13 Cortex** — the two cores. Sentinel: a ~400-LUT
four-axis core that fits the smallest FPGAs — edge sensing, satellite
duty. Cortex: the 13-axis manifold engine with the full arithmetic
pipelines. A constellation is many Sentinels reporting dissonance to a
Cortex governor.

**M31 / A₃₁** — M31 is the Mersenne prime 2³¹−1, beloved of hardware
because reduction mod M31 is a shift and an add. A₃₁ is a 4-component
number system over M31 with basis [1, √3, √5, √15], used by the Padé
pipeline. (Fine print: it has rare "norm-zero" elements that can't be
inverted; hardware detects them with a flag rather than pretending
otherwise.)

**Lucas phinary** — exact arithmetic with the golden ratio φ, done in the
ring Z[φ] reduced by a Lucas prime. Supports multiply, inverse, φ-scaling,
and chirality flips. A million-step φ-scaling loop comes back with zero
drift — try that in `double`. ("Phinary" elsewhere usually means base-φ
positional notation; here it means the modular ring. Papers say "Lucas
phinary ring.")

**RPLU / Padé** — the Rational Polynomial Look-Up engine evaluates Padé
approximants (ratios of polynomials — the rational-arithmetic answer to
"I need something function-shaped") over A₃₁, [4/4] degree, table-driven.

**Jet ring / hyper-Catalan / Geode** — machinery for solving polynomial
equations exactly by power series, following Wildberger & Rubine's 2025
paper. A "jet" is a truncated power series the hardware multiplies like a
small convolution; the hyper-Catalan numbers count the series
coefficients; the Geode is a factorization structure inside them. The
repo's oracle reproduces the paper's published tables bit-exactly.

**Piranha pulse / Fibonacci dispatch** — instructions launch at cycles 8,
13, 21 of a repeating 34-cycle frame (consecutive Fibonacci numbers). The
schedule is a fixed counter: fully deterministic, spectrum-friendly
(golden-ratio spacing avoids stacking switching noise on one harmonic),
and algebraically kin to the φ-arithmetic in the datapath.

**Southbridge** — the RP2350 microcontroller that sits between any host
and the FPGA: it owns the SD card, boot, table hydration, and streams
commands over an 8-opcode SPI protocol. If you want to talk to a flashed
SPU from a Pi, a laptop, or a Pico — this is the door.
Protocol: `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`.

**Spin** — a named, reproducible bitstream configuration: a chosen subset
of modules built for a specific board (ROBOTICS, LUCAS, RPLU2PADE, …).
A *probe* is a spin that exists to produce one piece of silicon evidence.
Full catalog with statuses: `docs/SPIN_CATALOG.md`.

**Lithic** — the house discipline: single-purpose modules, typically
50–150 lines; split concerns rather than grow files. Lithic-L is the same
philosophy as a program format (`.lith`).

## Conversion tables

### Angle ↔ spread

Spread s = sin²θ. Note every entry is exact in Q(√3) — that's not a
coincidence, it's why the field was chosen. (Hardware carries scaled
integer representatives; the *values* are exact.)

| Angle θ | Spread s (exact) | Spread s (decimal) |
|---:|---|---:|
| 0° | 0 | 0.0000 |
| 15° | (2−√3)/4 | 0.0670 |
| 30° | 1/4 | 0.2500 |
| 45° | 1/2 | 0.5000 |
| 60° | 3/4 | 0.7500 |
| 75° | (2+√3)/4 | 0.9330 |
| 90° | 1 | 1.0000 |

Two lines at spread s and their complement: s(90°−θ) = 1−s(θ).

### Distance ↔ quadrance

Q = d². A point at conventional distance 5 has quadrance 25. "A is closer
than B" ⇔ Q(A) < Q(B) — order is preserved, so nearest-neighbor logic
(like the SOM classifier's best-matching-unit search) never needs the
square root.

### RationalSurd packing

`P + Q·√3` packs as `{P[15:0], Q[15:0]}` in one 32-bit word:

| Value | (P, Q) | Hex word | ≈ decimal |
|---|---|---|---:|
| 1 (identity) | (1, 0) | `0x0001_0000` | 1.000 |
| √3 | (0, 1) | `0x0000_0001` | 1.732 |
| 2 + √3 | (2, 1) | `0x0002_0001` | 3.732 |
| −1 | (−1, 0) | `0xFFFF_0000` | −1.000 |

(The decimal column is for your intuition only — the machine never
computes it.)

### Q12 fixed point (rotor coefficients)

Real value = raw / 4096. A signed 16-bit Q12 field spans −8.000 to
+7.99976 in steps of 1/4096 ≈ 0.000244. Example: φ ≈ 1.6180 → raw 6627.

### Timing

| Quantity | Value |
|---|---|
| Core clock | 24 MHz |
| Dispatch frame | 34 cycles (Fibonacci: pulses at cycle 8, 13, 21) |
| Frame rate | 24 MHz / 34 ≈ 705.9 kHz |
| Reference-pulse design target | 61.44 kHz (= 60 × 1024) |

Honesty note: 61.44 kHz is a design target for the deterministic I/O
domain; it is not integer-derivable from 24 MHz (nearest divider ÷391
gives 61.381 kHz, −0.09%). Details: `knowledge/CLOCK_ARCHITECTURE.md`.

## Where the ideas come from (reading list)

- **N.J. Wildberger**, *Divine Proportions: Rational Trigonometry to
  Universal Geometry* (Wild Egg, 2005) — quadrance and spread. His
  YouTube channel **Insights into Mathematics** (the *WildTrig* series)
  is the gentlest on-ramp anywhere.
- **N.J. Wildberger & D. Rubine**, *A Hyper-Catalan Series Solution to
  Polynomial Equations, and the Geode*, The American Mathematical
  Monthly (2025) — the series mathematics behind the jet/series units.
- **Kirby Urner** — Quadray coordinates (4dsolutions.net); **Tom Ace** —
  the Quadray basis matrix (minortriad.com).
- **R. Buckminster Fuller**, *Synergetics* (Macmillan, 1975) — the IVM
  and the vector equilibrium.
- **A.R. Thomson**, *Quadray Rotors* (v5, 2026) — the rotor algebra on
  tetrahedral axes the SPU-4 implements.
- **S.L. Arlinghaus** — hexagonal hierarchies and spatial synthesis
  (*Solstice: An Electronic Journal of Geography and Mathematics*) — the
  deployment geometry of the constellation tier.
- **B.R. Davis** — the Davis framework the stability gate is named for
  (see `docs/ATTRIBUTION.md` for the idea-by-idea ledger).
- **Toolchain**: everything builds with the open-source
  [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build)
  (Yosys + nextpnr) — no vendor IDE required.

*CC0 1.0 Universal, like the rest of `docs/`.*
