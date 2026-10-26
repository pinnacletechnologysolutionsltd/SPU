# Engineering Contract Draft: D4 Canonical Decision P1

Date: 2026-09-29  
Contract ID: `D4-CANONICAL-DECISION-P1-2026-09-29`  
Status: **P1 EXACT EXPERIMENT PASS; REPOSITORY GATE PASS**

Roles: spec author — Codex; halt-and-flag implementer — future agent;
integration auditor — future agent. P1 is software only. Do not add RTL,
nearest-lattice quantization, off-lattice noise, E8, synthesis, or hardware.

## 0. Pre-execution commands

Run from the repository root:

```bash
cat build/d4_canonical_decision_p0/repo_gate/run_01/result.json
cat build/d4_canonical_decision_p0/oracle_04.json
python3 software/tests/test_d4_canonical_decision.py \
  --output build/d4_canonical_decision_p0/p1_preflight_01.json
git diff --check
```

Require exactly one P0 repository-gate terminal marker, `COMPLETE`, and
`result.json` exit 0 before P1 execution. The P0 oracle preflight must pass
without overwriting evidence. If either fails, halt and flag. Review the
rules below for a contradictory split, label, training update, or action
before implementation; do not repair a frozen rule silently.

## 1. Decision and scoped files

Measure held-out invariant decision error against codebook bits and prototype
count. Compare a canonical SOM with a canonical non-SOM codebook, raw SOM,
augmented raw SOM, raw non-SOM codebook, and augmented raw non-SOM codebook.
Measure whether canonical outputs reconstruct exact equivariant actions.
Also evaluate the direct integer norm-threshold rule as a zero-prototype
control. The synthetic norm-band task cannot establish a general hardware
advantage when that direct rule already gives zero error.

Implement `software/tests/d4_decision_p1.py`,
`software/tests/d4_decision_p1_data.py`,
`software/tests/d4_decision_p1_metrics.py`, and
`software/tests/test_d4_canonical_decision_p1.py`, plus this contract and
`docs/D4_CANONICAL_DECISION_RESEARCH_NOTE.md`. Reuse
`software/tests/d4_canonical_exact.py`. Split a source file if it exceeds
the repository's 50–150-line Lithic guidance. Do not modify P0 evidence,
P0 arithmetic, existing SOM hardware, or generated files.

## 2. Exact task and split

Use the P0 domain `D4_B`, group order, chamber, and canonical map without
changes. Enumerate the 57 chamber representatives in lexicographic order.
Define the three-class invariant label solely from squared norm:

```text
y(x) = 0 if ||x||² <= 12
       1 if 14 <= ||x||² <= 30
       2 if ||x||² >= 32
```

The bounded D4 domain has only even squared norms. Assert representative
class counts `(13,24,20)` before training. Within each class, sort
representatives lexicographically and assign fold `j mod 5` to its local
index `j`. Run all five held-out folds. All transformed states of a base
representative must remain in its fold. Assert every representative is held
out exactly once and every class occurs in each held-out fold. Evaluate on
all distinct orbit images of every held-out representative: across the five
folds, exactly 3,281 states must be scored once. Report both equal-weight
per-representative error and per-state error; the former is primary.

For unaugmented raw training, provide one fixed orientation per training
representative: if `r` is its index in the global lexicographic list of 57
representatives, use group element `GROUP[(37*r+11) % 192]` on that
representative. For augmented raw training, use every distinct orbit image,
sorted lexicographically, each with exact weight `1/|Orb(c)|`; each base
representative then has total weight one. Canonical training uses each
representative once with weight one. No held-out state, its canonical
representative, or its label may enter training or initialization.
The implementation may multiply every training weight by the common exact
factor 192: augmented samples then have integer weight `192/|Orb(c)|`,
and unaugmented/canonical samples have weight 192. This preserves all
weighted means and majority comparisons exactly; no floating point is used.

## 3. Frozen learners and capacity axis

Train at `K=(1,2,4,8,16,32)` nodes/prototypes for each fold and arm.
Represent every prototype as four signed four-bit integer coordinates
within `[-4,4]`; its assigned class uses two bits. Count `18*K` stored
codebook bits for all six arms. Count topology as implicit fixed wiring,
and report transient eight-bit D4 transform metadata separately. Do not
claim that this accounting measures RTL canonicalizer cost.

Use squared Euclidean distance over four integer coordinates. BMU ties go
to the lower prototype index. Initialize with deterministic farthest-first
selection from distinct training coordinates: first lexicographic minimum;
then maximize distance to the nearest already chosen coordinate, breaking
ties lexicographically. Assert at least `K` unique training coordinates.

Run 12 batch epochs for both learner families. In each epoch, assign each
weighted training coordinate to its BMU using the current prototypes.
For the non-SOM codebook, update prototype `i` from only samples assigned
to `i`. For the SOM, place nodes on a one-dimensional ring and include
samples whose BMU has ring distance at most radius `2` in epochs `0..3`,
`1` in epochs `4..7`, and `0` in epochs `8..11`. For each coordinate,
accumulate the weighted numerator and denominator as exact integers or
`fractions.Fraction`; divide only as an exact rational `N/D` after every
sample has contributed. Round its absolute value using `q,r=divmod(|N|,D)`:
increment `q` if `2r>D`, or if `2r=D` and `q` is odd, then restore the sign.
Clamp the rounded integer to `[-4,4]`. Assert `D>0`. Retain an unchanged
prototype if its update set is empty. Do not use floating point, random
ordering, or learning libraries.

After epoch 11, assign each node the weighted majority class among samples
whose final BMU is that node; ties go to the lower class. For an empty node,
use the class of the nearest training coordinate to its prototype, with
ties resolved by coordinate then class. Predict by final BMU and node class.
Record winner and runner-up squared distances and their gap. For `K=1`,
record runner-up/gap as unavailable, not zero.

## 4. Exact controls and metrics

Assert `y(w x)=y(x)` for all 629,952 state/group pairs. For each held-out
state, compare canonical prediction under `C(x)` against the same
representative's prediction under every orbit transform; all must match.
The raw arms may disagree across an orbit; report their disagreement rate.

Let class multipliers be `m=(1,2,3)`. A canonical model with predicted
class `k` emits `F(C(x),k)=m[k]*C(x)` and reconstructs
`g_x^-1 F(C(x),k)`. Assert exact equality to `m[k]*x`, exact equivariance
under every group transform, and stabilizer compatibility at every tested
representative. Compare the emitted vector to the true action `m[y(x)]*x`;
report this action error separately from class error, including the zero
state count. Raw arms emit `m[predicted_class(x)]*x`; report their orbit
equivariance failures without treating them as oracle failures.
This action control proves the canonicalize/decide/inverse-transform path
only for the stabilizer-compatible scalar action family above; do not
generalize it to arbitrary equivariant policies.

For each `(fold,arm,K)`, record representative-weighted and state-weighted
error, per-class confusion, prototype bits, exact BMU distance evaluations
in training and inference, coordinate update counts, and mean/median
runner-up gap. Aggregate five folds using exact integer counts or rational
fractions. The primary curve is representative-weighted decision error
versus `18*K` codebook bits; plot or table all points without selecting a
favorable budget after seeing results. Report state-weighted error beside
it. Report the direct norm-threshold control separately with zero prototypes,
zero decision error, and its explicit arithmetic/comparison operations;
do not imply that its implementation costs zero hardware bits. Compare arms
at matched `K` and at the smallest `K` achieving each observed error level;
do not set an arbitrary compression target.

## 5. Command and evidence gate

After P0 gate pass and pre-execution review, run a focused implementation
check and then the frozen P1 command through a fresh output path:

```bash
python3 -m py_compile software/tests/d4_decision_p1.py \
  software/tests/test_d4_canonical_decision_p1.py
python3 software/tests/test_d4_canonical_decision_p1.py \
  --output build/d4_canonical_decision_p1/exact_01.json
git diff --check
```

The test must refuse to overwrite evidence, print one `PASS`/`FAIL`, and
record the source revision and dirty status, exact task/split assertions,
all six arms' capacity curves and action controls, and a machine-readable
configuration. If runtime is expected above 60 seconds, freeze a one-attempt
timeout and cumulative budget and use `tools/run_detached_job.sh`. A
repository-wide gate requires its own bounded attempt. No P1 result may be
described as a silicon, SOM-node-compression, or hardware-cost result.

**Execution preflight (2026-09-29):** P0 repository gate has exactly one
`COMPLETE` marker with exit 0. The fresh P0 oracle at
`build/d4_canonical_decision_p0/p1_preflight_01.json` passed. Python compile,
`git diff --check`, exact 57-representative/5-fold/class-count checks, exact
ties-to-even edge cases, and a focused fold-0, `K=1` pass for all six arms
passed. A fold-0 `K=32` augmented raw SOM smoke also completed 393 held-out
states and 75,456 exact equivariance comparisons. No full P1 result has
been produced.

Freeze one full P1 detached attempt, 1,800 seconds per attempt and cumulative.
The attempt is consumed on any outcome. Do not retry, change the task/split,
or extend the timeout without renewed owner authorization. Run:

```bash
tools/run_detached_job.sh \
  --output build/d4_canonical_decision_p1/full_run_01 \
  --timeout 1800 --notify-desktop -- \
  python3 software/tests/test_d4_canonical_decision_p1.py \
    --output build/d4_canonical_decision_p1/exact_01.json
```

Inspect only exactly one terminal marker and `result.json` in a later
session. A `COMPLETE` marker must be paired with the P1 evidence verdict and
independent audit of the capacity curves before interpretation.

**P1 exact result (2026-09-29): PASS.** The sole detached attempt has exactly
one `COMPLETE` marker and exit 0 after 119 seconds at
`build/d4_canonical_decision_p1/full_run_01`. The evidence
`build/d4_canonical_decision_p1/exact_01.json` has SHA-256
`5e54191ab0ed52d1d6c1ab1dfc28fb6c560515e3352ff2ff447c75d2e14e556f`.
An independent evidence audit recomputed the aggregate errors from 180 fold
rows, checked 36 `(arm,K)` points, 3,281 held-out states and 57
representatives per point, `18*K` bit accounting, and 629,952 equivariance
comparisons per point. All canonical arms had zero equivariance failures.

Representative-weighted held-out decision error, rounded for this table
(exact rational values remain in the JSON):

| Arm | K=1 | K=2 | K=4 | K=8 | K=16 | K=32 |
|---|---:|---:|---:|---:|---:|---:|
| Canonical SOM | 57.9% | 57.9% | 57.9% | 29.8% | 35.1% | 22.8% |
| Canonical codebook | 57.9% | 43.9% | 35.1% | 36.8% | 35.1% | 28.1% |
| Raw SOM | 57.9% | 57.9% | 57.9% | 59.3% | 48.4% | 46.8% |
| Augmented raw SOM | 57.9% | 57.9% | 57.9% | 54.8% | 53.3% | 44.6% |
| Raw codebook | 57.9% | 58.5% | 62.3% | 59.0% | 49.0% | 39.7% |
| Augmented raw codebook | 57.9% | 57.9% | 57.9% | 59.9% | 53.8% | 47.8% |

The best tested learned point is canonical SOM at `K=32` (576 stored
codebook bits), 13/57 representative-weighted error. At that same capacity,
canonical codebook is 16/57, raw codebook is about 39.7%, and augmented raw
SOM is about 44.6%. The direct norm-threshold control has zero error with
zero prototypes; it has arithmetic/comparison cost and prevents a general
hardware or SOM-compression claim from this synthetic task. Canonical SOM is
not consistently ahead of canonical codebook across capacities. The action
path was exactly equivariant for the tested stabilizer-compatible scalar
family; action correctness still follows decision correctness except at the
zero state. No off-lattice, P2, E8, or silicon claim follows from this run.

Repository-integration preflight: Python compile and `git diff --check` pass;
the P1 exact evidence is durable and the fresh gate evidence path is absent.
Freeze one repository-gate attempt at 1,800 seconds per attempt and
cumulative. The attempt is consumed on any outcome; no retry or timeout
extension is authorized. Run:

```bash
tools/run_detached_job.sh \
  --output build/d4_canonical_decision_p1/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Interpret only a durable terminal marker and `result.json` in a later
session. The repository gate does not replace the standalone P1 exact
experiment; `run_all_tests.py` does not currently invoke it.

**Repository-gate result (2026-09-29): PASS.** The sole detached attempt at
`build/d4_canonical_decision_p1/repo_gate/run_01` has exactly one terminal
marker, `COMPLETE`, and `result.json` reports exit 0 after 880 seconds. The
frozen attempt is consumed. The standalone P1 exact evidence above remains
the basis for the capacity and equivariance findings.

## 6. Stop and follow-on boundary

Any leakage across base representatives, nonexact group/action identity,
floating-point update, or mismatch between logged and recomputed metrics is
`FAIL`. A model with worse decision error is a valid experimental result,
not a reason to alter the label or split. An off-lattice noisy branch with
explicit `Q_D4` is a separately frozen P1b. P2 RTL and E8 remain separate
decisions after P1 evidence.
