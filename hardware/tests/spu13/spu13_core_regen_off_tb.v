// spu13_core_regen_off_tb.v -- ENABLE_REGEN profile test (CPU-PROFILE-2).
// REGEN_EN=1 (default run): full profile; REGEN K=6 commits both QR lanes.
// REGEN_EN=0 (runner variant "regen_off"): base profile; REGEN (0x09) is
// unsupported -- it completes, writes no QR state, and latches the sticky
// REGEN_PREC fault (regen_debug_status[9]). Independent operations
// (QLDI/QSUB/ROTC) must commit the SAME values in both profiles; the
// expected values below come from the Python VM (test_cpu_profile.py checks
// the same constants), not from this RTL.
`timescale 1ns/1ps

module spu13_core_regen_off_tb #(parameter REGEN_EN = 1);
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg inst_valid = 0;
    reg [63:0] inst_word = 64'd0;
    wire inst_done;
    wire [15:0] regen_debug_status;
    integer errors = 0;

    // Stage B: qr_commit readback + compensation knob
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    reg [7:0] regen_dphi_cfg = 8'd0;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0), .ENABLE_CORE_RPLU_V2(0),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .ENABLE_IROTC(0), .ENABLE_REGEN(REGEN_EN)
    ) uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .regen_dphi_cfg(regen_dphi_cfg),
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(), .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(),
        .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .rns_error(), .ecc_single_err(), .ecc_double_err(),
        .rotc_debug_status(),
        .regen_debug_status(regen_debug_status)
    );

    function [63:0] qldi;
        input [7:0] lane;
        begin
            qldi = {8'h1D, lane, 8'd0, 8'd1, 8'd2, 8'd3, 8'd4, 8'd0};
        end
    endfunction

    function [63:0] qldi_val;
        input [7:0] lane;
        input [7:0] a;
        input [7:0] b;
        input [7:0] c;
        input [7:0] d;
        begin
            qldi_val = {8'h1D, lane, 8'd0, a, b, c, d, 8'd0};
        end
    endfunction

    function [63:0] regen;
        input [15:0] k;
        begin
            regen = {8'h09, 8'd0, 8'd0, k, 16'd0, 8'd0};
        end
    endfunction

    function [63:0] ld_word;   // scalar LD (NOT in E_REGEN)
        begin
            ld_word = {8'h00, 8'd0, 8'd0, 16'd1, 16'd0, 8'd0};
        end
    endfunction

    function [63:0] irotc_word; // IROTC (0xD6); ENABLE_IROTC=0 -> not eligible
        begin
            irotc_word = {8'hD6, 8'd0, 8'd0, 16'd0, 16'd0, 8'd0};
        end
    endfunction

    function [63:0] rotc;
        input [7:0] dst;
        input [7:0] src;
        input [5:0] angle;
        begin
            rotc = {8'h1C, dst, src, 8'd0, 2'b00, angle, 24'd0};
        end
    endfunction

    function [63:0] qsub;
        input [7:0] dst;
        input [7:0] src_a;
        input [7:0] src_b;
        begin
            qsub = {8'h1B, dst, src_a, 16'd0, {12'd0, src_b[3:0]}, 8'd0};
        end
    endfunction

    // capture one qr_commit pulse (lane + 4 components)
    task capture_commit;
        output [3:0] lane;
        output signed [31:0] va, vb, vc, vd;
        integer guard;
        begin
            lane = 0; va = 0; vb = 0; vc = 0; vd = 0;
            guard = 0;
            while (!qr_commit_valid && guard < 50) begin
                @(posedge clk);
                guard = guard + 1;
            end
            if (qr_commit_valid) begin
                lane = qr_commit_lane;
                va = qr_commit_A[31:0]; vb = qr_commit_B[31:0];
                vc = qr_commit_C[31:0]; vd = qr_commit_D[31:0];
                @(posedge clk);
            end
        end
    endtask

    // issue REGEN and capture both qr_commit pulses as they fire
    task issue_regen_capture;
        input [15:0] k;
        output [3:0] l0, l1;
        output signed [31:0] a0, b0, c0, d0, a1, b1, c1, d1;
        integer guard;
        begin
            l0 = 0; l1 = 0;
            a0 = 0; b0 = 0; c0 = 0; d0 = 0;
            a1 = 0; b1 = 0; c1 = 0; d1 = 0;
            @(posedge clk);
            inst_word <= regen(k);
            inst_valid <= 1'b1;
            @(posedge clk);
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
            guard = 0;
            while (!inst_done && guard < 200) begin
                @(posedge clk);
                if (qr_commit_valid) begin
                    case (qr_commit_lane)
                        4'd0: begin
                            l0 = qr_commit_lane;
                            a0 = qr_commit_A[31:0]; b0 = qr_commit_B[31:0];
                            c0 = qr_commit_C[31:0]; d0 = qr_commit_D[31:0];
                        end
                        4'd1: begin
                            l1 = qr_commit_lane;
                            a1 = qr_commit_A[31:0]; b1 = qr_commit_B[31:0];
                            c1 = qr_commit_C[31:0]; d1 = qr_commit_D[31:0];
                        end
                        default: ;
                    endcase
                end
                guard = guard + 1;
            end
            @(posedge clk);
            if (guard >= 200) begin
                $display("FAIL: REGEN instruction timeout k=%0d", k);
                errors = errors + 1;
            end
        end
    endtask

    task issue;
        input [63:0] word;
        integer guard;
        begin
            @(posedge clk);
            inst_word <= word;
            inst_valid <= 1'b1;
            @(posedge clk);
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
            guard = 0;
            while (!inst_done && guard < 200) begin
                @(posedge clk);
                guard = guard + 1;
            end
            @(posedge clk);
            if (guard >= 200) begin
                $display("FAIL: instruction timeout word=%h", word);
                errors = errors + 1;
            end
        end
    endtask

    task check;
        input [255:0] label;
        input cond;
        begin
            if (!cond) begin
                $display("FAIL: %0s", label);
                errors = errors + 1;
            end else begin
                $display("PASS: %0s", label);
            end
        end
    endtask

    // regen_debug_status layout: [11] done, [10] busy, [9] fault,
    // [8] K mismatch, [7:2] count, [1] K valid, [0] block active
    wire fault_bit  = regen_debug_status[9];
    wire [5:0] count6 = regen_debug_status[7:2];



    // Expected phase-A commits (lane, A, B, C, D low 32 bits), VM-derived.
    reg [3:0]         exp_lane [0:4];
    reg signed [31:0] exp_v    [0:19];
    integer a_idx = 0, a_bad = 0, commits_b = 0;
    reg phaseA = 0, phaseB = 0;
    initial begin
        exp_lane[0] = 0; exp_v[0]  =  3; exp_v[1]  =  1; exp_v[2]  =  0; exp_v[3]  =  2;
        exp_lane[1] = 1; exp_v[4]  =  1; exp_v[5]  =  2; exp_v[6]  =  5; exp_v[7]  =  0;
        exp_lane[2] = 2; exp_v[8]  =  2; exp_v[9]  = -1; exp_v[10] = -5; exp_v[11] =  2;
        exp_lane[3] = 3; exp_v[12] =  3; exp_v[13] =  2; exp_v[14] =  0; exp_v[15] =  1;
        exp_lane[4] = 4; exp_v[16] =  1; exp_v[17] =  5; exp_v[18] =  0; exp_v[19] =  2;
    end
    always @(posedge clk) if (rst_n) begin
        if (qr_commit_valid && phaseA) begin
            if (a_idx > 4) a_bad = a_bad + 1;
            else if (qr_commit_lane !== exp_lane[a_idx] ||
                     $signed(qr_commit_A[31:0]) !== exp_v[a_idx*4]   ||
                     $signed(qr_commit_B[31:0]) !== exp_v[a_idx*4+1] ||
                     $signed(qr_commit_C[31:0]) !== exp_v[a_idx*4+2] ||
                     $signed(qr_commit_D[31:0]) !== exp_v[a_idx*4+3]) begin
                a_bad = a_bad + 1;
                $display("FAIL: phase-A commit %0d mismatch lane=%0d %h %h %h %h", a_idx,
                         qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D);
            end
            a_idx = a_idx + 1;
        end
        if (qr_commit_valid && phaseB) commits_b = commits_b + 1;
    end
    initial begin
        repeat (4) @(posedge clk);
        rst_n = 1;
        repeat (20) @(posedge clk);
        phaseA = 1;
        issue(qldi_val(8'd0, 8'd3, 8'd1, 8'd0, 8'd2));
        issue(qldi_val(8'd1, 8'd1, 8'd2, 8'd5, 8'd0));
        issue(qsub(8'd2, 8'd0, 8'd1));
        issue(rotc(8'd3, 8'd0, 6'd1));
        issue(rotc(8'd4, 8'd1, 6'd5));
        issue(ld_word());
        repeat (4) @(posedge clk);
        phaseA = 0;
        check("A: 5 commits match VM values", a_idx == 5 && a_bad == 0);
        check("no fault before any REGEN", fault_bit === 1'b0);
        issue(qldi(8'd0));
        phaseB = 1;
        issue(regen(16'd6));   // 5 phase-A eligible ops + 1 QLDI
        repeat (4) @(posedge clk);
        phaseB = 0;
        if (REGEN_EN == 0) begin
            // hang detection: issue() raises FAIL on inst_done timeout
            check("off: fault latched, not silent", fault_bit === 1'b1);
            check("off: REGEN wrote no QR state", commits_b === 0);
            issue(qldi_val(8'd5, 8'd1, 8'd1, 8'd1, 8'd1));
            check("off: sticky, later ops still run", fault_bit === 1'b1);
        end else begin
            check("on: REGEN K=6 passes, no fault", fault_bit === 1'b0);
            check("on: REGEN committed both lanes", commits_b >= 2);
        end
        if (errors == 0) $display("spu13_core_regen_off_tb: PASS REGEN_EN=%0d", REGEN_EN);
        else $display("spu13_core_regen_off_tb: FAIL errors=%0d", errors);
        $finish;
    end
endmodule
