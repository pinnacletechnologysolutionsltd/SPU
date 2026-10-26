`timescale 1ns / 1ps

// Testbench: spu13_m31_multiplier — Verifies F_{p^4} multiplication + M31 reduction
module spu13_m31_multiplier_tb;

    reg clk, rst_n, start;
    reg [31:0] a0, a1, a2, a3;
    reg [31:0] b0, b1, b2, b3;
    wire [31:0] r0, r1, r2, r3;
    wire done, busy, rns_error;

    spu13_m31_multiplier uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(r0), .r1(r1), .r2(r2), .r3(r3),
        .done(done), .busy(busy),
        .rns_error(rns_error)
    );

    localparam P = 32'h7FFFFFFF;

    // Clock
    always #5 clk = ~clk;

    integer test_pass, test_total;

    // Python reference: compute expected in F_{p^4}
    task check_mult;
        input [31:0] ea0, ea1, ea2, ea3;
        input [31:0] eb0, eb1, eb2, eb3;
        input [31:0] exp0, exp1, exp2, exp3;
        begin
            test_total = test_total + 1;
            a0 = ea0; a1 = ea1; a2 = ea2; a3 = ea3;
            b0 = eb0; b1 = eb1; b2 = eb2; b3 = eb3;
            start = 1; #10; start = 0;
            wait(done);
            #2;  // Let NBAs settle
            if (rns_error) begin
                $display("FAIL: rns_error asserted for A=(%h,%h,%h,%h) * B=(%h,%h,%h,%h)",
                         ea0, ea1, ea2, ea3, eb0, eb1, eb2, eb3);
            end else if (r0 !== exp0 || r1 !== exp1 || r2 !== exp2 || r3 !== exp3) begin
                $display("FAIL: A=(%h,%h,%h,%h) * B=(%h,%h,%h,%h)", ea0,ea1,ea2,ea3, eb0,eb1,eb2,eb3);
                $display("  expected (%h,%h,%h,%h)", exp0, exp1, exp2, exp3);
                $display("  got      (%h,%h,%h,%h)", r0, r1, r2, r3);
            end else begin
                test_pass = test_pass + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; start = 0;
        test_pass = 0; test_total = 0;
        #20 rst_n = 1; #10;

        // Test 1: Identity: (1,0,0,0) * (1,0,0,0) = (1,0,0,0)
        check_mult(32'd1, 32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0);

        // Test 2: Scalar multiply: (5,0,0,0) * (3,0,0,0) = (15,0,0,0)
        check_mult(32'd5, 32'd0, 32'd0, 32'd0, 32'd3, 32'd0, 32'd0, 32'd0, 32'd15, 32'd0, 32'd0, 32'd0);

        // Test 3: √3 × √3 = 3: (0,1,0,0) * (0,1,0,0) = (3,0,0,0)
        check_mult(32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd3, 32'd0, 32'd0, 32'd0);

        // Test 4: √5 × √5 = 5: (0,0,1,0) * (0,0,1,0) = (5,0,0,0)
        check_mult(32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd5, 32'd0, 32'd0, 32'd0);

        // Test 5: √15 × √15 = 15: (0,0,0,1) * (0,0,0,1) = (15,0,0,0)
        check_mult(32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd1, 32'd15, 32'd0, 32'd0, 32'd0);

        // Test 6: √3 × √5 = √15: (0,1,0,0) * (0,0,1,0) = (0,0,0,1)
        check_mult(32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd0, 32'd1);

        // Test 7: Large values near M31 limit, verifying reduction
        // (P-1, 0, 0, 0) * (2, 0, 0, 0) = (2P-2 mod P, 0, 0, 0) = (P-2, 0, 0, 0)
        check_mult(P-1, 32'd0, 32'd0, 32'd0, 32'd2, 32'd0, 32'd0, 32'd0, P-2, 32'd0, 32'd0, 32'd0);

        // Test 8: Python reference: (10,2,0,4) * (5,0,1,2) from paste
        check_mult(32'd10, 32'd2, 32'd0, 32'd4, 32'd5, 32'd0, 32'd1, 32'd2, 32'd170, 32'd30, 32'd22, 32'd42);

        // Test 9: Zero multiply
        check_mult(32'd0, 32'd0, 32'd0, 32'd0, 32'd123, 32'd456, 32'd789, 32'd101112, 32'd0, 32'd0, 32'd0, 32'd0);

        if (test_pass == test_total)
            $display("PASS: spu13_m31_multiplier_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_m31_multiplier_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
