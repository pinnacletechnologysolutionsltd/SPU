# SPU Vivado file list. Grammar: 'incdir <dir>' | 'define NAME[=VAL]' | 'verilog <file>' | 'sv <file>' | '# comment'. Paths are relative to the repository root.
# Order is the read order. Do not edit to make a run pass; changes need a new review and a new hash.
# Tensegrity link (silicon-proven standalone top per docs/hardware_evidence.md): top = spu_a7_tensegrity_link_top,
# constraints spu_a7_tensegrity_link.xdc. Same clock/reset construct as the Base top. Derived from synth_a7_tensegrity_link.ys.
sv hardware/rtl/peripherals/io/spu_spi_slave.v
sv hardware/rtl/core/spu13/spu13_zphi_mul_serial.v
sv hardware/rtl/core/spu13/spu13_zphi_mul_serial_karatsuba.v
sv hardware/rtl/core/spu13/spu13_tensegrity_intersection.v
sv hardware/rtl/core/spu13/spu13_tensegrity_guard.v
sv hardware/rtl/core/spu13/spu13_tensegrity_sidecar.v
sv hardware/boards/artix7/spu_a7_tensegrity_link_top.v
