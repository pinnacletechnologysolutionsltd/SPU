#!/usr/bin/env bash
set -e
mkdir -p build

echo "=== SPU-4 Standalone Probe for Tang Primer 25K ==="

echo "--- Yosys Synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu4_probe.ys

echo "--- NextPNR Place & Route ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu4_probe.json \
    --write build/spu4_probe_pnr.json \
    --freq 12

echo "--- Gowin Bitstream Pack ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu4_probe_pnr.json \
    -o build/tang_primer_25k_spu4_probe.fs

echo "=== DONE: build/tang_primer_25k_spu4_probe.fs ==="
