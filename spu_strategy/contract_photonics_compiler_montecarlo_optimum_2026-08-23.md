# Engineering Contract: Monte-Carlo Closeness-to-Optimum Check (E17 Part 3)

**Date:** 2026-08-23
**Contract ID:** `contract_photonics_compiler_montecarlo_optimum_2026-08-23.md`
**Status:** RAN TO COMPLETION 2026-08-23. **RESULT: DP near-optimal,
CONFIRMED at both σ_det points (20/20 blocks each)** — no evaluated
alternative ever beat DP's schedule outside noise. Important caveat: 39
of 40 blocks were saturated at perfect recovery, where any reasonable
same-N schedule ties trivially; the one genuinely informative block
(σ=1e-5, block 2, 0.9460 recovery) independently confirmed DP's
schedule was the actual best among all 91 fully-enumerated alternatives.
See §10.

**Implementation note, flagged before running (storage, not statistics):**
§5 calls for "per-repeat outcome vectors" for the paired analysis: 2,000
ints × up to 500 candidates × 40 blocks would produce an unworkably
large output file (compare E17's 8.3MB from 90K scalar records). The
paired `mean(D)`/`SE(D)` are computed in full during the run for every
candidate (nothing about the statistics is approximated), but only the
*summary* is retained per candidate in the output; raw per-repeat
vectors are kept only for DP's own schedule and the single best-observed
alternative per block (for auditability/spot-checking), not all
evaluated candidates. This is a storage decision, not a statistical
shortcut.

**Roles:**
- **Spec Author:** Claude, formalizing John's explicit choice (2026-08-23)
  of the Monte-Carlo comparison over the alternative (refitting a
  corrected model and re-running the DP against it) — the alternative
  was flagged as risking exactly the conflation ("better search" vs.
  "better model") E17 Part 2 was designed to avoid.
- **Halt-and-Flag Implementer:** review the per-block enumeration scope
  and compute budget (§3) before implementing — this is the most
  compute-intensive contract in the chain so far and needs an explicit
  cap, not an open-ended full enumeration.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_compiler_optimal_placement_2026-08-23.md` (E17
  Part 2) — the DP and its frozen dominating points (σ=1e-6, λ=0.01:
  mean 2.05 events, 1.0000 recovery; σ=1e-5, λ=0.01: mean 4.24 events,
  0.9853 recovery). `run_chain_boundary_noisy_diag` (E15) is **not**
  reused unmodified this time — the common-random-numbers requirement
  (§3/§4, added at Halt-and-Flag review) needs an addressable noise
  source, incompatible with that function's stateful sequential `rng`
  argument. A new scoring function is required, verified equivalent to
  the original via its own cross-check gate (§4) — the same discipline
  every substitute/generalized scorer in this chain has required
  (E14's `_diag`, E15's boundary generalization, E16's `m0trace`).
- `contract_photonics_compiler_regen_placement_2026-08-23.md` (E17) —
  the standing, still-open correlation hypothesis
  (`P(R_{i+1}|R_i,m0_i,m0_{i+1}) ≠ P(R_{i+1}|m0_{i+1})`), which this
  contract does not test directly but whose *consequence* (a gap
  between DP's chosen schedule and the true best schedule) it can
  detect without needing to characterize the correlation itself.

---

## 1. Objective

**For a sample of individual blocks, does the DP's chosen schedule
(from E17 Part 2, using the same event budget it itself selected)
achieve the highest — or statistically indistinguishable from the
highest — *actually simulated* recovery probability among all other
schedules using the same number of REGEN events for that same block?**

This directly measures how much headroom, if any, remains between "the
DP's answer under its own (known-conservative) objective" and "the true
best answer for that specific computation," without needing to first
characterize *why* the objective is conservative. If DP already lands
at or near the top for most sampled blocks, the correlation hypothesis
is a refinement, not a correction — the compiler is already close to
optimal in practice. If DP is measurably below the best alternative for
a sizable fraction of blocks, that is direct, model-free evidence of
real remaining headroom, motivating the correlation investigation on
stronger grounds than "the aggregate calibration is off."

**Explicitly not attempted:** searching over *all* possible schedules
regardless of event count (the space is astronomically large across
different N) — this contract fixes N to DP's own per-block choice and
asks only "was this placement, at this N, the best one," not "was this
N the best N" (E17 Part 2's λ sweep already explores the N-vs-reliability
trade-off at the aggregate level). No new noise model, no refitting.

## 2. Objective grounding

E17 Part 2's DP chooses a schedule by maximizing a **predicted** score
built from the closed-form, known-conservative `P_event_fit`. Two
distinct explanations are consistent with "DP dominates greedy but its
own predictions stay conservative":

1. **The conservative bias is roughly uniform** across candidate
   segments (a constant or near-constant offset in `logp`) — in which
   case it does not distort the *ranking* of candidate schedules, only
   the absolute predicted probability. DP would then already be
   choosing the (or a near-) best schedule, and the correlation
   hypothesis is a footnote about magnitude, not placement quality.
2. **The conservative bias varies by segment/context** (e.g. depends on
   which specific `m0` transitions or op patterns are involved) — in
   which case it *would* distort rankings, and DP could be leaving a
   *better-placed*, same-event-count schedule undiscovered.

Only a **direct, model-free comparison** — Monte-Carlo evaluating
multiple candidate schedules against the real simulator — can
distinguish these. That is what this contract does.

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| σ_det test points | `[1e-6, 1e-5]` (E17 Part 2's two points) |
| λ (fixes DP's schedule) | `0.01` — the strongest dominating point at
  both σ (E17 Part 2 §9) |
| n_blocks sampled | 20 per σ_det (40 total) — the first 20 accepted
  trials by trial index, not cherry-picked. **Explicitly a screening
  experiment, not a population-level estimate** (Halt-and-Flag review):
  the §6 90% threshold is ~18/20 — a single block shifts the headline
  classification by 5 points. Report the raw count (`k`/20), not just
  the pass/fail label. |
| candidate-schedule cap per block | `interior_positions` **asserted**
  to have length 14 in code (not assumed). If `C(14, N-1) ≤ 500` (N =
  DP's own event count for that block), enumerate **all** same-N
  schedules; otherwise **randomly sample 500** (seeded, reproducible).
  Terminology (Halt-and-Flag review): report `enumeration_mode = full
  \| sampled`, `n_total_schedules = C(14,N-1)`, `n_evaluated_schedules`.
  When `sampled`, the conclusion is **"DP was not beaten among the 500
  sampled alternatives,"** not "DP is rank 1" — `rank_among_evaluated`
  is a distinct field from any claim about the full schedule space. |
| Monte-Carlo repeats per candidate schedule | 2,000, using **common
  random numbers** (§4) — every candidate for a given (block, repeat)
  sees the same underlying noise realization; only the boundary
  placement differs. Schedules compared by their **full boundary list**,
  never by event count alone (Halt-and-Flag review, same discipline the
  E17-Part-2 `segment_m0` bug established the need for). |
| E16 law constants (frozen, reference only, not the objective here) |
  `a = -4.79`, `β = 3.19` |
| noise axes | `sigma_phi = sigma_amp = 0` (unchanged) |

**Compute budget — smoke-measured, not assumed (Halt-and-Flag review):**
the nominal ≈640M op-equivalent estimate (40 blocks × 500 candidates ×
2,000 repeats × O(16)) is not trusted on its own. The smoke gate (§7
gate 1) must report **median and maximum candidates/block, median and
maximum wall-time/block, and extrapolated total runtime** before the
full run is authorized — Python-level per-call overhead could make the
real bottleneck very different from the nominal op count. If the
extrapolated cost is unacceptable, the fix is reducing `n_blocks` or
`repeats`, **reported explicitly and re-locked in this contract before
proceeding** — never silently shrunk mid-run.

## 4. New code (additive) — Halt-and-Flag review required before running

`photonics/run_photonic_compiler_montecarlo_optimum_sweep.py`:

- `build_nd_table(master, block_id, repeat, sigma_det)` — the
  common-random-numbers primitive (Halt-and-Flag review). Returns a
  precomputed table of detector-noise draws, one 2-lane×4-component
  Gaussian(0,σ_det) vector **per op position 1..16**, deterministically
  derived from `(master, block_id, repeat)` alone — **not** from how
  many draws a given candidate's evaluation would sequentially consume.
  This is what makes the noise addressable: two candidates that share a
  boundary position see bit-identical noise there, and every candidate
  for a given `(block_id, repeat)` draws from the same table regardless
  of its own boundary count or positions.
- `score_schedule_addressable(pb, block, boundaries, nd_table)` — a new
  scoring function (replacing `run_chain_boundary_noisy_diag` for this
  contract only, per the normative-references note above): identical
  control flow, but pulls `nd_last` from `nd_table[i-1]` at op position
  `i` instead of drawing from a stateful `rng`, and uses the fixed
  `dp=[0,0], ap=[1,1]` implied by `sigma_phi=sigma_amp=0` directly
  (skipping the now-pointless draws) rather than calling
  `_noise_per_op`. Returns `(ok, qr0)`, matching the original's
  whole-trial semantics (AND across all boundaries, not a short-circuit
  on first failure).
- `same_n_schedules(n_boundaries, interior_positions, cap, rng)` —
  enumerates or samples boundary sets of size `n_boundaries` from
  `interior_positions` (§3), asserting `len(interior_positions) == 14`.
- `monte_carlo_recovery(pb, block, boundaries, master, block_id,
  sigma_det, n_repeats)` — for `repeat` in `range(n_repeats)`: build
  (or reuse — see caching note below) `nd_table(master, block_id,
  repeat, sigma_det)`; score via `score_schedule_addressable`. Returns
  the **per-repeat outcome vector**, not just an aggregate `n_ok` — the
  paired-difference statistics (§5) need the vector, not a summary.
- `evaluate_block(block, block_id, sigma_det, lam, master)` — computes
  DP's own schedule (E17 Part 2's `optimal_placement`, reused
  verbatim); enumerates/samples same-N alternatives; Monte-Carlo
  evaluates **every** candidate, including DP's own (never reusing E17
  Part 2's one-shot observation — Halt-and-Flag review), against the
  **same** `nd_table` per repeat; returns all candidates' per-repeat
  outcome vectors plus `rank_among_evaluated`, `enumeration_mode`,
  `n_total_schedules`, `n_evaluated_schedules`.

**Caching note:** since `nd_table` depends only on `(block_id, repeat)`,
build it **once per repeat** and reuse it across all candidates for that
block — not once per (candidate, repeat), which would be correct but
wasteful (the whole point of CRN is one shared table per repeat).

**Halt-and-Flag pre-review items:**
- **CRN correctness gate (replaces the earlier "RNG independence" item
  — superseded by the redesign):** confirm (a) `nd_table` is identical
  across candidates for the same `(block_id, repeat)` (by construction,
  but verify the code doesn't accidentally thread candidate identity
  into the derivation); (b) tables differ across `repeat` values for
  the same block (genuine independence between repeats); (c) tables
  differ across `block_id` values (no cross-block collision).
- **Equivalence cross-check (new, required by the normative-references
  change above):** for a sample of (block, single boundary list, seed)
  triples, confirm `score_schedule_addressable` reproduces
  `run_chain_boundary_noisy_diag`'s exact `(ok, qr0)` when the table is
  built to capture the same sequential rng's nd draws at every op
  position for that specific run — establishes the new function is a
  faithful reimplementation, not merely "differently wrong."
- **Fairness of the comparison:** already folded into `evaluate_block`'s
  spec above — DP scored under the identical protocol as every
  alternative, explicit design constraint, not an afterthought.
- **Degenerate N:** if DP's own `n_boundaries` for a block is 1 (just
  `[16]`) there are no alternatives (`C(14,0)=1`) — a valid, reportable
  "no alternatives exist" case, not an error.

## 5. Metrics & outputs

- **Primary — paired-difference statistic (Halt-and-Flag review,
  supersedes the original independent-CI plan):** for each evaluated
  candidate `j` and DP (`D`), using the shared per-repeat outcome
  vectors, compute `D_r = X_{j,r} - X_{D,r}` for each repeat `r`, then
  `mean(D)` and `SE(D) = std(D, ddof=1) / sqrt(R)` directly from the
  paired differences (this automatically captures the variance
  reduction from positive correlation between `X_j` and `X_D` on shared
  noise realizations — the entire point of CRN — without needing to
  estimate the covariance term separately). Report per candidate:
  `mean(D)`, `95% CI = mean(D) ± 1.96·SE(D)`, and whether that interval
  excludes 0 (candidate beats DP) or DP excludes candidate (DP beats
  candidate). **Explicitly labeled a candidate-level comparison, not a
  family-wise guarantee** (Halt-and-Flag review) — selecting the best
  of up to 500 evaluated candidates and reporting its own pairwise CI
  does not carry ordinary 95% coverage for "the maximum specifically";
  the contract does not claim it does.
- **Per block:** `rank_among_evaluated` (1 = best observed), whether
  the best-observed alternative's paired-difference CI excludes 0
  relative to DP (a real, not noise-level, gap), `enumeration_mode`,
  `n_total_schedules`, `n_evaluated_schedules`.
- **Aggregate, per σ_det — reported as a screening result (§3):**
  `k`/20 blocks where DP is rank-1-or-CI-tied; distribution of
  `mean(D)` for the best alternative where DP is *not* tied.
- Output: canonical JSON
  (`results/sweeps/compiler_montecarlo_optimum_sweep.json`), per-block
  and per-candidate records (including per-repeat outcome vectors —
  needed for the paired analysis, not optional), frozen copy with
  sha256, README entry.

## 6. Falsification criteria (non-vacuous)

Reported as a **screening outcome on 20 blocks per σ_det**, not a
population estimate (§3) — the classification below is an engineering
threshold, not a statistical claim about all possible blocks.

- **DP near-optimal (Confirmed):** DP is rank-1 or CI-tied-for-rank-1
  in ≥18/20 sampled blocks at both σ_det — the conservative bias is
  ~uniform (§2 explanation 1); the correlation hypothesis is a
  magnitude footnote, not a placement-quality issue.
- **Partial headroom:** DP is CI-tied-for-best in 10–17/20 blocks —
  report the gap distribution for the remainder; motivates but does not
  mandate a follow-on correlation investigation.
- **Real headroom (would motivate the correlation investigation
  directly):** DP is CI-tied-for-best in <10/20 sampled blocks, or the
  mean `D` (best − DP) across non-tied blocks exceeds 0.02 absolute —
  concrete, model-free evidence that placement quality itself (not just
  aggregate calibration) has room to improve, independent of whatever
  mechanism explains it.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0a. CRN correctness gate (SS4): table identity/independence checks.
# 0b. Equivalence cross-check (SS4): score_schedule_addressable vs.
#     run_chain_boundary_noisy_diag on matched (block, boundaries, seed).

# 1. Smoke pass -- SMALL n_blocks/n_repeats, but must report: median and
#    max candidates/block, median and max wall-time/block, extrapolated
#    total runtime (SS3). Full-run authorization is conditional on this
#    report, not automatic.
cd /home/user/Projects/hardware/SPU
PHOTONIC_MC_BLOCKS=3 PHOTONIC_MC_REPEATS=200 .venv/bin/python3 \
  photonics/run_photonic_compiler_montecarlo_optimum_sweep.py

# 2. Full run (per SS3's locked n_blocks/repeats/cap -- or an explicitly
#    re-locked, reported adjustment if gate 1's extrapolation demands it)
.venv/bin/python3 photonics/run_photonic_compiler_montecarlo_optimum_sweep.py

# 3. Reproducibility: two full runs, bit-identical.

# 4. Aggregate analysis (SS5/SS6) -- screening result, k/20 per sigma.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No search over N** (event count) — fixed to DP's own per-block
  choice at λ=0.01; the N-vs-reliability trade-off is E17 Part 2's own
  scope, already covered.
- **No refitting E16's law or building a corrected objective** — this
  contract is model-free by design (§1); if it finds real headroom, the
  *next* contract (not this one) would investigate why.
- **No new σ_det points** — reuses E17 Part 2's two.
- **No claim about the correlation mechanism itself** — this contract
  can only detect whether a gap exists, not explain one if found.

## 9. Smoke pass compute report (2026-08-23) — full run authorized

Gate 0a/0b: clean (table identity/independence confirmed; 0/300
mismatches on the equivalence cross-check against
`run_chain_boundary_noisy_diag`). Gate 1 (3 blocks/σ, 200 repeats):
`n_evaluated` candidates/block highly skewed — 1, 1, 14, 91, 91, 501
(median 52.5, max 501, hit the cap once). Measured rate ≈1,632
(candidate×repeat) evaluations/sec. Extrapolated full run (20 blocks/σ
× 2σ × 2,000 repeats): **~95 minutes**, with substantial uncertainty
given the 6-block smoke sample's skew (worst case, several hours if
many of the 40 real blocks hit the 500-candidate cap). Reported to
John explicitly per §3's requirement; **authorized to run as locked**
(no parameter reduction) — accepting the runtime uncertainty rather
than re-scoping.


## 10. Results (2026-08-23) — DP near-optimal, CONFIRMED, with an
## important power caveat

**All gates passed:** gate 0a/0b (table identity/independence
confirmed; 0/300 mismatches on the equivalence cross-check against
`run_chain_boundary_noisy_diag`); gate 1 (smoke, §9); gate 2 (full run,
40 blocks); gate 3 (reproducibility, two full runs — each ~80–90
minutes — bit-identical, sha256
`4bf394082692abbe1a9d32516d814dc0728d735c0b6dd9653efda4327a67b05d`).

**Gate 4 (aggregate, per §6's screening-experiment convention):
CONFIRMED at both σ_det points — 20/20 blocks each**, decisively above
the 18/20 threshold. `best_beats_dp_ci` was `False` for every single
block across the entire run — no evaluated alternative ever beat DP's
schedule outside noise, at either σ_det.

**Important caveat, reported honestly rather than declaring a clean
win (Halt-and-Flag discipline):** 39 of the 40 blocks have
`dp_recovery_mc = 1.0000` — DP's schedule (and, necessarily, every
alternative it's compared against) achieves perfect recovery across all
2,000 repeats. At the ceiling, *any* reasonable same-N schedule ties
trivially (`mean_d = 0.00000` exactly, `CI = [0,0]` exactly) — this
confirms DP is not worse than any alternative, but the comparison has
essentially no power to distinguish "DP found the true optimum" from
"recovery is saturated regardless of placement, for any schedule with
this many events." This is a direct consequence of testing at E17 Part
2's *dominating* operating point (λ=0.01, already selected because it
achieves near-perfect reliability) — informative for confirming no
regression, not for detecting a subtle ranking advantage.

**The one genuinely informative data point:** block 2 at σ=1e-5
(`dp_recovery_mc = 0.9460`, not saturated) is the sole case with real
variance. Verified directly (not inferred from the aggregate): DP's own
3-boundary schedule `[3, 13, 16]` was independently confirmed as
`best_boundaries` — i.e., DP's schedule achieved the *highest* Monte-Carlo
recovery among all 91 fully-enumerated same-N alternatives (`C(14,2)=91`,
full enumeration, not sampled) for that specific block, at 1,892/2,000
successes. This is the one case where "DP wins" is a substantive claim
about search quality, not a ceiling artifact, and it held.

**Interpretation:** at E17 Part 2's own dominating operating point
(λ=0.01, the two σ_det values it was shown to dominate greedy at), DP's
schedule choice is never beaten and, in the one block where the
comparison had real statistical power, was genuinely the best among all
enumerated alternatives. Per §2's two-explanation framing: this is
consistent with explanation 1 (the conservative calibration bias is
roughly uniform across candidate segments, so it does not distort
rankings at this operating point) rather than explanation 2. **Scope
caveat:** this was tested only at λ=0.01 and two σ_det values where
recovery is already high — it does not rule out explanation 2 holding
at a different operating point (e.g. a more aggressive λ, or a σ_det
where recovery is more marginal across more blocks) where saturation
would not mask a ranking-quality gap. A follow-on contract targeting a
less-saturated regime (e.g. λ chosen to land `dp_recovery_mc` reliably
in the 0.5–0.9 band across most sampled blocks, not just one) would give
this method its fair test — not attempted here, per §8's non-goals.

**Evidence artifact:**
`results/sweeps/compiler_montecarlo_optimum_sweep_frozen_v1_2026-08-23.json`,
sha256 `4bf394082692abbe1a9d32516d814dc0728d735c0b6dd9653efda4327a67b05d`.
Driver: `photonics/run_photonic_compiler_montecarlo_optimum_sweep.py`.

