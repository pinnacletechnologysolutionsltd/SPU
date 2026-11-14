# rtl0c_synth.tcl — RTL-0C gate C3, stage 1: synthesis of psurd_board_top with board constraints, generated
# clock, asynchronous-pad exceptions and the fail-closed structural and pin checks. No place or route here,
# so a script or structure problem does not consume a route attempt (plan D7).
# usage: vivado -mode batch -source rtl0c_synth.tcl -tclargs REPO_ROOT OUT_DIR
set root [lindex $argv 0]; set out [lindex $argv 1]
if {![string match "2026.1*" [version -short]]} { error "Vivado 2026.1 required" }
file mkdir $out
source [file join $root hardware/boards/artix7/psurd_rtl0c/rtl0c_checks.tcl]
set srcs {
  hardware/boards/artix7/psurd_board_top.v
  hardware/rtl/core/psurd/psurd_sys_top.v hardware/rtl/core/psurd/psurd_link.v hardware/rtl/core/psurd/psurd_loader.v
  hardware/rtl/core/psurd/psurd_runctl.v hardware/rtl/core/psurd/psurd_record.v hardware/rtl/core/psurd/psurd_uart_rx.v
  hardware/rtl/peripherals/whisper/spu_uart_tx.v
  hardware/rtl/core/psurd/psurd_core.v hardware/rtl/core/psurd/psurd_decode.v hardware/rtl/core/psurd/psurd_exec.v
  hardware/rtl/core/psurd/psurd_imem.v hardware/rtl/core/psurd/psurd_sign.v hardware/rtl/core/psurd/psurd_bank_lutram.v
  hardware/rtl/core/spu13/spu13_surd_load.v hardware/rtl/core/spu13/spu13_surd_arith.v
  hardware/rtl/math/surd_cpu_products.v hardware/rtl/math/surd_normalize_unit.v hardware/rtl/math/surd_binary_gcd3.v
  hardware/rtl/math/surd_exact_quotient.v
}
foreach s $srcs { read_verilog [file join $root $s] }
read_xdc [file join $root hardware/boards/artix7/psurd_board.xdc]
synth_design -top psurd_board_top -part xc7a100tfgg676-1 -flatten_hierarchy rebuilt -verilog_define SYNTHESIS=1
# Generated 25 MHz clock at the divider flop (as spu_a7_surd_cpu_base.xdc), once the pins are known to be unique.
create_generated_clock -name cpu_clk -source [rtl0c_one pin cpu_clk_div_reg/C] -divide_by 2 [rtl0c_one pin cpu_clk_div_reg/Q]
rtl0c_structure synth $out
rtl0c_pins synth $out
# Exceptions only from each asynchronous pad to its verified first synchronizer stage.
set_false_path -from [get_ports rst_n]   -to [rtl0c_one pin {rst_sync_reg[0]/D}]
set_false_path -from [get_ports uart_rx] -to [rtl0c_one pin u_sys/urx/rx_s1_reg/D]
write_checkpoint -force [file join $out synth.dcp]
report_utilization -file [file join $out util.rpt]
report_utilization -hierarchical -hierarchical_depth 5 -file [file join $out util_hier.rpt]
report_clocks -file [file join $out clocks.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file [file join $out timing_summary.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
report_drc -file [file join $out drc.rpt]
report_methodology -file [file join $out methodology.rpt]
set f [open [file join $out timing_estimate.txt] w]
puts $f "wns [get_property SLACK [get_timing_paths -max_paths 1 -setup]]"
puts $f "whs [get_property SLACK [get_timing_paths -max_paths 1 -hold]]"
close $f
