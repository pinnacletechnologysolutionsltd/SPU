// spu13_m31_multiplier_seq_tb.v — Oracle-driven testbench
//
// Compares sequential M31 multiplier output against the Python/C++ oracle.
// Uses the existing parallel multiplier as reference in simulation.

`timescale 1ns/1ps

module spu13_m31_multiplier_seq_tb;

    reg         clk = 0;
    reg         rst_n = 0;
    reg         s_start, p_start;
    reg  [31:0] a0, a1, a2, a3;
    reg  [31:0] b0, b1, b2, b3;
    wire [31:0] sr0, sr1, sr2, sr3;
    wire        sdone, sbusy;
    wire [31:0] pr0, pr1, pr2, pr3;
    wire        pdone, pbusy;

    spu13_m31_multiplier_seq #(.DEVICE("SIM")) u_seq (
        .clk(clk), .rst_n(rst_n), .start(s_start),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(sr0), .r1(sr1), .r2(sr2), .r3(sr3),
        .done(sdone), .busy(sbusy), .rns_error()
    );

    spu13_m31_multiplier u_par (
        .clk(clk), .rst_n(rst_n), .start(p_start),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(pr0), .r1(pr1), .r2(pr2), .r3(pr3),
        .done(pdone), .busy(pbusy), .rns_error()
    );

    always #5 clk = ~clk;  // 100 MHz

    localparam [31:0] P = 32'h7FFFFFFF;

    integer fail = 0;
    integer test_n = 0;

    task run_test;
        input [31:0] ta0, ta1, ta2, ta3;
        input [31:0] tb0, tb1, tb2, tb3;
        begin
            test_n = test_n + 1;
            // Set operands one cycle before asserting start to avoid
            // race between blocking assignments and posedge sampling
            @(posedge clk);
            a0 = ta0; a1 = ta1; a2 = ta2; a3 = ta3;
            b0 = tb0; b1 = tb1; b2 = tb2; b3 = tb3;
            @(posedge clk);
            s_start = 1;
            p_start = 1;
            @(posedge clk);
            s_start = 0;
            p_start = 0;

            // Wait for parallel result (parallel: 2-cycle pipeline from start assertion)
            @(posedge clk);  // stage 0→1
            @(posedge clk);  // stage 1 output valid

            // Wait for sequential result
            wait(sdone);
            @(posedge clk);

            // Sequential should match parallel
            if (sr0 !== pr0 || sr1 !== pr1 || sr2 !== pr2 || sr3 !== pr3) begin
                $display("FAIL test %0d: seq=(%h,%h,%h,%h) par=(%h,%h,%h,%h)",
                    test_n, sr0, sr1, sr2, sr3, pr0, pr1, pr2, pr3);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        rst_n = 0; s_start = 0; p_start = 0;
        #20 rst_n = 1;
        #20;

        // Test 1: identity (1 × 1)
        run_test(32'd1, 32'd0, 32'd0, 32'd0,
                 32'd1, 32'd0, 32'd0, 32'd0);

        // Test 2: A × identity
        run_test(32'd12345, 32'd67890, 32'd11111, 32'd22222,
                 32'd1, 32'd0, 32'd0, 32'd0);

        // Test 3: symmetric product
        run_test(32'd100, 32'd200, 32'd300, 32'd400,
                 32'd100, 32'd200, 32'd300, 32'd400);

        // Test 4: near-M31 values
        run_test(P-1, P-2, P-3, P-4,
                 P-5, P-6, P-7, P-8);

        // Test 5: small values
        run_test(32'd2, 32'd3, 32'd5, 32'd7,
                 32'd11, 32'd13, 32'd17, 32'd19);

        // Test 6: zeros
        run_test(32'd0, 32'd0, 32'd0, 32'd0,
                 32'd0, 32'd0, 32'd0, 32'd0);

        // Test 7: random-ish
        run_test(32'h12345678, 32'h23456789, 32'h3456789A, 32'h456789AB,
                 32'h56789ABC, 32'h6789ABCD, 32'h789ABCDE, 32'h89ABCDEF);

        if (fail == 0)
            $display("PASS (%0d tests)", test_n);
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

endmodule
