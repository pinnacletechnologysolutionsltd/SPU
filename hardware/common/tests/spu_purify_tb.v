// Testbench: spu_purify_tb.v
// Verifies spectral GCD reduction and display scaling.
//
// Cases:
//  1. Full spread (numer=denom=272) → pixel_val == max_out (255)
//  2. Zero spread (numer=0, denom=272) → pixel_val == 0
//  3. Half spread (numer=136, denom=272 → GCD=136 → 1/2) → pixel_val ≈ 127
//  4. Quarter spread (numer=68, denom=272 → GCD=68 → 1/4) → pixel_val ≈ 63
//  5. max_out=1023 (10-bit PHY), half spread → pixel_val ≈ 511

`timescale 1ns/1ps
`include "spu_purify.v"
`include "spu_rational_lut.v"

module spu_purify_tb;

    reg         clk, reset;
    reg  [63:0] numer, denom;
    reg  [9:0]  max_out;
    reg         valid_in;
    wire [9:0]  pixel_val;
    wire        valid_out;

    integer fail = 0;

    spu_purify uut (
        .clk(clk), .reset(reset),
        .numer(numer), .denom(denom),
        .max_out(max_out), .valid_in(valid_in),
        .pixel_val(pixel_val), .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    task apply_and_check;
        input [63:0] n, d;
        input [9:0]  mx;
        input [9:0]  expected_lo, expected_hi;  // acceptable range [lo, hi]
        input [63:0] label;
        begin
            @(negedge clk);
            numer = n; denom = d; max_out = mx; valid_in = 1;
            @(posedge clk); #1;  // registered output: 2 cycles
            @(posedge clk); #1;
            valid_in = 0;
            if (!valid_out) begin
                $display("FAIL (%0d): valid_out not asserted", label);
                fail = fail + 1;
            end else if (pixel_val < expected_lo || pixel_val > expected_hi) begin
                $display("FAIL (%0d): pixel_val=%0d not in [%0d, %0d]",
                         label, pixel_val, expected_lo, expected_hi);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        clk = 0; reset = 1; valid_in = 0;
        numer = 0; denom = 1; max_out = 255;
        #12; reset = 0;

        // Case 1: full spread → max_out
        apply_and_check(272, 272, 10'd255, 10'd254, 10'd255, 1);

        // Case 2: zero spread → 0
        apply_and_check(0, 272, 10'd255, 10'd0, 10'd0, 2);

        // Case 3: half spread (numer=136, denom=272, GCD=136 → 1/2)
        // Expected: ~127 (255/2). Allow ±2 for LUT approximation.
        apply_and_check(136, 272, 10'd255, 10'd125, 10'd129, 3);

        // Case 4: quarter spread (numer=68, denom=272, GCD=68 → 1/4)
        // Expected: ~63 (255/4). Allow ±3.
        apply_and_check(68, 272, 10'd255, 10'd60, 10'd66, 4);

        // Case 5: 10-bit PHY, half spread → ~511
        apply_and_check(136, 272, 10'd1023, 10'd509, 10'd515, 5);

        // Case 6: large coprime fraction 3/7 → pixel_val ≈ 109 (255*3/7)
        // Allow ±3 for LUT approximation.
        apply_and_check(3, 7, 10'd255, 10'd106, 10'd112, 6);

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL: %0d error(s)", fail);
        $finish;
    end

endmodule
