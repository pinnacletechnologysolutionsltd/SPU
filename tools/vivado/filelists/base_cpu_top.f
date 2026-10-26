# SPU Vivado file list. Grammar: 'incdir <dir>' | 'define NAME[=VAL]' | 'verilog <file>' | 'sv <file>' | '# comment'. Paths are relative to the repository root.
# Order is the read order. Do not edit to make a run pass; changes need a new review and a new hash.
# Base SPU CPU (CPU-BASE-TOP-1): top = spu_a7_surd_cpu_base_top, part xc7a100tfgg676-1, constraints spu_a7_surd_cpu_base.xdc.
# ENABLE_REGEN=0 is set by the top's own instantiation (no -generic needed). Derived from the frozen S2-R2 manifest
# (build/cpu_base_top1_s2r2_prep/source_manifest.json, 20 sources, same order as the Yosys read list).
incdir hardware/rtl/arch
incdir hardware/rtl/core/spu13
sv hardware/rtl/common/prim/spu_hamming_72_64.v
sv hardware/rtl/core/shared/spu_quadray_regfile.v
sv hardware/rtl/core/shared/spu_quadray_regfile_ecc.v
sv hardware/rtl/core/spu13/fpga_chain.v
sv hardware/rtl/core/spu13/spu13_core.v
sv hardware/rtl/core/spu13/spu13_regen.v
sv hardware/rtl/core/spu13/spu13_surd_arith.v
sv hardware/rtl/core/spu13/spu13_surd_bank.v
sv hardware/rtl/core/spu13/spu13_surd_exec.v
sv hardware/rtl/core/spu13/spu13_surd_load.v
sv hardware/rtl/math/rational_surd5_scale_manager.v
sv hardware/rtl/math/surd_binary_gcd3.v
sv hardware/rtl/math/surd_cpu_products.v
sv hardware/rtl/math/surd_exact_quotient.v
sv hardware/rtl/math/surd_normalize_unit.v
sv hardware/rtl/peripherals/bio/spu_annealer.v
sv hardware/rtl/peripherals/io/spu_i2s_out.v
sv hardware/rtl/top/spu_ve_qr_init.v
sv hardware/boards/artix7/spu_a7_surd_cpu_bench_top.v
sv hardware/boards/artix7/spu_a7_surd_cpu_base_top.v
