# INA226 coarse-monitor capture runbook

This is the bench procedure for the frozen contract in
`INA226_COARSE_MONITOR_CONTRACT.md`. Do not collect a physical dataset until
the actuator rating, supply current limit, INA226 shunt marking, and wiring
checks below are complete.

The contract entered Git at commit `ed16263`, before this ingestion code or
any synthetic/physical score existed.

## 1. Prepare the manifest

> **A one-time re-`init` against the v2 contract is required (2026-08-06).**
>
> The manifest is `build/ina226_capture/manifest.json` (**not**
> `capture_manifest.json`, which earlier revisions named and which does not
> exist). The existing one is pinned to the **v1** contract and now fails with
> *"capture contract format mismatch"* — that is expected, not a fault. Re-run
> `init` once against v2, then treat the manifest as frozen again.
>
> This is safe only because **no session has been sealed**: all 30
> `csv_sha256` fields are null. Confirm that before running it:
>
> ```sh
> python3 -c "import json;m=json.load(open('build/ina226_capture/manifest.json'));\
> print(sum(1 for s in m['sessions'] if s['csv_sha256']), 'sealed of', len(m['sessions']))"
> ```
>
> If that prints anything other than `0 sealed of 30`, **stop** — `init`
> performs a bare `write_bytes` with **no existence check**
> (`tools/ina226_capture_pipeline.py:390`) and will silently discard sealed
> hashes.
>
> Use the **measured** supply limit, not the front-panel setting. A supply
> displaying 280 mA was measured regulating at 307.4 mA on 2026-08-06; `init`
> refuses a limit above the actuator's continuous rating, and recording an
> unverified number defeats the check.

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
| VCC | 3V3 (pin 36) | sensor logic power |
| GND | GND (pin 13) | common reference |
| SDA | GP8 (pin 11) | I2C0 data |
| SCL | GP9 (pin 12) | I2C0 clock |
| ALERT / ALE | GP15 or open | reserved; v1 polls |
| VBS | VIN− node | **bus-voltage sense — required** |
| VIN+ | bench-supply positive | high side before shunt |
| VIN- | actuator positive | high side after shunt |

The actuator negative returns directly to bench-supply ground. Do not put an
FPGA board's supply through the INA226 for this experiment. Confirm the module
is marked `R100`; a different shunt invalidates the current scaling.

> **`VIN−` is not a negative terminal.** It is the downstream side of the
> shunt and sits within ~30 mV of `VIN+` — a positive node. The actuator's
> **positive** lead goes there. This wording has caused wiring errors twice.

> **`VBS` must be jumpered to the `VIN−` node** (the same net as the actuator's
> positive lead), **not** to supply negative. VBUS is measured against the
> INA226's own ground, so tying `VBS` to ground reads exactly 0 mV on every
> row and every `normal`/`elevated_load` session is rejected at seal. Earlier
> revisions of this table omitted `VBS` entirely.

> **Bench-supply ground must be common with the logger ground**, or `bus_mV` is
> meaningless. Run the actuator's return current **directly to the supply
> terminal** and take a separate thin reference wire from that terminal to the
> Pico's GND. Do not let actuator current share a breadboard rail with logic
> ground: at 200–300 mA the contact resistance both shifts the ground reference
> (observed corrupting the CDC stream during stalls) and drops enough voltage
> to push `bus_mV` below tolerance. A breadboarded power path measured 0.96 Ω
> and degraded to 1.44 Ω within one session on 2026-08-06.

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

> **Do not trust a fixed `/dev/ttyACM*` number.** It is assigned in enumeration
> order and moves whenever the DirtyJTAG programmer, the southbridge, or the
> logger is replugged — the logger has appeared as both `ttyACM0` and `ttyACM3`
> in one session, and `ttyACM0` was the *programmer* for part of it. Identify
> the board by its USB serial before every capture:
>
> ```sh
> for d in /dev/ttyACM*; do
>   echo "$d $(udevadm info -q property -n $d | sed -n 's/^ID_SERIAL_SHORT=//p')"
> done
> ```

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

### Rehearse the chain without a bench

`tools/generate_ina226_synthetic_capture.py` writes a complete synthetic
30-session set using the profiles measured on 2026-08-06, so seal → verify →
run → byte-comparison can be exercised before any physical capture. It is also
the end-to-end test of the v2 stall exemption: its stall sessions carry a
collapsed rail that every v1 row would have rejected.

On the frozen seed the run reports `som_balanced=100.00% replay_eligible=True`
and result SHA-256 `d989e8d1…`. If that hash changes, the pipeline changed.

Expect `baseline_superiority_claim_authorized: False` — a plain threshold ties
the SOM on separable data. That is the contract working correctly, and the
physical capture should be expected to reproduce it. Synthetic data proves the
machinery, never the science.

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
