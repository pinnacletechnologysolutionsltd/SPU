# Engineering Contract: Detector-Noise Boundary Sweep (E9)

**Date:** 2026-08-21
**Contract ID:** `contract_photonics_detector_boundary_2026-08-21.md`
**Status:** RESULT: FALSIFIED, FROZEN (2026-08-21). Full run complete,
reproducibility CONFIRMED (two independent 127-cell × 30,000-trial runs,
bit-identical — including a targeted empirical check that `cell()` is
actually deterministic run-to-run, not assumed; see §10.4), frozen copy
`results/sweeps/detector_boundary_sweep_frozen_v1_2026-08-21.json` (sha256
`1a3306a1…`), README entry added. The scaling-law consistency criterion
(§7) failed — see §10.3. Backend contract §3.3: REQUIRES REVISION, not yet
revised (flagged, not silently fixed — see the dated pointer added to
`contract_photonics_backend_2026-08-20.md` §3.3). Next investigation
(K-dependent/cascade-depth mechanism) and E10 (combined-axis): NOT
AUTHORIZED — separate contracts required, per John's explicit direction
2026-08-21 ("I would not do that yet... that's a hypothesis, not a finding
from E9").

**Roles:**
- **Spec Author:** GTP/DeepSeek (proposal — the detector axis is the binding
  constraint per E8, §3.3 of `contract_photonics_backend_2026-08-20.md`, and
  deserves a dedicated high-resolution sweep before being treated as a final
  spec number) + Claude (this document).
- **Halt-and-Flag Implementer:** pre-review for RNG/stream alignment with E8
  (reuse, not reimplementation), CI adequacy near the crossing, band-rejection
  confounds.
- **Integration Auditor:** reproducibility gates, hygiene, evidence freeze.

**Normative references (evidence base, not modified by this contract):**
- `contract_regen_isa_0x09_2026-08-20.md` — REGEN v1 architectural semantics
  (frozen; this experiment characterizes an implementation profile, it does
  not touch ISA semantics).
- `contract_photonics_backend_2026-08-20.md` §3.3 — the declared envelope
  (E8) this sweep refines. Cited numbers below (K\* table, σ_det ≲ 0.05/2^m)
  come from that frozen artifact.

---

## 1. Objective

E8's declared envelope (`results/sweeps/photonic_envelope_frozen_v1_2026-08-20.json`,
60 cells × 3 axes × 4 coarse levels) established that **detector noise is the
binding constraint** on the photonic backend's regeneration depth K — not
differential phase, not amplitude. But E8's detector axis only tested four
levels (`{0, 1e-4, 3e-4, 1e-3}`), and three of the five K values (K=4, 8, 16)
already read `K*(99.9%) = 0` at the *smallest nonzero* level tested. That
means **E8 never actually located the transition for the K values that
matter most** — it only knows the transition is somewhere below 1e-4 for
K≥4, and somewhere below 1.96e-4 for K=1 (per the contract's closed-form
estimate σ_det ≲ 0.05/2^m).

**This experiment's only job:** hold σ_φ = 0 and σ_amp = 0 (isolate the
detector axis exactly, per the Spec Author's explicit guidance — no
combined-axis effects yet), and densely map P_recover(σ_det) for each
K ∈ {1, 2, 4, 8, 16}, resolving the 99.9%, 99%, and 95% crossing points to
within one grid step. This turns "5.8e-7 @ K=16" from a closed-form estimate
into a measured number — and, per §2.1, tests whether the 2^-m scaling
mechanism behind that estimate actually holds at K=2, 4, 8 too, or was only
ever a two-point fit.

**Explicitly deferred (not this contract):** the combined-axis realistic
envelope (σ_φ, σ_amp, σ_det simultaneously) — GTP's proposed E10. That sweep
needs E9's actual crossing points as its center-of-grid inputs; drafting it
now would mean guessing at the grid, which is exactly the kind of premature
specification this project's contracts are supposed to avoid. See §9.

## 2. Definitions (locked, inherited from E8 — no reimplementation)

- **Backend, block generation, chain evaluation:** reuse
  `PhotonicQuadrayBackend`, `gen_block`, `cell` from
  `photonics/run_photonic_envelope_sweep.py` verbatim (import, do not copy).
  Same Quadray block construction (QLDI + ROTC/QSUB lattice-safe ops,
  band-rejection [1000, 30000]), same paired-arm evaluation (A = per-op
  REGEN, B = chain with one conditioned REGEN per block).
- **K:** ∈ {1, 2, 4, 8, 16}, same M_K operand scaling as E8
  (`{1:2000, 2:2000, 4:2000, 8:2000, 16:2000}`).
- **ΔT:** 2.0 K (E8's value; common-mode thermal is handled by the
  compensation law and is not the axis under test here).
- **Isolation (locked):** σ_φ = 0, σ_amp = 0 for every cell. Only σ_det
  varies. This is the Spec Author's explicit design constraint — a combined
  sweep answers a different, harder-to-interpret question.

### 2.1 Empirical vs. predicted crossing (the ratio test — reviewer addition)

Per Halt-and-Flag review of this draft (2026-08-21): the important result is
not "the measured points fit the closed-form estimate" (a claim about two
numbers) — it's whether the closed-form's underlying **scaling mechanism**
(σ_det ≲ 0.05/2^m, backend contract §3.3) actually governs recovery at every
K, not just the two K values it was fit to. Three quantities, kept
explicitly distinct throughout §6–§7:

- **σ\*_det(K)** — the *empirical* crossing: the largest grid σ_det at which
  measured P_recover_B(K, σ_det) ≥ 99.9% (reported as a **bracket**, §6 —
  never as a single interpolated number presented as exact).
- **m̄(K)** — the *measured* mean accumulated scale exponent for K-op
  blocks. **Not invented for this contract** — `cell()` already computes and
  returns it (`run_photonic_envelope_sweep.py:129`, field `mean_total_m`),
  because block generation (`gen_block`) is independent of the noise level
  applied afterward, so m̄(K) can be read directly from any of that K's 23
  cells (report the mean and spread across all 23 for a variance check —
  see the Halt-and-Flag note below).
- **σ_det,pred(K) = 0.05 / 2^m̄(K)** — the backend contract's own closed-form
  (§3.3), evaluated at the *measured* m̄(K) rather than an assumed or
  interpolated one. This is the same formula, not a new model.
- **R_K = σ\*_det(K) / σ_det,pred(K)** — the ratio. **R_K approximately
  constant across K=1,2,4,8,16 is the actual falsifiable claim.** Two points
  agreeing (K=1, K=16 — the only two the closed-form was fit to) is
  unfalsifiable by construction; five independent points agreeing is
  evidence the 2^-m scaling mechanism is real, not coincidental.

**Halt-and-Flag note (flag before running, do not silently assume):**
`gen_block`'s ROTC step only grows m on 3 of its 6 angles (the other 3 are
identity/permutation, denominator 1 — see backend contract §8, "ROTC thirds
are conditional"); QSUB always grows m by 1. Since `gen_block` picks
ROTC-vs-QSUB and the ROTC angle uniformly at random, **m̄(K) is itself a
random variable across the block population, not a deterministic function
of K.** Report its spread (std. dev. or IQR across the 23 cells at fixed K,
which should all draw from the same block-generation distribution) alongside
the mean — if the spread is wide relative to the log-grid spacing, R_K's
apparent constancy (or violation) could be an artifact of which blocks got
sampled, not the scaling law itself. This is exactly the kind of
"unhandled edge case" AGENTS.md's Halt-and-Flag role exists to catch before
implementation, not after.

## 3. Locked parameters — the dense detector grid

**Revised 2026-08-21 after the §8 smoke pass** (this is the smoke pass doing
its job, per §3's original "do not launch the full run blind" gate — not a
reopening of the design review). At `PHOTONIC_TRIALS=200`, the original
single 23-point grid (below) resolved K=1, 2, 4, 8 cleanly, but **K=16's
crossing sits below the grid's floor**: E8's frozen det=0 baseline gives
B=1.0000 exactly, while this grid's smallest nonzero point (1e-7) already
reads B=0.595 — a cliff the grid never captures the top of. Running the
full 30,000-trial sweep on the single grid would have produced 115 cells
with no usable K=16 bracket at any trial count, because the grid itself
doesn't reach low enough. Fix (John's call, 2026-08-21): split K=16 onto
its own finer, lower sub-grid rather than lowering the floor for all five K
(which would have wasted compute re-sampling K=1/2/4/8 territory that's
already well-bracketed).

E8 established two anchor points (§3.3 of the backend contract, Appendix
formula σ_det ≲ 0.05/2^m): K=1 → σ_det ≈ 1.96e-4, K=16 → σ_det ≈ 5.8e-7.
That's a ~340× span across five K values — a single linearly-spaced grid
cannot resolve all five crossings. The main grid is log-spaced, ~5 points
per decade, spanning the full range with margin on both ends:

```
DET_LEVELS = [
    1e-7, 1.5e-7, 2e-7, 3e-7, 5e-7, 7e-7,
    1e-6, 1.5e-6, 2e-6, 3e-6, 5e-6, 7e-6,
    1e-5, 1.5e-5, 2e-5, 3e-5, 5e-5, 7e-5,
    1e-4, 1.5e-4, 2e-4, 3e-4, 5e-4,
]
```

used for K ∈ {1, 2, 4, 8}. K=16 additionally gets a fine sub-grid **below**
the main grid's floor, with no overlap/duplication (the main grid's 1e-7–5e-4
points are still evaluated for K=16 too, since the smoke data shows the
cliff's *upper* edge is inside that range):

```
DET_LEVELS_K16_EXTRA = [
    1e-9, 1.5e-9, 2e-9, 3e-9, 5e-9, 7e-9,
    1e-8, 1.5e-8, 2e-8, 3e-8, 5e-8, 7e-8,
]
```

K=16's full grid = `DET_LEVELS_K16_EXTRA + DET_LEVELS` (12 + 23 = 35 points).
This is a **hypothesis about where the cliff is, not a confirmed bracket** —
the 200-trial smoke pass only established that the cliff is somewhere below
1e-7; §8 requires a targeted higher-trial-count smoke check across
`DET_LEVELS_K16_EXTRA` specifically before committing to the full run, in
case the true crossing is below 1e-9 too (see §8 step 1b, new).

(23 × 4 + 35 = **127 cells**, up from 115.)

| parameter | value |
|---|---|
| axis | det only; phi=0, amp=0 (locked) |
| K | {1, 2, 4, 8, 16} (E8's set) |
| det levels (K=1,2,4,8) | 23 log-spaced points, 1e-7 – 5e-4 |
| det levels (K=16) | 35 log-spaced points, 1e-9 – 5e-4 (split grid, above) |
| ΔT | 2.0 K |
| M_K (operand scaling) | {1:2000, 2:2000, 4:2000, 8:2000, 16:2000} (E8's) |
| band | [1000, 30000] (E8's) |
| seed | 13 |
| trials per cell | 30,000 (E8's count — reused for direct comparability; see §7's CI-adequacy precondition) |
| cells | 127 (measured: 200-trial smoke pass of the final split-grid script = 127 cells / 28.6s) |

**Compute budget (measured 2026-08-21, final split-grid design):** the
actual 127-cell script (`run_photonic_detector_boundary_sweep.py`, K=16
split grid included) ran in 28.6s at 200 trials/cell (100% CPU,
single-threaded). Extrapolating linearly to 30,000 trials/cell (150×):
**≈ 71.4 minutes** for the full run. (An earlier estimate of ≈65 min,
extrapolated from a K=16-only partial measurement before the final script
existed, is superseded by this direct measurement of the actual script.)

## 4. Procedure per cell (det_level, K)

Identical to E8's `cell()` function (`run_photonic_envelope_sweep.py:90-130`),
called with `axis="det", level=det_level`. No new evaluation logic — this
contract's only implementation content is the grid and the driver loop.

## 5. New script (additive, Lithic ≤ 150 lines)

`photonics/run_photonic_detector_boundary_sweep.py` — imports `gen_block`,
`cell`, `M_K`, `BAND`, `SEED`, `KS` from `run_photonic_envelope_sweep`
(same directory; add `photonics/` to `sys.path`, matching the `ROOT`-relative
import pattern already used by every other `run_photonic_*.py` script — see
`docs/SESSION_HANDOVER_2026-08-20.md` §2 for the convention this repo
settled on 2026-08-21). Defines only: `DET_LEVELS` (§3), a `main()` loop
over `(level, K)` pairs calling the imported `cell("det", level, K,
n_trials)`, and canonical incremental JSON output (same discipline as E1–E8:
write after every cell, so an interrupted run keeps completed cells).

**Do NOT** duplicate `gen_block`/`cell`/`PhotonicQuadrayBackend` logic into
the new file — that would violate both the Lithic budget and the "same
tested implementation" requirement in §2.

## 6. Metrics & outputs

- P_recover_A(K, σ_det), P_recover_B(K, σ_det) with 95% CI, for all 115
  cells — the primary artifact.
- **Crossing table (derived, post-hoc) — brackets are the reported quantity,
  not a false-precision number.** For each K and each of {99.9%, 99%, 95%}:
  report the two adjacent grid points that bracket the crossing
  (`[σ_lo, σ_hi]`, with their measured P_recover_B and CI). An interpolated
  point estimate MAY be included as a secondary, clearly-labeled convenience
  value — it is never the primary reported result, and must never be quoted
  on its own in any later document (e.g. an updated backend contract) without
  its bracket alongside it.
- **The ratio table (§2.1) — the primary scientific result of this
  contract:** for each K, σ\*_det(K) (as a bracket), m̄(K) (mean ± spread
  across the 23 same-K cells), σ_det,pred(K) = 0.05/2^m̄(K), and R_K. Report
  whether R_K is approximately constant across the five K values (§7) — this
  is the claim the experiment exists to test, not the individual crossings.
- Output: canonical JSON (`results/sweeps/detector_boundary_sweep.json`),
  frozen copy with sha256, README entry — same discipline as E1–E8.

## 7. Falsification criteria (non-vacuous)

- **Monotonicity:** P_recover_B(K, σ_det) must be non-increasing in σ_det
  for fixed K, and the crossing σ_det must be non-increasing in K (matches
  the "tighter detector budget at higher K" mechanism from E8 — a violation
  means the mechanism is misunderstood, not just imprecisely measured).
- **Scaling-law consistency (the primary falsification test, §2.1):** R_K
  must be approximately constant across K=1, 2, 4, 8, 16 — concretely, all
  five R_K values must fall within a common factor-of-2 band (e.g.
  max(R_K)/min(R_K) ≤ 2). This is strictly stronger than checking K=1 and
  K=16 alone (those two are not independent evidence — the closed-form was
  fit to them); K=2, 4, 8 are the actual test. **If R_K is not
  approximately constant, the 2^-m scaling mechanism in backend contract
  §3.3 does not generalize** — the two-anchor formula was a coincidental fit,
  and §3.3 must be corrected or re-scoped to state it is only validated at
  K=1 and K=16, not as a general law (HALT, do not silently keep the
  general-law wording in the repo).
- **CI-adequacy is a firm precondition, not a post-hoc escalation:** a
  crossing bracket is only reportable if the 95% CI at both bracketing grid
  points is tight enough that the bracket itself (not just a point estimate)
  is meaningful — i.e., the CIs of the two bracketing cells must not
  overlap the 99.9%/99%/95% line simultaneously in a way that makes "which
  side of the line" ambiguous. If they do, rerun that cell at a higher trial
  count (e.g. 100,000) before reporting any bracket at that K. This is a
  real possibility at K=16 where per-cell trial cost may already be at the
  edge of the compute budget flagged in §3 — flag if it forces a scope
  renegotiation.
- Saturation/band-rejection must never be scored as success — inherited
  from E8's `gen_block` band filter; no changes to that logic in this
  contract.

## 8. Verification gates (implementer/auditor)

```bash
# 1. Smoke pass — confirm the harness runs and estimate wall-clock cost.
#    DONE 2026-08-21: 115 cells (original single-grid design) / 23.7s at
#    200 trials/cell. Result: K=1,2,4,8 well-bracketed; K=16's crossing is
#    below the grid floor -> split-grid revision in SS3.
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_detector_boundary_sweep.py

# 1b. Targeted K=16 sub-grid smoke check (NEW, required before the full run) —
#     confirm DET_LEVELS_K16_EXTRA (1e-9-7e-8) actually brackets the cliff
#     the SS1 smoke pass found below 1e-7; if B-recovery is still < 1.0 at
#     the grid's new floor (1e-9), the sub-grid must extend further and this
#     step repeats. Use more trials than SS1 (e.g. 2000) since K=16's ~58%
#     rejection rate makes 200-trial estimates noisy at this K specifically.

# 2. Full run (only after step 1b confirms the K=16 sub-grid actually
#    brackets the cliff, and the SS3 compute-budget estimate is re-checked
#    against the K=16 sub-grid's rejection-rate cost)
.venv/bin/python3 photonics/run_photonic_detector_boundary_sweep.py

# 3. Reproducibility: two full runs, bit-identical (timestamps excluded) —
#    same discipline as E1-E8, verified with the strip-and-compare pattern
#    from contract_regen_isa_0x09_2026-08-20.md §4.

# 4. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (flagged 2026-08-21, see session cleanup):** always use
`.venv/bin/python3`, never bare `python3` — the latter lacks numpy in this
environment and silently falls back to a different (still internally
self-consistent, but non-matching) RNG stream, which will make the
reproducibility gate in step 3 fail for the wrong reason.

## 9. Non-Goals

- **No combined-axis sweep (E10)** — deferred until this contract's crossing
  table exists to seed E10's grid design. Drafting E10 now would be
  specifying a sweep around numbers we don't have yet.
- **No change to the E8 declared envelope, K\* table, or backend contract
  wording** — this experiment refines the detector row's precision; it does
  not supersede E8 until its results are reviewed and a decision is made to
  update `contract_photonics_backend_2026-08-20.md` §3.3. That update, if
  warranted, is a separate, explicit edit — not an automatic consequence of
  running this sweep.
- **No hardware component selection** (receiver architecture, ADC part
  numbers) — this is still a software model sweep; "hardware component
  requirements" (GTP's stated eventual goal) is downstream of E9 **and**
  E10, not this contract.
- **No new noise mechanisms** — only σ_det varies; σ_φ and σ_amp stay at
  the E8 evaluation machinery's existing defaults (locked to 0 in §2).

---

## 10. Results (2026-08-21) — full run, 127 cells × 30,000 trials

**Status: RUN COMPLETE.** `results/sweeps/detector_boundary_sweep.json`,
sha256 `1a3306a1…`. Not yet frozen with a `_frozen_v1_` copy or README entry
(§8 step 3, reproducibility rerun, not yet performed — see below).

### 10.1 Crossing brackets (all three thresholds; m̄(K) shown once per K)

| K | m̄(K) | 99.9% bracket | B | 99% bracket | B | 95% bracket | B |
|---|---|---|---|---|---|---|---|
| 1 | 7.992 | [5.0e-5, 7.0e-5] | .9995→.9800 | [5.0e-5, 7.0e-5] | .9995→.9800 | [7.0e-5, 1.0e-4] | .9800→.8136 |
| 2 | 8.000 | [5.0e-5, 7.0e-5] | .9991→.9598 | [5.0e-5, 7.0e-5] | .9991→.9598 | [7.0e-5, 1.0e-4] | .9598→.6731 |
| 4 | 9.979 | [1.0e-5, 1.5e-5] | 1.0000→.9956 | [1.5e-5, 2.0e-5] | .9956→.9449 | [1.5e-5, 2.0e-5] | .9956→.9449 |
| 8 | 13.212 | [7.0e-7, 1.0e-6] | 1.0000→.9941 | [1.0e-6, 1.5e-6] | .9941→.8954 | [1.0e-6, 1.5e-6] | .9941→.8954 |
| 16 | 16.394 | [3.0e-9, 5.0e-9] | .9999→.9839 | [3.0e-9, 5.0e-9] | .9999→.9839 | [5.0e-9, 7.0e-9] | .9839→.9252 |

All brackets are single adjacent-grid-point pairs (CI-adequacy precondition
met, §7 — no bracket spans more than one grid step, and the 95% CIs at each
bracketing point are tight enough that "which side of the threshold" is
unambiguous at every K). Note 99.9%/99% and 99%/95% coincidences are not a
consistent pattern across K (K=1,2,16 share 99.9%/99%; K=4,8 share 99%/95%
instead) — a grid-resolution artifact of where the log-spaced points happen
to fall, not a real feature of the underlying curve.

### 10.2 The ratio table (§2.1 — the primary result)

σ_det,pred(K) = 0.05/2^m̄(K), evaluated at the *measured* m̄(K) (std. dev.
of m̄ across each K's cells: 0.000 — `gen_block`'s ROTC/QSUB angle mix is
apparently far less variable in practice than the §2.1 Halt-and-Flag note
worried about, at this M_K=2000/band=[1000,30000] operating point).
σ\*_det(K) taken as the geometric mean of each bracket (a point estimate for
this table only — the bracket itself, §10.1, is the primary reported
crossing per §6):

| K | σ\*_det(K) (bracket midpoint) | σ_det,pred(K) | R_K |
|---|---|---|---|
| 1 | 5.92e-5 | 1.96e-4 | 0.301 |
| 2 | 5.92e-5 | 1.95e-4 | 0.303 |
| 4 | 1.22e-5 | 4.96e-5 | 0.247 |
| 8 | 8.37e-7 | 5.27e-6 | 0.159 |
| 16 | 3.87e-9 | 5.81e-7 | 0.0067 |

**max(R_K)/min(R_K) = 0.303/0.0067 ≈ 45.4.**

### 10.3 Falsification verdict (§7)

- **Monotonicity: PASS.** Crossing σ_det is non-increasing in K at every
  step, and R_K itself is non-increasing in K — both hold cleanly.
- **Scaling-law consistency: FAIL.** The §7 threshold is
  max(R_K)/min(R_K) ≤ 2; the measured value is ≈45. **The σ_det ≲ 0.05/2^m
  closed-form in `contract_photonics_backend_2026-08-20.md` §3.3 does not
  generalize across K.** Two structural observations, not yet explained:
  - Even at K=1 (one of the formula's own two fit points), R_1 = 0.301, not
    ≈1 — the empirical 99.9% crossing is ~3.3× tighter than the formula
    predicts. The formula may have been derived or fit differently than a
    direct 99.9%-crossing measurement (E8's own grid only tested
    `{0, 1e-4, 3e-4, 1e-3}`, coarse enough that a 5.9e-5 crossing would have
    read as "K\*(99.9%)=0 at the smallest level tested," not located).
  - R_K does not decay smoothly with m̄(K) either: the K=8→K=16 step drops
    R by ~24× over Δm̄≈3.2, versus ~1.5–1.9× per similar Δm̄ step
    earlier in the table. Something specific to K=16 (16 sequential chain
    operations) degrades performance beyond what the scale-exponent
    bookkeeping alone predicts — a chain-length effect, not (or not only) a
    scale-exponent effect. Not investigated further under this contract
    (§9 non-goals — no new noise mechanisms).
- **CI-adequacy: PASS** — see §10.1.

**Per §7's own instruction ("HALT, do not silently keep the general-law
wording in the repo"): `contract_photonics_backend_2026-08-20.md` §3.3
currently states `σ_det ≲ 0.05/2^m` without qualification. This is now
falsified as a general law and needs Spec Author review before any further
edit — not silently corrected by this document.** Flagged, not fixed.

### 10.4 Reproducibility — CONFIRMED (2026-08-21)

Per John's explicit direction: the interpretation of E9 was frozen (§10.1–
§10.3) and the backend contract flagged (not silently edited) *before* the
reproducibility rerun was authorized and launched — the rerun was not an
automatic continuation of the original hypothesis.

**What counts as reproducible for a falsification — checked, not assumed:**
confirmed empirically (not just read from the code) that `cell()` is fully
deterministic: two calls with identical `(axis, level, K, n_trials)`
produce bit-identical results, because `master = make_master_rng(SEED)` is
freshly constructed per call and `trial_rng(master, trial)` is keyed by the
trial *index* (incremented every attempt, accepted or rejected), not by the
accepted count — so the raw trial sequence is identical regardless of run.
**The standard E1–E8 bit-identical strip-and-compare test applies directly;
no looser order-of-magnitude fallback was needed.**

**Result:** two independent full 127-cell × 30,000-trial runs (~63 min
each) produced **bit-identical output dicts** (`a == b`, no stripping
required — this script emits no timestamp field). Frozen:
`results/sweeps/detector_boundary_sweep_frozen_v1_2026-08-21.json`, sha256
`1a3306a186193f1bdfda179a3fc19f8f1182905d56a2e8ef7e979b3870f1afda`. README
entry added (`results/sweeps/README.md`). **The falsification in §10.3 is
not a Monte Carlo fluke — it reproduces exactly.**

E10 (combined-axis) and the K-dependent/cascade-depth mechanism
investigation (§10.3's second observation) remain explicitly **not
authorized**; separate contracts, separate decisions.
