// spu_twin_regfile_tb.v — Testbench for twin-register file + RAU
// Verifies register read/write, PHSLK cross-multiplication, RAU ops.

`timescale 1ns/1ps

`include "spu_isa_defines.vh"

module spu_twin_regfile_tb;

    reg clk, rst_n;
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end

    // ── Register file signals ──
    reg  [ 4:0] raddrA, raddrB, waddr;
    reg         rselA_O, rselB_O, wren, wsel_O;
    reg  [63:0] wdata;
    wire [63:0] rdataA, rdataB;

    reg         flags_update, chord_in_update, quad_out_update;
    reg  [63:0] flags_in, chord_in_data, quad_out_data;
    reg         spu4_mode;

    // ── RAU signals ──
    reg  [63:0] rau_opA_O, rau_opB_C, rau_opA_extra;
    reg  [ 3:0] rau_op;
    wire [63:0] rau_result;
    wire        rau_coherent, rau_zero, rau_sign;

    spu_twin_regfile u_regfile (
        .clk(clk), .rst_n(rst_n),
        .raddrA(raddrA), .rselA_O(rselA_O), .rdataA(rdataA),
        .raddrB(raddrB), .rselB_O(rselB_O), .rdataB(rdataB),
        .wren(wren), .waddr(waddr), .wsel_O(wsel_O), .wdata(wdata),
        .flags_update(flags_update), .flags_in(flags_in),
        .chord_in_update(chord_in_update), .chord_in_data(chord_in_data),
        .quad_out_update(quad_out_update), .quad_out_data(quad_out_data),
        .spu4_mode(spu4_mode)
    );

    spu_rau u_rau (
        .opA_O(rau_opA_O),
        .opB_C(rau_opB_C),
        .opA_extra(rau_opA_extra),
        .rau_op(rau_op),
        .result(rau_result),
        .coherent(rau_coherent),
        .result_zero(rau_zero),
        .result_sign(rau_sign)
    );

    integer errors;
    reg [63:0] expected;

    task check;
        input [63:0] got;
        input [63:0] want;
        input [200:0] desc;
        if (got !== want) begin
            $display("FAIL: %s: got 0x%h, expected 0x%h", desc, got, want);
            errors = errors + 1;
        end else begin
            $display("PASS: %s", desc);
        end
    endtask

    initial begin
        errors = 0;
        rst_n = 0; raddrA = 0; raddrB = 0; rselA_O = 1; rselB_O = 1;
        wren = 0; waddr = 0; wsel_O = 1; wdata = 0;
        flags_update = 0; chord_in_update = 0; quad_out_update = 0;
        spu4_mode = 0;
        rau_opA_O = 0; rau_opB_C = 0; rau_opA_extra = 0; rau_op = 0;

        #20 rst_n = 1;
        #10;

        // ═════════════════════════════════════════════════════════════════
        // 1. Register file: write then read .O slot
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Register File: write/read .O ──");
        wren = 1; waddr = 10; wsel_O = 1; wdata = 64'hDEADBEEFCAFEFACE;
        #20 wren = 0;
        raddrA = 10; rselA_O = 1;
        #10;
        check(rdataA, 64'hDEADBEEFCAFEFACE, "RF: R10.O write/read");

        // ═════════════════════════════════════════════════════════════════
        // 2. Register file: write .C, read .C
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Register File: write/read .C ──");
        wren = 1; waddr = 11; wsel_O = 0; wdata = 64'h1234567890ABCDEF;
        #20 wren = 0;
        raddrB = 11; rselB_O = 0;
        #10;
        check(rdataB, 64'h1234567890ABCDEF, "RF: R11.C write/read");

        // ═════════════════════════════════════════════════════════════════
        // 3. Register file: R0 always reads zero
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Register File: R0 is ZERO ──");
        raddrA = 0; rselA_O = 1;
        #10;
        check(rdataA, 64'd0, "RF: R0 reads 0");

        // ═════════════════════════════════════════════════════════════════
        // 4. Register file: SPU-4 mode suppresses upper banks
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Register File: SPU-4 mode ──");
        spu4_mode = 1;
        wren = 1; waddr = 20; wsel_O = 1; wdata = 64'hBAD;
        #20 wren = 0;
        raddrA = 20; rselA_O = 1;
        #10;
        check(rdataA, 64'd0, "RF: SPU-4 mode: R20 ignored");
        spu4_mode = 0;

        // ═════════════════════════════════════════════════════════════════
        // 5. RAU: QADD — quadrance add
        // ═════════════════════════════════════════════════════════════════
        $display("\n── RAU: QADD (quadrance add) ──");
        // Quadray (10,0,0,0) → Q = 10² = 100
        // Quadray (5,0,0,0)  → Q = 5² = 25
        // Sum = 125
        rau_opA_O = {16'd10, 16'd0, 16'd0, 16'd0};  // a=10
        rau_opB_C = {16'd5, 16'd0, 16'd0, 16'd0};   // a=5
        rau_op = 4'd1;  // QADD
        #10;
        // a_sq = 10*10 = 100, e_sq = 5*5 = 25 + others=0 → qadd = 125
        check(rau_result, 64'd125, "RAU QADD: (10²)+(5²)=125");

        // ═════════════════════════════════════════════════════════════════
        // 6. RAU: PHSLK — matching quadrances → coherent
        // ═════════════════════════════════════════════════════════════════
        $display("\n── RAU: PHSLK coherent (matching) ──");
        // Both quadrays have a=10 → both Q = 100
        rau_opA_O = {16'd10, 16'd0, 16'd0, 16'd0};
        rau_opB_C = {16'd10, 16'd0, 16'd0, 16'd0};
        rau_op = 4'd9;  // PHSLK
        #10;
        check(rau_result, 64'd100, "RAU PHSLK: Q=100");
        if (rau_coherent !== 1) begin
            $display("FAIL: RAU PHSLK: not coherent (expected 1)");
            errors = errors + 1;
        end else begin
            $display("PASS: RAU PHSLK: coherent=1");
        end

        // ═════════════════════════════════════════════════════════════════
        // 7. RAU: PHSLK — mismatched quadrances → not coherent
        // ═════════════════════════════════════════════════════════════════
        $display("\n── RAU: PHSLK not coherent (mismatched) ──");
        rau_opA_O = {16'd10, 16'd0, 16'd0, 16'd0};  // Q = 100
        rau_opB_C = {16'd20, 16'd0, 16'd0, 16'd0};  // Q = 400
        rau_op = 4'd9;
        #10;
        if (rau_coherent !== 0) begin
            $display("FAIL: RAU PHSLK: coherent (expected 0 for mismatch)");
            errors = errors + 1;
        end else begin
            $display("PASS: RAU PHSLK: coherent=0 (mismatch detected)");
        end

        // ═════════════════════════════════════════════════════════════════
        // 8. RAU: QCMP — equal quadrances → zero flag
        // ═════════════════════════════════════════════════════════════════
        $display("\n── RAU: QCMP ──");
        rau_opA_O = {16'd7, 16'd0, 16'd0, 16'd0};  // Q = 49
        rau_opB_C = {16'd7, 16'd0, 16'd0, 16'd0};  // Q = 49
        rau_op = 4'd4;  // QCMP
        #10;
        check(rau_zero, 1'b1, "RAU QCMP: equal → zero=1");
        check(rau_sign, 1'b0, "RAU QCMP: equal → sign=0");

        // ═════════════════════════════════════════════════════════════════
        // 9. RAU: TNSR — tensor M = 4I
        // ═════════════════════════════════════════════════════════════════
        $display("\n── RAU: TNSR (tensor ×4) ──");
        rau_opA_O = {16'd3, 16'd1, 16'd4, 16'd1};
        rau_op = 4'd8;  // TNSR
        #10;
        // Each component shifted left 2 = ×4
        check(rau_result[63:48], 16'd12, "RAU TNSR: a=3→12");
        check(rau_result[47:32], 16'd4,  "RAU TNSR: b=1→4");
        check(rau_result[31:16], 16'd16, "RAU TNSR: c=4→16");
        check(rau_result[15:0],  16'd4,  "RAU TNSR: d=1→4");

        // ═════════════════════════════════════════════════════════════════
        // 10. RAU: QMUL
        // ═════════════════════════════════════════════════════════════════
        $display("\n── RAU: QMUL ──");
        rau_opA_O = {16'd10, 16'd0, 16'd0, 16'd0};  // Q = 100
        rau_opB_C = {16'd5, 16'd0, 16'd0, 16'd0};   // Q = 25
        rau_op = 4'd3;  // QMUL
        #10;
        check(rau_result, 64'd2500, "RAU QMUL: 100×25=2500");

        // ═════════════════════════════════════════════════════════════════
        // Results
        // ═════════════════════════════════════════════════════════════════
        #10;
        $display("\n── SUMMARY ──");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end

endmodule
