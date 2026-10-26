# Engineering Contract: Accumulated Optical-Depth Loss Investigation (E12)

**Date:** 2026-08-22 (revised same day — see §0)
**Contract ID:** `contract_photonics_optical_depth_2026-08-22.md`
**Status:** RESULT: NEGATIVE, mechanistically explained. Closed before the
full 30,000×4 sweep — see §9. Two independent failure modes (uncompensated
attenuation, §0; mean-compensated residual variance, §9) both exceed BQE
precision tolerance. No new hypothesis retrofit; per John's explicit
direction, next candidate is regeneration placement, not further loss
tuning (§9.5).

**Roles:**
- **Spec Author:** Claude, from direct code inspection and John/GTP's
  prioritization after E11 ("the most promising remaining candidate is one
  that is structurally physical, not algebraic").
- **Halt-and-Flag Implementer:** pre-review of the loss model and
  compensation scoring function (§4) — the naive version of this contract
  was already caught and revised mid-implementation (§0); this revision
  needs its own review before running anything at scale.
- **Integration Auditor:** reproducibility gates, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_cascade_depth_2026-08-22.md` (E11) §10 — the
  algebraic-normalization-vs-physical-transfer-loss distinction this
  contract acts on.
- `contract_photonics_detector_boundary_2026-08-21.md` (E9) — the
  K=8→K=16 collapse this contract investigates (R_8=0.159, R_16=0.0067,
  ratio ≈23.7×).

---

## 0. Revision history (why this isn't the original draft)

The first version of this contract (frozen, then partially implemented
2026-08-22) modeled **fully uncompensated** loss: 1.8 dB/op applied to
every mirrored op, no correction anywhere. Two things were found during
Halt-and-Flag implementation, before any noisy sweep ran, that invalidated
that design:

1. **The proposed noiseless sanity gate was wrong.** It assumed field
   magnitude after K ops would match `LOSS_LINEAR^K` (or `^(K-1)`)
   exactly. Measured directly (multiple trials, full vector norm, exact
   op counts): it doesn't, and not by a small margin — e.g. two K=8 trials
   with identical lane-0 op counts (7) gave ratios of 0.537 and 0.234
   against a predicted 0.234. Cause: `gen_block`'s QSUB draws its two
   sources randomly from lanes `{0, 1}`; when a subtraction mixes a
   heavily-attenuated lane-0 history with a barely-attenuated lane-1 value
   (rescaled to a common `m` first), the result depends on the interplay
   between two different loss histories, not a clean product. This is the
   same *class* of stochastic-mixing effect discovered while designing E11
   (there, for `m`'s growth), now found again for loss accumulation.
2. **The fully-uncompensated model is physically unrealistic and
   produces a degenerate experiment.** Verified: even at detector-noise
   levels near each K's own baseline transition zone, the loss condition
   showed **0% recovery** for both K=8 and K=16 — the systematic
   (noiseless) attenuation alone already exceeds the BQE rounding margin,
   so there is no crossing to compare between K=8 and K=16 under this
   model; the R'_8/R'_16 comparison the original design was built around
   cannot be constructed. A real system would obviously calibrate for a
   *known, deterministic* per-op loss — exactly as REGEN's existing
   compensation trim (`÷cos(K·δφ)`) already corrects for the *known*
   thermal phase drift. Treating a known constant as fully uncompensated
   was an unrealistic strawman.

**Revised hypothesis (John's direction, 2026-08-22):** don't test whether
raw, uncompensated loss explains the gap — test whether the **residual,
stochastic** loss variance left over *after* calibrating for the known
mean loss explains it. This is a meaningfully different, better-motivated
question, not a patch on the old one.

## 1. Objective (revised)

**Does the stochastic residual in per-trial accumulated optical loss —
left uncorrected even after a receiver-side gain trim calibrated to the
*known mean* loss for a given K — explain E9's K=8→K=16 detector-noise
collapse?**

The mean loss is trivially compensable (§0, point 2) and is NOT the
hypothesis under test. What's left uncompensated is the *variance around
that mean*, caused by `gen_block`'s stochastic lane-mixing (§0, point 1):
individual trials experience more or less effective attenuation than the
K-specific average, and no calibration based on the mean alone can correct
for that per-trial deviation. This residual is structurally similar to an
extra noise source — one `m`'s deterministic bookkeeping has no way to
see, since `m` only tracks the *count* of ops, not how much each one's
specific lane-mixing history diluted or preserved the loss.

**Explicitly out of scope:** regeneration placement, operation ordering
(both already deferred), tuning the 1.8 dB value, and any claim beyond
"the residual variance contributes X to the observed gap."

## 2. Objective grounding — what's measured vs. what's assumed

Unlike the original draft, this revision **does not pre-register an
analytic prediction from a formula** (§0 showed the formula is wrong for
`gen_block`'s structure). Instead, the mean compensation factor `L̄(K)`
and its residual variance are **measured empirically**, as the first step
of this contract's own procedure — not assumed, not derived analytically.

```
L̄(K) := mean, over N noiseless loss-condition trials at fixed K, of
         ||fld_loss[lane0]|| / ||fld_baseline[lane0]||
         (full 4-component vector norm, same op-count trial pairs,
         same seed/trial-index stream so blocks match exactly)
```

This is the same measurement already spot-checked during Halt-and-Flag
review (§0) — this contract formalizes it as a required, reported step
(§4), run at full statistical power (not 2-3 trials), for both K=8 and
K=16, before any compensated-loss sweep is trusted.

**`L̄(K)` is deliberately a scalar calibration of full-vector field
amplitude, not an optimization of the final BQE score.** These are not
automatically the same quantity — the receiver's actual observable is
`inphase` (the real part of one complex component plus detector noise),
not the 4-component vector norm. Using the norm keeps this experiment
about the physical transfer-loss phenomenon itself, not about
reverse-engineering whatever scalar happens to maximize recovery (which
would make this a tuning exercise, not a measurement). **Diagnostic only,
not used to alter `L̄(K)`:** also report the distribution of the
compensated `inphase` ratio (loss/baseline, same paired-trial technique)
at zero detector noise — this shows whether the norm-based calibration
tracks what the detector actually sees, without feeding back into the
compensation rule.

**The falsifiable question, precisely:** does a receiver that knows and
corrects for `L̄(K)` (per K, a single scalar trim — architecturally
identical to how the existing `1/cK` phase trim already works: one
correction, applied once, at final detection) still show a
K=8-vs-K=16 recovery gap larger than the loss-free baseline's own gap? If
yes, the *residual* (not the mean) is doing real work, and the size of the
extra gap is the measurement. If the compensated-loss condition's gap
matches baseline's gap, the residual isn't the mechanism either.

## 3. Locked parameters

| condition | K | loss model |
|---|---|---|
| baseline-8 | 8 | none (existing `PhotonicQuadrayBackend`, unmodified) |
| comp-loss-8 | 8 | 1.8 dB/op physical loss + mean-calibrated trim `1/L̄(8)` |
| baseline-16 | 16 | none (existing `PhotonicQuadrayBackend`, unmodified) |
| comp-loss-16 | 16 | 1.8 dB/op physical loss + mean-calibrated trim `1/L̄(16)` |

`gen_block` (E9's generator) reused verbatim, same rationale as the
original draft (§1 of the prior version): the residual-variance hypothesis
is specifically *about* `gen_block`'s stochastic mixing, so a cleaner
generator (E11-style) would eliminate the exact phenomenon under test.

| parameter | value |
|---|---|
| K | {8, 16} |
| L̄(K) measurement | ≥2,000 noiseless trials per K, full distribution reported (§5) — not just mean+std |
| M_K | {8: 2000, 16: 2000} (E9's) |
| band | [1000, 30000] (E8/E9's) |
| seed | 13 |
| det levels | not fixed in advance (same discipline as the original draft) — smoke pass locates the transition region for each condition before any grid is frozen |
| trials per cell | 30,000 (E1–E11's count) |

**Calibration/evaluation separation (mandatory, Halt-and-Flag gate — John's
explicit requirement, 2026-08-22):** no trial index contributing to
`L̄(K)`'s measurement may contribute to any noisy compensated-loss
recovery estimate. Concretely: `L̄(K)` uses `trial_rng(master, trial)` for
`trial ∈ [0, 2000)`; every noisy sweep cell (smoke and full run alike)
must use `trial ∈ [2000, 2000+n_trials)` (an offset trial-index range,
enforced in code, not by convention). `L̄(8)` and `L̄(16)` are computed
once, frozen, and persisted as top-level fields in the output JSON's
metadata before any noisy cell is run — they are inputs to the sweep, not
recomputed per cell or per run.

## 4. New code (additive, Lithic ≤ 150 lines total across both new pieces)

**4a. `PhotonicQuadrayBackendWithLoss`** — unchanged from the original
draft: subclass, overrides only `_apply_op_field`, calls `super()` first,
then multiplies the destination lane by `10^(-1.8/20)` if the op was
mirrored. Already implemented and spot-checked (§0).

**4b. `measure_L_bar(K, n_trials)`** — NEW. Runs `n_trials` paired
noiseless replays over trial indices `[0, n_trials)` (the calibration
range — never reused by the noisy sweep, §3) — baseline vs. loss, same
block via matched seed/trial-index streams (the exact technique used in
§0's debugging). Records `||fld_loss[lane0]|| / ||fld_baseline[lane0]||`
per trial. Returns the full distribution, not just mean+std: **mean,
std, median, IQR (25th/75th percentile), min, max, coefficient of
variation, and the raw value list** — the median/IQR matter specifically
because stochastic lane-mixing could plausibly produce a skewed or
heavy-tailed distribution, which SD alone would misrepresent.

**4c. Compensated scoring** — a new, small function that mirrors
`run_chain_noisy`'s arm-B-only final-detection logic (not a full
reimplementation — `run_chain_noisy` doesn't expose the raw pre-rounding
`inphase`, so the specific compensated comparison must be written fresh,
reusing `_apply_op_field`, `_load_exp`, and the noise-draw helper
verbatim), multiplying `inphase` by the fixed scalar `1/L̄(K)` (measured
in 4b, NOT re-measured per trial) before the existing
`(1<<m)*(inphase/cK)/SCALE` rounding step.

**Halt-and-Flag pre-review items — execution order fixed (John's
requested sequence, 2026-08-22), not to be reordered or compressed:**

1. **Generator/oracle population identity (checked first, highest
   priority):** rejection rates must match baseline exactly for both K
   (band-rejection uses the exact oracle, unaffected by the loss model —
   same generated blocks → same oracle → same accepted/rejected
   population → only optical transfer differs). If rejection counts
   differ, the experiment isn't measuring what this contract says it
   measures — HALT before anything else.
2. **`L̄(K)` calibration** (§4b), on the disjoint calibration trial range
   (§3), frozen into output metadata before any noisy cell runs.
3. **Compensated-scorer invariant:** the "loss never outperforms
   baseline" per-trial check (§0's original fix was against the
   *uncompensated* scorer) must be re-verified specifically for the
   *compensated* scoring function — compensation could in principle
   change this, unverified until checked.
4. **Baseline reproduction check:** `baseline-8`/`baseline-16` must match
   E9's original brackets closely.
5. Smoke pass (§7).
6. Full sweep (§7).

**Also still applies:** loss-placement (QLDI vs. gate-only) remains an
explicit model assumption — report results as testing this specific
model, not a general claim about where physical loss lives.

## 5. Metrics & outputs

- `L̄(K)` and its **full distribution** (mean, std, median, IQR, min/max,
  coefficient of variation, raw values), for K=8 and K=16 — a primary
  artifact in its own right, independent of the noisy sweep result.
- The diagnostic-only compensated-`inphase`-ratio distribution (§2) —
  reported, never used to alter `L̄(K)`.
- P_recover_B(σ_det) for baseline and comp-loss, both K — the noisy sweep.
- Crossing brackets (99.9%, 99%, 95%), reported as brackets, same
  discipline as E9/E11.
- **The comparison (the primary result) — the statistic is:**

  ```
  Q = (R_comp,8 / R_comp,16) / (R_base,8 / R_base,16)
  ```

  `Q = 1` is the natural null (no detectable residual-variance
  contribution). See §6 for the tiered interpretation — do not collapse
  this into a single "substantial/not substantial" threshold.
- Output: canonical JSON (`results/sweeps/optical_depth_sweep.json`),
  including `L̄(8)`, `L̄(16)`, and their full distributions as frozen
  metadata fields, frozen copy with sha256, README entry — same
  discipline as E1–E11.

## 6. Falsification criteria (non-vacuous)

- **`L̄(K)` measurement must complete and be reported with its full
  distribution** before any compensated sweep runs.
- **Baseline reproduction check:** `baseline-8`/`baseline-16` must match
  E9's original brackets closely; a mismatch means the harness diverges
  from E9's and must be resolved (HALT) first.
- **Generator/oracle population identity and compensated-scorer
  invariant** (§4's ordered Halt-and-Flag items 1 and 3) must both pass
  before trusting the noisy comp-loss sweep.
- **`Q`'s tiered interpretation (John's explicit correction, 2026-08-22 —
  do not collapse this into one threshold):**
  - `Q ≈ 1`: no detectable residual-variance contribution.
  - `Q > 1` (any amount): evidence of a real residual-loss contribution —
    quantify it, don't just note the direction.
  - `Q` meaningfully between 1 and ~23.7×: a genuine partial contribution;
    report the fraction of E9's gap this represents explicitly (e.g.,
    "residual loss variance accounts for roughly a factor of X of the
    observed Y×").
  - `Q` near E9's ~23.7×: residual loss variance could plausibly account
    for most of the E9 gap — a strong result, still not proof of
    exclusivity (other factors could still combine).
  - `Q` at or beyond 23.7×: unexpected — investigate the relationship to
    E9 rather than reporting it at face value (an *over*-explanation is as
    surprising as no explanation, and deserves scrutiny before being
    taken as confirmation).
- **Residual variance ruled out** iff `Q` is statistically
  indistinguishable from 1 — comp-loss's K-gap matches baseline's gap once
  the mean is corrected for. Report as cleanly as a confirmation.

## 7. Verification gates (implementer/auditor) — fixed order

**Fixed order, matching §4's Halt-and-Flag sequence exactly — do not
reorder or compress:**

```bash
# 0. Generator/oracle population identity: rejection rates must match
#    baseline exactly for both K, before anything else is trusted.

# 1. L-bar calibration (SS4b): >=2000 noiseless paired trials per K, on
#    the calibration trial-index range [0, 2000) -- disjoint from every
#    noisy sweep cell (SS3). Report the full distribution (mean, std,
#    median, IQR, min/max, CV). Freeze L-bar(8) and L-bar(16) into output
#    metadata before proceeding.

# 2. Compensated-scorer invariant: confirm comp-loss never outperforms
#    baseline per-trial, using the COMPENSATED scoring function
#    specifically (not the uncompensated one already checked in SS0's
#    history).

# 3. Baseline reproduction check: baseline-8/baseline-16 vs E9's original
#    brackets.

# 4. Smoke pass, all four conditions -- confirm gen_block reuse reproduces
#    E9's baseline crossings, and locate the comp-loss conditions'
#    crossing regions before locking a grid. Every noisy cell (smoke and
#    full run alike) uses trial-index range [2000, 2000+n_trials).
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_optical_depth_sweep.py

# 5. Full run (only after step 4 confirms grid ranges and step 3 passes)
.venv/bin/python3 photonics/run_photonic_optical_depth_sweep.py

# 6. Reproducibility: two full runs, bit-identical -- checked empirically
#    first (E9/E11/original-E12-draft lesson), not assumed.

# 7. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No regeneration-placement investigation** — deferred to its own
  contract regardless of this one's outcome.
- **No operation-ordering investigation** — parked per E11's review.
- **No tuning the loss value or the compensation methodology** — 1.8 dB
  stays fixed at its established value; the mean-trim architecture (a
  single scalar at final detection) is fixed as specified, not iterated on
  to improve the result.
- **No claim about which specific op types should carry loss** beyond the
  Halt-and-Flag-flagged default (§4).
- **No E10 (combined-axis)** — still deferred behind understanding the
  K=16 anomaly.
- **No re-litigating the original uncompensated-loss design** — §0
  documents why it was abandoned; this is not "try uncompensated loss
  again with a different value."

## 9. Results (2026-08-22) — closed without the full sweep

**Status: NEGATIVE RESULT, mechanistically explained. Closed before the
30,000×4 full sweep** (§7 steps 5-7 not run) — the calibration and
invariant-checking steps already demonstrated a structural degeneracy that
no amount of additional trial count would resolve, per John's explicit
direction not to spend the full compute budget on a result already
determined at the calibration/invariant stage.

### 9.1 What was run (gates 0-2 of §7, in order)

- **Gate 0 (generator/oracle population identity):** exact match, both K
  (K=8: rej=0.5575 both conditions; K=16: rej=0.5730 both conditions) —
  confirms rejection is governed purely by `gen_block`'s oracle check,
  unaffected by the loss model, as designed.
- **Gate 1 (`L̄(K)` calibration, §4b, 2000 trials each, calibration trial
  range `[0, 2000)`):**

  | K | n | mean | std | median | IQR | min | max | CV |
  |---|---|---|---|---|---|---|---|---|
  | 8 | 2000 | 0.48755 | 0.14893 | 0.52085 | [0.3663, 0.6607] | 0.01748 | 1.00734 | 0.3055 |
  | 16 | 2000 | 0.49554 | 0.16377 | 0.53703 | [0.3757, 0.6607] | 0.03460 | 2.52480 | 0.3305 |

  **The means are nearly flat across K (0.488 vs 0.496) — very different
  from the abandoned `LOSS_LINEAR^K` model's steep prediction (0.19 vs
  0.036).** `gen_block`'s stochastic lane-mixing (§0) doesn't compound
  loss the way a clean chain would. **The spread is measurably wider at
  K=16** (CV 0.331 vs 0.306; max ratio 2.52 vs 1.01 — some K=16 trials
  show loss-condition norm *exceeding* baseline, from subtractive
  cancellation asymmetry in `gen_block`'s QSUB mixing lane 0 with lane 1).
  This K-dependent widening is consistent with the residual-variance
  hypothesis, independent of what the noisy sweep later showed.
- **Gate 2 (compensated-scorer invariant, spot-checked, not exhaustively):**
  `comp_B` never exceeded `base_B` across 4 paired (K, level) checks near
  each K's baseline transition zone, and separately, `comp_B = 0.0000`
  held across both K at det levels 1e-6, 1e-4, and 1e-3 (10 (K, level)
  spot checks total, 300-1000 trials each) — not the full formal per-trial
  paired invariant test E11/the abandoned E12 draft used, but consistent
  with it everywhere checked.

### 9.2 The decisive finding: `comp_B = 0.0000`, independent of detector noise

Across every tested detector-noise level for both K — from levels near
each K's own baseline transition zone up to 1e-3 (three orders of
magnitude above where E9's actual crossings live) — the compensated-loss
condition showed **exactly 0% recovery**. Traced to a specific example
(K=16, one accepted trial): actual per-trial loss ratio 0.288 against the
calibrated mean 0.496 — a ~42% deviation, well within the measured
CV≈30% spread, but the recovered integer magnitudes in this system run
into the hundreds/thousands against a ±0.5 BQE rounding tolerance, meaning
the *required* relative precision is on the order of 10⁻³–10⁻⁴. A ~30%
residual is two to three orders of magnitude too large for *any* single
scalar correction to close.

Because `comp_B = 0.0000` regardless of detector noise level, detector
noise is not the limiting variable here — the compensation residual alone
already places every trial outside the BQE acceptance basin before any
detector noise is even added.

### 9.3 Conclusion — precisely scoped (not overstated)

**What this contract establishes:** no single fixed scalar compensation
per K can recover exact BQE under the specified 1.8 dB/op loss model
applied through `gen_block`'s stochastic mixing. This is **not** the
broader claim that no compensation scheme whatsoever could work — an
adaptive, per-trial compensation that somehow observed the actual optical
transfer for each trial could theoretically remove the residual. But that
would be a fundamentally different receiver architecture, and not one the
current SPU design possesses. The scientifically precise statement:

> **The accumulated-loss mechanism, at this magnitude, is incompatible
> with the existing scalar-calibrated receiver architecture at the
> precision exact BQE recovery demands.**

Combined with §0's uncompensated result, this is now **two independent
failure modes converging on the same conclusion**: raw uncompensated
attenuation exceeds BQE tolerance; mean-compensated residual variance
*also* exceeds it. That convergence substantially lowers the probability
that "ordinary accumulated optical loss" is the hidden explanation for
E9's K=16 collapse — a stronger, more defensible result than either
finding alone.

**This is itself a useful architectural finding**, independent of whether
it explains E9: it establishes a real limit on what a single-scalar
receiver-side calibration can correct for in this system, at this
sensitivity.

### 9.4 What's preserved as evidence

- `L̄(8)`, `L̄(16)` and their full distributions (§9.1) — including the
  raw 2000-value lists, retained in the calibration run's output, not
  just summary statistics.
- The specific actual-vs-mean example (K=16, ratio 0.288 vs L̄=0.496,
  §9.2) demonstrating the mechanism concretely, not just statistically.
- The `comp_B = 0.0000` noise-independence result across the tested range
  (§9.1 gate 2).
- The compensated-scorer invariant spot-checks (§9.1 gate 2).
- The code: `PhotonicQuadrayBackendWithLoss`, `measure_L_bar`,
  `run_chain_compensated`, `cell` — all in
  `photonics/run_photonic_optical_depth_sweep.py`, unchanged from what
  produced these results.
- This contract's §0 (the abandoned uncompensated design and why) and §9
  (this section) together are the complete record — no separate write-up
  needed.

### 9.5 Next: K-dependent error amplification, not further loss tuning

Per John's explicit direction: don't continue tuning the loss model (a
different dB value, a different placement, a different compensation
scheme) to try to rescue this hypothesis — that would convert a clean
negative result into curve-fitting. The investigation should move toward
mechanisms that could plausibly produce **K-dependent error amplification
at the sub-percent scale** — the precision regime E9's actual crossings
live in, not the ~30% regime this contract found. Regeneration placement
(GTP's second-ranked candidate, not yet drafted) is the natural next
candidate; operation ordering remains parked (E11 §10).
