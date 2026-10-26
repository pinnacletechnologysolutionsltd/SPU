# Fixture generator: write OUT/FAILED (or OUT/COMPLETE) exactly as the flow would, using the CURRENT gate procs.
#   tclsh regen_failed_g1.tcl FLOW LOADER OUT "name:period ..." (expected clocks)  "name:period ..." (clocks that exist)
source [lindex $argv 1] ; spu_load_procs [lindex $argv 0]
set out [lindex $argv 2] ; set ::have [dict create]
foreach e [lindex $argv 4] { lassign [split $e :] n p ; dict set ::have $n $p }
proc get_clocks {args} { set n [lindex $args end] ; if {[dict exists $::have $n]} { return $n } ; return {} }
proc get_property {args} { return [dict get $::have [lindex $args 1]] }
file delete -force [file join $out FAILED] [file join $out COMPLETE]
if {[catch {spu_gate $out [dict create -strict 1 expect_clocks [lindex $argv 3]]} err]} { set fh [open [file join $out FAILED] w] ; puts $fh $err ; close $fh } else { set fh [open [file join $out COMPLETE] w] ; puts $fh ok ; close $fh }
