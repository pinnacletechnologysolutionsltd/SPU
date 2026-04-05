// spu_triple_spread.v — Wildberger Triple Spread Law identity gate (v1.0)
// Checks if three rational Spread values s1, s2, s3 satisfy:
//   (s1+s2+s3)² == 2(s1²+s2²+s3²) + 4·s1·s2·s3
// where each si = si_n / d  (common denominator form, no division needed).
//
// Substituting si = si_n/d and clearing d³:
//   d·(Σsi_n)² == 2d·(Σsi_n²) + 4·Πsi_n
//
// This is the Fresnel link — holds for physically valid spread triangles
// on an IVM lattice (e.g. equilateral s=3/4, glass-air s=(3/4,1/4,1)).
//
// Inputs:  s1_n, s2_n, s3_n — 16-bit spread numerators
//          d                — 16-bit common denominator
// Output:  valid            — 1 if Triple Spread identity holds
//
// Purely combinational. Uses 64-bit intermediate to avoid overflow.
// CC0 1.0 Universal.

module spu_triple_spread (
    input  wire [15:0] s1_n,
    input  wire [15:0] s2_n,
    input  wire [15:0] s3_n,
    input  wire [15:0] d,
    output wire        valid
);

    wire [63:0] n1 = {48'h0, s1_n};
    wire [63:0] n2 = {48'h0, s2_n};
    wire [63:0] n3 = {48'h0, s3_n};
    wire [63:0] dd = {48'h0, d};

    wire [63:0] sum_n    = n1 + n2 + n3;
    wire [63:0] sum_n_sq = sum_n * sum_n;                      // (Σsi_n)²
    wire [63:0] sum_sq   = n1*n1 + n2*n2 + n3*n3;             // Σsi_n²
    wire [63:0] prod     = n1 * n2 * n3;                       // Πsi_n

    wire [63:0] lhs = dd * sum_n_sq;                           // d·(Σsi_n)²
    wire [63:0] rhs = (dd * sum_sq << 1) + (prod << 2);        // 2d·Σsi_n² + 4Πsi_n

    assign valid = (lhs == rhs);

endmodule
