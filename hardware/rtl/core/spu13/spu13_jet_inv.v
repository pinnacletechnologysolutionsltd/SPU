`timescale 1ns / 1ps

// spu13_jet_inv.v — Jet Inverse Re-assembly Pipeline
//
// Computes J⁻¹ for a jet J = c₀ + c₁·ε + c₂·ε² in A_SPU = GF(p⁴)[ε]/(ε³).
//
// Formula (geometric series for local rings):
//   J⁻¹ = c₀⁻¹  −  ε(c₁·c₀⁻²)  +  ε²(c₁²·c₀⁻³ − c₂·c₀⁻²)
//
// Pipeline:
//   1. Zero-divisor check: c₀=0 → assert err_zero_divisor, done immediately
//   2. Conjugate reduction tower: c₀⁻¹ (~76 cycles)
//   3. Shadow multiply chain: c₀⁻² → c₀⁻³ → c₁·c₀⁻² → c₁² → c₁²·c₀⁻³ → c₂·c₀⁻²
//   4. Reassembly: m₀=c₀⁻¹, m₁=−c₁·c₀⁻², m₂=c₁²·c₀⁻³−c₂·c₀⁻²
//
// Total latency: ~76 (tower) + ~18 (6 multiplies) = ~94 cycles.

module spu13_jet_inv (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // ── Input jet J = (c₀, c₁, c₂) ──────────────────────────────────
    input  wire [31:0]  c0_z0, c0_z1, c0_z2, c0_z3,
    input  wire [31:0]  c1_z0, c1_z1, c1_z2, c1_z3,
    input  wire [31:0]  c2_z0, c2_z1, c2_z2, c2_z3,

    // ── Output inverse J⁻¹ = (m₀, m₁, m₂) ──────────────────────────
    output reg  [31:0]  m0_z0, m0_z1, m0_z2, m0_z3,
    output reg  [31:0]  m1_z0, m1_z1, m1_z2, m1_z3,
    output reg  [31:0]  m2_z0, m2_z1, m2_z2, m2_z3,
    output reg          done,
    output wire         busy,
    output reg          err_zero_divisor,

    // ── F_{p^4} inverter interface ──────────────────────────────────
    output reg          inv_start,
    output reg  [31:0]  inv_z0,  inv_z1,  inv_z2,  inv_z3,
    input  wire [31:0]  inv_r0,  inv_r1,  inv_r2,  inv_r3,
    input  wire         inv_done, inv_busy,
    input  wire         inv_flags_v,

    // ── Shared M31 multiplier interface ─────────────────────────────
    output reg          mult_start,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done
);

    localparam P = 32'h7FFFFFFF;

    // ── FSM states ───────────────────────────────────────────────────
    localparam ST_IDLE        = 4'd0;
    localparam ST_TOWER_WAIT  = 4'd1;   // Waiting for c₀⁻¹ from tower
    localparam ST_MUL_LAUNCH  = 4'd2;   // Launch multiply, advance step
    localparam ST_MUL_WAIT    = 4'd3;   // Wait for multiplier
    localparam ST_COMBINE     = 4'd4;   // Compute m₁, m₂
    localparam ST_DONE        = 4'd5;

    reg [3:0] state;

    // ── Multiply step counter (0..5) ─────────────────────────────────
    // 0: c₀⁻² = m₀·m₀
    // 1: c₀⁻³ = c₀⁻²·m₀
    // 2: h1   = c₁·c₀⁻²
    // 3: c₁²  = c₁·c₁
    // 4: c₁²·c₀⁻³
    // 5: c₂·c₀⁻²
    reg [2:0] mul_step;

    // ── Pipeline registers ───────────────────────────────────────────
    reg [31:0] sq_r0, sq_r1, sq_r2, sq_r3;  // c₀⁻²
    reg [31:0] cu_r0, cu_r1, cu_r2, cu_r3;  // c₀⁻³
    reg [31:0] h1_r0, h1_r1, h1_r2, h1_r3;  // c₁·c₀⁻²
    reg [31:0] s1_r0, s1_r1, s1_r2, s1_r3;  // c₁²
    reg [31:0] t1_r0, t1_r1, t1_r2, t1_r3;  // c₁²·c₀⁻³
    reg [31:0] t2_r0, t2_r1, t2_r2, t2_r3;  // c₂·c₀⁻²

    assign busy = (state != ST_IDLE) && (state != ST_DONE);

    function [31:0] m31_add;
        input [31:0] x, y;
        reg [32:0] sum;
        begin sum = {1'b0, x} + {1'b0, y};
            m31_add = (sum >= P) ? (sum - P) : sum[31:0]; end
    endfunction

    function [31:0] m31_sub;
        input [31:0] x, y;
        begin m31_sub = (x >= y) ? (x - y) : (x + P - y); end
    endfunction

    function [31:0] m31_neg;
        input [31:0] x;
        begin m31_neg = (x == 32'd0) ? 32'd0 : (P - x); end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= ST_IDLE;
            done     <= 1'b0;
            err_zero_divisor <= 1'b0;
            inv_start <= 1'b0;
            mult_start <= 1'b0;
            mul_step <= 3'd0;
            m0_z0 <= 32'd0; m0_z1 <= 32'd0; m0_z2 <= 32'd0; m0_z3 <= 32'd0;
            m1_z0 <= 32'd0; m1_z1 <= 32'd0; m1_z2 <= 32'd0; m1_z3 <= 32'd0;
            m2_z0 <= 32'd0; m2_z1 <= 32'd0; m2_z2 <= 32'd0; m2_z3 <= 32'd0;
        end else begin
            case (state)
                ST_IDLE: begin
                    done <= 1'b0;
                    err_zero_divisor <= 1'b0;
                    if (start) begin
                        // Zero-divisor check: c₀ = 0 → not invertible
                        if (c0_z0 == 32'd0 && c0_z1 == 32'd0 &&
                            c0_z2 == 32'd0 && c0_z3 == 32'd0) begin
                            err_zero_divisor <= 1'b1;
                            m0_z0 <= 32'd0; m0_z1 <= 32'd0; m0_z2 <= 32'd0; m0_z3 <= 32'd0;
                            m1_z0 <= 32'd0; m1_z1 <= 32'd0; m1_z2 <= 32'd0; m1_z3 <= 32'd0;
                            m2_z0 <= 32'd0; m2_z1 <= 32'd0; m2_z2 <= 32'd0; m2_z3 <= 32'd0;
                            state <= ST_DONE;
                        end else begin
                            // Launch F_{p^4} inverter for c₀⁻¹
                            inv_z0 <= c0_z0; inv_z1 <= c0_z1;
                            inv_z2 <= c0_z2; inv_z3 <= c0_z3;
                            inv_start <= 1'b1;
                            state <= ST_TOWER_WAIT;
                        end
                    end
                end

                ST_TOWER_WAIT: begin
                    inv_start <= 1'b0;
                    if (inv_done) begin
                        if (inv_flags_v) begin
                            // Tower flagged singularity (shouldn't happen after our check)
                            err_zero_divisor <= 1'b1;
                            state <= ST_DONE;
                        end else begin
                            // m₀ = c₀⁻¹ captured
                            m0_z0 <= inv_r0; m0_z1 <= inv_r1;
                            m0_z2 <= inv_r2; m0_z3 <= inv_r3;
                            // Launch multiply step 0: c₀⁻² = m₀·m₀
                            mult_a0 <= inv_r0; mult_a1 <= inv_r1;
                            mult_a2 <= inv_r2; mult_a3 <= inv_r3;
                            mult_b0 <= inv_r0; mult_b1 <= inv_r1;
                            mult_b2 <= inv_r2; mult_b3 <= inv_r3;
                            mult_start <= 1'b1;
                            mul_step <= 3'd0;
                            state <= ST_MUL_LAUNCH;
                        end
                    end
                end

                ST_MUL_LAUNCH: begin
                    mult_start <= 1'b0;
                    state <= ST_MUL_WAIT;
                end

                ST_MUL_WAIT: begin
                    if (mult_done) begin
                        case (mul_step)
                            3'd0: begin  // c₀⁻² = m₀·m₀
                                sq_r0 <= mult_r0; sq_r1 <= mult_r1;
                                sq_r2 <= mult_r2; sq_r3 <= mult_r3;
                                // step 1: c₀⁻³ = c₀⁻²·m₀
                                mult_a0 <= mult_r0; mult_a1 <= mult_r1;
                                mult_a2 <= mult_r2; mult_a3 <= mult_r3;
                                mult_b0 <= m0_z0; mult_b1 <= m0_z1;
                                mult_b2 <= m0_z2; mult_b3 <= m0_z3;
                            end
                            3'd1: begin  // c₀⁻³
                                cu_r0 <= mult_r0; cu_r1 <= mult_r1;
                                cu_r2 <= mult_r2; cu_r3 <= mult_r3;
                                // step 2: h1 = c₁·c₀⁻²
                                mult_a0 <= c1_z0; mult_a1 <= c1_z1;
                                mult_a2 <= c1_z2; mult_a3 <= c1_z3;
                                mult_b0 <= sq_r0; mult_b1 <= sq_r1;
                                mult_b2 <= sq_r2; mult_b3 <= sq_r3;
                            end
                            3'd2: begin  // h1 = c₁·c₀⁻²
                                h1_r0 <= mult_r0; h1_r1 <= mult_r1;
                                h1_r2 <= mult_r2; h1_r3 <= mult_r3;
                                // step 3: c₁² = c₁·c₁
                                mult_a0 <= c1_z0; mult_a1 <= c1_z1;
                                mult_a2 <= c1_z2; mult_a3 <= c1_z3;
                                mult_b0 <= c1_z0; mult_b1 <= c1_z1;
                                mult_b2 <= c1_z2; mult_b3 <= c1_z3;
                            end
                            3'd3: begin  // c₁²
                                s1_r0 <= mult_r0; s1_r1 <= mult_r1;
                                s1_r2 <= mult_r2; s1_r3 <= mult_r3;
                                // step 4: c₁²·c₀⁻³
                                mult_a0 <= mult_r0; mult_a1 <= mult_r1;
                                mult_a2 <= mult_r2; mult_a3 <= mult_r3;
                                mult_b0 <= cu_r0; mult_b1 <= cu_r1;
                                mult_b2 <= cu_r2; mult_b3 <= cu_r3;
                            end
                            3'd4: begin  // c₁²·c₀⁻³
                                t1_r0 <= mult_r0; t1_r1 <= mult_r1;
                                t1_r2 <= mult_r2; t1_r3 <= mult_r3;
                                // step 5: c₂·c₀⁻²
                                mult_a0 <= c2_z0; mult_a1 <= c2_z1;
                                mult_a2 <= c2_z2; mult_a3 <= c2_z3;
                                mult_b0 <= sq_r0; mult_b1 <= sq_r1;
                                mult_b2 <= sq_r2; mult_b3 <= sq_r3;
                            end
                            3'd5: begin  // c₂·c₀⁻² — all multiplies done
                                t2_r0 <= mult_r0; t2_r1 <= mult_r1;
                                t2_r2 <= mult_r2; t2_r3 <= mult_r3;
                                state <= ST_COMBINE;
                            end
                        endcase
                        if (mul_step < 3'd5) begin
                            mul_step <= mul_step + 3'd1;
                            mult_start <= 1'b1;
                            state <= ST_MUL_LAUNCH;
                        end
                    end
                end

                ST_COMBINE: begin
                    // m₁ = -h1
                    m1_z0 <= m31_neg(h1_r0); m1_z1 <= m31_neg(h1_r1);
                    m1_z2 <= m31_neg(h1_r2); m1_z3 <= m31_neg(h1_r3);
                    // m₂ = c₁²·c₀⁻³ − c₂·c₀⁻² = t1 − t2
                    m2_z0 <= m31_sub(t1_r0, t2_r0);
                    m2_z1 <= m31_sub(t1_r1, t2_r1);
                    m2_z2 <= m31_sub(t1_r2, t2_r2);
                    m2_z3 <= m31_sub(t1_r3, t2_r3);
                    state <= ST_DONE;
                end

                ST_DONE: begin
                    done <= 1'b1;
                    state <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
