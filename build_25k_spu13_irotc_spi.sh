#!/usr/bin/env bash
# build_25k_spu13_irotc_spi.sh — Tang 25K IROTC over southbridge SPI
# MATH=1 southbridge + CORE_ENABLE_IROTC=1: A5 rotations via SPI 0xB1, results via 0xAE.
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-13 IROTC SPI spin) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_irotc_spi.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst \
    --json build/spu13_irotc_spi.json \
    --write build/spu13_irotc_spi_pnr.json \
    --log build/spu13_irotc_spi_nextpnr.log \
    --report build/spu13_irotc_spi_timing_report.json \
    --detailed-timing-report \
    --placed-svg build/spu13_irotc_spi_placed.svg \
    --routed-svg build/spu13_irotc_spi_routed.svg \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_irotc_spi_pnr.json \
    -o build/tang_primer_25k_spu13_irotc_spi.fs

echo ""
echo "=== SPU-13 Southbridge Bitstream Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_irotc_spi.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_irotc_spi.fs"
