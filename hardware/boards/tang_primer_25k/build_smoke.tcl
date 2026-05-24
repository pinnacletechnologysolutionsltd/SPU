# build_smoke.tcl — GOWIN EDA batch build for Tang Primer 25K Smoke Test
#
# Runs full Synthesis → Place & Route → Bitstream in headless mode.
# Target: GW5A-LV25MG121C1/I0
#
# Usage (Windows, from repo root):
#   "C:\Gowin\Gowin_V1.9.10.x\IDE\bin\gw_sh.exe" hardware/boards/tang_primer_25k/build_smoke.tcl
#
# Usage (Linux, if GOWIN EDA is installed):
#   gw_sh hardware/boards/tang_primer_25k/build_smoke.tcl
#

set BOARD_DIR  "hardware/boards/tang_primer_25k"
set RTL_ROOT   "hardware/rtl"
set OUT_DIR    "build/tang_primer_25k_smoke"

file mkdir $OUT_DIR
create_project -name smoke_25k -dir $OUT_DIR -pn GW5A-LV25MG121C1/I0 -opt_strategy area

# Add files from synth_gowin_25k_smoke.ys
add_file -type verilog "$BOARD_DIR/pll_gowin_stub.v"
add_file -type verilog "$BOARD_DIR/gowin_sp_stub.v"

add_file -type verilog "$RTL_ROOT/top/spu_sierpinski_clk.v"
add_file -type verilog "$RTL_ROOT/common/sync/spu_soft_start.v"
add_file -type verilog "$RTL_ROOT/common/prim/spu_multiplier_serial.v"

add_file -type verilog "$RTL_ROOT/core/shared/davis_gate_dsp.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_decoder.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_euclidean_alu.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_regfile.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_core.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_top.v"
add_file -type verilog "$RTL_ROOT/gpu/spu4_bram_ip.v"

add_file -type verilog "hardware/boards/tang25k/spu_tang25k_top.v"
add_file -type cst     "$BOARD_DIR/tang_primer_25k_smoke.cst"

set_option -synthesis_tool gowinsynthesis
set_option -top_module     spu_tang25k_top
set_option -verilog_std    v2001
set_option -use_cpu_as_gpio 1
set_option -output_base_name smoke_25k

run all

puts "=== Smoke Test Build complete: $OUT_DIR/smoke_25k.fs ==="
puts "Flash with:"
puts "  openFPGALoader -b tangprimer25k $OUT_DIR/smoke_25k.fs"
