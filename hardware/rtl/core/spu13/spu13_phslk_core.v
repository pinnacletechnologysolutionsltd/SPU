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
//
// Non-unit detection is a registered 3-stage pipeline (o₀ and c₀ fed on
// consecutive cycles), overlapped with the jet MAC run — it settles by
// cycle ~5, so it adds no latency; `done` is gated on its completion in
// case a future MAC ever finishes first. Evaluating the norm's depth-3
// multiply cascade combinationally would cap Fmax below the 50 MHz board
// clocks; one multiply level per clocked stage keeps timing clean.

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

    // ── Non-unit detection — registered 3-stage norm pipeline ────────
    // N(z) = (z0² + 3z1² − 5z2² − 15z3²)² − 3·(2·z0z1 − 5·2·z2z3)²
    // Stage 1: six full 32×32 products of the muxed operand.
    // Stage 2: fold to the F_p(√3) pair (d0, d1) — small scales only.
    // Stage 3: two squaring products, final subtract, exact zero test.
    // Operands are fed o₀ then c₀ on consecutive cycles; both verdicts
    // are registered by cycle ~5 while the jet MAC is still running.

    reg  [1:0]  feed;                        // feed[0]: o₀ this cycle, feed[1]: c₀
    wire [31:0] f_z0 = feed[0] ? o0_z0 : c0_z0;
    wire [31:0] f_z1 = feed[0] ? o0_z1 : c0_z1;
    wire [31:0] f_z2 = feed[0] ? o0_z2 : c0_z2;
    wire [31:0] f_z3 = feed[0] ? o0_z3 : c0_z3;

    reg         s1_v, s1_sel;                // sel: 0 = o₀, 1 = c₀
    reg  [31:0] s1_z0sq, s1_z1sq, s1_z2sq, s1_z3sq, s1_z0z1, s1_z2z3;
    reg         s2_v, s2_sel;
    reg  [31:0] s2_d0, s2_d1;
    reg         ez_o, ez_c, ez_o_v, ez_c_v;
    reg         mac_seen, fired, done_r;

    wire [31:0] norm_w = m31_sub(m31_mul(s2_d0, s2_d0),
                                 m31_mul_small(m31_mul(s2_d1, s2_d1), 4'd3));
    wire        nonunit_w = (norm_w == 32'd0);
    wire        ez_ready  = ez_o_v && ez_c_v;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            feed   <= 2'b00;
            s1_v   <= 1'b0;  s1_sel <= 1'b0;
            s2_v   <= 1'b0;  s2_sel <= 1'b0;
            ez_o   <= 1'b0;  ez_c   <= 1'b0;
            ez_o_v <= 1'b0;  ez_c_v <= 1'b0;
            mac_seen <= 1'b0; fired <= 1'b0; done_r <= 1'b0;
        end else begin
            done_r <= 1'b0;

            if (start) begin
                feed   <= 2'b01;
                ez_o_v <= 1'b0;  ez_c_v <= 1'b0;
                mac_seen <= 1'b0; fired <= 1'b0;
                s1_v <= 1'b0;    s2_v <= 1'b0;
            end else begin
                feed <= {feed[0], 1'b0};

                // Stage 1
                s1_v   <= |feed;
                s1_sel <= feed[1];
                if (|feed) begin
                    s1_z0sq <= m31_mul(f_z0, f_z0);
                    s1_z1sq <= m31_mul(f_z1, f_z1);
                    s1_z2sq <= m31_mul(f_z2, f_z2);
                    s1_z3sq <= m31_mul(f_z3, f_z3);
                    s1_z0z1 <= m31_mul(f_z0, f_z1);
                    s1_z2z3 <= m31_mul(f_z2, f_z3);
                end

                // Stage 2
                s2_v   <= s1_v;
                s2_sel <= s1_sel;
                if (s1_v) begin
                    s2_d0 <= m31_sub(m31_add(s1_z0sq, m31_mul_small(s1_z1sq, 4'd3)),
                                     m31_mul_small(m31_add(s1_z2sq, m31_mul_small(s1_z3sq, 4'd3)), 4'd5));
                    s2_d1 <= m31_sub(m31_mul_small(s1_z0z1, 4'd2),
                                     m31_mul_small(m31_mul_small(s1_z2z3, 4'd2), 4'd5));
                end

                // Stage 3
                if (s2_v) begin
                    if (!s2_sel) begin ez_o <= nonunit_w; ez_o_v <= 1'b1; end
                    else         begin ez_c <= nonunit_w; ez_c_v <= 1'b1; end
                end
            end

            // Completion coupling: done fires once both the MAC and the
            // norm pipeline have finished (the MAC is the long pole today).
            if (mac_done) mac_seen <= 1'b1;
            if ((mac_seen || mac_done) && ez_ready && !fired) begin
                done_r <= 1'b1;
                fired  <= 1'b1;
            end
        end
    end

    assign err_zero_divisor = ez_o || ez_c;

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

    assign flag_c = done_r && lane0_ok && lane1_ok && lane2_ok && !err_zero_divisor;
    assign flag_v = !err_zero_divisor;
    assign done   = done_r;
    assign busy   = mac_busy || (feed != 2'b00) || s1_v || s2_v || (mac_seen && !fired);

endmodule
