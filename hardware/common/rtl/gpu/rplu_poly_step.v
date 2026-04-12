// rplu_poly_step.v
// Single Horner "POLY_STEP" combinational helper used by RPLU pipelines.
// Computes: acc_out = (acc_in * x_q32) >>> 32 + coef_q32
// NOTE: This is a simulation-friendly, fully-combinational implementation.
// It is guarded by USE_LOCAL_POLY in callers so default behaviour is unchanged.

`timescale 1ns / 1ps
module rplu_poly_step(
    input  wire signed [127:0] acc_in,
    input  wire signed [63:0]  x_q32,
    input  wire signed [63:0]  coef_q32,
    output wire signed [127:0] acc_out
);

    // Full-width product (128 * 64 => 192 bits)
    wire signed [191:0] prod = acc_in * x_q32;
    // Arithmetic shift right by 32 to align Q32 multiply result
    wire signed [159:0] shifted = prod >>> 32;
    // Sign-extend coef (64 -> 160) to match shifted width for correct addition
    wire signed [159:0] coef_ext = {{96{coef_q32[63]}}, coef_q32};
    wire signed [159:0] sum160 = shifted + coef_ext;

    // Truncate/pack to 128-bit accumulator width (matches existing acc width in RPLU)
    assign acc_out = sum160[127:0];

endmodule
