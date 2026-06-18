#!/usr/bin/env bash
# build_25k_spu13_rplu_probe.sh - SPU-13 RPLU probe for Tang Primer 25K
set -e

mkdir -p build

export PATH=$PATH:/Users/johncurley/oss-cad-suite/bin

echo "--- 1. Yosys Synthesis (SPU-13 RPLU probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_rplu_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_rplu_probe.json \
    --write build/spu13_rplu_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio build/spu13_rplu_probe_pnr.json -o build/tang_primer_25k_spu13_rplu_probe.fs

echo ""
echo "=== SPU-13 RPLU Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_rplu_probe.fs"
echo "To load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_rplu_probe.fs"
