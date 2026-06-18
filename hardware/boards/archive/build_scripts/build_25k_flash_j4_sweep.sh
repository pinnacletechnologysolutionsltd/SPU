#!/usr/bin/env bash
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_flash_j4_sweep.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_flash_j4_sweep.cst \
    --json build/flash_j4_sweep.json \
    --write build/flash_j4_sweep_pnr.json \
    --freq 50

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio build/flash_j4_sweep_pnr.json -o build/tang_primer_25k_flash_j4_sweep.fs

echo ""
echo "=== Build Complete ==="
echo "Bitstream size: $(stat -f%z build/tang_primer_25k_flash_j4_sweep.fs) bytes"
echo "To flash: openFPGALoader -b tangprimer25k -f build/tang_primer_25k_flash_j4_sweep.fs"
