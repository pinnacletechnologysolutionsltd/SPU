`timescale 1ns / 1ps

// spu13_phslk_core.v — PHSLK Predicate: Wheeler-Feynman Phase-Lock Coherence Check
//
// Semantics: For Offer jet O = (o₀, o₁, o₂) and Confirmation jet C = (c₀, c₁, c₂),
// coherence is defined as O·C ≡ (1, 0, 0) in A_SPU = A31[ε]/(ε³).
//
// Decomposed into three lane checks:
//   Lane 0 (ε⁰): o₀·c₀ ≡ 1   → base identity
//   Lane 1 (ε¹): o₀·c₁ + o₁·c₀ ≡ 0  → velocity cancellation
//   Lane 2 (ε²): o₀·c₂ + o₁·c₁ + o₂·c₀ ≡ 0  → acceleration cancellation
//
// FLAGS:
//   FLAGS.C = 1  → all three lanes match identity → coherent (JC branch)
//   FLAGS.V = 0  → valid inversion path
//   err_zero_divisor = 1  → o₀ or c₀ is a non-unit in A31
//
// Latency: ~12 cycles (6 multiplies cascaded through shared M31 multiplier).
// With dedicated DSP banks (Wukong): 3-4 cycles achievable.

module spu13_phslk_core (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // ── Offer jet O = (o₀, o₁, o₂) ─────────────────────────────────
    input  wire [31:0]  o0_z0, o0_z1, o0_z2, o0_z3,
    input  wire [31:0]  o1_z0, o1_z1, o1_z2, o1_z3,
    input  wire [31:0]  o2_z0, o2_z1, o2_z2, o2_z3,

    // ── Confirmation jet C = (c₀, c₁, c₂) ──────────────────────────
    input  wire [31:0]  c0_z0, c0_z1, c0_z2, c0_z3,
    input  wire [31:0]  c1_z0, c1_z1, c1_z2, c1_z3,
    input  wire [31:0]  c2_z0, c2_z1, c2_z2, c2_z3,

    // ── Flags ──────────────────────────────────────────────────────
    output wire         flag_c,         // Coherent: O·C ≡ (1,0,0)
    output wire         flag_v,         // Valid: O is invertible (o₀≠0)
    output wire         err_zero_divisor,
    output wire         done,
    output wire         busy,

    // ── Shared M31 multiplier interface ─────────────────────────────
    output wire         mult_start,
    output wire [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output wire [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done
);

    localparam [31:0] P = 32'h7FFFFFFF;

    function [31:0] m31_reduce_72;
        input [71:0] z;
        reg [33:0] chunk0, chunk1, chunk2, sum_all;
        begin
            chunk0  = {3'd0, z[30:0]};
            chunk1  = {3'd0, z[61:31]};
            chunk2  = {24'd0, z[71:62]};
            sum_all = chunk0 + chunk1 + chunk2;
            if (sum_all >= P) sum_all = sum_all - P;
            if (sum_all >= P) sum_all = sum_all - P;
            m31_reduce_72 = sum_all[31:0];
        end
    endfunction

    function [31:0] m31_add;
        input [31:0] x, y;
        reg [32:0] sum;
        begin
            sum = {1'b0, x} + {1'b0, y};
            m31_add = (sum >= P) ? (sum - P) : sum[31:0];
        end
    endfunction

    function [31:0] m31_sub;
        input [31:0] x, y;
        begin
            m31_sub = (x >= y) ? (x - y) : (x + P - y);
        end
    endfunction

    function [31:0] m31_mul;
        input [31:0] x, y;
        reg [63:0] product;
        begin
            product = {32'd0, x} * {32'd0, y};
            m31_mul = m31_reduce_72({8'd0, product});
        end
    endfunction

    function [31:0] m31_mul_small;
        input [31:0] x;
        input [3:0] scale;
        reg [71:0] product;
        begin
            product = {40'd0, x} * scale;
            m31_mul_small = m31_reduce_72(product);
        end
    endfunction

    function is_nonunit_a31;
        input [31:0] z0, z1, z2, z3;
        reg [31:0] z0_sq, z1_sq, z2_sq, z3_sq;
        reg [31:0] a2_0, a2_1, b2_0, b2_1;
        reg [31:0] d0, d1;
        reg [31:0] d0_sq, d1_sq3;
        reg [31:0] norm_n;
        begin
            z0_sq = m31_mul(z0, z0);
            z1_sq = m31_mul(z1, z1);
            z2_sq = m31_mul(z2, z2);
            z3_sq = m31_mul(z3, z3);

            a2_0 = m31_add(z0_sq, m31_mul_small(z1_sq, 4'd3));
            a2_1 = m31_mul_small(m31_mul(z0, z1), 4'd2);
            b2_0 = m31_add(z2_sq, m31_mul_small(z3_sq, 4'd3));
            b2_1 = m31_mul_small(m31_mul(z2, z3), 4'd2);

            d0 = m31_sub(a2_0, m31_mul_small(b2_0, 4'd5));
            d1 = m31_sub(a2_1, m31_mul_small(b2_1, 4'd5));

            d0_sq = m31_mul(d0, d0);
            d1_sq3 = m31_mul_small(m31_mul(d1, d1), 4'd3);
            norm_n = m31_sub(d0_sq, d1_sq3);
            is_nonunit_a31 = (norm_n == 32'd0);
        end
    endfunction

    // ── Jet MAC instance for O·C ────────────────────────────────────
    wire [31:0] r0_z0, r0_z1, r0_z2, r0_z3;
    wire [31:0] r1_z0, r1_z1, r1_z2, r1_z3;
    wire [31:0] r2_z0, r2_z1, r2_z2, r2_z3;
    wire mac_done, mac_busy;
    wire mac_ez_unused;  // jet MAC err_zero_divisor not used in multiply path

    spu13_jet_mac #(.N(2)) u_mac (
        .clk(clk), .rst_n(rst_n), .start(start), .op_mul(1'b1),
        .j_coeff('{'{o0_z0,o0_z1,o0_z2,o0_z3},
                    '{o1_z0,o1_z1,o1_z2,o1_z3},
                    '{o2_z0,o2_z1,o2_z2,o2_z3}}),
        .k_coeff('{'{c0_z0,c0_z1,c0_z2,c0_z3},
                    '{c1_z0,c1_z1,c1_z2,c1_z3},
                    '{c2_z0,c2_z1,c2_z2,c2_z3}}),
        .r_coeff('{'{r0_z0,r0_z1,r0_z2,r0_z3},
                    '{r1_z0,r1_z1,r1_z2,r1_z3},
                    '{r2_z0,r2_z1,r2_z2,r2_z3}}),
        .done(mac_done), .busy(mac_busy), .err_zero_divisor(mac_ez_unused),
        .mult_start(mult_start),
        .mult_a0(mult_a0), .mult_a1(mult_a1), .mult_a2(mult_a2), .mult_a3(mult_a3),
        .mult_b0(mult_b0), .mult_b1(mult_b1), .mult_b2(mult_b2), .mult_b3(mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1), .mult_r2(mult_r2), .mult_r3(mult_r3),
        .mult_done(mult_done)
    );

    // ── Non-unit detection (combinational, before MAC) ───────────────
    assign err_zero_divisor = is_nonunit_a31(o0_z0, o0_z1, o0_z2, o0_z3) ||
                              is_nonunit_a31(c0_z0, c0_z1, c0_z2, c0_z3);

    // ── Identity comparison (combinational, after mac_done) ─────────
    // Lane 0: must equal (1, 0, 0, 0)
    wire lane0_ok = (r0_z0 == 32'd1) && (r0_z1 == 32'd0) &&
                    (r0_z2 == 32'd0) && (r0_z3 == 32'd0);
    // Lane 1: must equal (0, 0, 0, 0)
    wire lane1_ok = (r1_z0 == 32'd0) && (r1_z1 == 32'd0) &&
                    (r1_z2 == 32'd0) && (r1_z3 == 32'd0);
    // Lane 2: must equal (0, 0, 0, 0)
    wire lane2_ok = (r2_z0 == 32'd0) && (r2_z1 == 32'd0) &&
                    (r2_z2 == 32'd0) && (r2_z3 == 32'd0);

    assign flag_c = mac_done && lane0_ok && lane1_ok && lane2_ok && !err_zero_divisor;
    assign flag_v = !err_zero_divisor;
    assign done   = mac_done;
    assign busy   = mac_busy;

endmodule
