# Engineering Contract: Regeneration-Placement M=2 Extension (E14)

**Date:** 2026-08-22
**Contract ID:** `contract_photonics_regen_placement_m2_2026-08-22.md`
**Status:** RESULT — OUTCOME B, DIMINISHING RETURNS, FROZEN (2026-08-22).
Full run complete, reproducibility CONFIRMED (two independent runs,
bit-identical). M=2 improves on M=4 by only 2.00× at 99.9% (vs. the
31.62× seen going M=8→M=4) — the improvement-per-halving trend peaks at
M=4 and sharply reverses, not a smooth saturation. §4b's lane-attribution
instrumentation (100% of ~3,769 failed trials, both M=2 and the M=4
matched control) found **zero** lane-1 involvement, ruling out the
lane-1-exposure hypothesis by direct measurement — leaving M=2's
QLDI-only first REGEN boundary as the surviving, untested candidate
explanation. M=2 closes 69.4% of the full log-scale gap (up from M=4's
62.0%); 17.1× remains. See §9.

**Roles:**
- **Spec Author:** Claude, from E13's result and John/GTP's explicit
  post-review framing: "Does the M=4→M=2 improvement continue the E13
  trend, saturate, or reverse because the first two-op QLDI-only
  regeneration and increased whole-state re-entry introduce a competing
  effect?"
- **Halt-and-Flag Implementer:** pre-review of the lane-attribution
  extension (§4b) before running anything — it was proposed beyond what
  was explicitly requested and has now been **approved** (John,
  2026-08-22): included, not optional.
- **Integration Auditor:** reproducibility gates, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_regen_placement_2026-08-22.md` (E13) — the frozen
  M=16/8/4 curve this contract extends, **not reruns**. E13's exact
  numbers: M=16→M8: 10.00× (1.000 dec); M=8→M=4: 31.62× (1.500 dec);
  remaining gap M=4→native-K=8: 34.2× (1.533 dec). The acceleration
  (1.0 dec then 1.5 dec, not constant-per-halving) is the pattern this
  contract tests for continuation.
- `contract_photonics_detector_boundary_2026-08-21.md` (E9) — native K=8
  reference crossing (~5.92e-5 geomean), unchanged, not rerun.

---

## 1. Objective

**Does the M=4→M=2 improvement continue E13's accelerating trend,
saturate, or reverse — specifically because M=2's first regeneration
boundary occurs before any QSUB/ROTC computation (right after the two
QLDIs), a structurally different boundary than M=4's (which has two
combine ops before its first REGEN)?**

Four pre-registered outcomes (not decided after seeing data):

```
A. Continued acceleration — M=2 dramatically approaches or exceeds
   K=8's native crossing (~5.92e-5).
B. Diminishing returns — M=2 improves over M=4, but by less than the
   trend's own acceleration would suggest (i.e., less than ~31.62×
   again).
C. Saturation — M=2 ≈ M=4, no further meaningful improvement.
D. Reversal — M=2 performs WORSE than M=4.
```

**D is the scientifically interesting failure mode** — it would make the
lane-1-exposure hypothesis (flagged in E13 §4, unmeasured there) directly
visible for the first time, since M=2 doubles the REGEN-boundary count
(8, vs M=4's 4) and gives lane 1 twice as many independent exposures.

**Pre-registered interpretation branch, stated before running (per
explicit instruction — do not construct this after seeing the data): if
M=2 underperforms M=4, that must NOT be read as "regeneration frequency
has an optimum at M=4."** Two structurally distinct candidate causes exist
and must be reported separately, not collapsed into one verdict:
(i) the lane-1-exposure effect (more REGEN boundaries, more independent
detector-noise draws on the static lane), or (ii) something specific to
regenerating freshly-loaded, not-yet-computed operands (M=2's first
boundary has no combine-op history behind it at all — a qualitatively
different state than any boundary tested in E13).

**Explicitly out of scope:** M=1 (already the established Arm-A limit,
not new territory — mixing it in would conflate an existing reference
with this new intermediate point); rerunning M=16/8/4 (E13's frozen curve
is the comparison baseline, reused as-is); any claim beyond what the M=2
curve shows relative to that frozen baseline.

## 2. Objective grounding

`run_chain_periodic_noisy` (`photonics/run_photonic_regen_placement_sweep.py`,
built and verified in E13) already scores **every group's** REGEN against
that group's own exact oracle state, not just the final one — control #1
(strict per-group noiseless correctness, not just "final state matches")
is satisfied by the existing harness's design, not a new requirement to
build; §4a's job is to verify this explicitly for M=2's specific
structure (untested there), not to change the scoring logic.

**M=2's group structure (`gen_block(rng,16)`'s flat 16-op sequence, ops
split at multiples of 2):** group 1 = ops[0:2] = the two QLDIs only (zero
combine ops — confirmed in E13 §3 as the reason M=2 was originally
excluded); groups 2-8 = seven groups of 2 pure-combine ops each
(14 combines / 2 = 7). **Total: 8 groups, 8 REGEN boundaries** — exactly
double M=4's 4.

## 3. Locked parameters

| condition | source |
|---|---|
| M=2 | **new — this contract's only measured condition** |
| M=4, M=8, M=16 | **E13's frozen curve, reused, NOT rerun** — `results/sweeps/regen_placement_sweep_frozen_v1_2026-08-22.json` |

| parameter | value |
|---|---|
| K (logical length) | 16 (unchanged) |
| block generator | `gen_block` (E9/E13's, unmodified) |
| M_K | 2000 (E9/E13's K=16 value) |
| band | [1000, 30000] (unchanged) |
| seed | 13 |
| det levels | **not fixed in advance — wide exploratory smoke pass required
  on BOTH sides of M=4's frozen crossing (~1.73e-6).** Outcome A (M=2 near
  or beyond K=8's ~5.92e-5) and outcome D (M=2 below M=4's own territory)
  are both live possibilities per §1 — the smoke grid must be wide enough
  to catch either without assuming a direction, same discipline as E9's
  K=16 grid-floor lesson. Suggested starting range: 1e-7 to 1e-3 (spans
  from well below M=4's crossing to well above K=8's native crossing). |
| trials per cell | 30,000 (E9–E13's count) |

## 4. New code — Halt-and-Flag review required before running

**4a. Strict M=2 noiseless verification (control #1, John's explicit
requirement — not just "reproduces the oracle," every group checked):**
run `run_chain_periodic_noisy(pb, block, M=2, sigma_det=0, rng)` for
≥500 trials, and **separately** verify, for each of the 8 groups per
trial, that group's `rec == qr` snapshot at that boundary — not just the
function's aggregate `all_ok` return value. This requires a small
diagnostic variant (or an inline instrumentation pass) that surfaces
per-group pass/fail, not just the whole-trial boolean the existing
function returns. Must be 100% at every group, every trial, before
proceeding.

**4b. Lane-attribution instrumentation (APPROVED, John 2026-08-22 —
included, not optional):** extend `run_chain_periodic_noisy` (or a
variant) to track, per trial, whether any failing group's mismatch was
attributable to lane 0's components, lane 1's, or both (`rec[0] != qr[0]`
vs `rec[1] != qr[1]`, checked at every REGEN boundary, accumulated across
the trial). Report, per (M, det_level) cell: recovery (as before), plus
the fraction of *failed* trials attributable to lane 0 only / lane 1 only
/ both. Makes outcome D's two candidate causes (§1) empirically
distinguishable rather than inferred from curve shape alone. Run this
instrumentation for M=2 and, as a **matched control (not a full rerun)**,
re-derive it for a modest sample of M=4 trials at a comparable noise
level (not the full 30,000×12 grid — a few thousand trials at one or two
levels near M=4's own crossing, enough to establish whether lane-1
attributable failures are already-negligible-there for contrast).

**Halt-and-Flag pre-review items:**
- Confirm the lane-attribution accounting doesn't change `all_ok`'s
  existing semantics (it's additive instrumentation, not a scoring
  change) — the recovery curve itself must be identical to what an
  unmodified `run_chain_periodic_noisy` would produce, checked by
  comparing a sample against the unmodified function's output before
  trusting the instrumented version for the full run.
- Rejection-population invariant (E9/E12/E13's established check):
  M=2's rejection rate must match `gen_block(rng,16)`'s own baseline
  exactly, same as E13's M=4/8/16 all did.

## 5. Metrics & outputs

- P_recover(σ_det) for M=2, the full curve — the primary artifact,
  reported alongside (not replacing) E13's frozen M=4/8/16 curve for
  direct visual/numeric comparison.
- Crossing bracket (99.9%, 99%, 95%) for M=2.
- **The comparison (the primary result):** M=2's geomean crossing vs
  M=4's frozen 1.732e-6 — expressed as a ratio and in decades, exactly
  the format E13 used, so the four-point sequence (16→8→4→2) reads as one
  continuous table.
- If §4b is approved and run: the lane-0/lane-1/both failure-attribution
  breakdown for M=2, with the M=4 matched-control sample for contrast.
- Output: canonical JSON (`results/sweeps/regen_placement_m2_sweep.json`),
  frozen copy with sha256, README entry — same discipline as E1–E13.

## 6. Falsification criteria (non-vacuous)

- **Strict per-group noiseless gate (§4a) must pass — 100% at every
  group, every trial** — before any noisy interpretation.
- **Rejection-population invariant must pass.**
- **Outcome classification (§1's four-way taxonomy) — report which one
  occurred, do not force a binary confirm/reject:**
  - **A (continued acceleration):** M=2's crossing improvement over M=4
    is ≥31.62× (matching or exceeding E13's own M=8→M=4 acceleration) —
    the trend continues or strengthens.
  - **B (diminishing returns):** M=2 improves over M=4, but by less than
    31.62× — report the actual factor; this is evidence the acceleration
    itself is not indefinite, informative in its own right.
  - **C (saturation):** M=2's crossing is statistically indistinguishable
    from M=4's — report as cleanly as E11/E12's rule-outs.
  - **D (reversal):** M=2 performs measurably worse than M=4. **Do not
    conclude "regeneration has an optimum at M=4."** Report §4b's direct
    lane-attribution measurement — which candidate cause (lane-1 exposure
    vs. regenerating not-yet-computed operands, §1) the data actually
    supports, not just both named as open possibilities.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0. Strict per-group noiseless gate (SS4a): M=2, >=500 trials, EVERY
#    group at EVERY trial checked individually against its own oracle
#    snapshot, not just the whole-trial aggregate.

# 0b. Rejection-population invariant: M=2's rejection matches
#     gen_block(rng,16)'s own baseline exactly.

# 0c. Lane-attribution instrumentation validation (SS4b): confirm the
#     instrumented scorer produces an IDENTICAL recovery curve to the
#     unmodified run_chain_periodic_noisy on a sample, before trusting
#     it for the full run.

# 1. Wide exploratory smoke pass -- locate M=2's crossing region without
#    assuming a direction (SS3). Lock the grid from this pass; do not
#    move points afterward regardless of what the full run shows.
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_regen_placement_m2_sweep.py

# 2. Full run (only after step 1 confirms grid coverage on both sides of
#    M=4's frozen crossing)
.venv/bin/python3 photonics/run_photonic_regen_placement_m2_sweep.py

# 3. Reproducibility: two full runs, bit-identical -- checked empirically
#    first (E9/E11/E12/E13 lesson), not assumed.

# 4. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No M=1** — already the established Arm-A limit; not part of this
  contract's intermediate-frequency sequence.
- **No rerunning M=16/8/4** — E13's frozen curve is reused as-is; if
  reproducibility of THIS contract's own M=2 result is ever in doubt,
  that's a two-run bit-identical check on M=2 alone, not a re-verification
  of E13.
- **No further mechanism speculation beyond §1's two pre-registered
  candidates** if outcome D occurs — a genuinely new hypothesis (a third
  candidate cause) is a separate, later, explicitly-authorized contract,
  not something to construct inside this one's interpretation.
- **No tuning M below 2** — M=1 is Arm A (out of scope, above); there is
  no M=0 in this architecture's terms.
- **No E10 (combined-axis)** — still deferred behind understanding K=16.

## 9. Results (2026-08-22) — full run, 16 cells × 30,000 trials, CONFIRMED

**Status: OUTCOME B — DIMINISHING RETURNS.** Reproducibility CONFIRMED:
two independent full runs, bit-identical.
`results/sweeps/regen_placement_m2_sweep_frozen_v1_2026-08-22.json`, sha256
`90e1bf35…`.

### 9.1 Gates passed (per §7)

- **Gate 0 (strict per-group noiseless):** 500/500 trials, all 8 groups
  per trial individually correct, exact independent-oracle match.
- **Gate 0b (rejection invariant):** 0.5504, identical to M=16/8/4 and
  `gen_block(rng,16)`'s own baseline.
- **Gate 0c (instrumentation validation):** the lane-attribution-
  instrumented scorer produced identical recovery to the unmodified
  `run_chain_periodic_noisy` at every level checked.

### 9.2 The crossing — precise, not the smoke estimate

| threshold | bracket | geomean | ratio to M=4 (1.732e-6) | decades |
|---|---|---|---|---|
| 99.9% | [3.0e-6, 4.0e-6] | 3.464e-6 | **2.00×** | 0.301 |
| 99% | [5.0e-6, 7.0e-6] | 5.916e-6 | 3.42× | 0.534 |
| 95% | [7.0e-6, 1.0e-5] | 8.367e-6 | 4.83× | 0.684 |

**At the 99.9% threshold used throughout this investigation, M=2 improves
on M=4 by only 2.00× — far short of the 31.62× seen going from M=8 to
M=4.** The full recovery curve (all 16 grid points) is monotonic within
itself (no crossovers), CI-tight (n=30,000 throughout), and cleanly
resolved — this is not a sampling artifact.

### 9.3 The improvement-per-halving sequence reverses direction

```
M=16 → M=8:  1.000 decades (10.00x)
M=8  → M=4:  1.500 decades (31.62x)   <- peak
M=4  → M=2:  0.301 decades (2.00x)    <- sharp reversal
```

The trend does not merely fail to continue accelerating — it **peaks at
M=4 and then collapses**, landing below even the first step's magnitude.
This is a structurally distinct signature from simple saturation (which
would show a smooth flattening, not a sharp reversal after a peak).

### 9.4 Lane-attribution result (§4b) — cleanly rules out one candidate

Across 6 cells (M=2 at 4 levels near and past its crossing, M=4 matched
control at 2 levels near its own crossing — E13's [1e-6,3e-6] bracket),
5,000 trials each, ~3,769 total failed trials analyzed:

**100% of failures at both M=2 and M=4 are attributable to lane 0 only.
Zero lane-1-only failures. Zero "both" failures.** This holds despite
M=2 having double M=4's REGEN-boundary count (8 vs 4) — if lane-1
exposure frequency were a meaningful failure contributor, it should show
up more at M=2 than M=4; it shows up at neither.

**The lane-1-exposure hypothesis (E13 §4's flagged concern, one of §1's
two pre-registered candidates) is now ruled out by direct measurement,
not inference.** This was the more mechanistically "boring" candidate;
its elimination sharpens the remaining explanation.

### 9.5 Interpretation — the QLDI-only-first-boundary candidate is what remains

With lane-1 exposure eliminated, the surviving pre-registered candidate
(§1) is: **something specific to M=2's first REGEN boundary occurring
immediately after the two QLDIs, before any QSUB/ROTC computation has
happened.** This is the one structural feature that uniquely
distinguishes M=2 from M=4/8/16 (all of which have at least one combine
op — M=4 has two — before their first REGEN boundary).

**This contract does not prove that mechanism directly** — it establishes
the deceleration is real, reproducible, and not explained by the
alternative (lane-1), leaving the QLDI-only-boundary explanation as the
surviving candidate rather than a confirmed cause. Testing it directly
(e.g., a variant M=2 grouping that defers the first REGEN until after at
least one combine op) is a natural, separately-authorized follow-on, not
undertaken here per §8's scope discipline.

### 9.6 Updated gap accounting (four-point sequence, 16→8→4→2)

```
M=16 (5.48e-9) ──1.0dec──> M=8 (5.48e-8) ──1.5dec──> M=4 (1.73e-6) ──0.3dec──> M=2 (3.46e-6)
                                                                          |
                                                            remaining: 1.232 dec (17.1x)
                                                                          v
                                                                 native K=8 (5.92e-5)
```

**M=2 closes 69.4% of the full 4.033-decade gap** (up from M=4's 62.0%)
— genuine additional progress, but the *marginal* gain from this last
halving (7.4 percentage points) is far smaller than the marginal gain
from the M=8→M=4 halving (which alone closed 37.2 percentage points).
**A 17.1× gap remains** between M=2 (the most frequent regeneration
tested across E13+E14) and native K=8.

### 9.7 What's preserved as evidence

- The full 16-point recovery curve for M=2, alongside E13's frozen
  M=16/8/4 curve — the complete four-point sequence, not just crossings.
- The lane-attribution breakdown (§9.4): 6 cells, ~3,769 failed trials,
  zero lane-1 involvement at either M=2 or the M=4 matched control.
- Code: `run_chain_periodic_noisy_diag`, `cell_lane_attrib`, both in
  `photonics/run_photonic_regen_placement_m2_sweep.py`, verified identical
  to the unmodified scorer (§9.1 gate 0c) before being trusted.

### 9.8 Next (not authorized)

Testing the QLDI-only-first-boundary hypothesis directly (a variant
grouping, or M=2 with the first REGEN deferred) is the natural next step
— a new, separately-authorized contract, not an extension of this one.
The remaining 17.1× gap at M=2 is now the open question, narrower than
E13's original 34.2× but not closed. M=1 (Arm A) remains the separately-
established endpoint, unchanged.
