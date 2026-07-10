// spu13_core_irotc_opcode_tb.v — IROTC/LOAD2X/SCALE2 through the real core
//
// Copyright 2026 John Curley
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Core-level proof of the ENABLE_IROTC integration: decode → φ-plane
// typestate guards → engine → writeback into the core's own QR file,
// plus the tag transition algebra at every existing QR write site
// (ROTC thirds/bypass/octahedral classes, QSUB lattice join, QLDI raw
// load, SCALE2 recondition). Expected values derived from the
// exact-Fraction oracle (test_icosahedral_catalog.py), 2026-07-10 —
// same source the VM is trace-equivalent to and the engine TB's golden
// vectors are generated from.
`timescale 1ns/1ps

module spu13_core_irotc_opcode_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;
    wire inst_done;
    wire [15:0] rotc_debug_status;
    integer errors = 0;

    // typestate encodings (match core localparams)
    localparam [1:0] T_UN = 2'd0, T_FR = 2'd1, T_MA = 2'd2, T_CO = 2'd3;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(0),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .ENABLE_IROTC(1)
    ) uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(),
        .mem_burst_wr(), .mem_addr(),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(),
        .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(), .qr_commit_lane(),
        .qr_commit_A(), .qr_commit_B(),
        .qr_commit_C(), .qr_commit_D(),
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
        .rotc_debug_status(rotc_debug_status)
    );

    function [63:0] load2x;
        input [7:0] lane;
        input signed [7:0] a; input signed [7:0] b;
        input signed [7:0] c; input signed [7:0] d;
        begin
            load2x = {8'hD7, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0};
        end
    endfunction

    function [63:0] qldi;
        input [7:0] lane;
        input signed [7:0] a; input signed [7:0] b;
        input signed [7:0] c; input signed [7:0] d;
        begin
            qldi = {8'h1D, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0};
        end
    endfunction

    function [63:0] irotc;
        input [7:0] dst; input [7:0] src;
        input conj; input [5:0] idx;
        begin
            // sel in p1_a[6:0]: word[30] = conjugate flag, word[29:24] = idx
            irotc = {8'hD6, dst, src, 8'd0, 1'b0, conj, idx, 24'd0};
        end
    endfunction

    function [63:0] scale2;
        input [7:0] dst; input [7:0] src;
        begin
            scale2 = {8'hD8, dst, src, 40'd0};
        end
    endfunction

    function [63:0] qsub3;
        input [7:0] dst; input [7:0] lhs; input [3:0] rhs;
        begin
            qsub3 = {8'h1B, dst, lhs, 16'd0, 12'd0, rhs, 8'd0};
        end
    endfunction

    function [63:0] rotc;
        input [7:0] dst; input [7:0] src; input [5:0] angle;
        begin
            rotc = {8'h1C, dst, src, 8'd0, 2'b00, angle, 24'd0};
        end
    endfunction

    task issue;
        input [63:0] word;
        integer guard;
        begin
            @(posedge clk);
            inst_word <= word; inst_valid <= 1'b1;
            @(posedge clk);
            inst_valid <= 1'b0; inst_word <= 64'd0;
            guard = 0;
            while (!inst_done && guard < 200) begin
                @(posedge clk); guard = guard + 1;
            end
            @(posedge clk);
            if (guard >= 200) begin
                $display("FAIL: instruction timeout word=%h", word);
                errors = errors + 1;
            end
        end
    endtask

    // Check a lane's four Z[phi] pairs (a = low half, b = high half)
    task expect_phi;
        input [3:0] lane;
        input signed [31:0] aa; input signed [31:0] ab;
        input signed [31:0] ba; input signed [31:0] bb;
        input signed [31:0] ca; input signed [31:0] cb;
        input signed [31:0] da; input signed [31:0] db;
        input [255:0] label;
        begin
            if (uut.gen_qrf.u_qrf.u_regfile.reg_A[lane] !== {ab, aa} ||
                uut.gen_qrf.u_qrf.u_regfile.reg_B[lane] !== {bb, ba} ||
                uut.gen_qrf.u_qrf.u_regfile.reg_C[lane] !== {cb, ca} ||
                uut.gen_qrf.u_qrf.u_regfile.reg_D[lane] !== {db, da}) begin
                $display("FAIL %0s: QR%0d A=%h B=%h C=%h D=%h",
                         label, lane,
                         uut.gen_qrf.u_qrf.u_regfile.reg_A[lane],
                         uut.gen_qrf.u_qrf.u_regfile.reg_B[lane],
                         uut.gen_qrf.u_qrf.u_regfile.reg_C[lane],
                         uut.gen_qrf.u_qrf.u_regfile.reg_D[lane]);
                errors = errors + 1;
            end else
                $display("PASS %0s", label);
        end
    endtask

    task expect_tag;
        input [3:0] lane;
        input [1:0] tag;
        input [255:0] label;
        begin
            if (uut.qr_tags[lane] !== tag) begin
                $display("FAIL %0s: tag[QR%0d]=%0d expected %0d",
                         label, lane, uut.qr_tags[lane], tag);
                errors = errors + 1;
            end else
                $display("PASS %0s", label);
        end
    endtask

    // Issue a word expected to FAULT: debug bit15 set with the code in
    // [11:10]; destination lane and its tag bit-identically untouched.
    task expect_fault;
        input [63:0] word;
        input [1:0] code;
        input [3:0] dst;
        input [255:0] label;
        reg [255:0] hold;
        reg [1:0] tag_hold;
        begin
            hold = {uut.gen_qrf.u_qrf.u_regfile.reg_A[dst],
                    uut.gen_qrf.u_qrf.u_regfile.reg_B[dst],
                    uut.gen_qrf.u_qrf.u_regfile.reg_C[dst],
                    uut.gen_qrf.u_qrf.u_regfile.reg_D[dst]};
            tag_hold = uut.qr_tags[dst];
            issue(word);
            if (!rotc_debug_status[15] || rotc_debug_status[13:12] !== code) begin
                $display("FAIL %0s: status=%h expected fault code %0d",
                         label, rotc_debug_status, code);
                errors = errors + 1;
            end else if ({uut.gen_qrf.u_qrf.u_regfile.reg_A[dst],
                          uut.gen_qrf.u_qrf.u_regfile.reg_B[dst],
                          uut.gen_qrf.u_qrf.u_regfile.reg_C[dst],
                          uut.gen_qrf.u_qrf.u_regfile.reg_D[dst]} !== hold ||
                         uut.qr_tags[dst] !== tag_hold) begin
                $display("FAIL %0s: destination disturbed by fault", label);
                errors = errors + 1;
            end else
                $display("PASS %0s", label);
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        rst_n = 1;
        // VE hydration walks lanes 1-12 with init-port priority after
        // boot_done — wait for it, or it overwrites early instructions.
        wait (uut.gen_qrf.ve_qr_init_done === 1'b1);
        repeat (2) @(posedge clk);

        // ── LOAD2X: doubled load, FRESH ─────────────────────────────
        issue(load2x(8'd1, 0, 3, -6, 9));
        expect_phi(1, 0,0, 6,0, -12,0, 18,0, "LOAD2X doubles into QR1");
        expect_tag(1, T_FR, "LOAD2X sets FRESH");

        // ── IROTC main idx 36 (period-5, phi-arithmetic) ────────────
        // Oracle: A=(-3,6) B=(-12,9) C=(3,-15) D=(12,0)
        issue(irotc(8'd2, 8'd1, 1'b0, 6'd36));
        expect_phi(2, -3,6, -12,9, 3,-15, 12,0, "IROTC idx36 main bit-exact");
        expect_tag(2, T_MA, "IROTC main output is MAIN");

        // ── IROTC conjugate idx 36 from FRESH ───────────────────────
        // Oracle: A=(3,-6) B=(-3,-9) C=(-12,15) D=(12,0)
        issue(irotc(8'd3, 8'd1, 1'b1, 6'd36));
        expect_phi(3, 3,-6, -3,-9, -12,15, 12,0, "IROTC idx36 conj bit-exact");
        expect_tag(3, T_CO, "IROTC conj output is CONJ");

        // ── faults: BADIDX / UNTAGGED / CATMIX, destination pinned ──
        expect_fault(irotc(8'd4, 8'd1, 1'b0, 6'd60), 2'd1, 4'd4,
                     "BADIDX idx 60 faults, QR4 pinned");
        issue(qldi(8'd5, 1, 2, 3, 4));
        expect_tag(5, T_UN, "QLDI raw load clears tag");
        expect_fault(irotc(8'd4, 8'd5, 1'b0, 6'd0), 2'd2, 4'd4,
                     "UNTAGGED source faults, QR4 pinned");
        expect_fault(irotc(8'd4, 8'd2, 1'b1, 6'd3), 2'd3, 4'd4,
                     "CATMIX conj-on-MAIN faults, QR4 pinned");
        expect_fault(irotc(8'd4, 8'd3, 1'b0, 6'd3), 2'd3, 4'd4,
                     "CATMIX main-on-CONJ faults, QR4 pinned");

        // ── main-catalog chain step: idx 40 on the idx36 result ─────
        // Oracle: A=(-3,-9) B=(-12,15) C=(12,0) D=(3,-6)
        issue(irotc(8'd4, 8'd2, 1'b0, 6'd40));
        expect_phi(4, -3,-9, -12,15, 12,0, 3,-6, "chain idx40(idx36) bit-exact");
        expect_tag(4, T_MA, "chain stays MAIN");

        // ── ROTC tag classes on the shared register file ────────────
        issue(rotc(8'd5, 8'd2, 6'd1));       // thirds
        expect_tag(5, T_UN, "thirds ROTC clears to UNTAGGED");
        expect_fault(irotc(8'd6, 8'd5, 1'b0, 6'd0), 2'd2, 4'd6,
                     "IROTC after thirds faults UNTAGGED");
        issue(rotc(8'd5, 8'd2, 6'd21));      // A4 bypass (AB)(CD)
        expect_tag(5, T_MA, "A4 bypass ROTC preserves MAIN");
        issue(rotc(8'd5, 8'd2, 6'd26));      // octahedral, not in A5
        expect_tag(5, T_UN, "octahedral ROTC demotes MAIN to UNTAGGED");
        issue(rotc(8'd5, 8'd1, 6'd26));      // octahedral on FRESH
        expect_tag(5, T_FR, "octahedral ROTC passes FRESH through");

        // ── SCALE2 recondition: MAIN → FRESH → conjugate legal ──────
        // Oracle: 2*idx36 = A=(-6,12) B=(-24,18) C=(6,-30) D=(24,0)
        issue(scale2(8'd7, 8'd2));
        expect_phi(7, -6,12, -24,18, 6,-30, 24,0, "SCALE2 doubles MAIN data");
        expect_tag(7, T_FR, "SCALE2 reconditions to FRESH");
        // conj idx 3 on the reconditioned value:
        // Oracle: A=(12,9) B=(24,-18) C=(-21,24) D=(-15,-15)
        issue(irotc(8'd8, 8'd7, 1'b1, 6'd3));
        expect_phi(8, 12,9, 24,-18, -21,24, -15,-15,
                   "conj rotation after SCALE2 bit-exact");
        expect_tag(8, T_CO, "reconditioned catalog switch lands CONJ");

        // ── QSUB lattice join ───────────────────────────────────────
        issue(qsub3(8'd9, 8'd2, 4'd4));      // MAIN - MAIN
        expect_tag(9, T_MA, "QSUB MAIN-MAIN joins to MAIN");
        issue(qsub3(8'd9, 8'd2, 4'd3));      // MAIN - CONJ
        // Oracle: m36 - c36 = A=(-6,12) B=(-9,18) C=(15,-30) D=(0,0)
        expect_phi(9, -6,12, -9,18, 15,-30, 0,0, "QSUB values componentwise");
        expect_tag(9, T_UN, "QSUB MAIN-CONJ clears to UNTAGGED");

        if (errors == 0)
            $display("spu13_core_irotc_opcode_tb: PASS");
        else begin
            $display("spu13_core_irotc_opcode_tb: FAIL (%0d errors)", errors);
            $display("FAIL");
        end
        $finish;
    end
endmodule
