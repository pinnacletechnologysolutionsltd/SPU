`timescale 1ns / 1ps

// rplu_thimble_pade_tb.v - smoke test for Horner handshake and A31 unit trap.

module rplu_thimble_pade_tb;

    reg clk, rst_n, start;
    reg coeff_we, coeff_is_den;
    reg [2:0] coeff_addr;
    reg [31:0] coeff_c0, coeff_c1, coeff_c2, coeff_c3;
    reg [31:0] saddle_c0, saddle_c1, saddle_c2, saddle_c3;

    wire [31:0] result_c0, result_c1, result_c2, result_c3;
    wire done, busy, flags_v;

    wire mult_start;
    wire [31:0] mult_a0, mult_a1, mult_a2, mult_a3;
    wire [31:0] mult_b0, mult_b1, mult_b2, mult_b3;
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire mult_done, mult_busy;

    wire inv_start;
    wire [31:0] inv_z0, inv_z1, inv_z2, inv_z3;
    wire [31:0] inv_r0, inv_r1, inv_r2, inv_r3;
    wire inv_done, inv_busy, inv_flags_v;

    wire inv_mult_start;
    wire [31:0] inv_mult_a0, inv_mult_a1, inv_mult_a2, inv_mult_a3;
    wire [31:0] inv_mult_b0, inv_mult_b1, inv_mult_b2, inv_mult_b3;
    wire [31:0] inv_mult_r0, inv_mult_r1, inv_mult_r2, inv_mult_r3;
    wire inv_mult_done, inv_mult_busy;

    rplu_thimble_pade uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .saddle_c0(saddle_c0), .saddle_c1(saddle_c1),
        .saddle_c2(saddle_c2), .saddle_c3(saddle_c3),
        .coeff_we(coeff_we), .coeff_is_den(coeff_is_den),
        .coeff_addr(coeff_addr),
        .coeff_c0(coeff_c0), .coeff_c1(coeff_c1),
        .coeff_c2(coeff_c2), .coeff_c3(coeff_c3),
        .result_c0(result_c0), .result_c1(result_c1),
        .result_c2(result_c2), .result_c3(result_c3),
        .done(done), .busy(busy), .flags_v(flags_v),
        .mult_start(mult_start),
        .mult_a0(mult_a0), .mult_a1(mult_a1),
        .mult_a2(mult_a2), .mult_a3(mult_a3),
        .mult_b0(mult_b0), .mult_b1(mult_b1),
        .mult_b2(mult_b2), .mult_b3(mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1),
        .mult_r2(mult_r2), .mult_r3(mult_r3),
        .mult_done(mult_done), .mult_busy(mult_busy),
        .inv_start(inv_start),
        .inv_z0(inv_z0), .inv_z1(inv_z1),
        .inv_z2(inv_z2), .inv_z3(inv_z3),
        .inv_r0(inv_r0), .inv_r1(inv_r1),
        .inv_r2(inv_r2), .inv_r3(inv_r3),
        .inv_done(inv_done), .inv_busy(inv_busy),
        .inv_flags_v(inv_flags_v)
    );

    spu13_m31_multiplier u_mult_pade (
        .clk(clk), .rst_n(rst_n), .start(mult_start),
        .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
        .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
        .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
        .done(mult_done), .busy(mult_busy)
    );

    spu13_m31_multiplier u_mult_inv (
        .clk(clk), .rst_n(rst_n), .start(inv_mult_start),
        .a0(inv_mult_a0), .a1(inv_mult_a1),
        .a2(inv_mult_a2), .a3(inv_mult_a3),
        .b0(inv_mult_b0), .b1(inv_mult_b1),
        .b2(inv_mult_b2), .b3(inv_mult_b3),
        .r0(inv_mult_r0), .r1(inv_mult_r1),
        .r2(inv_mult_r2), .r3(inv_mult_r3),
        .done(inv_mult_done), .busy(inv_mult_busy)
    );

    spu13_fp4_inverter u_inv (
        .clk(clk), .rst_n(rst_n), .start(inv_start),
        .z0(inv_z0), .z1(inv_z1), .z2(inv_z2), .z3(inv_z3),
        .inv0(inv_r0), .inv1(inv_r1), .inv2(inv_r2), .inv3(inv_r3),
        .done(inv_done), .busy(inv_busy), .flags_v(inv_flags_v),
        .mult_start(inv_mult_start),
        .mult_a0(inv_mult_a0), .mult_a1(inv_mult_a1),
        .mult_a2(inv_mult_a2), .mult_a3(inv_mult_a3),
        .mult_b0(inv_mult_b0), .mult_b1(inv_mult_b1),
        .mult_b2(inv_mult_b2), .mult_b3(inv_mult_b3),
        .mult_r0(inv_mult_r0), .mult_r1(inv_mult_r1),
        .mult_r2(inv_mult_r2), .mult_r3(inv_mult_r3),
        .mult_done(inv_mult_done), .mult_busy(inv_mult_busy)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;
    integer wait_cycles;

    task pulse_start;
        begin
            start = 1'b1;
            #10;
            start = 1'b0;
            wait_cycles = 0;
            while (!done && wait_cycles < 1000) begin
                #10;
                wait_cycles = wait_cycles + 1;
            end
        end
    endtask

    task check;
        input ok;
        input [255:0] msg;
        begin
            test_total = test_total + 1;
            if (ok) test_pass = test_pass + 1;
            else $display("FAIL: %0s", msg);
        end
    endtask

    task write_den0;
        input [31:0] z0, z1, z2, z3;
        begin
            coeff_is_den = 1'b1;
            coeff_addr = 3'd0;
            coeff_c0 = z0; coeff_c1 = z1; coeff_c2 = z2; coeff_c3 = z3;
            coeff_we = 1'b1;
            #10;
            coeff_we = 1'b0;
        end
    endtask

    initial begin
        clk = 0;
        rst_n = 0;
        start = 0;
        coeff_we = 0;
        coeff_is_den = 0;
        coeff_addr = 0;
        coeff_c0 = 0; coeff_c1 = 0; coeff_c2 = 0; coeff_c3 = 0;
        saddle_c0 = 32'd2; saddle_c1 = 0; saddle_c2 = 0; saddle_c3 = 0;
        test_pass = 0;
        test_total = 0;

        #20 rst_n = 1;
        #20;

        // Default coefficients are numerator=1, denominator=1.
        pulse_start();
        check(done && !flags_v, "default 1/1 completes without FLAGS.V");
        check(result_c0 == 32'd1 && result_c1 == 32'd0 &&
              result_c2 == 32'd0 && result_c3 == 32'd0,
              "default 1/1 returns A31 one");

        // p - sqrt(15) + uv is a nonzero zero-divisor in the split algebra.
        write_den0(32'h2CEE24B2, 32'd0, 32'd0, 32'd1);
        pulse_start();
        check(done && flags_v, "nonzero zero-divisor denominator asserts FLAGS.V");

        if (test_pass == test_total)
            $display("PASS: rplu_thimble_pade_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: rplu_thimble_pade_tb (%0d/%0d)", test_pass, test_total);

        $finish;
    end

endmodule
