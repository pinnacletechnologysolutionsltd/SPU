# Hydraulic pump SOM case study

Date frozen: 2026-07-19

## Status

This is a predeclared real-data truth gate for the SPU-13 SOM sidecar. No
classifier score had been calculated when the task, features, folds, and claim
gates in this document and
`software/datasets/hydraulic_pump_som_v1.json` were frozen.

The study asks one narrow question: can the existing seven-node deterministic
SOM distinguish no, weak, and severe internal pump leakage from a single
100 Hz motor-power channel while generalizing across held-out combinations of
the other test-rig conditions?

It does not claim cross-machine generalization. The source contains one
physical hydraulic test rig. It also does not alter the SOM v1 training
schedule, RTL, map format, or SOM1 result ABI.

## Source and licence

The source is the UCI Machine Learning Repository dataset **Condition
monitoring of hydraulic systems**, created by Nikolai Helwig, Eliseo
Pignanelli, and Andreas Schuetze:

- DOI: `10.24432/C5CW21`
- record: <https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems>
- licence: CC BY 4.0

Raw data is downloaded on demand into `build/` and is not committed. The
manifest pins the archive and the two consumed source files by SHA-256. Derived
feature files and maps remain build artifacts unless a later publication
explicitly packages them with attribution under compatible terms.

## Frozen task

Only cycles with `stable_flag == 0` are accepted. The target is profile column
3, internal pump leakage:

| Source value | Class |
|---:|---|
| 0 | `no_leakage` |
| 1 | `weak_leakage` |
| 2 | `severe_leakage` |

The input is `EPS1.txt`, motor power in watts sampled at 100 Hz for 60 seconds
per cycle. Decimal source tokens are parsed exactly into integer deciwatts;
binary floating point is not used.

Each cycle contributes 16 fixed 32-sample windows. Window `i` starts at
`floor(i * (6000 - 32) / 15)`, so the complete operating cycle is sampled
without choosing phases after looking at results.

Every window produces the same four auditable temporal statistics planned for
the INA226 monitor, expressed here in deciwatts:

1. round-half-even mean;
2. peak-to-peak range;
3. round-half-even mean absolute successive difference;
4. round-half-even mean absolute deviation from the exact rational mean.

## Leakage-safe folds

A nuisance group is the tuple `(cooler condition, valve condition,
accumulator pressure)`. All pump labels and repeated cycles for one nuisance
tuple stay in one fold. A test fold therefore contains operating-condition
combinations that the trainer never sees.

Groups are ordered by SHA-256 of
`hydraulic-pump-v1:<cooler>:<valve>:<accumulator>` and assigned round-robin to
five folds. This makes the split deterministic without giving chronological or
lexicographic structure special treatment.

Normalization is fitted from training windows only. Each lane is mapped to
`0..30000` by an exact round-half-even affine transform. Held-out values are
clamped only at the declared Cartesian/SOM boundary, with low/high and vector
collapse diagnostics recorded.

The scored unit is a complete physical cycle, not a window. Threshold,
centroid, and SOM window predictions are reduced by plurality over the 16
windows; an exact vote tie retains the lower class id.

## Baselines and claim gates

The report must include:

- majority-class accuracy;
- one training-fitted scalar threshold for no-leakage versus leakage;
- three-class nearest centroid;
- seven-node SOM;
- collapsed binary SOM versus the threshold;
- fold and aggregate confusion matrices, balanced accuracy, range diagnostics,
  map hashes, and exact-tie counts.

Hardware replay is eligible only if aggregate three-class SOM balanced
accuracy is at least 70% and the worst fold is at least 50%.

An accuracy-superiority statement is permitted only if the SOM exceeds the
three-class centroid and its collapsed binary decision exceeds the scalar
threshold. Passing the replay gate does not imply passing the superiority
gate.

If either gate fails, the result is recorded as a negative. The frozen folds,
features, and thresholds must not be tuned against held-out scores. A new
feature hypothesis requires a versioned follow-up contract.

## Relationship to existing evidence

The synthetic current replay already proves the integer feature → Cartesian
bridge → SOM → SOM1 software ABI. Iris already proves complete software/FPGA
equivalence on Tang and Artix hardware. This case study tests real-signal
generalization only. It cannot invalidate or strengthen those hardware proofs;
it determines whether a real map is worth replaying through the already-proven
sidecar.
