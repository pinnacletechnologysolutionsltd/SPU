# Paderborn current-only cross-validation

## Verdict

The 15-bearing, five-fold result does not support a current-only bearing-fault
classifier with the present four-feature profiles. This is a feature/data
representation result, not an FPGA-capacity or SOM arithmetic limitation.

The strongest finding is negative but actionable: absolute time-domain
features, a 100 Hz envelope, and exact carrier/shaft lag residuals all fail to
separate unseen physical bearings reliably. Uploading any resulting map to the
already proven SOM1 sidecar would reproduce a poor model exactly; it would not
improve it.

## Dataset contract

The machine-readable contract is
`software/datasets/paderborn_current_cv_v1.json`. It pins the official source
archives, all 15 SHA-256 checksums, citation, CC BY-NC 4.0 boundary, one
operating condition, and five folds.

The subset follows the real-damage bearing selection used by the Paderborn
benchmark paper:

| Fold | Healthy | Inner-race damage | Outer-race damage |
|---:|---|---|---|
| 0 | K001 | KI04 | KA04 |
| 1 | K002 | KI14 | KA15 |
| 2 | K003 | KI16 | KA16 |
| 3 | K004 | KI18 | KA22 |
| 4 | K005 | KI21 | KA30 |

Each fold trains on the other twelve bearings and tests on the three listed
physical bearings. Every recording/window from a bearing remains in the same
fold. There is no window-level or recording-level identity leakage.

Only `N15_M07_F10` is used: nominally 1500 rpm, 0.7 Nm, and 1000 N, with 20
four-second recordings per bearing. The importer selects the two named
phase-current channels, converts binary64 amperes exactly to integer
microamps, and remains integer-only afterward.

## Feature contracts

- `native64k`: four absolute time-domain statistics over 4096 source samples;
- `envelope100`: four statistics over an exact 100 Hz mean-absolute envelope;
- `periodic64k`: four dimensionless ppm residuals over 12,800 samples.

The periodic profile uses the observed 640-sample current-carrier period and
2,560-sample shaft period. Its lanes are:

1. half-carrier anti-residual, `|x[n] + x[n-320]|`;
2. carrier-cycle residual, `|x[n] - x[n-640]|`;
3. shaft-cycle residual, `|x[n] - x[n-2560]|`;
4. carrier-cycle envelope deviation.

Each residual is divided by the same window's mean absolute three-phase
current and rounded to integer ppm, ties to even. This removes gross current
gain while preserving an auditable, multiplier/divider-friendly definition.
There are no FFT twiddles or floating-point spectral coefficients.

## Five-fold result

The binary threshold task is healthy versus damaged. Its majority-class
baseline is 66.55% because two of three bearings are damaged. Centroid and SOM
are three-class tasks with a 33.45% majority baseline. Balanced accuracy gives
each true class equal weight.

| Profile / model | Accuracy | Balanced accuracy | Majority baseline |
|---|---:|---:|---:|
| Native threshold, binary | 49.22% | 37.51% | 66.55% |
| Native centroid, 3-class | 33.05% | 33.12% | 33.45% |
| Native SOM, 3-class | 25.44% | 25.46% | 33.45% |
| Envelope threshold, binary | 53.43% | 45.20% | 66.56% |
| Envelope centroid, 3-class | 34.42% | 34.48% | 33.44% |
| Envelope SOM, 3-class | 35.48% | 35.49% | 33.44% |
| Periodic threshold, binary | 60.72% | 45.76% | 66.56% |
| Periodic centroid, 3-class | 15.90% | 15.93% | 33.44% |
| Periodic SOM, 3-class | 32.06% | 32.04% | 33.44% |

The best nominal SOM result, envelope at 35.48%, is only about two percentage
points above the class baseline and is not balanced across faults. Per-class
recall is 53.58% healthy, **4.18% inner**, and 48.70% outer. The periodic
threshold's 60.72% is below an always-damaged alarm and has only 0.60% healthy
recall. Neither is operationally useful.

Fold variance is also extreme. Envelope SOM ranges from 11.02% to 49.09%; the
periodic SOM ranges from 8.33% to 49.24%. Individual bearings still reach 0%
recall in several folds, confirming identity/domain sensitivity.

## Clamping diagnosis

Every fold records:

- low/high out-of-training-range counts for every feature;
- diagnostics by split and physical bearing;
- raw and normalized unique-vector counts;
- vectors with one or all lanes clipped;
- unclamped affine values outside signed P18;
- winner-node and winner-label histograms by split and bearing;
- the same classifier evaluated with clamping disabled in software.

Across all three profiles and all five folds, clamped and unclamped SOM test
accuracy is identical. No fold loses a unique feature vector through
normalization. Clipping exists, but the wider twelve-bearing training range
makes it non-causal for these failures. This supersedes the single-point
collapse hypothesis from the nine-bearing pilot.

## Reproduction

Keep the source archives and derived data under ignored `build/` because the
source corpus is CC BY-NC 4.0. Verify the archives and run:

```sh
python3 tools/paderborn_cross_validate.py verify \
  --archive-root build/paderborn_raw

python3 tools/paderborn_cross_validate.py run \
  --mat-root build/paderborn_raw/extracted \
  --output build/paderborn_cross_validation
```

The output contains five validated `SPU_SOM_MAP_V1` artifacts per profile,
training-only hashes, full confusion matrices, balanced metrics, range/node
diagnostics, and `paderborn_cross_validation_v1.json`.

## Engineering decision

Stop tuning the seven-node map against this feature set. The next research
step, if current-based bearing diagnosis remains strategically important, is a
predeclared deterministic current-spectrum front end evaluated against the
same folds—such as fixed-bin integer correlations or an integer filter bank at
published motor-current sidebands. It must beat both the majority alarm and a
simple conventional baseline before any FPGA replay or product wording.

INA226 remains useful for the original coarse current/load/stall anomaly
monitor. It is not a 64 kHz phase-current acquisition path and should not be
conflated with this bearing benchmark. A successful high-rate feature contract
would require an appropriate isolated current/Hall front end and ADC, while
the existing SOM1 inference ABI can remain unchanged.
