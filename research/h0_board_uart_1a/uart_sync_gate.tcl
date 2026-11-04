# Fail closed if the actual two UART synchronizer paths cannot be verified.
proc h0_uart_sync_gate {phase out} {
 set f [open [file join $out uart_sync_${phase}.txt] w]
 set fail 0
 set expected [list {board/link/rx/rx_meta_reg/D} {board/link/activity_meta_reg/D}]
 set p [get_ports -quiet uart_rx]
 if {[llength $p]!=1} {puts $f "HOLD missing uart_rx port";close $f;error "HOLD UART RX port"}
 set actual {}
 foreach x [all_fanout -quiet -flat -endpoints_only -from $p] {lappend actual [get_property NAME $x]}
 puts $f "RX_ENDPOINTS $actual EXPECTED $expected"
 if {[lsort -unique $actual] ne [lsort -unique $expected]} {puts $f "HOLD unverified RX fanout or merged first stage";set fail 1}
 foreach {first second} {
  board/link/rx/rx_meta_reg board/link/rx/rx_sync_reg
  board/link/activity_meta_reg board/link/activity_sync_reg
 } {
  set fc [h0_cell $first];set sc [h0_cell $second]
  set fq [h0_pin "$first/Q"];set fd [h0_pin "$first/D"]
  set sd [h0_pin "$second/D"];set ck1 [h0_pin "$first/C"];set ck2 [h0_pin "$second/C"]
  if {[llength $fc]!=1 || [llength $sc]!=1 || [llength $fq]!=1 || [llength $fd]!=1 || [llength $sd]!=1 || [llength $ck1]!=1 || [llength $ck2]!=1} {
   puts $f "HOLD missing or renamed synchronizer $first -> $second";set fail 1;continue
  }
  set a1 [string toupper [get_property ASYNC_REG $fc]];set a2 [string toupper [get_property ASYNC_REG $sc]]
  if {$a1 ni {1 TRUE} || $a2 ni {1 TRUE}} {puts $f "HOLD missing ASYNC_REG $first -> $second";set fail 1}
  set ends {};foreach x [all_fanout -quiet -flat -endpoints_only -from $fq] {lappend ends [get_property NAME $x]}
  puts $f "CHAIN $first -> $second Q_ENDPOINTS=$ends ASYNC_REG=$a1,$a2"
  if {[lsort -unique $ends] ne [list "$second/D"]} {puts $f "HOLD unverified first-to-second-stage path";set fail 1}
  foreach ck [list $ck1 $ck2] {
   set clocks [get_clocks -quiet -of_objects $ck]
   if {[llength $clocks]!=1 || [get_property NAME $clocks] ne "cpu_clk"} {puts $f "HOLD synchronizer clock $ck clocks=$clocks";set fail 1}
  }
 }
 puts $f "VERDICT [expr {$fail ? {HOLD} : {PASS}}]";close $f
 if {$fail} {error "HOLD: UART synchronizer path missing, merged or unsafe at $phase"}
 return [list [h0_pin {board/link/rx/rx_meta_reg/D}] [h0_pin {board/link/activity_meta_reg/D}]]
}
