`timescale 1ns/1ps

// spu_davis_gate.v
// The Davis Law Gasket (v1.3 - Pulse-Locked Stability Arbiter)
// Objective: Monitor Lattice Tension via Quadrance Summation.
// Field: Rational Field Q(sqrt3).

module spu_davis_gate #(
    parameter [63:0] TAU_Q = 64'h0000_1000_0000_0000 // Fixed-point stability limit
)(
    input  wire        clk,
    input  wire        rst_n,
    
    // 64-bit Chord (Input axis)
    // Consists of 4x 16-bit RationalSurd (p, q) pairs or 4x 16-bit Quadray elements
    input  wire [63:0] chord_in,
    
    output wire        over_curvature,
    output wire [63:0] quadrance_sum
);

    // 1. Unpack Chord into 4x 16-bit elements
    wire signed [15:0] a;
    assign a = chord_in[63:48];
    wire signed [15:0] b;
    assign b = chord_in[47:32];
    wire signed [15:0] c;
    assign c = chord_in[31:16];
    wire signed [15:0] d;
    assign d = chord_in[15:0];

    // 2. Algebraic Quadrance: Q = A^2 + B^2 + C^2 + D^2
    // These will be inferred as DSP slices on iCE40/ECP5.
    wire [31:0] qa;
    assign qa = a * a;
    wire [31:0] qb;
    assign qb = b * b;
    wire [31:0] qc;
    assign qc = c * c;
    wire [31:0] qd;
    assign qd = d * d;

    wire [63:0] q_sum;
    assign q_sum = (qa + qb) + (qc + qd);

    // 3. The Davis Limit Arbiter
    // Bitwise comparison for zero-branch "Laminar" failure detection.
    assign over_curvature = (q_sum > TAU_Q[31:0]); // Using 32-bit comparison for 16-bit inputs
    assign quadrance_sum  = {32'h0, q_sum};

endmodule
