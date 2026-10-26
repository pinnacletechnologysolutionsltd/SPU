# Load only the 'proc' definitions of a flow script (no top-level execution). Usage: source load_procs.tcl ; spu_load_procs FILE
proc spu_load_procs {f} {
    set fh [open $f] ; set txt [read $fh] ; close $fh ; set cmd ""
    foreach line [split $txt \n] {
        append cmd $line \n
        if {[info complete $cmd]} { if {[lindex [string trim $cmd] 0] eq "proc"} { uplevel #0 $cmd } ; set cmd "" }
    }
}
