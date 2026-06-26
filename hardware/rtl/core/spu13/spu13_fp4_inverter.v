`timescale 1ns / 1ps

// spu13_fp4_inverter.v — Conjugate Reduction Tower for F_{p^4} inversion
//
// Computes Z_inv = Z^(-1) in F_{p^4} over M31 using nested quadratic extension
// tower collapse, avoiding O(p^4) exponentiation.
//
// Algorithm (Conjugate Reduction Tower):
//   1. Z_conj  = (c0, c1, -c2, -c3)         — conjugate w.r.t. √5, √15
//   2. W       = Z * Z_conj                  — collapses to F_{p^2}(√3): (w0, w1, 0, 0)
//   3. W_conj  = (w0, -w1, 0, 0)            — conjugate w.r.t. √3
//   4. N       = W * W_conj                  — collapses to scalar in F_p
//   5. N_inv   = N^(p-2) mod p              — Fermat exponentiation (30-bit exponent)
//   6. Temp    = Z_conj * W_conj             — F_{p^4} partial result
//   7. Result  = Temp * N_inv                — scalar × vector final scaling
//
// Pipeline: Stage A (×4) → Stage B (×4) → Stage C (Fermat ~62) → Stage D (×8)
// Total latency: ~76 cycles, deterministic.
//
// Singularity detection: if N == 0, asserts FLAGS.V and aborts.

module spu13_fp4_inverter (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  z0, z1, z2, z3,     // Z = c0 + c1√3 + c2√5 + c3√15
    output reg  [31:0]  inv0, inv1, inv2, inv3,
    output reg          done,
    output reg          busy,
    output reg          flags_v,             // Zero-norm singularity exception
    // Shared multiplier interface (connect to spu13_m31_multiplier)
    output reg          mult_start,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done,
    input  wire         mult_busy
);

    localparam [31:0] P      = 32'h7FFFFFFF;
    localparam [30:0] P_MINUS_2 = 31'h7FFFFFFD;  // p-2 = 2^31-3

    // ── State machine ───────────────────────────────────────────────
    localparam S_IDLE        = 4'd0;
    localparam S_STAGE_A     = 4'd1;   // Z * Z_conj → W
    localparam S_STAGE_B     = 4'd2;   // W * W_conj → N
    localparam S_FERMAT_INIT = 4'd3;   // Init Fermat chain
    localparam S_FERMAT_SQ   = 4'd4;   // Square step
    localparam S_FERMAT_MUL  = 4'd5;   // Conditional multiply step
    localparam S_STAGE_D1    = 4'd6;   // Z_conj * W_conj → Temp
    localparam S_STAGE_D2    = 4'd7;   // Temp * N_inv → Result (4 scalar mults)
    localparam S_DONE        = 4'd8;
    localparam S_EXCEPTION   = 4'd9;   // Zero-norm trap

    reg [3:0]  state;
    reg [31:0] zc0, zc1, zc2, zc3;     // Z_conjugate storage
    reg [31:0] w0, w1, w2, w3;         // W = Z * Z_conj
    reg [31:0] wc0, wc1, wc2, wc3;     // W_conj
    reg [31:0] norm_n;                 // Scalar norm N
    reg [31:0] ninv;                   // N_inv
    reg [31:0] temp0, temp1, temp2, temp3; // Temp = Z_conj * W_conj
    reg [31:0] fermat_res;             // Running result in Fermat chain
    reg [4:0]  fermat_bit;             // Current bit index (30 down to 0)
    reg [3:0]  stage_d2_idx;           // 0-3 for scalar multiply lanes

    // ── Fast M31 reduction for scalar ───────────────────────────────
    function [31:0] m31_reduce;
        input [63:0] z;
        reg [31:0] lo, hi, sum;
        begin
            lo  = z[30:0];
            hi  = z[62:31];
            sum = lo + hi;
            if (sum >= P) sum = sum - P;
            m31_reduce = sum;
        end
    endfunction

    // ── Sequential FSM ──────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= S_IDLE;
            done       <= 1'b0;
            busy       <= 1'b0;
            flags_v    <= 1'b0;
            mult_start <= 1'b0;
        end else begin
            done       <= 1'b0;
            mult_start <= 1'b0;

            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        busy    <= 1'b1;
                        flags_v <= 1'b0;
                        // Latch Z and compute Z_conj: flip √5, √15 signs
                        zc0 <= z0;
                        zc1 <= z1;
                        zc2 <= (P - z2) % P;   // -z2 mod P
                        zc3 <= (P - z3) % P;   // -z3 mod P
                        // Start multiply: Z * Z_conj
                        mult_a0    <= z0;
                        mult_a1    <= z1;
                        mult_a2    <= z2;
                        mult_a3    <= z3;
                        mult_b0    <= z0;
                        mult_b1    <= z1;
                        mult_b2    <= (P - z2) % P;
                        mult_b3    <= (P - z3) % P;
                        mult_start <= 1'b1;
                        state      <= S_STAGE_A;
                    end
                end

                // ── Stage A: Z * Z_conj → W ─────────────────────────
                S_STAGE_A: begin
                    if (mult_done && !mult_start) begin
                        // W = Z * Z_conj — should be in F_{p^2}(√3): (w0, w1, ~0, ~0)
                        w0 <= mult_r0;
                        w1 <= mult_r1;
                        w2 <= mult_r2;
                        w3 <= mult_r3;
                        // Compute W_conj: flip √3 sign → (w0, -w1, 0, 0)
                        wc0 <= mult_r0;
                        wc1 <= (P - mult_r1) % P;
                        wc2 <= 32'd0;
                        wc3 <= 32'd0;
                        // Start Stage B: W * W_conj
                        mult_a0    <= mult_r0;
                        mult_a1    <= mult_r1;
                        mult_a2    <= mult_r2;
                        mult_a3    <= mult_r3;
                        mult_b0    <= mult_r0;
                        mult_b1    <= (P - mult_r1) % P;
                        mult_b2    <= 32'd0;
                        mult_b3    <= 32'd0;
                        mult_start <= 1'b1;
                        state      <= S_STAGE_B;
                    end
                end

                // ── Stage B: W * W_conj → N (scalar norm) ────────────
                S_STAGE_B: begin
                    if (mult_done && !mult_start) begin
                        norm_n <= mult_r0;  // N = w0² - 3·w1² (mod P)
                        // Zero-norm check
                        if (mult_r0 == 32'd0) begin
                            flags_v <= 1'b1;
                            state   <= S_EXCEPTION;
                        end else begin
                            // Init Fermat: result = 1, N loaded
                            fermat_res <= 32'd1;
                            fermat_bit <= 5'd30;
                            state      <= S_FERMAT_INIT;
                        end
                    end
                end

                // ── Fermat chain init: one cycle setup ──────────────
                S_FERMAT_INIT: begin
                    state <= S_FERMAT_SQ;
                end

                // ── Fermat square step ──────────────────────────────
                S_FERMAT_SQ: begin
                    // Square: res = res * res mod P
                    fermat_res <= m31_reduce(fermat_res * fermat_res);
                    // Check if current bit of P_MINUS_2 is set
                    if (P_MINUS_2[fermat_bit])
                        state <= S_FERMAT_MUL;
                    else if (fermat_bit == 5'd0)
                        state <= S_STAGE_D1;  // Done
                    else begin
                        fermat_bit <= fermat_bit - 1;
                        // stay in S_FERMAT_SQ for next iteration
                    end
                end

                // ── Fermat conditional multiply step ────────────────
                S_FERMAT_MUL: begin
                    // res = res * N mod P
                    fermat_res <= m31_reduce(fermat_res * norm_n);
                    if (fermat_bit == 5'd0) begin
                        ninv  <= m31_reduce(fermat_res * norm_n);  // final value
                        // Start Stage D1: Z_conj * W_conj
                        mult_a0    <= zc0;
                        mult_a1    <= zc1;
                        mult_a2    <= zc2;
                        mult_a3    <= zc3;
                        mult_b0    <= wc0;
                        mult_b1    <= wc1;
                        mult_b2    <= wc2;
                        mult_b3    <= wc3;
                        mult_start <= 1'b1;
                        state      <= S_STAGE_D1;
                    end else begin
                        fermat_bit <= fermat_bit - 1;
                        state      <= S_FERMAT_SQ;
                    end
                end

                // ── Stage D1: Temp = Z_conj * W_conj ────────────────
                S_STAGE_D1: begin
                    if (mult_done && !mult_start) begin
                        temp0 <= mult_r0;
                        temp1 <= mult_r1;
                        temp2 <= mult_r2;
                        temp3 <= mult_r3;
                        stage_d2_idx <= 4'd0;
                        // Start Stage D2 lane 0: temp0 * ninv
                        mult_a0    <= mult_r0;
                        mult_a1    <= 32'd0;
                        mult_a2    <= 32'd0;
                        mult_a3    <= 32'd0;
                        mult_b0    <= ninv;
                        mult_b1    <= 32'd0;
                        mult_b2    <= 32'd0;
                        mult_b3    <= 32'd0;
                        mult_start <= 1'b1;
                        state      <= S_STAGE_D2;
                    end
                end

                // ── Stage D2: scalar × ninv (4 lanes sequential) ───
                S_STAGE_D2: begin
                    if (mult_done && !mult_start) begin
                        case (stage_d2_idx)
                            4'd0: begin
                                inv0 <= mult_r0;
                                // Lane 1
                                mult_a0    <= temp1;
                                mult_a1    <= 32'd0;
                                mult_a2    <= 32'd0;
                                mult_a3    <= 32'd0;
                                mult_b0    <= ninv;
                                mult_b1    <= 32'd0;
                                mult_b2    <= 32'd0;
                                mult_b3    <= 32'd0;
                                mult_start <= 1'b1;
                                stage_d2_idx <= 4'd1;
                            end
                            4'd1: begin
                                inv1 <= mult_r0;
                                mult_a0    <= temp2;
                                mult_a1    <= 32'd0;
                                mult_a2    <= 32'd0;
                                mult_a3    <= 32'd0;
                                mult_b0    <= ninv;
                                mult_b1    <= 32'd0;
                                mult_b2    <= 32'd0;
                                mult_b3    <= 32'd0;
                                mult_start <= 1'b1;
                                stage_d2_idx <= 4'd2;
                            end
                            4'd2: begin
                                inv2 <= mult_r0;
                                mult_a0    <= temp3;
                                mult_a1    <= 32'd0;
                                mult_a2    <= 32'd0;
                                mult_a3    <= 32'd0;
                                mult_b0    <= ninv;
                                mult_b1    <= 32'd0;
                                mult_b2    <= 32'd0;
                                mult_b3    <= 32'd0;
                                mult_start <= 1'b1;
                                stage_d2_idx <= 4'd3;
                            end
                            4'd3: begin
                                inv3 <= mult_r0;
                                done <= 1'b1;
                                busy <= 1'b0;
                                state <= S_IDLE;
                            end
                        endcase
                    end
                end

                // ── Exception: zero-norm singularity ─────────────────
                S_EXCEPTION: begin
                    flags_v <= 1'b1;
                    done    <= 1'b1;
                    busy    <= 1'b0;
                    state   <= S_IDLE;
                end

                S_DONE: begin
                    done  <= 1'b1;
                    busy  <= 1'b0;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
