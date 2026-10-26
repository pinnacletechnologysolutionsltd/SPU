// spu13_lucas_mac.v — Lucas Phinary MAC Co-Processor
// Ring: Z[phi] / L_p.  All ops exact, zero floating-point.
//
// Copyright 2026 John Curley
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// PSCALE(1c) PCHIRAL(1c) PMUL(3c) PINV(O(log L_p) via Extended Binary GCD).
// PHSLK(1c): rational phase coherence by cross multiplication.
module spu13_lucas_mac #(
    parameter L_P = 521,
    parameter L_P_BITS = 10,
    parameter FAST_ONLY = 0,
    parameter PINV_MAX_ITERS = 64
) (
    input wire clk, rst_n, ce, start,
    input wire [2:0] opcode,  // 0=PSCALE 1=PCHIRAL 2=PMUL 3=PINV 4=PHSLK
    input wire [L_P_BITS-1:0] op_a, op_b, op_c, op_d,
    input wire [L_P_BITS-1:0] phslk_n2_a, phslk_n2_b,
    input wire [L_P_BITS-1:0] phslk_d2_a, phslk_d2_b,
    output reg busy, done, error,
    output reg [L_P_BITS-1:0] result_a, result_b,
    output reg                phslk_coherent,
    output reg                phslk_zero_divisor,
    output wire               norm_violation
);
    localparam [2:0] OP_PSCALE=0, OP_PCHIRAL=1, OP_PMUL=2, OP_PINV=3, OP_PHSLK=4;
    localparam [1:0] S_IDLE=0, S_BUSY=1;

    function [L_P_BITS-1:0] red_pair;
        input [L_P_BITS:0] x;
        reg [L_P_BITS:0] t;
        begin
            t = x;
            if (t >= L_P) t = t - L_P;
            if (t >= L_P) t = t - L_P;
            red_pair = t[L_P_BITS-1:0];
        end
    endfunction

    localparam [31:0] BARRETT_MU = 32'h8000_0000 / L_P;

    function [L_P_BITS-1:0] red_full;
        input [31:0] x;
        reg [63:0] q_est;
        reg [31:0] r_est;
        begin
            q_est = (x * BARRETT_MU) >> 31;
            r_est = x - (q_est * L_P);
            if (r_est >= L_P) r_est = r_est - L_P;
            red_full = r_est[L_P_BITS-1:0];
        end
    endfunction

    wire [L_P_BITS-1:0] ps_b = red_pair({1'b0, op_a} + {1'b0, op_b});
    wire [L_P_BITS-1:0] pc_a = red_pair({1'b0, op_a} + {1'b0, op_b});
    wire [L_P_BITS-1:0] pc_b = (op_b == 0) ? 0 : red_pair((2*L_P) - op_b);

    function [2*L_P_BITS-1:0] phi_mul_pair;
        input [L_P_BITS-1:0] a1, b1, a2, b2;
        reg [L_P_BITS-1:0] ar, br;
        begin
            ar = red_full(a1*a2 + b1*b2);
            br = red_full(a1*b2 + a2*b1 + b1*b2);
            phi_mul_pair = {br, ar};
        end
    endfunction

    function [L_P_BITS-1:0] phi_norm;
        input [L_P_BITS-1:0] a, b;
        reg [31:0] a2, ab, b2;
        begin
            a2 = a * a;
            ab = a * b;
            b2 = b * b;
            phi_norm = red_full(a2 + ab + L_P*L_P - b2);
        end
    endfunction

    wire [2*L_P_BITS-1:0] phslk_left;
    wire [2*L_P_BITS-1:0] phslk_right;
    wire                  phslk_match;
    wire                  phslk_den_zero_divisor;

    assign phslk_left  = phi_mul_pair(op_a, op_b, phslk_d2_a, phslk_d2_b);
    assign phslk_right = phi_mul_pair(phslk_n2_a, phslk_n2_b, op_c, op_d);
    assign phslk_match = (phslk_left == phslk_right);
    assign phslk_den_zero_divisor = (phi_norm(op_c, op_d) == 0) ||
                                    (phi_norm(phslk_d2_a, phslk_d2_b) == 0);

    reg [1:0] pm_st; reg [31:0] pm_ac, pm_bd, pm_ad, pm_bc;

    // PINV: Extended Binary GCD for norm modular inverse
    reg [L_P_BITS-1:0] pinv_norm;                          // N(a+b*phi)
    reg [L_P_BITS-1:0] pinv_norm_inv;                      // N^-1 mod L_P
    reg [L_P_BITS-1:0] pinv_ca, pinv_cb;                   // saved conjugate
    reg [L_P_BITS-1:0] pinv_u, pinv_v;                     // GCD: u, v
    reg [L_P_BITS-1:0] pinv_x1, pinv_x2;                   // Bezout: x1, x2
    localparam [2:0] PINV_SETUP = 3'd0;
    localparam [2:0] PINV_GCD = 3'd1;
    localparam [2:0] PINV_MUL = 3'd2;
    localparam [2:0] PINV_REDUCE = 3'd3;

    reg [2:0] pinv_st;
    reg [7:0] pinv_iter;
    reg [31:0] pinv_res_a_mul, pinv_res_b_mul;

    reg [1:0] state;
    reg [2:0] active_opcode;
    reg [L_P_BITS-1:0] active_norm_lhs;
    reg [L_P_BITS-1:0] active_norm_rhs;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; done <= 0; error <= 0; busy <= 0;
            result_a <= 0; result_b <= 0;
            phslk_coherent <= 1'b0; phslk_zero_divisor <= 1'b0;
            pm_st <= 0; pm_ac <= 0; pm_bd <= 0; pm_ad <= 0; pm_bc <= 0;
            pinv_norm <= 0; pinv_norm_inv <= 0;
            pinv_ca <= 0; pinv_cb <= 0;
            pinv_u <= 0; pinv_v <= 0; pinv_x1 <= 0; pinv_x2 <= 0; pinv_st <= 0;
            pinv_iter <= 0; pinv_res_a_mul <= 0; pinv_res_b_mul <= 0;
            active_opcode <= 0; active_norm_lhs <= 0; active_norm_rhs <= 0;
        end else if (!ce) begin
            done <= 0;
            error <= 0;
        end else begin
            done <= 0; error <= 0;
            case (state)
                S_IDLE: if (start) begin
                    active_opcode <= opcode;
                    active_norm_lhs <= phi_norm(op_a, op_b);
                    active_norm_rhs <= phi_norm(op_c, op_d);
                    case (opcode)
                        OP_PSCALE: begin
                            phslk_coherent <= 1'b0; phslk_zero_divisor <= 1'b0;
                            result_a <= op_b; result_b <= ps_b; done <= 1;
                        end
                        OP_PCHIRAL: begin
                            phslk_coherent <= 1'b0; phslk_zero_divisor <= 1'b0;
                            result_a <= pc_a; result_b <= pc_b; done <= 1;
                        end
                        OP_PMUL: begin
                            phslk_coherent <= 1'b0; phslk_zero_divisor <= 1'b0;
                            if (FAST_ONLY) begin
                                error <= 1;
                            end else begin
                                pm_ac <= op_a * op_c; pm_bd <= op_b * op_d;
                                pm_ad <= op_a * op_d; pm_bc <= op_b * op_c;
                                pm_st <= 0; state <= S_BUSY; busy <= 1;
                            end
                        end
                        OP_PINV: begin
                            phslk_coherent <= 1'b0; phslk_zero_divisor <= 1'b0;
                            if (FAST_ONLY) begin
                                error <= 1;
                            end else begin
                                pinv_norm <= phi_norm(op_a, op_b);
                                pinv_ca <= pc_a; pinv_cb <= pc_b;  // save conjugate
                                pinv_st <= PINV_SETUP; pinv_iter <= 0;
                                state <= S_BUSY; busy <= 1;
                            end
                        end
                        OP_PHSLK: begin
                            phslk_coherent <= phslk_match;
                            phslk_zero_divisor <= phslk_den_zero_divisor;
                            result_a <= {{(L_P_BITS-1){1'b0}}, phslk_match};
                            result_b <= {{(L_P_BITS-1){1'b0}}, phslk_den_zero_divisor};
                            done <= 1;
                        end
                        default: error <= 1;
                    endcase
                end

                S_BUSY: case (active_opcode)
                    OP_PMUL: begin
                        if (pm_st == 0) pm_st <= 1;
                        else if (pm_st == 1) pm_st <= 2;
                        else begin
                            result_a <= red_full(pm_ac + pm_bd);
                            result_b <= red_full(pm_ad + pm_bc + pm_bd);
                            done <= 1; busy <= 0; pm_st <= 0; state <= S_IDLE;
                        end
                    end
                    OP_PINV: begin
                        if (pinv_st == PINV_SETUP) begin
                            if (pinv_norm == 0) begin
                                error <= 1; busy <= 0; state <= S_IDLE;
                                pinv_st <= PINV_SETUP; pinv_iter <= 0;
                            end
                            else begin
                                pinv_u <= pinv_norm; pinv_v <= L_P;
                                pinv_x1 <= 1; pinv_x2 <= 0;
                                pinv_iter <= 0;
                                pinv_st <= PINV_GCD;
                            end
                        end else if (pinv_st == PINV_GCD) begin
                            // Extended Binary GCD for N^-1 mod L_P
                            if (pinv_u == 1) begin
                                pinv_norm_inv <= red_full(pinv_x1); pinv_st <= PINV_MUL;
                            end else if (pinv_v == 1) begin
                                pinv_norm_inv <= red_full(pinv_x2); pinv_st <= PINV_MUL;
                            end else if (pinv_iter >= PINV_MAX_ITERS) begin
                                error <= 1; busy <= 0; state <= S_IDLE;
                                pinv_st <= PINV_SETUP; pinv_iter <= 0;
                            end else if (pinv_u[0] == 0) begin
                                pinv_u <= pinv_u >> 1;
                                pinv_x1 <= (pinv_x1[0] == 0) ? (pinv_x1 >> 1) : ((pinv_x1 + L_P) >> 1);
                                pinv_iter <= pinv_iter + 8'd1;
                            end else if (pinv_v[0] == 0) begin
                                pinv_v <= pinv_v >> 1;
                                pinv_x2 <= (pinv_x2[0] == 0) ? (pinv_x2 >> 1) : ((pinv_x2 + L_P) >> 1);
                                pinv_iter <= pinv_iter + 8'd1;
                            end else if (pinv_u >= pinv_v) begin
                                pinv_u <= pinv_u - pinv_v;
                                pinv_x1 <= (pinv_x1 >= pinv_x2) ? (pinv_x1 - pinv_x2) : (pinv_x1 + L_P - pinv_x2);
                                pinv_iter <= pinv_iter + 8'd1;
                            end else begin
                                pinv_v <= pinv_v - pinv_u;
                                pinv_x2 <= (pinv_x2 >= pinv_x1) ? (pinv_x2 - pinv_x1) : (pinv_x2 + L_P - pinv_x1);
                                pinv_iter <= pinv_iter + 8'd1;
                            end
                        end else if (pinv_st == PINV_MUL) begin
                            pinv_res_a_mul <= pinv_ca * pinv_norm_inv;
                            pinv_res_b_mul <= pinv_cb * pinv_norm_inv;
                            pinv_st <= PINV_REDUCE;
                        end else begin
                            result_a <= red_full(pinv_res_a_mul);
                            result_b <= red_full(pinv_res_b_mul);
                            done <= 1; busy <= 0; pinv_st <= 0; state <= S_IDLE;
                        end
                    end
                    default: begin busy <= 0; state <= S_IDLE; end
                endcase
            endcase
        end
    end

    // ── Quadratic norm invariant checker ──────────────────────────
    // N(a+bφ) = a² + ab - b² mod L_P
    // PSCALE: N(out) ≡ -N(in)   (φ-multiplication negates the norm)
    // PCHIRAL: N(out) ≡ N(in)   (conjugation preserves the norm)
    wire [L_P_BITS-1:0]  norm_out = phi_norm(result_a, result_b);
    wire [L_P_BITS-1:0]  pmul_norm_expected = red_full(active_norm_lhs * active_norm_rhs);
    wire [L_P_BITS-1:0]  pinv_norm_product = red_full(active_norm_lhs * norm_out);

    // PSCALE: N(out) = L_P - N(in) (mod L_P)  [negation in the field]
    // PCHIRAL: N(out) = N(in)
    // PMUL: N(out) = N(lhs) * N(rhs)
    // PINV: N(in) * N(out) = 1
    assign norm_violation = done && !error && (
        (active_opcode == OP_PSCALE)  ? (norm_out != (active_norm_lhs == 0 ? 0 : L_P - active_norm_lhs)) :
        (active_opcode == OP_PCHIRAL) ? (norm_out != active_norm_lhs) :
        (active_opcode == OP_PMUL)    ? (norm_out != pmul_norm_expected) :
        (active_opcode == OP_PINV)    ? (pinv_norm_product != {{(L_P_BITS-1){1'b0}}, 1'b1}) :
        1'b0
    );
endmodule
