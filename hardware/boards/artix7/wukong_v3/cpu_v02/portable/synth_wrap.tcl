# Portable counterpart of provenance/original_flow/wrap.tcl: cap Vivado worker threads at 2, then run the unmodified synthesis-only flow script.
set_param general.maxThreads 2
puts "BOARD3_MAXTHREADS=[get_param general.maxThreads]"
source [file normalize [file join [file dirname [file normalize [info script]]] .. .. .. .. .. .. tools vivado spu_vivado_flow.tcl]]
