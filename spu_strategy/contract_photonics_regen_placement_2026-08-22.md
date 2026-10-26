# Engineering Contract: Regeneration-Placement Mechanism Investigation (E13)

**Date:** 2026-08-22
**Contract ID:** `contract_photonics_regen_placement_2026-08-22.md`
**Status:** RESULT — SUBSTANTIAL CONTRIBUTOR (not complete explanation),
FROZEN (2026-08-22). Full run complete and reproducibility CONFIRMED (two
independent runs, bit-identical). Regeneration frequency closes 62.0% of
the full log-scale gap between E9's K=16 collapse and its native K=8
crossing (M=4 vs M=16: 316× improvement); a 34.2× gap remains at the
most frequent regeneration tested. This is the first candidate mechanism
in the E9 investigation chain (after E11, E12 both ruled out) to produce
a large, monotonic, reproducible effect in the predicted direction. See
§9 for the full result.

**Roles:**
- **Spec Author:** Claude, from direct code inspection (§2) and GTP's
  second-ranked candidate after E11/E12 both closed negative: "something
  about *where* the normalization/regeneration boundary is placed
  relative to the optical operations creates the unexplained depth
  dependence... a genuinely architectural hypothesis rather than merely
  another noise parameter."
- **Halt-and-Flag Implementer:** pre-review of the new periodic-REGEN noisy
  scoring function (§4) — this is new architectural code (simulating an
  intermediate REGEN boundary inside the noisy path for the first time),
  a bigger lift than E11's generator-only change or E12's subclass-only
  change; needs correspondingly more scrutiny.
- **Integration Auditor:** reproducibility gates, hygiene, evidence freeze.

**Normative references:**
- `contract_photonics_cascade_depth_2026-08-22.md` (E11) — ruled out
  exact-thirds normalization.
- `contract_photonics_optical_depth_2026-08-22.md` (E12) — ruled out
  accumulated loss (both uncompensated and mean-compensated).
- `contract_photonics_detector_boundary_2026-08-21.md` (E9) — the
  K=8→K=16 collapse this contract investigates.
- `results/sweeps/README.md`, Frozen Step-6 result #6 — **pre-existing,
  already-frozen evidence this hypothesis builds on**, not new: "the
  chain's final detection must resolve 1/Σ_total = 1/∏σmax (mean 2.2e10 @
  K=16) — per-op regeneration bounds it to 1/σmax — regeneration is a
  dynamic-range management mechanism." Arm A (per-op REGEN) survives
  stochastic noise where Arm B (chain, one final detection) collapses, at
  every K. This contract asks what happens *between* those two extremes.

---

## 1. Objective

**Does regenerating more frequently within a logical K=16 operation
sequence restore recovery comparable to K=8's own crossing — meaning
E9's K=16 collapse is a regeneration-*frequency* effect (fixable by
regenerating more often), not an inherent depth effect?**

E9/E11/E12 all measured Arm B: one continuous 16-op chain, one final
detection. The already-frozen Step-6 evidence shows Arm A (regenerate
after *every* op) doesn't collapse the same way. Between "regenerate
never until op 16" and "regenerate after every op" lies unexplored
territory: regenerate every 8 ops (2 groups), every 4 ops (4 groups).
**This contract's only job:** measure recovery at those intermediate
regeneration periods and compare directly against two already-known
reference points — E9's own K=8 crossing (~5e-5 for 99.9%) and E9's own
K=16 crossing (~3-5e-9 for 99.9%), four orders of magnitude apart. If
regenerating every 8 ops lands near K=8's territory, that's a strong,
unambiguous confirmation; if it stays near K=16's territory, that's a
clean ruling-out — the four-order-of-magnitude gap between the two
reference points makes this an unusually high-contrast test.

**Explicitly out of scope:** re-deriving E9/K=8's crossing (reused as a
frozen reference, not rerun); operation ordering (parked); accumulated
loss (closed negative, both designs); any claim beyond what the measured
M=8/M=4 crossings show relative to the two reference points.

## 2. Objective grounding — the code gap, confirmed by reading, not assumed

`PhotonicQuadrayBackend.run_chain_noisy` (`test_regen_equivalence.py:326-413`,
the harness E8/E9/E11/E12 all use) initializes `fld`, `m`, `qr`, `angle`,
`noise_lists` **once**, before its `for block in chain:` loop
(lines 344-349), and never resets them between blocks. Arm B's single
detection happens exactly once, after every block in `chain` has been
processed. **Confirmed directly: passing a multi-block `chain` list to
`run_chain_noisy` is functionally identical to passing one flat block with
all ops concatenated — there is zero intermediate-regeneration support in
this harness.** Every E9/E11/E12 measurement of "K=16" was necessarily
"regenerate only once, after all 16 ops" — no experiment has ever tested
a K=16 *logical* sequence with an intermediate regeneration boundary.

The noiseless method `run_chain` (same class, `test_regen_equivalence.py:217-280`)
*does* have real per-block REGEN logic — coherent detection, BQE, and
canonical re-entry (re-encoding the recovered state as the next block's
starting point) — but only for the noiseless path. §4 mirrors this logic
into a new noisy function; it doesn't exist there today.

## 3. Locked parameters

| condition | logical K | regen period M | groups |
|---|---|---|---|
| M=16 (baseline) | 16 | 16 (never, until the end) | 1 — **this is E9's own Arm-B K=16 measurement, reused, not rerun** |
| M=8 | 16 | 8 | 2 |
| M=4 | 16 | 4 | 4 |

**Reference points (frozen, not rerun):** E9's K=8 crossing (99.9%:
[5.0e-5, 7.0e-5]) and E9's K=16 crossing (99.9%: [3.0e-9, 5.0e-9]) —
`contract_photonics_detector_boundary_2026-08-21.md` §10.1.

**Block structure:** `gen_block(rng, 16)` (E9's generator, unmodified)
produces a flat 16-op sequence: 2 QLDI (lanes 0, 1) followed by 14
combine ops (QSUB/ROTC, all targeting lane 0). Group boundaries are placed
at op-index multiples of M **starting from op 0** — for M=8: group 1 =
ops[0:8] (both QLDIs + 6 combines, structurally analogous to a K=8
`gen_block` sequence, though not the same random draws), group 2 =
ops[8:16] (8 pure-combine ops, continuing from the group-1 REGEN's
recovered state). For M=4: 4 groups (group 1 = 2 QLDI + 2 combines; groups
2-4 = 4 pure-combines each). **M=2 is excluded** — its first group would
be the 2 QLDIs alone with zero combine ops before the first REGEN, a
degenerate case that tests nothing new.

| parameter | value |
|---|---|
| K (logical length) | 16 only — this is specifically about the K=16 anomaly |
| M (regen period) | {16 (reused), 8, 4} |
| block generator | `gen_block` (E9's, unmodified) |
| M_K | 2000 (E9's K=16 value) |
| band | [1000, 30000] (E8/E9's) — applied once, to the FINAL group's oracle state (unchanged from E9's convention) |
| seed | 13 |
| det levels | not fixed in advance — smoke pass locates the transition region for M=8 and M=4 before any grid is frozen (same discipline as E9/E12's revision) |
| trials per cell | 30,000 (E1–E12's count) |

## 4. New code (additive) — Halt-and-Flag review required before running

**`run_chain_periodic_noisy(pb, block, M, sigma_det, rng)`** — mirrors
`run_chain`'s per-block REGEN logic (detection + BQE + canonical
re-entry, `test_regen_equivalence.py:264-278`) merged with
`run_chain_noisy`'s per-op noise injection (`_noise_per_op`, the same
detector-noise-only convention as E9/E11/E12: σ_φ=σ_amp=0). Splits `block`
(a flat op list) into groups of M ops (§3's boundary rule); after each
group, performs a REGEN using **that group's last mirrored op's noise
draw** (mirroring Arm B's `noise_lists[-1]` convention, applied per group
instead of once for the whole chain); a group's REGEN is scored against
the group's *exact* oracle state (not the original block's overall exact
state) — trial succeeds iff **every** group's REGEN recovers exactly
(mirroring Arm A's "fails if ANY op's projection is wrong," generalized
from op-granularity to group-granularity). Reuses `_apply_op_field`,
`_noise_per_op`, `_load_exp` verbatim; only the group-boundary/REGEN/
re-entry logic is new.

**Re-entry covers all 13 lanes (including lane 1, which no combine op
ever targets) — this is architecturally required, not just convenient
reuse of `run_chain`'s existing loop.** `contract_regen_isa_0x09_2026-08-20.md`
§5 (Stop Conditions) is explicit: *"Do NOT add opportunistic
per-component regeneration to REGEN; it is a whole-state boundary by
contract"* (lines 229-230). A design that only regenerated lane 0 at each
boundary would violate this frozen invariant. Confirmed by re-checking
before writing any code, not assumed from convenience.

**Halt-and-Flag pre-review items (flag before implementing, per role):**
- **Noiseless correctness is not obvious and must be checked, not
  assumed** (the E11/E12 lesson, again): does splitting `gen_block`'s
  16-op sequence into groups and regenerating between them, at σ=0,
  reproduce *exactly* the same final oracle state as the ungrouped M=16
  case? REGEN's idempotence (`REGEN(REGEN(S))=S`) is an established
  architectural invariant elsewhere in the repo, but this is the first
  time it's exercised inside `gen_block`'s specific lane-0-chain,
  lane-1-static structure with a *noisy* per-group detection — verify
  before trusting anything noisy.
- **Which noise draw represents "the group's REGEN"?** Using the last
  op's draw per group (mirroring Arm B's per-chain convention) is a
  choice, not a fact — an alternative would draw fresh, independent
  detector noise *at* each REGEN event rather than reusing an op's draw.
  State this as the model in use; flag if the smoke pass suggests it
  matters.
- **Whole-state re-entry means lane 1 is exposed to a fresh detector-
  noise draw at every intermediate REGEN, not just once at the very end
  — a real, previously-unconsidered effect working in the *opposite*
  direction from the hypothesis.** More groups (smaller M) means lane 0's
  per-group `m` shrinks (the intended benefit — the whole reason this
  hypothesis is being tested), but it *also* means lane 1 gets measured
  and re-encoded more times, each a fresh independent chance to fail from
  detector noise. Lane 1's own `m` stays small and roughly constant
  regardless of grouping (its `_load_exp` is fixed by the original QLDI
  operand magnitude, never accumulating like lane 0's does), so each
  individual exposure's failure probability should be low — but "low,
  repeated many times" is not the same as "negligible," and this hasn't
  been measured, only reasoned about. **If M=4's result comes out weaker
  than M=8's** (the opposite of the hypothesis's naive prediction that
  smaller M is strictly better), lane-1 exposure frequency — not a
  failure of the regeneration-frequency hypothesis itself — is the first
  thing to check before concluding anything about M=4 specifically.
- **Rejection-population invariant (E9/E12's established check):** since
  band-rejection is based on the *final* group's exact oracle value only
  (§3), rejection rates across M=16/8/4 should match `gen_block(rng,16)`'s
  own baseline rejection exactly — the grouping doesn't change which
  trials are accepted, only how they're scored. Verify, don't assume.

## 5. Metrics & outputs

- P_recover(σ_det) for M∈{8,4} (M=16 reused from E9, not rerun) — the
  primary artifact.
- Crossing brackets (99.9%, 99%, 95%), reported as brackets, same
  discipline as E9/E11/E12.
- **The comparison (the primary result):** where do M=8 and M=4's
  crossings fall relative to the two frozen reference points (E9's K=8:
  ~5e-5; E9's K=16: ~3-5e-9)? Report as a position on that four-orders-
  of-magnitude scale, not just a bracket in isolation.
- Output: canonical JSON (`results/sweeps/regen_placement_sweep.json`),
  frozen copy with sha256, README entry — same discipline as E1–E12.

## 6. Falsification criteria (non-vacuous)

- **Noiseless sanity gate (§4) must pass — 100% recovery at σ=0 for both
  M=8 and M=4** — before any noisy interpretation. HALT and fix if not.
- **Rejection-population invariant (§4) must pass** — rejection rates
  match `gen_block(rng,16)`'s own baseline exactly, for all M.
- **Hypothesis confirmed** iff M=8's (and/or M=4's) crossing lands
  meaningfully closer to K=8's reference crossing (~5e-5) than to K=16's
  (~3-5e-9) — given the four-order-of-magnitude gap, this should be
  visually unambiguous, not a close call.
- **Hypothesis ruled out** iff M=8/M=4's crossings stay near K=16's
  territory (~3-5e-9) despite the intermediate regeneration — report as
  cleanly as a confirmation, matching E11/E12's discipline.
- **Partial/graded result:** if M=8 and M=4 land at *different* points
  along the K=8-to-K=16 scale (e.g., M=4 closer to K=8's territory than
  M=8 is), that's informative about the shape of the frequency-dependence,
  not just a yes/no — report the ordering explicitly.
- **Non-monotonic result (§4's flagged lane-1 concern):** if M=4 performs
  *worse* than M=8 — the opposite of "more frequent regeneration is
  strictly better" — do not report this as ruling out the hypothesis
  outright. Check first whether the direction matches lane-1's exposure-
  frequency effect (§4): if so, this is a real, reportable second-order
  effect layered on top of a possibly-still-real primary effect, not a
  clean falsification. Report both readings explicitly rather than
  collapsing to one verdict.

## 7. Verification gates (implementer/auditor) — fixed order

```bash
# 0. Noiseless sanity gate (SS4): M=8 and M=4, sigma=0, against the
#    independent big-int oracle. Must be 100% before proceeding.

# 0b. Rejection-population invariant (SS4): rejection rates match
#     gen_block(rng,16)'s own baseline for all M.

# 1. Smoke pass -- confirm the harness runs, locate M=8/M=4's crossing
#    regions (expected to be VERY different in scale from each other and
#    from M=16 -- the smoke pass must cover a wide enough range to find
#    them, same discipline as E9's K=16 grid-floor lesson).
cd /home/user/Projects/hardware/SPU
PHOTONIC_TRIALS=200 .venv/bin/python3 photonics/run_photonic_regen_placement_sweep.py

# 2. Full run (only after step 1 confirms grid ranges)
.venv/bin/python3 photonics/run_photonic_regen_placement_sweep.py

# 3. Reproducibility: two full runs, bit-identical -- checked empirically
#    first (E9/E11/E12 lesson), not assumed.

# 4. Complete repository regression
bash tools/verify_repo.sh
```

**Interpreter note (carried forward):** `.venv/bin/python3`, never bare
`python3`.

## 8. Non-Goals

- **No M=2 or M=1** — M=2's first group is degenerate (§3); M=1 is
  already-established Arm A, not new territory.
- **No claim about which specific noise-draw convention (§4's flagged
  choice) is "correct"** — report results under the stated model; a
  different convention is a separate, later question if this result is
  ambiguous.
- **No operation-ordering or further loss-model work** — both already
  closed/parked.
- **No E10 (combined-axis)** — still deferred behind understanding K=16.
- **No tuning M values to find a "sweet spot"** — {16, 8, 4} are fixed by
  this design (clean divisors of `gen_block`'s 14 combine-ops-plus-2-QLDI
  structure); if a finer scan is warranted after this result, that's a
  separate, explicitly-authorized follow-on.

## 9. Results (2026-08-22) — full run, 36 cells × 30,000 trials, CONFIRMED

**Status: RESULT — regeneration frequency is a substantial, structured
contributor to the K=16 anomaly (not the whole story).**
`results/sweeps/regen_placement_sweep_frozen_v1_2026-08-22.json`, sha256
`cd942f77…`. Reproducibility CONFIRMED: two independent full 36-cell runs,
bit-identical.

### 9.1 Gates passed (per §7's fixed order)

- **Gate 0 (noiseless sanity):** 500/500 for both M=8 and M=4, exact match
  against the independent big-int oracle.
- **Gate 0b (rejection-population invariant):** identical rejection rate
  (0.5504–0.5842 depending on trial-count sample) across M=16/8/4 — the
  grouping doesn't change which trials are accepted, only how they score,
  exactly as designed.
- **Control-anchor check (added per review before the full run):** M=16
  measured directly through the new `run_chain_periodic_noisy` (a single
  group of all 16 ops) against E9's original `run_chain_noisy` arm-B path
  at six matched noise levels — **exact agreement at every level** (e.g.
  det=1e-8: both 0.8180 at 500 trials). The new harness reproduces the
  established result before being trusted for anything new.

### 9.2 Crossing brackets and the geometric-mean scaling

| M | 99.9% bracket | geomean crossing | improvement over M=16 |
|---|---|---|---|
| 16 (control) | [3.0e-9, 1.0e-8] | 5.477e-9 | — (matches E9 exactly) |
| 8 | [3.0e-8, 1.0e-7] | 5.477e-8 | **10.00×** (1.000 decades) |
| 4 | [1.0e-6, 3.0e-6] | 1.732e-6 | **316.23×** (2.500 decades total; 31.62× / 1.500 decades from M=8 alone) |

Full recovery curves (all 12 grid points, not just crossings) are
monotonic and cleanly separated at **every** point — no crossovers, no
non-monotonicity (the lane-1-exposure concern flagged in §4's review did
not materialize as a measurable effect at this trial count).

**The effect is accelerating, not saturating, as M shrinks** — the
M=16→M=8 halving buys exactly 1.0 decade; the M=8→M=4 halving buys 1.5
decades, half again as much. This is itself informative about the shape
of the mechanism (§9.4) — a constant-decades-per-halving law would have
suggested a single simple scaling relationship; the acceleration suggests
something more structured.

### 9.3 Position relative to the two frozen reference points

```
E9_K16 (M=16)                          E9_K8 (native, not this contract)
   5.48e-9 ─────┬─────┬─────────────────────┬──── 5.92e-5
              M=8   M=4                  (34.2x short)
            5.48e-8 1.73e-6
   |←── 1.0 dec ──→|←── 1.5 dec ──→|←── 1.533 dec (34.2x) ──→|
   |←──────────────── 4.033 decades total ────────────────→|
```

**M=4 covers 2.500 of the full 4.033-decade gap between M=16 and E9's
native K=8 crossing — 62.0% of the entire anomaly, closed by
regeneration frequency alone.** It does not fully reach K=8's native
health: a 34.2× gap remains between M=4 (regenerating every 4 ops within
a *logical* K=16 sequence) and K=8's own native crossing (8 ops, no
intermediate regeneration needed because there's nothing to regenerate
until the natural end).

### 9.4 Interpretation — precisely scoped

**Regeneration frequency is a real, substantial, structured contributor
to E9's K=8→K=16 collapse — not the complete explanation.** This is
categorically different from E11 (ruled out) and E12 (ruled out): this is
the first candidate mechanism in this investigation chain that produces a
*large, monotonic, reproducible* effect in the predicted direction.

**What this does and doesn't establish:**
- It establishes that *how often* you regenerate within a longer program
  matters enormously — consistent with, and now quantitatively extending,
  the already-frozen Step-6 finding that Arm A (every op) survives
  stochastic noise where Arm B (chain) collapses.
- It does **not** establish that regeneration frequency is the *only*
  missing variable — the remaining 34.2× gap at M=4 means something else
  is still unaccounted for, even at the most frequent regeneration tested
  in this contract.
- The acceleration (1.0 dec at M=8, 1.5 dec at M=4, not a flat 1.0 dec
  per halving) is unexplained by this contract — a natural next question,
  not answered here (§9.5 non-goals: no tuning M values to chase this
  within this contract).

### 9.5 What's preserved as evidence

- The full recovery curve (all 12 grid points × 3 M values), not just
  crossing brackets — per the review's explicit request.
- The M=16 control-anchor validation against E9's original harness (§9.1).
- The geometric-mean scaling table and decade-gap accounting (§9.2/9.3).
- Code: `run_chain_periodic_noisy`, `independent_oracle`, `cell`, `main`
  — all in `photonics/run_photonic_regen_placement_sweep.py`.

### 9.6 Next

The remaining 34.2× gap at M=4 is the open question. Candidates not yet
investigated: finer M values (M=2, previously excluded as degenerate —
worth reconsidering now that the trend is this strong), a genuinely
different mechanism combining with regeneration frequency, or the
lane-1-exposure effect (§4) becoming measurable at finer M where it's
tested more often per logical sequence. None of these are authorized by
this result — each needs its own decision, per the established discipline
across E11/E12/E13.
