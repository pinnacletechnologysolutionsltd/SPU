# INA226 coarse anomaly monitor v1 contract

Date frozen: 2026-07-19

## Status and question

This contract was frozen before an INA226 was available and before any
physical capture was ingested or scored. Its machine-readable source of truth
is `software/datasets/ina226_coarse_monitor_v1.json`.

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
