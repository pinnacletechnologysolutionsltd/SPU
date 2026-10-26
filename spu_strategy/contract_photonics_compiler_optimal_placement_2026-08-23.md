# Engineering Contract: Whole-Chain Optimal REGEN Placement (E17 Part 2)

**Date:** 2026-08-23
**Contract ID:** `contract_photonics_compiler_optimal_placement_2026-08-23.md`
**Status:** RAN TO COMPLETION 2026-08-23. **RESULT: DOMINATES E17's
greedy placement, decisively, at both σ_det points.** Best dominating
point: σ=1e-6, 21.9% fewer REGEN events at equal (perfect) reliability;
σ=1e-5, 36.4% fewer events *and* a reliability improvement outside
greedy's own 95% CI. Gate 0's cross-check caught and fixed a real bug
(`segment_m0` initially ignored `QSUB`'s lane-1 dependency) before any
prediction was trusted. See §9.

**Roles:**
- **Spec Author:** Claude, extending E17 per John's explicit choice
  (2026-08-23, "Extend E17 itself: whole-chain-product optimization") —
  the harder, strictly-more-general placement problem E17 §8 explicitly
  deferred: `minimize N_REGEN subject to P_chain ≥ P_target,chain`,
  rather than E17's per-event worst-case rule.
- **Halt-and-Flag Implementer:** review the DP formulation (§4) — in
  particular the segment-`m0` computation and the candidate-boundary
  restriction — before implementing.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_compiler_regen_placement_2026-08-23.md` (E17) —
  the greedy per-event rule and its frozen results (2.62 mean events at
  σ=1e-6 for 1.0 reliability; 0.9793 at σ=1e-5 with 6.67 mean events,
  beating every fixed-`M` policy). This contract's central question:
  **does whole-chain-optimal placement beat greedy's own numbers at the
  same noise levels?** `run_chain_boundary_noisy_diag` (E15) is reused
  again, unmodified — still no new scoring code.
- `contract_photonics_m0_dynamic_range_2026-08-22.md` §10 (E16) — the
  frozen law `a=-4.79, β=3.19`, reused as-is (not refit — same
  discipline as E17).

---

## 1. Objective

**Does an optimal (dynamic-programming) REGEN placement — chosen to
maximize predicted whole-chain recovery `P_chain = ∏ P_event(m0_i,σ)`
for a given REGEN-event budget, rather than enforcing a fixed per-event
floor — achieve a better efficiency/reliability trade-off than E17's
greedy rule, when actually executed (not just predicted)?**

Unlike greedy (which forces every individual event above a fixed
per-event target), the optimal formulation can trade safety unevenly
across events — spend less margin on already-safe windows, more on
risky ones — as long as the *product* clears the bar. This is a
genuinely different, strictly more general placement policy, not a
tuned version of greedy.

**Explicitly out of scope:** the correlation hypothesis flagged after
E17 (`P(R_{i+1}|R_i,m0_i,m0_{i+1}) ≠ P(R_{i+1}|m0_{i+1})`) — that is a
separate, not-yet-authorized line (a different kind of question: *why*
the model is conservative, not *how far* a better placement policy can
push efficiency). This contract still uses the plain product model as
the optimization objective, deliberately, to isolate "is greedy leaving
efficiency on the table within the model's own terms" from "is the
model itself missing physics." σ=1e-4 is **not retested** — E17 already
established it as universally degenerate (no policy recovers there);
retesting it here would not be informative and wastes the compute
budget.

## 2. Objective grounding — the DP formulation, precisely

For a fixed block (16 ops) and `σ_det`, candidate REGEN boundaries are
restricted to positions `{0, 2, 3, 4, ..., 16}` — **never between the
two initial QLDIs** (position 1), matching the implicit convention of
every prior contract in this chain (E13–E17), where the first group
always contains both QLDIs. Splitting them was never tested and is not
introduced here without separate justification.

The exact oracle trajectory `qr[lane]` at every position `0..16` is
**independent of REGEN placement** (it is pure algebra — `exact_qsub`/
`exact_rotc` replayed once through the whole block, unaffected by where
REGEN happens). This is computed once per block (`precompute_qr_traj`).
For any candidate segment `(i, j)` (REGEN — or the start — at `i`, next
REGEN at `j`), the resulting `m0` at `j` is deterministic given `qr` at
`i`: `_load_exp(qr[0] at i)`, then `+1` for every combine op in `(i,j]`
(every combine op's destination is lane 0, a `gen_block` invariant) —
or, for the one segment starting at `i=0`, the first op (QLDI on lane 0)
*sets* `m0` directly rather than incrementing (`_load_exp` of the loaded
value), exactly mirroring production re-entry semantics.

This gives `logp(i,j) = log(P_event_fit(m0_at_j_given_start_i, σ_det))`
for every one of the `O(16²)=136` candidate segments — cheap to compute
per trial. The placement problem is then a shortest-path/DP over
positions `0..16`: for a REGEN-cost parameter `λ`,

```
score[0] = 0
score[j] = max over valid i<j of (score[i] + logp(i,j) - λ)
```

with backpointers recovering the optimal boundary sequence. Sweeping
`λ` traces out a **Pareto frontier** of (mean REGEN events, predicted
`P_chain`) — `λ→0` favors more REGEN events wherever they help even
marginally; large `λ` favors fewer, coarser groups.

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| σ_det test points | `[1e-6, 1e-5]` — E17's two informative points;
  σ=1e-4 not retested (§1) |
| λ sweep | `[0, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]` —
  spans from "REGEN wherever it helps at all" toward "REGEN as rarely as
  possible"; confirm via smoke pass (§7 gate 1) that this range actually
  produces a spread of mean-event-counts bracketing greedy's own 2.62 /
  6.67, not assumed correct from this back-of-envelope choice alone |
| candidate boundary positions | `{0, 2, 3, ..., 16}` (§2) |
| E16 law constants (frozen, not refit) | `a = -4.79`, `β = 3.19` |
| trials per (σ_det, λ) cell | 10,000 — smaller than E17's 30,000
  because this contract needs a **frontier** (9 λ values × 2 σ points =
  18 cells) rather than 3 single points; 10,000/cell still gives
  CI half-widths under 1% at the recovery rates observed in E17 |
| noise axes | `sigma_phi = sigma_amp = 0` (unchanged) |

## 4. New code (additive) — Halt-and-Flag review required before running

`photonics/run_photonic_compiler_optimal_placement_sweep.py`:

- `precompute_qr_traj(block)` — one exact pass, `qr[lane]` at every
  position `0..16`, independent of placement.
- `segment_m0(block, qr_traj, i, j)` — the §2 formula, a direct replay
  of ops `(i,j]` tracking only `m[0]`'s evolution from the `_load_exp`
  reset at `i`.
- `optimal_placement(block, qr_traj, sigma_det, lam)` — the DP (§2),
  returns `(boundaries, m0_trace, predicted_p_chain)` — note
  `predicted_p_chain` uses the **pure** accumulated `logp` sum, not the
  λ-penalized `score` (λ only steers *which* path is chosen, it is not
  part of the reported prediction).
- `cell(sigma_det, lam, n_trials)` — same per-trial-record convention as
  E17's `cell()`: score the **actual noisy** recovery via **E15's
  unmodified** `run_chain_boundary_noisy_diag`, record `(predicted,
  observed_ok, n_regen)` per trial.

**Halt-and-Flag pre-review items:**
- **DP noiseless correctness** — verify, for 500+ trials, several λ
  values, that the DP's chosen boundaries, replayed through
  `run_chain_boundary_noisy_diag` at `sigma_det=0`, reproduce the exact
  oracle at every boundary (same discipline as E15/E16/E17's own gate
  0s) — a new algorithm, needs its own gate, not inferred from E17's.
- **`segment_m0` cross-check against `greedy_place`:** for the *specific*
  boundaries greedy placement chose (E17, frozen), confirm
  `segment_m0(block, qr_traj, i, j)` reproduces the same `m0` values
  E17's `greedy_place` computed at those same boundaries, for a sample
  of trials — this validates the new segment-based computation against
  the already-verified sequential one, on a case where both must agree.
- **DP correctness (shortest-path optimality):** for a small number of
  trials, brute-force-verify the DP's chosen path is truly optimal for
  its `λ` (enumerate all valid boundary sequences for a short synthetic
  block, or spot-check that no single-boundary perturbation of the DP's
  chosen path improves `score`) — a DP bug that silently returns a
  suboptimal-but-valid path would not be caught by the noiseless-oracle
  gate alone, since any valid placement passes that gate.

**Gate 0 result (2026-08-23): the cross-check caught a real bug before
any prediction was trusted.** The first `segment_m0` implementation
assumed every combine op increments `m[0]` by a flat `+1` from its own
previous value — true for `ROTC` (`src=dst=0` always, a `gen_block`
invariant) but **wrong for `QSUB`**, whose production semantics are
`m[0] = max(m[sa], m[sb]) + 1` (`_apply_op_field`,
`test_regen_equivalence.py`), and `sa`/`sb` can draw from lane 1, whose
exponent can exceed lane 0's. This produced 734–1330 mismatches per
600-trial sample against E17's already-verified `greedy_place` on
identical boundary sets — caught precisely because the contract required
that specific cross-check rather than relying on the noiseless-oracle
gate alone (which cannot catch this: any valid boundary set recovers
exactly in the noiseless case regardless of whether the *predicted* m0
was computed correctly). Fixed by tracking `m[1]` alongside `m[0]`
within `segment_m0` (constant across a segment for `i≥2`, since lane 1
is never a combine-op destination; evolving only for the `i=0` segment,
which includes the QLDI that sets it). Rerun on the same 5λ × 2σ ×
600-trial grid: 0 shape issues, 0 oracle mismatches, **0 cross-check
mismatches** (was 734–1330 per 600-trial line), 0/76 optimality
mismatches.

## 5. Metrics & outputs

- **Primary — the frontier comparison:** for each σ_det, plot (mean
  `n_regen`, observed whole-trial recovery) across all `λ` values,
  forming the DP's empirical Pareto frontier. Overlay E17's frozen
  greedy point (2.62, 1.0000) at σ=1e-6 and (6.67, 0.9793) at σ=1e-5.
  **The test:** does the DP frontier reach a point with `n_regen ≤`
  greedy's own count and observed recovery `≥` greedy's own recovery
  (a dominating point — strictly better on both axes, or equal on one
  and better on the other)?
- **Secondary — calibration, same convention as E17 §6:** report whether
  the DP's own predictions are conservative in the same direction E17
  found (informative either way — if the bias direction matches, that's
  further evidence for the standing correlation hypothesis, tested
  without assuming it).
- Output: canonical JSON
  (`results/sweeps/compiler_optimal_placement_sweep.json`), per-trial
  records, frozen copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

- **DP noiseless correctness and optimality checks (§4) must pass**
  before trusting any frontier point.
- **Dominates greedy:** at either σ_det, the DP frontier contains a
  point with `mean_n_regen ≤ 0.95 × greedy's mean_n_regen` AND observed
  recovery `≥` greedy's observed recovery minus its own 95% CI half-width
  (i.e., not worse within noise) — a genuine, non-trivial efficiency
  gain beyond greedy, confirming GTP's optimization framing adds real
  value beyond the simpler rule.
- **Matches greedy, no dominance:** the frontier's best achievable point
  at greedy's own `n_regen` is statistically indistinguishable from
  greedy's own observed recovery (CIs overlap) — the simpler per-event
  rule was already close to optimal; the harder optimization buys
  little in practice for this op family, a genuinely useful negative
  result (says greedy is a good-enough heuristic, don't over-engineer
  the compiler pass).
- **Underperforms greedy:** no frontier point reaches greedy's
  (n_regen, recovery) pair — would indicate a bug in the DP or its
  scoring, since the optimal-by-construction placement should never do
  *worse* than a valid heuristic under the same predictive model; treat
  as a HALT condition requiring investigation, not a reportable
  scientific finding.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0. DP noiseless correctness + segment_m0 cross-check against
#    greedy_place + DP optimality spot-check (SS4).

# 1. Smoke pass -- confirm the lambda sweep produces a real spread of
#    mean-n_regen values bracketing greedy's 2.62/6.67, at both sigma
#    points; adjust the lambda grid if not (report the adjustment,
#    don't silently widen it after seeing the full run).
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=300 .venv/bin/python3 photonics/run_photonic_compiler_optimal_placement_sweep.py

# 2. Full run (2 sigma points x 9 lambda values x 10,000 trials)
.venv/bin/python3 photonics/run_photonic_compiler_optimal_placement_sweep.py

# 3. Reproducibility: two full runs, bit-identical.

# 4. Frontier analysis (SS5/SS6) -- dominates / matches / underperforms.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No σ=1e-4 retest** (§1) — already established as universally
  degenerate; not informative here.
- **No refitting E16's law** — same discipline as E17.
- **No correlation-hypothesis investigation** (§1) — separate, later,
  not-yet-authorized contract.
- **No new op-sequence family or K value.**
- **No hardware implications drawn from this contract** — this remains
  entirely within the "compiler pass over the existing ISA" scope E17
  established; nothing here touches the adaptive-hardware question
  (design rule doc §4).

## 9. Results (2026-08-23)

**All gates passed:** gate 0 (500+ trials × 5 λ × 2 σ, 0 shape issues,
0 oracle mismatches; the required cross-check caught a real bug in the
first `segment_m0` implementation before anything was trusted — §4's
addendum has the full story; 76-configuration brute-force optimality
spot-check, 0 mismatches); gate 1 (smoke, 300 trials/cell — dominance
already visible at smoke scale, λ grid not adjusted); gate 2 (full run,
18 cells × 10,000 trials); gate 3 (reproducibility, two runs,
bit-identical, sha256
`6911fd3f0f9f51e9a36b1000800ade8bfe91a3664caf6530ecbcccdfbd25c3df`).

**Gate 4/6 (frontier comparison against E17's frozen greedy point):
DOMINATES, decisively, at both σ_det points.**

| σ_det | greedy (n, recovery) | best DP point (n, recovery) | events saved | reliability change |
|---|---|---|---|---|
| 1e-6 | (2.62, 1.0000) | λ=0.01: (2.047, 1.0000) | **−21.9%** | equal (both perfect) |
| 1e-5 | (6.67, 0.9793) | λ=0.01/0.03: (4.240, 0.9853) | **−36.4%** | **+0.0060, outside greedy's own CI** |

At σ=1e-6, **5 of 9** λ values dominate greedy outright (fewer events,
equal-or-better reliability); the least dominant end of that range
(λ=0.03/0.1) trades a small reliability loss (0.9974–0.9983 vs. 1.0)
for even fewer events (1.84–1.88), a genuinely different point on the
frontier, not a failure. At σ=1e-5, **8 of 9** λ values dominate; only
the most aggressive setting (λ=0.1, 3.31 events) drops reliability
(0.9352) below greedy's 0.9793 — the frontier's other extreme, trading
reliability for an even larger efficiency gain than the dominant region
offers.

At σ=1e-5's best dominating point, DP's 95% CI (`[0.9829, 0.9877]`)
does not contain greedy's own point estimate (0.9793) — the reliability
improvement is not just numerically larger, it is statistically
distinguishable from greedy's frozen result, not only more efficient.

**Interpretation:** the whole-chain-product optimization is not merely
a theoretical refinement of greedy — it recovers a substantial,
measurable efficiency gain (22–36% fewer REGEN events) *and*, at the
noisier of the two test points, a real reliability gain too, by
trading margin unevenly across events rather than enforcing a uniform
per-event floor. This confirms GTP's framing precisely: greedy was a
good, simple heuristic (E17 already beat every fixed-`M` policy with
it), but it was leaving real efficiency on the table relative to the
model's own optimum — exactly the kind of headroom a genuine
optimization formulation should be expected to find, and did.

**What this does not resolve:** the DP's own predictions remain
conservative in the same direction E17's greedy predictions were
(compare `mean_predicted` to `mean_observed` in the gate 2 log —
e.g. σ=1e-5, λ=0.01: predicted 0.9730 vs. observed 0.9853) — the
standing correlation hypothesis (§1) is neither confirmed nor
falsified by this contract, which deliberately used the same
(uncorrected) product model as its optimization objective. That
remains open, separate, not-yet-authorized work.

**Evidence artifact:**
`results/sweeps/compiler_optimal_placement_sweep_frozen_v1_2026-08-23.json`,
sha256 `6911fd3f0f9f51e9a36b1000800ade8bfe91a3664caf6530ecbcccdfbd25c3df`.
Driver: `photonics/run_photonic_compiler_optimal_placement_sweep.py`.

