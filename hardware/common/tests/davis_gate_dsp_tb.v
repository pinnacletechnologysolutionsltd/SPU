// davis_gate_dsp_tb.v — Testbench: davis_gate_dsp (GOWIN / SIM)
// Verifies gasket_sum, quadrance, and q_rotated against known values.
// Uses DEVICE="SIM" — inferred multiply, no vendor primitives needed.
//
// Test vectors (A=4, B=3, C=2, D=1):
//   gasket_sum = 4+3+2+1         = 10         (combinational)
//   quadrance  = 16+3*9+4+1      = 16+27+4+1  = 48  (1-cycle DSP latency)
//   q_rotated  = {B,C,D,A}       = {3,2,1,4}

`timescale 1ns/1ps

module davis_gate_dsp_tb;

    reg         clk   = 0;
    reg         rst_n = 0;
    reg  [63:0] q_in  = 0;

    wire [63:0] q_rot;
    wire [31:0] quad;
    wire [15:0] gsum;

    davis_gate_dsp #(.DEVICE("SIM")) u_dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .q_vector  (q_in),
        .q_rotated (q_rot),
        .quadrance (quad),
        .gasket_sum(gsum)
    );

    always #10 clk = ~clk;  // 50 MHz

    integer fail = 0;

    task check;
        input [31:0]  got;
        input [31:0]  exp;
        input [127:0] name;
        begin
            if (got !== exp) begin
                $display("FAIL: %s  got=%0d  exp=%0d", name, got, exp);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        // Release reset
        @(posedge clk); rst_n = 1;

        // ── Test 1: A=4, B=3, C=2, D=1 ──────────────────────────────── //
        q_in = {16'd4, 16'd3, 16'd2, 16'd1};
        @(posedge clk);

        // gasket_sum and q_rotated are combinational — valid immediately
        check(gsum,         16'd10,  "T1 gasket_sum");
        check(q_rot[63:48], 16'd3,   "T1 rot[A]=B");
        check(q_rot[47:32], 16'd2,   "T1 rot[B]=C");
        check(q_rot[31:16], 16'd1,   "T1 rot[C]=D");
        check(q_rot[15:0],  16'd4,   "T1 rot[D]=A");

        // quadrance has 1-cycle DSP latency — sample after next edge
        @(posedge clk);
        check(quad, 32'd48, "T1 quadrance"); // 16+27+4+1=48

        // ── Test 2: A=0, B=0, C=0, D=0 (zero vector) ────────────────── //
        q_in = 64'h0;
        @(posedge clk);
        check(gsum, 16'd0, "T2 gasket_sum=0");
        @(posedge clk);
        check(quad, 32'd0, "T2 quadrance=0");

        // ── Test 3: A=100, B=0, C=0, D=0 ─────────────────────────────  //
        q_in = {16'd100, 48'h0};
        @(posedge clk);
        check(gsum, 16'd100, "T3 gasket_sum");
        @(posedge clk);
        check(quad, 32'd10000, "T3 quadrance=100^2");

        // ── Test 4: Basis rotation twice = {C,D,A,B} ─────────────────  //
        q_in = {16'd1, 16'd2, 16'd3, 16'd4};
        @(posedge clk);
        check(q_rot[63:48], 16'd2, "T4 rot[0]");
        check(q_rot[47:32], 16'd3, "T4 rot[1]");
        check(q_rot[31:16], 16'd4, "T4 rot[2]");
        check(q_rot[15:0],  16'd1, "T4 rot[3]");

        // ── Report ────────────────────────────────────────────────────  //
        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);

        $finish;
    end

endmodule
