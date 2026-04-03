`ifndef SQR_PARAMS_VH
`define SQR_PARAMS_VH

// sqr_params.vh
// Exact Rational Coefficients for Tetrahedral Rotation
// Derived from Thomson SQR v3.1 (Feb 2026)
// Scaling: Q12 (1.0 = 16'h1000)
// Note: uses `define so this file can be included at any scope.

// 120-Degree Rotation (Pure Permutation)
`define SQR_120_F 16'h0000
`define SQR_120_G 16'h1000
`define SQR_120_H 16'h0000

// 60-Degree Rotation (Rational SQR)
// F = 2/3, G = 2/3, H = -1/3
`define SQR_60_F 16'h0AAB
`define SQR_60_G 16'h0AAB
`define SQR_60_H 16'hFAAB

// 180-Degree Rotation (Janus Inversion)
// F = -1/3, G = 2/3, H = 2/3
`define SQR_180_F 16'hFAAB
`define SQR_180_G 16'h0AAB
`define SQR_180_H 16'h0AAB

// Identity
`define SQR_ID_F 16'h1000
`define SQR_ID_G 16'h0000
`define SQR_ID_H 16'h0000

`endif // SQR_PARAMS_VH

