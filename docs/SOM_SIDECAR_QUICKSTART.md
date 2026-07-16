# SOM-SIDECAR evaluator quickstart

This is the canonical first-hour procedure for the Tang Primer 25K
SOM-SIDECAR. It loads a checksummed seven-node Iris map through an RP2350,
classifies all 150 checked-in samples, and requires every FPGA winner to match
the exact software oracle.

## What this proves

- all 28 prototype values are accepted over the real RP2350-to-FPGA SPI link;
- the FPGA executes the fixed-434-clock exact `Q(sqrt(3))` BMU schedule;
- 150/150 FPGA winner nodes match the oracle;
- the checked node labels classify 147/150 Iris samples (98.0%).

It is not yet a physical-sensor demo. Features in this procedure come from the
checked CSV corpus.

## Required hardware

- Tang Primer 25K with dock;
- Raspberry Pi Pico 2 / RP2350 board;
- four SPI signal wires plus a common ground;
- one USB connection for the RP2350 console and one USB connection for the
  Tang dock/debugger.

No SD card is needed for this spin.

Never leave the RP2350 powered and driving SPI into an unpowered FPGA board.
Power both boards before driving the link, or disconnect the four SPI signals
during independent power cycling.

## Wiring

The proven zero-header RP2350 wiring is:

| Signal | Tang Primer 25K J4/package pin | RP2350 |
|---|---|---|
| MISO, FPGA to RP2350 | C10 | GP0 |
| CS#, RP2350 to FPGA | G10 | GP1 |
| SCK, RP2350 to FPGA | D10 | GP2 |
| MOSI, RP2350 to FPGA | B10 | GP3 |
| Ground | GND | GND |

The Tang dock's visible FPGA UART is package pin C3 and normally appears as the
Sipeed debugger's second serial interface, commonly `/dev/ttyUSB1`. The RP2350
USB CDC console commonly appears as `/dev/ttyACM0`. Confirm the actual paths:

```bash
ls -l /dev/serial/by-id/
```

## Build and load the RP2350 console

With `PICO_SDK_PATH` configured:

```bash
cmake -S hardware/rp2350 -B build/rp2350_som \
  -DPICO_BOARD=pico2 \
  -DSPU_RP2350_ZERO_HEADER_SPI=ON \
  -DSPU_DIAG_SPI_BAUD_HZ=250000
cmake --build build/rp2350_som --target rp2350_spu_diag -j
picotool load -f build/rp2350_som/rp2350_spu_diag.uf2
picotool reboot
```

The 250 kHz SPI rate is the conservative diagnostic default.

## Build and load the FPGA image

```bash
bash build_25k_spu13_som_sidecar.sh
openFPGALoader -b tangprimer25k \
  build/tang_primer_25k_spu13_som_sidecar.fs
```

The corpus-proven image recorded on 2026-07-17 has SHA-256:

```text
946574dc25ad7aada168f9f06af101cd0df747230c0fea0ca9dae0ad5d9e7c3c
```

Rebuilding may produce a different artifact hash as the toolchain or RTL
changes; record the new hash with any new evidence.

## Run the reproducible hardware proof

```bash
python3 tools/iris_som_demo.py --hardware \
  --console-port /dev/ttyACM0 \
  --uart-port /dev/ttyUSB1
```

Expected final line:

```text
IRIS_SOM_V1: PASS (150/150 FPGA winners bit-exact to oracle)
```

Expected confusion matrix:

```text
                 predicted
true             set  ver  vir
setosa            50    0    0
versicolor         0   48    2
virginica          0    1   49
accuracy: 147/150 (98.0%)
```

The canonical map is `software/models/iris_som_v1.json`. The runner refuses to
continue if that artifact differs from deterministic regeneration.

## Optional host-library installation

The general southbridge client is installable from the repository:

```bash
python3 -m pip install -e .
spu-host --port /dev/ttyACM0 raw ping
```

The Iris corpus runner intentionally has no pyserial dependency; it uses the
standard-library POSIX serial transport in `tools/som_map.py`.

## Current product boundary

- Semantic labels come from the checksummed map artifact on the host.
- The compact hardware result still carries the sidecar's fixed legacy label
  LUT as independent link telemetry.
- Runner-up, exact distances, confidence gap, ambiguity, sensor-health flags,
  and map generation belong in the planned versioned `SOM1` result frame.
- Physical INA226 sensor acquisition and deterministic temporal feature
  extraction are the next evaluator tranche.
