# Engineering Contract: Cascade-Depth Mechanism Investigation (E11)

**Date:** 2026-08-22
**Contract ID:** `contract_photonics_cascade_depth_2026-08-22.md`
**Status:** RESULT: HYPOTHESIS RULED OUT, FROZEN (2026-08-22).
All gates passed in order (oracle → noiseless validation → smoke →
full run). Arm T and Arm N's crossing brackets coincide exactly — see §9.1.
**Uncompensated `/3` divisions from exact-thirds ROTC angles do not explain
E9's K=8→K=16 collapse.** The collapse remains unexplained; no new
hypothesis was retrofit onto this result, per John's explicit instruction.
Reproducibility CONFIRMED (§9.4): two full runs, bit-identical. Frozen copy
`results/sweeps/cascade_depth_sweep_frozen_v1_2026-08-22.json`, sha256
`2e322400…`.

**Roles:**
- **Spec Author:** Claude, from direct code inspection (§2.1) — not a
  retrofit onto E9's data (John's explicit instruction after E9: "I would
  resist interpreting the mechanism yet... that's a hypothesis, not a
  finding"). This contract proposes exactly one hypothesis, motivated by
  reading the noise-application code, and a controlled experiment to
  confirm or rule it out.
- **Halt-and-Flag Implementer:** pre-review of the new controlled
  block-generator (§4) — this is genuinely new code, unlike E9's pure reuse
  of E8's harness, and needs the same scrutiny E9 gave to `gen_block`.
- **Integration Auditor:** reproducibility gates, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_detector_boundary_2026-08-21.md` (E9) — the
  falsifying result this contract investigates. §10.3's second observation
  (K=8→K=16 R_K collapse, ~24× over Δm̄≈3.2) is this contract's objective.
- `contract_photonics_backend_2026-08-20.md` §3.3 — the falsified closed
  form, already flagged with a dated pointer; this contract does not
  re-litigate that flag, it investigates the mechanism behind it.

---

## 1. Objective

E9 measured R_K = σ\*_det(K)/σ_det,pred(K) across K∈{1,2,4,8,16} and found
it is not approximately constant — falsifying the backend contract's
`σ_det ≲ 0.05/2^m` general law. Most of that decline is gradual (R_1=0.301
→ R_8=0.159, a ~1.9× drop over Δm̄≈5.2), but the **K=8→K=16 step drops R by
~24× over Δm̄≈3.2 alone** — disproportionate, and unexplained by the
scalar scale-exponent model. **This contract's only job:** test one
concrete, code-grounded hypothesis for that disproportionate collapse, via
a controlled experiment — not survey candidate mechanisms, not fit a
corrected formula.

**Explicitly out of scope:** correcting the backend contract's formula
(this is a mechanism test, not a re-calibration); testing the other
candidate variables GTP raised (operation ordering, accumulated loss,
regeneration placement) — if this contract's hypothesis is confirmed but
doesn't fully explain the collapse, those become candidates for a
follow-on contract, not something to fold in here.

## 2. Objective grounding — the hypothesis, from code, not from data

### 2.1 How detector noise actually enters the K-chain (read, not assumed)

`PhotonicQuadrayBackend.run_chain_noisy` (`software/tests/test_regen_equivalence.py:326-413`)
draws a fresh per-op noise tuple `(dp, ap, nd)` at every mirrored op
(`_noise_per_op`, line 318), but **arm B (the `recovery_B` metric E9's
crossings are built on) only uses the LAST op's detector-noise draw**
(line 365: `dp, ap, nd = noise_lists[-1]`) — a single one-shot Gaussian
draw of absolute std σ_det, added to the field's real part at the one
final coherent detection (line 370: `inphase = fld[lane][k].real + nd[ln][k]`).
On recovery, this gets multiplied by `1 << m[lane]` (line 371) — so a fixed
absolute detector noise, after `2^m` amplification, is exactly the
mechanism the backend contract's `σ_det ≲ 0.5·s/2^m` formula describes.

**If `m` (the accumulated scale exponent) is the only thing that matters,
R_K should be constant** — the `2^m` amplification is the whole story, and
E9 already uses the *measured* m̄(K), not an assumed one. It isn't
constant. So something else, uncaptured by the scalar `m`, must also be
degrading recovery — and it must scale with the number of combine
operations, since the effect gets sharply worse specifically at high K.

### 2.2 The candidate: uncompensated `/3` divisions from "exact-thirds" ROTC angles

`m[dst] = m[src] + 1` (`test_regen_equivalence.py:257`, `:312`) is
**unconditional** for every ROTC op regardless of angle — confirmed
empirically too: E9's measured m̄(K) had **zero spread across cells**
(§10.2 of the E9 contract), consistent with every combine op incrementing
`m` by exactly 1. But the field division applied to the ROTC angles is
**not** uniformly `/2`: `exact_rotc` (`test_regen_equivalence.py:84-102`)
shows angles {0, 2, 5} are pure permutations (denominator 1, division `/2.0`
only, from `_apply_op_field`'s unconditional `/2.0` — `line 253/308`), while
angles {1, 3, 4} ("exact thirds") apply an **additional** `/3` division
(`div=3.0`, line 307) that `m`'s `+1` bookkeeping never compensates for.

**Hypothesis (untested):** a K-op block containing more angle-{1,3,4}
ROTC ops accumulates more uncompensated `/3` shrinkage than a block of the
same K containing only angle-{0,2,5} ROTC ops (or QSUB), even though both
report identical `m̄(K)` — and this uncompensated shrinkage, not `m`
itself, is what makes the recovered signal more vulnerable to a fixed
absolute detector noise at high K. Since `gen_block`'s combine-op mix is
stochastic (random 50/50 ROTC-vs-QSUB choice, and a random angle shuffle
when ROTC is chosen — `run_photonic_envelope_sweep.py:64-76`), a K=16
block has 14 chances to draw a thirds-angle versus K=8's 6 chances — more
opportunities for uncompensated shrinkage to accumulate, which could
explain why the collapse is disproportionately worse at K=16.

**This is the minimum additional state variable candidate per John's
framing** — not "K itself," not "operation ordering," but specifically:
*the count of uncompensated-division ops in the chain*. If this doesn't
explain the collapse, those other candidates are still open; if it does,
they may not be needed at all.

## 3. Locked parameters — the controlled two-arm design

To isolate this variable cleanly, **do not reuse `gen_block`'s stochastic
mixing** (its random ROTC/QSUB choice and random lane-source selection for
QSUB can reset `m`'s growth mid-chain — a real effect discovered while
designing this contract, not previously documented; `gen_block`'s
apparent "zero-spread m̄" is a *mean*-of-30000-trials stability, not
evidence that individual trials don't vary). Instead: two purpose-built
arms, both **pure self-rotation chains** (`ROTC(dst=0, src=0, angle)`
repeated, no QSUB, no lane-mixing — QLDI once, then K−1 self-ROTCs),
differing only in the angle set drawn from:

| Arm | Angle set | `/3` per combine-op | m growth per combine-op |
|---|---|---|---|
| **T** (thirds) | {1, 3, 4}, random choice each step, shuffle-retry on lattice-reject (§4) | yes, every op | +1 (unconditional, same as N) |
| **N** (no-thirds, control) | {0, 2, 5}, random choice each step | never | +1 (unconditional, same as T) |

**Both arms have identical per-trial deterministic scale-exponent
bookkeeping m = m₀ + (K−1), independent of the selected angles** — not a
stochastic mean like `gen_block`'s m̄(K) (§3's opening note), an exact
per-trial value every single time, since `+1` per self-ROTC applies
regardless of which angle in the set gets drawn (m₀ ≈ 8 from the single
QLDI's `_load_exp`; K−1 self-ROTCs each +1 — one fewer than `gen_block`'s
K−2 combine-ops since there's no second QLDI here). The *only* difference
between arms is whether `/3` divisions
accumulate. This is the cleanest possible isolation of §2.2's hypothesis.

| parameter | value |
|---|---|
| K | 16 only (E9's most degraded case — the disproportionate collapse this contract investigates) |
| arms | T (angles {1,3,4}), N (angles {0,2,5}) |
| det levels | E9's existing K=16 split grid, reused verbatim: `DET_LEVELS_K16_EXTRA + DET_LEVELS` (35 points, 1e-9–5e-4) — already proven to bracket a K=16-scale crossing; both arms' own predicted crossing (~5.96e-9, §3 below) sits inside this range, but the smoke pass (§7) must confirm this before the full run, same discipline as E9 |
| M_K | 2000 (E9/E8's value, for direct comparability) |
| band | [1000, 30000] (E8/E9's) |
| seed | 13 |
| trials per cell | 30,000 (E9's count, for direct comparability) |
| cells | 35 × 2 arms = 70 |

**Predicted outcome, computed precisely (corrected after an initial drafting
error — this design's per-trial deterministic m is NOT the same as
`gen_block`'s stochastic K=16 mean m̄ of 16.4, since it uses one QLDI +
(K−1) monotonic self-ROTCs instead of two QLDI + (K−2)
stochastically-mixed combines; recomputed from `_load_exp(M_K=2000)=8`,
giving m = 8 + (K−1) = **23** for K=16, exactly, every trial, for both
arms by construction):**

- σ_det,pred at m=23 (the closed-form's own prediction for *this* design,
  computed the same way as E9's σ_det,pred(K)) = **0.05/2²³ ≈ 5.96e-9**.
- **Arm N (no thirds) is the closed-form's own best case** — a pure
  single-lane chain with only `/2` divisions, exactly what `m`'s `+1`
  bookkeeping was designed to compensate. If the hypothesis in §2.2 is
  right, **Arm N's crossing should land close to 5.96e-9** — matching the
  formula almost by construction, since nothing uncompensated is
  happening.
- **Arm T (all thirds) should show a substantially tighter (smaller)
  crossing than Arm N's** — every one of the 15 self-ROTC steps adds an
  uncompensated `/3` shrinkage on top of the `/2` that `m` already
  accounts for; the compounding effect across 15 steps could be large
  (rejection from repeated modulo-3 lattice checks may itself limit how
  often a full 15-step thirds chain is even achievable — a real risk
  flagged in §4's Halt-and-Flag review, not a reason to expect a specific
  number).
- Notably, 5.96e-9 (Arm N's predicted crossing) sits close to E9's
  original *mixed-composition* K=16 measurement (~3–7e-9, geometric mean
  3.87e-9) — consistent with the idea that E9's stochastic block
  generator produced a *partial* thirds-fraction (not the full 15/15 of
  Arm T), landing somewhere between Arm N and Arm T. This is a plausible
  consistency check, not a locked prediction — `gen_block`'s actual
  average thirds-fraction per K=16 block was never measured (§3's opening
  note) and isn't claimed here.

**Predicted outcome if the hypothesis is wrong:** Arm T and Arm N show
statistically indistinguishable crossings (both near 5.96e-9, or both
somewhere else entirely, but not clearly separated). That rules out §2.2
and leaves the collapse unexplained — a legitimate, reportable result (§6),
not a failed contract.

## 4. New block generator (additive, Lithic ≤ 150 lines) — Halt-and-Flag review required before running

`gen_self_rotc_chain(rng, K, angle_set)`:
1. `v0 = [rint(rng, -M_K[16], M_K[16]) for _ in range(4)]`; `qr0 = list(v0)`;
   block = `[("QLDI", 0, tuple(v0))]`.
2. For `K − 1` steps: shuffle `angle_set`, try each in order via
   `exact_rotc(qr0, ang)` (reuse verbatim from `run_photonic_envelope_sweep.py`
   / `test_regen_equivalence.py` — do not reimplement); on the first
   non-`None` result, append `("ROTC", 0, 0, ang)`, set `qr0 = list(result)`.
   **If no angle in the set is lattice-safe** (only possible for Arm T,
   since Arm N's angles never fail `exact_rotc`'s modulo-3 check): reject
   the whole trial (return `None`), counted as rejected — same convention
   as `gen_block`'s band rejection.
3. Band check: `final = max(abs(c) for c in qr0)`; reject (return `None`)
   if outside `[1000, 30000]`.
4. Return `block`.

**Halt-and-Flag pre-review items (flag before implementing, per role):**
- Confirm `exact_rotc`'s repeated self-application (`src=dst=0`, no other
  lane involved) doesn't hit an edge case `gen_block`'s original
  lane-mixing design avoided — e.g., does repeated angle-1 (or any single
  angle) application cycle back to a fixed point or degenerate lattice
  faster than the mixed-lane version? Run a noiseless sanity check (both
  arms, K=16, zero noise) against the independent big-int oracle
  (`exact_rotc` applied K−1 times directly, no field/complex-number path)
  before any noisy sweep — confirms the new generator's blocks are
  correct, not just "doesn't crash."
- Arm T's rejection rate is unknown and could be high (three sequential
  modulo-3 lattice checks per step, compounding over 15 steps) — the
  smoke pass (§7) must report it; if very high, the compute-budget
  estimate needs recalculating, same as E9's K=16 sub-grid lesson.

## 5. Metrics & outputs

- P_recover_B(σ_det) for both arms, all 35 grid points — the primary
  artifact (arm A/per-op REGEN is not the subject of this investigation;
  report it if `cell()`-equivalent machinery produces it for free, but
  don't design around it).
- **Crossing brackets** (99.9%, 99%, 95%) for both arms, reported as
  brackets per E9's discipline (§6 of E9's contract) — not false-precision
  point estimates.
- **The comparison (the primary result):** Arm T's crossing vs Arm N's
  crossing, and both vs E9's original (mixed-op) K=16 crossing
  (~3e-9–5e-9 for 99.9%, from E9 §10.1). Report as a three-way bracket
  comparison, not a single number.
- Output: canonical JSON (`results/sweeps/cascade_depth_sweep.json`),
  frozen copy with sha256, README entry — same discipline as E1–E9.

## 6. Falsification criteria (non-vacuous)

- **Sanity gate (must pass before the noisy sweep runs at all):** at
  σ_det=0, both arms must show 100% recovery — if either doesn't, the new
  generator has a bug (HALT, fix before proceeding; do not interpret a
  buggy-generator result as a mechanism finding).
- **Hypothesis confirmed** iff Arm N's crossing bracket is meaningfully
  higher (less tight — recovery survives more detector noise) than Arm
  T's, by more than the width of either bracket (i.e., the brackets don't
  overlap) — matching §3's predicted direction.
- **Hypothesis ruled out** iff Arm T's and Arm N's crossing brackets
  overlap or coincide — report this as cleanly as a confirmation; do not
  search for a different post-hoc explanation within this contract (per
  John's instruction — a new hypothesis is a new, separately-authorized
  contract).
- **Partial result:** if Arm N's crossing is higher than Arm T's but still
  meaningfully below Arm N's own predicted 5.96e-9 (i.e., even the
  "clean," thirds-free design underperforms its own closed-form
  prediction), that means `/3` divisions are *a* contributing factor but
  not the whole explanation for E9's original collapse — report the
  residual gap explicitly, do not claim full explanation.

## 7. Verification gates (implementer/auditor) — fixed order, no skipping

**Per Halt-and-Flag review: independent oracle → noiseless generator
validation → smoke/rejection measurement → full sweep → interpretation.
If the noiseless gate fails, HALT — fix the generator before looking at
any noisy result. Do not debug the generator by reasoning about noisy
output; a wrong generator makes any detector-noise finding meaningless.**

```bash
# 0a. Independent oracle for both arms: K-1 applications of exact_rotc
#     directly on the big-int state (no field/complex-number path at all) —
#     this is the ground truth the generator's noiseless output is checked
#     against, not the noisy-sweep machinery.

# 0b. Noiseless generator validation (Halt-and-Flag §4) — both arms, K=16,
#     sigma_det=sigma_phi=sigma_amp=0, generator's output run through
#     PhotonicQuadrayBackend.run_chain_noisy and compared to 0a's oracle.
#     MUST be 100% recovery for both arms before proceeding to step 1.
#     FAIL -> HALT, fix the generator, rerun 0a/0b. Do not proceed.

# 1. Smoke pass — confirm the harness runs, measure Arm T's rejection rate,
#    estimate wall-clock cost (which may differ substantially from E9's,
#    given the pure-self-rotation design's different rejection profile)
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_cascade_depth_sweep.py

# 2. Full run (only after step 1's compute-budget check)
.venv/bin/python3 photonics/run_photonic_cascade_depth_sweep.py

# 3. Reproducibility: two full runs, bit-identical — checked empirically
#    (not assumed) per the E9 lesson, using the same `cell()`-style
#    deterministic-RNG pattern if reused, or freshly verified if not.

# 4. Complete repository regression
bash tools/verify_repo.sh

# 5. Interpretation (§6) only after 0-4 all pass — not before.
```

**Interpreter note (carried from E9):** `.venv/bin/python3`, never bare
`python3` — numpy availability affects the RNG path.

## 8. Non-Goals

- **No formula correction** — this contract tests one hypothesis; even a
  full confirmation doesn't automatically mean the backend contract gets a
  new formula. That's a separate decision (E9's §10.3 already establishes
  the old one is falsified; this contract is about mechanism, not
  replacement).
- **No testing of other candidate mechanisms** (operation ordering,
  accumulated loss, effective optical depth, regeneration placement) — if
  this hypothesis doesn't fully explain the collapse, those remain
  candidates for separately-authorized follow-on contracts.
- **No K values other than 16** — the disproportionate collapse is
  specifically a K=8→K=16 phenomenon; extending to other K is a natural
  follow-on (and cheap, if this design is validated) but not this
  contract's scope.
- **No E10 (combined-axis)** — still gated on understanding the K=16
  anomaly first, per the existing deferral chain.

---

## 9. Results (2026-08-22) — full run, 70 cells × 30,000 trials

**Status: RUN COMPLETE.** `results/sweeps/cascade_depth_sweep.json`, sha256
`2e322400…`. Gate order followed exactly (§7): independent oracle →
noiseless generator validation (100% for both arms, both against the
oracle and against `PhotonicQuadrayBackend.run_chain_noisy` at σ=0 —
Arm T 321/321 and 148/148 across two independent checks, Arm N 936/936
and 468/468; rejection rates 66–70% for Arm T, 3–6% for Arm N, as flagged
possible in §4's Halt-and-Flag review) → smoke pass (29s/70 cells at 200
trials, extrapolated ≈72.5 min) → full run → this interpretation.
Determinism confirmed empirically (`cell()` bit-identical across repeated
calls with identical arguments), same discipline as E9.

### 9.1 Crossing brackets — T and N coincide

| Arm | 99.9% bracket | B | 99% bracket | B | 95% bracket | B |
|---|---|---|---|---|---|---|
| T | [1.5e-9, 2.0e-9] | .9998→.9868 | [1.5e-9, 2.0e-9] | .9998→.9868 | [2.0e-9, 3.0e-9] | .9868→.8163 |
| N | [1.5e-9, 2.0e-9] | .9997→.9883 | [1.5e-9, 2.0e-9] | .9997→.9883 | [2.0e-9, 3.0e-9] | .9883→.8174 |

All three thresholds land on the **identical bracket** for both arms.
Point-by-point B values track within Monte Carlo noise across the entire
transition region (e.g. 3e-9: T=.8163/N=.8174; 5e-9: T=.3468/N=.3401;
7e-9: T=.1428/N=.1334; 1e-8: T=.0463/N=.0412) — no systematic separation
in either direction at any grid point.

### 9.2 Falsification verdict (§6)

- **Sanity gate: PASS** (§7 step 0, above).
- **Hypothesis ruled out: CONFIRMED.** §6's criterion — "brackets overlap
  or coincide" — is met exactly, not marginally. **Uncompensated `/3`
  divisions from exact-thirds ROTC angles {1,3,4} do not explain E9's
  disproportionate K=8→K=16 detector-noise collapse.** A chain built
  entirely from thirds-angles and a chain built entirely from
  permutation-angles, with identical K, identical per-trial deterministic
  m=23, and identical everything else, show statistically indistinguishable
  detector-noise tolerance.
- **A secondary, unplanned finding:** both arms' measured crossing (~2–3e-9
  for 99.9%) sits noticeably tighter than the naive closed-form prediction
  of 5.96e-9 computed in §3. Partial explanation found during interpretation
  (not a new hypothesis under test — a correction to how the prediction
  itself was computed): the closed-form `σ_det ≲ 0.05/2^m` is a
  single-component threshold, but `run_chain_noisy`'s arm-B scoring
  requires all 4 independent lane-0 components to round correctly
  (`rec == qr` over `k in range(4)`), each with an independent detector-noise
  draw. Aggregating four independent per-component failure chances
  (`P(block fails) = 1-(1-p_component)^4 = 0.5` rather than `p_component =
  0.5`) tightens the predicted 50%-point from 5.96e-9 to ≈4.2e-9 — closer
  to, though not exactly matching, the ≈4–5e-9 region where both arms
  actually cross 50%. This four-component correction applies equally to
  both arms (and, since arm-B scoring is structurally the same in E9, would
  apply to E9's original K-sweep too) — it does not, and cannot, explain
  E9's K-dependent R_K spread, since it is a constant factor independent of
  K. It only explains why *this contract's own* §3 prediction (5.96e-9) was
  itself imprecise. Not pursued further under this contract (out of scope
  per §8 — this contract tests one hypothesis about K=8→K=16, not general
  formula precision).

### 9.3 What this means for the open investigation

**The K=8→K=16 collapse remains unexplained.** This contract's one
hypothesis is cleanly ruled out — not inconclusive, not partially
supported. Per John's instruction (repeated here since it now actually
applies): this is not the moment to retrofit a new explanation inside this
contract. The candidate variables GTP originally raised and this contract
explicitly deferred (§8) — operation ordering, accumulated loss, effective
optical depth, regeneration placement — remain open, alongside any other
candidate not yet identified. A follow-on mechanism-investigation contract,
separately authorized, is the right next step if this remains a priority;
it is not authorized by this result.

### 9.4 Reproducibility — CONFIRMED (2026-08-22)

Two independent full 70-cell × 30,000-trial runs, bit-identical
(`a == b`, no stripping needed — this script emits no timestamp field).
Frozen: `results/sweeps/cascade_depth_sweep_frozen_v1_2026-08-22.json`,
sha256 `2e322400e6812630b32b672b1f9ccf62f3b04320943bfd593d170bf37592dff8`.
README entry added. **E11's hypothesis-ruled-out result is not a Monte
Carlo fluke.**

A follow-on mechanism contract (candidates: regeneration placement,
per §10 below and E12's finding) remains not drafted beyond what §10/E12
themselves establish.

## 10. Post-E11 conceptual clarification (2026-08-22) — algebraic
normalization vs. physical transfer loss

Requested explicitly before drafting any follow-on contract: **why** did
§2.2's hypothesis fail, at the level of the actual mathematics, not just
empirically? The naive model was `/3 → extra attenuation → smaller signal
→ worse SNR`. This section shows that model was never correct, and states
the distinction that should govern which hypotheses get tested next.

**Verified computationally (not asserted):** for every one of the six ROTC
angles, `(F, G, H) / div` is an exact unit vector —

```
angle 0: (1,0,0)/1    -> sum of squares = 1 (exact: 1)
angle 1: (2,2,-1)/3   -> sum of squares = 1 (exact: 4/9+4/9+1/9 = 1)
angle 2: (0,1,0)/1    -> sum of squares = 1 (exact: 1)
angle 3: (-1,2,2)/3   -> sum of squares = 1 (exact: 1/9+4/9+4/9 = 1)
angle 4: (2,-1,2)/3   -> sum of squares = 1 (exact: 4/9+1/9+4/9 = 1)
angle 5: (0,0,1)/1    -> sum of squares = 1 (exact: 1)
```

**The `/3` is not an independent attenuation bolted onto an otherwise
comparable transform — it is the normalization constant that makes the
thirds-angle coefficients a unit vector, structurally identical in kind to
why the permutation angles' trivial coefficients `(1,0,0)` etc. are
already unit vectors without needing one.** `ROTC(dst, src, angle)`
applied to `(B, C, D)` is, for every angle, an exact orthogonal
(norm-preserving) rotation on that 3-component subspace — never a
lossy transform, regardless of which of the six angles is chosen. The
separate, universal `/2.0` applied to all four components (`A/2` and
`(F·B+H·C+G·D)/div/2`) is angle-independent and is exactly what `m += 1`
tracks. Since the rotation itself is norm-preserving for every angle and
the `/2` is uniform across every angle, **there was never a "gap" for `m`
to miss** — E11 had to come back negative given this structure, not just
happened to.

**The distinction to carry forward, stated as a rule:**

> **Algebraic normalization** (a divisor that exists to keep a transform's
> own coefficients on the correct scale — e.g., making a rotation
> orthogonal) is not the same thing as **physical transfer loss** (an
> independent attenuation mechanism in the physical substrate that the
> algebraic/ISA-level model doesn't represent at all). E11 tested the
> former by mistake, dressed up as a substrate mechanism. Don't keep
> testing hypotheses of the "scalar attenuation hidden inside an operation
> whose coefficients are mathematically coupled" family — that family is
> now considerably less plausible, at least within the ROTC/QSUB op set
> `m` already tracks exactly.

**Consequence for prioritizing the next contract:** the most promising
remaining candidate is one that is **structurally physical, not
algebraic** — a loss/attenuation mechanism that exists in the physical
field representation but has no corresponding term in the algebraic
scale-exponent bookkeeping at all (not even an implicit one, the way
ROTC's rotation turned out to have). That is a different *kind* of
hypothesis than §2.2's, not a variation on it. See
`contract_photonics_optical_depth_2026-08-22.md` (E12).
