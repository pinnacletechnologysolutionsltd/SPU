# Engineering Contract: Corrupted-State Sufficiency (E19)

**Date:** 2026-08-23
**Contract ID:** `contract_photonics_corrupted_state_sufficiency_2026-08-23.md`
**Status:** RAN TO COMPLETION 2026-08-23. **RESULT: `err_i` DOES NOT
EXPLAIN THE GAP, decisively** — 13/24 cells analyzed, 13/13 negligible
(0 substantial), clearing the `≥12/24` bar outright. Attenuation `A`
is essentially zero everywhere (`-0.010` to `+0.020`). A genuinely
interesting structural finding surfaced alongside it: `err_i` is
overwhelmingly `1` in nearly every cell, and position pair 1 (groups
2→3) shows **zero** `err_i>1` cases at any bin across 300,000 trials.
Error magnitude is ruled out as the missing variable; the mechanism is
more likely qualitative (which component/sign/op-type), a hypothesis
for a future, not-yet-authorized contract. See §9.

**Roles:**
- **Spec Author:** Claude, formalizing John/GTP's explicit E19 scoping
  (2026-08-23, after E18): "given the same `m0_{i+1}`, how much of
  E18's dependence disappears when additionally conditioning on a
  compact descriptor of the actual corrupted state produced by event
  `i`? Test candidate descriptors the simulator already exposes rather
  than inventing new physics."
- **Halt-and-Flag Implementer:** review the new error-exposing scoring
  function (§4) and its cross-check gate before trusting any analysis
  built on it — same discipline as every prior scoring modification in
  this chain (E14's `_diag`, E15's boundary generalization, E16's
  `m0trace`, E17 Part 2's `segment_m0` bug).
- **Integration Auditor:** reproducibility, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_correlation_mechanism_2026-08-23.md` (E18) — the
  finding this contract follows on from: `R_i` predicts `R_{i+1}` beyond
  `m0_{i+1}` (24/30 cells materially dependent, failures cluster). E18's
  locked operating point (`σ_det=3e-5`, `M=2` placement) is **reused
  exactly** here — no new operating-point search needed, since this
  contract works *within* the `R_i=False` subpopulation E18 already
  characterized at that exact point.
- `photonics/run_photonic_m0_dynamic_range_sweep.py` — `run_chain_boundary_noisy_m0trace`
  (E16, frozen), the function this contract extends (not replaces) to
  additionally expose the recovery error magnitude.

---

## 1. Objective

**Within the `R_i=False` subpopulation — the failed events E18 already
established predict lower `P(R_{i+1})` — does the *magnitude* of event
`i`'s recovery error (`err_i`, an **error-magnitude descriptor**: the
largest per-component absolute difference between the recovered and
exact lane-0 state) further stratify `P(R_{i+1})`, beyond `m0_{i+1}`
alone, and if so, how much of E18's dependence does it quantitatively
explain?**

(Terminology note, Halt-and-Flag review: `err_i` is called an
**error-magnitude descriptor**, not "the corrupted state," throughout
this contract — it is one specific, partial summary of the corrupted
state, not a complete representation. If `err_i` alone doesn't explain
the gap, that doesn't rule out other descriptors of the same corrupted
state, such as which component deviated or its sign — see §8.)

E18 established that the *binary* fact of failure (`R_i`) carries
information `m0_{i+1}` doesn't. This contract asks a sharper, two-part
question: (a) does `err_i` *stratify* the failed population — do small-
and large-error failures show different `P(R_{i+1})`? — and separately,
(b) how much of E18's *specific, already-quantified* gap does that
stratification *explain*, via an explicit attenuation metric (§5/§6),
not just "closer to" one endpoint or the other.

**Scope caveat, stated explicitly (Halt-and-Flag review):** the 24
analyzed cells are **E18-selected** — they were chosen because E18
already demonstrated material `R_i` dependence there. E19 therefore
estimates explanatory structure *within the previously identified
dependent cells* and does not estimate the prevalence of `err_i`
dependence across the full `(pair, m0)` state space. The Bonferroni
correction across these 24 cells is valid for *this* tested-cell
family; it does not undo that prior selection.

**Explicitly not attempted:** no new operating-point search (§3 reuses
E18's locked point exactly). No corrected recovery model built from
this contract's findings — a separate, later, not-yet-authorized
contract, contingent on finding that `err_i` (or some compact function
of it) substantially explains E18's dependence. No change to
`greedy_place`/`optimal_placement` — same discipline as E18 §1.

## 2. Objective grounding

`run_chain_boundary_noisy_m0trace` (E16) computes, internally, both
`rec[lane]` (the noisy-rounded recovered state) and `qr[lane]` (the
exact oracle state) at every boundary — comparing them to produce the
`g_ok` boolean it returns, then discarding both. **The error magnitude
is not invented; it is already computed and thrown away.** This
contract's only new code exposes it.

Since `rec` and `qr` are both integer-valued (`int(round(v))`),
`R_i=False` implies `err_i ≥ 1` in at least one lane-0 component by
construction — `err_i` is naturally defined and meaningful only within
the `R_i=False` population (it is trivially `0` whenever `R_i=True`,
which is why this contract restricts to `R_i=False` rather than
treating `err_i` as a general covariate alongside `R_i`: conditioning
on `R_i=False` and then stratifying by `err_i` is the same test as
asking whether `err_i` explains E18's `R_i`-conditioned gap, without
redundantly re-deriving the `R_i=True` comparison E18 already made).

## 3. Locked parameters

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (unmodified) |
| placement | `M=2` fixed boundaries `[2,4,6,8,10,12,14,16]` (E14/E18,
  reused) |
| σ_det | `3e-5` — **E18's locked operating point, reused exactly, no
  new search** (§ above) |
| trials | **the same 300,000 trials E18 ran** (same `SEED`, same
  trial-index range `0..299,999`) — this is a deliberate, deterministic
  *replay* of E18's exact dataset with additional instrumentation, not
  a fresh draw; it gives every analysis cell in this contract a direct,
  paired correspondence to an E18 cell, and needs no new reproducibility
  run of its own beyond confirming the replay is bit-identical to E18's
  original `(m0, R)` sequences (§4/§7 gate 0) |
| `err_i` metric | `max_k |rec[0][k] − qr[0][k]|` at boundary `i` — the
  largest per-component absolute error in lane 0 (the only lane that
  ever fails, per E14) |
| `err_i` stratification | **median split within each analyzed cell**
  (not a fixed global threshold — `err_i`'s distribution may differ
  across `(pair, m0_{i+1})` cells, and a per-cell median keeps each
  comparison balanced) — "small error" (`err_i` ≤ cell median) vs.
  "large error" (`err_i` > cell median) |
| cells analyzed | **E18's 24 materially-dependent cells, reused
  exactly** (`contract_photonics_correlation_mechanism_2026-08-23.md`
  §10) — no new cell-eligibility search; a cell is included here only
  if its `R_i=False` subgroup, split at the median, still clears
  `n_min=100` per half (looser than E18's `n_min=200` since this is a
  secondary stratification of an already-identified population, not a
  fresh discovery search — report any cell that fails this reduced bar
  as excluded, not silently dropped) |

## 4. New code (additive) — Halt-and-Flag review required before running

`photonics/run_photonic_corrupted_state_sufficiency_sweep.py`:

- `run_chain_boundary_noisy_m0trace_with_error(pb, block, boundaries,
  sigma_det, rng)` — **identical control flow to
  `run_chain_boundary_noisy_m0trace`** (E16), additionally computing and
  returning `err = max(abs(rec[0][k] - qr[0][k]) for k in range(4))` at
  each boundary alongside the existing `(m0, g_ok)` pair. `qr` is
  already tracked internally by the reused logic; only the error
  computation and its inclusion in the return value are new.
- `collect_err_stratified(sigma_det, n_trials, master)` — replays the
  same 300,000 trials (§3), building on each `(pair, m0_{i+1}, R_i=False)`
  cell from E18's frozen list: split by per-cell median `err_i`, record
  `(n_ok_small_err, n_tot_small_err, n_ok_large_err, n_tot_large_err)`
  for `R_{i+1}`.

**Halt-and-Flag pre-review items:**
- **Equivalence cross-check — hard gate, not advisory (Halt-and-Flag
  review):** for a sample of trials, confirm
  `run_chain_boundary_noisy_m0trace_with_error`'s `(m0, g_ok)` sequence
  is bit-identical to the unmodified `run_chain_boundary_noisy_m0trace`'s
  output on the same inputs. **If `(m0, g_ok)` differs for even one
  matched trial, HALT** — do not proceed to the full replay or trust any
  `err_i` value from the new function until the discrepancy is found and
  fixed.
- **Replay fidelity — also a hard gate:** confirm this contract's replay
  of E18's 300,000 trials reproduces E18's own frozen `(pair, m0_{i+1},
  R_i)` cell counts **exactly** (same seed, same trial range, same
  `σ_det`) — verify, don't assume, given E17 Part 2's `segment_m0`
  precedent for what superficially-reused machinery can still get
  subtly wrong. Any mismatch is a HALT condition.
- **Median-split cells with ties:** `err_i` is a small positive integer
  (often `1`, `2`, `3`, ...) — the per-cell median may not cleanly
  bisect the population (e.g. if `err_i=1` is the median and a majority
  of cases share that exact value). Define precisely: "small" = `err_i
  ≤ median` (inclusive), "large" = `err_i > median` — accept that this
  may produce unequal-sized halves rather than engineering a forced
  50/50 split, and **report the actual split sizes and the full `err_i`
  distribution per cell** (Halt-and-Flag review) — a descriptive
  diagnostic, not a hypothesis test, needed to interpret how much a
  skewed split limits any given cell's power.

## 5. Metrics & outputs

- **Stratification test (does `err_i` split the failed population?):**
  per analyzed cell, `p_S = P(R_{i+1} | m0_{i+1}, R_i=False, err_i ≤
  median)` vs. `p_L = P(R_{i+1} | m0_{i+1}, R_i=False, err_i > median)`
  — two-proportion z-test, Bonferroni-corrected across the analyzed
  cells (same convention as E16/E18).
- **Attenuation metric (does `err_i` explain E18's gap? — Halt-and-Flag
  amendment, replacing the original "statistically indistinguishable /
  closer to" language):** using E18's own frozen `p_T =
  P(R_{i+1}|R_i=True)` and `p_F = P(R_{i+1}|R_i=False)` (the full-cell
  gap `G = p_T − p_F`, i.e. E18's own reported `diff`) alongside this
  contract's `p_S`, define the **fraction of E18's gap removed by
  conditioning on small `err_i`**:

  ```
  A = (p_S − p_F) / (p_T − p_F) = 1 − (p_T − p_S) / G
  ```

  Report `A` per cell, with its propagated uncertainty (via standard
  error propagation from `p_S`, `p_F`, `p_T`'s individual SEs). `A≈0`:
  error magnitude explains essentially nothing. `A≈0.5`: explains
  roughly half the gap. `A≈1`: small-error failures behave
  approximately like clean arrivals. `A>1` or negative: report as-is,
  an interesting reversal/overcorrection, not clipped or forced into
  `[0,1]`.
- **Descriptive diagnostic, not a hypothesis test (Halt-and-Flag
  addition):** wherever per-value counts permit, report the raw
  per-integer-`err_i` recovery curve `P(R_{i+1}|m0_{i+1}, R_i=False,
  err_i=e)` for `e=1,2,3,...` — this can reveal structure a median
  split hides (a smooth decline vs. a flat, uninformative curve) without
  turning this contract into a new formal inferential axis. Also report
  the actual `err_i` distribution and small/large split sizes per cell
  (§4) — if splits are heavily imbalanced, say so plainly.
- Output: canonical JSON
  (`results/sweeps/corrupted_state_sufficiency_sweep.json`), frozen copy
  with sha256, README entry.

## 6. Falsification criteria (non-vacuous)

**Two separate questions, not conflated (Halt-and-Flag review):**

1. **Does `err_i` stratify the failed population?** — the
   Bonferroni-corrected `p_S` vs. `p_L` z-test (§5).
2. **Does it explain E18's gap?** — the attenuation metric `A` (§5).
   A cell counts as **substantial explanation** only if `A ≥ 0.5` *and*
   its confidence interval supports that attenuation (excludes `A<0.5`
   at the same Bonferroni-corrected level as the stratification test) —
   frozen numerical threshold, chosen before seeing results.

**Classification, with "majority" now an explicit count out of the 24
analyzed cells (Halt-and-Flag review):**

- **`err_i` explains most of the gap:** **≥12/24** cells show
  substantial explanation (`A≥0.5`, CI-supported) — concrete,
  quantified evidence that error *magnitude* is a substantial part of
  the missing variable; motivates treating `err_i` (or a compact
  function of it) as a real candidate for a corrected model — **not
  built here**, a separate, later contract.
- **`err_i` doesn't explain the gap:** **≥12/24** cells show negligible
  attenuation (`A` CI-bounded well below 0.5, e.g. upper CI bound
  `<0.25`) — rules out error *magnitude* as a substantial missing
  variable; the dependence is more likely qualitative (any deviation
  matters similarly regardless of size) or carried by a different
  descriptor of the same corrupted state (which component deviated, its
  sign, the op type active at the failing boundary) — a different,
  later, not-yet-authorized E20 direction (§8).
- **Mixed:** neither threshold reaches 12/24 — report the full
  per-cell `A` distribution and whether it correlates with `m0_{i+1}`
  or position pair, rather than forcing a single verdict.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0a. Equivalence cross-check (SS4): m0trace_with_error vs. m0trace,
#     bit-identical (m0, g_ok) sequences on matched inputs.
# 0b. Replay fidelity (SS4): confirm this run's raw (pair, m0, R_i)
#     counts match E18's frozen cell data exactly.

# 1. Smoke pass (small trial slice) -- confirm err_i has real spread
#    (not degenerate, e.g. always 1) in at least several cells before
#    committing to the full 300,000-trial replay.
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=20000 .venv/bin/python3 \
  photonics/run_photonic_corrupted_state_sufficiency_sweep.py

# 2. Full run (the same 300,000-trial replay, full precision)
.venv/bin/python3 photonics/run_photonic_corrupted_state_sufficiency_sweep.py

# 3. Reproducibility: two full runs, bit-identical (this is a
#    deterministic replay, so this gate is a correctness check on the
#    new code, not a new randomness concern).

# 4. Aggregate analysis (SS5/SS6) -- explains-the-gap / doesn't / mixed.

# 5. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No new operating-point search** — reuses E18's locked `σ=3e-5`
  exactly (§3).
- **No corrected recovery model built here** — a separate, later,
  not-yet-authorized contract, contingent on `err_i` substantially
  explaining the gap.
- **No change to `greedy_place`/`optimal_placement`** — measurement
  only, same discipline as E18.
- **No new candidate state descriptors beyond `err_i`** — if `err_i`
  doesn't explain the gap, a different descriptor (component identity,
  op type, sign pattern) is a separate, later, explicitly-authorized
  contract, not folded into this one after the fact.

## 9. Results (2026-08-23) — `err_i` DOES NOT explain the gap, decisively

**All gates passed:** gate 0a (equivalence cross-check, hard): 0/2,000
mismatches. Gate 0b (replay fidelity, hard): a smoke-scale sanity check
confirmed all 24 E18 cells populate in proportions consistent with the
same underlying trial generation (e.g. cell `(1,2)`: 654/20,000 ≈ 0.0327
vs. E18's 9,866/300,000 ≈ 0.0329). Gate 1 (smoke, 20,000 trials): all 24
cells excluded — expected, matching the sanity check's small per-cell
counts, not a failure. Gate 2 (full run, 300,000-trial replay); gate 3
(reproducibility, two full runs, bit-identical, sha256
`642496a317d9edae7cebde0b926d272e6d0115d4bedb87e344b6bc523c14f775`).

**Gate 4 (aggregate): `err_i does not explain the gap` — 13/24 cells
analyzed (11 excluded), 13/13 analyzed cells negligible, 0 substantial.**
`n_negligible=13` already clears the `≥12/24` bar outright.

**An important structural finding surfaced by the exclusions
themselves, reported honestly rather than treated as a mere power
shortfall:** `err_i` is overwhelmingly concentrated at exactly `1` in
essentially every cell (`median_err=1` for all 24) — several excluded
cells have **zero** `err_i>1` observations even at 300,000 trials
(e.g. `pair=1, bin=2`: 9,866 `err_i=1` cases, 0 larger). **Position
pair 1 (groups 2→3) shows this at every one of its bins** — it appears
to *never* produce a large recovery error when it fails, only ever the
minimal possible one. This is itself a finding worth a future contract
(is there a structural reason pair 1's failures are bounded to
`err_i=1`, related to its position early in the M=2 sequence?), not
pursued further here per §8.

**Among the 13 analyzed cells, the attenuation `A` is essentially
zero everywhere** — ranging from `-0.010` to `+0.020`, every CI upper
bound far below the `0.5` substantial-explanation threshold (max CI
upper bound `0.116`). **Regardless of whether the recovered value was
off by 1 or by more, `P(R_{i+1}|R_i=False)` stays close to the same
depressed level, far below `P(R_{i+1}|R_i=True)`.**

**Secondary, exploratory observation (not the primary classification,
reported per §5's descriptive-diagnostic allowance): the stratification
test's *direction* is mixed and appears to track `m0_{i+1}` region.**
At `m0_{i+1}∈{9,10}` (the high-recovery transition zone), several cells
show `p_small < p_large` (larger error → *higher* subsequent recovery,
`z` as extreme as `-4.26`) — counterintuitive. At `m0_{i+1}=11` (deeper
in the cliff), the sign flips: `p_small > p_large` (larger error →
*lower* recovery, `z` up to `3.02`) — the intuitive direction. Given
`n_large` is thin in every cell (often just above the `n_min=100` floor;
`err_i>1` is a rare tail event throughout), this pattern is reported as
a genuinely interesting lead for a future contract, not as an
established directional effect — the frozen classification rests on
`A`, not on this secondary sign pattern.

**Interpretation:** error *magnitude* is not the missing variable —
whatever information `R_i` carries beyond `m0_{i+1}` (E18), it is
carried by the *fact* of failure, not by *how far* the recovered value
missed. A plausible reading, consistent with the deterministic exact
arithmetic downstream of REGEN (`exact_qsub`/`exact_rotc` don't treat a
"slightly wrong" input differently from a "very wrong" one — both are
simply wrong integers entering the same deterministic transform, and
`m0` bookkeeping increments identically regardless of the actual
magnitude of a value): **once corrupted, a state's downstream
recoverability may depend on qualitative properties of the corruption
(which component deviated, its sign, which op type was active at the
failing boundary) rather than the corruption's size.** This is a
hypothesis for a future, not-yet-authorized contract (§8), not
established here — E19 only rules *magnitude* out as the explanation,
it does not establish what the real explanation is.

**Evidence artifact:**
`results/sweeps/corrupted_state_sufficiency_sweep_frozen_v1_2026-08-23.json`,
sha256 `642496a317d9edae7cebde0b926d272e6d0115d4bedb87e344b6bc523c14f775`.
Driver: `photonics/run_photonic_corrupted_state_sufficiency_sweep.py`.
