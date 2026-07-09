# Bench Metrics — INA226/INA219 Power Measurement Harness

Produces the power tables for the papers (central paper §Power and Timing).
Works today on a breadboard (Pico + INA226 or INA219 breakout); becomes
permanent when the bench adapter board is assembled
(`hardware/pcb/bench_adapter/bench_adapter_spec.md`). Rev A of the adapter
specifies the **INA226** (16-bit, hardware averaging, ID registers);
the INA219 logger is retained for existing breadboard stock. Both loggers
emit identical CSV, so the host tools don't care which is attached.

| File | Runs on | Purpose |
|---|---|---|
| `ina226_logger.py` | Pico / Pico 2 (MicroPython, copy as `main.py`) | Streams `t_ms,bus_mV,shunt_uV,current_uA` CSV at 100 Hz over USB CDC; 4× hardware averaging; startup TI ID check |
| `ina219_logger.py` | Pico / Pico 2 (MicroPython, copy as `main.py`) | Same CSV stream from the older INA219 module (12-bit, no averaging, no ID check) |
| `power_log.py` | Host | Captures the stream to a phase-annotated CSV (`--seconds` scripted, or interactive phase switching) |
| `power_table.py` | Host | Aggregates capture CSVs → markdown or `--latex` table. `--selftest` verifies the pipeline offline |

## Wiring (breadboard = same pins as the adapter board)

```
Pico GP8 -> SDA             Pico 3V3 -> VCC
Pico GP9 -> SCL             Pico GND -> GND
5V supply -> VIN+           VIN- -> target board 5V in
INA226 ALERT -> GP15 (reserved; unused by the v1 logger)
```

High-side sensing; the stock 0.1 Ω (R100) shunt drops 50 mV at 500 mA. The
calibration register is unused by design in both loggers — raw shunt counts
are converted with integer arithmetic in plain sight (INA226:
`current_uA = raw * 25`, exact; INA219: `current_uA = shunt_uV * 1000 / 100 mΩ`).
INA226 modules ship with R100 or R010 shunts — order R100 and check the
shunt marking on arrival.

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
- INA219 at 100 Hz / 12-bit averages nothing; std in the table is real
  sample scatter, not instrument noise floor. The INA226 logger applies 4×
  hardware averaging (588 µs conversions, ~4.7 ms per result) — note which
  logger produced a table when publishing. For long soaks the un-averaged
  INA219 scatter is the more conservative number.
- USB CDC timestamps come from the Pico (`t_ms`, monotonic); host ISO time is
  recorded per row for cross-referencing UART telemetry logs.
