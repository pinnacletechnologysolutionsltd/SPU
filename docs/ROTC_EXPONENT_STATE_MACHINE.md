# ROTC Exponent-Tagged State Machine — RTL Contract

Contract for implementing the verified fix in
`docs/ROTC_THIRDS_EXACTNESS_FIX.md` §2(c-revised). Same pattern as
`docs/SPARSE_JET_MAC.md`: the Python oracle
(`software/lib/rotc_thirds_native.py`) is the source of truth, RTL
acceptance means bit-exact agreement with it plus the fault conditions
below — not just "results come out right" on the untested path.

> **Provenance:** the framing of ROTC as a state-machine harness —
> exactness state carried by the data, rotations as guarded transitions,
> reduction as an explicit fallible operation — is due to Gene Yanenko
> (see `docs/ATTRIBUTION.md`). This document is the formalization of that
> idea against the /3 exactness finding.

## 1. Why it exists

Thirds-angle ROTC divides by 3 via `div3`, a true floor division that
silently truncates when the numerator isn't an exact multiple of 3 (see
the lexicon's Davis Gate entry, "/3 divisibility"). No per-axis
precondition check is composition-safe (verified: rotating about a
second axis can leave a previously-safe axis in a bad residue), and no
fixed rescaling of the representation works either (verified and
retracted: it compounds a 9× error instead of cancelling the 3×). The
only verified-correct fix defers reduction instead of forcing it every
step.

## 2. States

Each surd lane (P or Q) of each Quadray axis (A, B, C, D) carries:

```
(value: signed integer, exponent: unsigned integer, 0 <= exponent <= MAX_EXPONENT)
true_value = value / 3^exponent
```

- **CLEAN**: `exponent == 0` — the register holds the exact true value.
- **PENDING**: `exponent > 0` — the register holds `3^exponent * true_value`,
  reduction deferred.
- **FAULT.MISALIGNED**: attempted to combine B, C, D (or any two tagged
  values) at different exponents without an explicit ALIGN.
- **FAULT.OVERFLOW**: a ROTATE would push `exponent` past `MAX_EXPONENT`.
- **FAULT.INEXACT**: a REDUCE was requested and the true value is not an
  integer at the current exponent — see §4, this is not a bug.

## 3. Transitions

### ROTATE(angle), angle ∈ {1, 3, 4}
**Precondition:** B, C, D share a common exponent E. A is untouched —
independent history, exactly matching the existing RTL's `A_out <= A_in`.
**Effect:** apply the integer coefficients directly to `value` (zero
division): `B' = F·B + H·C + G·D` (etc., permuted per angle), new
exponent `E+1` for B', C', D'.
**Guards:** `E+1 > MAX_EXPONENT` → FAULT.OVERFLOW (caller must REDUCE
first). `B.exponent != C.exponent != D.exponent` → FAULT.MISALIGNED
(caller must ALIGN first). Oracle: `rotate_tagged`.

### ALIGN(X, target_exponent)
Raise a tagged value's exponent to `target_exponent` (must be ≥ current):
`value *= 3^(target_exponent - exponent)`. **Always exact** —
multiplication never loses information, which is why this direction
never faults, unlike REDUCE. Refuses to lower the exponent (that's
REDUCE's job, and it can legitimately fail). Oracle: `align_tagged`,
`align_pair`.

### REDUCE(X)
If `X.exponent == 0`: no-op, already CLEAN.
Else: check `X.value % 3^X.exponent == 0`. On success, transition to
CLEAN with `value / 3^exponent`. **On failure: FAULT.INEXACT — no value
is committed.** This is the same "detect, never silently corrupt" idiom
as A₃₁'s FLAGS.V and whisper's saturating (not silently wrapping)
dissonance field. Oracle: `reduce_tagged_exact` (raises
`InexactReduceError`); `reduce_tagged` (returns an exact `Fraction`,
oracle-only — RTL has no rational type, so RTL must implement
`reduce_tagged_exact`'s semantics, not `reduce_tagged`'s).

## 4. Guaranteed-safe reduction points — not a hedge, a proven fact

REDUCE failing is not a defect: it means the rotated point genuinely
isn't an integer Quadray lattice point right now, which is mathematically
correct information, not corrupted data. Two cases where REDUCE is
*guaranteed* to succeed, both verified against the oracle:

- **Full-period closure.** After a complete period-6 cycle (angle 1
  applied 6 times) or an equivalent closure, the state returns to the
  original integer point — REDUCE succeeds by construction. Verified:
  `test_reduce_tagged_exact_success_and_fault`. This is the same closure
  property the existing six-step silicon evidence already demonstrates;
  the tagged representation doesn't change that guarantee, it just
  stops requiring it at every intermediate step.
- **Single-axis chains where the classical precondition holds.** If the
  invariant axis A satisfies A ≡ 0 (mod 3) at the start (the original,
  narrower finding), REDUCE succeeds after every step in a chain that
  never switches axes — this is the old fix, recovered here as a special
  case rather than the general rule.

Anywhere else, an honest FAULT.INEXACT is the correct answer, not a
number.

## 5. `MAX_EXPONENT` sizing

Two independent constraints, and the second is usually binding first:

1. The exponent field's own bit width.
2. **Value magnitude growth.** Each rotation's coefficients have
   magnitude 2 or −1, so `value` grows roughly 3-5× per un-reduced
   rotation. A realistic fixed-width register (16 or 32 bits) will
   overflow on `value` well before a small exponent field (2-3 bits)
   would overflow on `exponent`. Recommendation: size `exponent` for the
   architecture's realistic un-reduced rotation-chain depth (a handful
   of bits is almost certainly enough), and let `value` overflow
   detection be the practical forcing function for when a REDUCE (or
   FAULT.OVERFLOW) becomes mandatory. Pin down the exact bound during
   RTL implementation against real register widths, not in this
   contract.

## 6. Interface (RTL-facing, sketch — not fixed by this contract)

- Each surd register gains an `exponent` field alongside `{P, Q}`.
- ROTATE / ALIGN / REDUCE can be separate micro-ops or fused into a
  single ROTC-with-tags sequencing (align-if-needed, then rotate) —
  implementation's choice. The **fault conditions and value semantics
  above are fixed**; the microarchitecture is not.
- FLAGS gains three fault conditions (MISALIGNED, OVERFLOW, INEXACT) —
  a cause code alongside the existing FLAGS.V pattern, not a new
  mechanism.

## 7. Acceptance checklist

- [x] Oracle implements and verifies ROTATE, REDUCE (both the
  always-exact `Fraction` form and the hardware-faithful
  `reduce_tagged_exact` fault form), and ALIGN —
  `software/lib/rotc_thirds_native.py`.
- [x] Cross-verified against the independent Fraction-based ground
  truth: original counterexample, broad sweep (7,203 cases, zero
  mismatches), zero-sum cases, surd (q≠0) components, a 4-step
  multi-axis composition chain, period-6 closure reduction success, a
  genuine INEXACT fault case, ALIGN exactness and its refusal to lower
  exponent — 69 checks total, `software/tests/test_rotc_thirds_native.py`,
  wired into `run_all_tests.py`.
- [x] RTL testbench: ROTATE normal case; ROTATE at the `MAX_EXPONENT`
  boundary (OVERFLOW); REDUCE success at an exact-divisibility point;
  REDUCE failure (INEXACT) reproducing the exact known counterexample
  (A=1, B=1, C=1, D=−3 via B=−5 at exp=1); ALIGN correctness;
  MISALIGNED fault triggering when B/C/D exponents differ —
  7 tests, all PASS, `hardware/tests/spu13/spu13_rotor_core_tagged_tb.v`.
  RTL implementation: `hardware/rtl/core/spu13/spu13_rotor_core_tagged.v`
  (314 lines, 4-bit exponents, powers-of-3 LUT, signed-division
  exactness, fault flag latching).
- [x] FLAGS semantics (MISALIGNED / OVERFLOW / INEXACT) documented in
  `knowledge/isa_reference.md` alongside the existing FLAGS.V entry
  (2026-07-09).
- [x] Golden-vector re-verification under tagged representation
  contract defined in `knowledge/isa_reference.md` (2026-07-09):
  ROTATE must produce 3× TDM golden at exp=1 for thirds angles;
  REDUCE must recover TDM golden at exp=0. RTL testbench verified.
  Silicon re-verification pending (probe `spu13_tang25k_rotc_tagged_probe.v`
  built, awaiting board run). Existing six-step silicon evidence
  remains valid for the TDM core baseline.

*CC0 1.0 Universal, like the rest of `docs/`.*
