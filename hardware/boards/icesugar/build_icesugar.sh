#!/usr/bin/env bash
# build_icesugar.sh — iCEsugar v1.5 (iCE40UP5K-SG48) build flow
# Usage:
#   ./build_icesugar.sh          # synth + pnr + pack
#   ./build_icesugar.sh synth    # synthesis only
#   ./build_icesugar.sh pnr      # place-and-route only (requires build/icesugar/icesugar.json)
#   ./build_icesugar.sh pack     # pack bitstream only (requires build/icesugar/icesugar.asc)
#   ./build_icesugar.sh flash    # flash via icesprog (iCEsugar USB programmer)

set -e

# Search for yosys and nextpnr if not in path
YOSYS=$(which yosys || echo "yosys")
NEXTPNR=$(which nextpnr-ice40 || echo "nextpnr-ice40")
ICEPACK=$(which icepack || echo "icepack")
ICESPROG=$(which icesprog || echo "icesprog")

PCF=hardware/boards/icesugar/icesugar.pcf
TOP=spu_icesugar_top
DEVICE=up5k
PACKAGE=sg48
BUILD_DIR=build/icesugar

mkdir -p $BUILD_DIR

STEP="${1:-all}"

synth() {
    echo "=== Synthesis (iCE40 UP5K) ==="
    $YOSYS hardware/boards/icesugar/synth_icesugar.ys
}

pnr() {
    echo "=== Place-and-Route (nextpnr-ice40 UP5K SG48) ==="
    $NEXTPNR \
        --$DEVICE --package $PACKAGE \
        --json $BUILD_DIR/icesugar.json \
        --pcf $PCF \
        --asc $BUILD_DIR/icesugar.asc \
        --freq 12 \
        --opt-timing
}

pack() {
    echo "=== Bitstream Pack ==="
    $ICEPACK $BUILD_DIR/icesugar.asc $BUILD_DIR/icesugar.bin
    echo "Output: $BUILD_DIR/icesugar.bin ($(du -h $BUILD_DIR/icesugar.bin | cut -f1))"
}

flash() {
    echo "=== Flash via icesprog ==="
    $ICESPROG $BUILD_DIR/icesugar.bin
}

case "$STEP" in
    synth) synth ;;
    pnr)   pnr   ;;
    pack)  pack  ;;
    flash) flash ;;
    all)   synth && pnr && pack ;;
    *)     echo "Unknown step: $STEP"; exit 1 ;;
esac

echo "=== Done ==="
