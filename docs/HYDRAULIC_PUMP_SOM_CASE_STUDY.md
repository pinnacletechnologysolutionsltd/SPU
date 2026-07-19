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

## Frozen-contract result

The first run and an immediate independent rerun produced byte-identical
`hydraulic_pump_som_result_v1.json` output:

- result SHA-256:
  `010e5155e1a0e33645e73d9359f590709514668df807264598faf8b6616b8c8f`;
- stable physical cycles: 1,449;
- evaluated windows: 23,184;
- held-out nuisance groups: 48 across five folds;
- SOM1 records checked against the exact oracle: 23,184;
- exact-tie/ambiguity windows: 0.

Cycle-level aggregate results are:

| Method | Balanced accuracy | Accuracy | Confusion matrix |
|---|---:|---:|---|
| Majority, 3-class | 33.33% | 33.75% | `[[489,0,0],[480,0,0],[480,0,0]]` |
| Nearest centroid, 3-class | 44.61% | 44.93% | `[[470,5,14],[346,36,98],[279,56,145]]` |
| Seven-node SOM, 3-class | 45.41% | 45.69% | `[[438,0,51],[324,0,156],[256,0,224]]` |
| Scalar threshold, binary | 50.00% | 66.25% | `[[0,489],[0,960]]` |
| SOM collapsed to binary | 64.79% | 56.73% | `[[438,51],[576,384]]` |

The five SOM balanced accuracies are 41.33%, 40.00%, 51.67%, 38.52%,
and 55.56%. Aggregate accuracy therefore fails the predeclared 70% replay
threshold, and the 38.52% worst fold fails the 50% floor.

The literal baseline-superiority predicate is true: 45.41% exceeds the
centroid's 44.61%, and binary SOM 64.79% exceeds the scalar threshold's 50%.
This does not authorize a superiority claim because the hardware-replay gate
fails and absolute three-class performance is weak. The scalar threshold is
also degenerate: it predicts leakage for every cycle.

This is not a normalization-collapse result. Across all held-out folds, only
12 windows clamp any feature, no window clamps all four, and one unique vector
is lost. Every trained map contains at least one weak-leakage node, but cycle
plurality never returns the weak class. The four frozen local statistics of a
single motor-power channel do not separate pump-leakage severity reliably
across unseen cooler/valve/accumulator combinations.

**Decision:** do not promote or replay these maps on FPGA, and do not tune the
v1 features or folds. This negative result does not bear on coarse
normal/load/stall monitoring with the INA226; subtle hydraulic leakage is a
different task. Any follow-up requires a v2 contract declared before scoring,
most plausibly with cycle-phase or multi-sensor features.

## Reproduction

Download the source without adding it to Git:

```sh
mkdir -p build/hydraulic_raw
curl -L --fail -o build/hydraulic_raw/condition_monitoring_hydraulic_systems.zip \
  'https://archive.ics.uci.edu/static/public/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems.zip'
```

Verify and extract only the two consumed files, then run the case study:

```sh
python3 tools/hydraulic_som_case_study.py extract
python3 tools/hydraulic_som_case_study.py verify
python3 tools/hydraulic_som_case_study.py run
```

The final command writes per-fold normalized CSVs, checksummed maps, complete
diagnostics, and `hydraulic_pump_som_result_v1.json` under
`build/hydraulic_pump_som/`. A completed negative gate exits successfully;
`PASS` means the frozen computation was reproduced, not that the accuracy gate
passed.
