#!/usr/bin/env bash
# build_25k_spu13_som_hydrate_probe.sh -- Tang 25K SOM BRAM hydration probe
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (SOM hydration probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_hydrate_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_som_hydrate_probe.json \
    --write build/spu13_som_hydrate_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_som_hydrate_probe_pnr.json \
    -o build/tang_primer_25k_spu13_som_hydrate_probe.fs

echo ""
echo "=== SOM Hydration Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_som_hydrate_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_som_hydrate_probe.fs"
echo ""
echo "UART output at 115200 baud:"
echo "  HYD:P T:3 B:6 E:00  PASS (initial read, write/readback, byte-enable preserve)"
echo "  HYD:F T:<n> B:<b> E:<code>  FAIL"
echo "LEDs: [0]=heartbeat [1]=off=PASS [2]=off=FAIL"
