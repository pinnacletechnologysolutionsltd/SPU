# RP2040/RP2350 Bring-Up Plan

For the display and deterministic SOM map direction, see
`docs/visual_som_devboard_plan.md`.

Status anchor: Tang Primer 25K is now the stable regression/probe target, while
Wukong Artix-7 100T is the Artix silicon-evidence and constrained integration
target. Full concurrent integration is reserved for an Artix-7 200T /
Kintex-class board. Use the Tang 25K split probes for low-risk RP2040/RP2350
firmware regression before moving new control paths onto Wukong.

Board-role sequencing lives in `docs/CURRENT_STATUS.md` and
`docs/build_and_bringup_guide.md`.

## Current Boundary

The legacy Tang 25K full-probe top exposes the RP2350 path as a UART byte input:

- FPGA `periph_rx` on pin `B3`
- 115200 baud host receiver in `spu13_tang25k_top.v`
- accepted control bytes: `w`, `a`, `s`, `d`, and space

The current RP2350 diagnostic path and Tang 25K southbridge probes have proven
the broader SPI slave protocol, including SD-backed RPLU2 hydration. Keep the
UART byte path as a legacy fallback and use SPI southbridge probes for current
regression work.

## Firmware Module Direction

Keep first-bring-up roles separate:

- RP2040 DirtyJTAG pod: JTAG programming and detection only.
- USB-UART/debug pod: plain telemetry path while FPGA pins are being proven.
- RP2350 southbridge: SPI control, table hydration, SD/cache, sensors, watchdog.

The RP2350 has enough headroom to combine these later, but one composite
firmware should come after JTAG, UART, and SPI are each proven independently.

Shared firmware modules should live under `hardware/rp_common/` and be reused by
RP2040/RP2350 applications where possible:

| Module | Status | Purpose |
|---|---|---|
| `spu_link` | Implemented | SPI command constants, endian helpers, status/manifold reads, chord writes, RPLU config writes |
| `spu_boot` | Implemented | Compiled-default RPLU hydration and symmetry-breath startup check |
| `spu_storage` | Implemented, awaiting hardware validation | FAT32 SD pack reader, manifest parsing, RPLU table hydration; optional SPI flash cache still planned |
| `spu_diag` | Implemented | USB CDC console: status, scale, read manifold, send chord, write RPLU record, hydrate defaults |
| `spu_sensors` | Planned | Sensor adapters that emit compact deterministic packets to FPGA |
| `spu_board` | Planned | Pin maps and role profiles for DirtyJTAG pod, RP2350 southbridge, Tang 25K, Wukong |

Hydration source priority should be:

1. Valid SD card pack.
2. Valid RP-side SPI flash fallback/cache, when present on a later board.
3. Compiled minimal defaults from `hardware/rp_common/rplu_default_tables.h`.

Tier 1 has a SPI-mode SD/FAT32 implementation, standalone smoke-test firmware,
and physical SD PMOD validation. Tier 2 remains planned. The firmware is
structured so each table source can feed the same FPGA SPI command layer.

## Phase 0: Toolchain Sanity

Required local tools:

```sh
cmake --version
ninja --version
picotool version
arm-none-eabi-gcc --version
```

On Arch, both compiler and newlib specs are required:

```sh
sudo pacman -S --needed arm-none-eabi-gcc arm-none-eabi-newlib
```

`arm-none-eabi-gcc` alone is not enough; Pico SDK links with
`--specs=nosys.specs`, provided by `arm-none-eabi-newlib`.

Required SDK environment:

```sh
export PICO_SDK_PATH=/path/to/pico-sdk
test -f "$PICO_SDK_PATH/external/pico_sdk_import.cmake"
```

Build checks. Use fresh build directories or clear stale CMake caches; a cache
created before `arm-none-eabi-gcc` was available can keep `/usr/bin/cc` and fail
on RP2040 Thumb assembly.

```sh
cmake -S hardware/rp2040 -B build/rp2040_visualiser_build -G Ninja \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" \
  -DCMAKE_C_COMPILER=/usr/bin/arm-none-eabi-gcc \
  -DCMAKE_CXX_COMPILER=/usr/bin/arm-none-eabi-g++ \
  -DCMAKE_ASM_COMPILER=/usr/bin/arm-none-eabi-gcc
ninja -C build/rp2040_visualiser_build rp2040_visualiser

cmake -S hardware/rp2350 -B build/rp2350_uart_injector_build -G Ninja \
  -DPICO_SDK_PATH="$PICO_SDK_PATH"
ninja -C build/rp2350_uart_injector_build rp2350_uart_injector
ninja -C build/rp2350_uart_injector_build rp2350_spu_interface
ninja -C build/rp2350_uart_injector_build rp2350_spu_diag
```

## RP2350 SD PMOD Smoke Test

Goal: prove the SD card and FAT32 path without depending on the FPGA.

Default SPI-mode SD pins are `spi1` with SCK GP10, MOSI/CMD GP11, MISO/DAT0
GP12, and CS/DAT3 GP13. Override them at configure time if the PMOD wiring uses
the future SDIO-style mapping, for example:

```sh
cmake -S hardware/rp2350 -B build/rp2350_sd_test -G Ninja \
  -DSPU_SD_SCK_PIN=10 \
  -DSPU_SD_MOSI_PIN=11 \
  -DSPU_SD_MISO_PIN=9 \
  -DSPU_SD_CS_PIN=6
ninja -C build/rp2350_sd_test spu_sd_test
```

Flash `build/rp2350_sd_test/spu_sd_test.uf2`. Expected USB CDC output:

```text
--- SPU SD Card Test ---
SD card and filesystem initialized successfully.
Successfully wrote ...
Read data matches written data.
Successfully deleted test.txt.
--- SPU SD Card Test Complete ---
```

Only after this passes should `sdhydrate` be used from `rp2350_spu_diag`.

Current hardware result (2026-06-28): southbridge SPI and default SD PMOD wiring
are proven after SD-side solder rework. With the Tang 25K southbridge bitstream
SRAM-loaded and `rp2350_spu_diag.uf2` built for the RP2350-Zero GP0-GP3 SPI0
map, `status` returns `raw=13 A5 00 00`. On the default SD map
`CS=GP13/SCK=GP10/MOSI=GP11/MISO=GP12`, raw SD probes return
`cmd0_r1=0x01 cmd8_r1=0x01 r7=00 00 01 AA`, `sdinit` reports `OK`, and
the standalone `spu_sd_test.uf2` write/read/delete smoke passes with halt code
0. With `/manifest.txt` selecting `/carbon_rplu.tbl`, `sdhydrate` loads 16
records with 0 skipped. SRAM-loading the SPI-only FPGA telemetry probe
`build/tang_primer_25k_southbridge_spi_probe.fs` proves FPGA-side receipt. The
probe reports `status raw=25 A5 00 00`; `cfgtele` reports count 0 before
hydration, then count 16 with last record
`sel=0 material=1 addr=2 data=0x0000000000010000`.

Updated hardware result (2026-06-30 NZT): the RP2350 and FPGA southbridge write
path was hardened and re-tested. Two bugs were fixed: the C CRC helper compared
`crc & 0x80` against a 0/1 data bit, and the FPGA SPI slave write state machine
could abandon or misalign `0xA5` payloads across firmware inter-byte gaps. With
`rp2350_spu_diag.uf2` rebuilt for the RP2350-Zero GP0-GP3 map, the SPI-only
probe now routes at 1,861 LUT4 / 840 DFF. Manual `rplu 0 1 2
0x0000000000010000` advances `cfgtele` from count 0 to count 1; clean
`sdhydrate` advances count 0 to 16 with checksum `0x3A0AB5E9` and
`status raw=25 A5 00 00`.

Core-attached split-probe result (2026-06-30 NZT): the rebuilt
`build/tang_primer_25k_spu13_southbridge_link.fs` routes at 4,054 LUT4 /
3,091 DFF and passes timing (`clk_50m` 55.48 MHz, `clk_core` 102.46 MHz
against 12 MHz). After SRAM load, diagnostics report `status raw=13 A5 00 00`;
manual `rplu` advances `cfgtele` to count 1; and clean `sdhydrate` advances
count 0 to 16 with checksum `0x3A0AB5E9`.

Full-core southbridge result (2026-06-29 NZT): `build_25k_spu13_southbridge.sh`
successfully synthesizes, places, routes, and packages
`build/tang_primer_25k_spu13_southbridge.fs`. Post-route timing passes the
12 MHz constraint (`clk_core` 72.28 MHz max, `clk_50m` 125.16 MHz max).
SRAM-loading this full image with openFPGALoader succeeds. The RP2350 diagnostic
path then reports `status raw=13 A5 00 00`; `cfgtele` reports `magic=SPUC`
with count 0 before hydration; `sdinit` succeeds; `sdhydrate` loads 16 records
with 0 skipped; and the final `cfgtele` reports count 16, last record
`sel=0 material=1 addr=2 data=0x0000000000010000`, checksum `0x3A0AB5E9`.

RPLU v2 consume-profile result (2026-06-29 NZT): the same full southbridge path
now accepts the corrected 149-record consume profile generated by
`tools/gen_rplu2_tables.py --profile consume_probe`. After SRAM-loading the
rebuilt `build/tang_primer_25k_spu13_southbridge.fs`, the RP2350 diagnostic
console streams all records over `rplu`; final telemetry reports count 149,
last record `sel=6 material=0 addr=0 data=0x0000000000000003`,
`rplu2_sum=0x0AA480E7`, and pass sentinel `rplu2_status=0xC02E0001`.
Decoded proof fields are `rplu2_num0=0x00000002`, `rplu2_delta=0`,
`rplu2_row1=0x00000001`, and `rplu2_kappa=0x00000003`. The rebuilt image also
includes SPI `S_FILL` CS-abort recovery and routes at `clk_50m` 133.55 MHz /
`clk_core` 67.76 MHz against the 12 MHz target.

Pre-rework SD raw-command probes tried the default map, the SDIO-style map
`CS=GP6/SCK=GP10/MOSI=GP11/MISO=GP9`, and the two mixed CS/MISO maps. None
returned the expected CMD0 idle response `0x01`; GP12 read as pulled high and
returned all `0xFF`, while GP9 read low and returned all `0x00`. If this failure
returns, meter the SD PMOD before changing firmware: confirm 3.3 V at the
socket, common ground, CLK continuity from GP10, CMD/MOSI from GP11, DAT3/CS
from GP13, and DAT0/MISO to GP12.

## Phase 1: RP2040 Visualizer Smoke

Goal: prove USB CDC and host framing before involving the FPGA.

1. Flash `rp2040_visualiser.uf2`.
2. Hold `GP28` low at boot for emulate mode.
3. Run the host visualizer/terminal against the RP2040 USB CDC port.
4. Confirm 104-byte frames arrive continuously.

This proves the PC-to-RP2040 display/debug lane and the 8-byte chord passthrough
buffering without relying on the FPGA or RP2350.

## Phase 2: RP2350 UART Byte Injector

Goal: use the known-good RPLU FPGA image without changing FPGA RTL.

1. Build `rp2350_uart_injector.uf2`, the minimal RP2350 UART firmware that
   forwards USB CDC bytes to FPGA `periph_rx` at 115200 baud.
2. Wire RP2350 TX to FPGA `periph_rx` / `B3` with shared ground.
3. Load `build/tang_primer_25k_spu13_rplu_full_probe.fs`.
4. Confirm the FPGA stays in RPLU PASS telemetry while accepting host bytes.

Build command once the SDK is visible:

```sh
cmake -S hardware/rp2350 -B build/rp2350_pico -G Ninja
ninja -C build/rp2350_pico rp2350_uart_injector
```

This is the lowest-risk RP2350-to-FPGA proof because it exercises the already
verified board top instead of introducing SPI at the same time.

## Phase 3: RP2350 PIO Heartbeat

Goal: prove the timing island.

PIO links are disabled by default in `rp2350_spu_interface`. Enable them only in
a dedicated test build:

```sh
cmake -S hardware/rp2350 -B build/rp2350_pio_check -G Ninja \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" \
  -DSPU_ENABLE_PIRANHA=ON \
  -DSPU_ENABLE_WHISPER=ON
ninja -C build/rp2350_pio_check rp2350_spu_interface
```

1. Enable only the `piranha_pulse` PIO state machine on `GP6`.
2. Scope or logic-analyzer check the pulse rate.
3. Feed the pulse to a spare FPGA input only after the UART byte path is stable.
4. Leave Whisper/PWI on `GP7` disconnected until its pulse widths are scoped.

Keep this separate from USB host work so timing bugs are isolated.

## Phase 4: SPI Control Plane

Goal: graduate from byte control to structured SPU/RPLU control.

1. Add SPI pins to the Tang 25K board top.
2. Instantiate `spu_spi_slave.v` beside the proven RPLU full-probe logic.
3. Flash `rp2350_spu_diag.uf2` and open the RP2350 USB CDC console.
4. Start read-only: `status` (`CMD_READ_STATUS`, `0xAC`, 4 bytes), then
   `manifold` (`CMD_READ_MANIFOLD`, `0xA0`, 32 bytes), `scale` (`0xAD`),
   last-QLDI `qr` (`0xAE`), then sticky `hex` (`0xAF`).
5. Add instruction ingress: `chord <16 hex digits>` (`CMD_WRITE_CHORD`, `0xB1`).
6. Add direct RPLU hydration: `rplu <sel> <material> <addr> <data64>` or
   `hydrate` (`CMD_WRITE_RPLU_CFG`, `0xA5`, HEADER + DATA).
7. Only then enable RP2350 boot-time RPLU table writes from SD or cached flash.

The RPLU flash boot path should remain the fallback while runtime writes are
being validated.

Diagnostic console commands:

```text
help
ping
status
scale
manifold
chord 4000000000010001
qr
hex
cfgtele
rplu 0 0 0 0x0000000000010000
hydrate
sdinit
sdcat manifest.txt
sdhydrate
```

## Phase 5: USB-A Host Inputs

Goal: map physical peripherals to deterministic FPGA control.

Start with simple HID-class input:

- keyboard: `w`, `a`, `s`, `d`, space
- mouse: delta-to-rotor P/Q adjustment
- gamepad: axes/buttons to compact chord stream

Keep RP2350 as the USB host and event conditioner. The FPGA should receive
small, deterministic control packets, not raw USB traffic.

## Industrial Cluster Direction

Use the Tang 25K or larger Gowin board as the SPU-13/RPLU mother. Use RP2350 and
SPU-4/Colorlight-class nodes as deterministic edge controllers:

- RP2350: USB/HID, watchdog, sensor conditioning, boot/control sequencing
- SPU-4: local scan loop, actuator gating, compact RPLU bank
- SPU-13: global manifold/RPLU oracle, flash images, telemetry authority
