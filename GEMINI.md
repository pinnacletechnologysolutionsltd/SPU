# SPU-13 Cluster Architecture & Workflow (Tang Primer 25K)

## Current System Architecture
- **Compute Engine:** GW5A-25A FPGA (Tang Primer 25K) running Dual SPU-13 + 8× SPU-4 satellites.
- **I/O Host:** RP2350 microcontroller (USB-A port) handling USB stack/peripherals, bridged to FPGA.
- **Bridge/Console:** BL616 MCU (USB-C port) providing JTAG programming and serial UART telemetry.
- **Clocking:** Raw 50 MHz crystal (PLLA bypassed in open-source synthesis flow).
- **Storage:** Onboard 32 MB SDRAM (W9825G6KH-6); SD card (optional) for asset streaming via `spu_sd_inhaler`.

## Current Status & Known Issues
- Bitstream synthesis is complete and functional in SRAM.
- UART telemetry through the USB-C bridge is silent, suggesting a clock-gating or reset-sequencing stall in the SPU-13 core.
- Flash programming (`openFPGALoader -f`) is failing (write-protect/driver issue), currently defaulting to SRAM loading.

## Immediate Development Goals
1. **Verification:** Force a simple heartbeat (1Hz toggle) on the `uart_tx` pin (C3) to verify the BL616 UART bridge link.
2. **Core Boot:** Debug the SPU-13 reset sequence once serial heartbeat is established.
3. **Firmware:** Integrate RP2350 firmware for USB-A Host functionality.
