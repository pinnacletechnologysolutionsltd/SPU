# rtl0b_synth.tcl — RTL-0B gate B5: out-of-context synthesis of the complete v0.3 system top psurd_sys_top
# (UART link, SPUI loader, run control, record builder, core). Same part, constraint and reports as the
# RTL-0S flow (rtl0s_synth.tcl); route the resulting checkpoint with psurd_rtl0s/rtl0p_impl.tcl unchanged.
# usage: vivado -mode batch -source rtl0b_synth.tcl -tclargs REPO_ROOT OUT_DIR
# Not a board build: no pins, PLL or bitstream. uart_rx / uart_tx are unconstrained ports (uart_rx enters a
# two-flop synchronizer); the timing scope is register-to-register paths on clk (40.000 ns).
set root [lindex $argv 0]
set out  [lindex $argv 1]
set part xc7a100tfgg676-1
file mkdir $out
set srcs {
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
read_xdc [file join $root hardware/boards/artix7/psurd_rtl0s/rtl0s.xdc]
synth_design -top psurd_sys_top -part $part -mode out_of_context -flatten_hierarchy rebuilt
write_checkpoint -force [file join $out synth.dcp]
report_utilization -file [file join $out util.rpt]
report_utilization -hierarchical -hierarchical_depth 4 -file [file join $out util_hier.rpt]
report_timing_summary -max_paths 10 -file [file join $out timing_summary.rpt]
report_timing -max_paths 20 -sort_by group -file [file join $out timing_paths.rpt]
report_clocks -file [file join $out clocks.rpt]
check_timing -file [file join $out check_timing.rpt]
report_high_fanout_nets -max_nets 20 -file [file join $out fanout.rpt]
report_drc -file [file join $out drc.rpt]
report_methodology -file [file join $out methodology.rpt]
# Structural checks (machine-readable; validated against report_utilization): see rtl0s_structure.tcl.
source [file join $root hardware/boards/artix7/psurd_rtl0s/rtl0s_structure.tcl]
rtl0s_structure [file join $out structure.txt]
set f [open [file join $out timing_estimate.txt] w]
puts $f "wns [get_property SLACK [get_timing_paths -max_paths 1 -setup]]"
puts $f "whs [get_property SLACK [get_timing_paths -max_paths 1 -hold]]"
close $f
