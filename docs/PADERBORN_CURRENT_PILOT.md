# Paderborn current-signature pilot

## Status

The first leakage-safe public-data pilot is reproducible and deliberately does
**not** support a bearing-classification product claim. The current four
time-domain features fit individual training bearings, but do not generalize
reliably to unseen physical bearings.

This is a useful truth gate. A random window split would mix recordings from
the same bearing between training and test and conceal this failure mode.

## Source and license

The source is the [Paderborn University Bearing Data Center](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter/data-sets-and-download),
cited as Lessmeier et al., PHM Society European Conference 2016,
DOI `10.36001/phme.2016.v3i1.1577`.

The corpus is licensed CC BY-NC 4.0. Commercial use requires separate
permission from the authors. Source archives, extracted recordings, feature
CSVs, and trained derivative maps are therefore generated below `build/` and
are not committed under the repository's source-code license.

The checked manifest is
`software/datasets/paderborn_current_pilot_v1.json`. It records source URLs,
archive SHA-256 checksums, citation, license, operating condition, and the
physical-bearing split.

## Frozen pilot

The pilot uses the `N15_M07_F10` condition: 1500 rpm, 0.7 Nm load torque,
and 1000 N radial force. It contains 20 four-second recordings from each of
nine bearings:

| Split | Healthy | Inner-race damage | Outer-race damage |
|---|---|---|---|
| Train | K001 | KI04 | KA04 |
| Validation | K002 | KI14 | KA15 |
| Test | K003 | KI16 | KA16 |

Every split therefore contains different physical hardware. The pilot is a
domain-shift detector, not a statistically sufficient product evaluation:
each class has only one bearing in each split.

## Exact import boundary

`software/lib/matlab_v5.py` is a dependency-free reader for the MATLAB v5
numeric, character, cell, and structure records used by this corpus.
`software/lib/paderborn_bearing.py` selects the two currents by their recorded
names (`phase_current_1` and `phase_current_2`), never by array position.

The calibrated binary64 values cross into the deterministic pipeline once:

1. each value's exact binary integer ratio is recovered;
2. amperes are multiplied by 1,000,000;
3. the rational result is rounded to integer microamps, ties to even;
4. all feature, normalization, baseline, SOM-training, and scoring operations
   after that point use integers only.

The unmeasured third phase is reconstructed as `-(phase_1 + phase_2)`.

## Feature profiles

The two time-domain profiles emit mean absolute current, peak-to-peak current,
mean absolute successive difference, and mean absolute deviation:

- `native64k`: non-overlapping 4096-sample, three-phase windows at the source
  rate (62 windows per recording);
- `envelope100`: exact mean-absolute envelope aggregation over 640 source
  samples, then non-overlapping 32-value windows (12 windows per recording).

The follow-up `periodic64k` profile uses 12,800-sample windows and four
dimensionless integer-ppm features: carrier half-cycle anti-residual, carrier
cycle residual, shaft-cycle residual, and carrier-cycle envelope deviation.
The corpus trace pins a 640-sample (100 Hz) current carrier and a 2,560-sample
(25 Hz) shaft period. No FFT, floating-point coefficient, or transcendental
approximation enters these lag identities.

`envelope100` is a 100 Hz envelope experiment, not an assertion that a 100 Hz
INA226 can recover the same information. The block statistics require access
to the original high-rate phase current.

Each lane is mapped to 0..30000 from training-only minima and maxima. Values
outside the training range are clipped and counted. No validation or test
statistic influences the scaler or model.

## Pilot result

Accuracy is by window, but bearing identity is held out in its entirety.
The threshold baseline is binary healthy/damaged. Centroid and SOM results are
the harder healthy/inner/outer task.

| Profile / split | Threshold binary | Centroid 3-class | 7-node SOM 3-class |
|---|---:|---:|---:|
| 64 kHz train | 79.09% | 96.77% | 95.35% |
| 64 kHz validation | 6.64% | 0.00% | 0.00% |
| 64 kHz test | 30.59% | 56.88% | 58.94% |
| 100 Hz envelope train | 67.64% | 91.39% | 84.31% |
| 100 Hz envelope validation | 62.76% | 0.00% | 3.49% |
| 100 Hz envelope test | 63.18% | 51.60% | 43.24% |
| Periodic 64 kHz train | 99.25% | 98.92% | 97.83% |
| Periodic 64 kHz validation | 32.89% | 31.46% | 31.55% |
| Periodic 64 kHz test | 33.47% | 36.90% | 41.76% |

At 64 kHz, validation clips 6,334 feature values and test clips 3,187. At
100 Hz envelope rate the corresponding counts are 426 and 74. The confusion
matrices show complete class swaps on the validation bearings, rather than a
small decision-boundary loss. The result is dominated by physical-bearing
domain shift and insufficient features/training identities.

The follow-up diagnostic also runs the same trained model with an unclamped
software affine projection. Native validation remains 0.00%, envelope
validation falls from 3.49% to 2.51%, and periodic validation changes only
from 31.55% to 31.46%. Native validation retains 3,547 unique vectors and no
vector has all four lanes clamped. Clamping concentrates winners but is not
the root cause.

The seven-node SOM is not the limiting platform resource here. It reproduces
the model it was given; the model lacks a bearing-invariant representation.
The larger 15-bearing result is recorded in
`docs/PADERBORN_CURRENT_CROSS_VALIDATION.md`.

## Reproduction

Place the nine official archives named in the manifest under
`build/paderborn_raw/`, then verify them:

```sh
python3 tools/paderborn_benchmark.py verify \
  --archive-root build/paderborn_raw
```

Extract only `N15_M07_F10_<bearing>_*.mat` from each archive under
`build/paderborn_raw/extracted/<bearing>/`, then run:

```sh
python3 tools/paderborn_benchmark.py benchmark \
  --mat-root build/paderborn_raw/extracted \
  --output build/paderborn_benchmark
```

The output includes full and training-only normalized feature CSVs, three
validated `SPU_SOM_MAP_V1` maps, full confusion matrices, per-bearing winner
histograms, directional range diagnostics, clamped-versus-unclamped scores,
source hashes, and `paderborn_benchmark_v1.json`. Each map's dataset hash names
its training-only CSV; validation and test rows are not part of that hash.

Focused offline truth gates are:

```sh
python3 software/tests/test_matlab_v5.py
python3 software/tests/test_paderborn_bearing.py
```

## Decision and next experiment

Do not tune the seven-node SOM against these held-out scores. The next useful
experiment is upstream of it:

1. expand to the paper's 15-bearing real-damage subset and use five
   bearing-level folds (four identities per class for training, one for test);
2. add deterministic periodic-residual or integer sideband-energy features
   tied to the known 50 Hz electrical and 25 Hz shaft periods;
3. select the feature contract using fold-level validation, then freeze it
   before a final held-out score;
4. only after the software model generalizes, replay its validated map through
   the already proven SOM1 hardware path.

For physical acquisition, INA226 remains appropriate for the coarse
load/stall/current-envelope anomaly demo. It should not be presented as a
64 kHz bearing-fault phase-current front end. If the high-rate periodic
features prove necessary, that path needs a suitable current transformer or
Hall front end and simultaneous ADC acquisition; the SOM sidecar itself does
not need to change.
