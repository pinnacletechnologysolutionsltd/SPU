# Engineering Contract: Corruption Support / Spread (E21)

**Date:** 2026-08-24
**Contract ID:** `contract_photonics_corruption_support_2026-08-24.md`
**Status:** AMENDED (round 1) 2026-08-24 — 5 amendments incorporated per
Halt-and-Flag review; re-review requested before freeze.

**Amendments incorporated (Halt-and-Flag round 1, 2026-08-24):**
1. Gate 5 renamed from "mediation" to **support-conditioned attenuation**
   throughout (§1, §5, §6, §8) — the contract does not establish
   `op_i → S_i → R_{i+1}` as a causal chain, only that `S_i` is a state
   descriptor present at the boundary that `op_i` acts on.
2. The pooled conditional eta² estimator is locked precisely (§3, §5):
   **SS_between and SS_total are summed across retained strata, then
   divided once** — not an n-weighted average of per-stratum eta²
   values (a different, non-equivalent estimator).
3. Explicit statement that Gate 0 and Gate 5 are **descriptive
   conditional analyses of E20's already-frozen 7 cells, not new
   significance tests** — the `4/7` majority bars are attenuation
   classifications, not p-value-based claims (§5, §6).
4. §6 outcome 4 fixed to refer to **`m0_i`** (what Gate 0 conditions on)
   rather than `m0_{i+1}` (E18's cell-defining variable) — these are
   different quantities and the original wording conflated them.
   **Gate 0 given explicit interpretive precedence** over outcomes 1–3:
   if Gate 0's confound bar is met, outcomes 1–3 become secondary/
   descriptive, not primary mechanistic conclusions (§6).
5. Replay fidelity (§7) strengthened beyond aggregate per-cell counts:
   also compares the **ordered `op_i` and `R_{i+1}` event sequence**
   per cell against E20's frozen `raw_events`, catching an ordering/
   indexing bug that a matching aggregate count alone would miss.

**Roles:**
- **Spec Author:** Claude, formalizing John/GTP's E21 scoping (2026-08-24,
  after E20): the corruption-*spread* hypothesis, a `m0_i` confound
  check to run first, and a mediation/attenuation framing rather than
  another flat stratification sweep.
- **Halt-and-Flag Implementer:** review the concrete numeric thresholds
  this contract commits to (§3, §5, §6), the Gate-0 replay-cost
  clarification (§2), and the ΔS_i exclusion (§8) before freeze.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_discrete_corruption_descriptor_2026-08-24.md` (E20)
  — the 24-cell family, `op_i` categories (`QSUB`/`ROTC_thirds`/
  `ROTC_plain`), the omnibus-chi2 + eta² toolkit, and the frozen result
  this contract interrogates: `op_i` clears Bonferroni-corrected omnibus
  significance in **7/24 cells** (all at `pair_id∈{1..5}`, `bin=9`, plus
  one at `pair_id=1,bin=8/10`), eta² 0.018–0.041 (small, not large),
  with a consistent `ROTC_plain > QSUB > ROTC_thirds` ordering at 5/6
  `bin=9` cells.
- `contract_photonics_corrupted_state_sufficiency_2026-08-23.md` (E19)
  — ruled out error *magnitude* (`err_i`); this contract asks about
  corruption *support* (how many components deviate), a different axis
  `err_i` says nothing about (a trial can have `err_i=1` at any support
  size 1–4, or `err_i>1` at support size 1).
- `contract_photonics_correlation_mechanism_2026-08-23.md` (E18) — the
  binning-hierarchy discipline (exact integer → width-2 → width-4 →
  exclude, decided by sample count only, before any outcome is
  examined) this contract reuses for `m0_i` binning (§5 Gate 0).

---

## 1. Objective

**Two related but distinct questions, run from one combined replay:**

1. **Does corruption *support* `S_i = #{k∈{0,1,2,3}: rec_i[k]≠qr_i[k]}`
   (how many of the 4 lane-0 components deviate, not which one or by
   how much) stratify `P(R_{i+1})` beyond `m0_{i+1}` alone, across the
   same 24 cells E18–E20 established?** A new hypothesis in its own
   right — tested against all 24 cells, its own Bonferroni family, same
   discipline as `j`/`sign`/`op_i` in E20.
2. **Support-conditioned attenuation (Amendment 1 — not "mediation" in
   the formal statistical sense, since `op_i → S_i → R_{i+1}` is not
   established as a causal chain): within the 7 cells where E20 found
   `op_i` significant, how much of that association survives
   conditioning on `S_i`?** If `op_i`'s association substantially
   collapses once `S_i` is held fixed, `op_i` was exposing *corruption
   geometry* rather than being a mechanism in its own right — a
   materially better engineering explanation than "some operations are
   worse than others." **Amendment 3:** this is a descriptive
   conditional re-analysis of E20's already-frozen 7 cells, not a new
   significance claim — the `4/7` majority bars (§6) classify attenuation,
   they are not p-value-based tests in their own right.

**Gate 0 (run and reported first, before interpreting either question
above): does E20's `op_i` effect survive conditioning on `m0_i`** (the
pre-boundary exponent, a potential confound since `op_i` and `m0_i`
both describe properties of the trajectory reaching boundary `i`, and
could be associated with each other independent of any direct `op_i`
effect)? Framed as a confound check, not a mechanism claim: surviving
`m0_i` conditioning is evidence `m0_i` alone doesn't account for the
effect, not proof of causality.

**Explicitly not attempted:** no joint `op_i × S_i` model beyond the
support-conditioned attenuation comparison in Gate 5 (§5). No
`ΔS_i = S_i^{out}-S_i^{in}`
("did corruption spread during this op") — the simulator does not
expose a rounded intermediate readout mid-REGEN-group (confirmed by
inspection, §2); this would need new instrumentation and is deferred,
not attempted here. No analysis of the corruption *mask*
`M_i=(1[Δ_0≠0],...,1[Δ_3≠0])` beyond recording it in raw evidence for a
possible future E22 — not a hypothesis test in this contract. No
corrected recovery model, no change to `greedy_place`/
`optimal_placement` — measurement only, same discipline as E18–E20.

## 2. Objective grounding

`S_i` is computed from the same `rec[0]` vs `qr[0]` comparison E19/E20
already perform — `S_i = Σ_k 1[rec[0][k]≠qr[0][k]]`, a count instead of
a max-magnitude (`err_i`, E19) or an argmax-index-plus-sign (`j`/`sign`,
E20). Not new physics, an unexposed byproduct of existing state, same
discipline as E19 §2 / E20 §2. **Locked (§4/§7 point 7):** `S_i` and the
mask are derived from `rec`/`qr` *after* `m0`, `g_ok`, `err`, `j`,
`delta_j`, `tie` are already computed, using values already in hand —
no additional RNG draw of any kind, and no change to the RNG consumption
order relative to E20's trace function. The equivalence gate (§4)
verifies this indirectly: RNG consumption drift would desynchronize
`gen_block`'s output and cascade into a `(m0,g_ok,err,j,delta_j)`
mismatch against E20's frozen trace, which the gate checks directly.

**`ΔS_i` feasibility, checked before writing this contract (not
assumed):** the simulator (`PhotonicQuadrayBackend`) accumulates
differential-phase and amplitude noise continuously into the complex
field `fld` across every op in a REGEN group, but only materializes a
*rounded* comparable state (`rec`, via `_load_exp` and integer rounding)
at REGEN boundaries — detector noise (`nd_last`) is injected and
consumed only at that same boundary crossing. There is no method on
`PhotonicQuadrayBackend` that produces a mid-group rounded readout, so
"the corrupted state entering the last op" is not a directly observable
quantity without adding a synthetic intermediate readout (which would
itself perturb the noise-accumulation semantics the whole investigation
chain has been careful not to touch). `ΔS_i` is deferred to a possible
E22 that explicitly scopes new instrumentation, not attempted here (§8).

**`m0_i` availability:** already computed inside the trace function
(`trace[pair_id] = (m0_i, r_i, ...)`), but E20's `collect_descriptor_
stratified` discarded it (only `m0_{ip1}` is used, as the cell key).
Persisting it requires a new field in the raw-event tuple, hence a full
replay (§3) — Gate 0 is *analytically* cheap (one more stratification
on already-collected data) but not compute-free; it is reported first,
**and given explicit interpretive precedence (Amendment 4, §6)** over
the `S_i` support-conditioned attenuation conclusions (§5 Gate 5), not
merely to avoid the replay cost.

## 3. Locked parameters

| parameter | value |
|---|---|
| K, block generator, placement, σ_det, trials | unchanged from E18–E20: `K=16`, `gen_block`, `M=2`, `σ_det=3e-5`, the same 300,000 trials (same `SEED`) |
| cells for `S_i`'s own test (§1 Q1) | all 24 of E18's materially-dependent cells (a new hypothesis, tested honestly across the full family, own Bonferroni correction) |
| cells for Gate 0 and Gate 5 (support-conditioned attenuation) | E20's **7** `op_i`-omnibus-significant cells only (no association to interrogate in the other 17) |
| `S_i` primary categorization | **`S=1` vs `S≥2`** (2-way) — chosen as primary for statistical power, matching E19's finding that large single-component deviations are already rare; a 4-way `S∈{1,2,3,4}` breakdown is reported as a **diagnostic only** (not the falsification-criterion variable), wherever categories clear `n_min`. **Locked (point 6):** the 4-way diagnostic never opportunistically merges an under-`n_min` category (e.g. `S=3` or `S=4`) into a neighbor to rescue it — it is reported as below-`n_min`/unavailable, exactly as E20's per-category floor already does for `j`/`op_i`, reusing that same function unchanged |
| `m0_i` binning (Gate 0) | E18's exact→width-2→width-4→exclude hierarchy, decided by per-bin sample count only, before any `R_{i+1}` statistic is computed on it |
| per-category / per-stratum minimum | `n_min=100`, unchanged from E19/E20 |
| statistical family | `S_i`'s own test: **24 cell-level omnibus tests**, Bonferroni-corrected within its own family (matching `j`/`sign`/`op_i` in E20). Gate 0 and Gate 5: no new Bonferroni family — these are *conditional re-analyses* of the 7 already-significant `op_i` cells, reported as attenuation ratios (below), not as fresh significance claims requiring their own correction |
| effect-size metric | eta², same definition as E20 Amendment 5 (no repeat of the `A_D` mistake) |
| support-conditioned attenuation metric (Gates 0 and 5), estimator locked (Amendment 2) | for each of the 7 cells, bin the stratifying variable (`m0_i` for Gate 0, `S_i`'s primary 2-way split for Gate 5). For each retained stratum (≥2 `op_i` categories with `n≥n_min`), compute that stratum's `SS_between = Σ_c n_c·(p_c-p̄_s)²` and `SS_total = n_s·p̄_s·(1-p̄_s)` using E20's exact per-category `p_c` definition. **The conditional pooled eta² is `(Σ_s SS_between_s) / (Σ_s SS_total_s)` — SS summed across strata first, divided once at the end.** This is deliberately **not** an `n`-weighted arithmetic mean of per-stratum eta² values (a different, non-equivalent estimator, rejected because it lets a stratum with a small denominator dominate) and **not** a category-share-weighted average (that was E20 round 1's tautological `A_D` construction). Report **attenuation ratio `= eta2_conditional_pooled / eta2_marginal`** (`eta2_marginal` = that cell's frozen E20 value). If `op_i`'s apparent association is entirely attributable to the stratifying variable, the pooled value goes to ~0 by genuine within-stratum conditional independence, not by algebraic identity — this construction is not tautological by the same argument that ruled out `A_D` |

## 4. New code (additive) — Halt-and-Flag review required before running

`photonics/run_photonic_corruption_support_sweep.py`:

- `run_chain_boundary_noisy_m0trace_with_support(pb, block, boundaries,
  sigma_det, rng)` — extends E20's `*_with_descriptor` to additionally
  return `S` (`Σ_k 1[rec[0][k]≠qr[0][k]]`) and the raw mask
  `(1[Δ_0≠0],...,1[Δ_3≠0])` per boundary, alongside the existing
  `(m0, g_ok, err, j, delta_j, tie)`.
- `collect_support_stratified(sigma_det, n_trials, master, target_cells)`
  — replays the same 300,000 trials; for each `(pair_id, m0_{ip1})` in
  the 24-cell family, among `R_i=False` observations, records the raw
  tuple `(m0_i, op_i, S_i, mask_i, r_ip1)` — `m0_i` and `mask_i` are new
  relative to E20's raw_events; `op_i` reuses E20's `op_type`.
- **Equivalence cross-check — hard gate:** confirm `(m0, g_ok, err, j,
  delta_j, tie)` from the new function matches E20's `*_with_descriptor`
  exactly on matched inputs (same pattern as E20 vs E19). `S` and the
  mask are derived *after* those fields from values already in hand
  (§2) — checked indirectly, since any RNG-consumption drift would
  desynchronize `gen_block` and cascade into a mismatch this gate
  catches directly.
- **Replay fidelity — hard gate, strengthened (Amendment 5):** at full
  scale (300,000 trials), confirm (a) the raw observation count per
  cell matches E18/E19/E20's frozen `n_tot_false` exactly (as before),
  **and** (b) the *ordered* `op_i` and `R_{i+1}` sequence per cell,
  compared element-by-element against E20's frozen `raw_events`, matches
  exactly. (b) catches an ordering/indexing bug (e.g. an off-by-one in
  `M2_BOUNDARIES[pair_id]`) that a matching aggregate count alone could
  miss. At smoke scale, (a) is checked proportionally (as E19/E20); (b)
  is not applicable at smoke scale (different trial count).

## 5. Metrics & outputs

**Gate 0 — `m0_i` confound check (7 cells, reported first, interpretive
precedence per Amendment 4):** bin `m0_i` within each cell (deterministic
hierarchy, §3), retain strata with `n≥n_min` and ≥2 `op_i` categories
represented, pool per the locked SS-summed estimator (§3 — not an
`n`-weighted average of stratum eta² values), report the attenuation
ratio per cell. **Not itself a falsification gate for the whole
contract** — a confound finding changes how E21's other results should
be read (§6 outcome 4), it does not stop the analysis. **Descriptive,
not a new significance test (Amendment 3)**, applied to E20's
already-frozen 7 cells.

**`S_i`'s own test (24 cells):** omnibus chi-square + eta² for the
`S=1` vs `S≥2` split, per cell, Bonferroni-corrected within its own
24-cell family — identical mechanics to E20's `j`/`sign`/`op_i` tests.
This IS a fresh significance test, unlike Gates 0/5, since it is applied
to the full 24-cell family rather than a subset already selected on a
prior test. 4-way `S∈{1,2,3,4}` category diagnostics reported alongside
wherever populated (§3), never opportunistically merged.

**Gate 5 — support-conditioned attenuation (Amendment 1; 7 cells):**
same estimator and construction as Gate 0 (§3), stratifying by `S_i`'s
primary 2-way split instead of `m0_i`. **Descriptive, not a new
significance test (Amendment 3):** its sole purpose is to quantify
attenuation of the already-frozen E20 `op_i` association, not to
establish independent significance of a conditional effect — the `4/7`
majority bars (§6) must not be read as a fresh hypothesis test.

**Output:** canonical JSON (`results/sweeps/corruption_support_sweep.
json`) containing Gate 0's per-cell attenuation ratios, `S_i`'s full
24-cell omnibus/eta² analysis, Gate 5's per-cell attenuation ratios,
the raw `(m0_i, op_i, S_i, mask_i, r_ip1)` tuples, and the equivalence/
replay-fidelity gate results. Frozen copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

**`S_i`'s own effect (24-cell family, primary result):** substantial
(`eta2≥0.14` CI-free point estimate **and** omnibus-significant) in
`≥12/24` cells → "support explains recovery"; negligible (`eta2<0.01`)
in `≥12/24` → "support does not explain recovery"; else mixed. Same
thresholds as E20 Amendment 5, applied to a new variable.

**Support-conditioned attenuation verdict (Gate 5, 7-cell family),
pre-registered numeric bars (Amendment 1 — renamed from "mediation"):**
attenuation ratio `<0.3` in a majority (`≥4/7`) of cells → **"support
accounts for most of the operation-type association."** Ratio `≥0.7`
in a majority → **"operation-type association survives support
conditioning."** Neither majority reached → mixed/inconclusive. Per
Amendment 3, this classifies attenuation of an already-frozen
association — it is not itself a significance test of a new effect.

**Gate 0 verdict, same construction and bars, applied to `m0_i` instead
of `S_i`:** ratio `<0.3` majority → "`op_i` association substantially
accounted for by `m0_i`"; `≥0.7` majority → "`op_i` association survives
`m0_i` conditioning"; else mixed.

**Combined interpretation — Amendment 4: Gate 0 takes explicit
interpretive precedence over outcomes 1–3.** Evaluate in this order:

0. **(Precedence.)** If Gate 0's confound bar is met (majority ratio
   `<0.3`) → the E20 `op_i`-`R_{i+1}` association was substantially
   accounted for by **`m0_i`** (the pre-boundary state Gate 0 conditions
   on — not `m0_{i+1}`, E18's original cell-defining variable; these are
   different quantities). Outcomes 1–3 below are then reported as
   **secondary/descriptive**, not primary mechanistic conclusions — do
   not present "support mediates the operation effect" as the headline
   finding if the operation effect was already substantially explained
   by `m0_i` before `S_i` was ever considered.
1. Otherwise, `S_i` substantial (§6 above) **and** Gate 5 shows
   attenuation (`<0.3` majority) → `op_i` was exposing corruption
   spread — the headline mechanistic result this contract is testing
   for.
2. `S_i` substantial **and** Gate 5 shows survival (`≥0.7` majority) →
   both corruption geometry and operation type contribute independently
   — motivates a future joint `op_i × S_i` model (not built here).
3. `S_i` negligible/mixed **and** `op_i` still significant (per E20) →
   the spread hypothesis is falsified; the `op_i` effect is real but not
   explained by component count — points toward something more specific
   about corrupted *values* or arithmetic structure as a future
   direction, not this contract's to open.

The `0.3 ≤ ratio < 0.7` gray zone (both gates) is deliberate and is not
collapsed to force a verdict — reported as "mixed."

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0a. Equivalence cross-check (SS4), hard HALT on any mismatch.
# 0b. Replay fidelity (SS4), hard HALT on any mismatch.

# 1. Smoke pass -- confirm S_i and m0_i distributions have real
#    representation before committing to the full replay.
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=20000 .venv/bin/python3 \
  photonics/run_photonic_corruption_support_sweep.py

# 2. Full run (the same 300,000-trial replay, full precision)
.venv/bin/python3 photonics/run_photonic_corruption_support_sweep.py

# 3. Reproducibility: two full runs, bit-identical.

# 4. Aggregate analysis in gate order: Gate 0 (m0_i confound check,
#    reported first, interpretive precedence) -> S_i's own 24-cell test
#    -> Gate 5 (support-conditioned attenuation) -> combined
#    interpretation (SS6).

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No `ΔS_i = S_i^{out}-S_i^{in}`** — the simulator does not expose a
  mid-REGEN-group rounded readout (§2); would need new instrumentation,
  deferred to a possible, separately-scoped E22.
- **No analysis of the corruption mask `M_i`** beyond recording it in
  raw evidence — a future E22 candidate (which *specific* components
  co-deviate at `S=2`, say), not tested here.
- **No joint `op_i × S_i` model** beyond the Gate-5 support-conditioned
  attenuation comparison — a full joint model is a possible follow-on
  under outcome 2 (§6), not built in this contract.
- **No new operating-point search** — reuses E18–E20's exact 300,000
  trials at `σ_det=3e-5`, `M=2`.
- **No corrected recovery model, no change to `greedy_place`/
  `optimal_placement`** — measurement only, same discipline as E18–E20.

## 9. Results (2026-08-24)

**Gates.** Equivalence cross-check: 0/2,000 mismatches. Replay fidelity:
exact match on all 24 cells against E18–E20's frozen `n_tot_false`,
**plus** the strengthened element-wise ordered `(op_i, R_{i+1})`
sequence check (Amendment 5) — exact match, all 24 cells. Reproducibility:
two full 300,000-trial runs bit-identical
(`sha256=dc4428a8f4f3ae5e6dea2733e6c6b63fec511cd74ed0cdc72e32968b8dcf8a41`).

**`S_i`'s own effect (24-cell family):** clean null. 23/24 cells
analyzed (1 excluded, insufficient `S≥2` population), **23/23
negligible, 0 substantial** — `eta2` ranging `5.2e-08` to `0.0058`,
essentially zero everywhere. Even cleaner than `op_i`'s own eta² range
(0.018–0.041) in E20 — corruption support carries *less* information
about `R_{i+1}` than operation type does, not more.

**Gate 0 (`m0_i` confound check, 7 cells) — verdict: "`op_i` association
survives `m0_i` conditioning" (7/7, unanimous, not just a majority).**
Attenuation ratios cluster tightly around **1.0** (range 0.972–1.130) —
conditioning on `m0_i` doesn't even partially reduce `op_i`'s
association in any of the 7 cells. `m0_i` is decisively ruled out as a
confound, not merely "not proven."

**Gate 5 (`S_i` support-conditioned attenuation, 7 cells) — verdict:
"operation-type association survives support conditioning" (7/7,
unanimous).** Attenuation ratios again cluster tightly around **1.0**
(range 0.922–1.030) — conditioning on `S_i` doesn't even partially
reduce `op_i`'s association in any of the 7 cells either. The spread
hypothesis's own prediction — that `op_i`'s association should collapse
once corruption support is held fixed — does not hold, cleanly, not
marginally.

**Combined interpretation: outcome 3.** The spread hypothesis is
falsified. `op_i`'s small, statistically robust E20 association is real
— confirmed independently robust to two separate, unanimous falsification
checks — but is explained by neither the pre-boundary state (`m0_i`) nor
corruption support (`S_i`). Whatever makes `ROTC_thirds` recover worse
than `ROTC_plain`/`QSUB` at `bin=9` (E20 §9) is not "how many components
are wrong" or "what state was the trajectory in before the op" — it
plausibly involves something more specific to the arithmetic structure
of the operation itself (e.g. the circulant mixing coefficients `F,G,H`
in `ROTC_thirds` vs. the pure permutation of `ROTC_plain`/elementwise
`QSUB`) or the actual corrupted *values*, not their count or position.
Not established here — a candidate direction for a future contract, not
opened by this one (§8).
