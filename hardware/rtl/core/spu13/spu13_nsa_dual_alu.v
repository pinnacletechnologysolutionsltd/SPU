`timescale 1ns / 1ps

// spu13_nsa_dual_alu.v — Dual-Number Arithmetic Unit for FSDG over F_{p^4}[epsilon]/(epsilon^2)
//
// Computes dual-number addition and multiplication over the dual ring
// A_SPU = F_{p^4}[epsilon] / (epsilon^2) where epsilon^2 = 0.
//
// Addition:   (A+eB) + (C+eD) = (A+C) + e(B+D)
//             Requires 2 F_{p^4} adds, 2 cycles (pipelined → 1 effective).
//
// Multiplication: (A+eB)(C+eD) = AC + e(AD + BC)
//             Requires 3 F_{p^4} multiplies + 2 adds.
//             Single multiplier: ~6 cycles serialized through TDM core.
//
// Inversion (not implemented here — uses fp4_inverter tower):
//   (A+eB)^(-1) = A^(-1) - e * A^(-1) * B * A^(-1)
//
// Input/Output: F_{p^4} elements as 4 × 32-bit coefficients
//   real_z0, real_z1, real_z2, real_z3 = A
//   eps_z0,  eps_z1,  eps_z2,  eps_z3  = B

module spu13_nsa_dual_alu (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // ── Operation select ────────────────────────────────────────────
    // 1'b0 = dual add, 1'b1 = dual multiply
    input  wire         op_mul,

    // ── Operand A (dual number) ─────────────────────────────────────
    input  wire [31:0]  a_real_z0, a_real_z1, a_real_z2, a_real_z3,
    input  wire [31:0]  a_eps_z0,  a_eps_z1,  a_eps_z2,  a_eps_z3,

    // ── Operand B (dual number) ─────────────────────────────────────
    input  wire [31:0]  b_real_z0, b_real_z1, b_real_z2, b_real_z3,
    input  wire [31:0]  b_eps_z0,  b_eps_z1,  b_eps_z2,  b_eps_z3,

    // ── Result (dual number) ────────────────────────────────────────
    output reg  [31:0]  r_real_z0, r_real_z1, r_real_z2, r_real_z3,
    output reg  [31:0]  r_eps_z0,  r_eps_z1,  r_eps_z2,  r_eps_z3,
    output reg          done,
    output wire         busy,

    // ── F_{p^4} multiplier interface (shared) ───────────────────────
    output reg          mult_start,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done, mult_busy
);

    localparam P = 32'h7FFFFFFF;

    // ── State machine ────────────────────────────────────────────────
    localparam IDLE         = 4'd0;
    localparam DONE_CYCLE   = 4'd1;
    // Multiply states — 3 multiplies through single 2-stage pipelined multiplier
    localparam MUL_AC_START = 4'd2;   // Assert start, capture operands
    localparam MUL_AC_WAIT  = 4'd3;   // Wait for 2-stage pipeline
    localparam MUL_AD_START = 4'd4;   // Capture AC, launch AD
    localparam MUL_AD_WAIT  = 4'd5;   // Wait for AD
    localparam MUL_BC_START = 4'd6;   // Capture AD, launch BC
    localparam MUL_BC_WAIT  = 4'd7;   // Wait for BC
    localparam MUL_COMBINE  = 4'd8;   // Combine: AD+BC, latch result

    reg [3:0] state;

    // ── Pipeline registers for intermediate results ─────────────────
    reg [31:0] ac_r0, ac_r1, ac_r2, ac_r3;   // AC product
    reg [31:0] ad_r0, ad_r1, ad_r2, ad_r3;   // AD product
    reg [31:0] bc_r0, bc_r1, bc_r2, bc_r3;   // BC product
    reg [31:0] ad_plus_bc_r0, ad_plus_bc_r1, ad_plus_bc_r2, ad_plus_bc_r3;

    assign busy = (state != IDLE) && (state != DONE_CYCLE);

    // ── done is sticky — asserted when result is valid, cleared on next start
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            done <= 1'b0;
        else if (start)
            done <= 1'b0;
        else if (state == DONE_CYCLE)
            done <= 1'b1;
    end

    // ── Modular addition helper ──────────────────────────────────────
    function [31:0] m31_add;
        input [31:0] x, y;
        reg [32:0] sum;
        begin
            sum = {1'b0, x} + {1'b0, y};
            m31_add = (sum >= P) ? (sum - P) : sum[31:0];
        end
    endfunction

    // ── Main FSM ─────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            mult_start   <= 1'b0;
            r_real_z0    <= 32'd0; r_real_z1 <= 32'd0; r_real_z2 <= 32'd0; r_real_z3 <= 32'd0;
            r_eps_z0     <= 32'd0; r_eps_z1  <= 32'd0; r_eps_z2  <= 32'd0; r_eps_z3  <= 32'd0;
            ac_r0 <= 32'd0; ac_r1 <= 32'd0; ac_r2 <= 32'd0; ac_r3 <= 32'd0;
            ad_r0 <= 32'd0; ad_r1 <= 32'd0; ad_r2 <= 32'd0; ad_r3 <= 32'd0;
            bc_r0 <= 32'd0; bc_r1 <= 32'd0; bc_r2 <= 32'd0; bc_r3 <= 32'd0;
            ad_plus_bc_r0 <= 32'd0; ad_plus_bc_r1 <= 32'd0; ad_plus_bc_r2 <= 32'd0; ad_plus_bc_r3 <= 32'd0;
        end else begin
            case (state)
                IDLE: begin
                    if (start) begin
                        if (!op_mul) begin
                            // ── Dual Add: (A+C) + e(B+D) (single cycle) ──
                            r_real_z0 <= m31_add(a_real_z0, b_real_z0);
                            r_real_z1 <= m31_add(a_real_z1, b_real_z1);
                            r_real_z2 <= m31_add(a_real_z2, b_real_z2);
                            r_real_z3 <= m31_add(a_real_z3, b_real_z3);
                            r_eps_z0  <= m31_add(a_eps_z0,  b_eps_z0);
                            r_eps_z1  <= m31_add(a_eps_z1,  b_eps_z1);
                            r_eps_z2  <= m31_add(a_eps_z2,  b_eps_z2);
                            r_eps_z3  <= m31_add(a_eps_z3,  b_eps_z3);
                            state <= DONE_CYCLE;
                        end else begin
                            // ── Dual Multiply: AC + e(AD+BC) ────────────
                            // Launch multiply 1: AC
                            mult_a0 <= a_real_z0; mult_a1 <= a_real_z1;
                            mult_a2 <= a_real_z2; mult_a3 <= a_real_z3;
                            mult_b0 <= b_real_z0; mult_b1 <= b_real_z1;
                            mult_b2 <= b_real_z2; mult_b3 <= b_real_z3;
                            mult_start <= 1'b1;
                            state <= MUL_AC_START;
                        end
                    end
                end

                DONE_CYCLE: begin
                    state <= IDLE;
                end

                // ── Multiply 1: AC — launch, wait 2-stage pipeline ──
                MUL_AC_START: begin
                    mult_start <= 1'b0;
                    state <= MUL_AC_WAIT;
                end

                MUL_AC_WAIT: begin
                    if (mult_done) begin
                        ac_r0 <= mult_r0; ac_r1 <= mult_r1;
                        ac_r2 <= mult_r2; ac_r3 <= mult_r3;
                        state <= MUL_AD_START;
                    end
                end

                // ── Multiply 2: AD (launch, then wait) ──────────────────
                MUL_AD_START: begin
                    // Launch next multiply — consistent 1-cycle pulse
                    mult_a0 <= a_real_z0; mult_a1 <= a_real_z1;
                    mult_a2 <= a_real_z2; mult_a3 <= a_real_z3;
                    mult_b0 <= b_eps_z0;  mult_b1 <= b_eps_z1;
                    mult_b2 <= b_eps_z2;  mult_b3 <= b_eps_z3;
                    mult_start <= 1'b1;
                    state <= MUL_AD_WAIT;
                end

                MUL_AD_WAIT: begin
                    mult_start <= 1'b0;
                    if (mult_done) begin
                        ad_r0 <= mult_r0; ad_r1 <= mult_r1;
                        ad_r2 <= mult_r2; ad_r3 <= mult_r3;
                        state <= MUL_BC_START;
                    end
                end

                // ── Multiply 3: BC ───────────────────────────────────
                MUL_BC_START: begin
                    mult_a0 <= a_eps_z0;  mult_a1 <= a_eps_z1;
                    mult_a2 <= a_eps_z2;  mult_a3 <= a_eps_z3;
                    mult_b0 <= b_real_z0; mult_b1 <= b_real_z1;
                    mult_b2 <= b_real_z2; mult_b3 <= b_real_z3;
                    mult_start <= 1'b1;
                    state <= MUL_BC_WAIT;
                end

                MUL_BC_WAIT: begin
                    mult_start <= 1'b0;
                    if (mult_done) begin
                        bc_r0 <= mult_r0; bc_r1 <= mult_r1;
                        bc_r2 <= mult_r2; bc_r3 <= mult_r3;
                        state <= MUL_COMBINE;
                    end
                end

                // ── Combine: AD + BC, final result = AC + e(AD+BC) ──
                MUL_COMBINE: begin
                    r_real_z0 <= ac_r0; r_real_z1 <= ac_r1;
                    r_real_z2 <= ac_r2; r_real_z3 <= ac_r3;
                    r_eps_z0  <= m31_add(ad_r0, bc_r0);
                    r_eps_z1  <= m31_add(ad_r1, bc_r1);
                    r_eps_z2  <= m31_add(ad_r2, bc_r2);
                    r_eps_z3  <= m31_add(ad_r3, bc_r3);
                    state <= DONE_CYCLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

    // ── eps output latched from ad_plus_bc after MUL_COMBINE ────────
    // (handled in the main FSM below, not in a separate always block)

endmodule
