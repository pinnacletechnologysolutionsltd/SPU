# INA226 coarse-monitor capture runbook

This is the bench procedure for the frozen contract in
`INA226_COARSE_MONITOR_CONTRACT.md`. Do not collect a physical dataset until
the actuator rating, supply current limit, INA226 shunt marking, and wiring
checks below are complete.

The contract entered Git at commit `ed16263`, before this ingestion code or
any synthetic/physical score existed.

## 1. Prepare the manifest

Choose a low-voltage replaceable fan or motor whose continuous-current rating
is documented and below the INA226/R100 750 mA measurement headroom. The
supply limit must not exceed either that headroom or the continuous rating.

```sh
python3 tools/ina226_capture_pipeline.py init \
  build/ina226_capture/capture_manifest.json \
  --nominal-bus-mv 5000 \
  --probe dc_fan_v1 \
  --actuator-model 'REPLACE_WITH_PART_NUMBER' \
  --actuator-continuous-ma 600 \
  --supply-limit-ma 600
```

Replace every example electrical value with the actuator's real documented
value. `init` refuses a supply limit above the continuous-current rating and
creates the thirty filenames under `build/ina226_capture/captures/`.

## 2. Wire and inspect with all power off

INA226 breadboard wiring:

| INA226 | RP2350/Pico 2 | Purpose |
|---|---|---|
| VCC | 3V3 | sensor logic power |
| GND | GND | common reference |
| SDA | GP8 | I2C0 data |
| SCL | GP9 | I2C0 clock |
| ALERT | GP15 or open | reserved; v1 polls |
| VIN+ | bench-supply positive | high side before shunt |
| VIN- | actuator positive | high side after shunt |

The actuator negative returns directly to bench-supply ground. Do not put an
FPGA board's supply through the INA226 for this experiment. Confirm the module
is marked `R100`; a different shunt invalidates the v1 current scaling.

Before enabling the output:

1. set the supply voltage with the output disabled;
2. set and verify the frozen current limit;
3. confirm no loose wire can short VIN+ to logic pins;
4. confirm the actuator can be stopped without fingers approaching blades;
5. have a physical power cutoff within reach.

## 3. Start the logger

Copy `tools/bench_metrics/ina226_logger.py` to the RP2350 as `main.py`. Its
startup identity check must not print `FAIL`. On the host, capture each file
with the exact probe and phase names from the manifest:

```sh
python3 tools/bench_metrics/power_log.py \
  --port /dev/ttyACM0 \
  --probe dc_fan_v1 \
  --label normal \
  --seconds 1.4 \
  --out build/ina226_capture/captures/b00-normal.csv
```

The 1.4-second capture provides more than the frozen 128 rows at 100 Hz; only
the first 128 valid rows are scored. The validator still checks every row and
rejects the session if later rows are malformed.

## 4. Follow the frozen order

Each row below is one capture block and later becomes a whole holdout group.
Stop and re-establish the physical load between sessions.

| Block | First | Second | Third |
|---:|---|---|---|
| 0 | normal | elevated load | current-limited stall |
| 1 | elevated load | current-limited stall | normal |
| 2 | current-limited stall | normal | elevated load |
| 3 | normal | elevated load | current-limited stall |
| 4 | elevated load | current-limited stall | normal |
| 5 | current-limited stall | normal | elevated load |
| 6 | normal | elevated load | current-limited stall |
| 7 | elevated load | current-limited stall | normal |
| 8 | current-limited stall | normal | elevated load |
| 9 | normal | elevated load | current-limited stall |

The `phase` strings in CSV are exactly `normal`, `elevated_load`, and
`current_limited_stall`; spaces in the table are only for readability.

Elevated load must remain out of current limit. Stall capture is allowed only
at or below the documented continuous-current rating, lasts no more than 1.5
seconds, and is followed by at least 30 seconds with the actuator unblocked
and allowed to cool. Abort on heating, smell, unstable wiring, an unexpected
supply transition, or shunt voltage approaching 75 mV.

## 5. Seal, verify, and score

Do not hand-edit hashes. Once all thirty files exist:

```sh
python3 tools/ina226_capture_pipeline.py seal \
  build/ina226_capture/capture_manifest.json

python3 tools/ina226_capture_pipeline.py verify \
  build/ina226_capture/capture_manifest.json
```

`verify` must report 30 sessions and 120 windows. Fix a rejected acquisition by
repeating the entire affected session under the same block/class condition,
then seal again. Never delete an inconvenient row or substitute a window.

Run the frozen study:

```sh
python3 tools/ina226_capture_pipeline.py run \
  build/ina226_capture/capture_manifest.json \
  --output build/ina226_coarse_monitor
```

Run it a second time to a separate output directory and byte-compare
`ina226_coarse_monitor_result_v1.json`. Only a map that passes the predeclared
replay gate proceeds to Tang and Artix SOM1 hardware replay.

## 6. Explain one decision exactly

Every normalized four-coordinate decision can be reduced to its exact
winner-versus-runner Voronoi inequality:

```sh
python3 tools/som_voronoi_explain.py \
  build/ina226_coarse_monitor/fold_0/map.json F0 F1 F2 F3
```

The output states `2*x·(runner-winner) <= ||runner||^2-||winner||^2` using
integer coefficients. Its integer slack is exactly
`runner_quadrance - winner_quadrance`, the SOM1 confidence gap. This is an
explanation of the hardware decision boundary, not a fitted surrogate.
