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
        .rns_error(), .ecc_single_err(), .ecc_double_err()
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
