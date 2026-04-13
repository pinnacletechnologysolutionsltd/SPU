#!/usr/bin/env bash
# build_25k_smoke.sh - Fast build script for Tang Primer 25K smoke test
# Requires: oss-cad-suite
set -e

mkdir -p build/vcd build/sim

echo "--- 1. Yosys Synthesis (Smoke Test) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_smoke.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt sspi_as_gpio \
    --json build/smoke.json \
    -o cst=hardware/boards/tang_primer_25k/tang_primer_25k_smoke.cst \
    --write build/smoke_pnr.json

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio build/smoke_pnr.json -o build/tang_primer_25k_smoke.fs

echo ""
echo "=== Build Complete ==="
echo "Bitstream size: $(stat -c%s build/tang_primer_25k_smoke.fs) bytes"
echo "To flash: openFPGALoader -b tang_primer_25k build/tang_primer_25k_smoke.fs"
