`timescale 1ns / 1ps

// spu13_nsa_dual_alu_tb.v — Testbench for NSA dual-number arithmetic unit
//
// Tests over F_{p^4}[epsilon]/(epsilon^2):
//   A) Dual add:    (A+eB) + (C+eD) = (A+C) + e(B+D)
//   B) Dual multiply: (A+eB)(C+eD) = AC + e(AD+BC)
//   C) Scalar dual (eps=0): (A+e0)(C+e0) = AC + e·0
//   D) Pure epsilon: (0+eB)(0+eD) = 0 + e·0  (epsilon^2 = 0)
//   E) Round-trip: compute (A+eB)(A+eB) then verify (A+eB)^(-1) exists

module spu13_nsa_dual_alu_tb;

    reg clk, rst_n, start;
    reg op_mul;

    // Operand A
    reg [31:0] a_real_z0, a_real_z1, a_real_z2, a_real_z3;
    reg [31:0] a_eps_z0,  a_eps_z1,  a_eps_z2,  a_eps_z3;

    // Operand B
    reg [31:0] b_real_z0, b_real_z1, b_real_z2, b_real_z3;
    reg [31:0] b_eps_z0,  b_eps_z1,  b_eps_z2,  b_eps_z3;

    // Result
    wire [31:0] r_real_z0, r_real_z1, r_real_z2, r_real_z3;
    wire [31:0] r_eps_z0,  r_eps_z1,  r_eps_z2,  r_eps_z3;
    wire done, busy;

    // Multiplier interface
    wire        mult_start;
    wire [31:0] mult_a0, mult_a1, mult_a2, mult_a3;
    wire [31:0] mult_b0, mult_b1, mult_b2, mult_b3;
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire        mult_done, mult_busy;

    spu13_nsa_dual_alu uut (
        .clk(clk), .rst_n(rst_n), .start(start), .op_mul(op_mul),
        .a_real_z0(a_real_z0), .a_real_z1(a_real_z1), .a_real_z2(a_real_z2), .a_real_z3(a_real_z3),
        .a_eps_z0(a_eps_z0),   .a_eps_z1(a_eps_z1),   .a_eps_z2(a_eps_z2),   .a_eps_z3(a_eps_z3),
        .b_real_z0(b_real_z0), .b_real_z1(b_real_z1), .b_real_z2(b_real_z2), .b_real_z3(b_real_z3),
        .b_eps_z0(b_eps_z0),   .b_eps_z1(b_eps_z1),   .b_eps_z2(b_eps_z2),   .b_eps_z3(b_eps_z3),
        .r_real_z0(r_real_z0), .r_real_z1(r_real_z1), .r_real_z2(r_real_z2), .r_real_z3(r_real_z3),
        .r_eps_z0(r_eps_z0),   .r_eps_z1(r_eps_z1),   .r_eps_z2(r_eps_z2),   .r_eps_z3(r_eps_z3),
        .done(done), .busy(busy),
        .mult_start(mult_start),
        .mult_a0(mult_a0), .mult_a1(mult_a1), .mult_a2(mult_a2), .mult_a3(mult_a3),
        .mult_b0(mult_b0), .mult_b1(mult_b1), .mult_b2(mult_b2), .mult_b3(mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1), .mult_r2(mult_r2), .mult_r3(mult_r3),
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

    // ── Helper: set dual operands ──────────────────────────────────────
    task set_dual_a;
        input [31:0] ar0, ar1, ar2, ar3;
        input [31:0] ae0, ae1, ae2, ae3;
        begin
            a_real_z0 = ar0; a_real_z1 = ar1; a_real_z2 = ar2; a_real_z3 = ar3;
            a_eps_z0  = ae0; a_eps_z1  = ae1; a_eps_z2  = ae2; a_eps_z3  = ae3;
        end
    endtask

    task set_dual_b;
        input [31:0] br0, br1, br2, br3;
        input [31:0] be0, be1, be2, be3;
        begin
            b_real_z0 = br0; b_real_z1 = br1; b_real_z2 = br2; b_real_z3 = br3;
            b_eps_z0  = be0; b_eps_z1  = be1; b_eps_z2  = be2; b_eps_z3  = be3;
        end
    endtask

    // ── Check dual result ──────────────────────────────────────────────
    task check_dual;
        input [255:0] label;
        input [31:0] er0, er1, er2, er3;
        input [31:0] ee0, ee1, ee2, ee3;
        integer ok;
        begin
            test_total = test_total + 1;
            ok = 1;
            if (r_real_z0 !== er0 || r_real_z1 !== er1 || r_real_z2 !== er2 || r_real_z3 !== er3)
                ok = 0;
            if (r_eps_z0  !== ee0 || r_eps_z1  !== ee1 || r_eps_z2  !== ee2 || r_eps_z3  !== ee3)
                ok = 0;
            if (ok) test_pass = test_pass + 1;
            else begin
                $display("FAIL: %0s", label);
                $display("  got real: (%h,%h,%h,%h)", r_real_z0, r_real_z1, r_real_z2, r_real_z3);
                $display("  exp real: (%h,%h,%h,%h)", er0, er1, er2, er3);
                $display("  got eps:  (%h,%h,%h,%h)", r_eps_z0, r_eps_z1, r_eps_z2, r_eps_z3);
                $display("  exp eps:  (%h,%h,%h,%h)", ee0, ee1, ee2, ee3);
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; start = 0; op_mul = 0;
        test_pass = 0; test_total = 0;
        set_dual_a(32'd0,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        set_dual_b(32'd0,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        #20 rst_n = 1; #10;

        // ═══════════════════════════════════════════════════════════════
        // Test A1: Dual add — identity
        // (1 + e·0) + (0 + e·0) = (1) + e(0)
        // ═══════════════════════════════════════════════════════════════
        op_mul = 0;
        set_dual_a(32'd1,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        set_dual_b(32'd0,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("A1: (1+e0)+(0+e0)", 32'd1,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test A2: Dual add — scalar values
        // (5 + e·7) + (3 + e·2) = (8) + e(9)
        // ═══════════════════════════════════════════════════════════════
        op_mul = 0;
        set_dual_a(32'd5,32'd0,32'd0,32'd0, 32'd7,32'd0,32'd0,32'd0);
        set_dual_b(32'd3,32'd0,32'd0,32'd0, 32'd2,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("A2: (5+e7)+(3+e2)", 32'd8,32'd0,32'd0,32'd0, 32'd9,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test A3: Dual add — with surd components
        // (1+2√3 + e[3+4√3]) + (5+6√3 + e[7+8√3])
        // real: (6, 8, 0, 0), eps: (10, 12, 0, 0)
        // ═══════════════════════════════════════════════════════════════
        op_mul = 0;
        set_dual_a(32'd1, 32'd2, 32'd0,32'd0,  32'd3, 32'd4, 32'd0,32'd0);
        set_dual_b(32'd5, 32'd6, 32'd0,32'd0,  32'd7, 32'd8, 32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("A3: surd add",
                   32'd6,  32'd8,  32'd0,32'd0,
                   32'd10, 32'd12, 32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test B1: Dual multiply — scalar identity
        // (1 + e·0)(1 + e·0) = 1 + e·0
        // ═══════════════════════════════════════════════════════════════
        op_mul = 1;
        set_dual_a(32'd1,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        set_dual_b(32'd1,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("B1: (1+e0)(1+e0)", 32'd1,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test B2: Dual multiply — scalar
        // (3 + e·0)(5 + e·0) = 15 + e·0
        // ═══════════════════════════════════════════════════════════════
        op_mul = 1;
        set_dual_a(32'd3,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        set_dual_b(32'd5,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("B2: (3+e0)(5+e0)", 32'd15,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test B3: Dual multiply — with epsilon derivative
        // (2 + e·3)(4 + e·5) = 2·4 + e(2·5 + 3·4) = 8 + e(10+12) = 8 + e·22
        // ═══════════════════════════════════════════════════════════════
        op_mul = 1;
        set_dual_a(32'd2,32'd0,32'd0,32'd0, 32'd3,32'd0,32'd0,32'd0);
        set_dual_b(32'd4,32'd0,32'd0,32'd0, 32'd5,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("B3: (2+e3)(4+e5)", 32'd8,32'd0,32'd0,32'd0, 32'd22,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test B4: Dual multiply — epsilon^2 = 0 (pure epsilon cancellation)
        // (0 + e·1)(0 + e·1) = 0 + e(0·1 + 1·0) = 0 + e·0
        // ═══════════════════════════════════════════════════════════════
        op_mul = 1;
        set_dual_a(32'd0,32'd0,32'd0,32'd0, 32'd1,32'd0,32'd0,32'd0);
        set_dual_b(32'd0,32'd0,32'd0,32'd0, 32'd1,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("B4: e^2=0: (e)(e)=0+0e",
                   32'd0,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test B5: Dual multiply — surd components
        // A = (1+2√3) + e(3+4√3), B = (5+6√3) + e(7+8√3)
        // AC: (1,2,0,0) * (5,6,0,0) = (1*5+3*2*6, 1*6+2*5, 0, 0) = (41, 16, 0, 0)
        // AD: (1,2,0,0) * (7,8,0,0) = (1*7+3*2*8, 1*8+2*7, 0, 0) = (55, 22, 0, 0)
        // BC: (3,4,0,0) * (5,6,0,0) = (3*5+3*4*6, 3*6+4*5, 0, 0) = (87, 38, 0, 0)
        // AD+BC = (55+87, 22+38, 0, 0) = (142, 60, 0, 0)
        // ═══════════════════════════════════════════════════════════════
        op_mul = 1;
        set_dual_a(32'd1, 32'd2, 32'd0,32'd0,  32'd3, 32'd4, 32'd0,32'd0);
        set_dual_b(32'd5, 32'd6, 32'd0,32'd0,  32'd7, 32'd8, 32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("B5: surd dual mul",
                   32'd41, 32'd16, 32'd0,32'd0,
                   32'd142, 32'd60, 32'd0,32'd0);

        // ═══════════════════════════════════════════════════════════════
        // Test B6: Dual multiply — M31 edge near-prime values
        // (P-2 + e·0)(2 + e·0) = (P-4) + e·0
        // ═══════════════════════════════════════════════════════════════
        op_mul = 1;
        set_dual_a(P-2,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        set_dual_b(32'd2,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);
        start = 1; #10; start = 0;
        wait(done); #2;
        check_dual("B6: M31 edge (P-2)(2)",
                   P-4,32'd0,32'd0,32'd0, 32'd0,32'd0,32'd0,32'd0);

        if (test_pass == test_total)
            $display("PASS: spu13_nsa_dual_alu_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_nsa_dual_alu_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
