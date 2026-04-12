// spu_triple_quad.v — Wildberger Triple Quad collinearity gate (v1.0)
// Checks if three Quadrances Q1, Q2, Q3 satisfy the collinearity identity:
//   (Q1+Q2+Q3)² == 2(Q1²+Q2²+Q3²)
// This holds if and only if three points are collinear in the rational field.
// NOTE: The +4Q1Q2Q3 term is for TANGENT CIRCLES (Descartes), NOT collinearity.
//
// Inputs:  Q1, Q2, Q3 — 32-bit unsigned Quadrance values (distance²)
// Outputs: collinear  — 1 if identity holds; tangent — 1 if Descartes holds
//
// Purely combinational — no clock, no DSP required at these widths.
// At Q=2^16 max, (Q1+Q2+Q3)² fits in 34+2=36 bits. Using 64-bit internally.
//
// CC0 1.0 Universal.

module spu_triple_quad (
    input  wire [31:0] Q1,
    input  wire [31:0] Q2,
    input  wire [31:0] Q3,
    output wire        collinear,  // (Q1+Q2+Q3)² == 2(Q1²+Q2²+Q3²)
    output wire        tangent     // (Q1+Q2+Q3)² == 2(Q1²+Q2²+Q3²) + 4Q1Q2Q3
);

    // Extend to 64-bit to avoid overflow
    wire [63:0] q1;
    assign q1 = {32'h0, Q1};
    wire [63:0] q2;
    assign q2 = {32'h0, Q2};
    wire [63:0] q3;
    assign q3 = {32'h0, Q3};

    wire [63:0] sum;
    assign sum = q1 + q2 + q3;
    wire [63:0] lhs       = sum * sum;                            // (Q1+Q2+Q3)²

    wire [63:0] rhs_sum2  = (q1*q1 + q2*q2 + q3*q3) << 1;       // 2(Q1²+Q2²+Q3²)
    wire [63:0] product   = q1 * q2 * q3;                         // Q1·Q2·Q3
    wire [63:0] rhs_tang  = rhs_sum2 + (product << 2);            // + 4Q1Q2Q3

    assign collinear = (lhs == rhs_sum2);
    assign tangent   = (lhs == rhs_tang);

endmodule
