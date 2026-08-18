# INA226 coarse anomaly monitor v4 contract

Date frozen: 2026-07-19 (v1) — amended 2026-08-06 (v2) — amended 2026-08-16
(v3) — amended 2026-08-18 (v4)

## Status and question

This contract was frozen before an INA226 was available and before any
physical capture was ingested or scored. Its machine-readable source of truth
is `software/datasets/ina226_coarse_monitor_v4.json`.

### What changed in v4, and why v3 is still on disk

**Amended 2026-08-18, `sessions_sealed_when_amended: 0`.** v4 adds a second
model, gated independently: `spu4_som_edge` (the four-node winner-take-all
classifier, `hardware/rtl/core/spu4/spu4_som_edge.v`), alongside the existing
seven-node SPU-13 SOM. Nothing about the capture schema, task, folds,
features, or validation changes — this is purely an addition to `models` and
`gates`.

**Why it had to happen now or never.** The edge-node product focus decided
2026-08-16 moved the deployable classifier to `spu4_som_edge` — see
`knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7 and the session notes for that
decision — but this contract's "Baselines and frozen gates" section, carried
over unchanged since v2, still named only the seven-node SOM. Found
2026-08-18 while building `tools/spu4_som_edge_trainer.py` and
`tools/spu4_som_edge_cross_validate.py`: the classifier this repo is actually
building tooling for had no predeclared accuracy gate. A gate committed after
real data exists has no integrity — same reasoning v3 used for the `pulses`
covariate — so this had to be written now, blind, or not at all.

**Both models are targeted explicitly, not one replacing the other.** Real
captures will be scored against both the existing seven-node SOM gate and the
new `spu4_som_edge` gate independently. A negative on one does not relax the
other's threshold, and passing one does not require passing the other.

**The `spu4_som_edge` threshold values are identical to the seven-node SOM's**
(aggregate ≥90%, worst fold ≥80%, per-class recall ≥80%) — same task, same
data, same bar, deliberately not an easier standard for the newer, simpler
classifier. `spu4_som_edge`'s v1 hardware ABI (`best_node`, `best_quadrance`)
does not expose a runner-up quadrance the way the SOM1 evidence frame's
confidence gap does, so there is currently no ambiguity gate for it — an
honest hardware boundary, not an oversight papered over for symmetry.

**What this amendment does NOT do.** `tools/ina226_capture_pipeline.py`'s
`run_study()` fully implements the seven-node SOM path — fold splitting,
per-fold normalization, majority/threshold/centroid baselines, gate checking
— and has **not** been extended to also train and score `spu4_som_edge` per
fold. `software/tests/test_ina226_capture.py`'s `CONTRACT` constant still
pins v3. Wiring `spu4_som_edge` into that pipeline (mirroring
`_som_session_pairs` with `tools/spu4_som_edge_trainer.py`'s `train_nodes`
and `find_bmu_edge` instead of the SOM1 evidence-frame path) is real,
separate, tracked follow-up work — attempting it inside this same change
alongside a frozen-contract amendment risked a rushed edit to pipeline code
that already produces real evidence for the seven-node path. This amendment
is the part that only has integrity if committed to *before* that
integration and before real data exist; the integration itself can safely
happen after, since the gate it must satisfy is now fixed and can't be
tuned against results either way.

### What changed in v3, and why the earlier versions are still on disk

**Amended 2026-08-16, `sessions_sealed_when_amended: 0`.** v3 adds a fifth
capture column, `pulses` — the raw encoder edge count per sample interval —
so that shaft rotation is recorded while capturing.

**Why it had to happen now or never.** Rotation cannot be retro-fitted: it is
sampled, not derived. Once block 0 is sealed, adding it means discarding
sessions or permanently losing the ability to condition on operating point.
The same latitude the v1→v2 amendment relied on — nothing sealed, no score in
existence — is what makes this legitimate, and it closes at block 0.

**Why it is needed at all.** Every prior negative on this track failed the
same way: the features encoded *operating condition* rather than *fault
state*, with no covariate to condition on. Rotation is that covariate.

**`pulses` is a COVARIATE, not a feature, and must never enter the feature
list.** Rotation trivially separates `current_limited_stall` from the other
classes, so a model given it would score well while demonstrating nothing
about current-based anomaly detection — it would be reporting that a stopped
motor has stopped. The feature list is unchanged at the same four
current-derived values, and `software/tests/test_ina226_capture.py` asserts
`"pulses" not in contract["features"]` so a future edit cannot quietly
invalidate the study.

Everything else — window, folds, capture order, models, gates — is carried
over from v2 unchanged.

**No class-conditional pulse gate is specified, deliberately.** It is not yet
known whether a current-limited stall on this rig stops rotation completely or
merely slows it, and inventing a threshold before measuring would encode a
guess as a validation rule. The first capture block answers that empirically.

**An all-zero pulse column does not prove the encoder was disconnected** — it
is indistinguishable from a stalled motor, which is a real class. Confirm the
encoder counts before capturing block 0.

### What changed in v2, and why v1 is still on disk

v1 (`ina226_coarse_monitor_v1.json`, SHA-256 `58b37ec5…`) applied the
50000 ppm bus-voltage tolerance to **every** row of **every** class. Current
limiting works by collapsing supply voltage, so a genuine
`current_limited_stall` cannot hold bus voltage within 5 % of nominal on any
bench — the two clauses were mutually exclusive as written.

Block 0 measured it on 2026-08-06: with the supply regulating in
constant-current at 307.4 mA, bus voltage collapsed to 1478–1501 mV and
**0 of 145 rows** fell inside the window, while `normal` and `elevated_load`
passed the same gate at 2995–3017 mV and 2897–2937 mV. Mean current ascended
98.3 → 240.8 → 307.4 mA, so the physical classes separated cleanly and only
this clause failed.

v2 scopes the bus-voltage check to `normal` and `elevated_load`. Every other
clause — shunt scaling, shunt headroom, cadence, row count, session rejection
policy — still applies to the stall class in full.

**v1 is deliberately left unmodified.** The claim that this study was
pre-registered rests on v1 being byte-identical to what entered Git at
`ed16263`; amending it in place would have destroyed that. This correction was
made before any session was sealed and before any score existed, so it is not
tuning against held-out results — the `failure_policy` prohibition on that
remains in force and unchanged.

The experiment asks one narrow product question: can the existing seven-node
SPU SOM distinguish **normal**, **elevated load**, and a safely bounded
**current-limited stall** from one 100 Hz current channel across independently
re-established bench sessions?

This is a coarse actuator-state monitor, not bearing diagnosis, leakage
severity grading, remaining-life estimation, or a safety controller. It does
not alter the SOM trainer, map format, FPGA RTL, or SOM1 result ABI.

## Frozen acquisition contract

The sensor is an INA226 at address `0x40` with the module's verified `R100`
(100 milliohm) shunt. `tools/bench_metrics/ina226_logger.py` supplies integer
measurements at 100 Hz. Each scored file must use the host logger schema:

```text
host_iso,probe,phase,t_ms,bus_mV,shunt_uV,current_uA
```

One file is one session and contains one class only. The first 128 rows are
used, producing four contiguous, non-overlapping 32-sample windows. There is
no search for a favourable interval. A malformed row, duplicate or
non-increasing timestamp, cadence interval outside 8--12 ms, shunt/current
inconsistency, or saturation rejects the complete session rather than dropping
an inconvenient sample.

The exact INA226/R100 consistency check is:

```text
abs(shunt_uV * 1000 - current_uA * 100) <= 500
```

The 500-unit residual permits only the logger's documented half-microvolt
integer truncation. Absolute shunt voltage must remain below 75,000 uV, leaving
headroom below the INA226's range. Bus voltage must stay within 5% of the
nominal millivolts recorded in the capture manifest.

## Frozen sessions and folds

There are ten capture blocks. Every block contains one session of each class,
for ten independently re-established sessions per class. To prevent class
order from being confounded with warm-up or drift, block `b` rotates the order
`normal, elevated_load, current_limited_stall` left by `b mod 3`.

The five folds are fixed as `capture_block mod 5`. A held-out fold therefore
contains two complete sessions of every class, and all four windows from a
session always remain together. Training on windows and testing on other
windows from the same physical session is prohibited.

Window predictions are reduced to one session decision by plurality. An exact
vote tie keeps the lower class id. Accuracy is scored at the session level;
window-level results are diagnostic only.

## Features and exact boundary

The input to classification is integer microamps. Every 320 ms window produces
the four already-published temporal features:

1. round-half-even mean current in milliamps;
2. round-half-even peak-to-peak current in milliamps;
3. round-half-even mean absolute successive difference in milliamps;
4. round-half-even mean absolute deviation from the exact rational mean in
   milliamps.

Normalization is fitted on training windows only. Each lane is mapped by exact
round-half-even affine arithmetic to `0..30000`. Held-out values may clamp only
at this declared boundary, and every clamp and vector collapse is reported.
The normalized vector then follows the existing Cartesian bridge, seven-node
SOM, and SOM1 evidence-frame path.

The hardware v1 ambiguity bit remains what the RTL implements: an exact zero
winner/runner-up confidence gap. The report must include the complete gap
distribution and exact-tie count; it must not retrofit a software-only reject
threshold and describe it as hardware behaviour.

## Baselines and frozen gates

Every fold must report training-majority, training-fitted scalar threshold
(`normal` versus either anomaly), three-class nearest centroid, and seven-node
SOM results. The report includes fold and aggregate confusion matrices,
balanced accuracy, per-class recall, feature ranges, clamp/collapse counts,
map hashes, confidence gaps, and SOM1 oracle equality.

A captured map is eligible for FPGA replay only when all of these hold:

- aggregate three-class SOM balanced accuracy is at least 90%;
- the worst fold is at least 80%;
- every class recall is at least 80%;
- every capture session passes acquisition validation;
- every generated software SOM1 record matches the exact oracle.

An accuracy-superiority statement is separately permitted only when the SOM
exceeds the three-class centroid and its collapsed normal/anomaly result
exceeds the scalar threshold. Passing the replay gate does not imply passing
the superiority gate. In particular, if a simple current threshold solves the
task equally well, the experiment may prove the hardware pipeline without
proving that a SOM is commercially necessary for this task.

Any failed gate is recorded as a negative. The capture selection, features,
folds, training schedule, or gates must not be tuned against held-out results.
A changed hypothesis requires a new versioned contract.

### spu4_som_edge gate (v4)

The same real captures, the same frozen folds (`capture_block mod 5`), the
same session-level plurality reduction over four windows, and the same
training-fold-normalized `0..30000` features are scored a second time against
`spu4_som_edge` — independently of, not instead of, the seven-node SOM gate
above. Every fold reports `spu4_som_edge`'s three-class confusion matrix,
balanced accuracy, and per-class recall, trained via
`tools/spu4_som_edge_trainer.py` and scored via
`software/lib/spu4_som_edge_oracle.py`'s `find_bmu_edge`.

A captured map is eligible for `spu4_som_edge` FPGA replay only when all of
these hold:

- aggregate three-class `spu4_som_edge` balanced accuracy is at least 90%;
- the worst fold is at least 80%;
- every class recall is at least 80%;
- every capture session passes acquisition validation;
- every generated prediction matches `find_bmu_edge`'s oracle exactly.

An accuracy-superiority statement for `spu4_som_edge` is separately permitted
only when it exceeds the three-class nearest centroid and its collapsed
normal/anomaly result exceeds the scalar threshold — the identical structure
as the seven-node claim, evaluated for `spu4_som_edge` on its own terms.

`spu4_som_edge` has no ambiguity/confidence-gap gate. Its v1 hardware ABI
(`best_node`, `best_quadrance`) does not report a runner-up, unlike the SOM1
evidence frame. This is a real hardware-contract boundary, not a gap in this
document.

**Not yet built:** the actual scoring code. `tools/ina226_capture_pipeline.py`
trains and scores the seven-node SOM per fold today; it does not yet also
train and score `spu4_som_edge`. That integration is tracked, separate work —
see "What changed in v4" above for why declaring the gate first, before that
code exists, is the part that has to happen now.

## Safety boundary

The monitored target is a separate low-voltage, replaceable actuator or fan,
never an FPGA supply rail. The current-limited-stall class is allowed only with
a bench-supply limit at or below the actuator's documented continuous-current
rating. Each captured stall exposure is at most 1.5 seconds and is followed by
at least 30 seconds of cooldown.

Abort immediately on heating, unexpected supply behaviour, shunt voltage over
75,000 uV, or an unknown actuator current rating. If the purchased actuator
cannot meet this safety boundary, do not weaken it at the bench: freeze a v2
task with a safe substitute condition before collecting data.

## What can be built before the sensor arrives

The capture manifest, strict CSV validator, deterministic feature/fold
materializer, hostile logger fixtures, capture-day runbook, and exact Voronoi
explanation can all be completed with synthetic files. Synthetic fixtures may
test plumbing and rejection behaviour only; they are not evidence that the
physical accuracy gates pass.

Also buildable now, same caveat: wiring `spu4_som_edge` into
`tools/ina226_capture_pipeline.py`'s `run_study()` (see "Not yet built" under
the `spu4_som_edge` gate above) needs no real sensor — `tools/spu4_som_edge_trainer.py`
and `tools/spu4_som_edge_cross_validate.py` are already proven against
synthetic data (`software/tests/data/synthetic_current_v1.csv`), and the same
pattern extends to the pipeline's fold/normalization machinery without a
physical capture in hand. Doing so does not make any accuracy claim true
early; it only means the scoring code exists and is tested before the gate
it must satisfy gets exercised for real.
