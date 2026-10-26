// spu13_core_regen_tb.v — Stage A REGEN core-integration smoke test
// (contract_regen_stageA_2026-08-20.md; extra auditor check beyond §4.1)
//
// Drives the full spu13_core with real instruction words: QLDI / LD /
// IROTC(disabled) eligibility counting, REGEN K validation, REGEN_PREC
// faulting, and counter clear semantics — including the E_REGEN three-layer
// agreement checks (eligible increments, ineligible does not, IROTC
// conditional on ENABLE_IROTC).
`timescale 1ns/1ps

module spu13_core_regen_tb;
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
        .ENABLE_IROTC(0)
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

    initial begin
        repeat (4) @(posedge clk);
        rst_n = 1;
        repeat (20) @(posedge clk);   // QR hydration walk before instructions

        // Core test 1: QLDI; QLDI; REGEN K=2 -> clean pass, counter cleared
        issue(qldi(8'd0));
        issue(qldi(8'd1));
        issue(regen(16'd2));
        check("C1: REGEN K=2 after 2 QLDI -> no REGEN_PREC fault", fault_bit === 1'b0);
        check("C1: counter cleared", count6 === 6'd0);

        // Core test 2: QLDI; REGEN K=2 -> REGEN_PREC fault, counter kept
        issue(qldi(8'd0));
        issue(regen(16'd2));
        check("C2: REGEN K=2 after 1 QLDI -> REGEN_PREC fault", fault_bit === 1'b1);
        check("C2: counter kept at 1", count6 === 6'd1);
        // clear the faulted counter before C3
        issue(regen(16'd1));

        // Core test 3: LD is NOT in E_REGEN -> does not increment; REGEN K=1
        // after [QLDI, LD] must pass (only QLDI counted)
        issue(qldi(8'd1));
        issue(ld_word());
        issue(regen(16'd1));
        check("C3: LD not counted (QLDI+LD, REGEN K=1 -> pass)", fault_bit === 1'b0);

        // Core test 4: IROTC disabled -> not eligible; REGEN K=1 after
        // [QLDI, IROTC] must pass (only QLDI counted)
        issue(qldi(8'd2));
        issue(irotc_word());
        issue(regen(16'd1));
        check("C4: IROTC (ENABLE_IROTC=0) not counted", fault_bit === 1'b0);

        // Core test 5: REGEN K=0 on empty counter -> idempotence
        issue(regen(16'd0));
        check("C5: REGEN K=0 -> clean pass-through (idempotence)", fault_bit === 1'b0);

        // ── Stage B: fixed-point chain recovery (whole-state) ──
        // program: QLDI QR0(1,2,3,4); QLDI QR1(1,0,0,0); ROTC QR0,QR0,1;
        //          QSUB QR0,QR0,QR1; REGEN K=4
        // exact: QR0 = (0,3,2,4), QR1 = (1,0,0,0)
        regen_dphi_cfg = 8'd0;
        issue(qldi(8'd0));                    // QR0 = (1,2,3,4)
        issue(qldi_val(8'd1, 8'd1, 8'd0, 8'd0, 8'd0));   // QR1 = (1,0,0,0)
        issue(rotc(8'd0, 8'd0, 6'd1));        // ROTC QR0,QR0,1 -> (1,3,2,4)
        issue(qsub(8'd0, 8'd0, 8'd1));        // QSUB QR0,QR0,QR1 -> (0,3,2,4)
        begin : stageb
            reg [3:0] l0, l1;
            reg signed [31:0] a0, b0, c0, d0, a1, b1, c1, d1;
            issue_regen_capture(16'd4, l0, l1, a0, b0, c0, d0, a1, b1, c1, d1);
            check("S1: REGEN recovers QR0 = (0,3,2,4) from the fixed-point chain",
                  l0 == 4'd0 && a0 == 32'd0 && b0 == 32'd3 && c0 == 32'd2 && d0 == 32'd4);
            check("S1: REGEN recovers QR1 = (1,0,0,0)",
                  l1 == 4'd1 && a1 == 32'd1 && b1 == 32'd0 && c1 == 32'd0 && d1 == 32'd0);
        end

        // ── Stage B: compensation exercised (dphi != 0) ──
        // same program with a per-op common-mode rotation; the trim must
        // restore the SAME exact state (experiment #3's law, in hardware)
        regen_dphi_cfg = 8'd100;
        issue(qldi(8'd0));
        issue(qldi_val(8'd1, 8'd1, 8'd0, 8'd0, 8'd0));
        issue(rotc(8'd0, 8'd0, 6'd1));
        issue(qsub(8'd0, 8'd0, 8'd1));
        begin : stageb_dphi
            reg [3:0] l0, l1;
            reg signed [31:0] a0, b0, c0, d0, a1, b1, c1, d1;
            issue_regen_capture(16'd4, l0, l1, a0, b0, c0, d0, a1, b1, c1, d1);
            check("S2: dphi=100 compensation recovers the same exact QR0",
                  l0 == 4'd0 && a0 == 32'd0 && b0 == 32'd3 && c0 == 32'd2 && d0 == 32'd4);
            check("S2: dphi=100 compensation recovers the same exact QR1",
                  l1 == 4'd1 && a1 == 32'd1 && b1 == 32'd0 && c1 == 32'd0 && d1 == 32'd0);
        end

        // ── Stage C cat 9: fault-then-clear (Stage-B chain preserved) ──
        // QLDI QR0(1,2,3,4); QLDI QR1(1,0,0,0); ROTC QR0,QR0,1; QSUB QR0,QR0,QR1
        // REGEN K=3 -> REGEN_PREC fault (counter kept at 4, chain preserved)
        // REGEN K=4 -> recovers (0,3,2,4) / (1,0,0,0) from the preserved chain
        regen_dphi_cfg = 8'd0;
        issue(qldi(8'd0));
        issue(qldi_val(8'd1, 8'd1, 8'd0, 8'd0, 8'd0));
        issue(rotc(8'd0, 8'd0, 6'd1));
        issue(qsub(8'd0, 8'd0, 8'd1));
        issue(regen(16'd3));   // fault: declared K=3 != counted 4
        check("S3a: REGEN K=3 faulted (counter kept at 4)",
              fault_bit === 1'b1);
        begin : stageb_fault
            reg [3:0] l0, l1;
            reg signed [31:0] a0, b0, c0, d0, a1, b1, c1, d1;
            issue_regen_capture(16'd4, l0, l1, a0, b0, c0, d0, a1, b1, c1, d1);
            check("S3: fault-then-clear: REGEN K=4 recovers the exact state",
                  l0 == 4'd0 && a0 == 32'd0 && b0 == 32'd3 && c0 == 32'd2 && d0 == 32'd4);
            check("S3: fault-then-clear: QR1 also recovered",
                  l1 == 4'd1 && a1 == 32'd1 && b1 == 32'd0 && c1 == 32'd0 && d1 == 32'd0);
        end

        if (errors == 0)
            $display("spu13_core_regen_tb: PASS");
        else
            $display("spu13_core_regen_tb: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule
