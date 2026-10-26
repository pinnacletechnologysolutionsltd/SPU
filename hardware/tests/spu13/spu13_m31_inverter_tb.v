`timescale 1ns / 1ps

// Testbench: spu13_m31_inverter — Verifies BEEA modular inversion over M31
module spu13_m31_inverter_tb;

    reg clk, rst_n, start;
    reg [31:0] x_in;
    wire [31:0] inv_out;
    wire done, busy;

    spu13_m31_inverter uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .x_in(x_in), .inv_out(inv_out), .done(done), .busy(busy)
    );

    localparam P = 32'h7FFFFFFF;

    always #5 clk = ~clk;

    // Verification: inv * x mod P should equal 1
    task check_inv;
        input [31:0] x;
        input [31:0] expected;
        begin
            x_in = x;
            start = 1; #10; start = 0;
            wait(done); #10;
            if (inv_out !== expected) begin
                $display("FAIL: inv(%h) expected %h, got %h", x, expected, inv_out);
                $stop;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; start = 0;
        #20 rst_n = 1; #10;

        // Test 1: inv(1) = 1
        check_inv(32'd1, 32'd1);

        // Test 2: inv(2) * 2 = 1 → inv(2) = (P+1)/2
        check_inv(32'd2, (P+1)/2);

        // Test 3: inv(P-1) = P-1 (since (P-1)^2 ≡ 1 mod P)
        check_inv(P-1, P-1);

        // Test 4: inv(3)
        // 3 * x ≡ 1 mod P → x = (2P+1)/3 = (2*2147483647+1)/3 = 1431655765
        check_inv(32'd3, 32'd1431655765);

        // Test 5: inv(1234567) — verify self-consistency
        // We'll just check that inv * x ≡ 1 mod P
        x_in = 32'd1234567;
        start = 1; #10; start = 0;
        wait(done); #10;
        if (((64'd1234567 * inv_out) % P) !== 64'd1) begin
            $display("FAIL: inv(1234567) * 1234567 != 1 mod P");
            $display("  inv_out = %h, product mod P = %h", inv_out, (64'd1234567 * inv_out) % P);
            $stop;
        end

        // Test 6: inv(65537)
        x_in = 32'd65537;
        start = 1; #10; start = 0;
        wait(done); #10;
        if (((64'd65537 * inv_out) % P) !== 64'd1) begin
            $display("FAIL: inv(65537) * 65537 != 1 mod P");
            $stop;
        end

        $display("PASS: spu13_m31_inverter_tb");
        $finish;
    end

endmodule
