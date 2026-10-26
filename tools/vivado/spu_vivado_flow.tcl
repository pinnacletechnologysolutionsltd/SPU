# spu_vivado_flow.tcl — non-project-mode Vivado batch flow for SPU Artix-7 targets.  PREPARED, NOT RUN.
#
#   vivado -mode batch -log OUT/vivado.log -journal OUT/vivado.jou -source tools/vivado/spu_vivado_flow.tcl -tclargs \
#       -top <module> -part <exact part> -filelist <file.f> -xdc <file.xdc> -outdir OUT \
#       [-generic NAME=VALUE]... [-stage synth|place|route] [-ack PLACE_APPROVED|ROUTE_APPROVED]
#
# Required: -top -part -filelist -xdc -outdir.  Nothing is guessed: part, top, sources and constraints come only from the arguments.
# Stages: synth (default) = synth_design + reports.  place / route are separate gated stages and refuse to run without the matching
# -ack token, which only an owner-authorized run supplies.  There is deliberately NO write_bitstream and no hardware access in this script.
# Failure behaviour: any error writes OUT/FAILED (message) and exits 1; success writes OUT/COMPLETE and exits 0; exactly one marker.
# OUT must already exist, must contain nothing but vivado.log/vivado.jou, and must not be inside tracked source (hardware/, software/, tools/, docs/).
# Reports before place_design are un-placed estimates: they are NOT timing closure evidence.

proc spu_fail {msg} { error "SPU_FLOW: $msg" }
proc spu_sha {f} { return [lindex [exec sha256sum $f] 0] }
proc spu_opt {args_dict key {default ""}} { if {[dict exists $args_dict $key]} { return [dict get $args_dict $key] } ; return $default }

proc spu_parse {argv} {
    set d [dict create generics {} expect_clocks {}]
    set known {-top -part -filelist -xdc -outdir -stage -ack -generic -strict -expect_clock}
    for {set i 0} {$i < [llength $argv]} {incr i 2} {
        set k [lindex $argv $i]
        if {[lsearch -exact $known $k] < 0} { spu_fail "unknown argument '$k'" }
        if {$i + 1 >= [llength $argv]} { spu_fail "argument $k has no value" }
        set v [lindex $argv [expr {$i + 1}]]
        if {$k eq "-generic"} { dict lappend d generics $v } elseif {$k eq "-expect_clock"} { dict lappend d expect_clocks $v } else { dict set d $k $v }
    }
    foreach r {-top -part -filelist -xdc -outdir} { if {![dict exists $d $r]} { spu_fail "missing required argument $r" } }
    if {![dict exists $d -stage]} { dict set d -stage synth }
    if {![dict exists $d -strict]} { dict set d -strict 0 }
    if {[lsearch -exact {0 1} [dict get $d -strict]] < 0} { spu_fail "-strict must be 0 or 1" }
    foreach e [dict get $d expect_clocks] { if {![regexp {^[A-Za-z_][A-Za-z0-9_]*:[0-9]+(\.[0-9]+)?$} $e]} { spu_fail "-expect_clock must be NAME:PERIOD_NS, got $e" } }
    if {[lsearch -exact {synth place route} [dict get $d -stage]] < 0} { spu_fail "-stage must be synth, place or route" }
    return $d
}

proc spu_find_outdir {argv} { set i [lsearch -exact $argv -outdir] ; if {$i >= 0 && $i + 1 < [llength $argv]} { return [file normalize [lindex $argv [expr {$i + 1}]]] } ; return "" }

proc spu_path {root p} { if {[file pathtype $p] eq "absolute"} { return [file normalize $p] } ; return [file normalize [file join $root $p]] }

proc spu_inside_source {root out} {
    foreach bad {hardware software tools docs knowledge} { if {[string first "[file normalize [file join $root $bad]]/" "$out/"] == 0} { return $bad } }
    return ""
}

proc spu_check_outdir {root out} {
    set bad [spu_inside_source $root $out]
    if {$bad ne ""} { spu_fail "outdir inside tracked source ($bad)" }
    if {![file isdirectory $out]} { spu_fail "outdir '$out' must exist (create it before launching Vivado)" }
    foreach f [glob -nocomplain -directory $out *] { if {[lsearch -exact {vivado.log vivado.jou} [file tail $f]] < 0} { spu_fail "outdir not empty: [file tail $f]" } }
}

proc spu_read_filelist {root fl} {
    set files {} ; set incs {} ; set defs {}
    set fh [open $fl r] ; set n 0
    while {[gets $fh line] >= 0} {
        incr n ; set line [string trim $line]
        if {$line eq "" || [string index $line 0] eq "#"} continue
        set kw [lindex $line 0] ; set arg [lindex $line 1]
        switch -- $kw {
            incdir  { lappend incs [spu_path $root $arg] }
            define  { lappend defs $arg }
            verilog { lappend files [list verilog [spu_path $root $arg]] }
            sv      { lappend files [list sv [spu_path $root $arg]] }
            default { close $fh ; spu_fail "$fl:$n: unknown keyword '$kw'" }
        }
    }
    close $fh
    foreach f $files { if {![file isfile [lindex $f 1]]} { spu_fail "missing source [lindex $f 1]" } }
    foreach i $incs { if {![file isdirectory $i]} { spu_fail "missing include dir $i" } }
    if {[llength $files] == 0} { spu_fail "$fl lists no sources" }
    return [list $files $incs $defs]
}

proc spu_manifest {root out d files xdc fl} {
    set m [open [file join $out run_manifest.txt] w]
    puts $m "tool_version [version -short]"
    puts $m "started [clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%SZ} -gmt 1]"
    puts $m "host [info hostname]"
    puts $m "git_head [exec git -C $root rev-parse HEAD]"
    puts $m "git_status_sha256 [lindex [exec sh -c "git -C $root status --porcelain | sha256sum"] 0]"
    foreach k {-top -part -stage -filelist -xdc -strict} { puts $m "arg $k [dict get $d $k]" }
    foreach e [dict get $d expect_clocks] { puts $m "arg -expect_clock $e" }
    foreach g [dict get $d generics] { puts $m "arg -generic $g" }
    puts $m "filelist_sha256 [spu_sha $fl]"
    puts $m "xdc_sha256 [spu_sha $xdc]"
    foreach f $files { puts $m "source_sha256 [spu_sha [lindex $f 1]] [string range [lindex $f 1] [expr {[string length $root] + 1}] end]" }
    close $m
}

proc spu_structure {out} {
    set s [open [file join $out structure.rpt] w]
    puts $s "BUFG_cells [llength [get_cells -hierarchical -quiet -filter {REF_NAME =~ BUFG*}]]"
    puts $s "DSP48E1_cells [llength [get_cells -hierarchical -quiet -filter {REF_NAME == DSP48E1}]]"
    puts $s "RAMB_cells [llength [get_cells -hierarchical -quiet -filter {REF_NAME =~ RAMB*}]]"
    puts $s "LUT_cells [llength [get_cells -hierarchical -quiet -filter {REF_NAME =~ LUT*}]]"
    puts $s "FF_cells [llength [get_cells -hierarchical -quiet -filter {REF_NAME =~ FD*}]]"
    foreach b [get_cells -hierarchical -quiet -filter {REF_NAME =~ BUFG*}] { puts $s "BUFG [get_property NAME $b]" }
    close $s
}

proc spu_reports {out tag} {
    report_utilization -file [file join $out ${tag}_utilization.rpt]
    report_utilization -hierarchical -file [file join $out ${tag}_utilization_hier.rpt]
    report_clocks -file [file join $out ${tag}_clocks.rpt]
    report_clock_networks -file [file join $out ${tag}_clock_networks.rpt]
    check_timing -verbose -file [file join $out ${tag}_check_timing.rpt]
    report_timing_summary -delay_type min_max -max_paths 20 -file [file join $out ${tag}_timing_summary.rpt]
    report_cdc -details -file [file join $out ${tag}_cdc.rpt]
    report_methodology -file [file join $out ${tag}_methodology.rpt]
    report_drc -file [file join $out ${tag}_drc.rpt]
    spu_structure $out
}

# Log scope marker, printed just before read_xdc. Built at run time so the literal never occurs in this file, hence never in Vivado's
# '# '-prefixed echo of it (Step 7 D1: the old scan matched its own echoed source). tests/gate_fixture_test.tcl checks the file stays free of it.
proc spu_scope_marker {} { return [join {SPU GATE SCOPE BEGIN} _] }

proc spu_scan_log {txt} {
    # A finding needs both: the line comes after the single scope marker, and it is a Vivado message at column 0 with a bracketed ID
    # ("CRITICAL WARNING: [Vivado 12-4739] ..."). Echoed source starts with '#'; the gate's own FAILED text starts with "SPU_FLOW" or blanks.
    set lines [split $txt \n] ; set at [lsearch -all -exact $lines [spu_scope_marker]]
    if {[llength $at] != 1} { return [list "log scope marker found [llength $at] times, expected 1 (log not written by this script run)"] }
    set bad {}
    foreach line [lrange $lines [expr {[lindex $at 0] + 1}] end] {
        if {[regexp {^CRITICAL WARNING: \[[A-Za-z][A-Za-z0-9_ ]* [0-9]+-[0-9]+\] } $line] && [regexp {No valid object|No cells matched|No ports matched|No pins matched|No nets matched|No clocks matched|not found} $line]} { lappend bad "constraint resolved to nothing: [string trim $line]" }
        # Step 7D3: Vivado 2026.1 reports an XDC set_property whose get_* matched nothing as WARNING [Vivado 12-584] (names the object) plus this
        # CRITICAL WARNING (no object name). It proves a set_property received no objects, not which object type was missing.
        if {[regexp {^CRITICAL WARNING: \[Common 17-55\] 'set_property' expects at least one object\.} $line]} { lappend bad "constraint resolved to nothing (set_property, object type unknown): [string trim $line]" }
    }
    # Vivado repeats XDC diagnostics when it re-reads constraints (NC1: twice); identical findings are one reason. Distinct file:line stay distinct.
    set uniq {} ; foreach b $bad { if {$b ni $uniq} { lappend uniq $b } }
    return $uniq
}

proc spu_scan_check_timing {txt} {
    # One authoritative count per check: the first occurrence (the numbered summary). Vivado 2026.1 repeats each line as a section header
    # (Step 7 D2); a repeat must agree with the summary, otherwise the report is not trusted. Thresholds and check names are unchanged.
    set counts [dict create] ; set bad {}
    foreach {all nm cnt} [regexp -all -inline {checking ([a-z_]+) \(([0-9]+)\)} $txt] {
        if {![dict exists $counts $nm]} { dict set counts $nm $cnt } elseif {[dict get $counts $nm] != $cnt} { lappend bad "check_timing: $nm summary [dict get $counts $nm] disagrees with section header $cnt" }
    }
    dict for {nm cnt} $counts {
        if {$cnt > 0 && [lsearch -exact {no_clock unconstrained_internal_endpoints multiple_clock generated_clocks pulse_width_clock} $nm] >= 0} { lappend bad "check_timing: $nm = $cnt" }
    }
    if {![dict exists $counts no_clock]} { lappend bad "check_timing report has no 'checking no_clock' section (format changed or report missing)" }
    return $bad
}

proc spu_gate {out d} {
    # Fail-closed constraint checks. Log and report patterns: real-tool validation is the Step 7 rerun (missing port, wrong clock name, unclocked
    # divided domain); offline coverage is tests/gate_fixture_test.tcl (Vivado 2026.1 excerpts) and tests/dryrun_stub.tcl.
    # The expected-clock check uses Vivado Tcl commands only; the strict scans read OUT/vivado.log and OUT/synth_check_timing.rpt.
    set bad {}
    foreach e [dict get $d expect_clocks] {
        lassign [split $e :] name period
        set c [get_clocks -quiet $name]
        if {[llength $c] == 0} { lappend bad "expected clock '$name' does not exist (missing or unresolved create_clock)" ; continue }
        set p [get_property PERIOD $c]
        if {abs($p - $period) > 1e-6} { lappend bad "clock '$name' period $p ns, expected $period ns" }
    }
    if {[dict get $d -strict]} {
        set log [file join $out vivado.log]
        if {[file exists $log]} {
            set fh [open $log r] ; set txt [read $fh] ; close $fh
            lappend bad {*}[spu_scan_log $txt]
        } else { lappend bad "strict mode needs OUT/vivado.log (launch with -log OUT/vivado.log)" }
        set ct [file join $out synth_check_timing.rpt]
        if {[file exists $ct]} {
            set fh [open $ct r] ; set txt [read $fh] ; close $fh
            lappend bad {*}[spu_scan_check_timing $txt]
        } else { lappend bad "strict mode needs synth_check_timing.rpt" }
    }
    if {[llength $bad]} { spu_fail "constraint gate failed:\n  [join $bad "\n  "]" }
}

proc spu_main {argv} {
    set root [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
    set d [spu_parse $argv]
    set out [file normalize [dict get $d -outdir]]
    spu_check_outdir $root $out
    set part [dict get $d -part] ; set top [dict get $d -top] ; set stage [dict get $d -stage]
    if {[llength [get_parts -quiet $part]] != 1} { spu_fail "part '$part' not found in this Vivado installation" }
    if {$stage eq "place" && [spu_opt $d -ack] ne "PLACE_APPROVED"} { spu_fail "stage place requires an owner-supplied -ack PLACE_APPROVED" }
    if {$stage eq "route" && [spu_opt $d -ack] ne "ROUTE_APPROVED"} { spu_fail "stage route requires an owner-supplied -ack ROUTE_APPROVED" }
    set fl [spu_path $root [dict get $d -filelist]] ; set xdc [spu_path $root [dict get $d -xdc]]
    if {![file isfile $fl]} { spu_fail "file list not found: $fl" } ; if {![file isfile $xdc]} { spu_fail "xdc not found: $xdc" }
    lassign [spu_read_filelist $root $fl] files incs defs
    spu_manifest $root $out $d $files $xdc $fl
    foreach f $files { if {[lindex $f 0] eq "sv"} { read_verilog -sv [lindex $f 1] } else { read_verilog [lindex $f 1] } }
    puts [spu_scope_marker]
    read_xdc $xdc
    set cmd [list synth_design -top $top -part $part]
    if {[llength $incs]} { lappend cmd -include_dirs $incs }
    if {[llength $defs]} { lappend cmd -verilog_define $defs }
    foreach g [dict get $d generics] { lappend cmd -generic $g }
    eval $cmd
    spu_reports $out synth
    write_checkpoint -force [file join $out synth.dcp]
    spu_gate $out $d
    if {$stage in {place route}} {
        opt_design ; place_design
        spu_reports $out place
        write_checkpoint -force [file join $out place.dcp]
    }
    if {$stage eq "route"} {
        route_design
        report_route_status -file [file join $out route_status.rpt]
        spu_reports $out route
        write_checkpoint -force [file join $out route.dcp]
    }
}

if {[catch {spu_main $argv} err]} {
    set o [spu_find_outdir $argv]
    set root [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
    # write FAILED only into a directory this run was allowed to use: valid and empty at start, or already ours (run_manifest.txt exists); never into source
    if {$o ne "" && [spu_inside_source $root $o] eq "" && [file isdirectory $o] && (![catch {spu_check_outdir $root $o}] || [file exists [file join $o run_manifest.txt]])} { catch { set fh [open [file join $o FAILED] w] ; puts $fh $err ; close $fh } }
    puts stderr "SPU_FLOW FAILED: $err"
    exit 1
}
set o [spu_find_outdir $argv]
set fh [open [file join $o COMPLETE] w] ; puts $fh "ok" ; close $fh
puts "SPU_FLOW COMPLETE"
exit 0
