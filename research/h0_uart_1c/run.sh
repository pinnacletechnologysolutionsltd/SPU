#!/usr/bin/env bash
set -euo pipefail
out=${1:?provide a new output directory}
mkdir -p "$(dirname "$out")"
mkdir "$out"
iverilog -g2012 -s serial_check -o "$out/serial.vvp" -f research/h0_uart_1c/sources.f research/h0_uart_1c/serial_check.v
vvp "$out/serial.vvp" | tee "$out/serial.log"
python3 research/h0_phys_1a/board_oracle.py "$out/serial.log" | tee "$out/oracle.log"
iverilog -g2012 -s edge_check -o "$out/edge.vvp" research/h0_uart_1a/h0_uart_adapter.v research/h0_uart_1c/edge_check.v
vvp "$out/edge.vvp" | tee "$out/edge.log"
python3 research/h0_uart_1c/edge_mutations.py | tee "$out/edge_mutations.log"
PYTHONDONTWRITEBYTECODE=1 python3 research/h0_uart_1c/test_host_loader.py 2>&1 | tee "$out/host.log"
iverilog -g2012 -s refusals -o "$out/refusals.vvp" -f research/h0_uart_1c/sources.f research/h0_uart_1c/refusals.v
vvp "$out/refusals.vvp" | tee "$out/refusals.log"
python3 research/h0_uart_1c/endpoint_mutations.py "$out/endpoint_mutants" | tee "$out/endpoint_mutations.log"
