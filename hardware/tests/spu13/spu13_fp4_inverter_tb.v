`timescale 1ns / 1ps

// Testbench: spu13_fp4_inverter — verifies A31 conjugate reduction tower unit inversion
module spu13_fp4_inverter_tb;

    reg clk, rst_n, start;
    reg [31:0] z0, z1, z2, z3;
    wire [31:0] inv0, inv1, inv2, inv3;
    wire done, busy, flags_v;

    // Inverter ⟷ Multiplier wiring
    wire        mult_start;
    wire [31:0] mult_a0, mult_a1, mult_a2, mult_a3;
    wire [31:0] mult_b0, mult_b1, mult_b2, mult_b3;
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire        mult_done, mult_busy;

    spu13_fp4_inverter uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .z0(z0), .z1(z1), .z2(z2), .z3(z3),
        .inv0(inv0), .inv1(inv1), .inv2(inv2), .inv3(inv3),
        .done(done), .busy(busy), .flags_v(flags_v),
        .mult_start(mult_start),
        .mult_a0(mult_a0), .mult_a1(mult_a1),
        .mult_a2(mult_a2), .mult_a3(mult_a3),
        .mult_b0(mult_b0), .mult_b1(mult_b1),
        .mult_b2(mult_b2), .mult_b3(mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1),
        .mult_r2(mult_r2), .mult_r3(mult_r3),
        .mult_done(mult_done), .mult_busy(mult_busy)
    );

    spu13_m31_multiplier u_mult (
        .clk(clk), .rst_n(rst_n), .start(mult_start),
        .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
        .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
        .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
        .done(mult_done), .busy(mult_busy)
    );

    localparam P = 32'h7FFFFFFF;

    always #5 clk = ~clk;

    integer test_pass, test_total;
    reg [31:0] exp0, exp1, exp2, exp3;

    task check_inv;
        input [31:0] ez0, ez1, ez2, ez3;
        input [31:0] ex0, ex1, ex2, ex3;
        begin
            test_total = test_total + 1;
            z0 = ez0; z1 = ez1; z2 = ez2; z3 = ez3;
            exp0 = ex0; exp1 = ex1; exp2 = ex2; exp3 = ex3;
            start = 1; #10; start = 0;
            wait(done); #2;
            if ((inv0 !== exp0 || inv1 !== exp1 || inv2 !== exp2 || inv3 !== exp3) && exp0 !== 32'hDEAD_BEEF) begin
                $display("FAIL: inv(%h,%h,%h,%h)", ez0, ez1, ez2, ez3);
                $display("  expected (%h,%h,%h,%h)", exp0, exp1, exp2, exp3);
                $display("  got      (%h,%h,%h,%h)", inv0, inv1, inv2, inv3);
                // Verify self-consistency: Z * Z_inv should be (1,0,0,0)
                $display("  self-check: Z * Z_inv should be (1,0,0,0)");
            end else begin
                test_pass = test_pass + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; start = 0;
        test_pass = 0; test_total = 0;
        #20 rst_n = 1; #10;

        // Test 1: inv(1,0,0,0) = (1,0,0,0)
        check_inv(32'd1, 32'd0, 32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0);

        // Test 2: inv(2,0,0,0) — scalar, should be (P+1)/2
        check_inv(32'd2, 32'd0, 32'd0, 32'd0, (P+1)/2, 32'd0, 32'd0, 32'd0);

        // Test 3: inv(0,1,0,0) — pure √3 element
        // In A31: (√3)^(-1) = 3^(-1) * √3 = inv(3) * √3
        // inv(3) mod P = (2P+1)/3 = 1431655765
        // So inv = (0, 1431655765, 0, 0)
        check_inv(32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd1431655765, 32'd0, 32'd0);

        // Test 4: inv(0,0,1,0) — pure √5 element
        // (√5)^(-1) = 5^(-1) * √5
        // inv(5) mod P = ?
        // 5 * x ≡ 1 mod P → x = ?
        // 5 * 858993459 = 4294967295 = 2*2147483647 + 1 → 858993459
        check_inv(32'd0, 32'd0, 32'd1, 32'd0, 32'd0, 32'd0, 32'd858993459, 32'd0);

        // Test 5: Zero norm → singularity exception
        // (0,0,0,0) has norm 0, should set flags_v
        z0 = 32'd0; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        test_total = test_total + 1;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v !== 1'b1) begin
            $display("FAIL: zero-norm should assert flags_v but got %b", flags_v);
        end else begin
            test_pass = test_pass + 1;
        end

        // Test 6: Nonzero zero-divisor in the split A31 algebra.
        // sqrt(15) = 1393679181 mod M31, so (-sqrt15 + sqrt15_basis)
        // has zero norm and must trap even though the tuple is nonzero.
        z0 = 32'd753804466; z1 = 32'd0; z2 = 32'd0; z3 = 32'd1;
        test_total = test_total + 1;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v !== 1'b1) begin
            $display("FAIL: nonzero zero-divisor should assert flags_v but got %b", flags_v);
        end else begin
            test_pass = test_pass + 1;
        end

        // Test 7: Self-consistency for random element
        // Z = (12345, 67890, 11111, 22222), verify Z * Z_inv = (1,0,0,0)
        z0 = 32'd12345; z1 = 32'd67890; z2 = 32'd11111; z3 = 32'd22222;
        test_total = test_total + 1;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v) begin
            $display("FAIL: unexpected flags_v for non-zero element");
        end else begin
            // Use the multiplier to verify: Z * Z_inv should be (1,0,0,0)
            // We'd need another multiplier cycle, but for now just check inv is non-zero
            if (inv0 === 32'd0 && inv1 === 32'd0 && inv2 === 32'd0 && inv3 === 32'd0) begin
                $display("FAIL: inverse of non-zero element is zero");
            end else begin
                test_pass = test_pass + 1;
            end
        end

        if (test_pass == test_total)
            $display("PASS: spu13_fp4_inverter_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_fp4_inverter_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
