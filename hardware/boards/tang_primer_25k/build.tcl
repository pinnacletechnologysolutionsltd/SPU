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
# ─── Project paths (relative to repo root, where you run gw_sh) ───────────
set BOARD_DIR  "hardware/boards/tang_primer_25k"
set RTL_ROOT   "hardware/rtl"
set OUT_DIR    "build/tang_primer_25k"

# ─── Create output directory ───────────────────────────────────────────────
file mkdir $OUT_DIR

# ─── Create / open project ────────────────────────────────────────────────
create_project -name spu13_25k -dir $OUT_DIR -pn GW5A-LV25MG121C1/I0 -opt_strategy area

# ─── Source files (same order as synth_gowin_25k.ys) ─────────────────────

# PLL stub — replaced by real rPLL during P&R
add_file -type verilog "$BOARD_DIR/pll_gowin_stub.v"

# Primitives
add_file -type verilog "$RTL_ROOT/common/prim/gowin_mult18.v"
add_file -type verilog "$RTL_ROOT/common/prim/spu_multiplier_serial.v"
add_file -type verilog "$RTL_ROOT/common/prim/spu_psram_ctrl.v"
add_file -type verilog "$RTL_ROOT/common/prim/spu_smul_tdm.v"
add_file -type verilog "$RTL_ROOT/common/prim/surd_multiplier.v"

# Core
add_file -type verilog "$RTL_ROOT/core/shared/spu_cross_rotor.v"
add_file -type verilog "$RTL_ROOT/core/shared/davis_gate_dsp.v"
add_file -type verilog "$RTL_ROOT/core/spu13/spu13_sequencer.v"
add_file -type verilog "$RTL_ROOT/core/shared/spu_rotor_vault.v"
add_file -type verilog "$RTL_ROOT/core/shared/spu_unified_alu_tdm.v"
add_file -type verilog "$RTL_ROOT/core/spu13/spu13_core.v"

# SPU-4 Sentinel
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_decoder.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_euclidean_alu.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_regfile.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_core.v"
add_file -type verilog "$RTL_ROOT/core/spu4/spu4_top.v"

# SPU-13 sub-modules
add_file -type verilog "$RTL_ROOT/core/spu13/spu13_berry_gate.v"
add_file -type verilog "$RTL_ROOT/core/spu13/spu13_janus_mirror.v"
add_file -type verilog "$RTL_ROOT/core/spu13/spu13_permute_13.v"
add_file -type verilog "$RTL_ROOT/core/spu13/spu13_top.v"

# System infrastructure
add_file -type verilog "$RTL_ROOT/top/spu_sierpinski_clk.v"
add_file -type verilog "$RTL_ROOT/common/sync/spu_soft_start.v"
add_file -type verilog "$RTL_ROOT/top/spu_laminar_power.v"
add_file -type verilog "$RTL_ROOT/peripherals/artery/spu_artery_fifo.v"
add_file -type verilog "$RTL_ROOT/peripherals/artery/spu_whisper_tx.v"
add_file -type verilog "$RTL_ROOT/top/spu_system.v"

# Memory bridges
add_file -type verilog "$RTL_ROOT/peripherals/storage/spu_mem_bridge_qspi.v"

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
