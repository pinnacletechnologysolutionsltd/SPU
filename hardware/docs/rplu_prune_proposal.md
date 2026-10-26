# RPLU Cubic Audit — Prune / Archive Proposal

Files scanned: 253  
Files with $readmem: 14  
Files with 'real': 7  
Files with 'float': 2  
\n## Candidate modules for archive / rewrite / centralize\n
|file|reason|readmem|max_reg|has_real|has_float|
|---|---|---:|---:|---:|---:|
|hardware/common/rtl/spu_microcode_rom.v|readmem |1|23|0|0|
|hardware/common/rtl/spu_whisper_bridge.v|large_reg |0|831|0|0|
|hardware/common/rtl/core/spu_core.v|large_reg |0|831|0|0|
|hardware/common/rtl/proto/spu_pmod_loader.v|large_reg |0|831|0|0|
|hardware/common/rtl/prim/spu_psram_ctrl.v|real large_reg |0|831|1|0|
|hardware/common/rtl/prim/spu_rotary_gate.v|large_reg |0|831|0|0|
|hardware/common/rtl/top/spu_system.v|large_reg |0|831|0|0|
|hardware/common/rtl/top/spu_pell_cache.v|large_reg |0|831|0|0|
|hardware/common/rtl/mem/spu_mem_bridge_ddr3.v|real |0|15|1|0|
|hardware/common/rtl/graphics/spu_fragment_pipe.v|float |0|127|0|1|
|hardware/common/rtl/bio/spu_fluid_solver.v|large_reg |0|831|0|0|
|hardware/common/rtl/bio/spu_proprioception.v|large_reg |0|831|0|0|
|hardware/common/rtl/io/spu_sd_controller.v|real |0|127|1|0|
|hardware/common/rtl/gpu/rational_sine_rom.v|readmem |1|31|0|0|
|hardware/common/rtl/gpu/rational_sine_rom_q32.v|readmem |1|63|0|0|
|hardware/common/rtl/gpu/rplu_skel.v|readmem |4|63|0|0|
|hardware/common/rtl/gpu/injection_gate.v|readmem |2|1|0|0|
|hardware/common/rtl/gpu/pade_eval_2_2.v|readmem |2|3|0|0|
|hardware/common/rtl/gpu/simple_lau.v|readmem |1|9|0|0|
|hardware/common/rtl/gpu/laminar_detector.v|large_reg |0|1023|0|0|
|hardware/common/rtl/gpu/pade_eval_4_4.v|readmem |2|3|0|0|
|hardware/common/rtl/gpu/rplu_exp.v|readmem |11|31|0|0|
|hardware/common/tests/spu_psram_dual_tb.v|float large_reg |0|831|0|1|
|hardware/common/tests/spu_mem_bridge_sdram_tb.v|real large_reg |0|831|1|0|
|hardware/common/tests/spu_spi_slave_tb.v|large_reg |0|831|0|0|
|hardware/common/tests/spu_pell_cache_tb.v|large_reg |0|831|0|0|
|hardware/common/tests/spu_whisper_bridge_v2_tb.v|large_reg |0|831|0|0|
|hardware/common/tests/spu_mem_bridge_ddr3_tb.v|large_reg |0|831|0|0|
|hardware/common/tests/rational_sine_provider_tb.v|real |0|0|1|0|
|hardware/common/tests/rplu_tb.v|readmem |4|63|0|0|
|hardware/common/tests/rplu_exp_tb.v|readmem |3|63|0|0|
|hardware/common/tests/pade_eval_4_4_tb.v|readmem |2|63|0|0|
|hardware/spu4/tests/spu4_precession_tb.v|readmem |1|23|0|0|
|hardware/boards/tang_primer_25k/spu_tang_top.v|real |0|0|1|0|
|hardware/boards/gw1n1/spu_gw1n1_top.v|readmem |1|15|0|0|
|hardware/vendor/ice40/SB_HFOSC.v|real |0|0|1|0|

Recommended actions:

- Archive: move legacy/scientific modules into hardware/archive/legacy_rtl for later translation to RPLU constants or accelerator builds.
- Rewrite: replace floating-point or large ROM table implementations with RPLU-driven constant expansion where numeric fidelity allows.
- Centralize: heavy BRAM/DSP modules (large_reg) should be considered for SPU-13 or a dedicated accelerator sandbox (SPU-4 cluster image).

Files with large ROM loads (readmem):
hardware/common/rtl/spu_microcode_rom.v:10:        $readmemh("spu_init.mem", rom_data);
hardware/common/rtl/gpu/rational_sine_rom.v:9:        $readmemh("hardware/common/rtl/gpu/rational_sine_4096.mem", rom);
hardware/common/rtl/gpu/rational_sine_rom_q32.v:9:        $readmemh("hardware/common/rtl/gpu/rational_sine_4096_q32.mem", rom);
hardware/common/rtl/gpu/rplu_skel.v:26:        $readmemh("hardware/common/rtl/gpu/rplu_rom_carbon.mem", rom_carbon);
hardware/common/rtl/gpu/rplu_skel.v:27:        $readmemh("hardware/common/rtl/gpu/rplu_rom_iron.mem", rom_iron);
hardware/common/rtl/gpu/rplu_skel.v:28:        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_carbon.mem", diss_carbon);
hardware/common/rtl/gpu/rplu_skel.v:29:        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_iron.mem", diss_iron);
hardware/common/rtl/gpu/injection_gate.v:42:        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm_carbon);
hardware/common/rtl/gpu/injection_gate.v:43:        $readmemh("hardware/common/rtl/gpu/vnorm_iron.mem", vnorm_iron);
hardware/common/rtl/gpu/pade_eval_2_2.v:30:        $readmemh("hardware/common/rtl/gpu/pade_num_2_2_q32.mem", num_coeff);
hardware/common/rtl/gpu/pade_eval_2_2.v:31:        $readmemh("hardware/common/rtl/gpu/pade_den_2_2_q32.mem", den_coeff);
hardware/common/rtl/gpu/simple_lau.v:16:        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm);
hardware/common/rtl/gpu/pade_eval_4_4.v:20:        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", num_coef);
hardware/common/rtl/gpu/pade_eval_4_4.v:21:        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", den_coef);
hardware/common/rtl/gpu/rplu_exp.v:32:        $readmemh("hardware/common/rtl/gpu/params_carbon.hex", params_carbon);
hardware/common/rtl/gpu/rplu_exp.v:33:        $readmemh("hardware/common/rtl/gpu/params_iron.hex", params_iron);
hardware/common/rtl/gpu/rplu_exp.v:44:        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", pade_num_q32);
hardware/common/rtl/gpu/rplu_exp.v:45:        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", pade_den_q32);
hardware/common/rtl/gpu/rplu_exp.v:47:        $readmemh("hardware/common/rtl/gpu/pade_num_4_4.mem", pade_num_q16);
hardware/common/rtl/gpu/rplu_exp.v:48:        $readmemh("hardware/common/rtl/gpu/pade_den_4_4.mem", pade_den_q16);
hardware/common/rtl/gpu/rplu_exp.v:53:        #1; // allow $readmemh to complete
hardware/common/rtl/gpu/rplu_exp.v:125:        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm_carbon);
hardware/common/rtl/gpu/rplu_exp.v:126:        $readmemh("hardware/common/rtl/gpu/vnorm_dissoc_carbon.mem", vnorm_dissoc_carbon);
hardware/common/rtl/gpu/rplu_exp.v:127:        $readmemh("hardware/common/rtl/gpu/vnorm_iron.mem", vnorm_iron);
hardware/common/rtl/gpu/rplu_exp.v:128:        $readmemh("hardware/common/rtl/gpu/vnorm_dissoc_iron.mem", vnorm_dissoc_iron);
hardware/common/tests/rplu_tb.v:33:        $readmemh("hardware/common/rtl/gpu/rplu_rom_carbon.mem", exp_carbon);
hardware/common/tests/rplu_tb.v:34:        $readmemh("hardware/common/rtl/gpu/rplu_rom_iron.mem",   exp_iron);
hardware/common/tests/rplu_tb.v:35:        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_carbon.mem", exp_diss_c);
hardware/common/tests/rplu_tb.v:36:        $readmemh("hardware/common/rtl/gpu/rplu_dissoc_iron.mem",   exp_diss_i);
hardware/common/tests/rplu_exp_tb.v:30:        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm_exp);
hardware/common/tests/rplu_exp_tb.v:31:        $readmemh("hardware/common/rtl/gpu/vnorm_dissoc_carbon.mem", vnorm_diss);
hardware/common/tests/rplu_exp_tb.v:32:        $readmemh("hardware/common/rtl/gpu/r_rom_carbon.mem", r_rom);
hardware/common/tests/pade_eval_4_4_tb.v:31:        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", num);
hardware/common/tests/pade_eval_4_4_tb.v:32:        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", den);
hardware/spu4/tests/spu4_precession_tb.v:18:        $readmemh("hardware/spu4/tests/precession.hex", prog_mem);
hardware/boards/gw1n1/spu_gw1n1_top.v:43:    initial $readmemh("spu_init.mem", seed_rom, 0, 7);
\nEnd of proposal.
