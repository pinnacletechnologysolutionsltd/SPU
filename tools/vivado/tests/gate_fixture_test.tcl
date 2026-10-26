# Offline regression for the strict-gate scanners in spu_vivado_flow.tcl against real Vivado 2026.1 output (Step 7 D1/D2). No Vivado needed.
#   tclsh tools/vivado/tests/gate_fixture_test.tcl [PRESERVED_OUT_DIR ...]
# Fixtures: fixtures/vivado_2026_1/ (verbatim line excerpts, see PROVENANCE.txt). Optional OUT dirs (e.g. build/vivado/step7_nc3_01) replay full files.
# Loads only the script's proc definitions; nothing at top level runs. Synthetic lines are marked SYNTHETIC; the only real 2026.1 CRITICAL WARNING
# captured so far is [Common 17-55] (nc1_vivado_log.excerpt).
set here [file dirname [file normalize [info script]]]
set flow [file join $here .. spu_vivado_flow.tcl]
set fx [file join $here fixtures vivado_2026_1]
proc slurp {f} { set fh [open $f] ; set t [read $fh] ; close $fh ; return $t }
set src [slurp $flow] ; set cmd ""
foreach line [split $src \n] { append cmd $line \n ; if {[info complete $cmd]} { if {[lindex [string trim $cmd] 0] eq "proc"} { eval $cmd } ; set cmd "" } }
set fails 0
proc check {name got want} {
    set ok [expr {$got eq $want}]
    puts [format "%-46s %s" $name [expr {$ok ? "OK" : "BAD\n    got:  $got\n    want: $want"}]]
    if {!$ok} { incr ::fails }
}
proc old_trigger_lines {txt} { llength [lsearch -all -regexp [split $txt \n] {CRITICAL WARNING.*(No valid object|No ports matched)}] }
set M [spu_scope_marker]
set CW "CRITICAL WARNING: \[Vivado 12-4739\] create_clock:No valid object(s) found for '-objects \[get_ports sys_clk\]'. \[x.xdc:7\]" ;# SYNTHETIC
set log [string trimright [slurp [file join $fx nc3_vivado_log.excerpt]] \n]
set ct [slurp [file join $fx nc3_check_timing.excerpt]]
set ct_want [list "check_timing: no_clock = 8172" "check_timing: unconstrained_internal_endpoints = 28651"]

check "marker literal absent from flow source"        [expr {[string first $M $src] < 0}] 1
check "fixture holds the D1 trigger (precondition)"   [expr {[old_trigger_lines $log] >= 2}] 1
check "D1: no marker -> fail closed, no false hit"    [spu_scan_log $log] [list "log scope marker found 0 times, expected 1 (log not written by this script run)"]
check "D1: echo before marker (scope layer)"          [spu_scan_log "$log\n$M\nINFO: ok"] {}
check "D1: echo after marker (format layer)"          [spu_scan_log "$M\n$log"] {}
check "D1: echoed real-format CW cannot fire"         [spu_scan_log "$M\n# $CW\n    $CW"] {}
check "D1: printed FAILED text cannot re-fire"        [spu_scan_log "$M\nconstraint resolved to nothing: $CW"] {}
check "positive: real-format CW after marker fires"   [spu_scan_log "$log\n$M\n$CW"] [list "constraint resolved to nothing: $CW"]
check "positive: CW before marker is out of scope"    [spu_scan_log "$CW\n$M"] {}
check "marker twice -> fail closed"                   [llength [spu_scan_log "$M\n$M"]] 1
check "D2: one authoritative count per check"         [spu_scan_check_timing $ct] $ct_want
check "D2: summary/header disagreement fails"         [spu_scan_check_timing "1. checking no_clock (0)\n1. checking no_clock (5)"] [list "check_timing: no_clock summary 0 disagrees with section header 5"]
check "all-zero report passes"                        [spu_scan_check_timing "1. checking no_clock (0)\n1. checking no_clock (0)\n4. checking unconstrained_internal_endpoints (0)"] {}
check "missing no_clock section fails"                [spu_scan_check_timing "garbage"] [list "check_timing report has no 'checking no_clock' section (format changed or report missing)"]
# Step 7D3: CRITICAL WARNING [Common 17-55] (set_property received no objects), real NC1 lines from Step 7V.
set nc1 [string trimright [slurp [file join $fx nc1_vivado_log.excerpt]] \n]
set nc1_lines [split $nc1 \n]
set cw55 [lindex $nc1_lines [lsearch -regexp $nc1_lines {^CRITICAL WARNING: \[Common 17-55\]}]]
set d3 "constraint resolved to nothing (set_property, object type unknown): $cw55"
set S55 "CRITICAL WARNING: \[Common 17-55\] 'set_property' expects at least one object. \[x.xdc:9\]" ;# SYNTHETIC
check "D3 fixture: real marker once, 17-55 twice"      [list [llength [lsearch -all -exact $nc1_lines $M]] [llength [lsearch -all -regexp $nc1_lines {^CRITICAL WARNING: \[Common 17-55\]}]]] {1 2}
check "D3: real NC1 diagnostic -> one reason"          [spu_scan_log $nc1] [list $d3]
check "D3: synthetic 17-55 detected"                   [spu_scan_log "$M\n$S55"] [list "constraint resolved to nothing (set_property, object type unknown): $S55"]
check "D3: distinct file:line stay distinct"           [llength [spu_scan_log "$M\n$S55\n[string map {x.xdc:9 x.xdc:10} $S55]"]] 2
check "D3: same message, wrong ID not detected"        [spu_scan_log "$M\n[string map {17-55 17-56} $S55]"] {}
check "D3: same ID, other command not detected"        [spu_scan_log "$M\n[string map {set_property get_property} $S55]"] {}
check "D3: same ID, unrelated message not detected"    [spu_scan_log "$M\nCRITICAL WARNING: \[Common 17-55\] something else entirely."] {}
check "D3: WARNING severity not detected"              [spu_scan_log "$M\n[string range $S55 9 end]"] {}
check "D3: echoed / indented 17-55 not detected"       [spu_scan_log "$M\n# $S55\n  $S55"] {}
check "D3: 17-55 before marker out of scope"           [spu_scan_log "$S55\n$M"] {}
check "D3 + D1: NC3 echo excerpt still clean"          [spu_scan_log "$log\n$M\n[join [lsearch -all -inline -not -exact $nc1_lines $M] \n]"] [list $d3]

foreach out $argv {
    set full [slurp [file join $out vivado.log]] ; set n [file tail $out]
    set lines [split $full \n]
    if {[llength [lsearch -all -exact $lines $M]] == 1} {
        # Log written by the repaired flow (Step 7V onward): scan as is. Expected findings depend on the run, so they are printed, not asserted.
        set f [spu_scan_log $full]
        check "$n: real marker, no finding from echo"     [llength [lsearch -all -glob $f {*: #*}]] 0
        check "$n: full check_timing"                     [spu_scan_check_timing [slurp [file join $out synth_check_timing.rpt]]] $ct_want
        puts "INFO $n log findings: [llength $f]" ; foreach x $f { puts "    $x" }
        continue
    }
    set i [lsearch -exact $lines "# if \{\[catch \{spu_main \$argv\} err\]\} \{"]
    while {$i >= 0 && [lindex $lines $i] ne "# \}"} { incr i }
    check "$n: full log holds D1 trigger"             [expr {[old_trigger_lines $full] >= 1}] 1
    check "$n: full log, no marker -> fail closed"    [llength [spu_scan_log $full]] 1
    check "$n: marker where spu_main starts -> clean" [expr {$i < 0 ? "no catch echo" : [spu_scan_log [join [linsert $lines [expr {$i + 1}] $M] \n]]}] {}
    check "$n: full check_timing"                     [spu_scan_check_timing [slurp [file join $out synth_check_timing.rpt]]] $ct_want
}
puts "GATE_FIXTURES [expr {$fails == 0 ? {PASS} : "FAIL ($fails)"}]"
exit [expr {$fails == 0 ? 0 : 1}]
