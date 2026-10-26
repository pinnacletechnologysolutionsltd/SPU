# Engineering Contract: First-Boundary Placement Investigation (E15)

**Date:** 2026-08-22
**Contract ID:** `contract_photonics_regen_boundary_placement_2026-08-22.md`
**Status:** FROZEN SPEC (design locked 2026-08-22, four amendments applied
per Halt-and-Flag review: (1) the E13-scaling extrapolation number
renamed and demoted from pass/fail threshold to reference point, since
E14 itself showed that acceleration factor doesn't generalize; (2) the
equivalence gate strengthened to per-trial comparison, not aggregate
`P_recover`; (3) "statistically indistinguishable" defined precisely via
bracket overlap / grid-interval movement, pre-registered before running;
(4) an explicit first-boundary state-equivalence diagnostic added, since
the whole hypothesis hinges on what that specific REGEN recovers.
Ran to completion 2026-08-22. **RESULT: RULED OUT** under the
pre-registered bracket-overlap criterion (99.9%/99%/95% brackets all
overlap or are identical to pure M2's frozen brackets), with a small,
quantified, statistically real residual effect (~+0.011 decades / ~2.7%
noise-tolerance shift, peak 7.8σ at level=3e-5) too small to explain
M=2's diminishing return. See §9.)

**Roles:**
- **Spec Author:** Claude, from E14's surviving candidate and John/GTP's
  explicit framing after E14's review: "Does the anomalous M=2 behavior
  arise specifically because REGEN occurs before the first combine
  operation?" — with the explicit caution that the control "needs careful
  design because simply shifting every boundary changes the number of
  operations in subsequent groups... this deserves its own contract
  rather than an ad hoc code modification."
- **Halt-and-Flag Implementer:** pre-review of the boundary-shift
  generalization (§4) — this changes `run_chain_periodic_noisy`'s
  interface (arbitrary boundary positions, not a uniform period M), a
  larger generalization than E13/E14's fixed-M grouping.
- **Integration Auditor:** reproducibility gates, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_regen_placement_m2_2026-08-22.md` (E14) — the
  surviving candidate this contract tests directly: M=2's first REGEN
  boundary occurs immediately after the two QLDIs, before any QSUB/ROTC
  computation — the one structural feature distinguishing M=2 from
  M=4/8/16 (all of which have combine ops before their first boundary).
  E14 ruled out the alternative candidate (lane-1 exposure) by direct
  measurement (100% of ~3,769 failures attributable to lane 0 only).
- `contract_photonics_regen_placement_2026-08-22.md` (E13) — the frozen
  M=16/8/4 curve, reused for reference values only, not rerun.

---

## 1. Objective

**Does deferring M=2's first REGEN boundary past exactly one combine
operation — while holding the total number of REGEN events and the
overall ~every-2-ops cadence as close to unchanged as possible — restore
some or all of the improvement M=2 failed to deliver in E14?**

This is explicitly **not** "M=2 vs M=4 again" (per John's correction) —
it is a test of one specific structural feature of M=2's grouping, with
everything else held as close to constant as the discrete op sequence
allows.

**Explicitly out of scope:** re-testing lane-1 exposure (already ruled
out, E14 §9.4); testing offsets other than +1 (a single, minimal
perturbation — a swept range of offsets is a natural E16 if this result
warrants it, not bundled here); any claim beyond what the shifted-M=2
curve shows relative to pure M=2 (E14, frozen) and M=4 (E13, frozen).

## 2. Objective grounding — the control design, worked out precisely

`gen_block(rng,16)` produces 2 QLDI + 14 combine ops = 16 ops. Pure M=2
(E14) groups at cumulative op-position multiples of 2: boundaries after
positions **[2, 4, 6, 8, 10, 12, 14, 16]** — 8 groups, group 1 = the two
QLDIs only (zero combines before the first REGEN).

**The minimal single-variable perturbation:** shift every boundary
position by exactly **+1**, except the fixed final endpoint (16, fixed
by the block's total length) — giving boundaries after positions
**[3, 5, 7, 9, 11, 13, 15, 16]**. This has two effects, and only two:

1. **Group 1 becomes 3 ops** (2 QLDI + 1 combine) — the first REGEN now
   happens *after* one combine op, directly testing the hypothesis.
2. **Group 8 becomes 1 op** (down from 2) — the shift has to be absorbed
   somewhere, and absorbing it entirely at the tail (rather than
   redistributing it across every group) keeps every *other* group at
   exactly the same size as pure M=2 (2 ops), so the cadence is
   unchanged everywhere except the two boundary groups that necessarily
   had to change.

**Total REGEN-event count stays at 8** (identical to pure M=2) — this
design does not confound "boundary placement" with "regeneration
frequency," which was the exact risk flagged in the review. The only
groups that differ in size from pure M=2 are group 1 (3 vs 2 ops) and
group 8 (1 vs 2 ops) — a symmetric, minimal trade-off, not a redesign of
the whole cadence.

## 3. Locked parameters

| condition | boundaries | source |
|---|---|---|
| M=2 (pure) | [2,4,6,8,10,12,14,16] | **E14's frozen result, reused, NOT rerun** |
| M=2-shifted | [3,5,7,9,11,13,15,16] | **new — this contract's only measured condition** |
| M=4 (reference only) | [4,8,12,16] | **E13's frozen result, reused, NOT rerun** |

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (E9/E13/E14's, unmodified) |
| M_K | 2000 |
| band | [1000, 30000] |
| seed | 13 |
| det levels | not fixed in advance — smoke pass required, wide range (E14's
  pure-M=2 crossing ~3.46e-6 as the floor reference; the E13-scaling
  extrapolation reference, below, as one ceiling data point — not a
  pass/fail threshold, §6) |
| trials per cell | 30,000 |

**The E13-scaling extrapolation reference (computed, not assumed —
renamed from "full-restoration target" per Halt-and-Flag review: E14
itself showed the E13 acceleration factor does NOT generalize — its own
successive factors were 10×, 31.62×, then only 2× — so re-applying
31.62× here would be assuming the exact law E14 falsified):** if
M=2-shifted recovered the same 31.62× E13 saw going M=8→M=4, applied to
M=4's own crossing, that predicts a crossing near
`1.732e-6 × 31.62 ≈ 5.48e-5` — strikingly close to native K=8's own
crossing (5.92e-5). **This is one reference point among several in §6's
outcome hierarchy, not the confirmation criterion** — landing near it
would be a particularly strong (not the only) form of confirmation.

## 4. New code (additive) — Halt-and-Flag review required before running

**Generalize `run_chain_periodic_noisy` from a uniform period `M` to an
explicit list of boundary positions.** `run_chain_boundary_noisy(pb,
block, boundaries, sigma_det, rng)` — identical logic to E13/E14's
function (whole-state REGEN, canonical re-entry, `_apply_op_field`/
`_noise_per_op` reused verbatim), except the REGEN trigger changes from
`if i % M == 0` to `if i in boundary_set` (boundaries precomputed as a
set for O(1) membership). Pure M=2 and M=2-shifted are then just two
different boundary lists passed to the *same* function — the
generalization is a strict superset of E13/E14's behavior, not a
divergent implementation.

**Equivalence gate — strengthened per Halt-and-Flag review (per-trial,
not aggregate):** "reproduces E14's frozen result" is not satisfied by
matching `P_recover` alone — that could hide compensating errors. For
identical seed, block, detector-noise draws, and σ, the generalized
function called with `boundaries = [2,4,6,8,10,12,14,16]` must reproduce,
**per trial**: the same generated block, the same rejection decision, the
same per-group success/failure at every one of the 8 boundaries, the same
final success bit, and the same noise draws consumed (i.e., the RNG
stream advances identically). This makes the generalized function a
demonstrably strict refactoring of E14's scorer, not merely an
implementation that happens to land on the same probability. Verify on a
sample (e.g. 500 trials, full per-trial diagnostic comparison, not just
the final aggregate) before trusting the shifted variant for anything.

**Halt-and-Flag pre-review items:**
- **Noiseless correctness for the shifted boundaries specifically** — the
  E11/E12/E13/E14 lesson, again: verify 500+ trials at σ=0, both boundary
  sets, against the independent oracle, before anything noisy.
- **Rejection-population invariant** — unaffected by boundary placement
  (band-rejection is on the final exact oracle state only), but verify,
  don't assume, matching every prior contract's discipline.
- **Group-8 asymmetry:** the shifted variant's last group has only 1 op
  (vs pure M=2's 2). A 1-op "group" still goes through a full whole-state
  REGEN (QLDI/QSUB/ROTC-agnostic — REGEN doesn't care how many ops
  preceded it). Confirm this doesn't hit an edge case in the canonical
  re-entry logic (e.g. `_load_exp` on a freshly-produced single-op state)
  — check explicitly, don't assume it's fine by analogy to group 1's
  pure-M=2 case (which is also short, but at the *front*, not the tail,
  and was already verified working in E14).
- **First-boundary state-equivalence diagnostic (added per Halt-and-Flag
  review):** because the entire hypothesis is about what the first REGEN
  recovers, explicitly capture, for a representative noiseless trial: pure
  M=2's first REGEN recovers the oracle state after `[QLDI, QLDI]`;
  M=2-shifted's first REGEN must recover the oracle state after
  `[QLDI, QLDI, <first combine op>]` — i.e., confirm the shifted variant's
  first-boundary comparison is against the state *including* that combine
  op's effect, not accidentally checked against the same 2-op oracle slice
  pure M=2 uses. The global 500+-trial noiseless gate would eventually
  catch a bug here (as a downstream failure), but this targeted diagnostic
  makes such a failure immediately interpretable rather than a mystery
  buried in an aggregate pass rate.

## 5. Metrics & outputs

- P_recover(σ_det) for M=2-shifted, the full curve — reported alongside
  E14's frozen pure-M=2 curve and E13's frozen M=4 curve for direct
  comparison (three curves on one chart/table, not just crossings).
- Crossing bracket (99.9%, 99%, 95%) for M=2-shifted.
- **The comparison (the primary result):** M=2-shifted's crossing vs
  pure M=2's 3.464e-6 (E14) and native K=8's own crossing (5.92e-5) — per
  §6's outcome hierarchy, not a single pass/fail number. Report the
  fraction of the pure-M2-to-K8 gap closed, and separately note where the
  result falls relative to the §3 E13-scaling extrapolation reference
  (~5.48e-5) as additional context, not the primary criterion.
- **Sanity check (secondary, not primary):** spot-check that failures
  under M=2-shifted are still lane-0-only (a handful of cells, not a full
  §4b-style instrumentation pass — E14 already established this
  pattern; this just confirms the shift didn't introduce a new lane-1
  pathway, it doesn't re-litigate E14's finding).
- Output: canonical JSON (`results/sweeps/regen_boundary_placement_sweep.json`),
  frozen copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

- **Equivalence check (§4) must pass** — per-trial, not just aggregate
  `P_recover` — before trusting anything about the shifted variant.
- **Noiseless and rejection gates must pass** for the shifted boundaries.
- **First-boundary state diagnostic (§4) must pass.**

**"Statistically indistinguishable from pure M=2" — defined precisely
(Halt-and-Flag review, do not decide this after seeing the curve):**
compare M=2-shifted's crossing bracket against E14's frozen pure-M=2
bracket ([3.0e-6, 4.0e-6] at 99.9%). If the shifted bracket **overlaps**
the frozen bracket (shares a grid point, or the shifted crossing falls
within it), that is "no detectable shift" — ruled out. If the shifted
crossing moves by **at least one full locked-grid interval** beyond the
frozen bracket, that is a measurable improvement — report it, don't wave
it away as noise. Where the underlying per-cell CIs permit it (n=30,000
throughout, so they should), also report `log10(R_shift / R_M2,pure)`
with its own uncertainty, rather than a bare bracket-overlap call alone.

**Outcome hierarchy (John's explicit restructuring, 2026-08-22 — an
extrapolated reference number is not the pass/fail line):**
- **Ruled out:** shifted ≈ pure M=2 (bracket overlap, above). The
  diminishing return at M=2 is **not** explained by either of E14's two
  pre-registered candidates (lane-1, now boundary placement) — a
  genuinely new hypothesis is needed, not constructed inside this
  contract.
- **Contributes:** shifted is measurably higher than pure M=2 (moved by
  ≥1 grid interval) but well short of native K=8's own crossing
  (5.92e-5) — boundary placement is *a* contributor, quantify the
  fraction of the pure-M2-to-K8 gap closed, same discipline as
  E13/E14's gap accounting.
- **Explains most/all of the remaining gap:** shifted approaches native
  K=8's crossing — boundary placement accounts for most or all of the
  17.1× gap E14 left open.
- **Particularly strong confirmation of this specific mechanism:**
  shifted lands near the §3 E13-scaling extrapolation reference
  (~5.48e-5) specifically — informative about the *shape* of the
  recovered curve (matching E13's own acceleration factor exactly would
  be a notable, not merely sufficient, additional signal), not a
  requirement for confirming the hypothesis in general.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0. Equivalence check (SS4, strengthened): run_chain_boundary_noisy with
#    M=2's boundary list reproduces E14's frozen pure-M=2 scorer PER-TRIAL
#    (block, rejection, every group's pass/fail, final bit, noise draws
#    consumed) -- not just matching aggregate P_recover. Sample comparison
#    (e.g. 500 trials with full diagnostics), not a full 30,000-trial
#    re-verification -- E14's result is already frozen and trusted.

# 0b. First-boundary state-equivalence diagnostic (SS4): confirm the
#     shifted variant's first REGEN is checked against the oracle state
#     AFTER the first combine op, not the pure-M=2 2-op slice.

# 1. Noiseless + rejection gates for the SHIFTED boundary list specifically.

# 2. Smoke pass -- locate M2-shifted's crossing region (floor: pure M=2's
#    3.46e-6; ceiling: native K=8's 5.92e-5, with the ~5.48e-5 E13-scaling
#    reference as an intermediate data point; give margin on both sides,
#    same discipline as every prior contract's grid-floor lessons).
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_regen_boundary_placement_sweep.py

# 3. Full run (only after step 2 confirms grid coverage)
.venv/bin/python3 photonics/run_photonic_regen_boundary_placement_sweep.py

# 4. Reproducibility: two full runs, bit-identical -- checked empirically
#    first, not assumed.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No sweep of offset values** (+2, +3, ...) — +1 is the minimal,
  cleanest test; a range is a separate, later, explicitly-authorized
  contract if this result warrants it.
- **No rerunning pure M=2 or M=4** — both reused frozen from E14/E13.
- **No full §4b-style lane-attribution instrumentation** — E14 already
  established the pattern conclusively; this contract only spot-checks
  that the shift doesn't introduce a new lane-1 pathway (§5), it doesn't
  re-run the full analysis.
- **No new hypothesis construction if this is ruled out** — a third
  candidate cause is a separate, later, explicitly-authorized contract.
- **No M=1, no E10 (combined-axis)** — unchanged from E13/E14's scope.

## 9. Results (2026-08-22) — RULED OUT under the pre-registered criterion,
## with a small, real, quantified residual effect

**All gates passed, in order:**
- Gate 0 (per-trial equivalence): 500 trials, level=5e-6, 0 mismatches —
  block, rejection decision, every group's pass/fail, final success bit,
  and RNG-stream state all matched E14's frozen `run_chain_periodic_noisy_diag`
  (M=2) exactly. `run_chain_boundary_noisy` is a confirmed strict
  refactoring, not a divergent implementation.
- Gate 0b (first-boundary state diagnostic): direct truncated-block test
  confirmed pure M=2's first REGEN reads the 2-op oracle prefix and
  M=2-shifted's reads the 3-op oracle prefix — using a representative
  trial where the first combine op is a genuine state change (angle≠0;
  the naive first accepted trial's first op happened to be a ROTC at
  angle 0, the identity rotation, which would have made this diagnostic
  vacuous — caught and avoided).
- Gate 1 (noiseless + rejection): 600 accepted trials, 0 failures against
  the full independent oracle for either boundary set.
- Gate 2 (smoke, 200 trials/cell): located the transition between ~5e-6
  and ~3e-5. 16-point grid locked: `[1e-6, 2e-6, 3e-6, 5e-6, 7e-6, 1e-5,
  1.5e-5, 2e-5, 2.5e-5, 3e-5, 4e-5, 5e-5, 7e-5, 1e-4, 2e-4, 3e-4]`.
- Gate 3 (full run, n=30,000/cell): completed.
- Gate 4 (reproducibility): two independent full runs, sha256
  `30e9802103a6665a057262545e9f294b5d036e333d7a20f09eb3ea8b3c4cc08b`,
  bit-identical.
- Gate 5 (`verify_repo.sh`): PASS (see repo regression log).

**Primary result — bracket-overlap test (pre-registered, §6), taken
literally:**

| percentile | pure M=2 bracket (frozen) | M=2-shifted bracket | verdict |
|---|---|---|---|
| 99.9% | [3.0e-6, 4.0e-6] | [3.0e-6, 5.0e-6] | **overlaps** (shares 3.0e-6) |
| 99% | [5.0e-6, 7.0e-6] | [5.0e-6, 7.0e-6] | **identical** |
| 95% | [7.0e-6, 1.0e-5] | [7.0e-6, 1.0e-5] | **identical** |

No crossing bracket moved by a full locked-grid interval at any of the
three pre-registered percentiles. **By the literal pre-registered
criterion, this is RULED OUT**: deferring the first REGEN boundary past
one combine op does not restore M=2's crossing threshold toward M=4's
(let alone K=8's).

**But the curve itself is not statistically indistinguishable from pure
M=2 — a small, real, reproducible effect is present**, and per §6's
instruction to report a quantified ratio rather than a bare overlap call:
at every grid point the two grids share between 3e-6 and 5e-5 (9 points),
M2-shifted's recovery is higher than pure M2's, monotonically, with the
separation reaching statistical significance (combined-CI sigma) at:

| level | pure M=2 | shifted | Δ | σ separation |
|---|---|---|---|---|
| 1e-5 | 0.8941 | 0.9032 | +0.0091 | 1.9 |
| 1.5e-5 | 0.7169 | 0.7318 | +0.0150 | 2.1 |
| 2e-5 | 0.5046 | 0.5309 | +0.0263 | **3.3** |
| 3e-5 | 0.1215 | 0.1651 | +0.0436 | **7.8** (peak) |
| 5e-5 | 0.0076 | 0.0148 | +0.0072 | **4.3** |

Quantified as a noise-axis shift (§6's `log10(R_shift/R_M2,pure)`,
computed at the 50%-recovery crossing via log-linear interpolation, the
point best-resolved by both grids): pure M2's 50% crossing ≈2.010e-5,
shifted's ≈2.064e-5 → **log10(R) ≈ +0.011 decades (~2.7% rightward
shift)**. This is roughly three orders of magnitude smaller than E13's
regeneration-frequency effect (1.0–1.5 decades per halving) and is why it
does not register as a bracket-level shift even though it is not zero.

**Interpretation:** QLDI-only-first-boundary placement is **not the (or
not a substantial) cause** of M=2's diminishing return relative to M=4 —
this specific, cleanly isolated structural feature accounts for at most a
few-percent effect, not the ~17.1× gap E14 left open. The direction of
the small residual is consistent with the hypothesis (deferring the first
REGEN past a combine op does help, marginally) but its magnitude rules it
out as a primary explanation. Per §8, no new hypothesis is constructed
here — a third candidate cause is a separate, later, explicitly-authorized
contract (see updated session handover / photonics memory for the current
open-question list).

**Secondary sanity check (§5):** spot-checked lane attribution at three
cells (levels 2e-5, 3e-5, 5e-5; n=3,000 each) under M2-shifted — failures
remain overwhelmingly lane-0-only (6,924/6,931 = 99.9%; 7 "both" failures
at the highest level, 5e-5, none lane-1-only) — the shift did not
introduce a new lane-1 pathway; consistent with E14's established
pattern, not a re-litigation of it.

**Evidence artifact:**
`results/sweeps/regen_boundary_placement_sweep_frozen_v1_2026-08-22.json`,
sha256 `30e9802103a6665a057262545e9f294b5d036e333d7a20f09eb3ea8b3c4cc08b`.
Driver: `photonics/run_photonic_regen_boundary_placement_sweep.py`.
