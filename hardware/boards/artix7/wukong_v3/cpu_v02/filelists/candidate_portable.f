# DERIVED, not a silicon-build input. Same entries and order as candidate_original.f; only the five experiment/ paths are rewritten to cpu_v02/rtl/. Paths are relative to the repository root.
# Its sha256 therefore differs from the golden build filelist_sha256 (cc5a0359...); see ../SOURCE_MANIFEST.md.
incdir hardware/rtl/arch
incdir hardware/rtl/core/spu13
sv hardware/rtl/core/spu13/fpga_chain.v
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
sv hardware/rtl/common/prim/spu_hamming_72_64.v
sv hardware/rtl/core/shared/spu_quadray_regfile.v
sv hardware/rtl/core/shared/spu_quadray_regfile_ecc.v
sv hardware/rtl/core/spu13/spu13_regen.v
sv hardware/rtl/top/spu_ve_qr_init.v
sv hardware/boards/artix7/wukong_v3/cpu_v02/rtl/spu13_core.v
sv hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_fetch_1b.v
sv hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_rst_1b_supervisor.v
sv hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_integrate_1_top.v
sv hardware/boards/artix7/wukong_v3/cpu_v02/rtl/board_top.v
