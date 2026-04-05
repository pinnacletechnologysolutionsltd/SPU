// davis_gate_dsp_tb.v — Testbench: davis_gate_dsp v2.1
// Verifies gasket_sum, quadrance (stiffness), ivm_quadrance (pairwise), q_rotated.
// Uses DEVICE="SIM" — inferred multiply, no vendor primitives needed.
//
// Test vectors (A=4, B=3, C=2, D=1):
//   gasket_sum    = 4+3+2+1               = 10
//   quadrance     = 16+27+4+1             = 48   (A²+3B²+C²+D² stiffness)
//   ivm_quadrance = (4-3)²+(4-2)²+(4-1)²
//                 + (3-2)²+(3-1)²+(2-1)² = 1+4+9+1+4+1 = 20  (pairwise)
//   q_rotated     = {B,C,D,A}             = {3,2,1,4}

`timescale 1ns/1ps

module davis_gate_dsp_tb;

    reg         clk   = 0;
    reg         rst_n = 0;
    reg  [63:0] q_in  = 0;

    wire [63:0] q_rot;
    wire [31:0] quad;
    wire [31:0] ivm_quad;
    wire [15:0] gsum;

    davis_gate_dsp #(.DEVICE("SIM")) u_dut (
        .clk          (clk),
        .rst_n        (rst_n),
        .q_vector     (q_in),
        .q_rotated    (q_rot),
        .quadrance    (quad),
        .ivm_quadrance(ivm_quad),
        .gasket_sum   (gsum)
    );

    always #10 clk = ~clk;  // 50 MHz

    integer fail = 0;

    task check;
        input [31:0]  got;
        input [31:0]  exp;
        input [127:0] name;
        begin
            if (got !== exp) begin
                $display("FAIL: %0s  got=%0d  exp=%0d", name, got, exp);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        @(posedge clk); rst_n = 1;

        // ── Test 1: A=4, B=3, C=2, D=1 ──────────────────────────────── //
        q_in = {16'd4, 16'd3, 16'd2, 16'd1};
        @(posedge clk);
        check(gsum,         16'd10, "T1 gasket_sum");
        check(q_rot[63:48], 16'd3,  "T1 rot[A]=B");
        check(q_rot[47:32], 16'd2,  "T1 rot[B]=C");
        check(q_rot[31:16], 16'd1,  "T1 rot[C]=D");
        check(q_rot[15:0],  16'd4,  "T1 rot[D]=A");
        @(posedge clk);
        check(quad,      32'd48, "T1 quadrance stiffness");  // A²+3B²+C²+D²
        check(ivm_quad,  32'd20, "T1 ivm_quadrance pairwise"); // Σᵢ<ⱼ(cᵢ-cⱼ)²

        // ── Test 2: Zero vector ───────────────────────────────────────── //
        q_in = 64'h0;
        @(posedge clk);
        check(gsum, 16'd0, "T2 gasket_sum=0");
        @(posedge clk);
        check(quad,     32'd0, "T2 quadrance=0");
        check(ivm_quad, 32'd0, "T2 ivm_quadrance=0");

        // ── Test 3: A=100, others zero ────────────────────────────────── //
        q_in = {16'd100, 48'h0};
        @(posedge clk);
        check(gsum, 16'd100, "T3 gasket_sum");
        @(posedge clk);
        check(quad,     32'd10000, "T3 quadrance=100²");  // A²=10000, rest 0
        // ivm: (100-0)²×3 = 30000
        check(ivm_quad, 32'd30000, "T3 ivm_quadrance=3×100²");

        // ── Test 4: IVM canonical basis (1,0,0,0) ─────────────────────── //
        // C++ Quadray::quadrance() of (1,0,0,0) = 3
        q_in = {16'd1, 48'h0};
        @(posedge clk);
        @(posedge clk);
        check(ivm_quad, 32'd3, "T4 ivm_quadrance canonical (1,0,0,0)=3");

        // ── Test 5: IVM neighbour (1,1,0,0) ───────────────────────────── //
        // C++ Quadray::quadrance() of (1,1,0,0) = (1-1)²+(1-0)²+(1-0)²+(1-0)²+(1-0)²+(0-0)² = 0+1+1+1+1+0 = 4
        q_in = {16'd1, 16'd1, 32'h0};
        @(posedge clk);
        @(posedge clk);
        check(ivm_quad, 32'd4, "T5 ivm_quadrance (1,1,0,0)=4");

        // ── Test 6: Rotation twice gives {C,D,A,B} ────────────────────── //
        q_in = {16'd1, 16'd2, 16'd3, 16'd4};
        @(posedge clk);
        check(q_rot[63:48], 16'd2, "T6 rot[0]");
        check(q_rot[47:32], 16'd3, "T6 rot[1]");
        check(q_rot[31:16], 16'd4, "T6 rot[2]");
        check(q_rot[15:0],  16'd1, "T6 rot[3]");

        // ── Report ─────────────────────────────────────────────────────── //
        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

endmodule
