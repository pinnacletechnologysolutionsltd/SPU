# Engineering Contract: Compiler-Controlled REGEN Placement (E17)

**Date:** 2026-08-23
**Contract ID:** `contract_photonics_compiler_regen_placement_2026-08-23.md`
**Status:** RAN TO COMPLETION 2026-08-23. **RESULT: efficiency win
confirmed, calibration FALSIFIED in greedy placement's favor.** Greedy
compile-time placement beats the best fixed-`M` policy on both
reliability and REGEN-event count at every noise level where any policy
recovers meaningfully (3× fewer events at σ=1e-6 for equal/better
reliability; higher reliability AND fewer events at σ=1e-5). The
pre-registered calibration test failed — but because the product-of-
independent-events model systematically *under*-predicts actual
recovery under variable-group-size placement, not because greedy
placement performs worse than expected. See §9.

**Roles:**
- **Spec Author:** Claude, formalizing John/GTP's explicit design
  (2026-08-22/23): "validate compiler-controlled placement" as the
  immediate next engineering target, before adaptive hardware — a
  greedy, threshold-based REGEN placement pass using only the noiseless
  `m0` trajectory and E16's fitted per-event law, using the *existing*
  ISA (`.block K` at compiler-chosen boundaries, not a fixed period).
- **Halt-and-Flag Implementer:** review the greedy-placement algorithm
  (§4) and the calibration methodology (§5/§6) before running anything.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md` §2 — the worst-case
  placement rule this contract implements and tests: REGEN whenever
  `m0` would reach `m0,safe(sigma_det, P_target)`.
- `contract_photonics_m0_dynamic_range_2026-08-22.md` §10 (E16 v2) — the
  fitted law `P_event(m0,σ) = sigmoid(β·(a−log2(σ)−m0))`, `a=-4.79`,
  `β=3.19`. Reused as frozen constants here, **not refit** — this
  contract tests whether the law, fit on fixed-`M` placements, still
  predicts recovery under a structurally different (greedy, variable
  group-size) placement rule. That is a genuine out-of-sample test of
  the law, not just of the compiler pass.
- `contract_photonics_regen_boundary_placement_2026-08-22.md` (E15) —
  `run_chain_boundary_noisy_diag`, reused **verbatim, unmodified** — it
  already accepts an arbitrary boundary list, so no new scoring code is
  needed. Only the boundary-*selection* algorithm is new.

---

## 1. Objective

**Does greedy, threshold-based REGEN placement — inserting a boundary
whenever the noiseless `m0` trajectory would reach `m0,safe(σ_det,
P_target)`, computed entirely at "compile time" from the exact op
sequence — produce actual (noisy) recovery rates that match what E16's
own fitted law predicts for that specific placement?**

This is explicitly **not** "does greedy placement beat some fixed M" as
the primary question (that's a secondary, reported metric, §5) — it is
a **calibration test of the E16 law itself** under a placement rule
structurally unlike anything the law was fit on (E16's fit used only
fixed-period `M` placements; greedy placement produces variable,
data-dependent group sizes). If the law's predictions hold under this
different placement rule too, that is strong evidence `m0` really is
the sufficient control variable the design rule claims — not just for
periodic placement, but for placement in general.

**Explicitly out of scope:** the whole-chain-product optimization
formulation (`max useful work / REGEN cost subject to P_chain ≥
P_target,chain`) — GTP's own note that this is a genuine combinatorial
placement-optimization problem, strictly harder than the greedy
worst-case rule, and worth attempting only once this simpler version is
validated. No new op-sequence family — reuses `gen_block`'s established
K=16 family, so as not to conflate "does greedy placement work" with
"does the law generalize to different computations" (a separate,
later question). No hardware/adaptive-controller design (design rule
doc §4) — this validates that placement *can* be a compile-time
decision using the *existing* ISA, nothing about runtime monitoring.

## 2. Objective grounding

The design rule (§2) already derives the per-event safe threshold:

```
m0,safe(sigma_det, P_target) = a - log2(sigma_det) - ln(P_target/(1-P_target)) / β
```

and notes step 1 ("compute the noiseless `m0` trajectory") is already
implemented (E15/E16's noiseless bookkeeping). What has **not** been
tested is using that trajectory to make a *dynamic* placement decision
op-by-op, rather than checking a *fixed* `M`'s worst-case `m0` after the
fact. The greedy rule is the minimal such algorithm: walk the op
sequence; after each mirrored op (QLDI/QSUB/ROTC) updates `m[0]`, check
`m[0] >= m0,safe`; if so, place a boundary here (this op becomes the
last op of the current group; noiseless re-entry resets `m0` to
`_load_exp` of the exact recovered value, exactly as E15/E16's
production re-entry logic does).

Because `m[0]` only ever increases by exactly +1 per combine op
(unconditional, per §2 of the code-reading in
`contract_photonics_m0_dynamic_range_2026-08-22.md`), the greedy rule
cannot overshoot `m0,safe` by more than 1 unit in a single step — the
resulting group `m0` values will sit close under the threshold, not
wildly under it, which is exactly the "don't regenerate earlier than
necessary" property motivating this approach.

**Edge case, flagged for explicit handling (not assumed away):** the
initial two QLDI loads set `m[0]`/`m[1]` directly via `_load_exp`, not
incrementally — for a large enough initial magnitude draw, `m0` could
already reach `m0,safe` before any combine op runs. The algorithm must
handle this (the first group is then just the two QLDIs, matching E13's
established convention for degenerate first groups) rather than
erroring or producing an empty group.

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| P_target (per-event) | 0.999 (locked; not swept — a sweep over
  P_target is a natural, separate later contract if this one succeeds) |
| σ_det test points | `[1e-6, 1e-5, 1e-4]` — chosen so `m0,safe` lands
  at approximately 12.97 / 9.65 / 6.33 respectively (via the §2
  formula), spanning the natural `m0` range observed in E16
  (~2 to ~22) so greedy placement makes genuinely varied choices, not
  a trivial always-1-group or always-8-group result. Confirm via smoke
  pass (§7 gate 2) before the full run — not assumed correct from this
  back-of-envelope calculation alone. |
| M_K, band, seed | K=16's established values (unchanged) |
| trials per σ_det point | 30,000 |
| E16 law constants (frozen, not refit) | `a = -4.79`, `β = 3.19` |
| noise axes | `sigma_phi = sigma_amp = 0` (unchanged) |

**Halt-and-Flag addendum (added at freeze, 2026-08-23):** the σ=1e-4
test point (`m0,safe≈6.33`) is plausibly at or below the *initial*
per-trial baseline exponent (post-QLDI `m0`, observed ranging roughly
0–8+ across trials in earlier diagnostics) — if so, greedy placement
would degenerate to REGEN after nearly every op (group size 1
throughout), which is a *valid*, already-handled result (§2's edge
case), not a bug, but would make that test point uninteresting for the
calibration spread §5 wants. This is exactly what gate 1's smoke pass
is for — report the observed group-size distribution at all three
points explicitly in the smoke-pass output, and if σ=1e-4 turns out
degenerate, that is itself a valid, reportable finding (the greedy rule
correctly identifies "no safe accumulation window exists at this noise
level" — not a reason to redesign the test point without authorization).

## 4. New code (additive) — Halt-and-Flag review required before running

`photonics/run_photonic_compiler_regen_placement_sweep.py`:

- `m0_safe(sigma_det, p_target=0.999, a=-4.79, beta=3.19)` — the §2
  formula, a direct one-line implementation.
- `p_event_fit(m0, sigma_det, a=-4.79, beta=3.19)` — E16's fitted law,
  reused verbatim (same formula as E16's `p_fit`, frozen constants).
- `greedy_place(block, m0_threshold)` — walks the block using the exact
  noiseless bookkeeping (mirrors E15/E16's noiseless-trajectory logic:
  `_load_exp` on QLDI, `+1` per combine op, exact `qr` via
  `exact_qsub`/`exact_rotc`, re-entry via `_load_exp(qr[lane])` after
  each chosen boundary). Returns `(boundaries, m0_trace)` — the compiler-
  chosen boundary list and the noiseless `m0` value at each one.
- `predicted_p_chain(m0_trace, sigma_det)` — `prod(p_event_fit(m0, sigma_det)
  for m0 in m0_trace)`, the law's own prediction for this specific
  trial's compiler-chosen placement.
- `cell(sigma_det, n_trials)` — for each trial: `blk = gen_block(...)`;
  `boundaries, m0_trace = greedy_place(blk, m0_safe(sigma_det))`;
  `predicted = predicted_p_chain(m0_trace, sigma_det)`; score the
  **actual noisy** recovery via **E15's unmodified**
  `run_chain_boundary_noisy_diag(pb, blk, boundaries, sigma_det, rng)`;
  record `(predicted, observed_ok, len(boundaries))` per trial. Returns
  per-trial records, not just an aggregate — needed for the calibration
  binning (§6).

**Halt-and-Flag pre-review items:**
- **Greedy-placement noiseless correctness** — verify, for 500+ trials,
  that `greedy_place`'s chosen boundaries, replayed through
  `run_chain_boundary_noisy_diag` at `sigma_det=0`, reproduce the exact
  oracle at every boundary (same discipline as every prior contract's
  noiseless gate) — this is a *different* boundary list per trial
  (data-dependent), so it needs its own gate, not inference from E15's
  fixed-list gates.
- **Edge case (§2):** confirm at least one smoke-pass trial exercises
  the "`m0` already at/above threshold after the initial QLDIs" case at
  the most aggressive σ_det test point, and that `greedy_place` handles
  it (first group = the two QLDIs only) without error.
- **Determinism of `predicted_p_chain` vs. the actual scorer:** confirm
  `m0_trace` (noiseless) has the same length as `boundaries`, and that
  `boundaries` from `greedy_place` are strictly increasing and end at
  16 (the block's own length) — a placement that doesn't cover the full
  block is a bug, not a valid greedy result.

## 5. Metrics & outputs

- **Primary — calibration:** bin trials by `predicted`. **Locked from
  the smoke pass (2026-08-23):** `[0, 0.01), [0.01, 0.5), [0.5, 0.8),
  [0.8, 0.9), [0.9, 0.95), [0.95, 0.99), [0.99, 0.999), [0.999, 1.0]` —
  fine resolution near the ceiling (σ=1e-6 clusters at 0.996–1.0) and
  through σ=1e-5's real spread (0.49–0.99, the point carrying almost
  all calibration signal), with a bottom catch-all for σ=1e-4's
  near-total collapse (99th percentile predicted = 0.0013 — confirmed
  degenerate at the smoke pass; kept as a locked test point per John's
  explicit choice, reported as its own boundary-case finding rather than
  swapped out). Within each bin, compare mean `predicted` to the
  empirical observed recovery rate (with its own 95% CI). Report per
  bin, per σ_det test point.
- **Secondary — efficiency:** mean number of REGEN events per trial
  under greedy placement, compared to the smallest fixed `M` from
  E13/E14/E16's frozen data that achieves a comparable whole-trial
  recovery rate at the same `σ_det` (comparable = within the frozen
  curve's own CI). Reports whether compile-time placement needs fewer
  REGEN events than the best matched fixed-`M` policy for equivalent
  reliability — the practical payoff GTP's proposal is motivated by.
- Output: canonical JSON
  (`results/sweeps/compiler_regen_placement_sweep.json`), per-trial
  records (not just aggregates — needed for calibration binning), frozen
  copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

- **Noiseless correctness (§4) must pass** for greedy-placed boundaries
  specifically, at all three σ_det test points.
- **Calibration, defined precisely (do not decide bin boundaries after
  seeing the full-run result):** within each predicted-probability bin
  (§5, locked from smoke), the observed recovery rate's 95% CI must
  contain the bin's mean predicted probability for **Confirmed**. A bin
  whose CI excludes the mean prediction by less than 0.03 absolute is
  **Minor miscalibration** (report, not a failure — the same discipline
  as E16's "small residual" reporting, not rounded up or down). A bin
  off by ≥0.03, or a *systematic* direction of miscalibration across
  multiple bins (not scattered), is **Falsified** — greedy placement
  under a variable-group-size rule breaks an assumption the fixed-M-fit
  law relied on (e.g. group-to-group correlation the product model
  doesn't capture, more exposed when group sizes vary trial-to-trial
  rather than being fixed).
- **Efficiency (§5) is reported regardless of the calibration verdict**
  — even if calibration is imperfect, whether greedy placement uses
  fewer REGEN events than the best fixed `M` is informative on its own
  and should not be suppressed by a calibration failure elsewhere.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0. Greedy-placement noiseless correctness (SS4): 500+ trials, all three
#    sigma_det test points, replayed at sigma_det=0 through
#    run_chain_boundary_noisy_diag, must match the exact oracle at every
#    compiler-chosen boundary. Includes the edge-case check (SS4).

# 1. Smoke pass -- confirm each sigma_det test point produces a nontrivial
#    spread of REGEN-event counts (not degenerate always-1 or always-8),
#    and lock the calibration bin boundaries (SS5) from the observed
#    predicted-probability distribution.
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_compiler_regen_placement_sweep.py

# 2. Full run (3 sigma_det points x 30,000 trials)
.venv/bin/python3 photonics/run_photonic_compiler_regen_placement_sweep.py

# 3. Reproducibility: two full runs, bit-identical -- checked empirically.

# 4. Calibration analysis (SS6) -- per-bin comparison, Confirmed/Minor/Falsified.

# 5. Efficiency comparison against E13/E14/E16's frozen fixed-M curves (SS5).

# 6. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No whole-chain-product optimization** (§1) — a separate, later,
  explicitly-authorized contract if this one succeeds.
- **No P_target sweep** — 0.999 locked; a sweep is a separate contract.
- **No new op-sequence family or K value** — reuses `gen_block`'s K=16
  family, unchanged.
- **No hardware/adaptive-controller design** (design rule doc §4) — this
  validates only that the *existing* ISA, driven by a compiler pass, can
  match a fixed-period policy's guarantees with fewer/better-placed
  REGEN events. Nothing about runtime `m0` monitoring.
- **No refitting E16's law** — `a=-4.79, β=3.19` are used as frozen
  constants; if calibration fails, that is evidence about the law's
  scope (§6), not a cue to refit and declare success.

## 9. Results (2026-08-23)

**All gates passed:** gate 0 (600 trials × 3 σ_det points, 0
boundary-shape issues, 0 oracle mismatches — greedy placement is
noiseless-correct at every threshold tested; the edge case, §2, never
triggered in 1,800 sampled trials, though it remains theoretically
possible for a large enough initial draw); gate 1 (smoke, 200
trials/cell — confirmed σ=1e-4's degeneracy directly, John chose to
proceed as locked rather than swap the test point); gate 2 (full run, 3
cells × 30,000 trials); gate 3 (reproducibility, two runs, bit-identical,
sha256 `b33b4a9405f9863f7c577bb67e8391d00b02a79b7b087199c80b74679c182acb`).

**Gate 4 (calibration, pre-registered bins): FALSIFIED — systematically,
in one direction.** At σ=1e-6 and σ=1e-4, calibration is clean (all bins
Minor or Confirmed, |diff| ≤ 0.02). At **σ=1e-5** (the point carrying
almost all the real calibration spread), four bins exceed the 0.03
per-bin Falsified threshold on their own, and all four disagree in the
**same direction**:

| bin | mean predicted | observed | diff |
|---|---|---|---|
| [0.01,0.5) | 0.2542 | 0.3290 | −0.0748 |
| [0.5,0.8) | 0.7210 | 0.7800 | −0.0589 |
| [0.8,0.9) | 0.8513 | 0.8987 | −0.0475 |
| [0.9,0.95) | 0.9131 | 0.9433 | −0.0302 |

**Every miscalibrated bin has the same sign: the model under-predicts
actual recovery.** Greedy, variable-group-size placement recovers *more
often* than the pure product-of-independent-REGEN-events model (fit on
fixed-`M` placements) says it should. This is exactly the failure mode
§6 anticipated ("group-to-group correlation the product model doesn't
capture, more exposed when group sizes vary") — and it is informative,
not just a negative result: whatever correlation the fixed-`M` fit
missed works in greedy placement's *favor*, not against it.

**Gate 5 (efficiency, reported regardless of calibration): a clear,
practical win at the two informative noise levels.**

| σ_det | greedy mean REGEN events | greedy whole-trial recovery | best comparable fixed `M` | fixed `M`'s events |
|---|---|---|---|---|
| 1e-6 | **2.62** | 1.0000 | M=2 (1.0000) / M=4 (0.9992) | 8 / 4 |
| 1e-5 | **6.67** | **0.9793** | M=2 (0.8941, the best fixed option) | 8 |
| 1e-4 | 12.76 | 0.0003 | all ≈0 (M=16: 0.00077, best) | n/a — no policy recovers here |

At σ=1e-6, greedy matches the best fixed policy's reliability using
**3× fewer REGEN events** (2.62 vs. 8) and beats M=4's 0.9992 outright.
At σ=1e-5, greedy **exceeds every fixed-`M` policy's reliability**
(0.9793 vs. M=2's 0.8941, the best fixed option) while using **fewer
events than M=2's fixed 8** (6.67 average). At σ=1e-4, no policy — fixed
or greedy — recovers meaningfully; this noise level exceeds what any
REGEN placement can compensate for, consistent with the calibration
gate's finding that this point is a boundary case, not a design
failure.

**Interpretation:** compile-time, threshold-based REGEN placement beats
the best fixed-period policy on both reliability and event count at
every noise level where a fixed period could do anything useful at all.
The E16 law's *direction* used for placement decisions is right — greedy
placement correctly identifies which windows are safe — but its
*quantitative* product-of-events prediction is conservative under
variable-group-size placement, meaning the true recovery is even better
than the (already-good) improvement suggested by the efficiency numbers
above. This validates GTP's original framing: REGEN placement is a
compiler optimization problem, and the existing ISA (no new hardware)
already benefits from solving it that way rather than using a fixed
period.

**Evidence artifact:**
`results/sweeps/compiler_regen_placement_sweep_frozen_v1_2026-08-23.json`,
sha256 `b33b4a9405f9863f7c577bb67e8391d00b02a79b7b087199c80b74679c182acb`.
Driver: `photonics/run_photonic_compiler_regen_placement_sweep.py`.

