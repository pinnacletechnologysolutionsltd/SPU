// spu13_lucas_sidecar.v -- Artix/Tang SPI-visible Lucas MAC adapter.
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
// Probe instruction format, delivered through the existing SPI CMD 0xB1 path:
//   [63:56] opcode: D0=PSCALE, D1=PCHIRAL, D2=PMUL, D3=PINV
//                   D4=PHSLK_LOAD, D5=PHSLK_EXEC
//   [55:52] destination QR lane
//   [51:42] coefficient a, reduced mod L_P
//   [41:32] coefficient b, reduced mod L_P
//   [31:22] coefficient c, reduced mod L_P (PMUL only)
//   [21:12] coefficient d, reduced mod L_P (PMUL only)
//   [11:0]  reserved
//
// For PHSLK, D4 loads fraction 1 as n1=(a,b), d1=(c,d).  D5 executes
// against fraction 2 encoded in the same fields as n2=(a,b), d2=(c,d).
// Result commit packs {zero_divisor, coherent} as the normal {b, a} pair.
//
// Result commit packs a + b*phi into QR component A as {b[31:0], a[31:0]}.
// QR components B/C/D are zero for this first sidecar proof.

module spu13_lucas_sidecar #(
    parameter L_P = 521,
    parameter L_P_BITS = 10,
    parameter MAC_CE_DIV = 64
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        inst_valid,
    input  wire [63:0] inst_word,
    output wire        inst_claimed,
    output reg         busy,
    output reg         error,
    output reg         qr_commit_valid,
    output reg  [3:0]  qr_commit_lane,
    output reg  [63:0] qr_commit_A,
    output reg  [63:0] qr_commit_B,
    output reg  [63:0] qr_commit_C,
    output reg  [63:0] qr_commit_D,
    output wire        norm_violation
);
    localparam [7:0] OP_PSCALE  = 8'hD0;
    localparam [7:0] OP_PCHIRAL = 8'hD1;
    localparam [7:0] OP_PMUL    = 8'hD2;
    localparam [7:0] OP_PINV    = 8'hD3;
    localparam [7:0] OP_PHSLK_LOAD = 8'hD4;
    localparam [7:0] OP_PHSLK_EXEC = 8'hD5;
    localparam [L_P_BITS-1:0] L_P_MOD = L_P;
    localparam [1:0] SIDE_IDLE = 2'd0;
    localparam [1:0] SIDE_PMUL = 2'd1;
    localparam [1:0] SIDE_PINV = 2'd2;
    localparam [1:0] PINV_NORM_REDUCE = 2'd0;
    localparam [1:0] PINV_TRY_REDUCE = 2'd1;
    localparam [1:0] PINV_RESULT_REDUCE = 2'd2;

    wire [7:0] op;
    assign op = inst_word[63:56];
    wire sidecar_op;
    assign sidecar_op = (op == OP_PSCALE) || (op == OP_PCHIRAL) ||
                        (op == OP_PMUL) || (op == OP_PINV) ||
                        (op == OP_PHSLK_LOAD) || (op == OP_PHSLK_EXEC);
    assign inst_claimed = inst_valid && sidecar_op;

    function [L_P_BITS-1:0] red_input;
        input [L_P_BITS-1:0] x;
        begin
            red_input = (x >= L_P_MOD) ? x - L_P_MOD : x;
        end
    endfunction

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

    reg         mac_start;
    reg  [2:0]  mac_opcode;
    reg  [L_P_BITS-1:0] mac_a;
    reg  [L_P_BITS-1:0] mac_b;
    reg  [L_P_BITS-1:0] mac_c;
    reg  [L_P_BITS-1:0] mac_d;
    reg  [L_P_BITS-1:0] mac_phslk_n2_a;
    reg  [L_P_BITS-1:0] mac_phslk_n2_b;
    reg  [L_P_BITS-1:0] mac_phslk_d2_a;
    reg  [L_P_BITS-1:0] mac_phslk_d2_b;
    wire        mac_busy;
    wire        mac_done;
    wire        mac_error;
    wire [L_P_BITS-1:0] mac_result_a;
    wire [L_P_BITS-1:0] mac_result_b;
    wire        mac_phslk_coherent;
    wire        mac_phslk_zero_divisor;
    wire        mac_norm_violation;
    localparam integer MAC_CE_BITS = (MAC_CE_DIV <= 1) ? 1 : $clog2(MAC_CE_DIV);
    reg [MAC_CE_BITS-1:0] mac_ce_ctr;
    wire mac_ce = (MAC_CE_DIV <= 1) ? 1'b1 : (mac_ce_ctr == MAC_CE_DIV - 1);

    spu13_lucas_mac #(
        .L_P(L_P),
        .L_P_BITS(L_P_BITS),
        .FAST_ONLY(0)
    ) u_mac (
        .clk(clk),
        .rst_n(rst_n),
        .ce(mac_ce),
        .start(mac_start),
        .opcode(mac_opcode),
        .op_a(mac_a),
        .op_b(mac_b),
        .op_c(mac_c),
        .op_d(mac_d),
        .phslk_n2_a(mac_phslk_n2_a),
        .phslk_n2_b(mac_phslk_n2_b),
        .phslk_d2_a(mac_phslk_d2_a),
        .phslk_d2_b(mac_phslk_d2_b),
        .busy(mac_busy),
        .done(mac_done),
        .error(mac_error),
        .result_a(mac_result_a),
        .result_b(mac_result_b),
        .phslk_coherent(mac_phslk_coherent),
        .phslk_zero_divisor(mac_phslk_zero_divisor),
        .norm_violation(mac_norm_violation)
    );

    assign norm_violation = mac_norm_violation;

    reg [3:0] lane_r;
    reg phslk_loaded;
    reg [L_P_BITS-1:0] phslk_n1_a;
    reg [L_P_BITS-1:0] phslk_n1_b;
    reg [L_P_BITS-1:0] phslk_d1_a;
    reg [L_P_BITS-1:0] phslk_d1_b;
    reg [1:0] side_state;
    reg [1:0] pmul_phase;
    reg [L_P_BITS-1:0] pmul_a;
    reg [L_P_BITS-1:0] pmul_b;
    reg [L_P_BITS-1:0] pmul_c;
    reg [L_P_BITS-1:0] pmul_d;
    reg [31:0] pmul_ac;
    reg [31:0] pmul_bd;
    reg [31:0] pmul_ad;
    reg [31:0] pmul_bc;
    reg [31:0] pmul_sum_a;
    reg [31:0] pmul_sum_b;
    reg [1:0] pinv_phase;
    reg [L_P_BITS-1:0] pinv_ca;
    reg [L_P_BITS-1:0] pinv_cb;
    reg [L_P_BITS-1:0] pinv_norm;
    reg [L_P_BITS-1:0] pinv_candidate;
    reg [31:0] pinv_norm_work;
    reg [31:0] pinv_prod_work;
    reg [31:0] pinv_res_a_work;
    reg [31:0] pinv_res_b_work;
    reg [L_P_BITS-1:0] in_a;
    reg [L_P_BITS-1:0] in_b;
    reg [L_P_BITS-1:0] fast_a;
    reg [L_P_BITS-1:0] fast_b;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy <= 1'b0;
            error <= 1'b0;
            mac_start <= 1'b0;
            mac_ce_ctr <= {MAC_CE_BITS{1'b0}};
            mac_opcode <= 3'd0;
            mac_a <= {L_P_BITS{1'b0}};
            mac_b <= {L_P_BITS{1'b0}};
            mac_c <= {L_P_BITS{1'b0}};
            mac_d <= {L_P_BITS{1'b0}};
            mac_phslk_n2_a <= {L_P_BITS{1'b0}};
            mac_phslk_n2_b <= {L_P_BITS{1'b0}};
            mac_phslk_d2_a <= {L_P_BITS{1'b0}};
            mac_phslk_d2_b <= {L_P_BITS{1'b0}};
            lane_r <= 4'd0;
            phslk_loaded <= 1'b0;
            phslk_n1_a <= {L_P_BITS{1'b0}};
            phslk_n1_b <= {L_P_BITS{1'b0}};
            phslk_d1_a <= {L_P_BITS{1'b0}};
            phslk_d1_b <= {L_P_BITS{1'b0}};
            side_state <= SIDE_IDLE;
            pmul_phase <= 2'd0;
            pmul_a <= {L_P_BITS{1'b0}};
            pmul_b <= {L_P_BITS{1'b0}};
            pmul_c <= {L_P_BITS{1'b0}};
            pmul_d <= {L_P_BITS{1'b0}};
            pmul_ac <= 32'd0;
            pmul_bd <= 32'd0;
            pmul_ad <= 32'd0;
            pmul_bc <= 32'd0;
            pmul_sum_a <= 32'd0;
            pmul_sum_b <= 32'd0;
            pinv_phase <= PINV_NORM_REDUCE;
            pinv_ca <= {L_P_BITS{1'b0}};
            pinv_cb <= {L_P_BITS{1'b0}};
            pinv_norm <= {L_P_BITS{1'b0}};
            pinv_candidate <= {L_P_BITS{1'b0}};
            pinv_norm_work <= 32'd0;
            pinv_prod_work <= 32'd0;
            pinv_res_a_work <= 32'd0;
            pinv_res_b_work <= 32'd0;
            qr_commit_valid <= 1'b0;
            qr_commit_lane <= 4'd0;
            qr_commit_A <= 64'd0;
            qr_commit_B <= 64'd0;
            qr_commit_C <= 64'd0;
            qr_commit_D <= 64'd0;
        end else begin
            if (MAC_CE_DIV > 1) begin
                mac_ce_ctr <= mac_ce ? {MAC_CE_BITS{1'b0}} : mac_ce_ctr + {{(MAC_CE_BITS-1){1'b0}}, 1'b1};
            end
            if (mac_start && mac_ce) begin
                mac_start <= 1'b0;
            end
            qr_commit_valid <= 1'b0;
            error <= 1'b0;

            if (busy && side_state == SIDE_PMUL && mac_ce) begin
                case (pmul_phase)
                    2'd0: begin
                        pmul_ac <= pmul_a * pmul_c;
                        pmul_bd <= pmul_b * pmul_d;
                        pmul_ad <= pmul_a * pmul_d;
                        pmul_bc <= pmul_b * pmul_c;
                        pmul_phase <= 2'd1;
                    end
                    2'd1: begin
                        pmul_sum_a <= pmul_ac + pmul_bd;
                        pmul_sum_b <= pmul_ad + pmul_bc + pmul_bd;
                        pmul_phase <= 2'd2;
                    end
                    default: begin
                        if (pmul_sum_a >= L_P) begin
                            pmul_sum_a <= pmul_sum_a - L_P;
                        end
                        if (pmul_sum_b >= L_P) begin
                            pmul_sum_b <= pmul_sum_b - L_P;
                        end
                        if (pmul_sum_a < L_P && pmul_sum_b < L_P) begin
                            busy <= 1'b0;
                            side_state <= SIDE_IDLE;
                            qr_commit_valid <= 1'b1;
                            qr_commit_lane <= lane_r;
                            qr_commit_A <= {22'd0, pmul_sum_b[L_P_BITS-1:0], 22'd0, pmul_sum_a[L_P_BITS-1:0]};
                            qr_commit_B <= 64'd0;
                            qr_commit_C <= 64'd0;
                            qr_commit_D <= 64'd0;
                        end
                    end
                endcase
            end else if (busy && side_state == SIDE_PINV && mac_ce) begin
                case (pinv_phase)
                    PINV_TRY_REDUCE: begin
                        if (pinv_norm == 0) begin
                            busy <= 1'b0;
                            error <= 1'b1;
                            side_state <= SIDE_IDLE;
                        end else if (red_full(pinv_norm * pinv_candidate) == 1) begin
                            pinv_res_a_work <= pinv_ca * pinv_candidate;
                            pinv_res_b_work <= pinv_cb * pinv_candidate;
                            pinv_phase <= PINV_RESULT_REDUCE;
                        end else if (pinv_candidate == (L_P - 1)) begin
                            busy <= 1'b0;
                            error <= 1'b1;
                            side_state <= SIDE_IDLE;
                        end else begin
                            pinv_candidate <= pinv_candidate + {{(L_P_BITS-1){1'b0}}, 1'b1};
                        end
                    end
                    default: begin
                        busy <= 1'b0;
                        side_state <= SIDE_IDLE;
                        qr_commit_valid <= 1'b1;
                        qr_commit_lane <= lane_r;
                        qr_commit_A <= {22'd0, red_full(pinv_res_b_work),
                                        22'd0, red_full(pinv_res_a_work)};
                        qr_commit_B <= 64'd0;
                        qr_commit_C <= 64'd0;
                        qr_commit_D <= 64'd0;
                    end
                endcase
            end else if (!busy && inst_claimed) begin
                in_a = red_input(inst_word[51:42]);
                in_b = red_input(inst_word[41:32]);
                if (op == OP_PHSLK_LOAD) begin
                    phslk_n1_a <= in_a;
                    phslk_n1_b <= in_b;
                    phslk_d1_a <= red_input(inst_word[31:22]);
                    phslk_d1_b <= red_input(inst_word[21:12]);
                    phslk_loaded <= 1'b1;
                end else if (op == OP_PHSLK_EXEC && !phslk_loaded) begin
                    error <= 1'b1;
                end else if (op == OP_PSCALE || op == OP_PCHIRAL) begin
                    if (op == OP_PSCALE) begin
                        fast_a = in_b;
                        fast_b = red_pair({1'b0, in_a} + {1'b0, in_b});
                    end else begin
                        fast_a = red_pair({1'b0, in_a} + {1'b0, in_b});
                        fast_b = (in_b == 0) ? {L_P_BITS{1'b0}} :
                                 red_pair((2 * L_P) - in_b);
                    end
                    qr_commit_valid <= 1'b1;
                    qr_commit_lane <= (inst_word[55:52] > 4'd12) ? 4'd0 : inst_word[55:52];
                    qr_commit_A <= {22'd0, fast_b, 22'd0, fast_a};
                    qr_commit_B <= 64'd0;
                    qr_commit_C <= 64'd0;
                    qr_commit_D <= 64'd0;
                end else if (op == OP_PMUL) begin
                    lane_r <= (inst_word[55:52] > 4'd12) ? 4'd0 : inst_word[55:52];
                    pmul_a <= in_a;
                    pmul_b <= in_b;
                    pmul_c <= red_input(inst_word[31:22]);
                    pmul_d <= red_input(inst_word[21:12]);
                    pmul_phase <= 2'd0;
                    side_state <= SIDE_PMUL;
                    busy <= 1'b1;
                end else if (op == OP_PINV) begin
                    lane_r <= (inst_word[55:52] > 4'd12) ? 4'd0 : inst_word[55:52];
                    fast_a = red_pair({1'b0, in_a} + {1'b0, in_b});
                    fast_b = (in_b == 0) ? {L_P_BITS{1'b0}} :
                             red_pair((2 * L_P) - in_b);
                    pinv_ca <= fast_a;
                    pinv_cb <= fast_b;
                    pinv_norm <= red_full((in_a * in_a) + (in_a * in_b) +
                                          (L_P * L_P) - (in_b * in_b));
                    pinv_candidate <= {{(L_P_BITS-1){1'b0}}, 1'b1};
                    pinv_phase <= PINV_TRY_REDUCE;
                    side_state <= SIDE_PINV;
                    busy <= 1'b1;
                end else begin
                    lane_r <= (inst_word[55:52] > 4'd12) ? 4'd0 : inst_word[55:52];
                    mac_opcode <= (op == OP_PSCALE) ? 3'd0 :
                                  (op == OP_PCHIRAL) ? 3'd1 :
                                  (op == OP_PMUL) ? 3'd2 :
                                  (op == OP_PINV) ? 3'd3 : 3'd4;
                    mac_a <= (op == OP_PHSLK_EXEC) ? phslk_n1_a : in_a;
                    mac_b <= (op == OP_PHSLK_EXEC) ? phslk_n1_b : in_b;
                    mac_c <= (op == OP_PHSLK_EXEC) ? phslk_d1_a : red_input(inst_word[31:22]);
                    mac_d <= (op == OP_PHSLK_EXEC) ? phslk_d1_b : red_input(inst_word[21:12]);
                    mac_phslk_n2_a <= red_input(inst_word[51:42]);
                    mac_phslk_n2_b <= red_input(inst_word[41:32]);
                    mac_phslk_d2_a <= red_input(inst_word[31:22]);
                    mac_phslk_d2_b <= red_input(inst_word[21:12]);
                    mac_start <= 1'b1;
                    busy <= 1'b1;
                end
            end else if (busy && (mac_done || mac_error)) begin
                busy <= 1'b0;
                error <= mac_error;
                if (mac_done && !mac_error) begin
                    qr_commit_valid <= 1'b1;
                    qr_commit_lane <= lane_r;
                    qr_commit_A <= {22'd0, mac_result_b, 22'd0, mac_result_a};
                    qr_commit_B <= 64'd0;
                    qr_commit_C <= 64'd0;
                    qr_commit_D <= 64'd0;
                end
            end
        end
    end
endmodule
