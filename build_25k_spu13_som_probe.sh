#!/usr/bin/env bash
# build_25k_spu13_som_probe.sh — SOM classification probe for Tang Primer 25K
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SOM probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_som_probe.cst \
    --json build/spu13_som_probe.json \
    --write build/spu13_som_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_som_probe_pnr.json \
    -o build/tang_primer_25k_spu13_som_probe.fs

echo ""
echo "=== SOM Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_som_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_som_probe.fs"
echo ""
echo "Connect USB-UART to C3 (TX) + GND at 115200 baud."
echo "Receives hex_q telemetry on SOM_CLASSIFY results."
