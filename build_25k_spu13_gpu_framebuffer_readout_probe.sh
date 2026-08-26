#!/usr/bin/env bash
# build_25k_spu13_gpu_framebuffer_readout_probe.sh — digital framebuffer
# readout proof. Streams the real depth-v2 + depth-compare pipeline's
# rendered image over UART (115200 baud) for a host to reconstruct --
# no video PMOD/PLL needed or available on this board.
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (framebuffer readout probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_gpu_framebuffer_readout_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_gpu_framebuffer_readout_probe.json \
    --write build/spu13_gpu_framebuffer_readout_probe_pnr.json \
    --log build/spu13_gpu_framebuffer_readout_probe_nextpnr.log \
    --report build/spu13_gpu_framebuffer_readout_probe_timing_report.json \
    --detailed-timing-report \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu13_gpu_framebuffer_readout_probe_pnr.json \
    -o build/tang_primer_25k_spu13_gpu_framebuffer_readout_probe.fs

echo ""
echo "=== Framebuffer Readout Probe: Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_gpu_framebuffer_readout_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_gpu_framebuffer_readout_probe.fs"
echo "Readout: python3 tools/read_gpu_framebuffer.py /dev/ttyUSB1"
