#!/usr/bin/env bash
set -euo pipefail

target="${1:-all}"

mkdir -p build

echo "--- 1. Yosys Synthesis (UART rescue) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_uart_rescue.ys

build_target() {
    local name="$1"
    local cst="$2"

    echo "--- 2. NextPNR (${name}) ---"
    nextpnr-himbaechel --device GW5A-LV25MG121NES \
        --vopt family=GW5A-25A \
        --vopt sspi_as_gpio \
        --vopt cst="${cst}" \
        --json build/uart_rescue.json \
        --write "build/uart_rescue_${name}_pnr.json" \
        --freq 50

    echo "--- 3. Package Bitstream (${name}) ---"
    gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
        "build/uart_rescue_${name}_pnr.json" \
        -o "build/tang_primer_25k_uart_rescue_${name}.fs"
}

case "${target}" in
    c3)
        build_target c3 hardware/boards/tang_primer_25k/tang_primer_25k_uart_rescue_c3.cst
        ;;
    b11)
        build_target b11 hardware/boards/tang_primer_25k/tang_primer_25k_uart_rescue_b11.cst
        ;;
    all)
        build_target c3 hardware/boards/tang_primer_25k/tang_primer_25k_uart_rescue_c3.cst
        build_target b11 hardware/boards/tang_primer_25k/tang_primer_25k_uart_rescue_b11.cst
        ;;
    *)
        echo "Usage: $0 [c3|b11|all]" >&2
        exit 2
        ;;
esac

echo ""
echo "=== UART Rescue Build Complete ==="
echo "C3  bitstream: build/tang_primer_25k_uart_rescue_c3.fs"
echo "B11 bitstream: build/tang_primer_25k_uart_rescue_b11.fs"
