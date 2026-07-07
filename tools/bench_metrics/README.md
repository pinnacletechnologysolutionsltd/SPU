# Bench Metrics — INA219 Power Measurement Harness

Produces the power tables for the papers (central paper §Power and Timing).
Works today on a breadboard (Pico + INA219 breakout); becomes permanent when
the bench adapter board is assembled
(`hardware/pcb/bench_adapter/bench_adapter_spec.md`).

| File | Runs on | Purpose |
|---|---|---|
| `ina219_logger.py` | Pico / Pico 2 (MicroPython, copy as `main.py`) | Streams `t_ms,bus_mV,shunt_uV,current_uA` CSV at 100 Hz over USB CDC |
| `power_log.py` | Host | Captures the stream to a phase-annotated CSV (`--seconds` scripted, or interactive phase switching) |
| `power_table.py` | Host | Aggregates capture CSVs → markdown or `--latex` table. `--selftest` verifies the pipeline offline |

## Wiring (breadboard = same pins as the adapter board)

```
Pico GP8 -> INA219 SDA      Pico 3V3 -> INA219 VCC
Pico GP9 -> INA219 SCL      Pico GND -> INA219 GND
5V supply -> INA219 VIN+    INA219 VIN- -> target board 5V in
```

High-side sensing; the stock 0.1 Ω shunt drops 50 mV at 500 mA. The
calibration register is unused by design — raw shunt microvolts are converted
with integer arithmetic in plain sight (`current_uA = shunt_uV * 1000 / 100 mΩ`).

## Sanity check before first real measurement

Power a 47 Ω / 5 W resistor as the load: expect ~106 mA at 5.0 V, ±5%.

## Measurement methodology (papers)

One capture per probe bitstream, two phases minimum:

- **baseline** — board powered, FPGA unconfigured (or blank image).
- **active** — probe bitstream loaded and running its self-driven loop.

Probe power = active − baseline. Suggested session for the Tang 25K ladder:

```bash
source .venv/bin/activate
python3 tools/bench_metrics/power_log.py --port /dev/ttyACM0 \
    --probe som_bmu_probe --label baseline --seconds 60 \
    --out build/metrics/som_bmu_baseline.csv
# load bitstream, wait for UART PASS line, then:
python3 tools/bench_metrics/power_log.py --port /dev/ttyACM0 \
    --probe som_bmu_probe --label active --seconds 60 \
    --out build/metrics/som_bmu_active.csv

python3 tools/bench_metrics/power_table.py build/metrics/*.csv          # markdown
python3 tools/bench_metrics/power_table.py --latex build/metrics/*.csv  # paper rows
```

Record alongside each session: bitstream SHA-256, build script name, board,
supply source, ambient conditions if unusual. Captures live under
`build/metrics/` (gitignored); promote finished tables into
`docs/hardware_evidence.md` with the capture commands, per ledger discipline.

## Caveats

- SRAM-loaded bitstreams are lost on power-cycle — sequence baseline capture
  *before* loading, or use flash-booted probes (see adapter spec §3 recipes).
- The 100 Hz / 12-bit configuration averages nothing; std in the table is
  real sample scatter, not instrument noise floor. For long soaks this is the
  honest number to publish.
- USB CDC timestamps come from the Pico (`t_ms`, monotonic); host ISO time is
  recorded per row for cross-referencing UART telemetry logs.
