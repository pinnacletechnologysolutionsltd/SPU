#!/usr/bin/env bash
# build_25k_sdram_pin_probe.sh - Minimal SDRAM header pin probe for Tang Primer 25K
set -e

mkdir -p build

export PATH=$PATH:/Users/johncurley/oss-cad-suite/bin

echo "--- 1. Yosys Synthesis (SDRAM pin probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_sdram_pin_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_sdram_pin_probe.cst \
    --json build/sdram_pin_probe.json \
    --write build/sdram_pin_probe_pnr.json \
    --freq 50

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio build/sdram_pin_probe_pnr.json -o build/tang_primer_25k_sdram_pin_probe.fs

echo ""
echo "=== SDRAM Pin Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_sdram_pin_probe.fs"
