# Engineering Contract: D4 Canonical Decision P1b

Date: 2026-09-29  
Contract ID: `D4-CANONICAL-DECISION-P1B-2026-09-29`  
Status: **COMPLETE; bounded software tranche qualified**

Roles: spec author — Codex; halt-and-flag implementer — Codex;
integration auditor — Codex with independent integer recomputation. P1b tests noisy observations and exact
bounded D4 quantization. It authorizes no RTL, synthesis, route, or hardware.

## 0. Pre-execution commands and halt review

Run from the repository root before P1b implementation:

```bash
cat build/d4_canonical_decision_p1/repo_gate/run_01/result.json
cat build/d4_canonical_decision_p1/exact_01.json
python3 software/tests/test_d4_canonical_decision.py \
  --output build/d4_canonical_decision_p1b/p0_preflight_01.json
git diff --check
```

Require exactly one `COMPLETE` marker and exit 0 for the P1 repository gate;
require a fresh P0 oracle pass. Refuse existing output paths. Before writing
the experiment, review bounded nearest-point ties, group equivariance,
profile weights, base-representative leakage, fixed-point widths, and action
codomain. Halt and flag any contradiction; do not silently change a frozen
profile or break a tie lexicographically.

## 1. Objective and scoped files

Measure whether P1's canonical decision advantage survives two exact
off-lattice perturbations followed by an explicit bounded nearest-D4 map.
Separate the effect of quantization from folding by comparing canonical,
raw, and augmented raw models on the same quantized observations. Include
raw noisy-coordinate codebooks as a control for information lost by `Q_D4`.
Reuse P0's group and chamber, P1's 57 representatives, five folds, label,
capacities, batch schedule, tie rules, and exact metric definitions.

Create small, single-purpose files under `software/tests/` named
`d4_decision_p1b_data.py`, `d4_decision_p1b_quantize.py`,
`d4_decision_p1b_metrics.py`, and `test_d4_canonical_decision_p1b.py`.
Split further if a file exceeds 150 lines. Adapt P1's learner through a
small scoped parameter for coordinate bounds; preserve P1 behavior and its
evidence. Update this contract and `docs/D4_CANONICAL_DECISION_RESEARCH_NOTE.md`
after interpretation. Do not edit generated files or P0/P1 evidence.

## 2. Frozen observations, labels, and split

Keep each P1 base representative `c` in its existing fold. Its latent label
is `y(c)` from P1; noise and quantization never relabel it. Use exact
fixed-point scale 16 and two ordered profiles:

```text
delta_0 = (1, 2, 3, 4) / 16
delta_1 = (11, 10, 3, 1) / 16
z(c,j,w) = w (c + delta_j),  j in {0,1}, w in W(D4).
```

Store `z` as its four integer numerators at scale 16. Apply each of the 192
group maps to each seed, including repeated quantized images, in frozen
group order. The rational observations themselves must have full orbit size
192; assert 21,888 unique `(base,profile,orientation)` observations and
that every base appears in only one fold. Every held-out observation is
scored exactly once across the five folds. Report each profile separately
and their equal-weight mean. Also report a secondary metric weighted by the
P1 base orbit sizes; never replace the primary equal-base metric with it.

## 3. Exact bounded quantizer

Define `Q_D4(z)` as the unique minimizer over P0's 3,281-state bounded
domain `D4_B` of `sum_i (z_i - 16*q_i)^2`. Evaluate the 114 seed observations
against all 3,281 candidates using integer arithmetic. Reject any seed
with two minimizers. Obtain transformed projections by group action and
assert, independently, `Q_D4(w z)=w Q_D4(z)` for all 21,888 observations;
spot-check direct exhaustive minimization for the four simple generators
on every seed. Do not use arbitrary tie selection or a nearest-integer
shortcut in the defining oracle.

Assert the frozen seed facts before model training: profile 0 projects to
its original `c` for all 57 bases; profile 1 changes 28 of 57 projected
states and changes the P1 norm-band label for 16 of 57. Record the full
projection and squared-distance distribution. These 16 crossings are the
error count for the direct norm rule applied after projection, not a lower
bound on every learned classifier. Log train/test projected-coordinate
collisions and conflicting latent labels without removing them.
At the 114 seed level, assert 57 distinct projected coordinates, 41
coordinates reached by both profiles, 16 with conflicting latent labels,
and 16 majority-label errors across the 114 equally weighted seeds.
Group-expanded conflict counts must be recomputed from the actual evaluation
weights; do not assume they equal seed counts.

Canonical quantized input is `C(Q_D4(z))`; retain deterministic metadata
`g_z` satisfying `g_z Q_D4(z)=C(Q_D4(z))`. Raw quantized input is `Q_D4(z)`.
Raw noisy input is the unprojected scale-16 numerator tuple. Do not pass
latent `c`, profile ID, or transform ID to any learner.

## 4. Frozen learners, controls, and storage

Use `K=(1,2,4,8,16,32)` and 12 exact batch epochs with P1's initialization,
BMU tie, SOM ring radii, weighted means, ties-to-even, final majority vote,
and empty-node rule. Train these eight arms at every fold and capacity:

```text
canonical_q_som          canonical_q_codebook
raw_q_som                raw_q_codebook
raw_q_augmented_som      raw_q_augmented_codebook
raw_noisy_codebook       raw_noisy_augmented_codebook
```

For each training base and profile, canonical and unaugmented arms use one
sample of weight 192; unaugmented orientation is P1's
`GROUP[(37*r+11)%192]`, where `r` is the base's global index. Augmented arms
use all 192 transformed observations with weight 1 each. Thus each base has
total weight 384 across both profiles in every arm. Keep repeated `Q_D4`
images as separate weighted records: they express uniform orientation
weight and can be merged only by summing identical weights exactly.

Quantized prototypes remain four integer coordinates in `[-4,4]`, with
P1's 18 bits per node including class. Raw noisy prototypes are four signed
8-bit fixed-point numerators at scale 16, plus two class bits: 34 bits per
node. Assert every update fits `[-128,127]`; clamp only quantized prototypes
to `[-4,4]`. Use squared integer distance in each arm's own units. Report
prototype count and actual codebook bits; compare the noisy-coordinate
controls by bits as well as `K`. Exclude canonicalizer, quantizer, and
training-workspace cost from codebook bits and report them separately as
unmeasured hardware costs. Do not call a matched-`K` comparison a matched-bit
comparison when widths differ.

Compute two exact nonlearned observed-input controls: P1's norm-band rule
on `Q_D4(z)`, and the same thresholds on `sum_i z_i^2` at scale 256
(`<=12*256`, `<=30*256`, else class 2). Report the inaccessible latent
`y(c)` rule only as the zero-error reference. If identical projected
coordinates carry conflicting latent labels, compute the exact majority-label
error among all observations at each projected coordinate as the empirical
irreducible error for quantized-input rules. Do not substitute the 16/57
norm-rule crossing count for this quantity.

## 5. Exact action and metrics

For canonical predicted class `k`, use P1's stabilizer-compatible action
`F(q,k)=m[k]*q`, `m=(1,2,3)`, and emit
`g_z^-1 F(C(Q_D4(z)),k)`. Assert it equals `m[k]*Q_D4(z)` exactly and is
equivariant over every transformed observation, including chamber walls.
Report action class error against `m[y(c)]*Q_D4(z)` separately from the
quantization displacement to the rational action `m[y(c)]*z`.
The latter is a nonzero exact rational vector even when class prediction is
correct. Do not claim arbitrary-policy equivariance from this scalar family.

For every `(fold,arm,K,profile)`, record confusion, equal-base and
base-orbit-weighted error, orbit disagreement, prototype bits, training and
inference distance evaluations, update counts, and winner/runner-up gaps.
Aggregate exact integer or rational counts over all five folds. Publish the
full error-versus-codebook-bits table, including all capacities; do not
select a favorable capacity after observing results. Compare P1 and P1b
only at the same task label, base split, and declared observation model.

## 6. Proposed commands and bounded evidence

After owner authorization, implementation, and a fresh pre-execution
review, run focused checks before the full experiment:

```bash
python3 -m py_compile software/tests/d4_decision_p1b_data.py \
  software/tests/d4_decision_p1b_quantize.py \
  software/tests/d4_decision_p1b_metrics.py \
  software/tests/test_d4_canonical_decision_p1b.py
python3 software/tests/test_d4_canonical_decision_p1b.py \
  --preflight --output build/d4_canonical_decision_p1b/preflight_01.json
git diff --check
```

The preflight must assert the 114 unique minima, frozen 28/16 changes,
57/41/16 seed collision/conflict facts,
21,888 equivariant transformed projections, fold isolation, exact weights,
fixed-point fit, and nonvacuous label crossings. It must refuse overwrite.
No model result is valid if these checks fail.

Owner-frozen full-run budget (2026-10-10): **one attempt, 1,800 seconds per
attempt and 1,800 seconds cumulative**, through a new evidence directory.
Owner instruction: "Approve one 1,800-second experiment". No retry, timeout
extension or repository-wide qualification is authorized by this budget; a launched attempt consumes its
slot on any outcome. Run:

```bash
tools/run_detached_job.sh \
  --output build/d4_canonical_decision_p1b/full_run_01 \
  --timeout 1800 --notify-desktop -- \
  python3 -B build/d4_canonical_decision_p1b/preparation_01/run_frozen.py
```

Interpret only one terminal marker plus `result.json` in a later session.
Require a machine-readable configuration, source revision/dirty status,
all 240 `(fold,arm,K)` rows, profile rows, control errors, projection
collisions, action checks, and an independent metric recomputation. A
repository-wide gate requires its own new owner-frozen attempt and
`bash tools/verify_repo.sh`; the existing T1p post-transport failed gate
does not become a P1b pass. Run the scoped D4 tests, ROTC/IROTC trace,
math-oracle, and Artix-7 mandatory gates per root `AGENTS.md` before any
completion claim or commit, using detached execution for jobs over 60s.

## 7. Stop and evidence boundary

Halt on a projection tie, failed quantizer equivariance, fold leakage,
changed P1 label/split/learner rule, inexact arithmetic, fixed-point
overflow, or a mismatch between evidence and recomputed metrics. A worse
learned curve is a valid result and never authorizes changing noise after
inspection. P1b is software-only: it cannot establish RTL area, throughput,
power, or silicon behavior. P2 requires a separate architecture contract
and a positive decision-usefulness review after P1b interpretation.

## 8. Implementation and launch record (2026-10-10)

```bash
python3 -B software/tests/test_d4_canonical_decision_p1b.py \
  --preflight --output build/d4_canonical_decision_p1b/preflight_04.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/tests/d4_decision_p1.py \
  software/tests/d4_decision_p1b_*.py \
  software/tests/test_d4_canonical_decision_p1b.py \
  spu_strategy/contract_d4_canonical_decision_p1b_2026-09-29.md \
  docs/D4_CANONICAL_DECISION_RESEARCH_NOTE.md
```

P1 prerequisites: retained repository gate has exactly one COMPLETE marker
and exit 0; fresh P0 evidence is `build/d4_canonical_decision_p1b/p0_preflight_01.json`.
Before hashes and original learner are in `preparation_01/before_manifest.json`
and `preparation_01/before/`. Existing P0/P1 evidence remains unchanged.

The learner retains its default bounds and adds explicit bounded coordinates
and clipping selection for noisy controls. Preparation compares the original
and new defaults on six fixtures. Exact merged training weights are permitted
by §4; report actual distance evaluations and pre-merge record counts separately.
Quantization displacement is reported at scale 16 and squared scale 256; action
class error and actual quantized-vector error remain separate when q is zero.

Independent audits recompute predictions, confusion, per-base errors, weighted
errors, gaps, action errors, displacement, controls and aggregate counts without
using the learner winner or metric evaluator. Corrupted metric and aggregate
controls must fail. Every source used by the full run is copied into
`preparation_01/source_snapshot`; `run_frozen.py` checks the frozen manifest
before and after execution. Full-run acceptance is software experiment evidence,
not full tranche closure. Required repository and Artix-7 gates remain pending
a separately budgeted qualification.

## 9. Interpreted experiment evidence

`build/d4_canonical_decision_p1b/full_run_01` has exactly one COMPLETE marker,
exit 0 and duration 309/1,800 seconds. The one-attempt budget is consumed.
All 240 fold rows and 48 aggregate rows passed; 1,050,624 predictions were
independently recomputed. Source hashes match final preflight.
`experiment_review.json` binds the report and frozen manifest. Complete curves
and controls are in `docs/D4_CANONICAL_DECISION_P1B_RESULTS_2026-10-10.md`.
Simple norm controls beat every learned arm on the primary metric.
No hardware promotion is authorized; full tranche qualification remains
pending its own owner-frozen budget and mandatory gates.

## 10. Qualification authorization (2026-10-10)

```bash
python3 -B build/d4_canonical_decision_p1b/qualification_preparation_01/verify_sources.py
tools/run_detached_job.sh \
  --output build/d4_canonical_decision_p1b/qualification_01 \
  --timeout 7200 --unit spu-d4-p1b-qualification-20261010-01 --notify-desktop -- \
  bash build/d4_canonical_decision_p1b/qualification_preparation_01/run_gates.sh \
  /home/user/Projects/hardware/SPU/build/d4_canonical_decision_p1b/qualification_01
```

Owner instruction: "Approve one 7,200-second qualification". Budget: one
attempt, 7,200-second wall-clock and cumulative limit; no retry or extension.
The isolated snapshot overlays unchanged D4 experiment sources onto the
qualified ISA baseline. Qualification recomputes retained P1b predictions
without retraining P1b, and reruns original P1 to require exact preservation
of all 180 fold and 36 aggregate results. Focused D4 checks, software ISA
checks, scoped core regression, repository verification, trace/math gates
and the separate requested-25-MHz Artix-7 Padé build are explicit gates.
Full snapshot source identity is checked before and after execution.
No integrated Surd/REGEN mapping, board operation or hardware promotion
is authorized. End the turn after LAUNCHED; interpret only a single terminal
marker and durable gate results in a later invocation.

## 11. Qualification closeout (2026-10-10)

The repaired campaign succeeded on its first attempt: `qualification_02` has
exactly one COMPLETE marker, exit 0 and duration 2,037/7,200 seconds.
All 13 fresh gate records pass; eleven completed computational gates are
explicitly reused with source/evidence hash bindings. Full repository 243/0,
scoped core 75/0, trace/math gates, separate 25-MHz-requested Artix-7 Padé build
and before/after checks of 2,034 snapshot source files pass.
`qualification_02/qualification_review.json` records the complete evidence.
The bounded software tranche is closed; learned-model limitations remain.
No hardware promotion or integrated Surd/REGEN qualification follows.
Two restart slots were unused; successful completion ends that campaign.
