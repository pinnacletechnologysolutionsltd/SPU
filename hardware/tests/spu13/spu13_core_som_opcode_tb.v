`timescale 1ns/1ps

module spu13_core_som_opcode_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;
    wire inst_done;
    wire hex_valid;
    wire [15:0] hex_q;
    wire [15:0] hex_r;

    wire axiomatic_fault;
    wire [1:0] fault_type;
    wire [15:0] fault_count;
    reg [15:0] phinary_level = 16'd0;  // bits [3:2] = axiomatic level

    wire mem_burst_rd;
    wire mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    integer errors = 0;
    reg issue_hex_valid = 1'b0;
    reg [15:0] issue_hex_q = 16'd0;
    reg [15:0] issue_hex_r = 16'd0;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(0),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(1)
    ) uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(phinary_level),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b0), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr), .mem_addr(mem_addr),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(1'b0),
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
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(axiomatic_fault),
        .fault_type(fault_type),
        .fault_count(fault_count),
        .rns_error(),
        .ecc_single_err(),
        .ecc_double_err()
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
        input integer max_cycles;
        integer guard;
        begin
            @(posedge clk);
            inst_word <= word;
            inst_valid <= 1'b1;
            guard = 0;
            while (!inst_done && guard < max_cycles) begin
                @(posedge clk);
                guard = guard + 1;
            end
            issue_hex_valid = hex_valid;
            issue_hex_q = hex_q;
            issue_hex_r = hex_r;
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
            if (guard >= max_cycles) begin
                $display("FAIL: instruction timeout word=%h", word);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("build/spu13_core_som_opcode_tb.vcd");
        $dumpvars(0, spu13_core_som_opcode_tb);

        #20 rst_n = 1;
        repeat (2) @(posedge clk);

        $display("TEST 1: QLDI source QR0 = (2,1,0,0)");
        issue(pack(8'h1D, 8'd0, 8'd0, 16'h0201, 16'h0000), 40);
        #1;

        if (uut.gen_qrf.u_qrf.u_regfile.reg_A[0][31:0] !== 32'sd2 ||
            uut.gen_qrf.u_qrf.u_regfile.reg_B[0][31:0] !== 32'sd1 ||
            uut.gen_qrf.u_qrf.u_regfile.reg_C[0][31:0] !== 32'sd0 ||
            uut.gen_qrf.u_qrf.u_regfile.reg_D[0][31:0] !== 32'sd0) begin
            $display("FAIL: QLDI source QR0 A=%0d B=%0d C=%0d D=%0d",
                     uut.gen_qrf.u_qrf.u_regfile.reg_A[0][31:0],
                     uut.gen_qrf.u_qrf.u_regfile.reg_B[0][31:0],
                     uut.gen_qrf.u_qrf.u_regfile.reg_C[0][31:0],
                     uut.gen_qrf.u_qrf.u_regfile.reg_D[0][31:0]);
            errors = errors + 1;
        end else begin
            $display("PASS: QLDI loaded SOM feature vector");
        end

        $display("TEST 2: SOM_CLASSIFY waits for reduced label");
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);

        if (issue_hex_valid !== 1'b1) begin
            $display("FAIL: SOM_CLASSIFY did not pulse hex_valid at inst_done");
            errors = errors + 1;
        end

        if (issue_hex_q !== 16'd1 || issue_hex_r !== 16'd0) begin
            $display("FAIL: SOM telemetry hex_q=%h hex_r=%h, expected 0001 0000",
                     issue_hex_q, issue_hex_r);
            errors = errors + 1;
        end else begin
            $display("PASS: SOM_CLASSIFY emitted label=1 ambiguous=0");
        end

        repeat (20) @(posedge clk);
        if (hex_valid === 1'b1 || inst_done === 1'b1) begin
            $display("FAIL: SOM_CLASSIFY retriggered after completion");
            errors = errors + 1;
        end else begin
            $display("PASS: SOM_CLASSIFY start was a single pulse");
        end

        // ── Axiomatic Gatekeeper Tests ─────────────────────────────
        // Level 0 (RCA₀): small integer features — no fault expected
        $display("TEST 3: RCA₀ level — small integer feature, expect no fault");
        phinary_level = 16'h0000;  // axiomatic_level = 00 (RCA₀)
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);

        if (axiomatic_fault !== 1'b0) begin
            $display("FAIL: RCA₀ spurious fault type=%b count=%d", fault_type, fault_count);
            errors = errors + 1;
        end else begin
            $display("PASS: RCA₀ gatekeeper silent (no overflow, no fractional bits)");
        end

        // Level 1 (WKL₀): same as RCA₀ for small integers
        $display("TEST 4: WKL₀ level — same feature, expect no fault");
        phinary_level = 16'h0004;  // axiomatic_level = 01 (WKL₀)
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);

        if (axiomatic_fault !== 1'b0) begin
            $display("FAIL: WKL₀ spurious fault type=%b", fault_type);
            errors = errors + 1;
        end else begin
            $display("PASS: WKL₀ gatekeeper silent");
        end

        // Level 3 (OFF): gatekeeper disabled
        $display("TEST 5: OFF level — gatekeeper disabled, expect no fault");
        phinary_level = 16'h000C;  // axiomatic_level = 11 (OFF)
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);

        if (axiomatic_fault !== 1'b0) begin
            $display("FAIL: OFF gatekeeper fired spuriously");
            errors = errors + 1;
        end else begin
            $display("PASS: OFF gatekeeper silent");
        end

        // Verify fault_count stayed at zero across all levels
        if (fault_count !== 16'd0) begin
            $display("FAIL: fault_count=%d (expected 0)", fault_count);
            errors = errors + 1;
        end else begin
            $display("PASS: fault_count=0 across all levels");
        end

        if (errors == 0)
            $display("spu13_core_som_opcode_tb: PASS");
        else
            $display("spu13_core_som_opcode_tb: FAIL (%0d errors)", errors);

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
