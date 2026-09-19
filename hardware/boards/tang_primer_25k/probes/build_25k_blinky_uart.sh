#!/usr/bin/env bash
# build_25k_blinky_uart.sh -- bench sanity probe: LEDs + repeating UART line.
# No SPU logic. Isolates bitstream load, clock, LED pins, and the C3->BL616
# USB-CDC UART leg. Expect three blink rates and "BLINK" lines at 115200.
set -e
mkdir -p build

echo "--- Yosys Synthesis (blinky+uart sanity probe) ---"
yosys -p "read_verilog hardware/boards/tang_primer_25k/tang25k_blinky_uart.v; \
    synth_gowin -family gw5a -top tang25k_blinky_uart -json build/blinky_uart.json"

echo "--- NextPNR Place & Route ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/blinky_uart.json \
    --write build/blinky_uart_pnr.json \
    --freq 12

echo "--- Gowin Bitstream Pack ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/blinky_uart_pnr.json \
    -o build/tang_primer_25k_blinky_uart.fs

echo "=== DONE: build/tang_primer_25k_blinky_uart.fs ==="
echo "Flash:  openFPGALoader -b tangprimer25k build/tang_primer_25k_blinky_uart.fs"
echo "Watch:  picocom -b 115200 <BL616 CDC tty>  ->  repeating BLINK lines"
