#!/usr/bin/env bash
# build_25k_spu13_lucas_mac_probe.sh — Lucas MAC standalone zero-drift probe
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (Lucas MAC probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_lucas_mac_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_lucas_mac_probe.json \
    --write build/spu13_lucas_mac_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_lucas_mac_probe_pnr.json \
    -o build/tang_primer_25k_spu13_lucas_mac_probe.fs

echo ""
echo "=== Lucas MAC Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_lucas_mac_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_lucas_mac_probe.fs"
echo ""
echo "UART output at 115200 baud:"
echo "  LUCAS:P  ← PASS (all 4 ops + 100-period zero-drift)"
echo "  LUCAS:F  ← FAIL"
echo "LEDs: [0]=heartbeat [1]=off=PASS [2]=off=FAIL"
