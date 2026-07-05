#!/usr/bin/env bash
# build_25k_spu13_rotc_probe.sh -- Tang 25K ROTC 0-5 standalone probe
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (ROTC probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_rotc_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_rotc_probe.json \
    --write build/spu13_rotc_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_rotc_probe_pnr.json \
    -o build/tang_primer_25k_spu13_rotc_probe.fs

echo ""
echo "=== ROTC Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_rotc_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_rotc_probe.fs"
echo ""
echo "UART output at 115200 baud:"
echo "  ROTC:P A:5 E:00  PASS (ROTC 0-5 trace + period closure)"
echo "  ROTC:F A:<n> E:<code>  FAIL"
echo "LEDs: [0]=heartbeat [1]=off=PASS [2]=off=FAIL"
