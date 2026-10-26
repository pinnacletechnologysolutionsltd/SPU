# Soul-0 Arithmetic and Memory Policy Study

**Date:** 2026-10-14
**Contract ID:** `contract_soul0_arithmetic_memory_2026-10-14.md`
**Status:** FROZEN SPECIFICATION — experiment launch budget is not authorized

## Commands

```bash
python3 -m unittest software.tests.test_soul0_arithmetic -v
python3 -m software.research.soul0.arithmetic_study --out build/research/soul0/arithmetic_memory_01
git diff --check -- software/research/soul0/arithmetic.py software/research/soul0/arithmetic_study.py software/research/soul0/arithmetic_fixtures_v1.json software/research/soul0/arithmetic_manifest_v1.json software/tests/test_soul0_arithmetic.py spu_strategy/contract_soul0_arithmetic_memory_2026-10-14.md
```

The unit-test command is permitted during implementation. The experiment command
is **not authorized until the owner freezes an attempt count, per-attempt wall
clock timeout, and cumulative campaign budget**. Do not infer that budget from
earlier Soul-0 campaigns. Its output directory must not exist at launch.

## Objective and scope

Answer two separate questions:

1. **Arithmetic precision:** does retaining fractional information remove the
   floor-update center stall, with independent exact-rational verification?
2. **Memory policy:** after a real regime change, which policy adapts while
   retaining useful behavior on returning regimes?

This is a synthetic, software-only study. The original Soul-0 experiments,
their fixtures, models, result files, hashes, and claims are immutable evidence.
Do not change the live Soul-0 update rule. Do not add SOM, Whisper, RTL, FPGA,
hardware behavior, or physical sensor data to this study.

Target files:

- `software/research/soul0/arithmetic.py`
- `software/research/soul0/arithmetic_study.py`
- `software/research/soul0/arithmetic_fixtures_v1.json`
- `software/research/soul0/arithmetic_manifest_v1.json`
- `software/tests/test_soul0_arithmetic.py`
- `spu_strategy/contract_soul0_arithmetic_memory_2026-10-14.md`

## Frozen model definitions

All models receive the same signed integer observations, threshold 20, and
pre-update alert decision. An alert is `true` only when the represented
absolute residual is **strictly greater than** the threshold. Each model then
updates its memory on every observation, including alerting observations. No
model may suppress updates based on its own alert.

| ID | State and update | Alert residual |
|---|---|---|
| A — Original | Integer center `c`, count `n`; `c' = floor((c*n+x)/(n+1))`, `n'=n+1` | `abs(x-c)` |
| B — Exact | Integer sum `S`, count `n`; `S'=S+x`, `n'=n+1`; center is rational `S/n` | `abs(x*n-S)/n` |
| C — Remainder | Integer floor center `c`, count `n`, remainder `r`; maintain `S=c*n+r`, `0<=r<n`; compute `(c',r')=divmod(c*n+r+x,n+1)`, `n'=n+1` | `abs(x*n-(c*n+r))/n` |
| D — Fixed-point | Q8 center `q`; initialize `q=floor(256*S/n)`; `q'=floor((q*n+256*x)/(n+1))`, `n'=n+1` | `abs(256*x-q)/256` |
| E — Rolling | Exact sum of the latest eight observations; append new value and evict oldest | `abs(8*x-sum(window))/8` |
| F — Forgetting | Q8 center `q`; initialize as D; `q'=floor((7*q+256*x)/8)` | `abs(256*x-q)/256` |

All divisions use mathematical floor, including negative numerators. This is
the tie and signed-rounding rule. B and C must represent the same exact
rational mean after every update. D is a quantized cumulative mean; F is a
deterministic EWMA with alpha `1/8`. Neither may be relabeled as exact.

Logical state uses byte-rounded fields at the minimum widths derived below:
A 4 bytes, B 5, C 6, D 5, E 16, F 3. Checkpoint byte counts are reported
separately from these logical in-memory widths.

Initialize A–D and F from training values `[98,99,100,101,102,98,99,100]`;
initialize E with the same eight values as its full window. For arithmetic
diagnostics, also initialize A–D from `(center=180,count=2)`; B uses
`sum=360,count=2`, C uses `(180,2,0)`, and D uses Q8 center `46080`, count 2.

## Frozen input streams

Freeze `arithmetic_fixtures_v1.json` with these generator parameters and hash
it in `arithmetic_manifest_v1.json` before evaluation:

- Input domain: signed integers `[-256,511]`.
- Threshold: 20. Noise cycle: `[-2,-1,0,1,2]`, restarted at index zero for
  each phase.
- Training: `[98,99,100,101,102,98,99,100]`.
- Adaptation phases, in order: B at center 200 for 64 samples, C at center 150
  for 64, returning A at center 100 for 64, returning B at center 200 for 64.
  Values are nominal center plus the noise cycle; there are no injected faults
  in this stream.
- Alert phases: use the existing v1 noise and +140 transient pattern (fault at
  index 10) for centers 100, 200, 150, 100, and 200, but store the expanded
  samples in this study's own fixture. Alert-phase clones start from the
  trained state and process the same ordered phases independently.
- Arithmetic regression: from the `(180,count=2)` seed, process 16 healthy
  center-200 samples with the same noise cycle.

Frozen artifact hashes:

| Artifact | SHA-256 |
|---|---|
| `software/research/soul0/arithmetic_fixtures_v1.json` | `2f740a49674fee8f1727f045fc1162bf880e5bcd4b838a09f65723b7f0a21d87` |
| `software/research/soul0/arithmetic_manifest_v1.json` | `1495538044e6f5f93b76cae9d1f550fb486ae5bf345cdeb64795f11c647a46bd` |
| `software/research/soul0/arithmetic.py` | `b1be48865f1302b4e5e3e4d2904e55a435c7d223674c93c41868c05998c9c48c` |
| `software/research/soul0/arithmetic_study.py` | `f4c604f3a328e4f13e2a9e2405c6ccfe1a65708ce94805a90bc9b0b548af036c` |
| `software/tests/test_soul0_arithmetic.py` | `8ff35a75854705a393eab503f002ec2e6e30d0c6ccb6ed6b22494e4d7b17e5b6` |

The evaluator must consume fixture values rather than regenerate them from
mutable runtime defaults. Source and fixture hashes must be checked before
running. Never modify the existing `heldout_fixtures_v1.json`.

## Measurements and verdicts

Report each variant independently; do not combine metrics into a score.

- **Arithmetic:** center and absolute error after every regression observation
  against an independent `fractions.Fraction` oracle; first index with a
  different result from A; B/C equality on all transitions.
- **Adaptation:** per-sample center error from the current nominal regime and
  adaptation lag. Lag is the first index at which error is at most 5 for three
  consecutive observations; report `null` if not reached in that phase.
- **Adaptation comparison:** compute exact pooled mean absolute center error
  over all post-update samples in B and C. Adaptation improvement passes only
  if at least one of A–D is strictly lower than both E and F. Report each
  variant's exact rational pooled metric; do not use a composite score.
- **Retention:** same error and lag measures on each returning regime.
  Report exact pooled mean absolute center error over A-return and B-return;
  this study assigns no standalone retention pass threshold.
- **Alerts:** healthy false alerts per phase; transient detections and delay
  (samples from fault arrival to first alert, or missed at arrival). Report both healthy
  adaptation and isolated alert-phase results; do not infer cross-regime fault
  discrimination from out-of-range transient detection.
- **Persistence:** canonical checkpoint byte count; save/restore must produce
  byte-identical future decisions and state on the remaining frozen input.
- **State/cost:** logical state bytes, executed primitive operation counts per
  phase, and required integer widths per state and intermediate expression.
  Count each executed add, subtract, multiply, absolute value, floor division,
  comparison, and modulo once at its source operation. Exclude indexing,
  iteration, allocation, serialization, and Python runtime overhead.
- **Invalid states:** reject truncated or malformed checkpoints, negative or
  zero counts, out-of-range inputs, and inconsistent C remainder state. No
  saturation is permitted; reject before state mutation. Demonstrate that a
  failed checkpoint restore leaves the live model unchanged.

Bound analysis must cover the fixture's maximum 264-observation cumulative
history and declared input domain. Report signed width for each state and
intermediate; do not claim hardware suitability from Python measurements.

## Required gates

1. Exhaustively compare one-step C and B transitions for every valid state
   center in `[-4,4]`, count in `[1,4]`, remainder in `[0,count-1]`, and input
   in `[-4,4]`, retaining only states with `-4*n<=c*n+r<=4*n`. Check
   `S=c*n+r`, alert equality, next state equality, and `0<=r<n`, including
   negative numerators and residuals. This exhaustive transition invariant establishes sequence
   correspondence by induction; also check both full frozen streams against
   the independent Fraction oracle.
2. Verify B and C match the independent Fraction oracle after every transition
   in the full four-phase adaptation stream, the five-phase alert stream, and
   the `(180,count=2)` arithmetic regression.
3. Preserve A's observed center-193 stall on the 16-sample regression and
   report it; this is a characterization gate, not a recovery claim.
4. Report adaptation, return-regime retention, false alerts, transient
   detections/delay, state bytes, checkpoint bytes, operation counts, and
   integer widths for all applicable variants. Do not set a winner threshold
   after observing results.
5. Verify save/restore replay and malformed-checkpoint rejection for all six
   variants.
6. Verify deterministic canonical output across two in-process evaluations,
   excluding only latency fields. Latency is descriptive and is not an
   acceptance gate.

Arithmetic correction, adaptation improvement, retention, and implementation
suitability receive separate verdicts. Arithmetic correction requires B and C
to match the exact oracle and avoid A's quantized stall on the regression.
Adaptation improvement uses the pooled-error criterion above against E and F;
no variant is presumed superior. Retention is reported independently without
a pass threshold. Suitability requires bounded state, rejection of invalid
input/state, deterministic persistence, and complete cost/width accounting.

## Execution and stop rules

1. Implement the frozen definitions and fixture; calculate and record hashes.
2. Run `python3 -m unittest software.tests.test_soul0_arithmetic -v`.
3. Stop on any test failure or B/C/oracle disagreement.
4. Do not run the study until the owner authorizes an explicit campaign budget.
   On authorization, update this contract with maximum attempts, per-attempt
   timeout, cumulative budget, and the exact output directory before launch.
5. A launched attempt consumes one authorized slot even if it fails, times
   out, or becomes unavailable. Do not retry, tune, or extend the budget
   without renewed authorization.
6. After an authorized study run, run the exact `git diff --check` command
   above. No full hardware or repository regression applies to this isolated
   software-research scope.

No product, hardware, silicon, or general adaptation advantage is claimed by
this contract.
