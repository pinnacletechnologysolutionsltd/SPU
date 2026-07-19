# Synthetic current-signature SOM1 replay

Date: 2026-07-17

`tools/som_sensor_replay.py` is the hardware-independent acceptance path for
the current-signature anomaly monitor. It proves the software chain before an
INA226 is attached:

```text
integer current trace
  -> deterministic temporal window features
  -> Cartesian P16/Q16 scalar boundary
  -> explicit sign extension to SOM P18/Q18
  -> exact rational BMU
  -> 52-byte CRC-protected SOM1 evidence frame
  -> strict host parser
```

This is synthetic replay evidence. It does not claim physical sensor accuracy,
RP2350 acquisition timing, or renewed Tang silicon proof.

## Trace and window contract

The generator produces 32 current samples at 100 Hz: one 320 ms window. All
samples are integer microamps. Three deterministic regimes are present:

- `normal` — low ripple around 420 mA;
- `bearing_drag` — elevated current, sawtooth ripple, tooth impulses, and a
  within-window upward trend;
- `stall` — high current with large periodic pulses.

The four integer-milliamp features are:

1. round-half-even mean current;
2. round-half-even peak-to-peak current;
3. round-half-even mean absolute successive difference;
4. round-half-even mean absolute deviation from the exact rational mean.

Feature extraction uses integer arithmetic. The mean absolute deviation keeps
`count * sample - total` integral, so it does not first round the mean. The
features then cross the existing Cartesian bridge at scale 1. They are small
exact integers in IEEE-754, incur no boundary rounding or saturation, and have
`Q=0`. `widen_sensor_scalar_to_som18()` pins the required signed P16/Q16 to
P18/Q18 adapter before classification.

## Checked artifacts

- feature CSV: `software/tests/data/synthetic_current_v1.csv`
- trained map: `software/models/synthetic_current_som_v1.json`
- dataset SHA-256:
  `4ed7e02b19c9e6b67116faa3f0d421b3958d3dc4a0098eee304550c44d0fe1ef`
- map SHA-256:
  `66bc408abd8111684c039378d4882aebdd77974e272717556c790eb6d8df2614`

The training set contains 12 windows per class. The holdout replay generates
six different windows per class from case indices 100 through 105; these are
not present in the training CSV.

## Run and regenerate

Validate the checked artifacts and replay the holdout corpus:

```bash
python3 tools/som_sensor_replay.py
```

Expected verdict:

```text
Current replay confusion: [[6, 0, 0], [0, 6, 0], [0, 0, 6]]
SENSOR_REPLAY: PASS windows=18 exact=18/18 ambiguous=0 ...
```

Regenerate the checked CSV and model after an intentional contract change:

```bash
python3 tools/som_sensor_replay.py --emit
```

The test pins both hashes, regenerates both artifacts, replays twice, checks
bit-identical frames, verifies consecutive result generations and stable map
generation, and sends every frame through the production host parser. A model
or generator change therefore requires an explicit golden-artifact update.

## Physical handoff

The INA226 logger already emits integer `current_uA` at 100 Hz. Physical
integration replaces `generate_current_window()` with those samples; the
window size, feature equations, bridge, map uploader, BMU oracle, and SOM1
consumer remain unchanged. The first bench run must separately verify sample
cadence, shunt value, saturation behavior, and FPGA/oracle evidence equality.
The frozen experiment and bench procedure are
`INA226_COARSE_MONITOR_CONTRACT.md` and `INA226_CAPTURE_RUNBOOK.md`.
