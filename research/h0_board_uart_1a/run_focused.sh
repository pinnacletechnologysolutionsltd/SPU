#!/usr/bin/env bash
set -euo pipefail
out_arg=${1:?provide a new evidence directory}
mkdir -p build
build=$(realpath -e build)
out=$(realpath -m -- "$out_arg")
[[ "$out" == "$build"/* && ! -e "$out" ]] || { echo "evidence must be a new build/ child" >&2; exit 98; }
mkdir -p "$(dirname "$out")"
mkdir "$out"
PYTHONDONTWRITEBYTECODE=1 python3 research/h0_board_uart_1a/generate_vectors.py build/h0-board-uart-1a-vectors.hex | tee "$out/vectors.log"
cp build/h0-board-uart-1a-vectors.hex "$out/vectors.hex"
iverilog -g2012 -s board_check -o "$out/board.vvp" -f research/h0_board_uart_1a/sources.f research/h0_board_uart_1a/board_check.v
vvp "$out/board.vvp" | tee "$out/board.log"
PYTHONDONTWRITEBYTECODE=1 python3 research/h0_phys_1a/board_oracle.py "$out/board.log" | tee "$out/oracle.log"
