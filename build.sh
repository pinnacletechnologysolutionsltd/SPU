#!/bin/bash
# SPU Master Build Script
# Usage: ./build.sh [target]
# Targets: 25k, 25k-ext, 9k, icesugar, ecp5, smoketest, all

# Default to help if no target provided
if [ -z "$1" ]; then
    echo "SPU Build System"
    echo "Usage: ./build.sh [25k | 25k-ext | 9k | icesugar | ecp5 | smoketest | all]"
    exit 1
fi

TARGET=$1

# Ensure build directories exist
mkdir -p build/tang_primer_25k
mkdir -p build/tang_primer_25k_extram
mkdir -p build/tang_nano_9k
mkdir -p build/icesugar
mkdir -p build/ecp5_25f
mkdir -p build/smoketest

build_25k() {
    echo "--- Building Tang Primer 25k (Standard) ---"
    yosys hardware/boards/tang_primer_25k/synth_gowin_25k.ys
}

build_25k_ext() {
    echo "--- Building Tang Primer 25k (External SDRAM) ---"
    yosys hardware/boards/tang_primer_25k/synth_gowin_25k_extram.ys
}

build_9k() {
    echo "--- Building Tang Nano 9k ---"
    yosys hardware/boards/tang_nano_9k/synth_gowin_9k.ys
}

build_icesugar() {
    echo "--- Building iCEsugar ---"
    ./hardware/boards/icesugar/build_icesugar.sh synth
}

build_ecp5() {
    echo "--- Building ECP5-25F ---"
    yosys hardware/boards/ecp5_25f/synth_ecp5.ys
}

run_smoketest() {
    ./smoketest.sh
}

case $TARGET in
    25k)
        build_25k
        ;;
    25k-ext)
        build_25k_ext
        ;;
    9k)
        build_9k
        ;;
    icesugar)
        build_icesugar
        ;;
    ecp5)
        build_ecp5
        ;;
    smoketest)
        run_smoketest
        ;;
    all)
        build_25k
        build_25k_ext
        build_9k
        build_icesugar
        build_ecp5
        ;;
    *)
        echo "Unknown target: $TARGET"
        exit 1
        ;;
esac

echo "Build complete. Artifacts in build/$TARGET/"
