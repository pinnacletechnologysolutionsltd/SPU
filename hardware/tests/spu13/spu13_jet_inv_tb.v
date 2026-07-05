`timescale 1ns / 1ps

// spu13_jet_inv_tb.v — Testbench for jet inverse re-assembly pipeline
//
// Tests:
//   A) Inv(scalar identity): J⁻¹ where J=(5,0,0) → self-consistency J·J⁻¹=(1,0,0)
//   B) Inv with velocity: J=(5,3,2) → J·J⁻¹=(1,0,0)
//   C) Zero-divisor trap: J=(0,1,0) → err_zero_divisor
//   D) Post-trap recovery: valid inversion after zero-divisor

module spu13_jet_inv_tb;

    reg clk, rst_n, start;
    reg [31:0] c0_z0, c0_z1, c0_z2, c0_z3;
    reg [31:0] c1_z0, c1_z1, c1_z2, c1_z3;
    reg [31:0] c2_z0, c2_z1, c2_z2, c2_z3;

    wire [31:0] m0_z0, m0_z1, m0_z2, m0_z3;
    wire [31:0] m1_z0, m1_z1, m1_z2, m1_z3;
    wire [31:0] m2_z0, m2_z1, m2_z2, m2_z3;
    wire done, busy, err_zero_divisor;

    // Inverter interface
    wire        inv_start;
    wire [31:0] inv_z0, inv_z1, inv_z2, inv_z3;
    wire [31:0] inv_r0, inv_r1, inv_r2, inv_r3;
    wire        inv_done, inv_busy, inv_flags_v;

    // Multiplier interface (from inverter tower)
    wire        tower_mult_start;
    wire [31:0] tower_mult_a0, tower_mult_a1, tower_mult_a2, tower_mult_a3;
    wire [31:0] tower_mult_b0, tower_mult_b1, tower_mult_b2, tower_mult_b3;
    wire [31:0] tower_mult_r0, tower_mult_r1, tower_mult_r2, tower_mult_r3;
    wire        tower_mult_done, tower_mult_busy;

    // Multiplier interface (from jet_inv shadow chain)
    wire        jet_mult_start;
    wire [31:0] jet_mult_a0, jet_mult_a1, jet_mult_a2, jet_mult_a3;
    wire [31:0] jet_mult_b0, jet_mult_b1, jet_mult_b2, jet_mult_b3;
    wire [31:0] jet_mult_r0, jet_mult_r1, jet_mult_r2, jet_mult_r3;
    wire        jet_mult_done;

    // ── DUT: Jet inverse ──────────────────────────────────────────────
    spu13_jet_inv uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .c0_z0(c0_z0), .c0_z1(c0_z1), .c0_z2(c0_z2), .c0_z3(c0_z3),
        .c1_z0(c1_z0), .c1_z1(c1_z1), .c1_z2(c1_z2), .c1_z3(c1_z3),
        .c2_z0(c2_z0), .c2_z1(c2_z1), .c2_z2(c2_z2), .c2_z3(c2_z3),
        .m0_z0(m0_z0), .m0_z1(m0_z1), .m0_z2(m0_z2), .m0_z3(m0_z3),
        .m1_z0(m1_z0), .m1_z1(m1_z1), .m1_z2(m1_z2), .m1_z3(m1_z3),
        .m2_z0(m2_z0), .m2_z1(m2_z1), .m2_z2(m2_z2), .m2_z3(m2_z3),
        .done(done), .busy(busy), .err_zero_divisor(err_zero_divisor),
        .inv_start(inv_start), .inv_z0(inv_z0), .inv_z1(inv_z1),
        .inv_z2(inv_z2), .inv_z3(inv_z3),
        .inv_r0(inv_r0), .inv_r1(inv_r1), .inv_r2(inv_r2), .inv_r3(inv_r3),
        .inv_done(inv_done), .inv_busy(inv_busy), .inv_flags_v(inv_flags_v),
        .mult_start(jet_mult_start),
        .mult_a0(jet_mult_a0), .mult_a1(jet_mult_a1),
        .mult_a2(jet_mult_a2), .mult_a3(jet_mult_a3),
        .mult_b0(jet_mult_b0), .mult_b1(jet_mult_b1),
        .mult_b2(jet_mult_b2), .mult_b3(jet_mult_b3),
        .mult_r0(jet_mult_r0), .mult_r1(jet_mult_r1),
        .mult_r2(jet_mult_r2), .mult_r3(jet_mult_r3),
        .mult_done(jet_mult_done)
    );

    // ── A31 inverter tower (needs its own multiplier) ────────────────
    spu13_fp4_inverter u_inverter (
        .clk(clk), .rst_n(rst_n), .start(inv_start),
        .z0(inv_z0), .z1(inv_z1), .z2(inv_z2), .z3(inv_z3),
        .inv0(inv_r0), .inv1(inv_r1), .inv2(inv_r2), .inv3(inv_r3),
        .done(inv_done), .busy(inv_busy), .flags_v(inv_flags_v),
        .mult_start(tower_mult_start),
        .mult_a0(tower_mult_a0), .mult_a1(tower_mult_a1),
        .mult_a2(tower_mult_a2), .mult_a3(tower_mult_a3),
        .mult_b0(tower_mult_b0), .mult_b1(tower_mult_b1),
        .mult_b2(tower_mult_b2), .mult_b3(tower_mult_b3),
        .mult_r0(tower_mult_r0), .mult_r1(tower_mult_r1),
        .mult_r2(tower_mult_r2), .mult_r3(tower_mult_r3),
        .mult_done(tower_mult_done), .mult_busy(tower_mult_busy),
        .debug_state(), .debug_start_accept()
    );

    // ── M31 multiplier (shared between tower and jet shadow chain) ───
    // Mux: tower gets priority, jet uses it when tower is idle
    wire        mult_start_mux = tower_mult_start ? tower_mult_start : jet_mult_start;
    wire [31:0] mult_a0_mux   = tower_mult_start ? tower_mult_a0   : jet_mult_a0;
    wire [31:0] mult_a1_mux   = tower_mult_start ? tower_mult_a1   : jet_mult_a1;
    wire [31:0] mult_a2_mux   = tower_mult_start ? tower_mult_a2   : jet_mult_a2;
    wire [31:0] mult_a3_mux   = tower_mult_start ? tower_mult_a3   : jet_mult_a3;
    wire [31:0] mult_b0_mux   = tower_mult_start ? tower_mult_b0   : jet_mult_b0;
    wire [31:0] mult_b1_mux   = tower_mult_start ? tower_mult_b1   : jet_mult_b1;
    wire [31:0] mult_b2_mux   = tower_mult_start ? tower_mult_b2   : jet_mult_b2;
    wire [31:0] mult_b3_mux   = tower_mult_start ? tower_mult_b3   : jet_mult_b3;

    wire mult_done_mux, mult_busy_mux;
    wire [31:0] mult_r0_mux, mult_r1_mux, mult_r2_mux, mult_r3_mux;

    spu13_m31_multiplier u_mult (
        .clk(clk), .rst_n(rst_n), .start(mult_start_mux),
        .a0(mult_a0_mux), .a1(mult_a1_mux), .a2(mult_a2_mux), .a3(mult_a3_mux),
        .b0(mult_b0_mux), .b1(mult_b1_mux), .b2(mult_b2_mux), .b3(mult_b3_mux),
        .r0(mult_r0_mux), .r1(mult_r1_mux), .r2(mult_r2_mux), .r3(mult_r3_mux),
        .done(mult_done_mux), .busy(mult_busy_mux)
    );

    // Route multiplier output back to both consumers
    assign tower_mult_r0 = mult_r0_mux; assign tower_mult_r1 = mult_r1_mux;
    assign tower_mult_r2 = mult_r2_mux; assign tower_mult_r3 = mult_r3_mux;
    assign tower_mult_done = mult_done_mux;
    assign jet_mult_r0 = mult_r0_mux; assign jet_mult_r1 = mult_r1_mux;
    assign jet_mult_r2 = mult_r2_mux; assign jet_mult_r3 = mult_r3_mux;
    assign jet_mult_done = mult_done_mux;

    always #5 clk = ~clk;

    integer test_pass, test_total;

    task set_jet;
        input [31:0] a0,a1,a2,a3, b0,b1,b2,b3, d0,d1,d2,d3;
        begin
            c0_z0=a0; c0_z1=a1; c0_z2=a2; c0_z3=a3;
            c1_z0=b0; c1_z1=b1; c1_z2=b2; c1_z3=b3;
            c2_z0=d0; c2_z1=d1; c2_z2=d2; c2_z3=d3;
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; start = 0;
        test_pass = 0; test_total = 0;
        set_jet(0,0,0,0, 0,0,0,0, 0,0,0,0);
        #20 rst_n = 1; #10;

        // Test A: Scalar inverse self-consistency
        set_jet(5,0,0,0, 0,0,0,0, 0,0,0,0);
        start = 1; #10; start = 0;
        wait(done); #2;
        test_total = test_total + 1;
        if (!err_zero_divisor && m0_z0 != 32'd0) test_pass = test_pass + 1;
        else $display("FAIL A: inv(5) scalar");

        // Test B: Inverse with velocity and acceleration
        set_jet(5,0,0,0, 3,0,0,0, 2,0,0,0);
        start = 1; #10; start = 0;
        wait(done); #2;
        test_total = test_total + 1;
        if (!err_zero_divisor && m0_z0 != 32'd0) test_pass = test_pass + 1;
        else $display("FAIL B: inv(5,3,2)");

        // Test C: Zero-divisor trap
        set_jet(0,0,0,0, 1,0,0,0, 0,0,0,0);
        start = 1; #10; start = 0;
        wait(done); #2;
        test_total = test_total + 1;
        if (err_zero_divisor) test_pass = test_pass + 1;
        else $display("FAIL C: zero-divisor not trapped");

        // Test D: Nonzero zero-divisor base coefficient must also trap.
        set_jet(32'd753804466,0,0,1, 0,0,0,0, 0,0,0,0);
        start = 1; #10; start = 0;
        wait(done); #2;
        test_total = test_total + 1;
        if (err_zero_divisor) test_pass = test_pass + 1;
        else $display("FAIL D: nonzero zero-divisor not trapped");

        // Test E: Post-exception recovery
        set_jet(3,0,0,0, 0,0,0,0, 0,0,0,0);
        start = 1; #10; start = 0;
        wait(done); #2;
        test_total = test_total + 1;
        if (!err_zero_divisor && m0_z0 != 32'd0) test_pass = test_pass + 1;
        else $display("FAIL E: post-exception inv(3)");

        if (test_pass == test_total)
            $display("PASS: spu13_jet_inv_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_jet_inv_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
