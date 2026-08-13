`timescale 1ns/1ps

// Lucas MAC poison proofs: rejected or overlapping operations must not commit
// a result, and CE stalls must preserve the in-flight operation.
module spu13_lucas_mac_poison_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0, ce = 1, start = 0;
    reg [2:0] opcode = 0;
    reg [9:0] op_a = 0, op_b = 0, op_c = 0, op_d = 0;
    reg [9:0] n2a = 0, n2b = 0, d2a = 0, d2b = 0;
    wire busy, done, error;
    wire [9:0] result_a, result_b;
    wire coherent, zero_divisor, norm_violation;
    integer failures = 0;

    reg f_start = 0;
    reg [2:0] f_opcode = 0;
    reg [9:0] f_a = 0, f_b = 0, f_c = 0, f_d = 0;
    wire f_busy, f_done, f_error;
    wire [9:0] f_result_a, f_result_b;

    spu13_lucas_mac dut (
        .clk(clk), .rst_n(rst_n), .ce(ce), .start(start), .opcode(opcode),
        .op_a(op_a), .op_b(op_b), .op_c(op_c), .op_d(op_d),
        .phslk_n2_a(n2a), .phslk_n2_b(n2b),
        .phslk_d2_a(d2a), .phslk_d2_b(d2b),
        .busy(busy), .done(done), .error(error),
        .result_a(result_a), .result_b(result_b),
        .phslk_coherent(coherent), .phslk_zero_divisor(zero_divisor),
        .norm_violation(norm_violation));

    spu13_lucas_mac #(.FAST_ONLY(1)) fast_only_dut (
        .clk(clk), .rst_n(rst_n), .ce(1'b1), .start(f_start),
        .opcode(f_opcode), .op_a(f_a), .op_b(f_b), .op_c(f_c), .op_d(f_d),
        .phslk_n2_a(10'd0), .phslk_n2_b(10'd0),
        .phslk_d2_a(10'd0), .phslk_d2_b(10'd0),
        .busy(f_busy), .done(f_done), .error(f_error),
        .result_a(f_result_a), .result_b(f_result_b),
        .phslk_coherent(), .phslk_zero_divisor(), .norm_violation());

    task accept;
        input [2:0] op;
        input [9:0] a, b, c, d;
        begin
            @(negedge clk); opcode=op; op_a=a; op_b=b; op_c=c; op_d=d; start=1;
            @(negedge clk); start=0;
        end
    endtask

    task expect_clean_result;
        input [9:0] a, b;
        input [127:0] label;
        begin
            if (result_a !== a || result_b !== b || error || norm_violation) begin
                $display("FAIL: %0s result=(%0d,%0d) error=%b norm=%b",
                         label, result_a, result_b, error, norm_violation);
                failures = failures + 1;
            end else $display("PASS: %0s", label);
        end
    endtask

    integer i;
    reg [9:0] saved_a, saved_b;
    initial begin
        #2; rst_n=0; #12; rst_n=1;

        // Establish a committed value: φ·1 = φ.
        accept(3'd0, 10'd1, 10'd0, 10'd0, 10'd0);
        #1; expect_clean_result(10'd0, 10'd1, "baseline PSCALE commit");
        saved_a = result_a; saved_b = result_b;

        // Invalid opcode reports an error and preserves the previous result.
        accept(3'd7, 10'd9, 10'd4, 10'd0, 10'd0);
        #1;
        if (!error || done || busy || result_a !== saved_a || result_b !== saved_b)
            begin
                $display("FAIL: invalid opcode committed or had wrong status");
                failures = failures + 1;
            end
        else $display("PASS: invalid opcode poison hold");

        // A start while PMUL is busy must not replace the in-flight operation.
        accept(3'd2, 10'd3, 10'd5, 10'd2, 10'd7);
        @(negedge clk); opcode=3'd0; op_a=10'd1; op_b=10'd0; start=1;
        @(negedge clk); start=0;
        wait(done || error); #1;
        expect_clean_result(10'd41, 10'd66, "busy overlap ignored");

        // CE low freezes the busy operation and suppresses visible pulses.
        accept(3'd2, 10'd3, 10'd5, 10'd2, 10'd7);
        repeat (2) @(negedge clk);
        ce = 0; saved_a = result_a; saved_b = result_b;
        repeat (3) begin
            @(negedge clk);
            if (!busy || done || error || result_a !== saved_a || result_b !== saved_b) begin
                $display("FAIL: CE stall changed in-flight state");
                failures = failures + 1;
            end
        end
        ce = 1; wait(done || error); #1;
        expect_clean_result(10'd41, 10'd66, "CE stall resumes exactly");

        // FAST_ONLY rejects PMUL/PINV without asserting busy or committing.
        @(negedge clk); f_opcode=3'd2; f_a=3; f_b=5; f_c=2; f_d=7; f_start=1;
        @(negedge clk); f_start=0; #1;
        if (!f_error || f_done || f_busy || f_result_a !== 0 || f_result_b !== 0) begin
            $display("FAIL: FAST_ONLY PMUL poison status/result");
            failures = failures + 1;
        end else $display("PASS: FAST_ONLY PMUL rejected without commit");

        @(negedge clk); f_opcode=3'd3; f_start=1;
        @(negedge clk); f_start=0; #1;
        if (!f_error || f_done || f_busy || f_result_a !== 0 || f_result_b !== 0) begin
            $display("FAIL: FAST_ONLY PINV poison status/result");
            failures = failures + 1;
        end else $display("PASS: FAST_ONLY PINV rejected without commit");

        if (failures == 0) $display("LUCAS_POISON: PASS");
        else $display("LUCAS_POISON: FAIL failures=%0d", failures);
        #20; $finish;
    end
endmodule
