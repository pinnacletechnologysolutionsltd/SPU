#!/usr/bin/env bash
# build_25k_b2_hold_probe.sh - Hold Tang Primer 25K SDRAM-header B2 low.
set -e

mkdir -p build

export PATH=$PATH:/Users/johncurley/oss-cad-suite/bin

echo "--- 1. Yosys Synthesis (B2 hold-low probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_b2_hold_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_b2_hold_probe.cst \
    --json build/b2_hold_probe.json \
    --write build/b2_hold_probe_pnr.json \
    --freq 50

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio build/b2_hold_probe_pnr.json -o build/tang_primer_25k_b2_hold_probe.fs

echo ""
echo "=== B2 Hold-Low Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_b2_hold_probe.fs"
