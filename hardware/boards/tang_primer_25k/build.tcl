# build.tcl — GOWIN EDA batch build for Tang Primer 25K (GW5A-LV25MG121)
#
# Runs full Synthesis → Place & Route → Bitstream in headless mode.
#
# Usage (Windows, from repo root):
#   "C:\Gowin\Gowin_V1.9.x\IDE\bin\gw_sh.exe" hardware/boards/tang_primer_25k/build.tcl
#
# Usage (Linux, if GOWIN EDA is installed):
#   gw_sh hardware/boards/tang_primer_25k/build.tcl
#
# Output: build/tang_primer_25k/tang_primer_25k.fs  (flash this to the board)
#
# CC0 1.0 Universal.

# ─── Project paths (relative to repo root, where you run gw_sh) ───────────
set BOARD_DIR  "hardware/boards/tang_primer_25k"
set RTL_COMMON "hardware/common/rtl"
set RTL_SPU4   "hardware/spu4/rtl"
set RTL_SPU13  "hardware/spu13/rtl"
set OUT_DIR    "build/tang_primer_25k"

# ─── Create output directory ───────────────────────────────────────────────
file mkdir $OUT_DIR

# ─── Create / open project ────────────────────────────────────────────────
create_project -name spu13_25k -dir $OUT_DIR -pn GW5A-LV25MG121C1/I0 -opt_strategy area

# ─── Source files (same order as synth_gowin_25k.ys) ─────────────────────

# PLL stub — replaced by real rPLL during P&R
add_file -type verilog "$BOARD_DIR/pll_gowin_stub.v"

# Primitives
add_file -type verilog "$RTL_COMMON/prim/gowin_mult18.v"
add_file -type verilog "$RTL_COMMON/prim/spu_multiplier_serial.v"
add_file -type verilog "$RTL_COMMON/prim/spu_psram_ctrl.v"
add_file -type verilog "$RTL_COMMON/prim/spu_smul_tdm.v"
add_file -type verilog "$RTL_COMMON/prim/surd_multiplier.v"

# Core
add_file -type verilog "$RTL_COMMON/spu_cross_rotor.v"
add_file -type verilog "$RTL_COMMON/core/davis_gate_dsp.v"
add_file -type verilog "$RTL_COMMON/core/spu13_sequencer.v"
add_file -type verilog "$RTL_COMMON/core/spu_rotor_vault.v"
add_file -type verilog "$RTL_COMMON/core/spu_unified_alu_tdm.v"
add_file -type verilog "$RTL_COMMON/core/spu13_core.v"

# SPU-4 Sentinel
add_file -type verilog "$RTL_SPU4/spu4_decoder.v"
add_file -type verilog "$RTL_SPU4/spu_4_euclidean_alu.v"
add_file -type verilog "$RTL_SPU4/spu4_regfile.v"
add_file -type verilog "$RTL_SPU4/spu4_core.v"
add_file -type verilog "$RTL_SPU4/spu4_top.v"

# SPU-13 sub-modules
add_file -type verilog "$RTL_SPU13/spu_berry_gate.v"
add_file -type verilog "$RTL_SPU13/spu_janus_mirror.v"
add_file -type verilog "$RTL_SPU13/spu_permute_13.v"
add_file -type verilog "$RTL_SPU13/spu_13_top.v"

# System infrastructure
add_file -type verilog "$RTL_COMMON/top/spu_sierpinski_clk.v"
add_file -type verilog "$RTL_COMMON/spu_soft_start.v"
add_file -type verilog "$RTL_COMMON/top/spu_laminar_power.v"
add_file -type verilog "$RTL_COMMON/proto/SPU_ARTERY_FIFO.v"
add_file -type verilog "$RTL_COMMON/proto/SPU_WHISPER_TX.v"
add_file -type verilog "$RTL_COMMON/top/spu_system.v"

# Memory bridges
add_file -type verilog "$RTL_COMMON/mem/spu_mem_bridge_qspi.v"

# Board top
add_file -type verilog "$BOARD_DIR/spu_tang_top.v"

# Physical constraints
add_file -type cst     "$BOARD_DIR/tang_primer_25k.cst"

# ─── Synthesis options ────────────────────────────────────────────────────
set_option -synthesis_tool gowinsynthesis
set_option -top_module     spu_tang_top
set_option -verilog_std    v2001
set_option -use_cpu_as_gpio 0
set_option -output_base_name spu13_25k

# Timing: target 24 MHz (41.667 ns period)
set_option -timing_driven 1

# ─── Run full flow ────────────────────────────────────────────────────────
run all

puts "=== Build complete: $OUT_DIR/spu13_25k.fs ==="
puts "Flash with:"
puts "  openFPGALoader -b tangprimer25k $OUT_DIR/spu13_25k.fs"
