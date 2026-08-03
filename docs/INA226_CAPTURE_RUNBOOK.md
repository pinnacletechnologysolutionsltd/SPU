# INA226 coarse-monitor capture runbook

This is the bench procedure for the frozen contract in
`INA226_COARSE_MONITOR_CONTRACT.md`. Do not collect a physical dataset until
the actuator rating, supply current limit, INA226 shunt marking, and wiring
checks below are complete.

The contract entered Git at commit `ed16263`, before this ingestion code or
any synthetic/physical score existed.

## 1. Prepare the manifest

> **The manifest for the current bench already exists — do not run `init`.**
>
> It is `build/ina226_capture/manifest.json` (**not** `capture_manifest.json`,
> which earlier revisions of this runbook named and which does not exist). It is
> pinned to probe `tamiya_75026_v1`, Tamiya 75026, 3000 mV bus, 280 mA
> continuous, 280 mA supply limit, and its `contract.sha256` was re-verified
> against `software/datasets/ina226_coarse_monitor_v1.json` on 2026-08-04.
>
> `init` performs a bare `write_bytes` with **no existence check**
> (`tools/ina226_capture_pipeline.py:390`) — running it silently replaces the
> manifest, and the 30 `csv_sha256` fields with it. Skip to §2.

Only for a *new* actuator on a fresh manifest: choose a low-voltage replaceable
fan or motor whose continuous-current rating is documented and below the
INA226/R100 750 mA measurement headroom. The supply limit must not exceed
either that headroom or the continuous rating.

```sh
python3 tools/ina226_capture_pipeline.py init \
  build/ina226_capture/manifest.json \
  --nominal-bus-mv 3000 \
  --probe tamiya_75026_v1 \
  --actuator-model 'Tamiya 75026' \
  --actuator-continuous-ma 280 \
  --supply-limit-ma 280
```

Every electrical value above is the **real** value for the current bench, not a
placeholder — earlier revisions carried a 600 mA example, which is more than
double this actuator's rating. Replace them only if the actuator changes.
`init` refuses a supply limit above the continuous-current rating.

`captures/` does not need to be created by hand; `power_log.py` makes the
output parent directory (`tools/bench_metrics/power_log.py:54`).

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
startup identity check must not print `FAIL`.

**Activate the venv first — `pyserial` is not installed in the system Python**,
and `power_log.py` exits with `pyserial required` without it:

```sh
source .venv/bin/activate     # pyserial 3.5 lives here, not in system python3
```

On the host, capture each file with the exact probe and phase names from the
manifest:

```sh
python3 tools/bench_metrics/power_log.py \
  --port /dev/ttyACM0 \
  --probe tamiya_75026_v1 \
  --label normal \
  --seconds 1.4 \
  --out build/ina226_capture/captures/b00-normal.csv
```

> **`--probe` must match the manifest exactly.** The validator enforces it per
> row — `software/lib/ina226_capture.py:294` raises *"row N has the wrong
> probe"*, and line 296 does the same for `phase`. A mismatch is not caught at
> capture time: it surfaces at `seal`/`verify`, after the physical session is
> over, and the only fix is to re-run the whole session. Earlier revisions of
> this runbook printed `dc_fan_v1` here while the manifest said
> `tamiya_75026_v1`, which would have rejected every row.

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

### Block 0 first — stop and check before committing to blocks 1-9

Block 0 is the shakedown. Run these three, then confirm mean current ascends
`normal < elevated_load < current_limited_stall` before spending the other nine
blocks' bench time:

```sh
source .venv/bin/activate
P=build/ina226_capture/captures
L="python3 tools/bench_metrics/power_log.py --port /dev/ttyACM0 --probe tamiya_75026_v1 --seconds 1.4"

$L --label normal                 --out $P/b00-normal.csv
$L --label elevated_load          --out $P/b00-elevated_load.csv
$L --label current_limited_stall  --out $P/b00-current_limited_stall.csv
```

If the three means do not separate, the physical load conditions are not
distinguishable and no amount of downstream scoring will fix it — re-establish
the loads rather than continuing. Observe the stall rules in the paragraph
below: ≤1.5 s, at or under 280 mA, then ≥30 s unblocked to cool.

> **One RP2350 cannot be both the SPI southbridge and the MicroPython logger.**
> Flashing `ina226_logger.py` as `main.py` displaces `rp2350_spu_diag`.
>
> Current bench assignment (2026-08-04): **RP2350-Zero = southbridge, Pico 2 =
> logger**, so the two roles never collide and no re-flash is needed. If you
> ever collapse them onto one device, restore `rp2350_spu_diag.uf2` afterwards —
> the documented resting state expects `0xB3` to return `version=1` at 125 kHz,
> and a failure against that is this, not a new fault.
>
> Note the southbridge must be built with `-DSPU_RP2350_ZERO_HEADER_SPI=ON` for
> the GP0-3 wiring; the compiled-in defaults are GP16-19
> (`rp2350_spu_diag.c:47-57`). Irrelevant to logging, but it is the same pair of
> boards, so it is easy to conflate the two builds.

Elevated load must remain out of current limit. Stall capture is allowed only
at or below the documented continuous-current rating, lasts no more than 1.5
seconds, and is followed by at least 30 seconds with the actuator unblocked
and allowed to cool. Abort on heating, smell, unstable wiring, an unexpected
supply transition, or shunt voltage approaching 75 mV.

## 5. Seal, verify, and score

Do not hand-edit hashes. Once all thirty files exist:

```sh
python3 tools/ina226_capture_pipeline.py seal \
  build/ina226_capture/manifest.json

python3 tools/ina226_capture_pipeline.py verify \
  build/ina226_capture/manifest.json
```

`verify` must report 30 sessions and 120 windows. Fix a rejected acquisition by
repeating the entire affected session under the same block/class condition,
then seal again. Never delete an inconvenient row or substitute a window.

Run the frozen study:

```sh
python3 tools/ina226_capture_pipeline.py run \
  build/ina226_capture/manifest.json \
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
