#!/bin/bash

# iCEsugar SPU-13 Build & Deploy Script
# Objective: Synthesize the Modular Sovereign Engine for iCE40UP5K.

TOP="spu_icesugar_top"
PCF="hardware/ice40_regular/icesugar_spu.pcf"
BUILD_DIR="build_icesugar"

mkdir -p $BUILD_DIR

echo "--- [SPU-13 Build] Synthesizing Sovereign Engine ---"
yosys -p "read_verilog -sv -I hardware/common/rtl/ -I hardware/common/rtl/core/ \
    hardware/boards/icesugar/spu_icesugar_top.v \
    hardware/common/rtl/top/spu_sierpinski_clk.v \
    hardware/common/rtl/top/spu_ghost_boot.v \
    hardware/common/rtl/mem/spu_mem_bridge_qspi.v \
    hardware/common/rtl/prim/spu_psram_ctrl.v \
    hardware/common/rtl/core/spu13_core.v \
    hardware/common/rtl/core/spu13_sequencer.v \
    hardware/common/rtl/core/spu_rotor_vault.v \
    hardware/common/rtl/spu_cross_rotor.v \
    hardware/common/rtl/core/davis_gate_dsp.v \
    hardware/common/rtl/spu_artery_tx.v; \
    synth_ice40 -top $TOP -json $BUILD_DIR/$TOP.json"

echo "--- [SPU-13 Build] Routing Manifold (nextpnr) ---"
nextpnr-ice40 --up5k --package sg48 --json $BUILD_DIR/$TOP.json --pcf $PCF --asc $BUILD_DIR/$TOP.asc

echo "--- [SPU-13 Build] Packing Bitstream ---"
icepack $BUILD_DIR/$TOP.asc $BUILD_DIR/$TOP.bin

echo "--- [SPU-13 Build] DONE ---"
echo "Bitstream: $BUILD_DIR/$TOP.bin"
echo "To deploy: iceprog $BUILD_DIR/$TOP.bin"
