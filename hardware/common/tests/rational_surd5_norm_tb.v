`timescale 1ns/1ps

module rational_surd5_norm_tb();
    reg [63:0] in_val;
    wire [63:0] out_val;
    wire [3:0] scale_shift;
    wire overflow;

    rational_surd5_norm uut (.in(in_val), .out(out_val), .scale_shift(scale_shift), .overflow(overflow));

    initial begin
        // Case 1: small values -> no shift
        in_val = {32'sd10, 32'sd20}; // P=10, Q=20
        #1;
        if (out_val == in_val && scale_shift == 0 && overflow == 0) $display("PASS case1"); else $display("FAIL case1: out=%h shift=%d of=%b", out_val, scale_shift, overflow);

        // Case 2: large P triggers shift
        in_val = {32'sd1073741824, 32'sd5}; // P = 2^30 = 1073741824
        #1;
        if (scale_shift == 1 && overflow == 0) $display("PASS case2 (shift)"); else $display("FAIL case2: out=%h shift=%d of=%b", out_val, scale_shift, overflow);

        // Case 3: extremely large values still overflow after one shift
        // Use INT32_MIN (-2147483648) since arithmetic shift keeps magnitude > MAX_MAG
        in_val = {32'h80000000, 32'h80000000}; // INT32_MIN bitpattern (signed -2147483648)
        #1;
        if (overflow == 1) $display("PASS case3 (overflow)"); else $display("FAIL case3: out=%h shift=%d of=%b", out_val, scale_shift, overflow);

        $finish;
    end
endmodule
