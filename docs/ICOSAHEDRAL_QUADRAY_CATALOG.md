# The Icosahedral Rotation Group in the Quadray Basis

**Status: machine-checked math only** (exact-Fraction oracle,
`software/tests/test_icosahedral_catalog.py`, 17 checks). No VM opcode, no
RTL, no silicon. Derived and verified 2026-07-10. This document records the
findings that will drive the ISA design; the derivation is kept executable
in the repository so it cannot silently drift (a previous derivation script
was deleted after note-taking and its central claim turned out to be wrong —
see §3).

## 1. Construction

The 60 rotations of the regular icosahedron (group A₅) are derived
constructively, with no literature matrices and no floating point:

- Exact arithmetic in Q(φ): numbers `a + b·φ` with rational `a, b`,
  reduced by `φ² = φ + 1`. Galois conjugation is `φ → 1 − φ`.
- Vertices: the 12 cyclic permutations of `(0, ±1, ±φ)`. This orientation
  is chosen deliberately: its symmetry group shares **exactly** the ROTC
  catalog's A₄ subgroup (coordinate 3-cycles about the `(±1,±1,±1)` axes
  and the 180° coordinate-axis flips — catalog angles 0, 2, 5, 15–23).
- Each rotation is solved from a flag image: vertex `v₁` and adjacent
  vertex `v₂` map to `(w₁, w₂)`, giving
  `R = [w₁ w₂ w₁×w₂]·[v₁ v₂ v₁×v₂]⁻¹`. The 12 × 5 flag images produce all
  60 rotations, so closure to exactly 60 is a checked theorem, not an
  input assumption.

Verified: 60 distinct; all orthogonal, det +1, vertex-set-preserving;
composition-closed; inverse-closed; conjugacy classes 1/15/20/24 by period
{1, 2, 3, 5}; trace spectrum {3¹, (−1)¹⁵, 0²⁰, φ¹², (1−φ)¹²}.

## 2. Relation to the 36-angle ROTC catalog

- The integer-entry subset of A₅ is **exactly** the catalog's A₄
  (angles 0, 2, 5, 15–23). 48 rotations are genuinely new.
- No octahedral angle (24–35) preserves the icosahedron, and no thirds
  circulant is icosahedral. A₅ ∩ S₄ = A₄, as group theory requires.
- New elements per icosahedron: 12 of period 2, 12 of period 3, 24 of
  period 5 (six 5-fold vertex axes × four nontrivial powers).

## 3. Field finding: ½Z[φ], not Z[φ]

**The prior session's claim that the quadray matrices have entries in
Z[φ] proper is false.** Converting each rotation to its quadray BCD 3×3
(`M = E⁻¹RE`, the same embedding verified bit-exact against the RTL for
angles 0–35) gives entries in the 11-value alphabet

```
{ 0, ±1, ±1/2, ±φ/2, ±φ⁻¹/2, ±√5/2 }        (φ⁻¹ = φ−1,  √5 = 2φ−1)
```

The halves survive the change of basis. Every matrix is `M = N/2` with
the numerator `N = 2M` having entries only in

```
{ 0, ±1, ±2, ±φ, ±φ⁻¹, ±√5 }
```

Consequences for the Lucas MAC:

- **No general Z[φ] multiply (PMUL) is needed to apply a rotation.**
  Every numerator entry is a PSCALE/add chain: `×φ` = 1 PSCALE,
  `×φ⁻¹ = φx − x` = PSCALE + SUB, `×√5 = 2φx − x` = PSCALE + ADD + SUB,
  `×2` = ADD. PINV is never needed (inverse = transpose, also in A₅).
- **The entire cost of the icosahedral family is the global /2** — and §4
  shows that cost is dischargeable.

## 4. The /2 is fallible per-step but statically dischargeable
   (opposite of the thirds /3)

On raw integer inputs the /2 truncates in ~3/4 of cases: over
`Z[φ]/2 ≅ F₄`, every new rotation's numerator has **rank 1** — exactly
16 of the 64 residue classes of `F₄³` are division-safe, uniformly across
all 48 rotations. So a naive implementation would need a per-step
divisibility guard, exactly like the thirds `/3`.

**Doubling theorem.** Because A₅ is a *finite, composition-closed* group
with uniform denominator 2, the identity `N_a·N_b = 2·N_{ab}` holds for
all pairs (both sides equal `4·M_aM_b`, and `M_aM_b` is again a group
element of the form `N_{ab}/2`). By induction, if the input register is
doubled **once at load time**, every pre-division sum in every A₅ chain
is even and every step is exact — even though intermediate vectors may be
odd. Machine-checked: 300 random 10-step chains over the full 60-element
group under hardware division semantics, zero faults, zero value
mismatches; control runs with undoubled loads fault at the expected rate.

This is the precise opposite of the thirds situation. The ROTC paper §5
records the global-rescale idea as a dead end for `/3` because the thirds
catalog is **not** composition-closed — chains escape the catalog and
denominators escalate as 3^k. A₅ is closed, so the denominator never
exceeds 2 and one rescale discharges the precondition forever.

**Caveat:** the discharge holds for *pure A₅ chains*. Mixing icosahedral
rotations with thirds circulants re-opens the escalation problem (the
mixed set generates an infinite group). In harness terms: the doubled
state is CLEAN under A₅ transitions and must drop to PENDING when a
thirds transition fires.

## 5. Galois conjugation and the second icosahedron (PCHIRAL bridge)

`φ → 1 − φ` maps all 48 new rotations *out* of this A₅ — onto the
rotation group of the dual-orientation icosahedron (the other Q(φ)
icosahedron on the same A₄ skeleton). The two A₅s share exactly A₄.
Since the Lucas MAC's PCHIRAL implements exactly this conjugation, the
second catalog of 48 comes for free: conjugate, rotate, conjugate back —
or equivalently run the same micro-programs with conjugated constants.

Total exact rotation inventory this makes reachable:
36 (current catalog) + 48 (A₅) + 48 (conjugate A₅) = **132 catalog
entries** — as a set of distinct rotations: |S₄ ∪ A₅ ∪ A₅′| = 120, plus
the 12 thirds rotors (order 6, not in any polyhedral group).

## 6. Hardware implications (design input, not design)

- An icosahedral rotation is a short Lucas MAC micro-program, not a
  single-cycle combinatorial pattern: per output component, a PSCALE/ADD
  chain over the three inputs, then a shared `>>1`. The doubling theorem
  means the `>>1` needs **no divisibility check inside an A₅ chain** —
  only the load path needs conditioning.
- Preferred conditioning shape (decided in discussion 2026-07-10):
  `LOAD2X` = shifted load (one wire) **plus a per-register DOUBLED tag**;
  the tag, not the shift, is what licenses the unguarded `>>1`. IROTC
  guards on the tag once at dispatch — same pattern/cost as the bad-angle
  gate, zero logic in the micro-program hot path, and an IROTC against an
  untagged register faults with the manifold untouched (poison-proof
  obligation carries over). Tag algebra, all verified by the oracle:
  set by `LOAD2X`/`SCALE2`; preserved by A₅ IROTC (doubling theorem),
  ADD/SUB of two tagged operands (linearity), and PCHIRAL (so the
  conjugate icosahedron runs under the same tag); cleared — the
  DOUBLED→PENDING harness transition — by thirds ROTC, mixed tagged/
  untagged ADD, or a raw LOAD. The Davis gate is scale-invariant and
  needs no changes; half-unit readback is the same convention family as
  the existing Q12 fixed-point scaling.
- Register format: components must carry Z[φ] pairs — the Lucas MAC's
  native operand format, not the Q(√3) `RationalSurd` packing. The
  opcode question is settled — and in fact forced: ROTC's angle field is
  6 bits and 36 + 48 > 64, so the family cannot extend the ROTC angle
  space. The dedicated opcode is specified in `docs/IROTC_SPEC.md`
  (IROTC/LOAD2X/SCALE2, canonical 0-59 index space pinned by checksum,
  conjugate-catalog flag, DOUBLED tag algebra, fault codes,
  verification plan).
- The state-machine harness (`docs/STATE_MACHINE_HARNESS.md`) gets a new
  state rather than a new guard: DOUBLED (CLEAN for all A₅ transitions;
  thirds transitions exit it).

## 7. Open items

- Axis/angle naming for the 48 (vertex/edge/face axes), catalog
  numbering, and the inverse table (inverse = transpose; pairing is
  period-driven: 72°↔288°, 144°↔216°, order-2/3 as usual).
- Exactness theorem in closed form (the rank-1-mod-2 structure of the
  numerators; why 16/64 uniformly).
- VM implementation + oracle trace test, then RTL micro-program design.
- Whether the doubled convention should be global (all quadray state
  carried ×2) or scoped to icosahedral programs.
