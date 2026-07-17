# SOM-SIDECAR evaluator quickstart

This is the canonical first-hour procedure for the Tang Primer 25K or Wukong
Artix-7 100T SOM-SIDECAR. It loads a checksummed seven-node Iris map through an RP2350,
classifies all 150 checked-in samples, and requires every FPGA winner to match
the exact software oracle.

## What this proves

- all 28 prototype values and seven semantic labels are accepted over the real
  RP2350-to-FPGA SPI link;
- the FPGA executes the fixed-434-clock exact `Q(sqrt(3))` BMU schedule;
- 150/150 FPGA winner nodes match the oracle;
- the checked node labels classify 147/150 Iris samples (98.0%).

It is not yet a physical-sensor demo. Features in this procedure come from the
checked CSV corpus.

## Required hardware

- Tang Primer 25K with dock, or Wukong Artix-7 100T plus DirtyJTAG;
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

For Wukong, use only the proven J11 bottom-row remap; the top row on the
recorded unit is damaged:

| Signal | Wukong J11/package pin | RP2350 |
|---|---|---|
| MISO, FPGA to RP2350 | J11-10 / B5 | GP0 |
| CS#, RP2350 to FPGA | J11-7 / J4 | GP1 |
| SCK, RP2350 to FPGA | J11-8 / G4 | GP2 |
| MOSI, RP2350 to FPGA | J11-9 / B4 | GP3 |
| Ground | J11-11 | GND |

Wukong UART TX is package pin E3. On the recorded bench the RP2350 console
was `/dev/ttyACM6` and the UART adapter was `/dev/ttyUSB0`.

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

For Wukong:

```bash
bash hardware/boards/artix7/build_a7.sh 100t somsidecar synth
bash hardware/boards/artix7/build_a7.sh 100t somsidecar pnr
PRJXRAY_ROOT=$HOME/toolchains/prjxray \
OPENXC7_PYTHON=$HOME/.local/venvs/prjxray/bin/python \
  bash hardware/boards/artix7/build_a7.sh 100t somsidecar pack
openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_SOMSIDECAR.bit
```

The corpus-proven image recorded on 2026-07-17 has SHA-256:

```text
946574dc25ad7aada168f9f06af101cd0df747230c0fea0ca9dae0ad5d9e7c3c
```

Rebuilding may produce a different artifact hash as the toolchain or RTL
changes; record the new hash with any new evidence.

The renewed SOM1-capable image built on 2026-07-17 has SHA-256:

```text
8753c4924ed6952c049a038a80cbe3bfb8b930e038842631665108af4ad1ff92
```

It uses 14,068 LUT4 (61%), 3,251 DFF (14%), and 8 BSRAM (14%), and routes at
75.79 MHz against the 50 MHz constraint. This hash is Tang-silicon proven.

The cross-vendor Wukong image has SHA-256:

```text
f22a34e78437583efcb6a5a0bafb800c9df6a0803ee8614e8184b170cf5bf180
```

It uses 8,013 SLICE_LUTX (6%), 3,098 SLICE_FFX (2%), 44 DSP48E1, and four
RAMB18E1 blocks, and routes at 65.63 MHz against the 50 MHz constraint.

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

If a deployment exposes only SPI, add `--no-uart`. This still validates the
compact SPI result and every SOM1 field and CRC; the canonical silicon proof
above retains UART so all three result surfaces are checked.

## Optional host-library installation

The general southbridge client is installable from the repository:

```bash
python3 -m pip install -e .
spu-host --port /dev/ttyACM0 raw ping
```

The Iris corpus runner intentionally has no pyserial dependency; it uses the
standard-library POSIX serial transport in `tools/som_map.py`.

## Current product boundary

- The renewed 52-byte `SOM1` frame and all seven semantic-label writes are now
  Tang-silicon verified over the complete 150-sample corpus. Winner, runner-up,
  exact distances, confidence gap, ambiguity, map/result generations,
  error/status, and CRC-32 matched the software oracle on every sample. See
  `docs/hardware_evidence.md` §3.2g.4.
- The compact result byte remains compatible and retains its legacy label LUT;
  consumers that need map-owned labels and replay evidence must use `SOM1`.
- The complete writable sidecar is silicon-proven on Tang 25K and Wukong
  Artix-7 with 150/150 exact SOM1 evidence records on both vendors. The older
  Artix `SOMPROBE` remains only a fixed historical fixture.
- Physical INA226 sensor acquisition and deterministic temporal feature
  extraction remain the next bench tranche. Their software ABI is now proven
  by `python3 tools/som_sensor_replay.py`; see `docs/SOM_SENSOR_REPLAY.md`.
