#!/usr/bin/env bash
# build_25k_spu13_rplu2_arith_probe.sh — Tang 25K southbridge + RPLU2 QR/config probe
#
# Tests QLDI/QSUB instruction path and RPLU2 config receive over SPI.
# The full SOM/BTU/Padé/inverter pipeline (PIPELINE=1) is too large for 25K
# and requires the Artix-7 build. This probe uses PIPELINE=0 (config only).

set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-13 RPLU2 QR/config probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_rplu2_arith_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst \
    --json build/spu13_rplu2_arith_probe.json \
    --write build/spu13_rplu2_arith_probe_pnr.json \
    --log build/spu13_rplu2_arith_probe_nextpnr.log \
    --report build/spu13_rplu2_arith_probe_timing_report.json \
    --detailed-timing-report \
    --placed-svg build/spu13_rplu2_arith_probe_placed.svg \
    --routed-svg build/spu13_rplu2_arith_probe_routed.svg \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_rplu2_arith_probe_pnr.json \
    -o build/tang_primer_25k_spu13_rplu2_arith_probe.fs

echo ""
echo "=== SPU-13 RPLU2 QR/Config Probe Build Complete ==="
echo "Bitstream:   build/tang_primer_25k_spu13_rplu2_arith_probe.fs"
echo "Load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_rplu2_arith_probe.fs"
