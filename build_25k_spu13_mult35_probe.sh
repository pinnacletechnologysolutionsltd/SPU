#!/usr/bin/env bash
# build_25k_spu13_mult35_probe.sh — corrected shared-multiplier isolation probe
# Synthesis + place/route only, not a silicon claim.
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (35x17 shared-multiplier probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_mult35_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_mult35_probe.json \
    --write build/spu13_mult35_probe_pnr.json \
    --log build/spu13_mult35_probe_nextpnr.log \
    --report build/spu13_mult35_probe_timing_report.json \
    --detailed-timing-report \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_mult35_probe_pnr.json \
    -o build/tang_primer_25k_spu13_mult35_probe.fs

echo ""
echo "=== 35x17 Shared-Multiplier Probe: Synthesis Complete ==="
echo "This is an AREA MEASUREMENT ONLY -- not flashed, not a silicon claim."
