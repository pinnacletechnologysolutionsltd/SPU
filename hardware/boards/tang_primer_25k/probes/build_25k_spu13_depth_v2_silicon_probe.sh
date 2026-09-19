#!/usr/bin/env bash
# build_25k_spu13_depth_v2_silicon_probe.sh — depth-v2 first silicon
# verification. Fixed test triangle, self-checks A_z/B_z/C_z/frac_bits
# and one per-pixel depth sample against hardcoded oracle-derived
# expected values, reports P/F + the raw depth over UART (115200 baud).
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (depth-v2 silicon probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_depth_v2_silicon_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_depth_v2_silicon_probe.json \
    --write build/spu13_depth_v2_silicon_probe_pnr.json \
    --log build/spu13_depth_v2_silicon_probe_nextpnr.log \
    --report build/spu13_depth_v2_silicon_probe_timing_report.json \
    --detailed-timing-report \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_depth_v2_silicon_probe_pnr.json \
    -o build/tang_primer_25k_spu13_depth_v2_silicon_probe.fs

echo ""
echo "=== Depth-v2 Silicon Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_depth_v2_silicon_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_depth_v2_silicon_probe.fs"
echo ""
echo "UART output at 115200 baud:"
echo "  DEPTH2:P D=00007EB7  <- PASS, depth=32439 (0x7eb7) at pixel (300,200)"
echo "  DEPTH2:F D=........  <- FAIL, reports the actual computed depth"
echo "LEDs: [0]=heartbeat [1]=off=PASS [2]=off=FAIL"
