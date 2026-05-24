# RP2040/RP2350 Bring-Up Plan

Status anchor: Tang Primer 25K RPLU full probe passes with the damaged-board
SDRAM mask `0x0402`. Keep that image as the stable FPGA target while bringing
up the RP2040/RP2350 side.

## Current Boundary

The proven Tang 25K full-probe top currently exposes the RP2350 path as a UART
byte input:

- FPGA `periph_rx` on pin `B3`
- 115200 baud host receiver in `spu13_tang25k_top.v`
- accepted control bytes: `w`, `a`, `s`, `d`, and space

The older RP2350 firmware in `hardware/rp2350/rp2350_spu_interface.c` expects a
broader FPGA SPI slave protocol. That SPI slave exists in
`hardware/rtl/peripherals/io/spu_spi_slave.v` and is wired in
`hardware/rtl/top/spu_system.v`, but it is not yet wired into the proven Tang 25K
RPLU full-probe top.

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
```

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

1. Enable the `piranha_pulse` PIO state machine on `GP6`.
2. Scope or logic-analyzer check the pulse rate.
3. Feed the pulse to a spare FPGA input only after the UART byte path is stable.

Keep this separate from USB host work so timing bugs are isolated.

## Phase 4: SPI Control Plane

Goal: graduate from byte control to structured SPU/RPLU control.

1. Add SPI pins to the Tang 25K board top.
2. Instantiate `spu_spi_slave.v` beside the proven RPLU full-probe logic.
3. Start read-only: `CMD_READ_STATUS`, then `CMD_READ_MANIFOLD`.
4. Add write path: `CMD_WRITE_CHORD`.
5. Only then enable RP2350 boot-time RPLU table writes.

The RPLU flash boot path should remain the fallback while runtime writes are
being validated.

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
