#!/usr/bin/env bash
# build_25k_sdram_min_probe.sh — Clean SDRAM test for Tang Primer 25K
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_sdram_min_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/sdram_min_probe.json \
    --write build/sdram_min_probe_pnr.json --freq 12

echo "--- 3. Package ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/sdram_min_probe_pnr.json \
    -o build/tang_primer_25k_sdram_min_probe.fs

echo "=== Bitstream: build/tang_primer_25k_sdram_min_probe.fs ==="
