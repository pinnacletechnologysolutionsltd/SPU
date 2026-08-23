# Photonic sweep reproducibility — canonical scheme

**Decision (2026-08-20): the canonical reproducibility scheme is
`software/tests/photonic_experiment_config.py`.** The previous
CSV + `.metadata.json` replay scheme described by earlier versions of this
README is **retired**. Do not start new sweeps with it.

## Why the old scheme was retired

1. **Incomplete parameter capture.** The per-sweep `.metadata.json` recorded
   only the swept variable (e.g. `deltaT_K`) plus `master_seed`/`num_trials`/
   `_start_global_trial`. It did **not** record the full physical parameter
   dict (`dn_eff_dT`, `n_eff`, `deltaL_a/b`, `lam_*_nm`, …), which differs per
   sweep script. A faithful replay was therefore impossible: the replay snippet
   had to guess `physical_params={'deltaT': ...}` and got different fallbacks
   than the run that produced the data.
2. **Replay snippet baked `ModelC.DEFAULTS`** for `sigma_phi`/`sigma_amp`/
   `loss_dB` — the same non-isolation defect fixed in the sweep scripts
   (handover §3a). Any replay through that snippet re-introduced the noise
   floor it was meant to control.
3. **All data it produced is invalid.** Every noisy path went through
   `WDMState.copy()`, which silently dropped the complex field attributes and
   reduced coherent detection to magnitude-only — making all phase-noise modes
   immune to phase drift (handover §3b root cause). The stale CSVs/JSONs were
   deleted on 2026-08-20.

## The canonical scheme (`photonic_experiment_config.py`)

- `PhysicalParams` — one auditable dataclass capturing **every** input to a
  Model-C experiment: seed, num_trials, noise_mode, lo_track, all physical
  thermo-optic params, all stochastic impairments, loss/calibration, and the
  `NOT_WIRED` (recorded-but-inactive) fields.
- `run_experiment(params, out_path=None)` — single entry point wrapping
  `ModelC_NoisyOptical.smul_with_noise` (no duplicated logic); persists the
  full `params` + seed + timestamp + recovery + MAE as JSON.
- `verify_reproducible(params)` — runs twice and asserts bit-identical results.

All impairments default to zero (unlike the retired sweep scripts which
inherited `ModelC.DEFAULTS`).

## Usage

```bash
cd software/tests
python3 photonic_experiment_config.py          # self-test: verify_reproducible + example run
```

```python
from photonic_experiment_config import PhysicalParams, run_experiment, verify_reproducible

p = PhysicalParams(seed=13, num_trials=500, noise_mode='C2', deltaT=5.0)
assert verify_reproducible(p), "same seed must reproduce identical results"
run_experiment(p, out_path='/tmp/exp_deltaT5.json')
```

For a sweep grid, call `run_experiment` once per cell (each cell is a fully
self-describing experiment with its own seed).

## Notes / open flags

- **`discrete_corruption_descriptor_sweep_frozen_v1_2026-08-24.json`**
  (sha256 `c059d2b5b6f38f25676ce2e4425ecf20d9c93cec5aa9811e836239fcfa05264`)
  — **E20, tests whether three discrete properties of the corrupted
  lane-0 state at a failing boundary — `j` (which component `k∈{0,1,2,3}`
  deviates most), `sign(Δ_j)`, and `op_i` (`QSUB` / `ROTC_thirds` /
  `ROTC_plain`, the op immediately preceding the boundary) — explain
  E18's `R_i`-conditioned dependence**
  (`contract_photonics_discrete_corruption_descriptor_2026-08-24.md`).
  Deterministic **replay of E18/E19's exact 300,000 trials**, same 24
  materially-dependent cells; equivalence gate 0/2,000 mismatches,
  replay-fidelity exact match on all 24 cells, reproducibility
  bit-identical. Tested as three **separate** univariate stratifications
  (a joint model would fragment the already-thin `R_i=False` population
  well below usable sample size). One statistical mid-course correction:
  the originally-specified gap-explanation metric `A_D` (a
  category-share-weighted average recovery rate) was found, after the
  first full run, to be mathematically tautological — it collapses
  identically to the cell's own marginal rate by the law of total
  probability whenever no category is excluded, so it read ≈0.00000 in
  23/24 cells for every descriptor regardless of whether the descriptor
  carried information. Replaced with eta-squared (proportion of outcome
  variance explained) — pure post-processing on the already-frozen raw
  event data, no resimulation, same sha256 before/after the swap.
  **RESULT: no large-effect descriptor found.** `j` and `sign` are clean
  nulls (0/23 and 0/24 cells omnibus-significant, eta² ≤0.0025
  everywhere). `op_i` is not: it clears Bonferroni-corrected omnibus
  significance in 7/24 cells (several overwhelmingly, e.g. p=4.5e-65 at
  pair=1/bin=9), but the effect size is small (eta² 0.018–0.041, Cohen's
  "small" band, well under the frozen `≥0.14` "large" bar), so it does
  not clear the "explains most of the gap" criterion either (18/24
  negligible, 0 substantial — aggregate tier "does not explain the
  gap," same as `j`/`sign`, but not for the same reason). **Do not
  reinterpret `op_i`'s result as an explanation of E18's gap — it is a
  statistically robust but small-effect modifier, not a sufficient-state
  descriptor.** Notable secondary pattern: at 5 of 6 `bin=9` cells,
  `op_i`'s categories replicate a consistent ordering with
  non-overlapping CIs — `ROTC_plain` (`A_c` +0.30 to +0.45) recovers
  best, `QSUB` (−0.11 to −0.17) middling, `ROTC_thirds` (−0.20 to −0.38)
  worst — a high-value lead for a future, more mechanistic experiment
  (why operation type matters specifically near `m0≈9`), not a
  conclusion in itself; no such follow-on was run. Driver:
  `photonics/run_photonic_discrete_corruption_descriptor_sweep.py`
  (`--reanalyze-only` recomputes the analysis block from the frozen
  `raw_events` without resimulating, used for the eta² swap).
- **`corrupted_state_sufficiency_sweep_frozen_v1_2026-08-23.json`**
  (sha256 `642496a317d9edae7cebde0b926d272e6d0115d4bedb87e344b6bc523c14f775`)
  — **E19, tests whether the *magnitude* of a failed event's recovery
  error (`err_i`) explains E18's `R_i`-conditioned dependence**
  (`contract_photonics_corrupted_state_sufficiency_2026-08-23.md`).
  `err_i` isn't invented — it's exposed from state the simulator already
  computes and discards (`rec[0]` vs `qr[0]`, already compared inside
  E16's frozen scoring function). A deterministic **replay of E18's
  exact 300,000 trials** (same seed, same `σ=3e-5`, same `M=2`), scoped
  to E18's own 24 materially-dependent cells — no new operating-point
  search needed. Hard equivalence gate (0/2,000 mismatches) before
  trusting the new instrumentation; reproducibility bit-identical.
  **RESULT: `err_i` does NOT explain the gap, decisively** — 13/24
  cells analyzed (11 excluded for insufficient large-error samples),
  **13/13 negligible, 0 substantial** (attenuation metric `A` ranging
  `-0.010` to `+0.020`, every CI far below the `0.5` threshold). A
  genuinely interesting structural finding surfaced alongside the
  exclusions: `err_i` is overwhelmingly exactly `1` in nearly every
  cell, and position pair 1 (groups 2→3) shows **zero** `err_i>1`
  cases across all 300,000 trials at any `m0` bin. Regardless of
  whether a failure's error was minimal or larger, subsequent recovery
  stays similarly depressed — ruling out error *magnitude* as the
  missing variable and pointing toward a qualitative mechanism (which
  component deviated, its sign, the op type active at failure) as the
  next hypothesis, not established here. Driver:
  `photonics/run_photonic_corrupted_state_sufficiency_sweep.py`.
- **`correlation_mechanism_sweep_frozen_v1_2026-08-23.json`** (sha256
  `c12f8589f8d4a91337c379ff934bab4db6f34fcb2d09b12110781b9e02f576cf`) +
  **`correlation_mechanism_search_frozen_v1_2026-08-23.json`** (sha256
  `f15163fa19c7e3798a6ae2d504b02e42bbbe442bb59bc0a85bff0f13cc9afcf4`) —
  **E18, directly tests whether `R_i` (event i's success/failure)
  predicts `R_{i+1}` beyond `m0_{i+1}` alone**
  (`contract_photonics_correlation_mechanism_2026-08-23.md`), at fixed
  `M=2` placement (not DP — a measurement question, not a placement
  one). Reuses E16's `run_chain_boundary_noisy_m0trace` verbatim — no
  new simulation code, only the "clean arrival up to `i`" pair-collection
  rule, a deterministic `m0` binning hierarchy (exact integer → width-2
  → width-4 → exclude, decided by sample count only, frozen before any
  significance was computed), and a search/inference split using
  disjoint RNG namespaces and disjoint trials (search: 20,000
  trials/candidate at 6 `σ_det` values, locked `σ=3e-5`; inference:
  300,000 fresh trials, run twice, bit-identical). **RESULT: REAL
  DEPENDENCE FOUND, decisively** — 24/30 tested cells (80%) both
  statistically and materially dependent (`|diff|>0.05` with a
  Bonferroni-adjusted CI excluding zero), 29/30 agreeing on direction:
  `R_i=False → lower P(R_{i+1})` (failures cluster) — the *opposite* of
  the originally proposed "noise anti-correlates" mechanism. Effect
  sizes are large (up to 78.5 points, `z>100` on several cells) and vary
  systematically with `m0_{i+1}` (largest near the ceiling, vanishing
  past the steep part of the recovery cliff). Establishes `m0` is not a
  sufficient statistic for next-event recovery — plausibly because it's
  a coarse bit-length descriptor that discards which specific corrupted
  value a failed group produced. **Does not contradict E17 Part 3/4**:
  placement decisions use the noiseless trajectory, computed before any
  `R_i` exists, so this correlation — however large — isn't exploitable
  by a compile-time optimizer. It explains *why* whole-chain success has
  been conservatively mispredicted throughout E9–E17 (positively
  correlated events push true joint success above the naive
  independent-product estimate), without reopening the placement
  question E17 already closed. Driver:
  `photonics/run_photonic_correlation_mechanism_sweep.py`.
- **`compiler_montecarlo_lesssaturated_sweep_frozen_v1_2026-08-23.json`**
  (sha256 `306be148d6d118b67d82d6b5cdea659b2002e8b2e9e158e3ada9ecee5654bc5b`)
  + **`compiler_montecarlo_lesssaturated_search_frozen_v1_2026-08-23.json`**
  (sha256 `756211493c37736f82dbe5f98cda4b6ae69f774e75e2eeb7295b5cb7e3a2abb5`)
  — **E17 Part 4, repeats E17 Part 3's Monte-Carlo closeness-to-optimum
  test at a deliberately located, non-saturated operating point**
  (`contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md`),
  closing E17 Part 3's power gap (39/40 blocks saturated there).
  A new operating-point search (gate 0c) swept a candidate `σ_det` grid
  measuring the count of blocks landing in `[0.2,0.8]` recovery at
  reduced precision; the first 8-point grid's best candidate (5e-5)
  landed at 9/20, one short of the `≥10/20` bar — HALTed and reported
  per the contract's own rule against silently loosening the bar; John
  chose to widen the grid (added 4.5e-5/5.5e-5/6e-5) rather than lower
  it. `σ=4.5e-5` cleared the bar at 12/20 (search precision). All other
  machinery (CRN, `score_schedule_addressable`, paired-difference
  statistics) reused verbatim from E17 Part 3, not re-gated. Full run
  (20 blocks, up to 500 candidates each), reproducibility bit-identical
  (~125 minutes/run). **RESULT: CONFIRMED — 20/20 blocks rank-1 or
  CI-tied-for-best, 0/20 beaten by any alternative**, and this time
  with real power: **11/20 blocks (55%) landed genuinely in the
  `[0.2,0.8]` band**, versus E17 Part 3's 1/40 (2.5%). A quick "discrete
  `N`-jump" explanation floated for the search grid's non-monotonic
  in-band counts was checked against the per-block data and found
  wrong before being written into the record — every block's own
  recovery decreases perfectly monotonically with `σ_det`; the
  aggregate non-monotonicity is just a superposition of many
  individually-monotonic curves crossing the target band at different
  points. Across both E17 Part 3 (saturated) and E17 Part 4
  (non-saturated) operating regimes, no evidence has been found that
  E16's conservative calibration bias distorts DP's schedule ranking —
  it looks like a magnitude effect, not a placement-ranking effect,
  within everything tested so far. Driver:
  `photonics/run_photonic_compiler_montecarlo_lesssaturated_sweep.py`.
- **`compiler_montecarlo_optimum_sweep_frozen_v1_2026-08-23.json`** (sha256
  `4bf394082692abbe1a9d32516d814dc0728d735c0b6dd9653efda4327a67b05d`) —
  **E17 Part 3, tests whether E17 Part 2's DP schedule is genuinely the
  best same-event-count placement for individual blocks, via a
  model-free Monte-Carlo comparison**
  (`contract_photonics_compiler_montecarlo_optimum_2026-08-23.md`).
  Uses common random numbers (a precomputed noise table addressable by
  op position, shared across every candidate schedule for a given
  block/repeat — not a stateful sequential rng, which would desync
  between candidates with different REGEN counts) for a paired-difference
  comparison, deliberately reusing E16/E17's uncorrected product model
  only to *choose* DP's schedule (via E17 Part 2's `optimal_placement`,
  reused verbatim), never to evaluate it. Required a new scoring
  function (`score_schedule_addressable`) verified equivalent to E15's
  `run_chain_boundary_noisy_diag` via its own cross-check gate (0/300
  mismatches). 20 blocks per σ_det (`[1e-6, 1e-5]`, E17 Part 2's
  dominating λ=0.01), up to 500 candidate schedules per block (full
  enumeration when `C(14,N-1)≤500`, else reproducibly sampled), 2,000
  paired repeats each, run twice, bit-identical (each run took
  ~80–90 minutes — the largest single sweep in this branch by compute).
  **RESULT: DP near-optimal, CONFIRMED — 20/20 blocks at both σ_det**,
  no evaluated alternative ever beat DP outside noise. **Important
  caveat, reported explicitly:** 39/40 blocks were saturated at perfect
  (1.0000) recovery, where any reasonable same-N schedule ties trivially
  — this confirms no regression but has little power to detect a subtle
  ranking advantage. The one non-saturated block (σ=1e-5, block 2,
  0.9460 recovery) is the substantive result: DP's own 3-boundary
  schedule was independently verified as the actual best among all 91
  fully-enumerated alternatives, not a ceiling artifact. Interpretation:
  at E17 Part 2's own dominating operating point, the E16 law's
  conservative bias appears roughly uniform across candidate segments
  (doesn't distort rankings) rather than context-dependent — but this
  was tested only at one λ and two σ_det values where recovery is
  already high, and does not rule out a ranking-quality gap at a less-
  saturated operating point (a follow-on contract, not attempted here).
  Driver: `photonics/run_photonic_compiler_montecarlo_optimum_sweep.py`.
- **`compiler_optimal_placement_sweep_frozen_v1_2026-08-23.json`** (sha256
  `6911fd3f0f9f51e9a36b1000800ade8bfe91a3664caf6530ecbcccdfbd25c3df`) —
  **E17 Part 2, tests whether a dynamic-programming whole-chain-optimal
  REGEN placement dominates E17's greedy placement**
  (`contract_photonics_compiler_optimal_placement_2026-08-23.md`).
  Rather than E17's fixed per-event floor, a DP (shortest-path over
  `O(16²)` candidate segments) maximizes predicted `P_chain = ∏
  P_event(m0_i,σ)` for a REGEN-cost parameter λ, tracing a Pareto
  frontier. Reuses E15's scorer unmodified; only the DP itself is new
  code. **Gate 0's required cross-check against E17's already-verified
  `greedy_place` caught a real bug**: the first `segment_m0`
  implementation assumed every combine op adds a flat `+1` to `m[0]`,
  true for `ROTC` but wrong for `QSUB` (production semantics: `m[0] =
  max(m[sa], m[sb]) + 1`, and `sa`/`sb` can draw from lane 1) — 734–1330
  mismatches per 600-trial sample before the fix, 0 after. A 76-config
  brute-force optimality spot-check also passed clean. 2 σ_det points
  (`[1e-6, 1e-5]`, reusing E17's informative pair; σ=1e-4 not retested,
  already established as universally degenerate) × 9 λ values, 10,000
  trials/cell, run twice, bit-identical. **RESULT: DOMINATES greedy,
  decisively, at both points.** σ=1e-6: 5/9 λ values dominate outright;
  best point uses 21.9% fewer REGEN events (2.05 vs. greedy's 2.62) at
  equal (perfect, 1.0000) reliability. σ=1e-5: 8/9 λ values dominate;
  best point uses 36.4% fewer events (4.24 vs. greedy's 6.67) *and*
  improves reliability (0.9853 vs. 0.9793 — outside greedy's own 95%
  CI, a statistically real gain, not just numerically larger). The DP's
  own predictions remain conservative in the same direction as greedy's
  (E17) — the standing correlation hypothesis is neither confirmed nor
  falsified here, deliberately, since this contract reused the
  uncorrected product model as its optimization objective. Driver:
  `photonics/run_photonic_compiler_optimal_placement_sweep.py`.
- **`compiler_regen_placement_sweep_frozen_v1_2026-08-23.json`** (sha256
  `b33b4a9405f9863f7c577bb67e8391d00b02a79b7b087199c80b74679c182acb`) —
  **E17, tests greedy compile-time REGEN placement** (insert a boundary
  whenever the noiseless `m0` trajectory reaches `m0_safe(sigma_det,
  P_target=0.999)`, computed from E16's frozen law `a=-4.79, β=3.19`)
  against the pure product-of-independent-events model's own predictions
  (`contract_photonics_compiler_regen_placement_2026-08-23.md`). Reuses
  E15's `run_chain_boundary_noisy_diag` unmodified — only the boundary-
  *selection* algorithm (`greedy_place`) is new. 3 σ_det points
  (`[1e-6, 1e-5, 1e-4]`), 30,000 trials/cell, per-trial (predicted,
  observed, n_regen) records, seed 13, run twice, bit-identical. Gate 0
  (noiseless correctness) clean at all 3 points, 0 oracle mismatches.
  Smoke pass confirmed σ=1e-4 is a genuinely degenerate test point
  (99th-percentile predicted = 0.0013) — John chose to keep it locked
  rather than swap it, reported as a boundary-case finding.
  **RESULT: calibration FALSIFIED, in greedy placement's favor.** At
  σ=1e-5 (the point with real predicted-probability spread), four bins
  exceed the pre-registered 0.03 per-bin threshold, all in the same
  direction: the model *under*-predicts actual recovery (e.g. predicted
  0.721 vs. observed 0.780 in the [0.5,0.8) bin) — greedy, variable-
  group-size placement recovers more reliably than the fixed-`M`-fit
  product model says it should, consistent with some group-to-group
  correlation the model doesn't capture working in greedy's favor.
  **Efficiency (reported regardless): a clear win.** At σ=1e-6, greedy
  matches the best fixed policy's 1.0 reliability using 2.62 mean REGEN
  events vs. M=2's fixed 8 (and beats M=4's 0.9992 outright). At σ=1e-5,
  greedy's 0.9793 whole-trial recovery *exceeds* every fixed-`M` option
  (best fixed, M=2, only reaches 0.8941) while using fewer events on
  average (6.67 vs. M=2's 8). At σ=1e-4, no policy recovers meaningfully
  — consistent with the calibration finding that this is a genuine
  boundary case, not a placement failure. Driver:
  `photonics/run_photonic_compiler_regen_placement_sweep.py`.
- **`m0_dynamic_range_sweep_frozen_v2_2026-08-22.json`** (sha256
  `c6841f14ac573e81d2900823d494530a3fab00172c6695fd6210cfdf5a56be8c`) —
  **E16 v2, corrects a measurement confound found in v1 the same day.**
  v1's `m0_histogram_raw` pooled every REGEN-group observation, including
  ones downstream of an earlier same-trial failure — once a group's
  recovered state diverges from the true oracle, it stays corrupted
  (59.9% of M=2's group-8 failures at the transition `m0` had an earlier
  same-trial failure). v2 adds `m0_histogram_clean`, which stops counting
  a trial's observations at its first failure. Same 16-cell grid, same
  30,000 trials/cell, reproducibility bit-identical (two runs). **Rerun
  of the pre-registered primary test on the corrected histogram: 0/122
  comparisons significant (was 25/128 on the raw histogram), max diff
  0.029 (was 0.103) — CONFIRMED. The v1 "M=2 is different" finding was
  entirely a contamination artifact, not real physics.** With M-invariance
  now genuinely confirmed, gate 6 (out-of-sample prediction against
  E13/E14's frozen curves) was run: fit `P(recover|m0,σ)` by maximum
  likelihood on the pooled clean data (a=-4.79, β=3.19 in
  `sigmoid(β·(a−log2(σ)−m0))`; a first fit attempt had a grid-search
  range bug that excluded the true optimum, caught by checking against
  training data before trusting it), then predicted E13/E14's whole-trial
  curves via a product-of-independent-per-event-probabilities model using
  independently-measured noiseless `m0`-trajectories. **All 12 crossing
  brackets (4 M × {99.9%,99%,95%}) overlap between predicted and frozen**,
  typically within 0.02 absolute recovery probability, across four
  decades of σ including levels far outside E16's own tested grid. This
  substantially answers the investigation's original objective: `m0`
  (the shared scale exponent at REGEN readout) and `σ_det`, combined via
  one per-event law and a product-of-events model, predict recovery
  across everything this investigation has covered (E9/E13/E14's
  independently-frozen curves reconstructed from E16's own per-group
  data). Driver: `photonics/run_photonic_m0_dynamic_range_sweep.py`.
- **`m0_dynamic_range_sweep_frozen_v1_2026-08-22.json`** (SUPERSEDED by
  v2 above — retained per repo discipline against silently rewriting a
  superseded result, do not cite its "FALSIFIED, concentrated in M=2"
  verdict as current) (sha256
  `794160db5fd13af8eb0b724fc336b2fb6dc1514901b38fa41c9639a8dd661e5b`) —
  **E16, tests whether per-REGEN-event recovery is governed by the local
  scale exponent `m[0]` and `sigma_det`, approximately independent of
  which regeneration interval M produced that `m0`**
  (`contract_photonics_m0_dynamic_range_2026-08-22.md`). Mechanism found
  by reading `PhotonicQuadrayBackend` directly: every combine op
  unconditionally increments `m[dst]`; REGEN re-derives `m` from the
  recovered value's own bit-length at re-entry (does NOT reset to a
  baseline); detector noise is injected before the `2^m` readout rescale
  — only lane 0 ever accumulates `m` growth (mechanistically explains
  E14's 100%-lane-0-only failures). 16 cells (M∈{2,4,8,16} × shared
  σ_det grid `[1e-7,1e-6,1e-5,3e-5]`), 30,000 trials/cell, 840,000
  group-observations, seed 13, run twice, bit-identical. **RESULT:
  FALSIFIED overall** (pre-registered Bonferroni-corrected pairwise
  z-test, 25/128 comparisons significant, max diff 0.103 — far above the
  5%/0.05 Confirmed bar), but **decisively concentrated in M=2**: pairs
  excluding M=2 (M∈{4,8,16} only) sit right at the Partially-confirmed
  boundary (8.8% significant, max diff 0.055), while M=2-involving pairs
  are robustly different (37.5% significant, max diff 0.103). A
  pre-registered trial-clustered bootstrap addendum confirms 23/25
  (92%) of the significant differences are not a within-trial-
  correlation artifact. Descriptive finding: the 50%-recovery crossing
  *location* is nonetheless nearly identical across all four M (within
  ~0.1–0.2 `m0` units, vs. the many-decades-scale K/M-dependence the
  original framing implied) and sits ~0.5 `m0` units below the naive
  `log2(0.05/sigma_det)` prediction, consistently. `m0` is the dominant
  factor governing recovery but not a fully sufficient statistic —
  M=2 has some additional, uncharacterized structural feature. Gate 6
  (out-of-sample prediction against E13/E14's frozen curves) NOT run,
  per the contract's own gating (primary test Falsified). Driver:
  `photonics/run_photonic_m0_dynamic_range_sweep.py`.
- **`regen_boundary_placement_sweep_frozen_v1_2026-08-22.json`** (sha256
  `30e9802103a6665a057262545e9f294b5d036e333d7a20f09eb3ea8b3c4cc08b`) —
  **E15, tests whether M=2's QLDI-only first REGEN boundary (E14's
  surviving candidate) explains its diminishing return**
  (`contract_photonics_regen_boundary_placement_2026-08-22.md`). Shifts
  every boundary by exactly +1 op ([2,4,...,16] → [3,5,...,15,16]),
  holding the 8-event REGEN count fixed — isolates "first boundary before
  any computation" from "regeneration frequency." 16 cells, 30,000
  trials/cell, K=16, seed 13, run twice, bit-identical. Equivalence gate
  (per-trial, not aggregate) and first-boundary state diagnostic both
  passed cleanly before the sweep. **RESULT: RULED OUT** under the
  pre-registered bracket-overlap criterion — 99.9%/99%/95% crossing
  brackets all overlap or are identical to pure M2's frozen brackets (no
  full-grid-interval shift at any of the three). A small, real,
  statistically significant residual is present (recovery higher at every
  shared grid point from 3e-6 to 5e-5, peak 7.8σ at level=3e-5) but
  quantifies to only ~+0.011 decades (~2.7%) at the 50%-recovery
  crossing — roughly three orders of magnitude smaller than E13's
  regeneration-frequency effect, and far short of closing any of the
  17.1× gap E14 left open. QLDI-only-first-boundary placement is ruled
  out as a substantial cause of M=2's diminishing return; a new
  hypothesis is needed for the remaining gap (not constructed in this
  contract, per its own non-goals). Lane-attribution spot-check (3 cells,
  n=3,000 each) confirms failures remain 99.9% lane-0-only, no new lane-1
  pathway introduced. Driver:
  `photonics/run_photonic_regen_boundary_placement_sweep.py`.
- **`regen_placement_m2_sweep_frozen_v1_2026-08-22.json`** (sha256
  `90e1bf35…a843f8651`) — **E14, the M=2 extension of E13's regeneration-
  placement investigation** (`contract_photonics_regen_placement_m2_2026-08-22.md`).
  16 cells (locked from a wide exploratory smoke pass), 30,000 trials/cell,
  K=16, M=16/8/4 reused from E13's frozen curve (not rerun), M=2 measured
  directly, seed 13, run twice, bit-identical. **RESULT: OUTCOME B,
  DIMINISHING RETURNS.** M=2 improves on M=4 by only 2.00× at 99.9%
  (geomean 3.464e-6 vs M=4's 1.732e-6) — far short of the 31.62× seen
  going M=8→M=4. The improvement-per-halving sequence (1.0 dec, 1.5 dec,
  then 0.3 dec) peaks at M=4 and sharply reverses, not a smooth
  saturation. New lane-attribution instrumentation (§4b of the contract)
  found **zero** lane-1-attributable failures across ~3,769 failed trials
  (both M=2 and an M=4 matched-control sample) — cleanly rules out the
  lane-1-exposure hypothesis by direct measurement, leaving M=2's
  QLDI-only first REGEN boundary (no combine op before it, unlike
  M=4/8/16) as the surviving, untested candidate. M=2 closes 69.4% of the
  full 4.033-decade gap to native K=8 (up from M=4's 62.0%); 17.1×
  remains. Driver: `photonics/run_photonic_regen_placement_m2_sweep.py`.
- **`regen_placement_sweep_frozen_v1_2026-08-22.json`** (sha256
  `cd942f77…6282935fa4`) — **E13, the regeneration-placement mechanism
  investigation** (`contract_photonics_regen_placement_2026-08-22.md`).
  36 cells (12-point det grid × M∈{4,8,16}), 30,000 trials/cell, K=16
  only, `gen_block` (E9's generator), M=16 measured directly as a
  control anchor (verified exact agreement with E9's original arm-B
  harness at 6 matched levels before trusting the new one), seed 13, run
  twice, bit-identical. **RESULT: SUBSTANTIAL CONTRIBUTOR, not complete
  explanation.** New code (`run_chain_periodic_noisy`) simulates
  intermediate whole-state REGEN boundaries within a 16-op sequence —
  something `run_chain_noisy` (used by every prior K-chain experiment)
  has never supported. Regenerating every 8 ops gives exactly 10.00×
  improvement over never regenerating until op 16; every 4 ops gives
  another 31.62× (316.23× total) — monotonic, accelerating, no
  crossovers. Covers 62.0% of the full 4.033-decade gap to E9's native
  K=8 crossing; a 34.2× gap remains at M=4, the most frequent tested.
  First candidate mechanism (after E11, E12 both ruled out) to produce a
  large, reproducible effect in the predicted direction — not a full
  explanation. Driver: `photonics/run_photonic_regen_placement_sweep.py`.
- **`cascade_depth_sweep_frozen_v1_2026-08-22.json`** (sha256
  `2e322400…37592dff8`) — **E11, the cascade-depth mechanism
  investigation** (`contract_photonics_cascade_depth_2026-08-22.md`).
  70 cells (35-point det grid × 2 arms), 30,000 trials/cell, K=16 only,
  pure self-rotation chains (Arm T: ROTC angles {1,3,4}, Arm N: {0,2,5}),
  identical deterministic per-trial m=23 for both arms, seed 13, run
  twice, bit-identical. **RESULT: HYPOTHESIS RULED OUT.** Tests whether
  uncompensated `/3` divisions from exact-thirds ROTC angles explain E9's
  disproportionate K=8→K=16 collapse — they don't: Arm T and Arm N's
  crossing brackets coincide exactly ([1.5e-9, 2.0e-9] for both at
  99.9%/99%). Mathematical grounding (§10 of the contract): `(F,G,H)/div`
  is an exact unit vector for all six ROTC angles — the `/3` is rotation
  normalization, not independent attenuation, so this result was
  structurally expected once checked, not a surprise. K=16's collapse
  remains unexplained. Driver:
  `photonics/run_photonic_cascade_depth_sweep.py`.
- **`detector_boundary_sweep_frozen_v1_2026-08-21.json`** (sha256
  `1a3306a1…870f1afda`) — **E9, the detector-boundary sweep**
  (`contract_photonics_detector_boundary_2026-08-21.md`). 127 cells
  (23-point log grid for K∈{1,2,4,8}, 35-point split grid — main 23 points
  plus a 12-point sub-grid below the floor — for K=16, after a smoke pass
  found K=16's crossing off the original single-grid's floor), 30,000
  trials/cell, σ_φ=σ_amp=0 (detector axis isolated), ΔT=2K, seed 13, run
  twice, bit-identical. **RESULT: FALSIFIED.** The E8 closed-form
  `σ_det ≲ 0.05/2^m` does not generalize: R_K = σ\*_det(K)/σ_det,pred(K)
  (measured crossing / prediction at the *measured* mean scale exponent
  m̄(K)) spans ~45× across K (0.301 at K=1 → 0.0067 at K=16), and is off by
  ~3.3× even at K=1, one of the formula's own two fit points — E8's original
  grid (`{0, 1e-4, 3e-4, 1e-3}`) was too coarse to have caught this. The
  K=8→K=16 step drops R by ~24× despite m̄ growing only ~3.2 — a
  disproportionate collapse not explained by the scalar-m model (mechanism
  not investigated under this contract; flagged for a separate follow-on).
  Backend contract §3.3 not silently corrected — a dated pointer to this
  result was added directly below the original claim, which remains as
  originally frozen. Driver: `photonics/run_photonic_detector_boundary_sweep.py`.
- **Frozen Step-6b result #7 (2026-08-20): `knoise_combined_sweep_frozen_v1_2026-08-20.json`**
  (identical to `knoise_combined_sweep.json`; sha256 f3e49dbf…). Combined
  multi-factor K-chain, contract_photonics_knoise_combined_2026-08-20.md.
  40 cells (8 noise combos × K ∈ {1,2,4,8,16}), 30000 draws/cell, identical
  machinery to step 6, seed 13, bit-identical across two runs.
  **Interaction classification: NO compounding.** Measured recovery is never
  significantly below the independent-product model (p_φ·p_amp·p_det); it
  typically sits between the product (lower bound) and the worst-axis
  reference — failures are partially correlated through the shared
  output-magnitude driver (large-intermediate trials fail on multiple axes
  simultaneously). Consequence: **K can be set from single-factor budgets;
  the product model is conservative; a joint noise budget is NOT required.**
  Arm B remains dominated by the Σ_total detector wall at K≥2 regardless of
  the other factors.
- **Frozen Step-6 result #6 (2026-08-20): `knoise_sweep_frozen_v1_2026-08-20.json`**
  (identical to `knoise_sweep.json`; sha256 47800546…). K-chain with per-op
  stochastic noise, contract_photonics_knoise_sweep_2026-08-20.md. 60 cells
  (3 factors × 4 levels × K ∈ {1,2,4,8,16}), 30000 draws/cell, ΔT=2K
  conditioned, arm A (per-op regeneration) vs arm B (chain) from the SAME
  paired stream, seed 13, bit-identical across two runs. **Result: A ≥ B at
  every (factor, level, K); B collapses on all stochastic axes while A
  survives** (φ 0.5°: A 61→25% vs B 61→0%; amp 1e-5: A 99.7→92% vs B 99.7→22%;
  det 1e-4: A 92→100% vs B 92→0%). **Key architectural finding:** the chain's
  final detection must resolve 1/Σ_total = 1/∏σmax (mean 2.2e10 @ K=16) —
  per-op regeneration bounds it to 1/σmax — regeneration is a dynamic-range
  management mechanism. σ=0 gate: A=B=100% at all K (Step-5 reproduction).
  Arm-A intermediates are projected unclamped (final-only SurdFixed64 clamp,
  per spec); det-only arm A recovery RISES with K (m_K shrinks → smaller σmax).
- **Frozen Step-5 result #5 (2026-08-20): `ksweep_frozen_v1_2026-08-20.json`**
  (identical to `ksweep.json`; sha256 20a45cc1…). K-operation regeneration
  sweep, contract_photonics_ksweep_2026-08-20.md. 10 cells (ΔT ∈ {2,5}K ×
  K ∈ {1,2,4,8,16}), 60000 draws/cell, continuous optical chain (no per-op
  rounding), per-op thermal rotation, unconditioned (A) vs conditioned
  (B, ÷cos K·δφ) from the same trial state, band [1000,30000] on the exact
  oracle, seed 13, bit-identical across two runs. **Result: B = 100.00% at
  every K and ΔT; A collapses 69.17%→13.09%→0% (ΔT=2K).** Conditioned
  deviation = 0.0 at all K (internal state is exactly the rotated ideal —
  possibility C ruled out by data). First-boundary-crossing histograms are
  smooth (gradual accumulation, no per-op instability). Dynamic-range cost:
  rejection 4.7%→90.7% (m_K 100→2).
- **Frozen Phase-2 result #4 (2026-08-20): `amp_phase_det_sweep_frozen_v1_2026-08-20.json`**
  (identical to `amp_phase_det_sweep.json`; sha256 5a6aefcf…). Amplitude ×
  differential-phase × detector-noise sweep, 180 cells (6 φ × 6 amp × 5 det),
  16000 trials/cell, canonical frozen base (C1), seed 13, bit-identical across
  two runs. Independent axes: phase 100%@0°→3.97%@5°; amp 100%@0→0.26%@1e-2;
  det 100%@0→0.22%@1e-2. Mechanism (100.00% per-trial agreement, stream-aligned
  probe): recovered_a = round(x_a·cos δφ_a·amp_a + n_a·σmax/s) — phase and
  amplitude are multiplicative scale errors (same heavy-tail family as #1–#3);
  detector noise is additive with σmax scaling (operand-dependent). Worst axis
  dominates the combined surface. **Model note:** amplitude draws now come from
  the per-trial seeded stream (rng fix 2026-08-20); frozen results #1–#3
  unaffected (σ_amp=0 there); T4 historical numbers changed (they were on the
  unreproducible global stream).
- **Frozen Phase-2 result #3 (2026-08-20): `deltaT_calib_sweep_frozen_v1_2026-08-20.json`**
  (identical to `deltaT_calib_sweep.json`; sha256 66862942…). Joint ΔT × ε
  sweep, 217 cells (7 ΔT × 31 ε), 16000 trials/cell, canonical frozen base
  (C2 + 1.8 dB loss-normalized), seed 13, bit-identical across two runs.
  **Key finding — the two errors do not simply add: they are one multiplicative
  scale factor.** recovered = round(x·cos δφ/(1+ε)); a trial fails iff
  |x|·|1−cos δφ/(1+ε)| ≥ 0.5 (100.00% per-trial agreement at all probes).
  ε>0 (undershoot) adds to cos-attenuation; ε<0 (overshoot) **cancels** it:
  the recovery ridge sits at ε* = cos(δφ)−1 — measured best-ε −5e-5 @ ΔT=2K
  and −3e-4 @ ΔT=5K match prediction to grid resolution, restoring recovery
  from 70.5%→100.0% and 9.9%→100.0%. Implication: thermal drift is exactly
  compensable by a temperature-tracked receiver gain trim.
- **Frozen Phase-2 result #2 (2026-08-20): `calib_sweep_frozen_v1_2026-08-20.json`**
  (identical to `calib_sweep.json`; sha256 551208a8…). Calibration-error sweep,
  16000 trials/cell, static 1.8 dB loss with loss-normalized BQE, canonical
  physical params, seed 13, bit-identical across two runs. Only ε varies.
  Calibration requirement: ≥99.9% → |ε|≤1.53e-5 (±1.3e-4 dB), ≥99% → 1.83e-5,
  ≥95% → 2.29e-5, ≥90% → 2.74e-5, ≥50% → 7.46e-5 (±6.5e-4 dB). Same
  heavy-tail mechanism as #1: failure iff max(|a′|,|b′|)·|ε|/|1+ε| ≥ 0.5
  (100.00% per-trial agreement at ε = 5e-5..5e-4). ε=0 control = 100.00%.
- **Frozen Phase-2 result #1 (2026-08-20): `deltaT_sweep_frozen_v1_2026-08-20.json`**
  (identical to `deltaT_sweep.json`; sha256 b3d5cecc…). Full ΔT sweep, 16000
  trials/cell, canonical `PhysicalParams`, master_seed=13, bit-identical across
  two runs (timestamps excluded). Thermal operating envelope (verified
  cos-attenuation mechanism + frozen-stream CDF): ≥99.9% → |ΔT|≤1.14K,
  ≥99% → 1.25K, ≥95% → 1.40K, ≥90% → 1.53K, ≥50% → 2.52K. Mechanism: a trial
  fails iff max(|a′|,|b′|)·(1−cos δφ) ≥ 0.5 with δφ = 4.85e-3·ΔT rad
  (predicted failures matched actual in 100.00% of trials at ±2K and ±5K).
- **Default divergence — RESOLVED (2026-08-20).** `PhysicalParams` is the
  single canonical source for unspecified parameters, carrying the silicon
  design values consistent with `test_photonic_surd_oracle.py`
  (n_eff=2.45, dn_eff_dT=1.86e-4, ΔL=6.4322 µm). The C2 fallback constants in
  `smul_with_noise` were aligned to them, and the root
  `physical_params_defaults.json` (an unloaded, divergent artifact) was
  deleted. `ModelC_NoisyOptical.DEFAULTS` remains only as the stochastic
  noise floor for the C0/C1 phase-sweep tests (T1–T3) — a different concept.
- **Sweep scripts re-pointed at `run_experiment()` (2026-08-20).**
  `run_photonic_deltaT_sweep.py`, `run_photonic_combined_sweep.py`, and
  `run_photonic_deltaT_calib_sweep.py` now emit the canonical per-cell JSON
  (full params + stats) instead of bare CSVs. `PHOTONIC_TRIALS=<n>` overrides
  the per-cell trial count for smoke runs. The retired scheme's generator,
  `photonics/generate_sweep_metadata.py`, is retained there for reference only.
- `coupler_error` and `crosstalk_dB` are recorded in `PhysicalParams` but not
  yet wired into the underlying model (see `NOT_WIRED` in the module).
- **`photonic_envelope_frozen_v1_2026-08-20.json`** (sha256
  `f300b6b9…54680b89`) — **E8, the declared regeneration envelope**
  (deliverable 2 of `contract_photonics_backend_2026-08-20.md`). 60 cells
  (3 noise axes × 4 levels × K {1,2,4,8,16}), 30,000 accepted trials/cell,
  seed 13, band [1000, 30000] on max |QR0 component|, ΔT = 2K conditioned,
  arms A/B paired draws. σ=0 gate: A=B=100% at all K. Key declared numbers:
  detector budget σ_det ≲ 0.05/2^m (1.96e-4 at K=1 → 5.8e-7 at K=16); the
  K* crossover: chain K*(99.9%) = 8 at σ_amp=1e-5 / 2 at 5e-5 / 1 at
  σ_φ=0.25° / 0 for any tested detector > 0; per-op REGEN holds ≥99% at
  σ_φ ≤ 0.25° and σ_amp ≤ 5e-5 through K=16 (detector-bound). Run twice,
  bit-identical (cells). Driver: `run_photonic_envelope_sweep.py`;
  extraction: `extract_photonic_envelope.py`.
