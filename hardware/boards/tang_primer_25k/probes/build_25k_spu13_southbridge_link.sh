#!/usr/bin/env bash
# build_25k_spu13_southbridge_link.sh — SPI link-only probe
# Proves the RP2350↔FPGA SPI link without any core compute overhead.
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (SPI link-only) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_southbridge_link.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst \
    --json build/spu13_southbridge_link.json \
    --write build/spu13_southbridge_link_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_southbridge_link_pnr.json \
    -o build/tang_primer_25k_spu13_southbridge_link.fs

echo ""
echo "=== SPI Link Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_southbridge_link.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_southbridge_link.fs"
echo "Test:     python3 tools/rp2040_flash_pmod.py --port <tty> diag"
