#!/usr/bin/env bash
# build_25k_spu13_southbridge.sh — Tang 25K RP2350 SPI southbridge
# FPGA pure-compute engine; RP2350 owns boot, table hydration, instruction streaming.
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-13 southbridge) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_southbridge.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst \
    --json build/spu13_southbridge.json \
    --write build/spu13_southbridge_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_southbridge_pnr.json \
    -o build/tang_primer_25k_spu13_southbridge.fs

echo ""
echo "=== SPU-13 Southbridge Bitstream Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_southbridge.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_southbridge.fs"
