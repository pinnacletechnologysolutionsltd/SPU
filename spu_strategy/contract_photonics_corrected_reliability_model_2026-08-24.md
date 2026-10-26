# Engineering Contract: Corrected Whole-Chain Reliability Model

**Date:** 2026-08-24
**Contract ID:** `contract_photonics_corrected_reliability_model_2026-08-24.md`
**Status:** RAN TO COMPLETION 2026-08-24. **RESULT: the corrected
estimator reduces the naive model's point-estimate gap by 71%
(`gap_naive=0.0143` → `gap_corrected=0.0041`) but is disqualified by its
own over-correction gate — `mean_corrected` exceeds the empirical rate's
95% CI upper bound. Not adopted as a design-time estimator. See §9.**

**Halt-and-Flag review round 2 (2026-08-24, reviewer external to this
session):** verdict "minor amendments; then authorize" — round 1's §2.1
verification accepted as sufficient, no re-derivation requested. Three
required changes, all incorporated below: (1) the `pair_id=i-2`
transition correspondence made explicit and auditable in the estimator
itself, not just in prose (§2.2); (2) pair-0 fallback reporting
strengthened to include the fraction of the 7 transitions using E18
cells vs. falling back, not just a prose caveat (§2.3, §5 output list);
(3) §5's "own dispersion band" criterion — flagged as ill-defined
because `p_corrected` is a deterministic per-trial prediction, not a
Bernoulli draw, so it has no natural analogue to the empirical rate's
Wilson/normal CI — replaced with the plain `gap_corrected` vs.
`gap_naive` comparison as the sole primary criterion, with the empirical
rate's CI retained only as supporting uncertainty context, not a gate
condition. Everything else (still-clean-branch derivation, all-succeed
target, pair-0 fallback itself, fresh RNG namespace, 300,000 validation
trials, the 0.5× threshold, the non-goals, no-new-operating-point rule)
explicitly endorsed unchanged.

**Halt-and-Flag review round 1 (2026-08-24):** §2.1's key fact verified
directly against code, not assumed. `run_chain_boundary_noisy_m0trace`
(`photonics/run_photonic_m0_dynamic_range_sweep.py:47-92`) computes each
boundary's *next* `m[0]` as `pb._load_exp(rec[lane=0])` — from the
*recovered* value, not the oracle `qr`. `greedy_place`
(`photonics/run_photonic_compiler_regen_placement_sweep.py:60-89`, the
noiseless-trajectory walk `predicted_p_chain` is evaluated against)
computes it as `PhotonicQuadrayBackend._load_exp(qr[lane=0])` — the same
static method, applied to the exact oracle value. `g_ok = (rec == qr)`
is defined per-boundary in the noisy trace. **Confirmed: whenever
`g_ok`/`R_i = True`, `rec == qr` exactly, so both computations apply the
identical `_load_exp` method to identical inputs — the realized and
noiseless `m0_{i+1}` are bit-identical on the still-clean branch.** §2.1's
argument holds; no revision needed. Proceeding to §7 gates.

**Roles:**
- **Spec Author:** Claude, formalizing item #1 of the E18–E21 closure's
  agreed future-work order (`docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md`
  §5.1/§6, "priority order agreed 2026-08-24"): build the corrected joint
  (non-independent-events) whole-chain reliability model the E18–E21
  campaign named but explicitly did not attempt.
- **Halt-and-Flag Implementer:** review the model formulation (§2) before
  any code is written — specifically whether restricting the corrected
  estimate to the "still-clean" path (§2.2) is a legitimate simplification
  or silently changes what's being predicted, and whether the pair-0
  fallback (§2.3) needs a stronger caveat than proposed.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md` §1/§4 — the marginal law
  `p_event_fit(m0, sigma_det)` (`a=-4.79, beta=3.19`) and the naive
  product-of-marginals estimator `predicted_p_chain(m0_trace, sigma_det)`
  this contract corrects, both reused **verbatim, unmodified**
  (`photonics/run_photonic_compiler_regen_placement_sweep.py:34-58`); §4's
  flagged residual ("§1's law itself is measurably conservative in
  *magnitude*... e.g. `sigma_det=1e-5`: 0.721 predicted vs. 0.780
  observed") is the gap this contract tries to close.
- `docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md` §5.1 — "a corrected
  joint model would need to be built, which this campaign deliberately
  did not attempt" — the explicit, not-yet-filled gap this contract
  addresses. §4 (observability distinction) is why this model is
  compile-time-usable despite being calibrated on realized (not
  noiseless) `m0` — see §2.2.
- `contract_photonics_correlation_mechanism_2026-08-23.md` (E18) — the
  calibration data this contract reuses **without resimulation**: frozen
  `results/sweeps/correlation_mechanism_sweep_frozen_v1_2026-08-23.json`
  (sha256 `c12f8589f8d4a91337c379ff934bab4db6f34fcb2d09b12110781b9e02f576cf`),
  30 cells at fixed `M=2`, `K=16`, `sigma_det=3e-5`, 300,000 trials,
  giving `P(R_{i+1}=True | R_i=True, m0_{i+1})` and
  `P(R_{i+1}=True | R_i=False, m0_{i+1})` per `(pair_id, m0_bin)` cell.
  §8's non-goal — "no corrected recovery law built from this contract's
  findings — a separate, later, not-yet-authorized contract, contingent
  on finding real dependence" — is exactly what this contract now opens,
  since E18 found real dependence decisively (§10 there).
- `photonics/run_photonic_m0_dynamic_range_sweep.py`'s
  `run_chain_boundary_noisy_m0trace` — reused **verbatim**, already
  reused unmodified across E16/E17/E18; returns, per trial, the realized
  `(m0_i, R_i)` at every one of the 8 `M=2` group boundaries.

---

## 1. Objective

Build a whole-chain "all `K/M=8` groups recover exactly" probability
estimator, `P_chain_corrected`, that uses E18's measured `R_i → R_{i+1}`
dependence instead of assuming independence, and validate it directly
against real Monte Carlo whole-chain outcomes at the same operating
point E18 was calibrated at (`M=2`, `K=16`, `sigma_det=3e-5`). Falsifiable
question: **does `P_chain_corrected` predict the observed whole-chain
recovery rate materially better than the existing
`predicted_p_chain` (product-of-marginals) estimator, at the operating
point where both the correlation (E18) and the conservatism gap
(design-rule doc §4) were independently measured?**

## 2. Model formulation

### 2.1 Why "all-succeed" specifically, and why this stays tractable

The target quantity — `P(R_1 ∧ R_2 ∧ ... ∧ R_8)`, all groups recover
exactly — is exactly what `predicted_p_chain` already computes and
exactly the quantity whose conservatism gap was measured (design-rule
doc §4). This contract does **not** attempt to model the full
outcome distribution (e.g. "exactly 7 of 8 succeed") — non-goal, §6.

Restricting to this one event is what keeps the correction tractable
despite `m0_{i+1}` itself being realization-dependent (design-rule doc
§1: `m0` is re-derived from the recovered value's own bit-length, so a
corrupted recovery can produce a different `m0_{i+1}` than the
noiseless trajectory would). **Key fact, to be confirmed by the
Halt-and-Flag implementer before coding (not assumed):** conditional on
`R_i = True` (event `i` recovers *exactly*), the recovered value is
bit-identical to the noiseless value by definition, so the realized
`m0_{i+1}` on that branch equals the noiseless, compile-time-computable
`m0_{i+1}`. Any trial that fails even one event before the end
contributes 0 to "all succeed" regardless of what happens after — so
the "all succeed" probability only ever needs to walk the **still-clean
branch**, on which realized `m0` and noiseless `m0` coincide at every
step by the fact above. This is what makes a compile-time-usable
corrected estimator possible from data that was collected conditioned
on realized (not noiseless) `m0`.

### 2.2 Estimator

Given the noiseless `m0` trajectory `[m0_1, ..., m0_8]` for a fixed
`M=2` placement (computed the same way `greedy_place`'s noiseless walk
does, just against the fixed `M2_BOUNDARIES` list instead of a dynamic
threshold — reuse that bookkeeping, do not reimplement it):

```
P_chain_corrected(m0_trace, sigma_det) =
    p_event_fit(m0_1, sigma_det)
    * Π_{i=2}^{8} p_true_cell(pair_id=i-2, m0_bin=m0_i)
```

where `p_true_cell(pair_id, m0_bin)` looks up E18's frozen
`P(R_{i}=True | R_{i-1}=True, m0_bin)` from the reused cell table
(`p_true` field, `analysis.cells` in the frozen E18 JSON), falling back
to `p_event_fit(m0_i, sigma_det)` (§2.3) when no cell exists at that
`(pair_id, m0_bin)`. `p_event_fit(m0_1, sigma_det)` (the unmodified
marginal law) is structurally correct for the first group — it has no
predecessor to correlate with, not an approximation.

**Transition-mapping lock (Halt-and-Flag round 2, amendment 1):**
E18's `pair_id` convention, taken from its own §10 ("pair=1 (groups
2→3)", "pair 0 (groups 1→2)"), is `pair_id p` ⇒ groups `(p+1)→(p+2)`.
For this estimator's transition `i-1 → i` (`i=2..8`), the correct E18
lookup is therefore **`pair_id = i-2`**, exactly as written above — for
`i=2` (groups 1→2) that's `pair_id=0` (E18's known-empty pair, §2.3);
for `i=8` (groups 7→8) that's `pair_id=6`. This correspondence must be
asserted in code, not just documented here (e.g. a table/assertion
tying `i` to `pair_id` at driver init), so a transposition bug would
fail loudly rather than silently mis-attribute a cell — the exact class
of bug E21's ordered-replay gate was added to catch.

### 2.3 Known coverage gap — pair 0 has no calibration data

E18 §10 recorded explicitly: pair 0 (groups 1→2) never produced an
eligible cell at any binning resolution (`m0_2`'s distribution too
concentrated to populate both `R_1` states at `n_min=200`). The `i=2`
term therefore always falls back to the uncorrected marginal law. This
is a genuine limitation, not a bug: the corrected model is only
corrected where E18 produced data (pairs 1–6, `m0` bins 2/8/9/10/11/12
per E18 §10's table), and reduces to the naive model at pair 0 and at
any `m0_i` bin outside E18's observed range. **Report the achieved
correction as partial, not complete, and say so in the results section
explicitly — do not round up to "the gap is closed."**

**Reporting strengthened (Halt-and-Flag round 2, amendment 2):** internally
this is a **partially corrected** whole-chain estimator, not a fully
corrected one — one of the 7 transitions (pair 0, `i=2`) always uses the
marginal-law fallback, not an E18 cell. The driver must report, per run
(§4/§7 output), not just as a prose caveat: the count of the 7
transitions that resolved to an E18 cell vs. fell back to the marginal
law (aggregated across all trials, since which `m0_bin` a trial lands in
varies trial-to-trial even at a fixed `pair_id`), and which `pair_id`
values ever hit the fallback path. This lets the results section state
concretely how much of `mean(p_corrected)`'s movement away from
`mean(p_naive)` is attributable to genuine E18 correction vs. residual
uncorrected structure, rather than leaving that as an unquantified
caveat.

## 3. Locked parameters (reused from E18, not re-chosen)

- `M=2`, `K=16`, boundaries `[2,4,6,8,10,12,14,16]` (8 groups, 7 pairs).
- `sigma_det = 3e-5` (E18's already-searched, locked operating point —
  no new operating-point search in this contract; picking a different
  `sigma_det` would require new E18-style calibration data first, out
  of scope, §6).
- E18's frozen cell table, used read-only.
- New Monte Carlo trials use a **fresh RNG trial-offset namespace**,
  disjoint from both E18's search offset (`100,000,000+`) and E18's
  inference namespace (`0+`): use offset `300,000,000+` (SS3-style
  separation, so the validation set is not the same draws the
  correction was calibrated on — even though the correction's
  functional form is fixed, not fit to this data, keeping the sets
  disjoint avoids any argument that validation is circular).

## 4. New code (additive, minimal) — Halt-and-Flag review required

One new driver, `photonics/run_photonic_corrected_reliability_sweep.py`
(target ≤150 lines, Lithic):
1. Load E18's frozen JSON, build the `(pair_id, m0_bin) -> p_true` lookup
   (§2.2). No resimulation of E18.
2. Per trial (fresh RNG namespace, §3): draw a block, compute the
   noiseless `m0` trajectory at the fixed `M2_BOUNDARIES` (reuse the
   noiseless-walk bookkeeping already used by `greedy_place`, parametrized
   by a fixed boundary list instead of a threshold), and separately run
   `run_chain_boundary_noisy_m0trace` (verbatim reuse) for the realized
   outcome.
3. Per trial, compute `p_naive = predicted_p_chain(m0_trace, sigma_det)`
   (verbatim reuse), `p_corrected` (§2.2, new), and
   `all_recovered = all(R_i for the 8 realized groups)`.
4. Aggregate and report: `mean(p_naive)`, `mean(p_corrected)`,
   `empirical_rate = mean(all_recovered)` with a Wilson or normal-approx
   CI on the empirical rate (same toolkit E16/E18 already use);
   `gap_naive`, `gap_corrected`, `gap_corrected / gap_naive`; total
   trial count and empirical all-succeed count; and, per §2.3's
   amendment-2 requirement, the count (across all trials × all 7
   transitions) resolving to an E18 cell vs. falling back, broken out by
   `pair_id`.

## 5. Falsification criteria (non-vacuous)

Let `gap_naive = |mean(p_naive) − empirical_rate|` and
`gap_corrected = |mean(p_corrected) − empirical_rate|`. **Primary
criterion is the plain gap comparison below (Halt-and-Flag round 2,
amendment 3) — no "own dispersion band" condition on `p_corrected`:**
`p_corrected` is a deterministic per-trial prediction (a function of
that trial's noiseless `m0` trajectory only), not a Bernoulli draw, so
it has no natural analogue to `empirical_rate`'s Wilson/normal CI; an
overlap-with-a-dispersion-band condition on it would be ill-defined and
could read differently depending on how "dispersion" is computed after
the fact. `empirical_rate`'s CI (§4) is retained and reported, but as
*supporting uncertainty context only*, not as part of any gate:

- **Model closes the gap (materially):** `gap_corrected ≤ 0.5 × gap_naive`.
- **Model partially helps:** `gap_corrected < gap_naive` but the 50%
  bar above is not met — report the actual ratio, do not round up.
- **Model does not help:** `gap_corrected ≥ gap_naive`.
- **Model actively wrong (distinct, worse failure mode — flag loudly if
  seen):** `mean(p_corrected)` exceeds `empirical_rate`'s CI upper bound
  (§4) by a material margin, i.e. the correction overshoots into
  *non-conservative* territory — unlike naive's conservative-only bias,
  an over-corrected model that overestimates reliability would be
  unsafe to use for margin-setting and should be reported as a reason
  **not** to adopt this estimator, not just a smaller partial win. (This
  is the one place `empirical_rate`'s CI legitimately gates a
  conclusion — bounding *how* wrong the correction would have to be to
  count as "actively wrong," not judging `p_corrected` against its own
  dispersion.)

All of `mean(p_naive)`, `mean(p_corrected)`, `empirical_rate`, and the
transition-coverage counts (§2.3) are computed once at the full run's
sample size and are not to be re-examined or re-binned after being seen
(no post-hoc threshold adjustment).

## 6. Non-Goals

- **No σ_det-general or M-general law.** Single operating point
  (`M=2`, `K=16`, `sigma_det=3e-5`), matching E18's calibration exactly.
  Generalizing to a continuous `(m0, sigma_det)` correction analogous to
  §1's marginal law would need new calibration sweeps at multiple
  `sigma_det`/`M` values — a separate, later contract, not attempted
  here.
- **No change to `greedy_place`/`optimal_placement`.** Those use
  `predicted_p_chain` as an optimization *objective*; whether to swap in
  a corrected objective is a separate decision, contingent on this
  contract's result, not made here (design-rule doc §5.2 already
  established the placement *ranking* result is unaffected by the
  correlation's existence — this contract is about estimate accuracy,
  not placement choice).
- **No modeling of partial-failure outcomes** (e.g. `P(exactly 7 of 8
  succeed)`) — all-succeed only (§2.1).
- **No investigation of the two PARKED §6 hypotheses from the E18–E21
  synthesis** (arithmetic/structural mechanism, actual corrupted
  values) — this contract uses E18's association empirically, it does
  not explain it.
- **No RTL or silicon claim.** Simulation-only, same discipline as every
  document in this chain.
- **No resimulation of E18.** Its frozen cell table is read-only input.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 1. Smoke pass (cost sanity check; report actual wall-clock, extrapolate)
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=2000 .venv/bin/python3 \
  photonics/run_photonic_corrected_reliability_sweep.py

# 2. Full run: 300,000 trials (matches E18's inferential sample size),
#    fresh RNG offset (300,000,000+, SS3 separation from E18's own
#    namespaces)
.venv/bin/python3 photonics/run_photonic_corrected_reliability_sweep.py

# 3. Reproducibility: two full runs, bit-identical (sha256 match)

# 4. Aggregate analysis per SS5 -- report gap_naive, gap_corrected, the
#    tier from SS5, and the pair-0/coverage-gap caveat (SS2.3) explicitly

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Stop conditions

- If the Halt-and-Flag review of §2.1's "still-clean branch" argument
  finds it does **not** hold (e.g. if `run_chain_boundary_noisy_m0trace`
  turns out to define `m0_{i+1}` some other way that doesn't coincide
  with the noiseless value on the `R_i=True` branch), **halt before
  writing the driver** — the whole estimator in §2.2 depends on that
  fact.
- If the smoke pass (gate 1) shows the full run would cost materially
  more than E18's own ~11-minute extrapolation at comparable trial
  count, halt and report before running gate 2 rather than silently
  reducing `n_trials`.

## 9. Results (2026-08-24) — RAN TO COMPLETION. RESULT: gap reduced 71%
## by point estimate, but disqualified by the over-correction gate.

**All gates passed.** Smoke pass (gate 1, 2,000 trials, amended driver):
~4s, extrapolated well under E18's own ~11-minute full-run budget — no
scope reduction needed. Full run (gate 2, 300,000 trials, fresh RNG
offset `300,000,000+`): ~9 minutes wall-clock. Reproducibility (gate 3):
two full runs, bit-identical, sha256
`047154a6cd83ea5972f8efe543289c984a4bb21340f357d92239f1ee495c035c`.
Repository regression (gate 5): `bash tools/verify_repo.sh` — see below.

**Headline numbers (N=300,000):**

| quantity | value |
|---|---|
| `mean_naive` (product-of-marginals) | 0.1361 |
| `mean_corrected` (this contract's estimator) | 0.1258 |
| `empirical_rate` (real whole-chain Monte Carlo) | 0.1217 |
| `empirical_rate` 95% CI | `[0.1206, 0.1229]` |
| `gap_naive` | 0.0143 |
| `gap_corrected` | 0.0041 |
| `gap_corrected / gap_naive` | 0.287 |

By the raw point-estimate comparison alone, `gap_corrected ≤ 0.5 ×
gap_naive` is satisfied with room to spare (0.287 ≪ 0.5) — the
correction moves the estimate 71% of the way from naive to truth.
**But this contract's tier logic (§5) does not stop at that comparison,
and the second, distinct gate is the one that actually fires:**
`mean_corrected` (0.1258) lies *above* `empirical_rate`'s own 95% CI
upper bound (0.1229) — a statistically real overshoot at this sample
size, not noise. Per §5, this is classified **"Model actively wrong
(over-corrected, non-conservative)"**, not "closes the gap." This tier
exists precisely because a closer-but-wrong-direction estimate is a
worse engineering failure mode than the naive model's known
conservative bias: naive's error is safe to build margin around;
this correction's error is not.

**Transition coverage (the round-2 amendment's diagnostic, and the
leading hypothesis for the overshoot — not yet demonstrated):**

| `pair_id` | groups | used E18 cell | fell back |
|---|---|---|---|
| 0 | 1→2 | 0 | 300,000 (100%) |
| 1 | 2→3 | 299,965 | 35 |
| 2 | 3→4 | 298,309 | 1,691 |
| 3 | 4→5 | 298,162 | 1,838 |
| 4 | 5→6 | 298,229 | 1,771 |
| 5 | 6→7 | 298,409 | 1,591 |
| 6 | 7→8 | 299,143 | 857 |

`pair_id=0` is uncorrected in every single trial (E18 §10's known
coverage gap, §2.3), while every other transition resolves to a real
E18 cell 99%+ of the time. This is exactly the shape of evidence §2.3
asked for: the model is not "mostly corrected with a small caveat" — it
is fully corrected on 6 of 7 transitions and *entirely* uncorrected on
exactly one. **State this precisely, not as a finding:** pair 0 being
the sole uncorrected transition is a **leading hypothesis for the
overshoot, not a demonstrated cause.** This contract isolates the
coverage asymmetry (a fact) but ran no follow-on experiment that varies
or removes pair 0's contribution to test whether it is actually
responsible — such an experiment (e.g. new calibration data at pair 0,
or an ablation re-running §2.2 with pair 0 excluded to see if the
overshoot shrinks) is a **parked future investigation, not authorized
by this contract and not opened here.**

**Interpretation.** This is a genuine, informative result, not a
failed experiment: E18's measured `R_i→R_{i+1}` dependence is real and
does carry predictive information (the 71% point-estimate gap
reduction is itself evidence the dependence is not spurious or
noise-dominated), but a correction built from *partial* coverage of
that dependence (6 of 7 transitions) is not automatically safe to
adopt — it can overshoot past the true value specifically because of
the transition(s) it *couldn't* correct, not despite them. The
architectural lesson generalizes beyond this one estimator: **local
conditional dependence can carry real predictive information while a
naive composition of locally calibrated conditional probabilities is
still non-conservative at the whole-chain level.** That is a
reliability-modeling result in its own right, independent of whether
this specific estimator is ever fixed.

**Engineering conclusion (three-way, explicit):**

| | estimator | status | reason |
|---|---|---|---|
| **Current production/design-rule estimator** | `predicted_p_chain` (naive, product-of-marginals) | **Adopted** | Conservative, independently validated (design-rule doc §1/§4), safe for margin-setting — its known bias is in the safe direction. |
| **Corrected conditional estimator** | `corrected_p_chain` (this contract, §2.2) | **Research-only, not adopted for design use** | Substantially more accurate point estimate (71% gap reduction) but demonstrated non-conservative at N=300,000 — the wrong-direction failure mode for a reliability estimator. |
| **Pair-0 calibration / partial-coverage fix** | not built | **Parked future investigation, not authorized** | Leading hypothesis for the overshoot (above), not a scoped or opened experiment. Do not treat this table's existence as authorization to start it. **Update 2026-08-24 (John-authorized Phase 0 only, `contract_photonics_pair0_calibration_2026-08-24.md`):** a cheap sensitivity check confirmed the hypothesis is quantitatively viable (exact viable range `p_hat_0∈[0.7173,0.7312]`, plausible, not extreme) — not ruled out, still not demonstrated. Phase 1 (actual calibration) remains unauthorized. |

This result and estimator are preserved as a completed, evidenced
experiment (not discarded because it wasn't adopted) — the frozen
artifact and this write-up are the record that the dependence was real,
that a straightforward exploitation of it was tried in good faith, and
that it was correctly rejected by its own pre-registered gate rather
than quietly adopted on the strength of a better-looking point
estimate.

**Evidence artifact:**
`results/sweeps/corrected_reliability_sweep_frozen_v1_2026-08-24.json`,
sha256 `047154a6cd83ea5972f8efe543289c984a4bb21340f357d92239f1ee495c035c`
(README entry added). Driver:
`photonics/run_photonic_corrected_reliability_sweep.py`.
