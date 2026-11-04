# Conservative register-mapped structural gate; no sequential equivalence proof.
proc h0_pin {name} {get_pins -quiet -hierarchical -filter [format {NAME == "%s"} $name]}
proc h0_cell {name} {get_cells -quiet -hierarchical -filter [format {NAME == "%s"} $name]}
proc h0_root_has {pin source_cell} {
 foreach obj [all_fanin -quiet -flat -startpoints_only -to $pin] {
  set name [get_property NAME $obj]
  if {[string first "${source_cell}/" $name] == 0} {return 1}
 }
 return 0
}
proc h0_count_regs {prefix count report} {
 set found 0
 for {set i 0} {$i<$count} {incr i} {
  set name [format {%s[%d]} $prefix $i];set cell [h0_cell $name]
  if {[llength $cell]==1 && [string match "FD*" [get_property REF_NAME $cell]]} {
   incr found;puts $report "MATCH $name [get_property REF_NAME $cell]"
  } else {puts $report "MISSING_OR_HIERARCHY_MISMATCH $name matched=[llength $cell]"}
 }
 return $found
}
proc h0_reachability_gate {phase out} {
 set f [open [file join $out reachability_${phase}.txt] w]
 set fail 0;set bank_total 0
 foreach bank {0 1} {
  set count 0
  for {set word 0} {$word<14} {incr word} {
   for {set bit 0} {$bit<64} {incr bit} {
    set name [format {board/cpu/cpu/banks/bank%d_reg[%d][%d]} $bank $word $bit]
    set c [h0_cell $name]
    if {[llength $c]==1 && [string match "FD*" [get_property REF_NAME $c]]} {incr count;puts $f "MATCH $name"} else {puts $f "MISSING_OR_HIERARCHY_MISMATCH $name matched=[llength $c]"}
   }
  }
  incr bank_total $count
  puts $f "BANK $bank OBSERVED $count EXPECTED 896"
  if {$count!=896} {
   set candidates [get_cells -quiet -hierarchical -filter "NAME =~ *bank${bank}_reg*"]
   puts $f "DIAGNOSTIC bank=$bank exact=$count wildcard_candidates=[llength $candidates] names=$candidates"
   if {[llength $candidates]>=896} {puts $f "DIAGNOSIS HIERARCHY_OR_PATTERN_MISMATCH"} else {puts $f "DIAGNOSIS MISSING_EXPECTED_NAMES_OR_OPTIMIZED_RENAMING"}
   set fail 1
  }
 }
 puts $f "BANK_TOTAL OBSERVED $bank_total EXPECTED 1792"
 set result [h0_count_regs {board/cpu/cpu/result_reg} 192 $f]
 puts $f "RESULT_STORAGE OBSERVED $result EXPECTED 192"
 if {$result!=192} {puts $f "DIAGNOSTIC result_candidates=[get_cells -quiet -hierarchical -filter {NAME =~ *result_reg*}]";set fail 1}
 set fetch [h0_count_regs {board/cpu/cpu/banks/fetch_data_reg} 64 $f]
 set held [h0_count_regs {board/cpu/cpu/held_word_reg} 64 $f]
 puts $f "FETCH OBSERVED $fetch REFERENCE 64 (informational)"
 puts $f "HELD OBSERVED $held REFERENCE 64 (informational)"
 # Each result bit must structurally reach endpoint response storage, then
 # adapter response storage. All payload bits must reach the serial TX shifter.
 set serial_roots {}
 for {set lane 0} {$lane<8} {incr lane} {
  set pin [h0_pin [format {board/link/tx/shift_reg[%d]/D} [expr {$lane+1}]]]
  if {[llength $pin]!=1} {puts $f "MISSING_OR_HIERARCHY_MISMATCH TX_SHIFT lane=$lane";set fail 1;lappend serial_roots {};continue}
  lappend serial_roots [all_fanin -quiet -flat -startpoints_only -to $pin]
 }
 set result_paths 0
 for {set bit 0} {$bit<192} {incr bit} {
  set src [format {board/cpu/cpu/result_reg[%d]} $bit]
  set ep [format {board/endpoint/done_payload_reg[%d]} $bit]
  set ap [format {board/link/adapter/rpayload_reg[%d]} $bit]
  set ed [h0_pin "$ep/D"];set ad [h0_pin "$ap/D"]
  set a [expr {[llength $ed]==1 && [h0_root_has $ed $src]}]
  set b [expr {[llength $ad]==1 && [h0_root_has $ad $ep]}]
  set c 0
  foreach obj [lindex $serial_roots [expr {$bit%8}]] {if {[string first "$ap/" [get_property NAME $obj]]==0} {set c 1;break}}
  puts $f "RESULT_PATH bit=$bit result_to_endpoint=$a endpoint_to_adapter=$b adapter_to_tx_shift=$c source=$src endpoint=$ep adapter=$ap"
  if {$a && $b && $c} {incr result_paths} else {set fail 1}
 }
 puts $f "RESULT_PATHS OBSERVED $result_paths EXPECTED 192"
 # Each serial shift stage must connect toward bit 1 before TX.
 for {set k 1} {$k<8} {incr k} {
  set d [h0_pin [format {board/link/tx/shift_reg[%d]/D} $k]]
  set prior [format {board/link/tx/shift_reg[%d]} [expr {$k+1}]]
  set ok [expr {[llength $d]==1 && [h0_root_has $d $prior]}]
  puts $f "TX_SHIFT_CHAIN $prior -> shift_reg\[$k\] OBSERVED $ok EXPECTED 1"
  if {!$ok} {set fail 1}
 }
 set txout [get_ports -quiet uart_tx]
 set txd [h0_pin {board/link/tx/tx_reg/D}]
 set txok [expr {[llength $txout]==1 && [llength $txd]==1 && [h0_root_has $txd {board/link/tx/shift_reg[1]}]}]
 if {$txok} {set txok [h0_root_has $txout {board/link/tx/tx_reg}]}
 puts $f "TX_SHIFT_TO_PORT OBSERVED $txok EXPECTED 1"
 if {!$txok} {set fail 1}
 puts $f "VERDICT [expr {$fail ? {HOLD} : {PASS}}]"
 close $f
 if {$fail} {error "HOLD: bank or result reachability gate failed at $phase; see report, including possible hierarchy mismatch"}
}
