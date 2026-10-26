# Engineering Contract: Correlation/Calibration Mechanism Investigation (E18)

**Date:** 2026-08-23
**Contract ID:** `contract_photonics_correlation_mechanism_2026-08-23.md`
**Status:** RAN TO COMPLETION 2026-08-23. **RESULT: REAL DEPENDENCE
FOUND — decisively.** 24/30 cells (80%) materially dependent, 29/30
agreeing on direction: `R_i=False → lower P(R_{i+1})` (failures
cluster), the opposite of the originally proposed mechanism. `m0` is
not a sufficient statistic for next-event recovery. Does not contradict
E17 Part 3/4 — placement is decided from the noiseless trajectory,
before `R_i` exists, so this is not exploitable by a compile-time
optimizer; it explains the magnitude-conservatism, not a ranking gap.
See §10.

**Roles:**
- **Spec Author:** Claude, formalizing John/GTP's explicit E18 scoping
  (2026-08-23, after E17 Part 4): "don't immediately modify the
  production DP. First measure the thing you've been deliberately
  refusing to assume: `P(R_{i+1}|R_i,m0_i,m0_{i+1})` versus
  `P(R_{i+1}|m0_{i+1})`, under the same physical simulator."
- **Halt-and-Flag Implementer:** review the stratification/binning
  design (§4) — the central risk here is not new simulation code (this
  contract reuses E16's already-gated machinery verbatim) but a
  statistical one: fragmenting the data into too many small cells to
  say anything with power.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_m0_dynamic_range_2026-08-22.md` §10 (E16 v2) —
  `run_chain_boundary_noisy_m0trace` is reused **verbatim, unmodified**.
  E16's own correction discarded exactly the data this contract studies:
  its `m0_histogram_clean` counting rule stops at a trial's first
  failure specifically to get an unbiased *marginal* `P(recover|m0)`
  estimate — this contract goes back to what that rule discarded
  (what happens at group `i+1` when group `i` failed) and studies it
  directly, rather than treating it as contamination to remove.
- `contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md`
  (E17 Part 4) — the frozen conclusion this contract follows on from:
  "no evidence was found that the conservative E16 calibration distorts
  DP's schedule ranking... it establishes that its hypothesized
  consequence has not appeared in the tested regimes." This contract
  tests the mechanism directly rather than continuing to infer its
  absence from placement outcomes.
- `contract_photonics_regen_placement_m2_2026-08-22.md` (E14) — the
  original M=2 fixed-period boundary list, reused for this contract's
  locked placement (§3): M=2 gives 8 groups (7 adjacent pairs) per
  K=16 trial, more within-trial structure to examine than M=4's 3 pairs.

---

## 1. Objective

**Does event `i`'s outcome (`R_i`, success or failure) predict event
`i+1`'s outcome beyond what `m0_{i+1}` alone predicts — i.e., is
`P(R_{i+1} | m0_{i+1}, R_i) ≠ P(R_{i+1} | m0_{i+1})` — measured directly
under the real simulator, at fixed `M=2` placement?**

This is the literal mechanism E17 Part 3/4 could only test the
*consequence* of. Confirming or ruling out a direct dependence here
settles, rather than infers, whether the standing correlation
hypothesis has any substance — and if it does, quantifies it precisely
enough to know whether it matters for anything downstream.

**Explicitly not attempted:** no change to `greedy_place` or
`optimal_placement` (the production placement code) — this is
measurement only. No new simulation primitives — `run_chain_boundary_noisy_m0trace`
is reused exactly as E16 froze it. No attempt yet to build a corrected
recovery law incorporating any dependence found — that is a separate,
later, not-yet-authorized contract, contingent on this one's result.
No claim, prior to measurement, about which direction a real dependence
would run (John's stated expectation — "probably magnitude, not
ranking" — is a prior to be tested, not assumed into the design).

## 2. Objective grounding

`run_chain_boundary_noisy_m0trace(pb, block, boundaries, sigma_det,
rng)` (E16, frozen) already returns, for each accepted trial, a
sequence `[(m0_1, R_1), (m0_2, R_2), ..., (m0_8, R_8)]` for `M=2`'s 8
groups — **the exact raw material this contract needs, already
produced by already-gated code.** E16's own correction (§9.2/§10 of its
contract) discarded everything after a trial's first failure specifically
because post-failure group outcomes are not *independent* draws at their
own `m0` — the corrupted state propagates forward. That is not a bug to
route around here; it is the object of study. This contract asks,
precisely: **given the state *is* corrupted (`R_i` = False), does the
*next* group's recovery — at whatever `m0_{i+1}` that corrupted state
happens to produce — differ from what a clean-arrival group at the same
`m0_{i+1}` would show?**

**Why this could produce exactly the observed conservative bias:** if
`R_i` and `R_{i+1}` are *positively* correlated beyond what `m0_{i+1}`
captures — e.g. because whatever noise realization pushed group `i`'s
BQE rounding the wrong way tends to correlate with a *smaller* actual
error at group `i+1` (or vice versa: failures and successes cluster) —
then a chain's *whole-trial* success probability would be systematically
*higher* than the naive product-of-independent-marginals model
predicts, exactly the direction E9→E17's whole chain has repeatedly
found. This contract does not assume this mechanism; it tests for the
correlation whose existence would make it possible.

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| placement | `M=2` fixed boundaries `[2,4,6,8,10,12,14,16]` (E14,
  reused) — **not DP or greedy**; a fixed, simple, already-characterized
  placement is the right tool for isolating a *measurement* question,
  not a placement-optimization one |
| position pairs examined | all 7 adjacent pairs `(1,2), (2,3), ...,
  (7,8)` (group indices within the M=2 sequence) |
| σ_det | **not locked a priori** — located by a smoke-scale search
  (§7 gate 0, same discipline as E17 Part 4's gate 0c) maximizing the
  number of `(position pair, m0_{i+1} bin)` cells with **at least
  `n_min=200` trials in *both* the `R_i=True` and `R_i=False` subgroups**
  — the binding constraint is getting enough `R_i=False` cases (rare at
  low `σ_det`, common but uninformative at very high `σ_det` where
  nearly everything fails) |
| search acceptance bar | **quantified explicitly (Halt-and-Flag
  amendment D):** a candidate `σ_det` is acceptable only if it produces
  **≥20 eligible `(pair, m0)` cells overall** (at any binning level,
  §4) **and ≥5 of the 7 position pairs represented by at least one
  eligible cell.** The search chooses the candidate maximizing eligible
  cell count among those clearing this bar; if none clears it, HALT and
  report the full per-candidate table (same rule as E17 Part 4 — no
  silent loosening) |
| n_trials | **not locked a priori** — determined by the search (§7 gate
  0) together with `σ_det`: report the trial count needed to clear the
  cell-count bar above at the chosen `σ_det`, lock it, then run at that
  scale (likely large — hundreds of thousands of trials — since
  `R_i=False` is a minority outcome even at an informative `σ_det`;
  report the actual number reached, don't assume a round figure) |
| search/inference separation | **required (Halt-and-Flag amendment A,
  the most important one):** the search (gate 0) uses its own RNG
  namespace and its own trials — none of the search's observations
  enter the inferential dataset. Once `σ_det` and `n_trials` are frozen
  from the search, the main run (gate 2) draws **fresh trials from an
  independent RNG namespace** (analogous to E17 Part 4's
  `SEARCH_BLOCK_ID_OFFSET` pattern, applied to trial indices here — the
  search uses trial indices from one large, disjoint offset range, the
  main run starts fresh from index 0). No adaptive stopping in the main
  run, no re-examining or extending the search after seeing the main
  run's results. |
| E16 law constants (reference only, not used as the objective here) |
  `a = -4.79`, `β = 3.19` |
| noise axes | `sigma_phi = sigma_amp = 0` (unchanged) |

## 4. New code (additive, minimal) — Halt-and-Flag review required

`photonics/run_photonic_correlation_mechanism_sweep.py`:

- Reuses `run_chain_boundary_noisy_m0trace` (E16, `photonics/run_photonic_m0_dynamic_range_sweep.py`)
  **verbatim** — no new simulation code.
- `collect_pair_stats(sigma_det, n_trials, boundaries=M2_BOUNDARIES)` —
  runs `n_trials` accepted blocks; for each, for each adjacent pair
  `(i, i+1)`, records `(m0_{i+1}, R_i, R_{i+1})` **only for trials where
  groups `1..i-1` all succeeded** (clean arrival up to `i` — `R_i`
  itself may be True or False, that's the variable under study; groups
  *before* `i` must be clean so we know `R_i`'s own value isn't itself
  contaminated by an earlier failure). Accumulates a nested histogram:
  `{(pair, m0_{i+1}, R_i): [n_ok_{i+1}, n_total_{i+1}]}`.
- `search_operating_point(candidate_sigmas, n_search_trials)` — for each
  candidate `σ_det`, run a reduced-scale pass **using the search RNG
  namespace** and report, per position pair, the number of eligible
  `(m0_{i+1}_bin, R_i)` cells per §3's binning hierarchy — locating
  `σ_det` per §3's quantified acceptance bar.

**`m0_{i+1}` binning hierarchy — frozen deterministically before any
significance is computed (Halt-and-Flag amendment C):** a cell's
resolution is decided **only** by sample count at that resolution,
never by whether a given resolution happens to produce significance.
Fixed order, applied per `(pair, m0_{i+1})` region:

1. **Exact integer `m0_{i+1}`** — used if both `R_i` states reach
   `n_min=200` at this resolution.
2. **Width-2 bins**, deterministic grouping `bin = 2 * floor(m0/2)`
   (i.e. `{0,1}→0, {2,3}→2, ...`, never a bin chosen to straddle a
   specific value) — used only if level 1 failed and level 2 clears
   `n_min=200` in both `R_i` states.
3. **Width-4 bins**, deterministic grouping `bin = 4 * floor(m0/4)` —
   used only if levels 1–2 failed and level 3 clears `n_min=200`.
4. **Excluded** — if level 3 still doesn't clear `n_min=200` in both
   `R_i` states, the cell is dropped, not forced into an ever-wider bin.

The resolution actually used is recorded per cell in the output (§5) —
never silently mixed or chosen post hoc.

**Halt-and-Flag pre-review items:**
- **"Clean arrival up to `i`" must be enforced precisely**, matching
  E16's own established definition exactly (stop-at-first-failure logic,
  contract SS4 of `contract_photonics_m0_dynamic_range_2026-08-22.md`)
  — reuse that logic's exact semantics, don't reimplement a subtly
  different version.
- **Multiple comparisons:** 7 position pairs × however many `m0_{i+1}`
  bins clear the count bar is a sizeable number of tests — use the same
  Bonferroni-corrected two-proportion z-test convention E16 §9/§10
  established, not an uncorrected per-cell threshold.
- **The secondary residual-`m0_i` check (§1's full formula includes
  `m0_i`, not just `R_i`):** report it, but as exploratory, not a hard
  falsification criterion — stratifying further by `m0_i` on top of
  `(m0_{i+1}, R_i)` fragments the data quickly; only report where cell
  counts remain adequate, and don't let a null result there be read as
  ruling out an `m0_i` effect the data simply couldn't see.

## 5. Metrics & outputs

- **Primary:** per `(position pair, m0_{i+1})` cell with adequate counts,
  `P(R_{i+1}=True | R_i=True)` vs. `P(R_{i+1}=True | R_i=False)`,
  two-proportion z-test, Bonferroni-corrected across all tested cells
  (E16 §9/§10 convention).
- **Secondary, exploratory:** where counts permit, the residual `m0_i`
  check (§4) — does `m0_i` predict `R_{i+1}` beyond `(m0_{i+1}, R_i)`.
- **Aggregate:** fraction of tested cells showing a significant
  difference, the direction (does `R_i=False` predict *higher* or
  *lower* `R_{i+1}`, consistent or inconsistent with §2's proposed
  mechanism), and effect-size distribution across significant cells.
- Output: canonical JSON (`results/sweeps/correlation_mechanism_sweep.json`),
  frozen copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

**Two-part cell classification (Halt-and-Flag amendment B — effect size
alone is not sufficient without statistical support, and vice versa):**
for each tested cell, compute the Bonferroni-adjusted 95% CI for
`P(R_{i+1}|R_i=True) − P(R_{i+1}|R_i=False)`.
- **Statistically dependent:** CI excludes zero.
- **Materially dependent:** CI excludes zero **and** `|diff| > 0.05` — a
  cell can be statistically but not materially dependent (a real but
  tiny effect, e.g. `p1=0.30` vs `p2=0.33` with a large enough sample to
  resolve it) or, in principle, show a large point-estimate difference
  that isn't materially classified because its CI doesn't clear zero —
  both are reported, only the second drives the tiers below.

- **Independence (Confirmed):** <5% of tested cells statistically
  dependent, and **zero** cells materially dependent — `R_i` adds no
  detectable, meaningful predictive power beyond `m0_{i+1}`; the
  conservative calibration bias found throughout E9–E17 is not
  explained by this specific correlation mechanism, and remains
  unexplained (a genuinely informative null result, not a dead end —
  it would rule out the leading hypothesis and motivate looking
  elsewhere, e.g. at the ROTC angle-normalization interaction flagged
  much earlier in this investigation and never fully closed out).
- **Real dependence found:** ≥5% of cells statistically dependent, or
  any cell materially dependent — direct evidence of a correlation
  mechanism. Report the **direction** explicitly: `R_i=False → higher
  P(R_{i+1})` would be the counterintuitive-but-mechanism-consistent
  direction (§2); the opposite direction (`R_i=False → lower
  P(R_{i+1})`, i.e. failures cluster) would be a different, equally
  real finding requiring its own interpretation, not forced into §2's
  proposed story.
- **Mixed/inconclusive:** scattered statistical-but-not-material
  significance without a clear direction — report honestly as
  inconclusive at this `σ_det`/`n_trials`
  scale, not rounded into either tier.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0. Operating-point search (SS3/SS4), SEARCH RNG NAMESPACE ONLY: locate
#    sigma_det and n_trials clearing the quantified acceptance bar
#    (>=20 eligible cells, >=5/7 position pairs represented). Report the
#    search table; HALT and report (do not silently loosen the bar) if
#    no candidate clears it. These search trials are discarded, not
#    reused in gates 1-2 (SS3 search/inference separation).
cd /home/user/Projects/hardware/SPU
.venv/bin/python3 photonics/run_photonic_correlation_mechanism_sweep.py --search-only

# 1. Smoke pass at the located operating point, FRESH inference RNG
#    namespace (independent of gate 0's) -- report actual wall-clock,
#    extrapolate the full run's cost, same discipline as E17 Part 3/4's
#    gate 1 (not assumed cheap just because the simulation code itself
#    is simple).
PHOTONIC_TRIALS=2000 .venv/bin/python3 \
  photonics/run_photonic_correlation_mechanism_sweep.py

# 2. Full run (at the located sigma_det/n_trials, fresh inference
#    trials -- no adaptive stopping, no re-examining gate 0 afterward)
.venv/bin/python3 photonics/run_photonic_correlation_mechanism_sweep.py

# 3. Reproducibility: two full runs, bit-identical.

# 4. Aggregate analysis (SS5/SS6) -- Independence / Real dependence /
#    Mixed, with direction stated explicitly if dependence is found.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No modification to `greedy_place` or `optimal_placement`** —
  measurement only, per §1.
- **No corrected recovery law built from this contract's findings** —
  a separate, later, not-yet-authorized contract, contingent on finding
  real dependence here.
- **No claim about magnitude-vs-ranking implications beyond what this
  contract directly measures** — E17 Part 3/4 already established the
  *placement* question is not currently distinguishable from
  independence; this contract tests the *mechanism* question on its own
  terms, not to re-litigate placement.
- **No DP/greedy re-run** — `M=2` fixed placement only, per §3.
- **No new noise axes** — detector-noise only, unchanged from every
  prior contract in this chain.

## 9. Gate 0/1 report (2026-08-23) — full run authorized

**Gate 0 (search, disjoint namespace, 20,000 trials/candidate):**
`σ=3e-5` cleared the bar cleanly (21 eligible cells ≥20, 6/7 pairs
represented ≥5); the only candidate to clear it among
`[1e-6,3e-6,1e-5,3e-5,1e-4,3e-4]`. Locked.

**Gate 1 (smoke, 2,000 trials at the locked `σ_det`):** compute budget
is modest — extrapolated **~11 minutes for the full 300,000-trial run**
(rate ≈300–600 trials/sec) — no scope reduction needed, proceeding
directly to the full run.

**Preliminary signal, explicitly flagged as smoke-scale and not the
inferential result (per §3's search/inference separation — this is not
a violation of that separation, since `σ_det`, `N_MIN`, and the binning
hierarchy were already frozen before this smoke pass ran; nothing about
this observation selects any analysis parameter):** at only 2,000
trials, 3 cells already cleared `n_min=200` and **all 3 showed large,
significant effects in the same direction** — e.g. `pair=1 (groups
2→3), m0=10`: `P(R_3|R_2=True)=0.652` vs. `P(R_3|R_2=False)=0.302`, a
35-point gap (`z=10.5`). The direction is `R_i=False → lower P(R_{i+1})`
— i.e. **failures cluster**, the opposite of §2's originally proposed
"noise anti-correlates" mechanism, and explicitly the "different,
equally real finding" §6 anticipated might occur instead. Not treated
as the result — the full, properly-powered 300,000-trial run (§10) is
the actual inferential dataset.

## 10. Results (2026-08-23) — REAL DEPENDENCE FOUND, decisively

**All gates passed:** gate 0 (search, disjoint namespace) locked
`σ=3e-5`; gate 1 (smoke) authorized the full run at modest cost; gate 2
(full run, 300,000 fresh inferential trials, disjoint from the search's
namespace) produced 30 eligible cells across the frozen binning
hierarchy (all resolved at **exact-integer** `m0_{i+1}` resolution —
the coarser width-2/width-4 fallbacks were never needed at this trial
count); gate 3 (reproducibility, two full runs, bit-identical, sha256
`c12f8589f8d4a91337c379ff934bab4db6f34fcb2d09b12110781b9e02f576cf`).

**Gate 4 (aggregate): Real dependence found — 24/30 cells (80%)
materially dependent** (Bonferroni-adjusted CI excludes zero *and*
`|diff|>0.05`), far above the 5%-of-cells bar. **29 of 30 cells agree
on direction**: `R_i=False → lower P(R_{i+1})` — the *opposite* of §2's
originally proposed "noise anti-correlates" mechanism. **Failures
cluster.** The single non-matching cell (`pair=5, m0=12, diff=-0.0004,
z=-0.08`) is not remotely significant — noise around zero, not a
genuine reversal.

**Effect sizes are large, not marginal**, and vary systematically with
`m0_{i+1}` in an interpretable pattern:

| `m0_{i+1}` region | typical effect | interpretation |
|---|---|---|
| 2 (near-ceiling) | +0.63 to +0.64 | `R_i=True`→~1.0 recovery; `R_i=False`→~0.36 — the largest effects, where there's the most "room" for `R_i` to matter |
| 9–10 (transition) | +0.24 to +0.79 | still large, the mechanism's core operating region |
| 11 (steep part of cliff) | +0.05 to +0.08 | shrinking but still material |
| 12 (past the cliff) | not material (4/6 not even statistically significant) | both `R_i` states are already near-zero recovery — little room left for `R_i` to matter |

Every one of the 24 material cells has `z > 10` (several exceed `z=100`)
— this is not a borderline statistical result inflated by a huge sample;
the effect is large enough to be visible even at modest cell sizes (the
smallest material cell has `n_tot_false=327`, §9's smoke pass already
saw it at `n=2,000` total trials).

**Interpretation — `m0` is not a sufficient statistic for next-event
recovery probability.** The information `R_i` carries beyond
`m0_{i+1}` is plausibly the *specific* corrupted value a failed
group's BQE rounding produced, not just its bit-length (`m0` is a
coarse, single-integer descriptor of scale; two different corrupted
values can share the same `m0_{i+1}` while differing in exactly how far
they landed from a correct lattice point) — a concrete, testable
follow-on hypothesis, **not established by this contract**, which only
establishes that some such information exists, not what it is.

**This does not contradict E17 Part 3/4's placement-ranking finding —
it answers a different question.** `greedy_place` and `optimal_placement`
choose REGEN boundaries using the **noiseless** `m0` trajectory, computed
before any noise is drawn — `R_i` is a stochastic, per-trial *outcome*
that does not exist at compile time. A compile-time placement algorithm
structurally cannot condition on `R_i`, so this correlation, however
large, is not exploitable by the kind of optimizer E17 built, and does
not retroactively put E17 Part 3/4's "no evidence of a ranking effect"
finding in question. What it *does* explain is **why** whole-chain
success has been systematically higher than the naive independent-events
product model predicts throughout E9–E17: if `R_i` and `R_{i+1}` are
positively correlated (successes cluster, equivalently), a chain's true
joint success probability exceeds the product of its marginals — exactly
the direction of every conservative-calibration finding in this
investigation's history.

**One data caveat, reported explicitly:** pair 0 (groups 1→2) never
produced an eligible cell at any binning resolution — `m0_2` (the state
immediately after the first real combine op) is apparently too
concentrated a distribution to populate both `R_1` states at `n_min=200`
at this `σ_det`/trial count. The finding is established across pairs
1–6 (6 of the 7 adjacent positions), not all 7.

**Evidence artifacts:**
`results/sweeps/correlation_mechanism_sweep_frozen_v1_2026-08-23.json`,
sha256 `c12f8589f8d4a91337c379ff934bab4db6f34fcb2d09b12110781b9e02f576cf`;
`results/sweeps/correlation_mechanism_search_frozen_v1_2026-08-23.json`,
sha256 `f15163fa19c7e3798a6ae2d504b02e42bbbe442bb59bc0a85bff0f13cc9afcf4`.
Driver: `photonics/run_photonic_correlation_mechanism_sweep.py`.

