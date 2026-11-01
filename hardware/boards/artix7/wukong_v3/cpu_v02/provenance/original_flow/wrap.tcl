# CPU-BOARD-3 Phase S: cap Vivado worker threads at 2, then run the unmodified synthesis-only flow script.
set_param general.maxThreads 2
puts "BOARD3_MAXTHREADS=[get_param general.maxThreads]"
source /home/john/.local/gate/spu-int3b-c3efc18/tools/vivado/spu_vivado_flow.tcl
