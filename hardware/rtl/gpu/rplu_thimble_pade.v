`timescale 1ns / 1ps

// rplu_thimble_pade.v — Thimble-Padé rational approximant engine over A31
//
// Evaluates a [M/N] Padé approximant P(x)/Q(x) at a given saddle point x
// in the split-biquadratic algebra A31 over M31 (p = 2^31 - 1).
//
// The Padé approximant approximates the Lefschetz thimble descent:
//   thimble_contribution = P(x) / Q(x)  where Q(x) is an A31 unit
//
// Uses the Conjugate Reduction Tower for A31 denominator unit inversion,
// then multiplies numerator × inverse_denominator.
//
// Pipeline:
//   Horner (NUM_COEFF × mult_latency) → A31 inverter (~76 cycles) → Final multiply

module rplu_thimble_pade #(
    parameter NUM_COEFF    = 5,         // [4/4] Padé = 5 coeffs each
    parameter COEFF_ADDR_W = 3          // ceil(log2(NUM_COEFF))
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  saddle_c0, saddle_c1, saddle_c2, saddle_c3,

    // Coefficient write interface
    input  wire         coeff_we,
    input  wire         coeff_is_den,
    input  wire [COEFF_ADDR_W-1:0] coeff_addr,
    input  wire [31:0]  coeff_c0, coeff_c1, coeff_c2, coeff_c3,

    // Result + status
    output reg  [31:0]  result_c0, result_c1, result_c2, result_c3,
    output reg          done,
    output reg          busy,
    output reg          flags_v,       // Zero-norm singularity from inverter

    // Shared multiplier interface
    output reg          mult_start,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done,
    input  wire         mult_busy,

    // A31 inverter interface
    output reg          inv_start,
    output reg  [31:0]  inv_z0, inv_z1, inv_z2, inv_z3,
    input  wire [31:0]  inv_r0, inv_r1, inv_r2, inv_r3,
    input  wire         inv_done,
    input  wire         inv_busy,
    input  wire         inv_flags_v,

    output wire [2:0]   debug_state
);

    // ── Coefficient storage ─────────────────────────────────────────
    reg [31:0] num_coeff [0:NUM_COEFF-1][0:3];
    reg [31:0] den_coeff [0:NUM_COEFF-1][0:3];

    integer ci, cj;
    initial begin
        for (ci = 0; ci < NUM_COEFF; ci = ci + 1) begin
            for (cj = 0; cj < 4; cj = cj + 1) begin
                num_coeff[ci][cj] = (ci == 0 && cj == 0) ? 32'd1 : 32'd0;
                den_coeff[ci][cj] = (ci == 0 && cj == 0) ? 32'd1 : 32'd0;
            end
        end
    end

    localparam [31:0] P = 32'h7FFFFFFF;

    function [31:0] m31_add;
        input [31:0] x, y;
        reg [32:0] sum;
        begin
            sum = {1'b0, x} + {1'b0, y};
            m31_add = (sum >= P) ? (sum - P) : sum[31:0];
        end
    endfunction

    always @(posedge clk) begin
        if (coeff_we) begin
            if (coeff_is_den) begin
                den_coeff[coeff_addr][0] <= coeff_c0;
                den_coeff[coeff_addr][1] <= coeff_c1;
                den_coeff[coeff_addr][2] <= coeff_c2;
                den_coeff[coeff_addr][3] <= coeff_c3;
            end else begin
                num_coeff[coeff_addr][0] <= coeff_c0;
                num_coeff[coeff_addr][1] <= coeff_c1;
                num_coeff[coeff_addr][2] <= coeff_c2;
                num_coeff[coeff_addr][3] <= coeff_c3;
            end
        end
    end

    // ── FSM ─────────────────────────────────────────────────────────
    localparam S_IDLE       = 3'd0;
    localparam S_HORNER     = 3'd1;
    localparam S_INVERT     = 3'd2;
    localparam S_MULTIPLY   = 3'd3;
    localparam S_DONE       = 3'd4;

    (* keep, fsm_encoding = "none" *) reg [2:0] state;
    reg [COEFF_ADDR_W:0] horner_idx;
    reg        horner_is_den;
    reg [31:0] horner_c0, horner_c1, horner_c2, horner_c3;
    reg [31:0] num_c0, num_c1, num_c2, num_c3;
    reg [31:0] den_c0, den_c1, den_c2, den_c3;
    reg [31:0] inv_c0, inv_c1, inv_c2, inv_c3;
    reg        inv_start_pending;

    assign debug_state = state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= S_IDLE;
            done         <= 1'b0;
            busy         <= 1'b0;
            flags_v      <= 1'b0;
            horner_idx   <= 0;
            mult_start   <= 1'b0;
            inv_start    <= 1'b0;
            inv_start_pending <= 1'b0;
        end else begin
            done       <= 1'b0;
            inv_start  <= 1'b0;
            mult_start <= 1'b0;

            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        busy         <= 1'b1;
                        flags_v      <= 1'b0;
                        inv_start_pending <= 1'b0;
                        horner_idx   <= NUM_COEFF - 2;
                        horner_c0    <= num_coeff[NUM_COEFF-1][0];
                        horner_c1    <= num_coeff[NUM_COEFF-1][1];
                        horner_c2    <= num_coeff[NUM_COEFF-1][2];
                        horner_c3    <= num_coeff[NUM_COEFF-1][3];
                        horner_is_den <= 1'b0;
                        mult_a0      <= num_coeff[NUM_COEFF-1][0];
                        mult_a1      <= num_coeff[NUM_COEFF-1][1];
                        mult_a2      <= num_coeff[NUM_COEFF-1][2];
                        mult_a3      <= num_coeff[NUM_COEFF-1][3];
                        mult_b0      <= saddle_c0;
                        mult_b1      <= saddle_c1;
                        mult_b2      <= saddle_c2;
                        mult_b3      <= saddle_c3;
                        mult_start   <= 1'b1;
                        state        <= S_HORNER;
                    end
                end

                S_HORNER: begin
                    if (mult_done) begin
                        if (!horner_is_den) begin
                            if (horner_idx == 0) begin
                                // Numerator complete: acc = acc*x + p0
                                num_c0 <= m31_add(mult_r0, num_coeff[0][0]);
                                num_c1 <= m31_add(mult_r1, num_coeff[0][1]);
                                num_c2 <= m31_add(mult_r2, num_coeff[0][2]);
                                num_c3 <= m31_add(mult_r3, num_coeff[0][3]);

                                // Start denominator Horner chain.
                                horner_c0     <= den_coeff[NUM_COEFF-1][0];
                                horner_c1     <= den_coeff[NUM_COEFF-1][1];
                                horner_c2     <= den_coeff[NUM_COEFF-1][2];
                                horner_c3     <= den_coeff[NUM_COEFF-1][3];
                                horner_idx    <= NUM_COEFF - 2;
                                horner_is_den <= 1'b1;
                                mult_a0       <= den_coeff[NUM_COEFF-1][0];
                                mult_a1       <= den_coeff[NUM_COEFF-1][1];
                                mult_a2       <= den_coeff[NUM_COEFF-1][2];
                                mult_a3       <= den_coeff[NUM_COEFF-1][3];
                                mult_b0       <= saddle_c0;
                                mult_b1       <= saddle_c1;
                                mult_b2       <= saddle_c2;
                                mult_b3       <= saddle_c3;
                                mult_start    <= 1'b1;
                            end else begin
                                // Continue numerator: acc = acc*x + p[idx]
                                horner_c0  <= m31_add(mult_r0, num_coeff[horner_idx][0]);
                                horner_c1  <= m31_add(mult_r1, num_coeff[horner_idx][1]);
                                horner_c2  <= m31_add(mult_r2, num_coeff[horner_idx][2]);
                                horner_c3  <= m31_add(mult_r3, num_coeff[horner_idx][3]);
                                mult_a0    <= m31_add(mult_r0, num_coeff[horner_idx][0]);
                                mult_a1    <= m31_add(mult_r1, num_coeff[horner_idx][1]);
                                mult_a2    <= m31_add(mult_r2, num_coeff[horner_idx][2]);
                                mult_a3    <= m31_add(mult_r3, num_coeff[horner_idx][3]);
                                mult_b0    <= saddle_c0;
                                mult_b1    <= saddle_c1;
                                mult_b2    <= saddle_c2;
                                mult_b3    <= saddle_c3;
                                mult_start <= 1'b1;
                                horner_idx <= horner_idx - 1;
                            end
                        end else begin
                            if (horner_idx == 0) begin
                                // Denominator complete: acc = acc*x + q0
                                den_c0 <= m31_add(mult_r0, den_coeff[0][0]);
                                den_c1 <= m31_add(mult_r1, den_coeff[0][1]);
                                den_c2 <= m31_add(mult_r2, den_coeff[0][2]);
                                den_c3 <= m31_add(mult_r3, den_coeff[0][3]);
                                inv_z0 <= m31_add(mult_r0, den_coeff[0][0]);
                                inv_z1 <= m31_add(mult_r1, den_coeff[0][1]);
                                inv_z2 <= m31_add(mult_r2, den_coeff[0][2]);
                                inv_z3 <= m31_add(mult_r3, den_coeff[0][3]);
                                inv_start <= 1'b1;
                                inv_start_pending <= 1'b1;
                                state <= S_INVERT;
                            end else begin
                                // Continue denominator: acc = acc*x + q[idx]
                                horner_c0  <= m31_add(mult_r0, den_coeff[horner_idx][0]);
                                horner_c1  <= m31_add(mult_r1, den_coeff[horner_idx][1]);
                                horner_c2  <= m31_add(mult_r2, den_coeff[horner_idx][2]);
                                horner_c3  <= m31_add(mult_r3, den_coeff[horner_idx][3]);
                                mult_a0    <= m31_add(mult_r0, den_coeff[horner_idx][0]);
                                mult_a1    <= m31_add(mult_r1, den_coeff[horner_idx][1]);
                                mult_a2    <= m31_add(mult_r2, den_coeff[horner_idx][2]);
                                mult_a3    <= m31_add(mult_r3, den_coeff[horner_idx][3]);
                                mult_b0    <= saddle_c0;
                                mult_b1    <= saddle_c1;
                                mult_b2    <= saddle_c2;
                                mult_b3    <= saddle_c3;
                                mult_start <= 1'b1;
                                horner_idx <= horner_idx - 1;
                            end
                        end
                    end
                end

                S_INVERT: begin
                    if (inv_start_pending && !inv_busy)
                        inv_start <= 1'b1;
                    if (inv_start_pending && inv_busy)
                        inv_start_pending <= 1'b0;
                    if (inv_done) begin
                        inv_start_pending <= 1'b0;
                        if (inv_flags_v) begin
                            // Zero-norm singularity — propagate exception
                            flags_v <= 1'b1;
                            done    <= 1'b1;
                            busy    <= 1'b0;
                            state   <= S_IDLE;
                        end else begin
                            inv_c0 <= inv_r0;
                            inv_c1 <= inv_r1;
                            inv_c2 <= inv_r2;
                            inv_c3 <= inv_r3;
                            // Multiply num × inv_den in A31
                            mult_a0    <= num_c0;
                            mult_a1    <= num_c1;
                            mult_a2    <= num_c2;
                            mult_a3    <= num_c3;
                            mult_b0    <= inv_r0;
                            mult_b1    <= inv_r1;
                            mult_b2    <= inv_r2;
                            mult_b3    <= inv_r3;
                            mult_start <= 1'b1;
                            state      <= S_MULTIPLY;
                        end
                    end
                end

                S_MULTIPLY: begin
                    if (mult_done) begin
                        result_c0 <= mult_r0;
                        result_c1 <= mult_r1;
                        result_c2 <= mult_r2;
                        result_c3 <= mult_r3;
                        done      <= 1'b1;
                        busy      <= 1'b0;
                        state     <= S_IDLE;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
