# SPU-13 Cluster Architecture & Workflow (Tang Primer 25K)

## Current System Architecture
- **Compute Engine:** GW5A-25A FPGA (Tang Primer 25K) running Dual SPU-13 + 8× SPU-4 satellites.
- **I/O Host:** RP2350 microcontroller (USB-A port) handling USB stack/peripherals (Keyboards, Mice, Sensors), bridged to FPGA via `uart_tx` (C3).
- **Bridge/Console:** BL616 MCU (USB-C port) providing JTAG programming and verified serial UART telemetry at 115,200 baud on Pin B11.
- **Clocking:** Raw 50 MHz crystal (PLLA bypassed in open-source synthesis flow).
- **Storage:** Onboard 32 MB SDRAM (W9825G6KH-6); SD card (optional) for asset streaming via `spu_sd_inhaler`.

## Hardware/Toolchain Known Issues
- **CPU/SSPI Config Pins (GW5A-25A):** The Tang Primer 25K raw 50 MHz clock on `E2` sits on special configuration-pin territory. Treat any `PR2017`/`sspi_as_gpio` style error as a target-configuration problem first, not a reason to patch `apycula`.
  - Keep `gowin_pack.py` upstream while debugging.
  - In the OSS flow, the repo currently requests `--sspi_as_gpio --cpu_as_gpio` explicitly.
  - In the vendor flow, the project baseline should enable `CPU as regular IO` when testing the raw `E2` clock path.
  - **Constraint:** Ensure `IO_PORT "sys_clk" PULL_MODE=NONE;` is set in the `.cst` file.

## Verified Pinout Baseline (Tang Primer 25K)
After extensive testing, a stable physical baseline has been established via the `spu_tang25k_uart_led_test.v` smoketest. This gives us a guaranteed working reference point for I/O.
- **Clock (`sys_clk`):** Pin `E2` (Raw 50 MHz crystal). `PULL_MODE=NONE` is mandatory.
- **LEDs (`led[0:2]`):** Pins `L6`, `E8`, `D7` (Active low).
- **Telemetry UART (`uart_tx_telemetry`):** Pin `B11` (115,200 baud). This routes directly to the onboard BL616 MCU for instant USB-C console access, allowing us to monitor the FPGA without the RP2350.
- **Host UART (`uart_tx`):** Pin `C3`. This routes to the RP2350 microcontroller for peripheral access.
- **SPI Flash (PMOD J4 Bottom Row):** Pins `G10` (CS), `D10` (SCK), `C10` (MOSI/D1), `B10` (MISO/DO). Verified by J4 sweep `M01:EF4018`. *Note: Ensure VCC and GND are tied to real power pins.*

## Immediate Development Goals
1. **Core Boot Telemetry:** Integrate the SPU-13 core and use the verified UART link to monitor the `soft_start` sequence and Program Counter (PC).
2. **Peripheral Bridge:** Integrate RP2350 firmware for USB-A Host functionality.
