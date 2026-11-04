# Preparation only: run later under separately authorized bounded job.
source [file join [file dirname [info script]] reset_structure.tcl]
source [file join [file dirname [info script]] reachability_gate.tcl]
source [file join [file dirname [info script]] uart_sync_gate.tcl]
proc main {} {
 set root [file normalize [file join [file dirname [info script]] ../..]]
 cd $root
 if {![string match "2026.1*" [version -short]]} {error "Vivado 2026.1 required"}
 if {![info exists ::env(H0_BOARD_UART_OUTPUT)] || [file pathtype $::env(H0_BOARD_UART_OUTPUT)] ne "absolute"} {error "H0_BOARD_UART_OUTPUT must be an absolute, new build/ child"}
 set out [file normalize $::env(H0_BOARD_UART_OUTPUT)]
 set build [file normalize [file join $root build]]
 if {![string match "${build}/*" $out] || [file exists $out]} {error "Output must be a new build/ child"}
 if {[catch {exec sha256sum -c research/h0_board_uart_1a/SOURCES.sha256} msg]} {error "Source identity failure: $msg"}
 set fp [open research/h0_board_uart_1a/sources.f r]; set manifest [read $fp]; close $fp
 set dirs {}; set sources {}
 foreach line [split $manifest "\n"] {
  set line [string trim $line]
  if {$line eq "" || [string index $line 0] eq "#"} {continue}
  if {[string match "+incdir+*" $line]} {lappend dirs [file normalize [string range $line 8 end]]} else {
   if {![file isfile $line]} {error "Missing source: $line"}
   lappend sources [file normalize $line]
  }
 }
 file mkdir $out
 set_param general.maxThreads 2
 read_verilog -sv $sources
 read_xdc research/h0_board_uart_1a/board.xdc
 synth_design -top h0_board_uart_1a_top -part xc7a100tfgg676-1 -flatten_hierarchy none -include_dirs $dirs
 set src [get_pins -quiet -hierarchical -filter {NAME =~ */supervisor/cpu_clk_reg/C}]
 set dst [get_pins -quiet -hierarchical -filter {NAME =~ */supervisor/cpu_clk_reg/Q}]
 if {[llength $src] != 1 || [llength $dst] != 1} {error "HOLD: generated clock register pins not unique"}
 create_generated_clock -name cpu_clk -source $src -divide_by 2 $dst
 # Check the actual two-stage input paths before granting narrow exceptions.
 set rx_first [h0_uart_sync_gate pre_opt $out]
 set_false_path -from [get_ports uart_rx] -to $rx_first
 h0_reachability_gate pre_opt $out
 foreach {c p} {sys_clk 20.000 cpu_clk 40.000} {
  set cl [get_clocks -quiet $c]
  if {[llength $cl] != 1 || abs([get_property PERIOD $cl] - $p) > 1e-6} {error "HOLD: invalid clock $c"}
 }
 report_utilization -file $out/synth_utilization.rpt
 report_clocks -file $out/synth_clocks.rpt
 report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file $out/synth_timing_summary.rpt
 write_checkpoint $out/synthesized.dcp
 check_async_reset pre_opt $out
 opt_design
 h0_uart_sync_gate post_opt $out
 h0_reachability_gate post_opt $out
 check_async_reset post_opt $out
 place_design
 check_async_reset placed $out
 report_utilization -file $out/placed_utilization.rpt
 report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file $out/placed_timing_summary.rpt
 write_checkpoint $out/placed.dcp
 route_design
 check_async_reset routed $out
 write_checkpoint $out/routed.dcp
 report_route_status -file $out/routed_route_status.rpt
 report_utilization -file $out/routed_utilization.rpt
 report_utilization -hierarchical -file $out/routed_hier_utilization.rpt
 report_clock_utilization -file $out/routed_clock_utilization.rpt
 report_clocks -file $out/routed_clocks.rpt
 report_clock_networks -file $out/routed_clock_networks.rpt
 report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file $out/routed_timing_summary.rpt
 report_timing -delay_type max -max_paths 20 -path_type full_clock_expanded -file $out/routed_setup.rpt
 report_timing -delay_type min -max_paths 20 -path_type full_clock_expanded -file $out/routed_hold.rpt
 set rp [get_pins -quiet -hierarchical -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
 if {[llength $rp] == 0} {error "HOLD: no asynchronous reset timing endpoints"}
 report_timing -delay_type max -to $rp -max_paths 100 -nworst 3 -path_type full_clock_expanded -file $out/routed_reset_recovery.rpt
 report_timing -delay_type min -to $rp -max_paths 100 -nworst 3 -path_type full_clock_expanded -file $out/routed_reset_removal.rpt
 report_drc -file $out/routed_drc.rpt
 report_methodology -file $out/routed_methodology.rpt
 report_exceptions -file $out/routed_exceptions.rpt
 check_timing -verbose -file $out/routed_check_timing.rpt
 report_cdc -details -file $out/routed_cdc.rpt
 report_clock_interaction -file $out/routed_clock_interaction.rpt
 set f [open $out/IMPLEMENTATION_FINISHED w]; puts $f "Reports generated; timing and DRC require review."; close $f
}
if {[catch {main} message options]} {puts stderr "H0-BOARD-UART-1A FAILED: $message"; exit 1}
exit 0
