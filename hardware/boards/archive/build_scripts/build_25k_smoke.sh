#!/usr/bin/env bash
# build_25k_smoke.sh - Fully configured build script (Restoring "working" flag set).
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_smoke.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_smoke.cst \
    --json build/smoke.json \
    --write build/smoke_pnr.json \
    --freq 50

echo "--- 3. Package Bitstream ---"
# Re-adding the full set of configuration flags that worked previously
gowin_pack -d GW5A-25A --sspi_as_gpio --cpu_as_gpio build/smoke_pnr.json -o build/tang_primer_25k_smoke.fs

echo ""
echo "=== Build Complete ==="
echo "Bitstream size: $(stat -f%z build/tang_primer_25k_smoke.fs) bytes"
echo "To flash: openFPGALoader -b tangprimer25k -f build/tang_primer_25k_smoke.fs"
