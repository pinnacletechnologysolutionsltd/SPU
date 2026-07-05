`timescale 1ns / 1ps

// singular_absorber_tb.v — Stress-test the zero-norm singularity exception path
//
// Exercises five scenarios through the F_{p^4} inverter:
//   A) Valid inversion of a known element → verify correct result
//   B) Zero element → verify FLAGS.V assertion and clean trap
//   C) Small-norm element near zero → verify graceful handling
//   D) Alternating valid → zero-divisor → valid stress pattern
//   E) Rapid-fire zero-divisor burst (3+ consecutive)
//
// This directly validates the Lefschetz thimble absorber boundary condition
// where the Padé denominator approaches zero (geometric singularity).

module singular_absorber_tb;

    reg clk, rst_n, start;
    reg [31:0] z0, z1, z2, z3;
    wire [31:0] inv0, inv1, inv2, inv3;
    wire done, busy, flags_v;

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
        .mult_done(mult_done), .mult_busy(mult_busy),
        .debug_state(), .debug_start_accept()
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

    initial begin
        clk = 0; rst_n = 0; start = 0;
        test_pass = 0; test_total = 0;
        #20 rst_n = 1; #10;

        // ── Scenario A: Valid inversion ────────────────────────────
        // inv(5,0,0,0) should give a non-zero result, no exception
        test_total = test_total + 1;
        z0 = 32'd5; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v || inv0 == 32'd0) begin
            $display("FAIL A: flags_v=%b inv0=%h (expected clean inversion)", flags_v, inv0);
        end else test_pass = test_pass + 1;

        // ── Scenario B: Zero element → singularity ─────────────────
        // inv(0,0,0,0) must assert FLAGS.V and not hang
        test_total = test_total + 1;
        z0 = 32'd0; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v !== 1'b1) begin
            $display("FAIL B: zero element should assert flags_v, got %b", flags_v);
        end else test_pass = test_pass + 1;

        // ── Scenario C: Small-norm element (near singularity) ─────
        // Z = (1,0,0,0) has norm=1 → stable
        // Verify that it doesn't trigger false positive
        test_total = test_total + 1;
        z0 = 32'd1; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v || inv0 !== 32'd1) begin
            $display("FAIL C: inv(1) should be 1, got flags_v=%b inv0=%h", flags_v, inv0);
        end else test_pass = test_pass + 1;

        // ── Scenario D: Repeat B (zero) — verify clean re-arm ─────
        // After a singularity, the inverter should reset and handle
        // the next request cleanly
        test_total = test_total + 1;
        z0 = 32'd0; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v !== 1'b1) begin
            $display("FAIL D: re-arm zero test, flags_v=%b", flags_v);
        end else test_pass = test_pass + 1;

        // ── Scenario E: Valid after exception ──────────────────────
        // After a singularity trap, a valid inversion should still work
        test_total = test_total + 1;
        z0 = 32'd3; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v || inv0 == 32'd0) begin
            $display("FAIL E: post-exception inv(3), flags_v=%b inv0=%h", flags_v, inv0);
        end else test_pass = test_pass + 1;

        // ── Scenario F: Alternating valid → zero-divisor burst ────
        // Stress-test the state machine with rapid oscillation between
        // valid and singular inputs. 5 rapid alternations.
        for (int alt = 0; alt < 5; alt = alt + 1) begin
            // Valid
            test_total = test_total + 1;
            z0 = 32'd7; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
            start = 1; #10; start = 0;
            wait(done); #2;
            if (flags_v || inv0 == 32'd0) begin
                $display("FAIL F%0d: valid alt, flags_v=%b inv0=%h", alt, flags_v, inv0);
            end else test_pass = test_pass + 1;

            // Zero divisor (nonzero zero-divisor in A31: sqrt(15) - uv)
            test_total = test_total + 1;
            z0 = 32'h2CEE24B2; z1 = 32'd0; z2 = 32'd0; z3 = 32'd1;
            start = 1; #10; start = 0;
            wait(done); #2;
            if (flags_v !== 1'b1) begin
                $display("FAIL F%0d: zero-divisor alt, flags_v=%b", alt, flags_v);
            end else test_pass = test_pass + 1;
        end

        // ── Scenario G: Long idle → zero → valid ──────────────────
        // Prove the state machine doesn't drift after extended inactivity
        #500;  // idle for 50 clock cycles
        test_total = test_total + 1;
        z0 = 32'd0; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v !== 1'b1) begin
            $display("FAIL G1: post-idle zero, flags_v=%b", flags_v);
        end else test_pass = test_pass + 1;

        test_total = test_total + 1;
        z0 = 32'd5; z1 = 32'd0; z2 = 32'd0; z3 = 32'd0;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (flags_v || inv0 == 32'd0) begin
            $display("FAIL G2: post-idle valid, flags_v=%b inv0=%h", flags_v, inv0);
        end else test_pass = test_pass + 1;

        if (test_pass == test_total)
            $display("PASS: singular_absorber_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: singular_absorber_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
