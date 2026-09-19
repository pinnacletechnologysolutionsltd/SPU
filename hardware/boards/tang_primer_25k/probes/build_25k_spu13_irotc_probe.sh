#!/usr/bin/env bash
# build_25k_spu13_irotc_probe.sh — IROTC Engine standalone probe
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (IROTC engine probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_irotc_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_irotc_probe.json \
    --write build/spu13_irotc_probe_pnr.json \
    --log build/spu13_irotc_probe_nextpnr.log \
    --report build/spu13_irotc_probe_timing_report.json \
    --detailed-timing-report \
    --freq 50

echo "--- 2b. Metrics artifact ---"
python3 tools/collect_fpga_metrics.py \
    --name tang25k_irotc_probe \
    --board "Tang Primer 25K" \
    --device GW5A-LV25MG121NES \
    --toolchain "Yosys + nextpnr-himbaechel + gowin_pack" \
    --top spu13_tang25k_irotc_probe \
    --report build/spu13_irotc_probe_timing_report.json \
    --log build/spu13_irotc_probe_nextpnr.log \
    --out-json build/metrics/tang25k_irotc_probe.json \
    --out-md build/metrics/tang25k_irotc_probe.md \
    --note "Standalone IROTC term-serial engine; 13-cycle fixed slot, 0 DSP, golden-vector self-check."

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_irotc_probe_pnr.json \
    -o build/tang_primer_25k_spu13_irotc_probe.fs

echo ""
echo "=== IROTC Engine Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_irotc_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_irotc_probe.fs"
echo ""
echo "UART output at 115200 baud:"
echo "  IROTC:P E=00  ← PASS"
echo "  IROTC:F E=XX  ← FAIL (XX = error code)"
echo "LEDs: [0]=heartbeat [1]=on=engine idle [2]=off=test finished (read verdict from UART, not LEDs)"
