#!/usr/bin/env bash
set -euo pipefail
out=${1:?provide a new output directory}
mkdir "$out"
base=research/h0_uart_1a
iverilog -g2012 -s uart_check -o "$out/uart.vvp" "$base/uart_rx.v" "$base/uart_tx.v" "$base/uart_check.v"
vvp "$out/uart.vvp" | tee "$out/uart.log"
iverilog -g2012 -s adapter_check -o "$out/adapter.vvp" "$base/h0_uart_adapter.v" "$base/adapter_check.v"
vvp "$out/adapter.vvp" | tee "$out/adapter.log"
iverilog -g2012 -s link_check -o "$out/link.vvp" "$base/uart_rx.v" "$base/uart_tx.v" "$base/h0_uart_adapter.v" "$base/h0_uart_link.v" "$base/link_check.v"
vvp "$out/link.vvp" | tee "$out/link.log"
iverilog -g2012 -s embedded_check -o "$out/embedded.vvp" "$base/uart_rx.v" "$base/uart_tx.v" "$base/h0_uart_adapter.v" "$base/h0_uart_link.v" "$base/embedded_check.v"
vvp "$out/embedded.vvp" | tee "$out/embedded.log"
python3 "$base/mutation_controls.py" | tee "$out/mutations.log"
