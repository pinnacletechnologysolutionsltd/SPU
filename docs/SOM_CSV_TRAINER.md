# Deterministic SOM CSV trainer

Date: 2026-07-17

`tools/train_som_csv.py` is the product entry point for converting a labeled
CSV dataset into a validated `SPU_SOM_MAP_V1` artifact. It uses only the Python
standard library and integer arithmetic. No NumPy, scikit-learn, or floating
point is required in the training path.

## Product boundary

The v1 trainer deliberately matches the current hardware sidecar:

- exactly four numeric feature columns;
- exactly seven SOM nodes;
- one to seven categorical classes;
- signed 18-bit prototype coefficients;
- `Q(sqrt(3))` feature and prototype records, with CSV inputs quantized onto
  the rational `P` lane and `Q=0`;
- the published 40-epoch dyadic update schedule.

This is a generalized dataset entry point, not a variable-shape ML framework.
Changing node count, feature count, coefficient width, or schedule requires a
new artifact/RTL contract rather than an undocumented CLI switch.

## Header-based example

For a CSV with columns `current,ripple,slope,variance,state`:

```bash
python3 tools/train_som_csv.py motor.csv \
  --output motor_som_v1.json \
  --header \
  --features current,ripple,slope,variance \
  --label state \
  --scale 1000 \
  --model motor-current-som-v1 \
  --dataset-name "motor current signatures"
```

Without `--header`, column selectors are zero-based indices and default to
features `0,1,2,3` plus label `4`. Use `--feature-names` to give index-selected
features stable semantic names.

The artifact stores the CSV filename as its logical `dataset_path` by default,
so the same data produces the same map when trained in different directories.
Use `--dataset-path` to record a stable repository-relative or catalog path.

The scale must be a power of ten. Every input decimal must be exactly
representable at that scale: for example, `1.23` is accepted at scale 100 but
`1.234` is rejected. The trainer never silently rounds or truncates a feature.

## Determinism and labeling

Class names are sorted lexicographically and assigned stable integer labels.
Initialization is mean-nearest followed by deterministic farthest-first
selection. Every epoch order is the SHA-256 ordering of
`model:order_seed:epoch:row_index`; the model identifier is therefore part of
the replay contract. Winner and neighbor updates are signed dyadic shifts.

After training, each node receives the majority class of its assigned samples,
with the lowest class id breaking equal vote counts. The output records the
dataset SHA-256, full schedule, initial sample indices, class/feature names,
prototype values, and map SHA-256.

The checked Iris model remains bit-identical after extraction into this shared
trainer: map SHA-256
`3373e851c29450e37fca76281f9ea4dbbdf1b94b34cf1b7bd74f6d83fe8eaa15`.

## Validate and upload

The CLI writes the artifact and immediately reloads it through the strict map
validator. A successful final line begins `SOM_CSV_TRAIN: PASS`.

Upload all 28 prototypes and seven semantic labels with:

```bash
python3 tools/upload_som_weights.py motor_som_v1.json --port /dev/ttyACM0
```

The uploader refuses an artifact whose dataset/map checksum, dimensions,
training schedule, coefficient range, labels, or required metadata are
invalid. Hardware classification evidence is then read through the `SOM1`
result frame described in `docs/SOM1_RESULT_FRAME.md`.
