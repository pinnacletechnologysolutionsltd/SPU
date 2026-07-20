`timescale 1ns/1ps

module spu13_zphi_mul_serial_karatsuba_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;
    reg start = 0;
    reg signed [71:0] xa, xb;
    reg signed [33:0] ya, yb;

    wire ref_busy, ref_done;
    wire fast_busy, fast_done;
    wire signed [107:0] ref_a, ref_b, fast_a, fast_b;
    integer errors = 0;
    integer i;

    localparam signed [71:0] X_MAX = {1'b0, {71{1'b1}}};
    localparam signed [71:0] X_MIN = {1'b1, {71{1'b0}}};
    localparam signed [33:0] Y_MAX = {1'b0, {33{1'b1}}};
    localparam signed [33:0] Y_MIN = {1'b1, {33{1'b0}}};

    spu13_zphi_mul_serial u_ref (
        .clk(clk), .rst_n(rst_n), .start(start),
        .xa(xa), .xb(xb), .ya(ya), .yb(yb),
        .busy(ref_busy), .done(ref_done), .out_a(ref_a), .out_b(ref_b)
    );

    spu13_zphi_mul_serial_karatsuba u_fast (
        .clk(clk), .rst_n(rst_n), .start(start),
        .xa(xa), .xb(xb), .ya(ya), .yb(yb),
        .busy(fast_busy), .done(fast_done), .out_a(fast_a), .out_b(fast_b)
    );

    task check_equivalent;
        input signed [71:0] in_xa, in_xb;
        input signed [33:0] in_ya, in_yb;
        input [255:0] label;
        integer cycles;
        reg saw_fast;
        reg signed [107:0] saved_a, saved_b;
        begin
            xa = in_xa; xb = in_xb; ya = in_ya; yb = in_yb;
            start = 1'b1;
            @(posedge clk); #1;
            start = 1'b0;
            cycles = 0;
            saw_fast = 0;
            while (!ref_done && cycles < 10) begin
                @(posedge clk); #1;
                cycles = cycles + 1;
                if (fast_done) begin
                    saw_fast = 1;
                    saved_a = fast_a;
                    saved_b = fast_b;
                    if (cycles != 3 || fast_busy) begin
                        errors = errors + 1;
                        $display("FAIL %0s candidate latency cycles=%0d busy=%b",
                                 label, cycles, fast_busy);
                    end
                end
            end
            if (!ref_done || ref_busy || cycles != 4 || !saw_fast ||
                saved_a !== ref_a || saved_b !== ref_b) begin
                errors = errors + 1;
                $display("FAIL %0s ref_cycles=%0d saw_fast=%b fast=(%0d,%0d) ref=(%0d,%0d)",
                         label, cycles, saw_fast, saved_a, saved_b, ref_a, ref_b);
            end else begin
                $display("PASS %0s", label);
            end
            @(posedge clk); #1;
        end
    endtask

    initial begin
        xa = 0; xb = 0; ya = 0; yb = 0;
        repeat (3) @(posedge clk);
        rst_n = 1;

        check_equivalent(2, 3, 5, 7, "positive coefficients");
        check_equivalent(-2, 3, 5, -7, "mixed signed coefficients");
        check_equivalent(0, 1, 0, 1, "phi squared identity");
        check_equivalent(100000, -200000, -30000, 40000,
                         "wide exact coefficients");
        check_equivalent(X_MAX, X_MAX, Y_MAX, Y_MAX,
                         "all positive maxima");
        check_equivalent(X_MIN, X_MIN, Y_MIN, Y_MIN,
                         "all negative minima");
        check_equivalent(X_MAX, X_MIN, Y_MIN, Y_MAX,
                         "cancelling extrema");
        check_equivalent(X_MIN, X_MAX, Y_MAX, Y_MIN,
                         "opposed extrema");

        for (i = 0; i < 64; i = i + 1) begin
            check_equivalent({$random, $random, $random},
                             {$random, $random, $random},
                             {$random, $random},
                             {$random, $random},
                             "deterministic random equivalence");
        end

        if (errors == 0)
            $display("SPU13_ZPHI_MUL_SERIAL_KARATSUBA_TB: PASS");
        else
            $display("SPU13_ZPHI_MUL_SERIAL_KARATSUBA_TB: FAIL errors=%0d", errors);
        $finish(errors != 0);
    end
endmodule
