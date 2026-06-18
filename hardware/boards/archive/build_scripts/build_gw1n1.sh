#!/usr/bin/env bash
# build_gw1n1.sh — GW1N-1 / GW1NZ-1 (Tang Nano 1K) full build
# Tier 1 Micro: Whisper Beacon — ~601 LUT, 0 DSP, BSRAM seed, no PSRAM
set -e

CHIPDB=~/.oss-cad-suite/share/nextpnr/himbaechel/gowin/chipdb-GW1NZ-1.bin
DEVICE=GW1NZ-LV1QN48C6/I5

mkdir -p build

echo "=== [1/4] Synthesis ==="
yosys synth_gw1n1.ys

echo "=== [2/4] Place & Route ==="
nextpnr-himbaechel \
    --device "$DEVICE" \
    --chipdb "$CHIPDB" \
    --json build/gw1n1.json \
    -o "cst=hardware/boards/gw1n1/gw1n1.cst" \
    --write build/gw1n1_pnr.json \
    --freq 27

echo "=== [3/4] Pack bitstream ==="
gowin_pack -d GW1NZ-1 build/gw1n1_pnr.json -o build/gw1n1.fs

echo "=== [4/4] Flash (openFPGALoader — connect Tang Nano 1K via USB) ==="
echo "    Run manually: openFPGALoader -b tangnano1k build/gw1n1.fs"
echo ""
echo "Build complete: build/gw1n1.fs"
