#!/usr/bin/env bash
# build_25k_spu13_som_sidecar.sh — Tang 25K standalone SOM edge classifier
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SOM sidecar) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_sidecar.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst \
    --json build/spu13_som_sidecar.json \
    --write build/spu13_som_sidecar_pnr.json \
    --log build/spu13_som_sidecar_nextpnr.log \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_som_sidecar_pnr.json \
    -o build/tang_primer_25k_spu13_som_sidecar.fs

echo ""
echo "=== SOM Sidecar Bitstream Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_som_sidecar.fs"
