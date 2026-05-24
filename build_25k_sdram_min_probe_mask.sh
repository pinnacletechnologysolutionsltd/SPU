#!/usr/bin/env bash
# build_25k_sdram_min_probe_mask.sh - SDRAM min probe with DQ[10] stuck-high masked
set -e

mkdir -p build

export PATH=$PATH:/Users/johncurley/oss-cad-suite/bin

echo "--- 1. Yosys Synthesis (SDRAM min probe, DQ[10] masked) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_sdram_min_probe_dq10_masked.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/sdram_min_probe_mask.json \
    --write build/sdram_min_probe_mask_pnr.json \
    --freq 50

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio build/sdram_min_probe_mask_pnr.json -o build/tang_primer_25k_sdram_min_probe_mask.fs

echo ""
echo "=== SDRAM Min Probe (DQ10 Masked) Build Complete ==="
echo "Bitstream: build/tang_primer_25k_sdram_min_probe_mask.fs"
echo "To load: openFPGALoader -b tangprimer25k build/tang_primer_25k_sdram_min_probe_mask.fs"
