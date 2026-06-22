#!/usr/bin/env bash
# build_25k_spu13_southbridge.sh - Minimal Tang 25K RP2350 SPI southbridge demo
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-13 southbridge probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_fpga.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_fpga.cst \
    --json build/spu13_southbridge.json \
    --write build/spu13_southbridge_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_southbridge_pnr.json \
    -o build/tang_primer_25k_spu13_fpga.fs

echo ""
echo "=== SPU-13 FPGA Bitstream Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_fpga.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_fpga.fs"
