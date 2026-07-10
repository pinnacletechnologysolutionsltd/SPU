`timescale 1ns/1ps

module spu13_core_rotc_opcode_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;
    wire inst_done;

    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    wire [15:0] rotc_debug_status;
    integer errors = 0;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(0),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0)
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
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
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

    function [63:0] qldi;
        input [7:0] lane;
        input signed [7:0] a;
        input signed [7:0] b;
        input signed [7:0] c;
        input signed [7:0] d;
        begin
            qldi = {8'h1D, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0};
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

    task expect_lane;
        input [3:0] lane;
        input signed [31:0] a;
        input signed [31:0] b;
        input signed [31:0] c;
        input signed [31:0] d;
        reg signed [31:0] got_a, got_b, got_c, got_d;
        begin
            got_a = uut.gen_qrf.u_qrf.u_regfile.reg_A[lane][31:0];
            got_b = uut.gen_qrf.u_qrf.u_regfile.reg_B[lane][31:0];
            got_c = uut.gen_qrf.u_qrf.u_regfile.reg_C[lane][31:0];
            got_d = uut.gen_qrf.u_qrf.u_regfile.reg_D[lane][31:0];
            if (got_a !== a || got_b !== b || got_c !== c || got_d !== d) begin
                $display("FAIL: QR%0d got (%0d,%0d,%0d,%0d), expected (%0d,%0d,%0d,%0d)",
                         lane, got_a, got_b, got_c, got_d, a, b, c, d);
                errors = errors + 1;
            end else begin
                $display("PASS: QR%0d = (%0d,%0d,%0d,%0d)", lane, a, b, c, d);
            end
        end
    endtask

    initial begin
        $dumpfile("build/spu13_core_rotc_opcode_tb.vcd");
        $dumpvars(0, spu13_core_rotc_opcode_tb);

        #20 rst_n = 1;
        repeat (20) @(posedge clk);

        issue(qldi(8'd0, 8'sd1, 8'sd2, 8'sd3, 8'sd4));
        expect_lane(4'd0, 32'sd1, 32'sd2, 32'sd3, 32'sd4);

        issue(rotc(8'd6, 8'd0, 6'd0));
        expect_lane(4'd6, 32'sd1, 32'sd2, 32'sd3, 32'sd4);

        issue(rotc(8'd7, 8'd0, 6'd1));
        expect_lane(4'd7, 32'sd1, 32'sd3, 32'sd2, 32'sd4);

        issue(rotc(8'd8, 8'd0, 6'd2));
        expect_lane(4'd8, 32'sd1, 32'sd4, 32'sd2, 32'sd3);

        issue(rotc(8'd9, 8'd0, 6'd3));
        expect_lane(4'd9, 32'sd1, 32'sd4, 32'sd3, 32'sd2);

        issue(rotc(8'd10, 8'd0, 6'd4));
        expect_lane(4'd10, 32'sd1, 32'sd2, 32'sd4, 32'sd3);

        issue(rotc(8'd11, 8'd0, 6'd5));
        expect_lane(4'd11, 32'sd1, 32'sd3, 32'sd4, 32'sd2);

        // ── Angles 6-11: axis-permutation conjugates ─────────────────
        // These route through u_perm_fwd → rotor → u_perm_inv in
        // spu13_core.v (invariant axis B for 6-7, C for 8-9, D for
        // 10-11), so unlike 0-5 they rewrite ALL FOUR components.
        // Source components are all multiples of 3 so every thirds
        // division is exact (VM rounds, RTL div3 truncates — they only
        // provably agree when the division is exact; same restriction
        // the 0-5 canonical vector already obeys). Expected values are
        // VM/exact-Fraction oracle outputs (test_rotc_vm_rtl_trace.py
        // generates the same numbers independently).
        issue(qldi(8'd2, 8'sd3, -8'sd6, 8'sd9, -8'sd12));
        expect_lane(4'd2, 32'sd3, -32'sd6, 32'sd9, -32'sd12);

        issue(rotc(8'd3, 8'd2, 6'd6));
        expect_lane(4'd3, 32'sd12, -32'sd6, -32'sd3, -32'sd9);

        issue(rotc(8'd4, 8'd2, 6'd7));
        expect_lane(4'd4, -32'sd9, -32'sd6, 32'sd12, -32'sd3);

        issue(rotc(8'd5, 8'd2, 6'd8));
        expect_lane(4'd5, -32'sd13, -32'sd4, 32'sd9, 32'sd2);

        issue(rotc(8'd3, 8'd2, 6'd9));
        expect_lane(4'd3, -32'sd4, 32'sd2, 32'sd9, -32'sd13);

        issue(rotc(8'd4, 8'd2, 6'd10));
        expect_lane(4'd4, -32'sd5, 32'sd1, 32'sd10, -32'sd12);

        issue(rotc(8'd5, 8'd2, 6'd11));
        expect_lane(4'd5, 32'sd1, 32'sd10, -32'sd5, -32'sd12);

        // Inverse-pair closure through the real core: angle 7 undoes
        // angle 6 (thirds conjugates about B are mutual inverses).
        issue(rotc(8'd3, 8'd2, 6'd6));
        issue(rotc(8'd3, 8'd3, 6'd7));
        expect_lane(4'd3, 32'sd3, -32'sd6, 32'sd9, -32'sd12);

        // ── Angles 12-14: Tranche 1 missing thirds conjugates ────────
        // Source is (3,-6,9,-12) loaded at QR2.
        // Angle 12 (180°@B): self-inverse, period 2.
        issue(rotc(8'd3, 8'd2, 6'd12));
        expect_lane(4'd3, -32'sd3, -32'sd6, -32'sd9, 32'sd12);

        // Angle 13 (240°@C): inverse of angle 9.
        issue(rotc(8'd4, 8'd2, 6'd13));
        expect_lane(4'd4, 32'sd2, -32'sd13, 32'sd9, -32'sd4);

        // Angle 14 (60°@D): inverse of angle 10.
        issue(rotc(8'd5, 8'd2, 6'd14));
        expect_lane(4'd5, 32'sd10, -32'sd5, 32'sd1, -32'sd12);

        // Inverse-pair closure: angle 9 then 13 = identity.
        issue(rotc(8'd3, 8'd2, 6'd9));
        issue(rotc(8'd3, 8'd3, 6'd13));
        expect_lane(4'd3, 32'sd3, -32'sd6, 32'sd9, -32'sd12);

        // Inverse-pair closure: angle 10 then 14 = identity.
        issue(rotc(8'd3, 8'd2, 6'd10));
        issue(rotc(8'd3, 8'd3, 6'd14));
        expect_lane(4'd3, 32'sd3, -32'sd6, 32'sd9, -32'sd12);

        // Angle 12 self-inverse round trip.
        issue(rotc(8'd3, 8'd2, 6'd12));
        issue(rotc(8'd3, 8'd3, 6'd12));
        expect_lane(4'd3, 32'sd3, -32'sd6, 32'sd9, -32'sd12);

        // ── Angles 15-23: Tranche 2 A₄ pure permutations ─────────────
        // Source (1,2,3,4) in QR0 — pure coordinate swaps, no /3.
        // Bypass 3-cycles (15-20): perm_sel + bypass_p5/bypass_p5_inv.
        issue(rotc(8'd3, 8'd0, 6'd15));
        expect_lane(4'd3, 32'sd4, 32'sd2, 32'sd1, 32'sd3);

        issue(rotc(8'd4, 8'd0, 6'd16));
        expect_lane(4'd4, 32'sd3, 32'sd2, 32'sd4, 32'sd1);

        issue(rotc(8'd5, 8'd0, 6'd17));
        expect_lane(4'd5, 32'sd4, 32'sd1, 32'sd3, 32'sd2);

        issue(rotc(8'd6, 8'd0, 6'd18));
        expect_lane(4'd6, 32'sd2, 32'sd4, 32'sd3, 32'sd1);

        issue(rotc(8'd7, 8'd0, 6'd19));
        expect_lane(4'd7, 32'sd3, 32'sd1, 32'sd2, 32'sd4);

        issue(rotc(8'd8, 8'd0, 6'd20));
        expect_lane(4'd8, 32'sd2, 32'sd3, 32'sd1, 32'sd4);

        // Double transpositions (21-23): direct wire swaps.
        issue(rotc(8'd9, 8'd0, 6'd21));
        expect_lane(4'd9, 32'sd2, 32'sd1, 32'sd4, 32'sd3);

        issue(rotc(8'd10, 8'd0, 6'd22));
        expect_lane(4'd10, 32'sd3, 32'sd4, 32'sd1, 32'sd2);

        issue(rotc(8'd11, 8'd0, 6'd23));
        expect_lane(4'd11, 32'sd4, 32'sd3, 32'sd2, 32'sd1);

        // Inverse-pair closure: angle 15 then 16 = identity.
        issue(rotc(8'd3, 8'd0, 6'd15));
        issue(rotc(8'd3, 8'd3, 6'd16));
        expect_lane(4'd3, 32'sd1, 32'sd2, 32'sd3, 32'sd4);

        // ── Angles 24-35: Tranche 3 octahedral group ─────────────────
        // Integer 3×3 matrices on BCD, entries 0,±1 — zero multiplies.
        // Self-inverse (period 2): 24,25,28,31,32,34
        // Inverse pairs (period 4): 26↔27, 29↔30, 33↔35
        // NOTE: octahedral rotations recompute A = -(B+C+D). Self-inverse
        // closure only holds when input has zero-sum (A+B+C+D=0).
        // Test 1: direct application on (1,2,3,4) in QR0 (non-zero-sum).
        issue(rotc(8'd3, 8'd0, 6'd24));
        expect_lane(4'd3, 32'sd9, -32'sd2, -32'sd4, -32'sd3);

        // Test 2: self-inverse on (-6,1,2,3) sum=0.
        issue(qldi(8'd2, -8'sd6, 8'sd1, 8'sd2, 8'sd3));
        expect_lane(4'd2, -32'sd6, 32'sd1, 32'sd2, 32'sd3);

        issue(rotc(8'd4, 8'd2, 6'd24));
        expect_lane(4'd4, 32'sd6, -32'sd1, -32'sd3, -32'sd2);

        issue(rotc(8'd4, 8'd4, 6'd24));
        expect_lane(4'd4, -32'sd6, 32'sd1, 32'sd2, 32'sd3);

        // Period-4 inverse pair 33↔35 on (-6,1,2,3) sum=0:
        //  33: (-6,1,2,3) → (-3,6,-1,-2) → 35: → (-6,1,2,3)
        issue(rotc(8'd4, 8'd2, 6'd33));
        expect_lane(4'd4, -32'sd3, 32'sd6, -32'sd1, -32'sd2);

        issue(rotc(8'd4, 8'd4, 6'd35));
        expect_lane(4'd4, -32'sd6, 32'sd1, 32'sd2, 32'sd3);

        // ── Bad-angle fault: manifold must NOT be corrupted ──────────
        // Angle 36 is the first angle past ROTC_MAX_VERIFIED_ANGLE (=35).
        // Load lane 12 with known poison values, issue ROTC with angle 36,
        // require the lane untouched plus BAD_ANGLE fault flag set.
        issue(qldi(8'd12, 8'sd99, 8'sd98, 8'sd97, 8'sd96));
        expect_lane(4'd12, 32'sd99, 32'sd98, 32'sd97, 32'sd96);

        issue(rotc(8'd12, 8'd0, 6'd36));
        expect_lane(4'd12, 32'sd99, 32'sd98, 32'sd97, 32'sd96);
        if (rotc_debug_status[15] !== 1'b1) begin
            $display("FAIL: angle 36 did not set BAD_ANGLE fault (status=%h)",
                      rotc_debug_status);
            errors = errors + 1;
        end else begin
            $display("PASS: angle 36 faulted (BAD_ANGLE) without touching QR12");
        end

        // Angle 63 (top of the 6-bit field) must fault the same way.
        issue(qldi(8'd1, 8'sd50, 8'sd51, 8'sd52, 8'sd53));
        expect_lane(4'd1, 32'sd50, 32'sd51, 32'sd52, 32'sd53);

        issue(rotc(8'd1, 8'd1, 6'd63));
        expect_lane(4'd1, 32'sd50, 32'sd51, 32'sd52, 32'sd53);
        if (rotc_debug_status[15] !== 1'b1) begin
            $display("FAIL: angle 63 did not set BAD_ANGLE fault (status=%h)",
                      rotc_debug_status);
            errors = errors + 1;
        end else begin
            $display("PASS: angle 63 faulted (BAD_ANGLE) without touching QR1");
        end

        if (errors == 0)
            $display("spu13_core_rotc_opcode_tb: PASS");
        else
            $display("spu13_core_rotc_opcode_tb: FAIL (%0d errors)", errors);

        #20;
        $finish;
    end
endmodule

module MULT27X36(
    output [62:0] DOUT,
    input  [26:0] A,
    input  [35:0] B,
    input  [25:0] D,
    input  [1:0]  CLK,
    input  [1:0]  CE,
    input  [1:0]  RESET,
    input         PSEL,
    input         PADDSUB
);
    assign DOUT = $signed(A) * $signed(B);
endmodule

module MULT18X18 #(
    parameter ASIGN = 1,
    parameter BSIGN = 1
) (
    input  [17:0] A,
    input  [17:0] B,
    output [35:0] P
);
    assign P = (ASIGN || BSIGN) ? ($signed(A) * $signed(B)) : (A * B);
endmodule

module SDPB #(
    parameter BIT_WIDTH_0 = 16,
    parameter BIT_WIDTH_1 = 16
) (
    input                         CLKA,
    input                         CEA,
    input                         RESETA,
    input  [13:0]                 ADA,
    input  [BIT_WIDTH_0-1:0]      DIA,
    input                         CLKB,
    input                         CEB,
    input                         RESETB,
    input  [13:0]                 ADB,
    output [BIT_WIDTH_1-1:0]      DOB
);
    assign DOB = {BIT_WIDTH_1{1'b0}};
endmodule
