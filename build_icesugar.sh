#!/usr/bin/env bash
# build_icesugar.sh — iCEsugar v1.5 (iCE40UP5K-SG48) build flow
# Usage:
#   ./build_icesugar.sh          # synth + pnr + pack
#   ./build_icesugar.sh synth    # synthesis only
#   ./build_icesugar.sh pnr      # place-and-route only (requires build/icesugar.json)
#   ./build_icesugar.sh pack     # pack bitstream only (requires build/icesugar_pnr.json)
#   ./build_icesugar.sh flash    # flash via icesprog (iCEsugar USB programmer)

set -e

OSS=~/.oss-cad-suite/bin
PCF=hardware/boards/icesugar/icesugar.pcf
TOP=spu_icesugar_top
DEVICE=up5k
PACKAGE=sg48

mkdir -p build

STEP="${1:-all}"

synth() {
    echo "=== Synthesis (iCE40 UP5K) ==="
    $OSS/yosys synth_icesugar.ys
}

pnr() {
    echo "=== Place-and-Route (nextpnr-ice40 UP5K SG48) ==="
    $OSS/nextpnr-ice40 \
        --$DEVICE --package $PACKAGE \
        --json build/icesugar.json \
        --pcf $PCF \
        --asc build/icesugar.asc \
        --freq 12 \
        --opt-timing
}

pack() {
    echo "=== Bitstream Pack ==="
    $OSS/icepack build/icesugar.asc build/icesugar.bin
    echo "Output: build/icesugar.bin ($(du -h build/icesugar.bin | cut -f1))"
}

flash() {
    echo "=== Flash via icesprog ==="
    icesprog build/icesugar.bin
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
