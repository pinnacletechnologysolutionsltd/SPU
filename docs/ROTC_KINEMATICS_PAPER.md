# Error as Fault, Not Drift: An Exact Rational Rotation ISA for Tetrahedral Kinematics

**Draft v0.1 — 2026-07-10**

John Curley
Pinnacle Technology Solutions Ltd.

*Draft status: v0.1 markdown, pre-TeX. Every claim in §10 is cross-referenced
against `docs/hardware_evidence.md`; do not add silicon claims without a
matching evidence entry.*

---

## Abstract

Classical kinematics chains accumulate floating-point rounding error
silently: composition turns approximation into drift, and no downstream
test can distinguish a drifted pose from a commanded one. We present ROTC,
a rotation instruction for a rational-arithmetic FPGA coprocessor (SPU-13)
that takes the opposite contract: **every rotation is either exact or
faults**. The instruction operates on Quadray (tetrahedral, 4-axis)
coordinates over the field Q(√3) with no floating point, no division, and
no transcendental approximation in the datapath. Its angle catalog is a
set of 24 exact rational rotations — verified, in exact
rational arithmetic, to have determinant +1, documented periods and
inverses, and to preserve the zero-sum invariant that the coprocessor's
stability gate (the Davis Gate) checks every cycle as an exact zero test.

The catalog's thirds operators divide by 3, and we prove this division is
exact on the zero-sum hyperplane **iff the rotation's invariant axis is
≡ 0 (mod 3)** — a precondition that is *not* preserved under composition,
so no static check can discharge it. Following a reframing due to Gene
Yanenko, we resolve this by treating ROTC not as a fixed-function
instruction but as a **state-machine harness**: register values carry an
explicit exactness state (CLEAN / PENDING / FAULT), rotations are guarded
transitions, and division is deferred to explicit reduction points where
inexactness is detected and reported rather than truncated. We describe
the hardware implementation (a time-division-multiplexed rotor core with
a shared surd multiplier, axis permuters, and a decode-level gate that
provably never writes the register file on an unverified angle), the
verification methodology (independent exact-fraction oracle, bit-exact
VM-vs-RTL trace equivalence across both datapaths, poison-value fault
proofs), and the application to forward/inverse kinematic chains that
close exactly — bit-for-bit — rather than approximately.

---

## 1. Introduction

A six-joint robot arm commanded through a round trip — six rotations out,
six inverse rotations back — should return to its starting pose. In IEEE-754
arithmetic it returns to a pose *near* the start, with an error that grows
with chain length, varies with rotation order, and is invisible to the
program: the drifted value is a well-formed float like any other. Industrial
practice compensates with periodic re-normalization, redundant sensing, and
tolerance windows, all of which convert a correctness question into a tuning
question.

This paper describes a rotation primitive built on the opposite contract.
The SPU-13 coprocessor performs all arithmetic exactly in the ring of
rational surds `P + Q√3` (packed integer pairs), with hard architectural
constraints: no floating point anywhere in the datapath, no division, no
transcendental approximation, no branches in hot paths. Under this regime a
rotation cannot be *approximately* right. It is either exactly right, or the
hardware raises a fault flag and refuses to commit a result. Composition
therefore cannot drift: a six-step closure either returns the bit-identical
starting vector — which we demonstrate on FPGA silicon — or faults at the
step where exactness was lost.

The interesting engineering content is in what "or faults" requires. Exact
rotation catalogs over the rationals necessarily include operators with
denominators (§3); ours divide by 3. We prove exactly when that division is
exact (§5), show the precondition cannot be maintained statically across
composed rotations, and adopt the resolution proposed by Evgeny Yanenko:
promote the instruction into a state-machine harness in which exactness is
tracked, deferred, and checked, rather than assumed (§6). The result is a
rotation ISA whose failure mode is a diagnosable fault code instead of a
silently wrong manifold.

Contributions:

1. A corrected, closed catalog of 24 exact rational rotations in
   Quadray coordinates, with machine-verified group structure (§3–4).
2. An exactness theorem for the catalog's thirds operators on the zero-sum
   hyperplane, with a reproducible counterexample and a proof sketch that
   the precondition is not composition-safe (§5).
3. The state-machine harness (CLEAN/PENDING/FAULT with ROTATE/ALIGN/REDUCE
   transitions) that makes deferred exact reduction an ISA-visible
   contract, including two proven guaranteed-safe reduction points (§6).
4. A division-free hardware implementation and a verification methodology
   in which an exact-fraction oracle, a Python VM, and the RTL are held
   bit-identical, and fault paths are proven by poison-value survival, not
   absence of crashes (§7–8).
5. An application of the catalog to forward/inverse kinematic chains with
   exact closure (§9).

## 2. Background and Related Work

**Quadray coordinates.** The SPU-13 represents spatial state on four
tetrahedral axes (A, B, C, D) rather than three orthogonal ones, following
Fuller's synergetics [1] and the Quadray literature developed by Urner and
others [2]. Where Urner's canonical form normalizes to non-negative
components with min = 0, the SPU works with signed components on the
**zero-sum hyperplane** ΣA+B+C+D = 0; this is the representation the
hardware's stability check (the Davis Gate) enforces cycle-by-cycle as an
exact integer zero test, not an epsilon comparison.

**Rational trigonometry.** Wildberger [3] showed that Euclidean geometry
can be developed with quadrance and spread in place of distance and angle,
eliminating transcendental functions and keeping every quantity in the
base field. ROTC is this program executed in silicon: "rotate by 60°"
never appears; what exists is an integer circulant with period 6.

**Spread-Quadray Rotors.** Thomson's SQR [4] develops a rotor algebra
native to the ABCD basis (half-angle Hamilton products; the K³ = −K cubic
identity is due to Murillo [5]; the D-up convention to Pohl). SQR is
specified over f64 and does not fix a field or a fixed-point
representation. The present work is complementary: a different machine —
integer circulants under a permutation conjugation, over an explicit
field, division-free — for the discrete rotation set a lattice-native
kinematics ISA needs, with hardware exactness semantics as the point of
divergence. The surd-field approach was shared with Thomson in early 2026;
his Synergetics Cookbook's future-work section independently proposes a
different field (Q(√2,√3)) for a different domain (exact convex hulls in
rendering) [6].

**State-machine framing.** The reframing of ROTC from a fixed-function
rotation instruction into a state-machine harness — exactness state
carried by the data, rotations as guarded transitions, reduction as an
explicit fallible operation — is due to Evgeny Yanenko. §6 is the
formalization of that idea; the same "detect, never silently corrupt"
idiom appears elsewhere in the SPU (the A₃₁ inverter's zero-norm flag,
saturating telemetry fields), but Yanenko's framing is what turned a
numeric caveat into an ISA contract.

## 3. The ROTC Catalog

ROTC (opcode 0x1C) applies one of a catalog of linear operators to a
Quadray register: `ROTC QRd, QRs, θ` with a 6-bit angle selector θ. Each
catalog entry is a circulant on three of the four components with the
fourth held invariant, specified by coefficients (F, G, H):

```
B' = (F·B + H·C + G·D) / denom
C' = (G·B + F·C + H·D) / denom
D' = (H·B + G·C + F·D) / denom      denom ∈ {1, 3}
```

Angles 0–5 act directly (A invariant). Angles 6–14 conjugate the same
three thirds coefficient sets by an axis permutation — the target
invariant axis is rotated into the circulant's A slot, the circulant is
applied, and the permutation is inverted — so the invariant axis becomes
B (6–7, 12), C (8–9, 13), or D (10–11, 14). Unlike 0–5, these rewrite all
four components of the destination register. Angles 12–14 (Tranche 1,
2026-07-10) supply the previously missing inverses of 9 and 10, making the
thirds catalog inverse-closed.

Angles 15–23 (Tranche 2) complete the A₄ even-permutation subgroup: 6
additional permuted 3-cycles via the bypass_p5/bypass_p5_inv hardware paths,
and 3 double-transpositions via dedicated bypass signals. All are pure
coordinate permutations with zero multiplications.

Angles 24–35 (Tranche 3, octahedral group, 2026-07-10) are the remaining 12
elements of S₄ — the full cube/octahedron rotation group. These are integer
3×3 matrices on (B,C,D) with entries 0 or ±1, implemented as 12 hardwired
combinatorial patterns (zero multiplies, zero DSPs, zero TDM cycles). They
recompute A from the zero-sum constraint rather than passing A through, so
self-inverse closure requires A+B+C+D=0 on input. The legacy claim that cube
rotations "require Q(√2)" is wrong: the √2 belongs to the cube's metric
quantities, not its rotation group.

The full catalog: 36 inverse-closed rotations — the identity, 12 thirds
circulants (1, 3, 4, 6–14), 11 non-identity A₄ permutations (2, 5, 15–23;
together with the identity these form the 12-element A₄), and 12
octahedral integer matrices (24–35).

| θ | Name | Invariant | F | G | H | Period | Inverse |
|---:|---|---|---:|---:|---:|---:|---:|
| 0 | identity | — | 1 | 0 | 0 | 1 | 0 |
| 1 | thirds period-6 | A | 2/3 | 2/3 | −1/3 | 6 | 4 |
| 2 | P5 forward cycle | A | 0 | 1 | 0 | 3 | 5 |
| 3 | thirds period-2 | A | −1/3 | 2/3 | 2/3 | 2 | 3 |
| 4 | thirds period-6 inverse | A | 2/3 | −1/3 | 2/3 | 6 | 1 |
| 5 | P5 inverse cycle | A | 0 | 0 | 1 | 3 | 2 |
| 6 | conj. of 4 about B | B | 2/3 | −1/3 | 2/3 | 6 | 7 |
| 7 | conj. of 1 about B | B | 2/3 | 2/3 | −1/3 | 6 | 6 |
| 8 | conj. of 3 about C | C | −1/3 | 2/3 | 2/3 | 2 | 8 |
| 9 | conj. of 1 about C | C | 2/3 | 2/3 | −1/3 | 6 | 13 |
| 10 | conj. of 4 about D | D | 2/3 | −1/3 | 2/3 | 6 | 14 |
| 11 | conj. of 3 about D | D | −1/3 | 2/3 | 2/3 | 2 | 11 |
| 12 | 180° about B | B | −1/3 | 2/3 | 2/3 | 2 | 12 |
| 13 | 240° about C | C | 2/3 | −1/3 | 2/3 | 6 | 9 |
| 14 | 60° about D | D | 2/3 | 2/3 | −1/3 | 6 | 10 |
| 15 | P5 fwd about B | B | — | — | — | 3 | 16 |
| 16 | P5 inv about B | B | — | — | — | 3 | 15 |
| 17 | P5 fwd about C | C | — | — | — | 3 | 18 |
| 18 | P5 inv about C | C | — | — | — | 3 | 17 |
| 19 | P5 fwd about D | D | — | — | — | 3 | 20 |
| 20 | P5 inv about D | D | — | — | — | 3 | 19 |
| 21 | (AB)(CD) | — | — | — | — | 2 | 21 |
| 22 | (AC)(BD) | — | — | — | — | 2 | 22 |
| 23 | (AD)(BC) | — | — | — | — | 2 | 23 |
| 24 | 180° edge (CD) | — | — | — | — | 2 | 24 |
| 25 | 180° edge (AB) | — | — | — | — | 2 | 25 |
| 26 | 90° face (x) | — | — | — | — | 4 | 27 |
| 27 | 270° face (x) | — | — | — | — | 4 | 26 |
| 28 | 180° edge (BC) | — | — | — | — | 2 | 28 |
| 29 | 90° face (z) | — | — | — | — | 4 | 30 |
| 30 | 270° face (z) | — | — | — | — | 4 | 29 |
| 31 | 180° edge (AD) | — | — | — | — | 2 | 31 |
| 32 | 180° edge (BD) | — | — | — | — | 2 | 32 |
| 33 | 270° face (y) | — | — | — | — | 4 | 35 |
| 34 | 180° edge (AC) | — | — | — | — | 2 | 34 |
| 35 | 90° face (y) | — | — | — | — | 4 | 33 |

Octahedral naming (24–35): each 180° edge rotation is central negation
composed with a single transposition of the cube's body diagonals — the
label names the swapped diagonal pair. The face-axis labels are shared
with the double transpositions of Tranche 2: squaring either member of a
90°/270° face pair lands exactly on the corresponding double
transposition (26² = 27² = 21, 29² = 30² = 23, 33² = 35² = 22, verified
in exact arithmetic).

The legacy catalog this table
replaces had three defects worth recording, because they motivate the
verification discipline of §8: one angle was documented with thirds
coefficients while the hardware bypassed it as a permutation; one was
singular (det = 0); one silently duplicated another. All three shipped in
documentation for months because nothing machine-checked the table.

## 4. Verified Group Structure

All 36 operators were verified in exact rational arithmetic
(arbitrary-precision `Fraction`, independent of both the VM and the RTL):

- **Determinant +1** for all 36 (proper rotations on the zero-sum
  hyperplane; the octahedral 12 additionally swap the two inscribed
  tetrahedra, confirming they are exactly the S₄ \ A₄ coset).
- **Zero-sum preservation**: for angles 0–23 every column of the operator
  sums to 1, so ΣABCD is invariant. Angles 24–35 instead *recompute*
  A = −(B+C+D): they agree with the corresponding cube rotation on the
  ΣABCD = 0 hyperplane and force zero-sum output, which is why their
  closure properties require zero-sum input.
- **Periods** as tabled: one identity, thirteen involutions
  (3, 8, 11, 12, 21–23, and the six octahedral edge rotations
  24/25/28/31/32/34), eight period-3 permutations (2, 5, 15–20), six
  period-4 face rotations (26/27, 29/30, 33/35), and eight period-6
  thirds rotors (1, 4, 6, 7, 9, 10, 13, 14). All 36 matrices pairwise
  distinct (the legacy duplicate defect cannot recur unnoticed).
- **Inverse closure**: every angle's inverse is a single catalog angle —
  1↔4, 2↔5, 6↔7, 9↔13, 10↔14, 15↔16, 17↔18, 19↔20, 26↔27, 29↔30, 33↔35
  are mutual pairs; the remaining fourteen are involutions (or the
  identity). Historically, angles 9 and 10 had no single-angle inverse in
  the 0–11 catalog (each was inverted only by its own 5th power) — a real
  ISA cost for inverse kinematics (§9) that motivated Tranche 1.
- **Subgroup structure**: the 12 pure permutations (0, 2, 5, 15–23) form
  A₄; adding the octahedral 12 closes to the full 24-element cube
  rotation group S₄, verified by exhaustive composition.

The thirds operators have period 6 and are therefore *not* automorphisms
of the integer Quadray lattice (the face-centered-cubic point group
contains no order-6 proper rotation); they are exact rational rotations of
the zero-sum hyperplane that act integrally only on a sublattice. §5 makes
that sublattice precise — and the exactness machinery of §6 is what makes
it safe to say so in hardware.

## 5. Exactness of the Thirds Operators

The nine thirds entries divide by 3. In hardware the division is a
magic-constant multiply (`n · 0x55555556`, upper word, sign-corrected) —
division-free, but a *floor* operation: if the circulant sum is not a
multiple of 3, it silently truncates.

**Theorem (exactness condition).** On the zero-sum hyperplane
(A+B+C+D = 0), a thirds rotation with invariant axis X is exact iff
X ≡ 0 (mod 3).

*Proof sketch (invariant axis A, angle 1).* Substituting C = −(A+B+D)
into the circulant sum 2B − C + 2D gives A + 3B + 3D ≡ A (mod 3); the
same substitution works for each row and each thirds coefficient set. The
sums are all ≡ the invariant axis mod 3, independent of the rotating
components. ∎

**Counterexample (empirical).** A=1, B=1, C=1, D=−3 is a genuine zero-sum
vector with A ≢ 0 (mod 3). In the Q12-scaled datapath the pre-division
sum is −20480, not a multiple of 3; floor division returns −6827 against
a true value of −6826.6̄ — a silent, permanently unflagged error in the
naive implementation. This class of input is fully reachable: the load
instruction accepts any signed immediate on any axis.

**The precondition does not compose.** One might hope to discharge
X ≡ 0 (mod 3) statically, at assembly time. This fails: the condition is
not preserved by the rotations themselves. Even the stronger invariant
"all four components ≡ 0 (mod 3)" is destroyed by a single rotation
(verified directly: (3, 3, 3, −9) rotates to a component of −5). Any
chain that switches invariant axes can therefore leave a
previously-safe axis in a bad residue class, and no toolchain check on
the initial state covers general kinematics.

**A documented dead end.** A fixed global rescaling of the representation
(carry every value as 3× its true value, hoping the /3 cancels
structurally) does not work: applying integer coefficients to an
already-scaled input produces a 9×-scaled output — a fixed rescaling
cannot absorb a multiplicative-per-application effect. We record this
because it was proposed, oracle-tested, and retracted within one day; the
negative result is kept executable in the repository so it cannot be
silently re-proposed.

## 6. The State-Machine Harness

The resolution — due, in framing, to Evgeny Yanenko — is to stop treating
ROTC as a pure function and start treating it as a harnessed state
machine: the *data* carries its exactness state, the *instruction* is a
guarded transition, and division is an explicit, fallible operation
rather than an implicit step.

Each surd lane of each axis carries a deferred-reduction tag:

```
(value: signed integer, exponent: e ≥ 0)     true_value = value / 3^e
```

**States.** CLEAN (e = 0: the register *is* the true value); PENDING
(e > 0: reduction deferred, value is 3^e × true value);
FAULT.MISALIGNED, FAULT.OVERFLOW, FAULT.INEXACT.

**Transitions.**

- **ROTATE(θ)** applies the *integer* coefficients directly — zero
  division — and increments the exponent. Guards: operands must share an
  exponent (else MISALIGNED); the incremented exponent must not exceed
  MAX_EXPONENT (else OVERFLOW; the bound is set by value-magnitude
  growth, roughly 3–5× per unreduced step, before the exponent field
  width binds).
- **ALIGN(X, e')** raises an exponent by multiplying: always exact,
  never faults — multiplication loses no information. It refuses to
  lower an exponent; that is REDUCE's job, and REDUCE can legitimately
  fail.
- **REDUCE(X)** checks `value ≡ 0 (mod 3^e)` and divides exactly on
  success; on failure it raises FAULT.INEXACT **and commits nothing**.

The essential point of the framing: **FAULT.INEXACT is not an error in
the machine — it is correct information about the geometry.** A rotated
point that is not currently an integer lattice point *should not* be
representable as one; the harness reports that fact instead of
manufacturing a nearby integer. Two reduction points are proven safe:

1. **Full-period closure.** After a complete period (e.g. angle 1 applied
   six times), the state returns to the original integer point and REDUCE
   succeeds by construction — the same closure property demonstrated on
   silicon.
2. **Single-axis chains with the §5 precondition.** If the invariant axis
   satisfies ≡ 0 (mod 3) at the start and the chain never switches axes,
   REDUCE succeeds after every step. The classical precondition is
   recovered as a special case of the harness, not the general rule.

Everywhere else, an honest fault is the correct answer, and the
scheduling of REDUCE becomes a compiler/programmer decision with explicit
semantics — exactly the shape of contract an ISA can promise and a
verification suite can enforce.

## 7. Hardware Implementation

**Rotor core.** The circulant executes on a time-division-multiplexed
rotor core sharing a single surd multiplier (9 multiplies scheduled over
an 11-cycle pipeline; DSP usage reduced from 36 to 4), with a
scalar-fast path for the catalog's small integer coefficients
{−1, 0, 1, 2} and hardwired per-angle sum networks. Division by 3 is the
magic-constant construction of §5 — the datapath contains no divider.

**Permuters.** Angles 6–11 wrap the rotor in a pair of combinational
4-way permuters (~16 LUTs each) that move the target invariant axis into
the circulant's fixed slot and back. The permutation is wiring, not
arithmetic: conjugation costs zero additional multiplies and zero
additional error surface.

**Angle gate.** A decode-level bound (`ROTC_MAX_VERIFIED_ANGLE`) refuses
any angle beyond the verified catalog before the rotor launches: no
register-file write occurs, and a sticky fault bit is raised in the
debug/status register. The bound is raised only when a new angle clears
the full verification bar of §8 — the gate encodes the project's claim
discipline in hardware.

**Tagged core.** The state-machine harness of §6 is implemented as a
separate exponent-tagged rotor core (314 lines) with the powers-of-3
table, exponent alignment, and the faulting exact-reduce; its REDUCE is
division-free via the same magic-constant technique generalized across
runtime exponents. It passes an 8-case acceptance testbench that includes
a regression for a real bug found during hardening (§8).

## 8. Verification Methodology

The methodology is oracle-first, three layers deep, and treats fault
paths as first-class proof obligations:

1. **Exact-fraction oracle.** Group structure (§4) and every expected
   rotation result are computed in arbitrary-precision rational
   arithmetic with no fixed-point scaling — independent of both the VM
   and the RTL, so agreement between the latter two cannot mask a shared
   error. This mattered: VM-vs-RTL equivalence *held* throughout the §5
   truncation era, because both sides implemented the same floor
   division. Equivalence proves consistency, not correctness; only the
   third, independent layer distinguishes them.
2. **Bit-exact trace equivalence.** All 36 angles are driven through
   the RTL — through the real permuter module, against *both* rotor
   datapaths (the coefficient-driven scalar path and the hardwired
   per-angle path the integrated core uses) for angles 0–23, and against
   the hardwired path for the octahedral 24–35 (the scalar F/G/H path
   cannot express a non-circulant matrix) — and compared bit-for-bit
   against the VM (336 checks). Thirds-exactness is required for
   equivalence (the VM rounds where the RTL floors), so equivalence
   vectors are chosen with all components ≡ 0 (mod 3); this restriction
   is itself a documented consequence of §5, not a convenience.
3. **Poison-value fault proofs.** The angle gate is proven by loading
   known poison values into the destination register, issuing an
   out-of-catalog angle, and asserting the poison survives bit-identically
   with the fault flag raised — on both the RTL and the VM. "It didn't
   crash" is not accepted as evidence that the manifold was untouched.

**Case study.** During synthesis-hardening of the tagged core's REDUCE, a
value was loaded with zero-extension instead of sign-extension. Every
negative lane value — routine in this representation — either missed an
exact reduction or false-faulted INEXACT. The one pre-existing
negative-value test happened to use a value whose zero-extended residue
was also nonzero mod 3, masking the bug. The Python oracle, which uses
native arbitrary-precision integers and has no extension step, disagreed
with the RTL on `−9` at exponent 1 (RTL: false INEXACT; oracle: reduces
to `−3`); the divergence located the bug, and the case is now a permanent
regression test. The episode is the methodology's argument in miniature:
the oracle must be *structurally* different from the implementation, or
it verifies nothing.

## 9. Application: Exact Kinematic Chains

The catalog's design target is rational robotics: forward kinematics as a
chain of circulant joint applications, inverse kinematics as the reversed
chain of catalog inverses, and closure — FK followed by IK — required to
be *exactly* zero, as a vector identity, not a norm below tolerance. The
software oracle implements circulant joints, forward/inverse chains, and
closure checks (56 automated checks), with hyperbolic scaling available
through a separate Pell rotor instruction (powers of the fundamental unit
2+√3, exact in Q(√3)).

Two properties matter for the robotics use case specifically:

- **Closure is bit-exact.** A commanded round trip returns the identical
  register contents, which the six-step silicon demonstration verifies on
  hardware. There is no re-normalization step anywhere because there is
  nothing to re-normalize.
- **Inverse availability is a catalog property.** Undoing an angle-9
  rotation currently costs five rotor launches (§4). For IK this is the
  difference between one instruction and five — the catalog completion of
  §11 exists because inverse kinematics makes inverse-closure a
  first-order ISA requirement, not an aesthetic one.

## 10. Silicon Status and Claim Discipline

This section states exactly what is proven where; the distinctions are
load-bearing.

| Claim | Evidence | Status |
|---|---|---|
| Angles 0–5, exact rotation + six-step closure | Tang Primer 25K probe, self-check line `ROTC:P A:5 E:00`; testbenches | **Silicon** |
| Angles 6–35, exact rotation incl. permutation conjugation, bypass permutations, and octahedral integer matrices | 336-check bit-exact VM/RTL trace (both datapaths for 6–23, hardwired path for 24–35); core-level opcode testbench incl. inverse round trips 6↔7, 9↔13, 10↔14, 15↔16, 33↔35 and 12/24 self-inverse closure | Simulation (probe queued) |
| Angle gate: unverified angle leaves manifold untouched | Poison-value proofs, RTL + VM | Simulation |
| Group structure (§4) | Exact-fraction verification | Machine-checked math |
| Exactness theorem + counterexample (§5) | Derivation + executable counterexample | Machine-checked math |
| Tagged core (state-machine harness) | 8-case acceptance TB incl. sign-extension regression | Simulation (probe exists, board run pending) |
| Thirds rotations "are exact" | — | **Only conditionally true** — see §5; stated unconditionally nowhere in this paper, deliberately |

## 11. Future Work

- **State-machine harness across the stack.** The CLEAN/PENDING/FAULT
  discipline proved itself on ROTC. Evgeny Yanenko's "Evolving Categories"
  (2004) provides the categorical foundation for extending the same harness
  to every SPU subsystem: SOM/BMU convergence, BTU collision arbitration,
  Padé singular-absorber engagement, Lucas MAC overflow, and batch-inverter
  zero-divisor isolation. A plan document (`docs/STATE_MACHINE_HARNESS.md`)
  defines the state machines, invariants, and verification methodology for
  each. The ROTC tagged core (8/8 acceptance tests) is the reference
  implementation. The Lucas MAC (6 states, ~200 LUTs) is the recommended
  Phase 2 target: smallest state space, existing 1M-step zero-drift oracle,
  and a natural bridge to the icosahedral work below.

- **Octahedral tranche (verified 2026-07-10).** The legacy angle map
  claimed cube/octahedron rotations "require Q(√2)". This is wrong: all 12
  octahedral rotations are integer 3×3 matrices (entries 0,±1) in the
  quadray basis — zero multiplies, zero surds. The √2 belongs to the cube's
  metric quantities, not its rotation group. Angles 24-35 were wired into
  the RTL as 12 hardwired combinatorial patterns (zero DSPs, zero TDM
  cycles) and cross-verified via 336-check trace equivalence + core-level
  opcode TB including inverse-pair and self-inverse closure on zero-sum
  vectors. A notable finding: because octahedral rotations recompute A from
  the zero-sum constraint rather than passing A through (as the thirds
  circulant does), self-inverse closure only holds when the input satisfies
  A+B+C+D=0 — the first rotation angles in the catalog with this constraint.

- **Icosahedral family via the Lucas MAC.** By the crystallographic
  restriction, 5-fold operators can never preserve the IVM lattice; an
  exact icosahedral catalog would act on a golden-ratio module over Q(√5).
  This connects the rotation ISA to the coprocessor's existing Z[φ]
  arithmetic unit (`spu13_lucas_mac.v`). With the Lucas MAC state machine
  in place (Phase 2 of the harness), icosahedral rotations inherit the same
  CLEAN/PENDING/FAULT discipline: PSCALE/PCHIRAL/PMUL/PINV each carry
  exactness preconditions, and OVERFLOW is a terminal state. Deriving the
  rotation matrices themselves is research, not engineering — the φ-module
  representation of the icosahedral group is a genuine open derivation.

- **Silicon runs.** Board runs for the tagged ROTC core probe and the full
  36-angle catalog (0-35) on Artix-7; the ROTC TDM core with angles 0-5
  is silicon-verified on Artix-7, and the tagged-core, extended-angle, and
  octahedral bitstream paths build clean in simulation.

## Acknowledgments

Evgeny Yanenko proposed the state-machine-harness framing of ROTC that §6
formalizes. Andy Ross Thomson's Spread-Quadray Rotors and Synergetics
Cookbook shaped the rotor-algebra context, and correspondence with him on
surd fields (early 2026) is reflected in §2; Leo Murillo's K³ = −K
identity and Pohl's D-up convention enter via that line of work. The
Quadray coordinate tradition follows Fuller and Urner; the rational-
trigonometry foundation is Wildberger's.

## References

[1] R. Buckminster Fuller, *Synergetics: Explorations in the Geometry of
Thinking*, Macmillan, 1975 (with E.J. Applewhite).

[2] K. Urner, Quadray coordinate writings and implementations,
1990s–present.

[3] N.J. Wildberger, *Divine Proportions: Rational Trigonometry to
Universal Geometry*, Wild Egg Books, 2005.

[4] A.R. Thomson, *Spread-Quadray Rotors: A Rational, Tetrahedral-Native
Rotor Algebra*, v5, May 2026.

[5] L. Murillo, K³ = −K cubic identity, Zenodo record 19689050, 2026.

[6] A.R. Thomson, *Synergetics Cookbook*, May 2026, §11.6.

[7] SPU-13 repository: RTL, oracles, testbenches, and the executable
counterexamples and negative results cited in §5
(`docs/ROTC_THIRDS_EXACTNESS_FIX.md`, `docs/ROTC_EXPONENT_STATE_MACHINE.md`,
`software/lib/rotc_thirds_native.py`).
