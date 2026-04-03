// SPU-13 Surd Multiplier Core (v2.9.22)
// Implements (a1 + b1*sqrt3) * (a2 + b2*sqrt3)
// Logic: (a1*a2 + 3*b1*b2) + (a1*b2 + b1*a2)*sqrt3

module spu_smul #(
    parameter BIT_WIDTH = 32
)(
    input  wire signed [BIT_WIDTH-1:0] a1, b1,
    input  wire signed [BIT_WIDTH-1:0] a2, b2,
    output wire signed [BIT_WIDTH-1:0] res_a, // Resulting Rational
    output wire signed [BIT_WIDTH-1:0] res_b  // Resulting Irrational (sqrt3)
);

    // 1. Cross-Product Intermediates (64-bit to prevent overflow)
    wire signed [63:0] aa = a1 * a2;
    wire signed [63:0] bb = b1 * b2;
    wire signed [63:0] ab = a1 * b2;
    wire signed [63:0] ba = b1 * a2;

    // 2. Surd Term (3*bb)
    // Fast shift-adder implementation: (bb << 1) + bb
    wire signed [63:0] surd_term = (bb << 1) + bb;

    // 3. Final Summation and Normalization (16-bit shift for fixed-point)
    assign res_a = (aa + surd_term) >>> 16;
    assign res_b = (ab + ba) >>> 16;

endmodule
