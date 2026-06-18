#!/usr/bin/env bash
set -euo pipefail

mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-13 boot probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_boot_probe.ys

echo "--- 2. NextPNR (SPU-13 boot probe) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_spu13_boot_probe.cst \
    --json build/spu13_boot_probe.json \
    --write build/spu13_boot_probe_pnr.json \
    --freq 50

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_boot_probe_pnr.json \
    -o build/tang_primer_25k_spu13_boot_probe.fs

echo ""
echo "=== SPU-13 Boot Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_boot_probe.fs"
