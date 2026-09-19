#!/usr/bin/env bash
# build_25k_blinky_uart_div2.sh -- bench sanity probe: same as
# build_25k_blinky_uart.sh but running everything through
# spu_tang25k_clk_pixel_div2.v (50MHz->25MHz) instead of raw sys_clk.
# Isolates whether that divider is alive on real silicon. Expect three
# blink rates and "DIV2K" lines at 115200 baud.
set -e
mkdir -p build

echo "--- Yosys Synthesis (blinky+uart+clkdiv sanity probe) ---"
yosys -p "read_verilog hardware/boards/tang_primer_25k/tang25k_blinky_uart_div2.v \
    hardware/boards/tang_primer_25k/spu_tang25k_clk_pixel_div2.v; \
    synth_gowin -family gw5a -top tang25k_blinky_uart_div2 -json build/blinky_uart_div2.json"

echo "--- NextPNR Place & Route ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/blinky_uart_div2.json \
    --write build/blinky_uart_div2_pnr.json \
    --freq 12

echo "--- Gowin Bitstream Pack ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/blinky_uart_div2_pnr.json \
    -o build/tang_primer_25k_blinky_uart_div2.fs

echo "=== DONE: build/tang_primer_25k_blinky_uart_div2.fs ==="
echo "Flash:  openFPGALoader -b tangprimer25k build/tang_primer_25k_blinky_uart_div2.fs"
