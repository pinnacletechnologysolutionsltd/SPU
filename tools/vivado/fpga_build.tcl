# Lightweight non-project Vivado build used by tools/vivado/fpga_build.py.
# No timing exceptions, bitstream generation, or qualification verdicts.

set_param general.maxThreads 2

proc fail {message} { error "FPGA_BUILD: $message" }

proc parse_args {argv} {
    set d [dict create]
    set allowed {-mode -top -part -filelist -xdc -outdir -checkpoint}
    for {set i 0} {$i < [llength $argv]} {incr i 2} {
        set key [lindex $argv $i]
        if {$key ni $allowed || $i + 1 >= [llength $argv]} { fail "invalid argument: $key" }
        dict set d $key [lindex $argv [expr {$i + 1}]]
    }
    foreach key {-mode -top -part -outdir} {
        if {![dict exists $d $key]} { fail "missing $key" }
    }
    if {[dict get $d -mode] ni {synth route report all}} { fail "mode must be synth, route, report, or all" }
    set mode [dict get $d -mode]
    if {$mode in {synth all}} {
        foreach key {-filelist -xdc} { if {![dict exists $d $key]} { fail "missing $key" } }
    }
    if {$mode in {route report} && ![dict exists $d -checkpoint]} { fail "$mode requires -checkpoint" }
    return $d
}

proc read_sources {root filelist} {
    set handle [open $filelist r]
    set sources {}; set includes {}; set defines {}
    set line_number 0
    while {[gets $handle line] >= 0} {
        incr line_number
        set line [string trim $line]
        if {$line eq "" || [string index $line 0] eq "#"} { continue }
        set kind [lindex $line 0]; set value [lindex $line 1]
        set path [file normalize [file join $root $value]]
        switch -- $kind {
            sv - verilog { lappend sources [list $kind $path] }
            incdir { lappend includes $path }
            define { lappend defines $value }
            default { close $handle; fail "$filelist:$line_number: unknown entry '$kind'" }
        }
    }
    close $handle
    if {![llength $sources]} { fail "source file list is empty" }
    foreach entry $sources {
        if {![file isfile [lindex $entry 1]]} { fail "source missing: [lindex $entry 1]" }
    }
    foreach path $includes {
        if {![file isdirectory $path]} { fail "include directory missing: $path" }
    }
    return [list $sources $includes $defines]
}

proc reports {out tag} {
    report_utilization -file [file join $out ${tag}_utilization.rpt]
    report_utilization -hierarchical -file [file join $out ${tag}_utilization_hier.rpt]
    report_clocks -file [file join $out ${tag}_clocks.rpt]
    report_clock_networks -file [file join $out ${tag}_clock_networks.rpt]
    report_clock_interaction -file [file join $out ${tag}_clock_interaction.rpt]
    check_timing -verbose -file [file join $out ${tag}_check_timing.rpt]
    report_timing_summary -delay_type min_max -max_paths 50 -file [file join $out ${tag}_timing_summary.rpt]
    report_cdc -details -file [file join $out ${tag}_cdc.rpt]
    report_methodology -file [file join $out ${tag}_methodology.rpt]
    report_drc -file [file join $out ${tag}_drc.rpt]
    report_exceptions -write_merged_exceptions -no_header -file [file join $out ${tag}_exceptions.rpt]
}

proc run_build {argv} {
    set d [parse_args $argv]
    set mode [dict get $d -mode]
    set out [file normalize [dict get $d -outdir]]
    if {![file isdirectory $out]} { fail "output directory missing: $out" }
    if {[llength [get_parts -quiet [dict get $d -part]]] != 1} { fail "part not found: [dict get $d -part]" }

    if {$mode in {synth all}} {
        set root [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
        set filelist [file normalize [file join $root [dict get $d -filelist]]]
        set xdc [file normalize [file join $root [dict get $d -xdc]]]
        if {![file isfile $filelist] || ![file isfile $xdc]} { fail "file list or XDC missing" }
        lassign [read_sources $root $filelist] sources includes defines
        foreach entry $sources {
            if {[lindex $entry 0] eq "sv"} { read_verilog -sv [lindex $entry 1] } else { read_verilog [lindex $entry 1] }
        }
        read_xdc $xdc
        set cmd [list synth_design -top [dict get $d -top] -part [dict get $d -part]]
        if {[llength $includes]} { lappend cmd -include_dirs $includes }
        if {[llength $defines]} { lappend cmd -verilog_define $defines }
        eval $cmd
        reports $out synth
        write_checkpoint -force [file join $out synth.dcp]
    } else {
        set checkpoint [file normalize [dict get $d -checkpoint]]
        if {![file isfile $checkpoint]} { fail "checkpoint missing: $checkpoint" }
        open_checkpoint $checkpoint
    }

    if {$mode eq "report"} {
        reports $out report
    } elseif {$mode in {route all}} {
        opt_design
        place_design
        reports $out place
        if {$mode eq "all"} { write_checkpoint -force [file join $out place.dcp] }
        route_design
        report_route_status -file [file join $out route_status.rpt]
        reports $out route
        write_checkpoint -force [file join $out route.dcp]
    }
}

if {[catch {run_build $argv} message options]} {
    puts stderr "FPGA_BUILD FAILED: $message"
    set out_index [lsearch -exact $argv -outdir]
    if {$out_index >= 0 && $out_index + 1 < [llength $argv]} {
        set out [lindex $argv [expr {$out_index + 1}]]
        if {[file isdirectory $out]} { catch {set f [open [file join $out FAILED] w]; puts $f $message; close $f} }
    }
    exit 1
}
set out_index [lsearch -exact $argv -outdir]
set out [lindex $argv [expr {$out_index + 1}]]
set f [open [file join $out COMPLETE] w]; puts $f "complete"; close $f
puts "FPGA_BUILD COMPLETE"
exit 0
