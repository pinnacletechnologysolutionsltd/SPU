# ROTC Thirds-Angle Exactness — Root Cause and Fix Proposal

Research note, 2026-07-08. Companion to the finding in
`knowledge/SPU_LEXICON.md` (Davis Gate entry, "/3 divisibility"). That
entry establishes the bug is real and reproducible; this document works
through the fix space and recommends one.

## 1. Root cause, precisely

Thirds-angle ROTC (angles 1, 3, 4) applies an integer circulant
`B' = 2B − C + 2D` (etc., coefficients permuted per angle) then divides
by 3 via `div3` — a magic-constant algorithm computing **true floor
division**, silently, with no remainder check. On the zero-sum invariant,
exactness requires the rotation's invariant axis A ≡ 0 (mod 3) — proven
in the lexicon entry, confirmed with a live counterexample.

**New result (this note):** that precondition is *not* self-sustaining
under axis composition. Verified by direct computation:

- If A ≡ 0 (mod 3) and a rotation is applied about that same fixed axis
  repeatedly, A never changes (it's a passthrough), so the precondition
  holds forever for that axis — checked through 3 consecutive rotations.
- But the *stronger* candidate invariant "all four components ≡ 0 (mod 3)"
  is **not preserved** by the rotation: starting from
  A=3,B=3,C=3,D=−9 (all multiples of 3), the rotated B comes out to −5,
  not a multiple of 3.

Consequence: a precondition check on the *current* invariant axis is
sufficient for a chain of rotations about *one* fixed axis, but is not
composition-safe — the moment a program rotates about a second axis
(one of the previously-circulating B/C/D components), that axis's
residue has to be re-established from scratch, and nothing in the
representation guarantees it will be.

## 2. Fix candidates

### (a) Detection only — an exactness flag
Expose the `div3` remainder (already computed as a byproduct of the
magic-constant algorithm) as a status bit, the same architectural pattern
as A₃₁'s FLAGS.V for non-invertible elements. Cheap, purely additive, no
regression risk to anything currently silicon-proven.
**Does not fix the rotation** — a program that hits this still gets a
wrong answer, just a flagged one. Worth having regardless of what else
is chosen, since it costs almost nothing and catches every case,
including future opcodes and hand-written test vectors the toolchain
never sees.

### (b) Toolchain-level precondition enforcement
Assembler statically ensures the invariant axis is ≡ 0 (mod 3) before
emitting a thirds-angle ROTC. Cheap, no RTL/representation change.
**Only safe for single-axis rotation chains** per §1 — the moment a
program composes rotations about different axes (which rational
robotics kinematics chains do routinely — see `fk_chain` in
`rational_robotics.py`), the precondition must be re-derived at every
axis switch, which means the assembler would need to track residues
through arbitrary data flow, including runtime-computed values it can't
see statically (QSUB results, prior rotation outputs). Not a complete
fix by itself.

### (c) RETRACTED 2026-07-08 — "thirds-native global unit" does not work

This section originally proposed redefining the internal Quadray unit to
be 1/3 of the classical IVM step (every raw integer implicitly 3× true
value), claiming the `/3` would cancel structurally. **This is
mathematically wrong, and building the oracle to verify it (per house
convention — contract, then oracle, then RTL) caught the error before
any RTL or silicon claim was touched.**

The error: applying the integer coefficients (2, 2, −1) directly to an
already-trebled input does not reproduce a trebled output — it produces
a **9×**-scaled output, not 3×. Concretely, with true b=1, c=1, d=−3:
true `b' = (2·1 − 1 + 2·(−3))/3 = −5/3`. Trebled input B=3, C=3, D=−9.
Raw integer combination `2B − C + 2D = −15`. But `3·b' = −5`, not −15 —
`−15 = 9·b'`. Every application of the integer-only coefficients to a
uniformly-prescaled input compounds an *extra*, uncancelled factor of 3,
because the coefficients themselves already carry the 3 that was
supposed to be divided out. A **fixed, uniform rescaling of the
representation cannot absorb a multiplicative-per-application effect** —
this was the flaw in the original reasoning. Verified computationally in
`software/lib/rotc_thirds_native.py` / `software/tests/test_rotc_thirds_native.py`,
which is why those files retain their name (the module is a permanent
audit trail of this dead end) but no longer ship it as the recommended
fix.

### (c-revised) Deferred-reduction, exponent-tagged representation

A genuinely valid alternative, found and cross-verified against the
independent ground-truth oracle across a real 4-step, multi-axis
composition chain (angles 1→3→4→1): carry state as `(value, exponent)`
where `true_value = value / 3^exponent`. Apply the raw integer
coefficients directly to `value` (no division, ever), and increment
`exponent` by 1 per thirds-angle rotation applied. This is **exact by
construction, with no information ever lost** — the division is not
eliminated, it is *deferred* to an explicit, chosen renormalization
point, where either it comes out exact (and the exponent resets to 0)
or — per an explicit `REDUCE` step — the residual is a well-defined,
checkable quantity rather than a silent truncation.

This is architecturally the same pattern already used elsewhere in this
codebase: the nilpotency-window tags on the sparse jet MAC
(`docs/SPARSE_JET_MAC.md`) defer exactly this kind of "don't lose
information, resolve it later, explicitly" decision. It is a real,
verified, viable fix — but it is **not a drop-in change**: every
register needs an extra exponent field, and combining two values with
different accumulated exponents (Davis Gate summing 13 axes with
different rotation histories, for instance) requires exponent alignment
first, the same complexity floating-point addition carries. This is a
genuine ISA extension deserving its own contract (interface, tag
algebra, acceptance checklist — same shape as `SPARSE_JET_MAC.md`), not
something to build as a side effect of closing this bug.

## 3. Recommendation

Two-tier, not three — (c) is gone, (c-revised) is real but big:

1. **Ship (a) now** — the exactness flag. Zero regression risk, catches
   every case, and it's the right safety net to have permanently
   regardless of what else happens (an A₃₁-style FLAGS bit is exactly
   the house idiom for "detect, don't silently corrupt").
2. **Scope (c-revised) as its own contract, if pursued at all.** It is
   verified correct, but it is a real ISA extension (new register field,
   exponent-alignment semantics for cross-axis combination) — not a
   bugfix-sized change, and not this session's to greenlit unilaterally
   given the design surface it opens.

(b) remains not recommended as a standalone fix — only safe for
single-axis rotation chains, which real robotics kinematics chains
violate routinely. It is, however, a reasonable *practical* mitigation
for the common case (many real kinematics operations do rotate
repeatedly about one fixed joint axis) while (c-revised) is scoped
properly, if scoped at all.

## 4. Formal state-machine contract — done

The (c-revised) fix is now specified as a formal state machine:
`docs/ROTC_EXPONENT_STATE_MACHINE.md` — states (CLEAN/PENDING/three FAULT
conditions), transitions (ROTATE/ALIGN/REDUCE), the guaranteed-safe
reduction points (proven, not assumed), and an acceptance checklist. The
oracle is complete and verified: 69 checks in
`software/tests/test_rotc_thirds_native.py`, covering ROTATE, REDUCE
(both the always-succeeds `Fraction` form and the hardware-faithful
faulting form), ALIGN, the multi-axis composition chain, and a genuine
INEXACT fault reproducing the original counterexample.

Remaining before RTL: `spu_vm.py` migration, RTL implementation against
the state-machine contract, and re-verification of existing golden
vectors under the tagged representation — tracked in the state-machine
doc's acceptance checklist, not duplicated here.

*CC0 1.0 Universal, like the rest of `docs/`.*
