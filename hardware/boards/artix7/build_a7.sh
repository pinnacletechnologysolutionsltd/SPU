#!/usr/bin/env bash
# build_a7.sh — SPU-13 Artix-7 Build Script (v1.1)
#
# Usage:
#   bash build_a7.sh                           # FULL spin on 100T
#   bash build_a7.sh 200t multimedia            # MULTIMEDIA spin on 200T
#   bash build_a7.sh 35t robotics synth          # synth only, ROBOTICS spin on 35T
#   bash build_a7.sh 100t intelligence           # INTELLIGENCE spin on 100T
#   bash build_a7.sh 100t sensor                 # SENSOR spin (minimal)
#
# Spins: multimedia | intelligence | robotics | full | sensor | custom

set -euo pipefail

DEVICE_CHIP="${1:-100t}"
SPIN="${2:-full}"
STEP="${3:-all}"

# Resolve spin to uppercase
SPIN=$(echo "$SPIN" | tr '[:lower:]' '[:upper:]')

case "$DEVICE_CHIP" in
    35t)
        PART="xc7a35tcsg324-1"; XDC="hardware/boards/artix7/spu_a7_35t.xdc"
        JSON="build/spu_a7_35t_${SPIN}.json"
        BITSTREAM="build/spu_a7_35t_${SPIN}.bit";;
    100t)
        PART="xc7a100tcsg324-1"; XDC="hardware/boards/artix7/spu_a7_100t.xdc"
        JSON="build/spu_a7_100t_${SPIN}.json"
        BITSTREAM="build/spu_a7_100t_${SPIN}.bit";;
    200t)
        PART="xc7a200tsbg484-1"; XDC="hardware/boards/artix7/spu_a7_200t.xdc"
        JSON="build/spu_a7_200t_${SPIN}.json"
        BITSTREAM="build/spu_a7_200t_${SPIN}.bit";;
    *) echo "Unknown device: $DEVICE_CHIP (use 35t|100t|200t)"; exit 1;;
esac

YS="hardware/boards/artix7/synth_a7.ys"

echo "=== SPU-13 Artix-7 Build ==="
echo "  Device: $DEVICE_CHIP ($PART)"
echo "  Spin:   $SPIN"
echo "  Step:   $STEP"
echo ""

synth() {
    echo ">>> Yosys Synthesis <<<"
    mkdir -p build
    yosys -p "chparam -set SPIN \"$SPIN\" spu_a7_top" "$YS"
}

pnr() {
    echo ">>> NextPNR Place & Route <<<"
    nextpnr-xilinx --chip "$PART" --xdc "$XDC" \
        --json "$JSON" --write "${JSON}.pnr.json" --freq 50
}

pack() {
    echo ">>> Bitstream Generation <<<"
    if command -v xc7frames2bit &>/dev/null; then
        xc7frames2bit --part_file "$PART" \
            --fasm "${JSON}.pnr.fasm" --bit "$BITSTREAM"
        echo "  Bitstream: $BITSTREAM"
    else
        echo "  Install Project X-Ray tools for bitstream generation."
        echo "  Or open Vivado and run: source hardware/boards/artix7/pack_a7.tcl"
    fi
}

flash() {
    [ -f "$BITSTREAM" ] || { echo "No bitstream. Build first."; exit 1; }
    openFPGALoader -b arty_a7 "$BITSTREAM"
}

case "$STEP" in
    synth) synth;;  pnr) pnr;;  pack) pack;;  flash) flash;;
    all) synth && pnr && pack;;
    *) echo "Unknown step: $STEP"; exit 1;;
esac
