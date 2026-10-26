#!/usr/bin/env bash
# ==============================================================================
# tools/build_probe.sh — Unified FPGA Probe Build Dispatcher
#
# Usage:
#   bash tools/build_probe.sh 25k <probe_name>
#   bash tools/build_probe.sh list [board]
#
# Examples:
#   bash tools/build_probe.sh 25k blinky_uart
#   bash tools/build_probe.sh 25k spu13_rotc_probe
#   bash tools/build_probe.sh 25k gpu_raster
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BOARD="${1:-}"
PROBE="${2:-}"

if [ "$BOARD" = "list" ] || [ -z "$BOARD" ]; then
    echo "=== Available Tang Primer 25K Probes ==="
    ls -1 hardware/boards/tang_primer_25k/probes/ | sed 's/^build_25k_//' | sed 's/\.sh$//'
    exit 0
fi

if [ -z "$PROBE" ]; then
    echo "Error: Probe name required."
    echo "Usage: bash tools/build_probe.sh $BOARD <probe_name>"
    echo "Run 'bash tools/build_probe.sh list' to see available probes."
    exit 1
fi

case "$BOARD" in
    25k|tang25k|tang_primer_25k)
        PROBE_DIR="hardware/boards/tang_primer_25k/probes"
        TARGET="$PROBE_DIR/build_25k_${PROBE}.sh"
        if [ ! -f "$TARGET" ]; then
            TARGET_MATCH=$(find "$PROBE_DIR" -maxdepth 1 -name "*${PROBE}*.sh" | head -n 1 || true)
            if [ -n "$TARGET_MATCH" ] && [ -f "$TARGET_MATCH" ]; then
                TARGET="$TARGET_MATCH"
            else
                echo "❌ Error: Could not find probe '$PROBE' in $PROBE_DIR."
                echo "Available probes:"
                ls -1 "$PROBE_DIR" | sed 's/^build_25k_//' | sed 's/\.sh$//'
                exit 1
            fi
        fi
        echo "=== Building Tang 25K Probe: $(basename "$TARGET") ==="
        bash "$TARGET"
        ;;
    *)
        echo "❌ Error: Unknown board '$BOARD'. Supported boards: 25k"
        exit 1
        ;;
esac
