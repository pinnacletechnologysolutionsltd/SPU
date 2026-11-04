# Fail closed on reset topology and source provenance. No timing guarantee.
proc approved_reset_start {obj} {
 set class [get_property CLASS $obj]
 if {$class eq "port"} {return [expr {[get_property NAME $obj] eq "raw_rst_n"}]}
 if {$class ne "pin" || [get_property REF_PIN_NAME $obj] ni {C Q}} {return 0}
 set cell [get_cells -quiet -of_objects $obj]
 if {[llength $cell] != 1 || ![string match "FD*" [get_property REF_NAME $cell]]} {return 0}
 set name [get_property NAME $cell]
 return [expr {[regexp {(^|/)supervisor/reset_hold_reg$} $name] ||
               [regexp {(^|/)supervisor/release_sync_reg\[1\]$} $name] ||
               [regexp {(^|/)reset_ctl/exec_rst_n_reg$} $name]}]
}
proc check_async_reset {phase out} {
 set f [open [file join $out async_${phase}.txt] w]
 set count 0; set unsafe 0
 foreach cell [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
  foreach pin [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}] {
   incr count
   set nets [get_nets -quiet -segments -of_objects $pin]
   set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
   set roots [all_fanin -quiet -flat -startpoints_only -to $pin]
   puts $f "PIN=$pin TYPE=[get_property REF_NAME $cell] DRIVERS=$drivers STARTPOINTS=$roots"
   if {[llength $drivers] != 1} {puts $f "HOLD ambiguous driver"; incr unsafe; continue}
   if {[llength $roots] != 1 || ![approved_reset_start [lindex $roots 0]]} {
    puts $f "HOLD unapproved or ambiguous reset source"; incr unsafe; continue
   }
   foreach obj [all_fanin -quiet -flat -to $pin] {
    if {[get_property CLASS $obj] ne "pin"} {continue}
    set c [get_cells -quiet -of_objects $obj]
    if {[llength $c] != 1} {puts $f "HOLD ambiguous fan-in cell $obj"; incr unsafe; continue}
    set ref [get_property REF_NAME $c]
    if {![regexp {^(FD[A-Z0-9_]*|LUT1|INV|BUF|IBUF|BUFG|BUFGCE)$} $ref]} {
     puts $f "HOLD unapproved reset fan-in cell $c ($ref)"; incr unsafe
    }
   }
  }
 }
 puts $f "COUNT=$count UNSAFE=$unsafe"; close $f
 if {$count == 0 || $unsafe != 0} {error "RESET HOLD: missing or unsafe async-reset structure at $phase"}
}
