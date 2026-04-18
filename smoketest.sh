#!/usr/bin/env bash
# smoketest.sh — Tang Primer 25K Verilator Smoke Test
# Usage: ./smoketest.sh

set -e

echo "--- SPU-4 Sentinel Smoke Test (Verilator) ---"

# Step 1: Check if Verilator is installed
if ! command -v verilator &> /dev/null; then
    echo "Error: verilator not found. Please install it to run smoke tests."
    exit 1
fi

# Step 2: Ensure build directory exists
mkdir -p build/smoketest

# Step 3: Run the simulation
# Assuming the binary is already compiled in the standard verilator path
# or we can re-compile if needed. 
SMOKE_BIN="build/verilator/tang25k_smoketest_tb/Vtang25k_smoketest_tb"

if [ -f "$SMOKE_BIN" ]; then
    echo "Executing: $SMOKE_BIN"
    $SMOKE_BIN
else
    echo "Warning: Smoketest binary not found at $SMOKE_BIN."
    echo "Attempting to locate any smoketest binary..."
    ALT_BIN=$(find build/verilator -name "Vtang25k_smoketest_tb" | head -n 1)
    if [ -n "$ALT_BIN" ]; then
        echo "Executing found binary: $ALT_BIN"
        $ALT_BIN
    else
        echo "Error: No smoketest binary found. Please compile the testbench first."
        exit 1
    fi
fi

echo "--- Smoketest Complete ---"
