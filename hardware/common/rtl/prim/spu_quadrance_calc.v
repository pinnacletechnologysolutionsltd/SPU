// SPU-13 Quadrance Calculator (v1.1 DSP-Optimized)
// Objective: Efficient distance calculation using SB_MAC16.
// Formula: Q = (a^2 + b^2 + c^2 + d^2) / 2

module quadrance_calc (
    input  wire signed [15:0] a, b, c, d,
    output wire [31:0] q_out 
);
    // These 16x16 multipliers fit exactly into the UP5K DSP slices.
    wire signed [31:0] sq_a;
    assign sq_a = a * a;
    wire signed [31:0] sq_b;
    assign sq_b = b * b;
    wire signed [31:0] sq_c;
    assign sq_c = c * c;
    wire signed [31:0] sq_d;
    assign sq_d = d * d;

    assign q_out = (sq_a + sq_b + sq_c + sq_d) >> 1; 
endmodule
