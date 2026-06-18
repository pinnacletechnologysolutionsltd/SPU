#!/usr/bin/env bash
# build_full_spu13.sh - Full SPU-13 Cluster Synthesis (Tang Primer 25K)
# Targets: Dual Mother Nodes + 8× SPU-4 Satellites, 32MB SDRAM
set -e

mkdir -p build/tang_primer_25k

echo "--- 1. Yosys Synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k.ys

echo "--- 2. Place & Route (nextpnr-himbaechel) ---"
nextpnr-himbaechel \
    --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/tang_primer_25k/tang_primer_25k.json \
    --write build/tang_primer_25k/tang_primer_25k_pnr.json \
    --chipdb /home/john/.oss-cad-suite/share/nextpnr/himbaechel/gowin/chipdb-GW5A-25A.bin

echo "--- 3. Bitstream Generation ---"
gowin_pack -d GW5A-25A --sspi_as_gpio -o build/tang_primer_25k.fs build/tang_primer_25k/tang_primer_25k_pnr.json

echo ""
echo "=== Build Complete ==="
echo "Bitstream: build/tang_primer_25k.fs"
echo "To flash: openFPGALoader -b tangprimer25k build/tang_primer_25k.fs"
