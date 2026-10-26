# Dry run of spu_vivado_flow.tcl under plain tclsh with STUB Vivado commands. Proves argument handling, gating, ordering and markers.
# It does NOT run Vivado and says nothing about synthesis, timing or the design. Usage: tclsh tools/vivado/tests/dryrun_stub.tcl SCRATCH_DIR
set here [file dirname [file normalize [info script]]]
set flow [file join $here .. spu_vivado_flow.tcl]
set root [file normalize [file join $here .. .. ..]]
set scratch [file normalize [lindex $argv 0]]
set ::trace {}
proc stubfile {args} { set i [lsearch -exact $args -file] ; if {$i >= 0} { set p [lindex $args [expr {$i+1}]] ; set fh [open $p w] ; puts $fh [expr {[string match *check_timing* $p] ? $::stub_ct : "stub"}] ; close $fh } }
foreach c {read_verilog read_xdc synth_design opt_design place_design route_design report_utilization report_clocks report_clock_networks check_timing report_timing_summary report_cdc report_methodology report_drc report_route_status} {
    proc $c {args} "lappend ::trace \[concat $c \$args\] ; stubfile {*}\$args"
}
proc write_checkpoint {args} { lappend ::trace [concat write_checkpoint $args] ; set fh [open [lindex $args end] w] ; puts $fh stub ; close $fh }
proc version {args} { return 2025.2-STUB }
proc get_parts {args} { if {[lindex $args end] eq "xc7a100tfgg676-1"} { return xc7a100tfgg676-1 } ; return {} }
proc get_cells {args} { return {} }
set ::stub_clocks [dict create]
set ::stub_ct "1. checking no_clock (0)\n2. checking unconstrained_internal_endpoints (0)\n"
set ::stub_log ""
set ::M [join {SPU GATE SCOPE BEGIN} _]   ;# scope marker the real flow prints before read_xdc (Step 7R)
proc get_clocks {args} { set n [lindex $args end] ; if {[dict exists $::stub_clocks $n]} { return $n } ; return {} }
proc get_property {args} { if {[lindex $args 0] eq "PERIOD"} { return [dict get $::stub_clocks [lindex $args 1]] } ; return stub }
rename exit ::real_exit
proc exit {code} { error "EXIT $code" }
set fails 0
proc scenario {name args_list expect_code expect_marker {extra {}}} {
    global flow scratch fails argv
    set out [file join $scratch $name] ; file delete -force $out ; file mkdir $out
    set ::trace {} ; set ::argv [string map [list @OUT $out] $args_list]
    if {$::stub_log ne ""} { set lf [open [file join $out vivado.log] w] ; puts $lf $::stub_log ; close $lf }
    foreach f $extra { set fh [open [file join $out $f] w] ; puts $fh x ; close $fh }
    set code -1
    if {[catch {source $flow} err]} { if {[regexp {EXIT (\d+)} $err -> c]} { set code $c } else { set code "TCLERR:$err" } }
    set marks [lmap m {COMPLETE FAILED} {expr {[file exists [file join $out $m]] ? $m : [continue]}}]
    set ok [expr {$code == $expect_code && $marks eq $expect_marker}]
    puts [format "%-34s code=%s markers=%s %s" $name $code [list $marks] [expr {$ok ? "OK" : "BAD (expected $expect_code [list $expect_marker])"}]]
    if {!$ok} { incr fails }
    return $out
}
set base [list -top spu_a7_surd_cpu_base_top -part xc7a100tfgg676-1 -filelist tools/vivado/filelists/base_cpu_top.f -xdc hardware/boards/artix7/spu_a7_surd_cpu_base.xdc -outdir @OUT]
set out [scenario good_synth $base 0 COMPLETE]
set tr $::trace
set rv [llength [lsearch -all -glob $tr {read_verilog *}]]
puts "  read_verilog calls: $rv (expect 20); read_xdc before synth_design: [expr {[lsearch -glob $tr {read_xdc *}] < [lsearch -glob $tr {synth_design *}]}]; place/route/bitstream calls: [llength [lsearch -all -glob $tr {*place_design*}]]/[llength [lsearch -all -glob $tr {*route_design*}]]/[llength [lsearch -all -glob $tr {*bitstream*}]]"
puts "  synth_design: [lindex $tr [lsearch -glob $tr {synth_design *}]]"
set mf [open [file join $out run_manifest.txt]] ; set m [read $mf] ; close $mf
puts "  manifest: source_sha256 lines [llength [regexp -all -inline {source_sha256} $m]], git_head [regexp {git_head [0-9a-f]{40}} $m], tool_version [regexp {tool_version 2025.2-STUB} $m], xdc_sha256 [regexp {xdc_sha256 [0-9a-f]{64}} $m]"
if {$rv != 20} { incr fails }
scenario good_tensegrity [list -top spu_a7_tensegrity_link_top -part xc7a100tfgg676-1 -filelist tools/vivado/filelists/tensegrity_link_top.f -xdc hardware/boards/artix7/spu_a7_tensegrity_link.xdc -outdir @OUT] 0 COMPLETE
scenario generic_passthrough [concat $base [list -generic FOO=1 -generic BAR=2]] 0 COMPLETE
puts "  generics reach synth_design: [expr {[string first {-generic FOO=1} [lindex $::trace [lsearch -glob $::trace {synth_design *}]]] >= 0}]"
scenario missing_part {-top t -filelist a -xdc b -outdir @OUT} 1 FAILED
scenario unknown_part [lreplace $base 3 3 xc7a100tFAKE] 1 FAILED
scenario unknown_arg [concat $base {-bogus 1}] 1 FAILED
scenario bad_stage [concat $base {-stage banana}] 1 FAILED
scenario place_without_ack [concat $base {-stage place}] 1 FAILED
puts "  place_design reached without ack: [llength [lsearch -all -glob $::trace {*place_design*}]] (expect 0)"
scenario place_wrong_ack [concat $base {-stage place -ack ROUTE_APPROVED}] 1 FAILED
scenario route_without_ack [concat $base {-stage route}] 1 FAILED
scenario place_with_ack [concat $base {-stage place -ack PLACE_APPROVED}] 0 COMPLETE
puts "  place stage trace has opt/place, no route: [expr {[llength [lsearch -all -glob $::trace {*route_design*}]] == 0 && [llength [lsearch -all -glob $::trace {opt_design*}]] == 1}]"
scenario route_with_ack [concat $base {-stage route -ack ROUTE_APPROVED}] 0 COMPLETE
puts "  route stage trace: opt [llength [lsearch -all -glob $::trace {opt_design*}]], place [llength [lsearch -all -glob $::trace {place_design*}]], route [llength [lsearch -all -glob $::trace {route_design*}]], bitstream [llength [lsearch -all -glob $::trace {*bitstream*}]]"
scenario outdir_not_empty $base 1 {} {stray.txt}
puts "  refused dir untouched (only stray.txt): [expr {[glob -nocomplain -directory [file join $scratch outdir_not_empty] *] eq [list [file join $scratch outdir_not_empty stray.txt]]}]"
scenario outdir_with_log_ok $base 0 COMPLETE {vivado.log vivado.jou}
set srcdir [file join $root hardware rtl arch] ; set before [lsort [glob -directory $srcdir *]]
scenario outdir_in_source [lreplace $base 9 9 $srcdir] 1 {}
set after [lsort [glob -directory $srcdir *]]
puts "  tracked source dir untouched (no FAILED/COMPLETE written into it): [expr {$before eq $after}]"
if {$before ne $after} { incr fails }
set fh [open [file join $scratch badfl.f] w] ; puts $fh "frobnicate x" ; close $fh
scenario bad_filelist_keyword [lreplace $base 5 5 $scratch/badfl.f] 1 FAILED
set fh [open [file join $scratch missingsrc.f] w] ; puts $fh "sv hardware/rtl/does_not_exist.v" ; close $fh
scenario missing_source_file [lreplace $base 5 5 $scratch/missingsrc.f] 1 FAILED
# --- constraint gate scenarios (Phase 2 step 7 logic; patterns still to be proven on real Vivado)
set ::stub_clocks [dict create sys_clk 20.000]
scenario expect_clock_ok [concat $base {-expect_clock sys_clk:20.000}] 0 COMPLETE
scenario expect_clock_missing [concat $base {-expect_clock cpu_clk:40.000}] 1 FAILED
scenario expect_clock_wrong_period [concat $base {-expect_clock sys_clk:10.000}] 1 FAILED
scenario expect_clock_bad_syntax [concat $base {-expect_clock sys_clk}] 1 FAILED
set ::stub_log "$::M\nINFO: ok" ; scenario strict_clean [concat $base {-strict 1}] 0 COMPLETE
set ::stub_ct "1. checking no_clock (12)\n2. checking unconstrained_internal_endpoints (0)\n" ; scenario strict_unclocked_domain [concat $base {-strict 1}] 1 FAILED
set ::stub_ct "1. checking no_clock (0)\n2. checking unconstrained_internal_endpoints (5)\n" ; scenario strict_unconstrained_endpoints [concat $base {-strict 1}] 1 FAILED
set ::stub_ct "1. checking no_clock (0)\n" ; set ::stub_log "$::M\nCRITICAL WARNING: \[Vivado 12-4739\] create_clock:No valid object(s) found for '-objects \[get_ports sys_clk\]'. \[x.xdc:7\]"
scenario strict_empty_collection [concat $base {-strict 1}] 1 FAILED
set ::stub_ct "garbage" ; set ::stub_log "$::M\nINFO: ok" ; scenario strict_report_format_changed [concat $base {-strict 1}] 1 FAILED
set ::stub_ct "1. checking no_clock (0)\n" ; set ::stub_log "" ; scenario strict_without_log [concat $base {-strict 1}] 1 FAILED
# Step 7R: D1 (echoed detector source, Vivado 2026.1 shape) must not fire; a log without the scope marker fails closed; D2 counts once.
set ::stub_log "INFO: ok" ; scenario strict_log_without_marker [concat $base {-strict 1}] 1 FAILED
set ::stub_log "$::M\n#  if {\[regexp {CRITICAL WARNING} \$line\] && \[regexp {No valid object|No ports matched} \$line\]} { lappend bad x }\nINFO: ok"
scenario strict_echoed_detector_source [concat $base {-strict 1}] 0 COMPLETE
set ::stub_ct "1. checking no_clock (12)\n\n1. checking no_clock (12)\n" ; set ::stub_log "$::M\nINFO: ok"
set out [scenario strict_duplicate_header [concat $base {-strict 1}] 1 FAILED]
set fh [open [file join $out FAILED]] ; set ftxt [read $fh] ; close $fh
set once [llength [regexp -all -inline {no_clock = 12} $ftxt]]
puts "  duplicate check_timing header reported once: $once (expect 1)"
if {$once != 1} { incr fails }
# Step 7D3: a genuine CRITICAL WARNING [Common 17-55] after the marker fails the gate, with its own reason.
set ::stub_ct "1. checking no_clock (0)\n" ; set ::stub_log "$::M\nCRITICAL WARNING: \[Common 17-55\] 'set_property' expects at least one object. \[x.xdc:22\]"
set out [scenario strict_common_17_55 [concat $base {-strict 1}] 1 FAILED]
set ftxt "" ; catch { set fh [open [file join $out FAILED]] ; set ftxt [read $fh] ; close $fh }
set r55 [llength [regexp -all -inline {set_property, object type unknown} $ftxt]]
puts "  Common 17-55 reported once: $r55 (expect 1)"
if {$r55 != 1} { incr fails }
set wrote [expr {[file exists [file join $scratch strict_unclocked_domain synth.dcp]] && [file exists [file join $scratch strict_unclocked_domain synth_utilization.rpt]]}]
puts "  gate failure still wrote the reports and checkpoint first: $wrote (expect 1)"
if {!$wrote} { incr fails }
set ::stub_ct "1. checking no_clock (0)\n2. checking unconstrained_internal_endpoints (0)\n" ; set ::stub_log "" ; set ::stub_clocks [dict create]
set sfh [open $flow] ; set txt [read $sfh] ; close $sfh
set code_lines [lmap l [split $txt \n] {expr {[string match {\#*} [string trim $l]] ? [continue] : $l}}]
set bits [llength [lsearch -all -glob $code_lines *write_bitstream*]]
puts "write_bitstream in executable lines: $bits (expect 0)"
if {$bits != 0} { incr fails }
set hp [llength [regexp -all -inline {/home/[a-z]+} $txt]]
puts "hardcoded /home paths in script: $hp (expect 0)"
if {$hp != 0} { incr fails }
puts "DRYRUN [expr {$fails == 0 ? {PASS} : "FAIL ($fails)"}]"
::real_exit [expr {$fails == 0 ? 0 : 1}]
