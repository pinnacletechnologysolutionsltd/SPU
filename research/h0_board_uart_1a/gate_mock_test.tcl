# Command-level mocks: validate gate decisions, not Vivado semantics.
source research/h0_board_uart_1a/reachability_gate.tcl
source research/h0_board_uart_1a/uart_sync_gate.tcl
set mode good
proc selected_name {args} {
 set pos [lsearch -exact $args -filter]
 if {$pos<0} {return ""}
 set filter [lindex $args [expr {$pos+1}]]
 if {[regexp {NAME == "([^"]+)"} $filter -> n]} {return $n}
 return candidate
}
proc get_cells {args} {
 global mode
 set n [selected_name {*}$args]
 if {$mode eq "hierarchy_mismatch" && $n eq "candidate"} {set all {};for {set i 0} {$i<896} {incr i} {lappend all "renamed_$i"};return $all}
 if {$mode eq "hierarchy_mismatch" && [string first {board/cpu/cpu/banks/bank0_reg} $n]==0} {return {}}
 if {$mode eq "bad_bank" && $n eq {board/cpu/cpu/banks/bank0_reg[0][0]}} {return {}}
 if {$mode eq "bad_result" && $n eq {board/cpu/cpu/result_reg[0]}} {return {}}
 if {$mode eq "fetch_pruned" && $n eq {board/cpu/cpu/banks/fetch_data_reg[0]}} {return {}}
 return [list $n]
}
proc get_pins {args} {return [list [selected_name {*}$args]]}
proc get_ports {args} {return [list [lindex $args end]]}
proc get_property {key obj} {
 switch -- $key {NAME {return $obj} REF_NAME {return FDRE} ASYNC_REG {if {$::mode eq "missing_async"} {return FALSE};return TRUE}}
 error "unexpected property $key"
}
proc get_clocks {args} {if {$::mode eq "bad_clock"} {return wrong_clk};return cpu_clk}
proc all_fanin {args} {
 global mode
 set pin [lindex [lindex $args end] 0]
 if {[regexp {^board/endpoint/done_payload_reg\[([0-9]+)\]/D$} $pin -> n]} {
  if {$mode eq "disconnected_result" && $n==0} {return unrelated/C}
  return [list "board/cpu/cpu/result_reg\[$n\]/C"]
 }
 if {[regexp {^board/link/adapter/rpayload_reg\[([0-9]+)\]/D$} $pin -> n]} {if {$mode eq "disconnected_adapter" && $n==0} {return unrelated/C};return [list "board/endpoint/done_payload_reg\[$n\]/C"]}
 if {[regexp {^board/link/tx/shift_reg\[([0-9]+)\]/D$} $pin -> n]} {
  set roots {};for {set i [expr {$n-1}]} {$i<192} {incr i 8} {lappend roots "board/link/adapter/rpayload_reg\[$i\]/C"};if {$n<8 && $mode ne "broken_shift"} {lappend roots "board/link/tx/shift_reg\[[expr {$n+1}]\]/C"};return $roots
 }
 if {$pin eq {board/link/tx/tx_reg/D}} {return {{board/link/tx/shift_reg[1]/C}}}
 if {$pin eq "uart_tx"} {if {$mode eq "disconnected_tx"} {return unrelated/C};return {board/link/tx/tx_reg/C}}
 return {}
}
proc all_fanout {args} {
 global mode
 set obj [lindex $args end]
 if {$obj eq "uart_rx"} {
  if {$mode eq "merged"} {return {board/link/rx/rx_meta_reg/D}}
  if {$mode eq "unsafe_fanout"} {return {board/link/rx/rx_meta_reg/D board/link/activity_meta_reg/D rogue/D}}
  return {board/link/rx/rx_meta_reg/D board/link/activity_meta_reg/D}
 }
 if {$obj eq "board/link/rx/rx_meta_reg/Q"} {return {board/link/rx/rx_sync_reg/D}}
 if {$obj eq "board/link/activity_meta_reg/Q"} {return {board/link/activity_sync_reg/D}}
 return {}
}
set out [lindex $argv 0]
if {$out eq ""} {error "provide new build/ test directory"}
set out [file normalize $out];set build [file normalize build]
if {![string match "${build}/*" $out] || [file exists $out]} {error "mock output must be a new build/ child"}
file mkdir $out
foreach mode {good fetch_pruned bad_bank hierarchy_mismatch bad_result disconnected_result disconnected_adapter disconnected_tx broken_shift} {
 set failed [catch {h0_reachability_gate $mode $out} msg]
 set want [expr {$mode ni {good fetch_pruned}}]
 if {$failed!=$want} {error "unexpected reachability $mode: $msg"}
 puts "reachability $mode [expr {$failed ? {HOLD} : {PASS}}]"
}
set f [open [file join $out reachability_hierarchy_mismatch.txt]];set report [read $f];close $f
if {[string first "DIAGNOSIS HIERARCHY_OR_PATTERN_MISMATCH" $report]<0} {error "hierarchy diagnosis missing"}
set f [open [file join $out reachability_bad_bank.txt]];set report [read $f];close $f
if {[string first "DIAGNOSIS MISSING_EXPECTED_NAMES_OR_OPTIMIZED_RENAMING" $report]<0} {error "missing-cell diagnosis missing"}
foreach mode {good merged unsafe_fanout missing_async bad_clock} {
 set failed [catch {h0_uart_sync_gate $mode $out} msg]
 set want [expr {$mode ne "good"}]
 if {$failed!=$want} {error "unexpected synchronizer $mode: $msg"}
 puts "synchronizer $mode [expr {$failed ? {HOLD} : {PASS}}]"
}
puts "GATE MOCKS PASS"
