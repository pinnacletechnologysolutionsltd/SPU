`timescale 1ns/1ps

module spu13_som_trace_tb;
    reg clk = 0; always #5 clk = ~clk;
    reg rst_n = 0;
    reg inst_valid = 0;
    reg [63:0] inst_word = 0;
    wire inst_done, hex_valid;
    wire [15:0] hex_q, hex_r;
    wire axiomatic_fault;
    wire [1:0] fault_type;
    wire [15:0] fault_count;
    reg [15:0] phinary_level = 0;
    wire mem_burst_rd, mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    integer errors = 0;

    spu13_core #(.DEVICE("SIM"),.ENABLE_RPLU(0),.ENABLE_LATTICE(0),.ENABLE_MATH(0),.ENABLE_SEQUENCER(0),.ENABLE_CORE_SOM(1))
    uut(.clk(clk),.rst_n(rst_n),.phi_8(0),.phi_13(0),.phi_21(0),
        .dec_fast_cfg_wr_en(0),.dec_fast_cfg_sel(0),.dec_fast_cfg_material(0),.dec_fast_cfg_addr(0),.dec_fast_cfg_data(0),.phinary_cfg(phinary_level),
        .prime_data(0),.prime_addr(0),.prime_we(0),.boot_done(0),.pell_data(0),.pell_addr(0),.pell_we(0),
        .manual_rotor_en(0),.manual_rotor_data(0),.mem_ready(1),.mem_burst_rd(mem_burst_rd),.mem_burst_wr(mem_burst_wr),.mem_addr(mem_addr),
        .mem_rd_manifold(0),.mem_wr_manifold(mem_wr_manifold),.mem_burst_done(0),
        .artery_wr_en(),.artery_wr_data(),.current_axis_ptr(),.current_axis_data(),
        .inst_valid(inst_valid),.inst_word(inst_word),.inst_done(inst_done),
        .ratio_cmp_res(),.ratio_cmp_valid(),.manifold_out(),.bloom_complete(),.scale_table_out(),.scale_overflow_out(),.is_janus_point(),
        .audio_mode(),.gasket_sum_out(),.quadrance_out(),.cycle_wrap(),
        .rplu_dissoc_out(),.rplu_dissoc_mask_out(),.rplu_addr_out(),
        .i2s_bclk(),.i2s_lrclk(),.i2s_dout(),.laminar_flow_index_out(),.thermal_pressure_out(),
        .hex_valid(hex_valid),.hex_q(hex_q),.hex_r(hex_r),.audio_p_out(),.audio_q_out(),
        .axiomatic_fault(axiomatic_fault),.fault_type(fault_type),.fault_count(fault_count));

    function [63:0] pack;
        input [7:0] op, r1, r2; input [15:0] a, b;
        begin pack = {op, r1, r2, a, b, 8'd0}; end
    endfunction

    task issue;
        input [63:0] w; input integer maxc; integer g;
        begin
            @(posedge clk); inst_word <= w; inst_valid <= 1; g = 0;
            while (!inst_done && g < maxc) begin @(posedge clk); g = g + 1; end
            inst_valid <= 0; inst_word <= 0;
            if (g >= maxc) begin $display("FAIL: timeout %h", w); errors = errors + 1; end
        end
    endtask

    // Load feature into QR0, run SOM_CLASSIFY on QR0, check result
    task test_som;
        input [7:0] tnum;
        input [15:0] qldi_a, qldi_b;
        input [15:0] exp_q, exp_r;
        begin
            $display("TEST %0d: QLDI QR0, p1a=%h p1b=%h  expect label=%0d amb=%0d",
                     tnum, qldi_a, qldi_b, exp_q, exp_r[0]);
            issue(pack(8'h1D, 8'd0, 8'd0, qldi_a, qldi_b), 40);
            repeat (2) @(posedge clk);  // let QLDI settle
            issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);
            if (hex_valid !== 1'b1) begin
                $display("  FAIL: no hex_valid"); errors = errors + 1;
            end else if (hex_q !== exp_q || hex_r !== exp_r) begin
                $display("  FAIL: hex_q=%h hex_r=%h  expected %h %h", hex_q, hex_r, exp_q, exp_r);
                errors = errors + 1;
            end else $display("  PASS: label=%0d ambiguous=%0d", hex_q, hex_r[0]);
            repeat (10) @(posedge clk); // gap between tests: let FSM fully reset
        end
    endtask

    initial begin
        $dumpfile("build/spu13_som_trace_tb.vcd");
        $dumpvars(0, spu13_som_trace_tb);
        #20 rst_n = 1; repeat (2) @(posedge clk);

        $display("=== SOM VM↔RTL Trace — 6 vectors (all via QR0) ===");

        test_som(1, 16'h0201, 16'h0000, 16'd1, 16'd0);   // (2,1,0,0) → label=1
        test_som(2, 16'h0000, 16'h0200, 16'd2, 16'd0);   // (0,0,2,0) → label=2
        test_som(3, 16'hFE00, 16'h0000, 16'd2, 16'd0);   // (-2,0,0,0) → label=2
        test_som(4, 16'h00FE, 16'h0000, 16'd3, 16'd0);   // (0,-2,0,0) → label=3
        test_som(5, 16'h0000, 16'h0000, 16'd0, 16'd0);   // (0,0,0,0) → label=0
        test_som(6, 16'h0100, 16'h0000, 16'd0, 16'd1);   // (1,0,0,0) → label=0 amb

        // Gatekeeper tests
        issue(pack(8'h1D, 8'd0, 8'd0, 16'h0100, 16'h0000), 40);
        repeat (1) @(posedge clk);

        $display("TEST 7: RCA0 gatekeeper — expect silent");
        phinary_level = 16'h0000;
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);
        if (axiomatic_fault) begin
            $display("  FAIL: spurious fault type=%b", fault_type); errors = errors + 1;
        end else $display("  PASS: silent");

        $display("TEST 8: WKL0 gatekeeper — expect silent");
        phinary_level = 16'h0004;
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);
        if (axiomatic_fault) begin
            $display("  FAIL: spurious fault"); errors = errors + 1;
        end else $display("  PASS: silent");

        $display("TEST 9: OFF gatekeeper — expect silent");
        phinary_level = 16'h000C;
        issue(pack(8'h2A, 8'd0, 8'd0, 16'd0, 16'd0), 260);
        if (axiomatic_fault) begin
            $display("  FAIL: spurious fault"); errors = errors + 1;
        end else $display("  PASS: silent");

        $display("");
        if (errors == 0) $display("spu13_som_trace_tb: ALL 9 TESTS PASSED");
        else $display("spu13_som_trace_tb: FAILED (%0d errors)", errors);
        #20 $finish;
    end
endmodule

module MULT27X36(output [62:0] DOUT, input [26:0] A, input [35:0] B, input [25:0] D, input [1:0] CLK, CE, RESET, input PSEL, PADDSUB);
    assign DOUT = $signed(A) * $signed(B);
endmodule
module MULT18X18 #(parameter ASIGN=1, BSIGN=1) (input [17:0] A, B, output [35:0] P);
    assign P = (ASIGN || BSIGN) ? ($signed(A) * $signed(B)) : (A * B);
endmodule
module SDPB #(parameter BIT_WIDTH_0=16, BIT_WIDTH_1=16) (input CLKA, CEA, RESETA, input [13:0] ADA, input [BIT_WIDTH_0-1:0] DIA, input CLKB, CEB, RESETB, input [13:0] ADB, output [BIT_WIDTH_1-1:0] DOB);
    assign DOB = {BIT_WIDTH_1{1'b0}};
endmodule
