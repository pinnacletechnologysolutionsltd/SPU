# Engineering Contract: Discrete Corruption Descriptor (E20)

**Date:** 2026-08-24
**Contract ID:** `contract_photonics_discrete_corruption_descriptor_2026-08-24.md`
**Status:** FROZEN 2026-08-24, AMENDED (round 2) same day post-results —
Amendment 1's `A_D` metric is mathematically tautological (proof + empirical
confirmation below) and is replaced by an eta-squared effect size. The
simulation/replay (equivalence check, replay fidelity, the 300,000-trial
raw event data) is unaffected and NOT rerun — round 2 is pure
post-processing on the already-frozen `raw_events`.

**Round-2 finding (why `A_D` was replaced):** `A_D` used `p_D = Σ_c
w_c·p_c` with `w_c` the *empirical* category share within the same cell
being analyzed. By the law of total probability, `Σ_c P(D=c)·P(R_{i+1}=1|
D=c) ≡ P(R_{i+1}=1) = p_F` identically whenever every category is
included — so `A_D ≡ 0` by construction, regardless of whether `D` carries
any information. Confirmed empirically on the full 300,000-trial run:
`A_D` was ≈0.00000 (5 decimals) in every one of the 24 cells for all three
descriptors except the one cell where the `n_min` floor excluded a
category (`op_i`, pair=1/bin=8, 10.4% excluded, `A_D=0.068` — exactly
proportional to the excluded fraction, not to any real effect). Underneath
this broken metric, the (unaffected) omnibus stratification test already
showed real, large signal for `op_i` (7/24 cells significant, several with
p < 1e-20) and none for `j` or `sign` (0/23, 0/24) — motivating the
replacement metric below rather than accepting the vacuous "does not
explain" verdict `A_D` produced for all three.

**Amendment 5 (round 2) — eta-squared replaces `A_D` as the gap/effect
metric (§5.2, §6):**

```
p_bar  = weighted mean of p_c across included categories (same
         computation as the old p_D, now an intermediate quantity only)
SS_between = sum_c n_c * (p_c - p_bar)^2
SS_total   = N * p_bar * (1 - p_bar)          (N = sum of included n_c)
eta2       = SS_between / SS_total
```

Standard proportion-of-variance-explained effect size for a categorical
predictor against a binary outcome — not tautological, since it measures
*dispersion between categories* rather than a weighted average that
collapses back to the cell's own marginal rate. Classified per Cohen's
conventional benchmarks for eta-squared: `<0.01` negligible, `0.01–0.06`
small, `0.06–0.14` medium, `≥0.14` large. No analytic CI is computed
(deferred as future work if a specific cell's borderline classification
needs it); "substantial" per cell requires **both** `eta2 ≥ 0.14` **and**
the cell's (unchanged) Bonferroni-corrected omnibus significance flag, to
avoid a large point-estimate driven by noise in an underpowered cell.
"Negligible" per cell is `eta2 < 0.01`. The `≥12/24` aggregate threshold
for "explains most" / "does not explain" is unchanged from §6.

`A_c` (per-category diagnostic, Amendment 2) is unaffected and still
reported.

---

**Roles:**
- **Spec Author:** Claude, formalizing John/GTP's explicit E20 scoping
  (2026-08-24, after E19): "reconstruct the actual corrupted lane-0
  transition at the failing boundary and ask whether something like
  `D_i = (j, sign(Δ_j), op_i)` collapses the E18 conditional
  dependence... turns `R_i → R_{i+1}` into `D_i → R_{i+1}|m0_{i+1}`."
- **Halt-and-Flag Implementer:** review whether testing `D_i`'s three
  components jointly or separately is the right scope (§1/§3) — the
  central risk is the same one E19 flagged for its own median split:
  fragmenting an already-thin `R_i=False` population into cells too
  small to say anything.
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_corrupted_state_sufficiency_2026-08-23.md` (E19)
  — this contract's entire methodology (deterministic replay of E18's
  exact 300,000 trials, the attenuation metric `A`, frozen thresholds,
  hard equivalence/replay-fidelity gates) is **reused exactly**, applied
  to new candidate descriptors instead of `err_i`. E19's own frozen
  conclusion: error *magnitude* explains none of E18's gap (max `A` CI
  upper bound `0.116` against a `0.5` bar) — ruling magnitude out is
  what motivates testing *discrete* properties of the corruption here.
- `contract_photonics_correlation_mechanism_2026-08-23.md` (E18) — the
  24 materially-dependent `(pair, m0_{i+1})` cells this contract reuses
  exactly, same selection-conditional scope caveat as E19 §1.
- E19's own structural finding (its §9): position pair 1 (groups 2→3)
  produced **zero** `err_i>1` cases at any bin across 300,000 trials —
  preserved here as its own observation, not assumed to generalize or
  folded into this contract's hypothesis.

**Amendments incorporated (Halt-and-Flag round 1, 2026-08-24):**
1. Gap explanation uses the descriptor-conditioned weighted rate `A_D`
   (§5.2), not a best-vs-worst single category's `A_c` (avoids
   post-hoc category selection; §3, §5, §6).
2. `A_c` retained as a per-category diagnostic only, never the
   "explains most" criterion (§5.3).
3. Statistical family frozen as 24 cell-level **omnibus** tests per
   descriptor, Bonferroni-corrected within each descriptor separately
   (§3, §5.1).
4. Raw `(j, delta_j, err, op_i, R_{i+1})` tuples retained in frozen
   evidence, not just the derived `sign` (§4, §5.4).
Also: `op_i`'s definition dropped the causal-responsibility framing in
favor of a purely mechanical one (§2).

---

## 1. Objective

**Within the `R_i=False` subpopulation, do any of three discrete
properties of the corrupted lane-0 state at boundary `i` — (a) which
component `j∈{0,1,2,3}` carries the largest deviation, (b) the sign of
that deviation, (c) the operation type active at boundary `i` (`QSUB`
vs. `ROTC` with exact-thirds angles vs. `ROTC` with plain angles) —
stratify `P(R_{i+1})` beyond `m0_{i+1}` alone, and if so, how much of
E18's gap does each explain?**

**Tested as three separate univariate stratifications, not one joint
`D_i` model (Halt-and-Flag scoping decision, §3):** a joint `(j, sign,
op)` descriptor has up to `4×2×3=24` categories, which would fragment
the `R_i=False` population — already thin enough that E19 had to
exclude 11/24 cells testing a single binary split — far below any
usable sample size. Testing the three components independently (each a
2–4-way split, the same order of magnitude as E19's binary split)
keeps this contract's cells comparably powered to E19's, at the cost of
not directly testing the full `D_i → R_{i+1}` claim John/GTP proposed —
if one or more components shows a real, attenuation-explaining effect
on its own, a joint model *combining only the descriptors that survived
this screening* is the natural, better-powered follow-on (§8), not
attempted here.

**Explicitly not attempted:** no joint `(j, sign, op)` model (§ above).
No new operating-point search or trial draw — reuses E19's exact replay
infrastructure (§3). No corrected recovery model, no change to
`greedy_place`/`optimal_placement` — same discipline as E18/E19.

## 2. Objective grounding

`rec[0]` and `qr[0]` (both already computed and compared inside the
reused scoring function) are 4-component integer vectors — E19 exposed
only their aggregate `max` deviation (`err_i`); this contract exposes,
additionally, **which** component achieves that max (`j`) and its
**sign**. Both are already-computed byproducts of the existing
comparison, not new physics (same discipline as E19 §2).

`op_i` — the operation active at boundary `i` — is defined mechanically
and without a causal claim (amendment, Halt-and-Flag round 1): **`op_i`
is the operation immediately preceding boundary `i`, obtained from
`block[i-1]`** (1-indexed `i`), categorized as `QSUB`, `ROTC_thirds`
(angles `{1,3,4}`, the angles with the exact-thirds division E11
studied), or `ROTC_plain` (angles `{0,2,5}`) — `QLDI` cannot occur here
since it only appears in ops 1–2 (group 1), outside the 24 analyzed
cells' scope (all `pair_id ≥ 1`, per E18/E19). The established finding
that only the *last* op's noise draw survives to affect a boundary's
readout motivates *why* this is a reasonable descriptor to test, but
E20's descriptor definition does not depend on or assert that this op
is causally responsible for the deviation — only that it is the
mechanically-preceding, reproducibly-identifiable operation.

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| placement | `M=2` fixed boundaries (E14/E18/E19, reused) |
| σ_det | `3e-5` — E18/E19's locked operating point, reused exactly |
| trials | **the same 300,000 trials E18/E19 ran** (same `SEED`, same
  trial-index range `0..299,999`) — a further-instrumented replay, same
  design as E19 §3 |
| cells analyzed | E18's 24 materially-dependent cells (same selection-
  conditional scope caveat as E19 §1) |
| descriptors tested | three, **separately** (§1): `j` (4-way),
  `sign(Δ_j)` (2-way), `op_i` (3-way) |
| per-category minimum | `n_min=100` per category (matching E19's
  reduced bar for a secondary stratification of an already-identified
  population) — a category failing this bar is excluded from the
  descriptor-conditioned weighted average (§5 Amendment 1) and from the
  omnibus test for that cell, and reported, not silently dropped, same
  as E19 §3 |
| primary gap-explanation metric (Amendment 1) | **descriptor-conditioned
  weighted recovery**, not per-category `A_c` — see §5. `A_c` is
  retained only as a diagnostic (Amendment 2), never the "explains
  most" criterion |
| statistical family (Amendment 3) | **24 cell-level omnibus tests per
  descriptor** (one omnibus test per `(pair, m0_{i+1})` cell, testing
  whether recovery differs among that cell's represented categories),
  Bonferroni-corrected **within each descriptor's own 24-test family**
  — three independent families (`j`: 24, `sign`: 24, `op_i`: 24), never
  pooled into one correction and never expanded to include every
  pairwise category comparison. For `sign` (2 categories), the omnibus
  test is the two-proportion z-test used throughout E16/E18/E19 |

## 4. New code (additive) — Halt-and-Flag review required before running

`photonics/run_photonic_discrete_corruption_descriptor_sweep.py`:

- `run_chain_boundary_noisy_m0trace_with_descriptor(pb, block,
  boundaries, sigma_det, rng)` — extends E19's
  `run_chain_boundary_noisy_m0trace_with_error` (itself an extension of
  E16's frozen `m0trace`) to additionally return, per boundary, `j`
  (`argmax_k |rec[0][k]-qr[0][k]|`, lowest index on ties), `delta_j`
  (the **signed** `rec[0][j]-qr[0][j]`, Amendment 4 — `sign` is derived
  from this, not computed/stored separately) alongside the existing
  `(m0, g_ok, err)`.
- `op_type(block, boundary_pos)` — categorizes `block[boundary_pos-1]`
  as `QSUB`, `ROTC_thirds`, or `ROTC_plain` per §2 (mechanical
  definition, no causal claim).
- `collect_descriptor_stratified(sigma_det, n_trials, master)` —
  replays the same 300,000 trials; for each `(pair, m0_{i+1})` in E18's
  24 cells, among `R_i=False` observations, records the raw tuple
  `(j, delta_j, err, op_i, R_{i+1})` per qualifying event (Amendment 4
  — `err` and the full raw tuple are retained in the frozen evidence
  even though only `j`, `sign(delta_j)`, and `op_i` are E20's
  inferential variables, so a later contract does not need to replay
  the simulator again to recover them).

**Halt-and-Flag pre-review items:**
- **Equivalence cross-check — hard gate (same discipline as E19):**
  confirm the new function's `(m0, g_ok)` sequence is bit-identical to
  E19's `run_chain_boundary_noisy_m0trace_with_error`'s (and therefore
  to E16's original) on matched inputs. Any mismatch is a HALT
  condition, not advisory.
- **Replay fidelity — hard gate:** confirm this contract's raw
  `(pair, m0_{i+1}, R_i)` counts match E18/E19's exactly.
- **Tie-breaking for `j` must be deterministic and stated, not
  incidental:** lowest-index tie-break, applied consistently — record
  how often ties actually occur (a diagnostic, not expected to be
  common given noise is continuous-valued before rounding, but report
  rather than assume).
- **`op_i` category sparsity:** some `(pair, m0)` cells may have very
  skewed op-type distributions (e.g. mostly `ROTC_plain`, few `QSUB`)
  — report actual category counts per cell alongside the test, same
  discipline as E19's `err_i` distribution reporting.

## 5. Metrics & outputs

Two distinct questions, kept separate per Halt-and-Flag review (does
the descriptor carry information at all vs. how much of E18's gap it
explains):

### 5.1 Stratification (does the descriptor carry information?)

- **Per descriptor, per cell:** one **omnibus test** (Amendment 3) over
  that cell's represented categories (chi-square-style multi-category
  test for `j`/`op_i`; the standard two-proportion z-test for `sign`),
  asking whether `P(R_{i+1})` differs among categories at all — not
  which pairwise comparison is largest.
- Bonferroni correction applied **within each descriptor's own 24-cell
  family**, independently (§3) — three corrected p-value sets, never
  pooled or expanded to pairwise category counts.
- If significant, report category-specific recovery rates `p_c` and
  counts as a follow-on breakdown (not a separate hypothesis test).

### 5.2 Effect size (Amendment 5, round 2 — primary metric, supersedes
Amendment 1's `A_D`)

For each descriptor, each cell, compute **eta-squared**:

```
p_bar      = weighted mean of p_c across included categories
SS_between = sum_c n_c * (p_c - p_bar)^2
SS_total   = N * p_bar * (1 - p_bar)
eta2       = SS_between / SS_total
```

`eta2` is the primary "how much of the outcome variance does this
descriptor explain" number — categories excluded by the `n_min=100`
floor (§3) are excluded from the computation, and this is reported per
cell. Classification thresholds (§6) are applied to `eta2`, not to any
single category's `A_c`. (Amendment 1's `A_D = (p_D-p_F)/(p_T-p_F)`
using a category-share-weighted `p_D` is mathematically tautological —
`p_D ≡ p_F` by the law of total probability whenever no category is
excluded — and is retired; see the round-2 finding at the top of this
contract.)

### 5.3 Diagnostic only (Amendment 2)

Per category, still report `p_c`, counts, and `A_c = (p_c-p_F)/(p_T-p_F)`
with its CI — useful for seeing *which* corruption signatures look
most/least recoverable, but never used as the "explains most"
criterion (that role belongs to `A_D`, §5.2).

### 5.4 Output

- Output: canonical JSON
  (`results/sweeps/discrete_corruption_descriptor_sweep.json`) — one
  block per descriptor, containing the omnibus test results (§5.1),
  `A_D` per cell (§5.2), and category-level diagnostics (§5.3), plus
  the raw `(j, delta_j, err, op_i, R_{i+1})` tuples (Amendment 4).
  Frozen copy with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

Applied **independently to each of the three descriptors** (`j`,
`sign`, `op_i`), using `eta2` (§5.2, Amendment 5, round 2) — not any
single category's `A_c`, and not the retired `A_D`:

- **Explains most of the gap:** `≥12/24` cells show substantial
  explanation (`eta2 ≥ 0.14` **and** that cell's omnibus test is
  Bonferroni-significant, §5.1) for that descriptor.
- **Does not explain the gap:** `≥12/24` cells show negligible
  explanation (`eta2 < 0.01`) for that descriptor.
- **Mixed:** neither threshold reached.

A descriptor's stratification result (§5.1 — does it carry information
at all) is reported alongside but is **not** itself the falsification
criterion: a descriptor could show a significant omnibus split yet
still fail to move `A_D` much (an effect too small or too evenly
distributed to account for much of the gap), and that combination is
itself a reportable, informative outcome, not a contradiction.

If **any** descriptor reaches "explains most," that descriptor becomes
the leading candidate for a joint model (§1's deferred follow-on). If
**all three** reach "does not explain," that is a strong, informative
result in its own right: it would mean the missing information in `R_i`
is not captured by *any* of these three natural discrete properties,
motivating a fundamentally different kind of descriptor (e.g. something
about the state *before* the failing op, not just the failure's own
signature) rather than another incremental variant of this contract's
approach.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0a. Equivalence cross-check (SS4), hard HALT on any mismatch.
# 0b. Replay fidelity (SS4), hard HALT on any mismatch.

# 1. Smoke pass -- confirm each descriptor's categories have real
#    representation (not degenerate, e.g. op_i always ROTC_plain) in
#    at least several cells before committing to the full replay.
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=20000 .venv/bin/python3 \
  photonics/run_photonic_discrete_corruption_descriptor_sweep.py

# 2. Full run (the same 300,000-trial replay, full precision)
.venv/bin/python3 photonics/run_photonic_discrete_corruption_descriptor_sweep.py

# 3. Reproducibility: two full runs, bit-identical (a deterministic
#    replay -- this gate is a correctness check on the new code).

# 4. Aggregate analysis (SS5/SS6) -- three independent verdicts.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No joint `(j, sign, op)` model** — deferred to a separate, later,
  explicitly-authorized contract, contingent on one or more components
  showing a real effect here (§1).
- **No new operating-point search or fresh trials** — reuses E18/E19's
  exact replay (§3).
- **No corrected recovery model, no change to `greedy_place`/
  `optimal_placement`** — measurement only, same discipline as E18/E19.
- **No investigation of the pair-1 (`err_i` always `1`) structural
  finding** — preserved as its own observation (E19 §9), not folded
  into this contract's hypothesis or scope.

## 9. Results (2026-08-24)

**Gates.** Equivalence cross-check: 0/2000 mismatches. Replay fidelity:
exact match on all 24 cells against E18/E19's frozen `n_tot_false`.
Reproducibility: two full 300,000-trial runs bit-identical
(`sha256=c059d2b5b6f38f25676ce2e4425ecf20d9c93cec5aa9811e836239fcfa05264`,
same hash after the round-2 eta-squared reanalysis, since round 2 is
pure post-processing on the frozen `raw_events` — no resimulation).

**Round 1 (as frozen, before results review):** Amendment 1's `A_D`
metric was found to be mathematically tautological — `p_D = Σ_c
w_c·p_c` collapses identically to the cell's own marginal `p_false` by
the law of total probability whenever no category is excluded by the
`n_min` floor. Confirmed empirically: `A_D` was ≈0.00000 (5 decimals)
in every one of the 24 cells for all three descriptors except the one
cell where a category was excluded (`op_i`, pair=1/bin=8, 10.4%
excluded, `A_D=0.068` — exactly proportional to the excluded fraction,
not to any real effect). This made `A_D`'s "does not explain the gap"
verdict for all three descriptors vacuous rather than informative — see
the round-2 amendment (top of this contract) for the fix.

**Round 2 (eta-squared, Amendment 5 — final).**

**Headline:** No tested discrete corruption descriptor explains E18's
dependence at large effect size. Component identity (`j`) and error
sign are null. Operation type (`op_i`) shows a small but highly
reproducible downstream recovery effect, especially at `m0=9`, with
`ROTC_plain > QSUB > ROTC_thirds`; this is insufficient to constitute
an explanation of the E18 gap but is a credible candidate for follow-up
investigation.

The formal `≥12/24`-cell aggregate tier (§6) collapses to "does not
explain the gap" for all three descriptors, but that binary tier hides
a real distinction the frozen omnibus test already draws. Three
interpretive categories, not two:

1. **Substantial explanation** — clears both `eta2≥0.14` and omnibus
   significance.
2. **Statistically real but sub-threshold** — omnibus-significant, but
   `eta2<0.14`.
3. **Null** — not omnibus-significant / negligible effect.

| descriptor | formal E20 tier | interpretation |
|---|---|---|
| `j` | does not explain the gap | **Null** — 0/23 omnibus-significant, eta² 0.00003–0.00246 |
| `sign` | does not explain the gap | **Null** — 0/24 omnibus-significant, eta² 0.00000–0.00146 |
| `op_i` | does not explain the gap | **Small, highly significant effect** — 7/24 omnibus-significant (several p<1e-20, e.g. p=4.5e-65 at pair=1/bin=9), eta² 0.018–0.041 (category 2 above, not category 3) |

`j` and `sign` are clean nulls: essentially zero variance explained
anywhere, zero significant omnibus splits across all 23/24 and 24/24
analyzed cells respectively.

`op_i` belongs in category 2, not category 3 — the aggregate "18/24
negligible, 0 substantial" count is the correct application of the
frozen threshold, but reporting it without the significance context
would make `op_i` sound equivalent to `j`/`sign`, which the data
explicitly reject: `op_i` clears the (Bonferroni-corrected) omnibus
significance bar in 7/24 cells, several overwhelmingly (p as low as
4.5e-65), but the effect size itself is *small* by Cohen's convention
(0.01–0.06), well under the `≥0.14` "large" bar Amendment 5 requires
for "substantial explanation." **Exploratory structural observation,
not a new hypothesis test** (this contract did not pre-register a
per-bin breakdown, so it is reported as a lead, not a finding): at 5 of
the 6 `bin=9` cells (pairs 1–5), `op_i` shows a small, tightly-
replicated, directionally consistent split with non-overlapping
category CIs in every one of those 5 cells:

| category | typical `A_c` at `bin=9` cells (diagnostic, not the primary metric) |
|---|---|
| `ROTC_plain` | +0.30 to +0.45 (recovers closer to clean) |
| `QSUB` | −0.11 to −0.17 |
| `ROTC_thirds` | −0.20 to −0.38 (recovers worst) |

**Conclusion:** none of the three univariate descriptors (`j`, `sign`,
`op_i`) is a *large-effect* explanation of E18's `R_i`-conditioned gap.
`j` and `sign` show no signal at all. `op_i` shows a real, small,
highly statistically robust, and directionally consistent signal
(exact-thirds `ROTC` corruption recovers worse than plain `ROTC` or
`QSUB` corruption) that the other two descriptors entirely lack —
informative for a future joint model or as a seed for further
investigation (§8 non-goal: no joint model attempted here), but not
itself sufficient to account for the bulk of E18's gap. Per E19's own
framing, this continues to push the missing information upstream,
toward the state *before* the failing operation, rather than toward any
one discrete signature of the failure itself examined so far.

**On next steps:** E20 → documentation → regression → handover, then
whether E21 is warranted is a deliberate decision, not an automatic
continuation — not opened in this contract. The `bin=9` pattern is
tempting to optimize around directly, but E18–E20 have specifically
built a discipline around not converting an interesting observation
into a post-hoc mechanism; a future E21, if authorized, should be
motivated by a specific mechanistic hypothesis (why does the operation
immediately preceding a boundary alter downstream recoverability, and
why is the effect strongest near the `m0=9` transition region?), not a
larger joint-descriptor search or an optimization pass over `op_i`.
