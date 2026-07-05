#!/usr/bin/env bash
# build_25k_spu13_lucas_phslk_probe.sh -- Tang 25K Lucas PHSLK probe
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (Lucas PHSLK probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_lucas_phslk_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_lucas_phslk_probe.json \
    --write build/spu13_lucas_phslk_probe_pnr.json \
    --log build/spu13_lucas_phslk_probe_nextpnr.log \
    --report build/spu13_lucas_phslk_probe_timing_report.json \
    --detailed-timing-report \
    --freq 12

echo "--- 2b. Metrics artifact ---"
python3 tools/collect_fpga_metrics.py \
    --name tang25k_lucas_phslk_probe \
    --board "Tang Primer 25K" \
    --device GW5A-LV25MG121NES \
    --toolchain "Yosys + nextpnr-himbaechel + gowin_pack" \
    --top spu13_tang25k_lucas_phslk_probe \
    --report build/spu13_lucas_phslk_probe_timing_report.json \
    --log build/spu13_lucas_phslk_probe_nextpnr.log \
    --out-json build/metrics/tang25k_lucas_phslk_probe.json \
    --out-md build/metrics/tang25k_lucas_phslk_probe.md \
    --note "PHSLK-only probe; covers coherent, mismatch, and zero-divisor denominator cases."

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_lucas_phslk_probe_pnr.json \
    -o build/tang_primer_25k_spu13_lucas_phslk_probe.fs

echo ""
echo "=== Lucas PHSLK Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_lucas_phslk_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_lucas_phslk_probe.fs"
echo ""
echo "UART output at 115200 baud:"
echo "  PHSLK:P  PASS (coherent/mismatch/zero-divisor cases)"
echo "  PHSLK:F  FAIL"
echo "LEDs: [0]=heartbeat [1]=off=PASS [2]=off=FAIL"
