`timescale 1ns / 1ps
// NUM-SOM-4 Phase B lockstep probe: previous spu13_core (spu13_core_base, extracted by the runner from git at 2a9a9f1, renamed) versus the
// current spu13_core under identical stimulus; every compared output must match every cycle. Configuration chosen by macros:
//   LK_V2 / LK_PIPE / LK_SOM select the core RPLU2/SOM branches; LK_MODE 0 = QLDI/QSUB/ROTC only, 1 = also in-domain 0x2A,
//   2 = also 0x2A with arbitrary injected 32-bit source data (only for configurations without the guard: out-of-domain pipeline input differs by design).
// Not a regression-gate testbench (file name avoids 'tb'). Exits nonzero ($fatal) on any mismatch.
`include "spu_arch_defines.vh"
module numsom4b_lock;
    reg clk = 1'b0; always #5 clk = ~clk;
    reg rst_n = 1'b0; reg inst_valid = 1'b0; reg [63:0] inst_word = 64'd0;
    reg cfg_wr_en = 1'b0; reg [2:0] cfg_sel = 3'd0; reg [9:0] cfg_addr = 10'd0; reg [63:0] cfg_data = 64'd0;
    wire [0:0] b_qr_commit_valid, n_qr_commit_valid;
    wire [3:0] b_qr_commit_lane, n_qr_commit_lane;
    wire [63:0] b_qr_commit_A, n_qr_commit_A;
    wire [63:0] b_qr_commit_B, n_qr_commit_B;
    wire [63:0] b_qr_commit_C, n_qr_commit_C;
    wire [63:0] b_qr_commit_D, n_qr_commit_D;
    wire [0:0] b_inst_done, n_inst_done;
    wire [0:0] b_hex_valid, n_hex_valid;
    wire [15:0] b_hex_q, n_hex_q;
    wire [15:0] b_hex_r, n_hex_r;
    wire [0:0] b_rns_error, n_rns_error;
    wire [0:0] b_ecc_single_err, n_ecc_single_err;
    wire [0:0] b_ecc_double_err, n_ecc_double_err;
    wire [0:0] b_axiomatic_fault, n_axiomatic_fault;
    wire [1:0] b_fault_type, n_fault_type;
    wire [15:0] b_fault_count, n_fault_count;
    wire [0:0] b_rplu_dissoc_out, n_rplu_dissoc_out;
    wire [9:0] b_rplu_addr_out, n_rplu_addr_out;
    wire [31:0] b_quadrance_out, n_quadrance_out;
    wire [0:0] b_cycle_wrap, n_cycle_wrap;
    wire [15:0] b_rotc_debug_status, n_rotc_debug_status;
    wire [15:0] b_regen_debug_status, n_regen_debug_status;
    wire [0:0] b_boot_ready, n_boot_ready;
    wire [1:0] b_boot_state_dbg, n_boot_state_dbg;
    wire [0:0] b_artery_wr_en, n_artery_wr_en;
    wire [63:0] b_artery_wr_data, n_artery_wr_data;
    wire [3:0] b_current_axis_ptr, n_current_axis_ptr;
    wire [63:0] b_current_axis_data, n_current_axis_data;
    wire [7:0] b_laminar_flow_index_out, n_laminar_flow_index_out;
    wire [31:0] b_thermal_pressure_out, n_thermal_pressure_out;
    wire [31:0] b_audio_p_out, n_audio_p_out;
    wire [31:0] b_audio_q_out, n_audio_q_out;
    wire [15:0] b_gasket_sum_out, n_gasket_sum_out;
    wire [0:0] b_is_janus_point, n_is_janus_point;
    wire [1:0] b_audio_mode, n_audio_mode;
    wire [0:0] b_ratio_cmp_valid, n_ratio_cmp_valid;
    wire [2:0] b_ratio_cmp_res, n_ratio_cmp_res;
    wire refused_new;
    spu13_core_base #(.DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(`LK_SOM),
        .ENABLE_CORE_RPLU_V2(`LK_V2), .ENABLE_CORE_RPLU_V2_PIPELINE(`LK_PIPE), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0), .SHARE_RPLU_PADE_INV_MULT(1)) ub (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0), .dec_fast_cfg_wr_en(cfg_wr_en), .dec_fast_cfg_sel(cfg_sel),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(cfg_addr), .dec_fast_cfg_data(cfg_data), .phinary_cfg(16'd0), .prime_data(24'd0),
        .prime_addr(4'd0), .prime_we(1'b0), .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0), .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0), .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(),
        .mem_burst_done(1'b0), .inst_valid(inst_valid), .inst_word(inst_word),
        .manifold_out(), .bloom_complete(), .scale_table_out(), .scale_overflow_out(), .i2s_bclk(), .i2s_lrclk(), .i2s_dout(), .rplu_dissoc_mask_out(),
        .qr_commit_valid(b_qr_commit_valid),
        .qr_commit_lane(b_qr_commit_lane),
        .qr_commit_A(b_qr_commit_A),
        .qr_commit_B(b_qr_commit_B),
        .qr_commit_C(b_qr_commit_C),
        .qr_commit_D(b_qr_commit_D),
        .inst_done(b_inst_done),
        .hex_valid(b_hex_valid),
        .hex_q(b_hex_q),
        .hex_r(b_hex_r),
        .rns_error(b_rns_error),
        .ecc_single_err(b_ecc_single_err),
        .ecc_double_err(b_ecc_double_err),
        .axiomatic_fault(b_axiomatic_fault),
        .fault_type(b_fault_type),
        .fault_count(b_fault_count),
        .rplu_dissoc_out(b_rplu_dissoc_out),
        .rplu_addr_out(b_rplu_addr_out),
        .quadrance_out(b_quadrance_out),
        .cycle_wrap(b_cycle_wrap),
        .rotc_debug_status(b_rotc_debug_status),
        .regen_debug_status(b_regen_debug_status),
        .boot_ready(b_boot_ready),
        .boot_state_dbg(b_boot_state_dbg),
        .artery_wr_en(b_artery_wr_en),
        .artery_wr_data(b_artery_wr_data),
        .current_axis_ptr(b_current_axis_ptr),
        .current_axis_data(b_current_axis_data),
        .laminar_flow_index_out(b_laminar_flow_index_out),
        .thermal_pressure_out(b_thermal_pressure_out),
        .audio_p_out(b_audio_p_out),
        .audio_q_out(b_audio_q_out),
        .gasket_sum_out(b_gasket_sum_out),
        .is_janus_point(b_is_janus_point),
        .audio_mode(b_audio_mode),
        .ratio_cmp_valid(b_ratio_cmp_valid),
        .ratio_cmp_res(b_ratio_cmp_res));

    spu13_core #(.DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(`LK_SOM),
        .ENABLE_CORE_RPLU_V2(`LK_V2), .ENABLE_CORE_RPLU_V2_PIPELINE(`LK_PIPE), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0), .SHARE_RPLU_PADE_INV_MULT(1)) un (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0), .dec_fast_cfg_wr_en(cfg_wr_en), .dec_fast_cfg_sel(cfg_sel),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(cfg_addr), .dec_fast_cfg_data(cfg_data), .phinary_cfg(16'd0), .prime_data(24'd0),
        .prime_addr(4'd0), .prime_we(1'b0), .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0), .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0), .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(),
        .mem_burst_done(1'b0), .inst_valid(inst_valid), .inst_word(inst_word),
        .rplu2_domain_refused(refused_new),
        .manifold_out(), .bloom_complete(), .scale_table_out(), .scale_overflow_out(), .i2s_bclk(), .i2s_lrclk(), .i2s_dout(), .rplu_dissoc_mask_out(),
        .qr_commit_valid(n_qr_commit_valid),
        .qr_commit_lane(n_qr_commit_lane),
        .qr_commit_A(n_qr_commit_A),
        .qr_commit_B(n_qr_commit_B),
        .qr_commit_C(n_qr_commit_C),
        .qr_commit_D(n_qr_commit_D),
        .inst_done(n_inst_done),
        .hex_valid(n_hex_valid),
        .hex_q(n_hex_q),
        .hex_r(n_hex_r),
        .rns_error(n_rns_error),
        .ecc_single_err(n_ecc_single_err),
        .ecc_double_err(n_ecc_double_err),
        .axiomatic_fault(n_axiomatic_fault),
        .fault_type(n_fault_type),
        .fault_count(n_fault_count),
        .rplu_dissoc_out(n_rplu_dissoc_out),
        .rplu_addr_out(n_rplu_addr_out),
        .quadrance_out(n_quadrance_out),
        .cycle_wrap(n_cycle_wrap),
        .rotc_debug_status(n_rotc_debug_status),
        .regen_debug_status(n_regen_debug_status),
        .boot_ready(n_boot_ready),
        .boot_state_dbg(n_boot_state_dbg),
        .artery_wr_en(n_artery_wr_en),
        .artery_wr_data(n_artery_wr_data),
        .current_axis_ptr(n_current_axis_ptr),
        .current_axis_data(n_current_axis_data),
        .laminar_flow_index_out(n_laminar_flow_index_out),
        .thermal_pressure_out(n_thermal_pressure_out),
        .audio_p_out(n_audio_p_out),
        .audio_q_out(n_audio_q_out),
        .gasket_sum_out(n_gasket_sum_out),
        .is_janus_point(n_is_janus_point),
        .audio_mode(n_audio_mode),
        .ratio_cmp_valid(n_ratio_cmp_valid),
        .ratio_cmp_res(n_ratio_cmp_res));

    wire [4095:0] vb = {b_qr_commit_valid, b_qr_commit_lane, b_qr_commit_A, b_qr_commit_B, b_qr_commit_C, b_qr_commit_D, b_inst_done, b_hex_valid, b_hex_q, b_hex_r, b_rns_error, b_ecc_single_err, b_ecc_double_err, b_axiomatic_fault, b_fault_type, b_fault_count, b_rplu_dissoc_out, b_rplu_addr_out, b_quadrance_out, b_cycle_wrap, b_rotc_debug_status, b_regen_debug_status, b_boot_ready, b_boot_state_dbg, b_artery_wr_en, b_artery_wr_data, b_current_axis_ptr, b_current_axis_data, b_laminar_flow_index_out, b_thermal_pressure_out, b_audio_p_out, b_audio_q_out, b_gasket_sum_out, b_is_janus_point, b_audio_mode, b_ratio_cmp_valid, b_ratio_cmp_res};
    wire [4095:0] vn = {n_qr_commit_valid, n_qr_commit_lane, n_qr_commit_A, n_qr_commit_B, n_qr_commit_C, n_qr_commit_D, n_inst_done, n_hex_valid, n_hex_q, n_hex_r, n_rns_error, n_ecc_single_err, n_ecc_double_err, n_axiomatic_fault, n_fault_type, n_fault_count, n_rplu_dissoc_out, n_rplu_addr_out, n_quadrance_out, n_cycle_wrap, n_rotc_debug_status, n_regen_debug_status, n_boot_ready, n_boot_state_dbg, n_artery_wr_en, n_artery_wr_data, n_current_axis_ptr, n_current_axis_data, n_laminar_flow_index_out, n_thermal_pressure_out, n_audio_p_out, n_audio_q_out, n_gasket_sum_out, n_is_janus_point, n_audio_mode, n_ratio_cmp_valid, n_ratio_cmp_res};
    integer cycles = 0, mism = 0, first_bad = -1, ops = 0, n2a = 0, n2a_refused = 0, ndone_b = 0, seed = 424242, i, g, k, op, ln, lm;
    reg [63:0] w, rv; reg [3:0] a1, a2, a3; reg [5:0] ang;
    always @(posedge clk) begin
        cycles = cycles + 1;
        if (vb !== vn) begin mism = mism + 1; if (first_bad < 0) first_bad = cycles; end
        if (b_inst_done) ndone_b = ndone_b + 1;
        if (refused_new) n2a_refused = n2a_refused + 1;
    end
    function [63:0] qldi; input [7:0] lane; input [7:0] a, b, c, d; qldi = {8'h1D, lane, 8'd0, a, b, c, d, 8'd0}; endfunction
    function bad; input [31:0] v; reg signed [63:0] s; begin s = $signed(v); bad = (s > 9457) || (s < -9457); end endfunction
    function lane_ok; input [3:0] l; reg [63:0] a, b, c, d; begin
        a = ub.gen_qrf.u_qrf.u_regfile.reg_A[l]; b = ub.gen_qrf.u_qrf.u_regfile.reg_B[l]; c = ub.gen_qrf.u_qrf.u_regfile.reg_C[l]; d = ub.gen_qrf.u_qrf.u_regfile.reg_D[l];
        lane_ok = !(bad(a[31:0]) | bad(a[63:32]) | bad(b[31:0]) | bad(b[63:32]) | bad(c[31:0]) | bad(c[63:32]) | bad(d[31:0]) | bad(d[63:32])); end endfunction
    task issue; input [63:0] x; begin @(posedge clk); inst_word <= x; inst_valid <= 1; @(posedge clk); inst_valid <= 0; end endtask
    task wait_done; begin g = 0; while (!b_inst_done && g < 800) begin @(posedge clk); g = g + 1; end repeat (1 + ($random(seed) & 3)) @(posedge clk); end endtask
    task cfg_write; input [2:0] sel; input [9:0] addr; input [63:0] data; begin
        @(negedge clk); cfg_sel = sel; cfg_addr = addr; cfg_data = data; cfg_wr_en = 1; @(negedge clk); cfg_wr_en = 0; cfg_sel = 0; cfg_addr = 0; cfg_data = 0; end endtask
    task do_reset; begin
        rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); rst_n <= 1; @(posedge clk);
        g = 0; while (!(b_boot_ready && n_boot_ready) && g < 300) begin @(posedge clk); g = g + 1; end repeat (4) @(posedge clk);
        cfg_write(3'd1, 10'd0, {32'd0, 32'd2}); cfg_write(3'd1, 10'd8, 64'd0);
        for (k = 0; k < 7; k = k + 1) begin cfg_write(3'd3, k, {32'd0, 32'd1}); cfg_write(3'd3, k + 64, 64'd0); end end endtask
    task inject_both; input [3:0] l; input [63:0] a, b, c, d; begin
        @(negedge clk);
        force ub.gen_qrf.u_qrf.wr_en = 1'b1; force ub.gen_qrf.u_qrf.wr_lane = l; force ub.gen_qrf.u_qrf.wr_A = a; force ub.gen_qrf.u_qrf.wr_B = b; force ub.gen_qrf.u_qrf.wr_C = c; force ub.gen_qrf.u_qrf.wr_D = d;
        force un.gen_qrf.u_qrf.wr_en = 1'b1; force un.gen_qrf.u_qrf.wr_lane = l; force un.gen_qrf.u_qrf.wr_A = a; force un.gen_qrf.u_qrf.wr_B = b; force un.gen_qrf.u_qrf.wr_C = c; force un.gen_qrf.u_qrf.wr_D = d;
        @(negedge clk);
        release ub.gen_qrf.u_qrf.wr_en; release ub.gen_qrf.u_qrf.wr_lane; release ub.gen_qrf.u_qrf.wr_A; release ub.gen_qrf.u_qrf.wr_B; release ub.gen_qrf.u_qrf.wr_C; release ub.gen_qrf.u_qrf.wr_D;
        release un.gen_qrf.u_qrf.wr_en; release un.gen_qrf.u_qrf.wr_lane; release un.gen_qrf.u_qrf.wr_A; release un.gen_qrf.u_qrf.wr_B; release un.gen_qrf.u_qrf.wr_C; release un.gen_qrf.u_qrf.wr_D;
        @(negedge clk); end endtask
    initial begin
        do_reset;
        for (i = 0; i < 160; i = i + 1) begin
            if (i % 40 == 39) do_reset;
            ln = $random(seed) & 255; a1 = (ln % 13); ln = $random(seed) & 255; a2 = (ln % 13); ln = $random(seed) & 255; a3 = (ln % 13);
            op = $random(seed) & 7;
            if (`LK_MODE == 0 && op > 4) op = op - 4;
            case (op)
                0, 1: w = qldi({4'd0, a1}, $random(seed), $random(seed), $random(seed), $random(seed));
                2:    w = {8'h1B, 4'd0, a1, 4'd0, a2, 16'd0, 12'd0, a3, 8'd0};
                3, 4: begin k = $random(seed) & 7; ang = (k < 6) ? k : (6 + ($random(seed) & 31)); w = {8'h1C, 4'd0, a1, 4'd0, a2, 10'd0, ang, 24'd0}; end
                default: begin   // 0x2A
                    if (`LK_MODE == 1) begin
                        if (!lane_ok(a2)) begin issue(qldi({4'd0, a2}, $random(seed), $random(seed), $random(seed), $random(seed))); wait_done; end
                    end else begin
                        rv = {$random(seed), $random(seed)};
                        if (($random(seed) & 3) != 0) inject_both(a2, rv, {$random(seed), $random(seed)}, {$random(seed), $random(seed)}, {$random(seed), $random(seed)});
                    end
                    w = {8'h2A, 4'd0, a1, 4'd0, a2, 40'd0}; n2a = n2a + 1; end
            endcase
            issue(w); ops = ops + 1; wait_done;
        end
        repeat (40) @(posedge clk);
        $display("LOCK v2=%0d pipe=%0d som=%0d mode=%0d ops=%0d ops_2A=%0d cycles=%0d base_done=%0d refusals_new=%0d mismatches=%0d", `LK_V2, `LK_PIPE, `LK_SOM, `LK_MODE, ops, n2a, cycles, ndone_b, n2a_refused, mism);
        if (mism != 0) $fatal(1, "lockstep mismatch: first at cycle %0d", first_bad);
        $finish;
    end
    initial begin #800000000; $display("TIMEOUT"); $fatal(1, "timeout"); end
endmodule
