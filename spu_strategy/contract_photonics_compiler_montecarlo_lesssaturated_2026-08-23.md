# Engineering Contract: Monte-Carlo Optimum Check at a Less-Saturated Operating Point (E17 Part 4)

**Date:** 2026-08-23
**Contract ID:** `contract_photonics_compiler_montecarlo_lesssaturated_2026-08-23.md`
**Status:** RAN TO COMPLETION 2026-08-23. **RESULT: DP near-optimal,
CONFIRMED (20/20 tied-or-best, 0/20 beaten), with real statistical
power this time — 11/20 blocks (55%) genuinely in the `[0.2,0.8]`
target band**, versus E17 Part 3's 1/40. No evidence of a
placement-ranking effect has been found across either operating
regime tested to date. See §10.

**Status (frozen-spec history):** FROZEN SPEC (2026-08-23). Halt-and-Flag review applied four
amendments before freeze: (1) gate 0c's search classification corrected
from a mismatched `(0.02,0.98)` coarse band to the exact `[0.2,0.8]`
target band at reduced precision (`n_search_repeats=1,000`), with the
bar restated as `≥10/20` blocks; (2) the operating-point search stated
explicitly as a locating procedure, not an inferential test — the final
classification is conditional on the selected `σ_det`; (3) independent
RNG namespaces for block generation, the search step, and the main run
stated explicitly; (4) §6's "Confirmed" tier relabeled "DP near-optimal
in this screening sample" to prevent the result reading as a universal
claim. Awaiting authorization to run.

**Roles:**
- **Spec Author:** Claude, formalizing the explicit follow-up flagged by
  both John/GTP's E17 Part 3 synthesis (2026-08-23: "if you do pursue
  it... deliberately choose an operating point where `0.2 ≲ P_recover
  ≲ 0.8` for a substantial fraction of blocks") and the design rule
  doc's own scope note (`docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md`
  §4: "a genuinely discriminating test... has not been run").
- **Halt-and-Flag Implementer:** review the operating-point search
  method (§4) — this contract adds exactly one new mechanism to an
  otherwise fully-reused pipeline, and that mechanism needs its own
  scrutiny before the (potentially large, per §3's compute note) full
  run is authorized.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_compiler_montecarlo_optimum_2026-08-23.md` (E17
  Part 3) — this contract's entire methodology (common random numbers,
  `score_schedule_addressable`, `same_n_schedules`, paired-difference
  statistics, sampled-rank semantics, screening-experiment framing) is
  **reused verbatim**, already gated (0/300 equivalence-cross-check
  mismatches, CRN identity/independence confirmed) — not re-derived or
  re-verified from scratch here. The one thing E17 Part 3 could not
  answer with real power: 39 of its 40 sampled blocks saturated at
  perfect recovery, where any reasonable same-N schedule ties trivially.
  This contract exists to close that specific gap, nothing else.
- `contract_photonics_compiler_optimal_placement_2026-08-23.md` (E17
  Part 2) — the DP (`optimal_placement`), reused verbatim; its own
  frontier data (`λ` sweep at `σ_det ∈ {1e-6, 1e-5}`) is the starting
  point for locating a less-saturated `σ_det` here.
- `docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md` §4 — states the scope
  limitation this contract addresses, and the target band explicitly
  (`0.2 ≲ P_recover ≲ 0.8`).

---

## 1. Objective

**Repeat E17 Part 3's Monte-Carlo closeness-to-optimum test — does the
DP's chosen schedule beat every same-event-count alternative when
directly simulated? — at a deliberately located operating point where a
substantial fraction of sampled blocks have genuinely non-saturated
recovery, so the aggregate result carries real statistical power across
most of the sample, not just one block out of forty.**

This is not a new hypothesis and not a new methodology — it is the same
question, asked at an operating point chosen specifically to give the
comparison something to distinguish. E17 Part 3's 20/20-and-20/20
"Confirmed" result is genuine but weak evidence for 39 of its 40 data
points (which tied trivially at the ceiling); this contract is designed
to produce genuinely strong evidence, in either direction.

**Explicitly not attempted:** any change to `λ` (fixed at `0.01`,
matching E17 Part 2/3, for direct comparability) — only `σ_det` is
searched. No new placement algorithm, no refitting E16's law, no
correlation-mechanism investigation. If this contract finds real
headroom (§6), the mechanism investigation is separate, later,
not-yet-authorized work — same discipline as E17 Part 3 §1/§8.

## 2. Objective grounding

E17 Part 3 tested `σ_det ∈ {1e-6, 1e-5}` at `λ=0.01` — exactly E17 Part
2's *dominating* points, chosen because DP achieves near-perfect
reliability there. That was the right choice for validating "DP beats
fixed-`M` and greedy" (E17/E17 Part 2's questions), but it is the wrong
choice for "is DP's specific schedule choice better than same-N
alternatives" (E17 Part 3's question) — at the ceiling, that question is
largely moot. A useful operating point for *this* contract needs
`m0_safe(σ_det, P_target=0.999)` to sit close to where typical blocks'
own `m0` trajectories actually land, not comfortably below them.

**No formula reliably predicts this in advance** (§1's law describes
*per-event* probability given `m0`, not the *distribution* of `m0`
values a block's DP-chosen schedule will produce at a given `σ_det`) —
so §3 does not lock `σ_det` a priori. Instead, §7 gate 0c is a dedicated
search: sweep a candidate grid, measure the empirical fraction of
sampled blocks landing in the target band at cheap scale, and lock
whichever candidate satisfies §3's threshold — reported explicitly,
following the exact discipline E9/E13/E14 used to lock their own grids
from smoke passes, not assumed correct from a back-of-envelope
derivation.

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| λ | `0.01` (fixed, matching E17 Part 2/3 — not searched) |
| σ_det | **not locked a priori** — located by §7 gate 0c's search over
  a candidate grid `[1.5e-5, 2e-5, 2.5e-5, 3e-5, 4e-5, 5e-5, 7e-5, 1e-4]`
  — **widened by explicit amendment after the first search pass**
  (2026-08-23): the initial grid's best candidate, `σ=5e-5`, landed at
  9/20, one block short of the ≥10/20 bar. Per §4's own Halt-and-Flag
  rule (no silent grid-widening or threshold-lowering), this was
  reported to John and he chose to widen the grid rather than lower the
  bar. Added: `[4.5e-5, 5.5e-5, 6e-5]`, bracketing the observed
  non-monotonic peak (in-band counts across the original 8 points:
  1,4,5,3,8,9,5,0 — not a smooth function of `σ_det`). **Checked, not
  assumed, while the main run was pending (halt-and-flag correction of
  an initial wrong guess):** the natural first guess — that this comes
  from `N` (DP's event count) shifting in discrete steps as `σ_det`
  grows — is directly contradicted by the search data: `N`'s
  distribution across the 20 blocks is nearly identical for every
  `σ_det` from 1.5e-5 through 5e-5. The real explanation is simpler:
  every block's `dp_recovery_est` decreases **perfectly monotonically**
  with `σ_det` (verified directly, all 20 per-block trajectories), and
  the aggregate in-band *count* is a superposition of 20 individually-
  monotonic transition curves, each crossing `[0.2,0.8]` at a different
  `σ_det` set by that block's own `m0` profile. Most of this sample's
  blocks happen to cross in the 3e-5–6e-5 window, producing the
  observed peak — no discrete mechanism required. —
  choosing the value that maximizes the count of `n_search_blocks=20`
  blocks with `dp_recovery_mc ∈ [0.2, 0.8]` (measured at
  `n_search_repeats=1,000` — the **same** `[0.2,0.8]` band the main
  experiment targets, not a coarser proxy; Halt-and-Flag review caught
  an earlier draft's mismatch here, see §4) — locked, and reported,
  before the main smoke pass (§7 gate 1) |
| target band | `0.2 ≤ dp_recovery_mc ≤ 0.8` for **≥10/20** sampled
  blocks at the locked `σ_det` (measured at gate 0c's `n_search_repeats`
  precision) — the explicit bar the search (§7 gate 0c) must clear
  before proceeding; if no candidate in the grid clears it, HALT and
  report rather than silently picking the closest candidate or
  loosening the bar |
| n_blocks sampled | 20 per the locked σ_det (same scale as E17 Part 3,
  for direct comparability) — **explicitly a screening experiment**,
  same caveat as E17 Part 3 §3 |
| candidate-schedule cap per block | 500, same rule as E17 Part 3
  (full enumeration when `C(14,N-1)≤500`, else reproducibly sampled) —
  **flagged: likely to bind more often here than in E17 Part 3**, since
  a less-saturated (higher) `σ_det` implies a lower `m0_safe`, which
  the DP compensates for with *more* REGEN events (larger `N`), and
  `C(14,N-1)` peaks sharply around `N-1=7` (`C(14,7)=3432`) — so this
  contract may spend more of its run at the cap than E17 Part 3 did |
| Monte-Carlo repeats per candidate schedule | 2,000, common random
  numbers, paired-difference statistics — identical to E17 Part 3 |
| E16 law constants (frozen, reference only) | `a = -4.79`, `β = 3.19` |
| noise axes | `sigma_phi = sigma_amp = 0` (unchanged) |

**Compute budget — smoke-measured, not assumed equal to E17 Part 3's
(Halt-and-Flag concern, flagged at draft time):** §3's candidate-cap
note above means this run could be *more* expensive than E17 Part 3's
~80–90 minutes per run, not less, despite reusing identical machinery.
The smoke gate (§7 gate 1) must report the same measurements E17 Part
3's did (median/max candidates per block, median/max wall-time per
block, extrapolated total) before the full run is authorized — do not
assume E17 Part 3's timing carries over.

## 4. New code (additive, minimal) — Halt-and-Flag review required

`photonics/run_photonic_compiler_montecarlo_lesssaturated_sweep.py`:

- Imports and reuses, **unmodified**, from
  `run_photonic_compiler_montecarlo_optimum_sweep.py`: `build_nd_table`,
  `score_schedule_addressable`, `same_n_schedules`, `paired_stats`,
  `evaluate_block` (parameterized by `sigma_det`, already generic).
  **No new scoring or CRN code** — E17 Part 3's own equivalence and CRN
  gates already cover this machinery; re-running them here would be
  redundant, not additional rigor (Non-Goals, §8).
- `search_operating_point(candidate_sigmas, lam, master, n_search_blocks=20,
  n_search_repeats=1000)` — the one new function. For each candidate
  `σ_det`, evaluate `n_search_blocks` blocks' DP schedules (via
  `optimal_placement`, E17 Part 2, reused verbatim) at
  `n_search_repeats=1,000` (enough precision to apply the **same**
  `[0.2,0.8]` band the main experiment targets — not a coarser proxy;
  see the Halt-and-Flag correction below), and report the count landing
  in `[0.2, 0.8]`. Returns the chosen `σ_det` and the full per-candidate
  report (not just the winner — the rejected candidates' counts are
  part of the evidence trail for why this `σ_det` was chosen).

**The operating-point search is a locating procedure, not an
inferential test** (Halt-and-Flag review, stated explicitly per
review): the selected `σ_det` is treated as fixed only after gate 0c
completes, and the final E17 Part 4 classification (§6) is explicitly
**conditional on that selected operating point** — it is not an
unconditional claim across `σ_det`. The search statistics themselves
(which candidates were tried, their counts) are part of the evidence
trail for *how* the operating point was chosen, not part of the
hypothesis test itself.

**RNG namespaces, stated explicitly (Halt-and-Flag review):** block
generation, the operating-point search (gate 0c), and the main
Monte-Carlo evaluation (gate 2) use **independent RNG derivations**,
even though the search and main run operate on the *same* first-20
generated blocks (intentional — this lets the cheap search estimate be
compared against the final, full-precision estimate for those same
blocks as an internal consistency check, not a data-reuse concern). Do
not let the search step's noise draws leak into or share state with the
main run's `nd_table` derivation.

**Halt-and-Flag pre-review items:**
- **Search-step classification band was originally mis-specified —
  corrected here, before implementation:** an earlier draft proposed a
  coarser `(0.02, 0.98)` "roughly saturated or not" band for the search
  step, distinct from the main experiment's `[0.2,0.8]` target. Caught
  at Halt-and-Flag review: those are not equivalent — a `σ_det`
  producing e.g. 18/20 blocks at 0.05–0.15 would pass the coarse
  `(0.02,0.98)` filter while having almost no blocks in the actual
  target band, silently defeating the contract's purpose. **Fixed: the
  search step uses the exact same `[0.2,0.8]` band as §3's target,
  just measured at reduced precision (`n_search_repeats=1,000` instead
  of the main run's 2,000) — a precision difference, not a definitional
  one.**
- **No σ_det found in the candidate grid clears the ≥10/20 bar:** a
  valid, reportable outcome, not an error — HALT, report the full
  per-candidate count table, and do not silently loosen the threshold
  or widen the grid without explicit authorization.

## 5. Metrics & outputs

Identical to E17 Part 3 §5 (rank_among_evaluated, paired-difference
`mean(D)`/`SE(D)`/CI per candidate, enumeration_mode/n_total/n_evaluated
per block, k/20 aggregate) — **plus**, new to this contract: the
operating-point search report (§4) as its own top-level section of the
output JSON, and a **saturation comparison against E17 Part 3**:
fraction of blocks with `dp_recovery_mc ∈ [0.2,0.8]` here vs. E17 Part
3's 1/40, reported explicitly as the direct measure of whether this
contract achieved its stated purpose (§1) regardless of the
Confirmed/Partial/Real-headroom outcome.

Output: canonical JSON
(`results/sweeps/compiler_montecarlo_lesssaturated_sweep.json`),
frozen copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

Same three-tier structure as E17 Part 3 §6, thresholds unchanged
(Confirmed ≥18/20, Partial 10–17/20, Real headroom <10/20, both
"CI-tied-for-best" defined identically) — **but relabeled to scope the
claim to this screening sample explicitly** (Halt-and-Flag review: the
label must not read as a universal or proven-optimal claim):

- **DP near-optimal in this screening sample (Confirmed):** DP is
  rank-1 or CI-tied-for-rank-1 in ≥18/20 sampled blocks at the located
  `σ_det`. Not "DP is proven near-optimal" — a 20-block screening
  result, conditional on the searched-and-locked operating point (§4).
- **Partial headroom in this screening sample:** 10–17/20.
- **Real headroom in this screening sample:** <10/20, or mean gap
  exceeds 0.02 absolute across non-tied blocks.

Reported **with the caveat inverted relative to E17 Part 3**: where E17
Part 3's Confirmed result carried a power caveat (most blocks
uninformative), this contract's result — whichever tier it lands in —
should carry a **power *credit***: if §4's search successfully locates
a `σ_det` with ≥10/20 blocks genuinely in-band, the resulting
classification is materially stronger evidence than E17 Part 3's,
because most of the 20 blocks are actually testing something. State the
achieved in-band count alongside the tier, not just the tier alone. If
Real headroom is found, that motivates — but does not itself
constitute — a follow-on correlation-mechanism investigation (§1/§8,
separate, not authorized by this contract).

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0a/0b. NOT re-run -- E17 Part 3's CRN correctness and equivalence
#        cross-check already cover the reused, unmodified machinery
#        (SS4/SS8). Re-verify only if this contract's own code review
#        finds an unexpected interaction (report if so).

# 0c. Operating-point search (SS4): locate sigma_det from the candidate
#     grid, clearing the ≥10/20 in-band bar. HALT and report if none does.
cd /home/user/Projects/hardware/SPU
.venv/bin/python3 photonics/run_photonic_compiler_montecarlo_lesssaturated_sweep.py --search-only

# 1. Smoke pass at the LOCKED sigma_det -- must report the same
#    compute-budget measurements E17 Part 3's did (SS3), not assumed.
PHOTONIC_MC_BLOCKS=3 PHOTONIC_MC_REPEATS=200 .venv/bin/python3 \
  photonics/run_photonic_compiler_montecarlo_lesssaturated_sweep.py

# 2. Full run (per SS3's locked n_blocks/repeats/cap at the located sigma_det)
.venv/bin/python3 photonics/run_photonic_compiler_montecarlo_lesssaturated_sweep.py

# 3. Reproducibility: two full runs, bit-identical.

# 4. Aggregate analysis (SS5/SS6) -- screening result, k/20, with the
#    in-band-fraction power credit stated alongside.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No re-verification of CRN/equivalence machinery** (§4) — already
  gated by E17 Part 3, reused verbatim.
- **No λ search** — fixed at `0.01` for direct comparability to E17
  Part 2/3; a `λ` sweep at a fixed `σ_det` is a separate, later,
  explicitly-authorized contract if motivated by this one's results.
- **No refitting E16's law or building a corrected objective** — same
  discipline as E17 Part 2/3.
- **No correlation-mechanism investigation**, even if this contract
  finds real headroom (§6) — a separate, later, not-yet-authorized
  contract would follow up on *why*, not this one.
- **No widening the candidate `σ_det` grid or lowering the ≥10/20 in-band
  bar** if the search (gate 0c) fails to clear it — report and halt,
  per §4's Halt-and-Flag item, rather than silently relaxing the target.

## 9. Smoke pass compute report (2026-08-23) — full run authorized

3 blocks, 200 repeats: `n_evaluated` = 501 (sampled, hit cap), 14
(full), 364 (full) — confirms §3's flagged expectation that `σ=4.5e-5`
pushes more blocks toward the 500-candidate cap than E17 Part 3's
points did. Measured rate ≈1,529 evaluations/sec (consistent with E17
Part 3's ≈1,632/sec). Extrapolated full run: **~2.1 hours/run, ~4.3
hours total for both reproducibility runs** — larger than E17 Part 3,
as anticipated, with the same 3-block-sample uncertainty caveat as
before. Reported to John explicitly per §3's requirement; **authorized
to run as locked** (no parameter reduction). Actual: ~125 minutes/run
(closer to the low end of the extrapolation).

## 10. Results (2026-08-23) — DP near-optimal, CONFIRMED, with real
## statistical power this time

**Gate 0c (operating-point search):** initial 8-point grid's best
candidate (`σ=5e-5`) landed at 9/20, one short of the `≥10/20` bar —
HALTed per §4, reported to John, who chose to widen the grid (§3). The
widened grid located `σ=4.5e-5` at 12/20 in-band (search precision,
`n_search_repeats=1,000`). The non-monotonic in-band pattern across the
grid was checked, not left as a guess: every block's own recovery
decreases perfectly monotonically with `σ_det` (verified directly, all
20 trajectories); the aggregate count's non-monotonicity is simply a
superposition of 20 individually-monotonic transition curves crossing
`[0.2,0.8]` at different `σ_det` values, most clustering near 4–5.5e-5
for this sample — an initial "discrete `N`-jump" guess was checked
against the data and found wrong (`N`'s distribution is nearly
identical across `σ=1.5e-5` through `5e-5`), corrected in §3 before the
main run rather than left on record.

**Gates 0a/0b:** not re-run, per §8 — E17 Part 3's CRN/equivalence
gates already cover this unmodified machinery.

**Gate 1 (smoke) → gate 2 (full run) → gate 3 (reproducibility):** full
run (20 blocks) took ~125 minutes; reproducibility rerun bit-identical,
sha256 `306be148d6d118b67d82d6b5cdea659b2002e8b2e9e158e3ada9ecee5654bc5b`.

**Gate 4 (aggregate): CONFIRMED.** 20/20 blocks are rank-1 or
CI-tied-for-rank-1 — decisively above the `≥18/20` bar, and **0/20**
blocks show `best_beats_dp_ci=True` (no evaluated alternative ever beat
DP outside noise, at any of up to 501 candidates per block). The three
blocks where DP wasn't literally rank 1 (blocks 0, 4, 8; ranks 3, 303,
356) are all at the noise floor (`dp_recovery_mc ≈ 0.0000–0.0005`,
`best_recovery_mc ≈ 0.0000–0.0015`) — a handful of successes out of
2,000 trials, not a meaningful ranking difference, and none
statistically beat DP.

**The power credit this contract was built to earn: 11/20 blocks
(55%) landed in the `[0.2,0.8]` target band** — up from E17 Part 3's
1/40 (2.5%). This is no longer a result carried by one exhaustively-
tested block; it is a genuinely well-powered screening result across
more than half the sample.

**Interpretation:** at a deliberately chosen, non-saturated operating
point, DP's schedule remained near-optimal — the same qualitative
finding as E17 Part 3, now on much stronger evidentiary footing.
Combined with E17 Part 3's result (also Confirmed, at the ceiling),
across two very different `σ_det` regimes and two very different levels
of statistical power, no evidence has yet been found that E16's
conservative calibration bias distorts DP's schedule *ranking* — the
conservatism looks like a magnitude effect, not a placement-ranking
effect, within everything tested so far (§1's scope caveat — one `λ`,
now two `σ_det` regimes — still applies to any further generalization).
**Real headroom was not found; the correlation-mechanism investigation
remains motivated by the magnitude gap alone, not by any demonstrated
placement-quality consequence, across both tests run to date.**

**Evidence artifacts:**
`results/sweeps/compiler_montecarlo_lesssaturated_sweep_frozen_v1_2026-08-23.json`,
sha256 `306be148d6d118b67d82d6b5cdea659b2002e8b2e9e158e3ada9ecee5654bc5b`;
`results/sweeps/compiler_montecarlo_lesssaturated_search_frozen_v1_2026-08-23.json`,
sha256 `756211493c37736f82dbe5f98cda4b6ae69f774e75e2eeb7295b5cb7e3a2abb5`.
Driver: `photonics/run_photonic_compiler_montecarlo_lesssaturated_sweep.py`.

