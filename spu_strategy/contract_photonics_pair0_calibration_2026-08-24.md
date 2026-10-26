# Engineering Contract: Pair-0 Calibration Follow-Up

**Date:** 2026-08-24
**Contract ID:** `contract_photonics_pair0_calibration_2026-08-24.md`
**Status:** PHASE 0 RAN TO COMPLETION 2026-08-24 (John-authorized).
**Phase 1 remains NOT authorized** — see §4 for the corrected Phase 0
result and why it doesn't change that.

**Phase 0 headline result (§4 for full write-up):** pair-0's missing
calibration **is quantitatively viable** as an explanation for the
corrected-reliability-model's overshoot — a plausible, non-extreme
hypothetical correction factor (exact range `[0.7173, 0.7312]`) would
close the gap. This reverses an initial, incorrect "not viable" reading
caused by a too-coarse sweep grid, caught and fixed before being
reported (§4). Separately, `R_1` failed **zero times in 300,000
trials**, confirming the rare-event-sampling mechanism (§3(a)) but
showing the naive fix ("more trials at the same `sigma_det`") is likely
impractical — see §4's revised Phase 1 cost read.

**Original scoping status (2026-08-24, before Phase 0 ran), preserved
for context:** SCOPED ONLY, not authorized to execute. Per the standing
rule this branch adopted the same day
(`docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` preamble): "an unanswered
question authorizes a new experiment only when it blocks an engineering
decision, not merely because it is unanswered." Nothing currently
adopted (`predicted_p_chain`, conservative) needs pair-0 calibration to
function. This document exists so that *if* a real engineering decision
ever does need it, the design work doesn't have to be redone from
scratch — not as a queued-up next step.

**Roles (for if/when authorized):**
- **Spec Author:** Claude, formalizing the "leading hypothesis, not
  demonstrated" follow-on flagged in
  `contract_photonics_corrected_reliability_model_2026-08-24.md` §9 and
  explicitly parked there and in
  `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md` §6.
- **Halt-and-Flag Implementer:** review Phase 0's design (§2) before
  Phase 1 is even considered — the whole point of the two-phase split
  is that Phase 1 (real new calibration data) should not be authorized
  by default, only if Phase 0 shows the hypothesis is quantitatively
  capable of explaining the overshoot.
- **Integration Auditor:** unchanged discipline if either phase ever
  runs — reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_corrected_reliability_model_2026-08-24.md` §9 —
  the finding this follows on from: `pair_id=0` falls back to the
  uncorrected marginal law in 100% of the 300,000 validation trials (the
  only transition with zero E18 coverage), and the corrected estimator
  overshot the empirical rate's 95% CI. "Leading hypothesis for the
  overshoot, not demonstrated."
- `contract_photonics_correlation_mechanism_2026-08-23.md` (E18) §10 —
  the original finding: "pair 0 (groups 1→2) never produced an eligible
  cell at any binning resolution... `m0_2`'s distribution too
  concentrated to populate both `R_1` states at `n_min=200`" at
  `sigma_det=3e-5`, 300,000 trials. **This contract's Phase 1 Gate 0
  needs to establish *why* — see §3.**

---

## 1. Objective (stated precisely, scope limited)

Two questions, kept explicitly separate because they have very different
costs:

- **Phase 0 (cheap, no new random data):** *is pair-0's miscalibration
  even quantitatively capable of explaining the corrected model's
  overshoot* (`mean_corrected=0.1258` vs. `empirical=0.1217`,
  `contract_photonics_corrected_reliability_model_2026-08-24.md` §9)?
  If sweeping the assumed pair-0 correction factor across every
  plausible value never brings `mean_corrected` back inside the
  empirical CI, pair 0 is **not** a sufficient explanation and Phase 1
  is not worth authorizing regardless of cost.
- **Phase 1 (real cost, new calibration data — contingent on Phase 0):**
  actually measure `P(R_2=True | R_1, m0_2)` at adequate sample size,
  substitute it for the marginal-law fallback, and re-validate the
  corrected estimator on a fresh sample.

## 2. Phase 0 — sensitivity/attribution check (design)

**Method:** the existing driver
(`photonics/run_photonic_corrected_reliability_sweep.py`) does not
persist per-trial state — only aggregates. Phase 0 needs one small,
additive change: store, per trial, `(m0_1, m0_2, all_recovered)` (three
numbers; the rest of the trial's state is not needed for this specific
sensitivity check) instead of only aggregate sums. This is a
**re-instrumentation of the existing driver, not a new experiment
design** — same trials, same RNG namespace (`300,000,000+`), same
operating point; a genuinely fresh Monte Carlo run is not required if a
prior run's per-trial log is reusable, but the existing frozen run did
**not** log per-trial data, so one **new run at the existing, already-
characterized cost (~9 minutes, 300,000 trials)** is needed regardless —
this is data collection with logging added, not a new question being
asked of the simulator.

**Analysis (pure post-processing once collected, no resimulation):**
for a swept range of hypothetical pair-0 correction values
`p_hat_0 ∈ [0, 1]` (e.g. 21 points, step 0.05), recompute
`mean_corrected(p_hat_0) = mean over trials of [p_event_fit(m0_1,sigma_det) ·
p_hat_0 · Π_{i=2}^{6} p_true_cell(...)]` — i.e. replace only the pair-0
factor with the swept value, holding every other (already-calibrated)
factor exactly as the frozen estimator computes it. Plot/report
`mean_corrected(p_hat_0)` against `empirical_rate`'s 95% CI.

**Phase 0 decision gate (pre-registered, not adjusted after seeing
results):**
- **Pair-0 hypothesis quantitatively viable:** some `p_hat_0` in a
  *plausible* range (i.e. not requiring `p_true(pair 0) ≈ 0` or `≈ 1`,
  which would itself be implausible given every other pair's calibrated
  value falls well inside `(0, 1)`) brings `mean_corrected(p_hat_0)`
  inside `empirical_rate`'s CI. → Phase 1 becomes a *candidate* for
  authorization (still not automatic — see §4).
- **Pair-0 hypothesis not viable:** no plausible `p_hat_0` closes the
  gap, or the required value is itself implausible (near 0 or 1). →
  Phase 1 should **not** be authorized; the overshoot has a different,
  unidentified cause, and that's a new, separate question — not a
  reason to reopen this one with a bigger experiment.

**Cost:** one ~9-minute simulation run (re-instrumented driver) plus
trivial post-processing. Far cheaper than Phase 1.

## 3. Phase 1 — real pair-0 calibration (contingent, design only)

**Only scoped, not authorized, and only worth considering if Phase 0
passes its gate (§2).** Even then, requires its own Halt-and-Flag round
before running — this section is not pre-authorization, it's so the
design doesn't have to be redone from zero later.

**Open sub-question Phase 1's own Gate 0 must resolve first:** *why*
does pair 0 fail to populate both `R_1` states? Two different
mechanisms, needing different fixes:
- **(a) Rare-event sampling problem:** `R_1` (recovery of the very
  first REGEN group, minimal accumulated noise, small `m0_1`) may
  simply succeed at very high marginal probability by construction of
  the physics — `R_1=False` is intrinsically rare at any trial count,
  not a binning artifact. If so, the fix is **more trials at the same
  `sigma_det=3e-5`** (a cost question, not a design question), or
  accepting a coarser statistical bar for this one cell.
- **(b) Genuine distributional concentration in `m0_2`:** the
  *bins* are the problem, not the `R_1=False` count — but E18 §10
  already reports the binning hierarchy (exact→width2→width4→exclude)
  was exhausted without success, which argues against this being purely
  a binning-resolution issue and *for* (a) — **not established, needs
  a two-line numerical check before Phase 1 proceeds:** report `R_1`'s
  marginal `n_true`/`n_false` counts alone (ignoring `m0_2` entirely)
  from the Phase 0 re-instrumented run's data — if `n_false` is itself
  under `n_min=200` in the *raw*, unbinned count, that settles it as
  (a) without needing any new experiment design.

**If (a):** Phase 1 is "run N trials at `sigma_det=3e-5`, `N` chosen so
`n_false ≥ 200`" — a straightforward cost-scaling question, no new
operating-point search needed (§3's own math: if `R_1=False` occurs at
rate `r`, need `N ≈ 200/r` trials; `r` is directly computable from the
Phase 0 run's own `n_false/N` once collected).

**If (b) turns out to be the actual mechanism after Phase 0's numerical
check (contrary to the current reading of E18 §10):** Phase 1 would need
its own operating-point search (a new `sigma_det`, disjoint from every
other pair's calibration point) — a materially bigger, separately-
scoped piece of work not designed here, because it would also need to
determine whether recalibrating pair 0 at a *different* `sigma_det` than
pairs 1–6 is even a coherent thing to substitute into the shared
estimator (§2.2 of the corrected-reliability-model contract implicitly
assumes one shared operating point across all 7 transitions).

## 4. What authorizing Phase 1 would actually require

Not decided here. At minimum: Phase 0 passing its gate (§2), Phase 1's
own Gate 0 resolving (a) vs. (b) (§3), a fresh Halt-and-Flag round on
whatever design (a) or (b) implies, and — separately from all of the
above — an actual engineering reason the conservative `predicted_p_chain`
estimator is insufficient for some concrete use (per the standing rule,
this contract's own existence does not supply that reason).

## 5. Non-goals

- **Not authorized to run anything, Phase 0 or Phase 1**, per the
  Status line. This is scope only.
- **No change to the adopted estimator** (`predicted_p_chain`) regardless
  of Phase 0/1 outcome — even a fully successful Phase 1 would produce a
  *candidate* corrected estimator requiring its own full re-validation
  (reproducibility, fresh sample, the "actively wrong" gate) before any
  adoption question — this contract does not pre-approve that either.
- **No new operating-point search designed for case (b)** — flagged as
  needing its own scoping if it turns out to be the actual mechanism,
  not designed here.
- **No investigation of the two other still-parked E18–E21 hypotheses**
  (arithmetic/structural mechanism, actual corrupted values) — unrelated
  to pair 0, still parked separately.

## References

- `contract_photonics_corrected_reliability_model_2026-08-24.md` §9 —
  the overshoot finding and pair-0 coverage table this follows on from.
- `contract_photonics_correlation_mechanism_2026-08-23.md` (E18) §10 —
  the original pair-0 exclusion finding.
- `docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` preamble — the "experiment
  only if it blocks a decision" rule this contract's Status line applies.
- `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md` §6 — pair-0 listed there as
  parked, not authorized; unchanged by this document.

## 4. Phase 0 results (2026-08-24, John-authorized, RAN TO COMPLETION)

**Driver:** `photonics/run_photonic_pair0_sensitivity_check.py`. Same
trial sequence as the corrected-reliability-model contract (`SEED`,
`TRIAL_OFFSET=300,000,000+`, `sigma_det=3e-5`, `M=2`, `K=16`,
300,000 trials) — a fresh, disjoint-from-E18 replay, not new random
data beyond what §2 already specified.

**Mid-course correction, caught before reporting (not after — no result
was shown to John before this was fixed):** the first full run used a
discrete 0.05-step grid over `p_hat_0 ∈ [0,1]` and reported **no**
grid point landing inside `empirical_rate`'s 95% CI — an apparent "not
viable" verdict. Because `mean_corrected(p_hat_0) = p_hat_0 · mean_base`
is *exactly* linear (§2's own design), the true viable range can be
solved in closed form rather than read off a grid: `[ci_lo/mean_base,
ci_hi/mean_base]`. The CI's width (`≈0.0023`) is narrower than one grid
step's swing in `mean_corrected` (`≈0.0084`), so the grid could — and
did — straddle a real, non-degenerate viable window without ever
landing a sample point inside it. Fixed by replacing the grid-based
viability check with the exact analytical range (grid retained only as
an illustrative printout); re-verified smoke-scale, then re-run at full
scale. This is the same class of error the campaign's discipline
(`[[controlled-mechanism-experiment-template]]`) exists to catch —
caught here by re-deriving the exact relationship the driver itself was
built on, not by a fresh review pass.

**Result (N=300,000, reproducibility bit-identical across two full
runs, sha256 `bb6042d647e62073e2e19877664820e062f948fdf897b52184d14241c601fd5b`):**

| quantity | value |
|---|---|
| `mean_base` (corrected estimator excluding pair-0's factor) | 0.168084 |
| `empirical_rate` | 0.1217 |
| `empirical_rate` 95% CI | `[0.1206, 0.1229]` |
| exact viable `p_hat_0` range | `[0.7173, 0.7312]` |
| `R_1` marginal | `n_true=300,000, n_false=0` |

**Verdict: Pair-0 hypothesis is quantitatively viable.** `[0.7173,
0.7312]` is nowhere near the near-0/near-1 implausibility bound (§2's
own pre-registered check) — it's an ordinary-looking probability, in
the same rough neighborhood as the *current* marginal-law fallback
value the estimator already uses there (back-of-envelope: the original
corrected-reliability-model's `mean_corrected=0.1258` implies an
effective average fallback around `0.1258/0.168084 ≈ 0.75` — so the
viable range is a modest, plausible **downward** correction from what
the naive law currently assumes, not an extreme swing). **This does not
demonstrate pair 0 is the actual cause — it demonstrates the hypothesis
survives the cheapest test that could have killed it.** Per §2's own
pre-registered gate, this makes Phase 1 a *candidate* for authorization,
not automatically authorized (§4 below on why the practical picture is
more complicated than "just calibrate it").

**`R_1` marginal (`n_false=0/300,000`) — cleanly confirms mechanism (a)
from §3, but complicates rather than simplifies Phase 1's cost:** zero
failures in 300,000 trials is not "rare," it's "not observed at this
sample size at all" — the true failure rate could be anywhere from
`~1/300,000` down to vanishingly small, and this run cannot distinguish
those. §3(a)'s proposed fix ("more trials at the same `sigma_det`") is
therefore **not obviously practical**: reaching `n_min=200` `R_1=False`
events could require anywhere from ~60M trials (if the true rate is
close to the largest value consistent with zero observed failures) to a
computationally infeasible number (if it's much smaller). §3(b) (a
different, higher-`sigma_det` operating point specifically to elevate
`m0_1`'s failure rate) now looks like the *more* practical path if
Phase 1 is ever pursued, despite the mechanism being (a) not (b) — a
distinction this contract's original §3 conflated by treating "which
mechanism" and "which fix is cheap" as the same question. **Not
resolved here** — Phase 1 remains unauthorized and this refinement is
recorded for whoever scopes Phase 1 next, not acted on now.

**Evidence artifact:**
`results/sweeps/pair0_sensitivity_check_frozen_v1_2026-08-24.json`,
sha256 `bb6042d647e62073e2e19877664820e062f948fdf897b52184d14241c601fd5b`
(README entry added).

**Phase 1 status, unchanged by this result:** still not authorized. A
viable-but-not-demonstrated hypothesis is exactly what §2's gate was
designed to produce as one of its two possible outcomes — it is a
reason Phase 1 *could* be proposed later with its own full Halt-and-Flag
round (§3's cost picture now needs revising per above), not a reason to
proceed now.
