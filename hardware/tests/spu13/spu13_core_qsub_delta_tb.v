`timescale 1ns/1ps

module spu13_core_qsub_delta_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;
    wire inst_done;

    wire mem_burst_rd;
    wire mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    reg [3:0] seen_qr_commit_lane;
    reg [63:0] seen_qr_commit_A, seen_qr_commit_B;
    reg [63:0] seen_qr_commit_C, seen_qr_commit_D;
    integer errors = 0;

    always @(posedge clk) begin
        if (qr_commit_valid) begin
            seen_qr_commit_lane <= qr_commit_lane;
            seen_qr_commit_A <= qr_commit_A;
            seen_qr_commit_B <= qr_commit_B;
            seen_qr_commit_C <= qr_commit_C;
            seen_qr_commit_D <= qr_commit_D;
        end
    end

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0)
    ) uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b0), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr), .mem_addr(mem_addr),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(mem_wr_manifold),
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
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out()
    );

    function [63:0] pack;
        input [7:0] op;
        input [7:0] r1;
        input [7:0] r2;
        input [15:0] p1_a;
        input [15:0] p1_b;
        begin
            pack = {op, r1, r2, p1_a, p1_b, 8'd0};
        end
    endfunction

    task issue;
        input [63:0] word;
        integer guard;
        begin
            @(posedge clk);
            inst_word <= word;
            inst_valid <= 1'b1;
            guard = 0;
            while (!inst_done && guard < 40) begin
                @(posedge clk);
                guard = guard + 1;
            end
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
            @(posedge clk);
            #1;
            if (guard >= 40) begin
                $display("FAIL: instruction timeout word=%h", word);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("build/spu13_core_qsub_delta_tb.vcd");
        $dumpvars(0, spu13_core_qsub_delta_tb);

        #20 rst_n = 1;
        repeat (2) @(posedge clk);

        $display("TEST 1: live-core QLDI/QSUB");
        issue(pack(8'h1D, 8'd1, 8'd0, 16'h0A14, 16'h1E28)); // QR1=(10,20,30,40)
        if (seen_qr_commit_lane !== 4'd1 ||
            seen_qr_commit_A !== 64'd10 || seen_qr_commit_B !== 64'd20 ||
            seen_qr_commit_C !== 64'd30 || seen_qr_commit_D !== 64'd40) begin
            $display("FAIL: QLDI telemetry lane=%0d A=%0d B=%0d C=%0d D=%0d",
                     seen_qr_commit_lane, seen_qr_commit_A, seen_qr_commit_B,
                     seen_qr_commit_C, seen_qr_commit_D);
            errors = errors + 1;
        end else begin
            $display("PASS: QLDI telemetry reports QR1=(10,20,30,40)");
        end
        issue(pack(8'h1D, 8'd2, 8'd0, 16'h0102, 16'h0304)); // QR2=(1,2,3,4)
        issue(pack(8'h1B, 8'd3, 8'd1, 16'h0000, 16'h0002)); // QR3=QR1-QR2

        if (uut.gen_qrf.u_qrf.reg_A[3][31:0] !== 32'sd9 ||
            uut.gen_qrf.u_qrf.reg_B[3][31:0] !== 32'sd18 ||
            uut.gen_qrf.u_qrf.reg_C[3][31:0] !== 32'sd27 ||
            uut.gen_qrf.u_qrf.reg_D[3][31:0] !== 32'sd36) begin
            $display("FAIL: QSUB result A=%0d B=%0d C=%0d D=%0d",
                     uut.gen_qrf.u_qrf.reg_A[3][31:0],
                     uut.gen_qrf.u_qrf.reg_B[3][31:0],
                     uut.gen_qrf.u_qrf.reg_C[3][31:0],
                     uut.gen_qrf.u_qrf.reg_D[3][31:0]);
            errors = errors + 1;
        end else begin
            $display("PASS: QSUB QR3 = QR1 - QR2");
        end

        $display("TEST 2: live-core DELTA");
        issue(pack(8'h1E, 8'd4, 8'd10, 16'd3, 16'd4));

        if (uut.gen_qrf.u_qrf.reg_A[4][31:0] !== 32'sd7 ||
            uut.gen_qrf.u_qrf.reg_B[4][31:0] !== 32'sd0 ||
            uut.gen_qrf.u_qrf.reg_C[4][31:0] !== 32'sd10 ||
            uut.gen_qrf.u_qrf.reg_D[4][31:0] !== 32'sd0) begin
            $display("FAIL: DELTA result A=%0d B=%0d C=%0d D=%0d",
                     uut.gen_qrf.u_qrf.reg_A[4][31:0],
                     uut.gen_qrf.u_qrf.reg_B[4][31:0],
                     uut.gen_qrf.u_qrf.reg_C[4][31:0],
                     uut.gen_qrf.u_qrf.reg_D[4][31:0]);
            errors = errors + 1;
        end else begin
            $display("PASS: DELTA QR4 = (7,0,10,0)");
        end

        if (errors == 0)
            $display("spu13_core_qsub_delta_tb: PASS");
        else
            $display("spu13_core_qsub_delta_tb: FAIL (%0d errors)", errors);

        #20;
        $finish;
    end
endmodule

// Local simulation stubs for unused Gowin primitives referenced by wrapper
// modules that are parsed while elaborating spu13_core with DEVICE="SIM".
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
