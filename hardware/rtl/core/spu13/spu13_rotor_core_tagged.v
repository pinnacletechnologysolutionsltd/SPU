// spu13_rotor_core_tagged.v — Exponent-tagged ROTC with deferred reduction
//
// Implements the state machine from docs/ROTC_EXPONENT_STATE_MACHINE.md §2–3.
// Each surd lane (P, Q) of each Quadray axis (A, B, C, D) carries a
// (value: signed 32-bit, exponent: 4-bit unsigned) pair.
// true_value = value / 3^exponent.
//
// Operations: ROTATE (op=00), ALIGN (op=01), REDUCE (op=10).
// Faults: MISALIGNED[0], OVERFLOW[1], INEXACT[2].

module spu13_rotor_core_tagged #(
    parameter EXP_WIDTH = 4,
    parameter ENABLE_REDUCE_DIV = 1  // 0 = stub out dividers for area-constrained synth
) (
    input  wire        clk,
    input  wire        rst_n,

    input  wire        start,
    output reg         done,

    input  wire [1:0]  op,

    // Quadray Input Coordinates (A,B,C,D) — value part only
    input  wire [63:0] A_in, B_in, C_in, D_in,

    // Per-lane exponents (flat ports)
    input  wire [EXP_WIDTH-1:0] exp_ap_in,
    input  wire [EXP_WIDTH-1:0] exp_aq_in,
    input  wire [EXP_WIDTH-1:0] exp_bp_in,
    input  wire [EXP_WIDTH-1:0] exp_bq_in,
    input  wire [EXP_WIDTH-1:0] exp_cp_in,
    input  wire [EXP_WIDTH-1:0] exp_cq_in,
    input  wire [EXP_WIDTH-1:0] exp_dp_in,
    input  wire [EXP_WIDTH-1:0] exp_dq_in,

    // Rotation Coefficients (F,G,H) — integer scalars as {32'd0, val}
    input  wire [63:0] F, G, H,

    // ALIGN target exponent and lane select (0=AP,1=AQ,2=BP,3=BQ,4=CP,5=CQ,6=DP,7=DQ)
    input  wire [EXP_WIDTH-1:0] align_target,
    input  wire [2:0]  align_lane,

    // REDUCE lane select
    input  wire [2:0]  reduce_lane,

    input  wire [5:0]  angle,
    input  wire        bypass_p5,
    input  wire        bypass_p5_inv,

    // Quadray Output Coordinates
    output reg  [63:0] A_out, B_out, C_out, D_out,

    // Per-lane output exponents (flat ports)
    output reg  [EXP_WIDTH-1:0] exp_ap_out,
    output reg  [EXP_WIDTH-1:0] exp_aq_out,
    output reg  [EXP_WIDTH-1:0] exp_bp_out,
    output reg  [EXP_WIDTH-1:0] exp_bq_out,
    output reg  [EXP_WIDTH-1:0] exp_cp_out,
    output reg  [EXP_WIDTH-1:0] exp_cq_out,
    output reg  [EXP_WIDTH-1:0] exp_dp_out,
    output reg  [EXP_WIDTH-1:0] exp_dq_out,

    // Fault flags: {INEXACT, OVERFLOW, MISALIGNED}
    output reg  [2:0]  fault,

    output reg  [3:0]  debug_state
);

    localparam S_IDLE       = 4'd0;
    localparam S_ROTATE     = 4'd1;
    localparam S_ALIGN      = 4'd2;
    localparam S_REDUCE     = 4'd3;
    localparam S_REDUCE_DIV = 4'd4;
    localparam S_DONE       = 4'd15;

    localparam MAX_EXPONENT = 4'd15;

    // ── Powers of 3 lookup (3^0 through 3^15) ────────────────────────
    function [31:0] pow3;
        input [3:0] e;
        begin
            case (e)
                4'd0:  pow3 = 32'd1;
                4'd1:  pow3 = 32'd3;
                4'd2:  pow3 = 32'd9;
                4'd3:  pow3 = 32'd27;
                4'd4:  pow3 = 32'd81;
                4'd5:  pow3 = 32'd243;
                4'd6:  pow3 = 32'd729;
                4'd7:  pow3 = 32'd2187;
                4'd8:  pow3 = 32'd6561;
                4'd9:  pow3 = 32'd19683;
                4'd10: pow3 = 32'd59049;
                4'd11: pow3 = 32'd177147;
                4'd12: pow3 = 32'd531441;
                4'd13: pow3 = 32'd1594323;
                4'd14: pow3 = 32'd4782969;
                4'd15: pow3 = 32'd14348907;
            endcase
        end
    endfunction

    // ── Lane exponent reader ──────────────────────────────────────────
    function [EXP_WIDTH-1:0] get_exp;
        input [2:0] lane;
        begin
            case (lane)
                3'd0: get_exp = exp_ap_in;
                3'd1: get_exp = exp_aq_in;
                3'd2: get_exp = exp_bp_in;
                3'd3: get_exp = exp_bq_in;
                3'd4: get_exp = exp_cp_in;
                3'd5: get_exp = exp_cq_in;
                3'd6: get_exp = exp_dp_in;
                3'd7: get_exp = exp_dq_in;
                default: get_exp = 4'd0;
            endcase
        end
    endfunction

    // ── Multiply a signed 32-bit value by 3^k ────────────────────────
    function signed [63:0] mul_pow3;
        input signed [31:0] val;
        input [EXP_WIDTH-1:0] k;
        begin
            mul_pow3 = $signed(val) * $signed({1'b0, pow3(k)});
        end
    endfunction

    // ── State ─────────────────────────────────────────────────────────
    reg [3:0] state;

    // Intermediate values during REDUCE
    reg signed [63:0] reduce_val64;
    reg [EXP_WIDTH-1:0] reduce_exp;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= S_IDLE;
            done        <= 1'b0;
            fault       <= 3'b0;
            debug_state <= S_IDLE;
            A_out <= 64'd0; B_out <= 64'd0; C_out <= 64'd0; D_out <= 64'd0;
            exp_ap_out <= 0; exp_aq_out <= 0;
            exp_bp_out <= 0; exp_bq_out <= 0;
            exp_cp_out <= 0; exp_cq_out <= 0;
            exp_dp_out <= 0; exp_dq_out <= 0;
            reduce_val64 <= 64'd0;
            reduce_exp   <= 4'd0;
        end else begin
            done  <= 1'b0;
            // fault is NOT cleared here — it's set in specific states
            // and persists until the next start.

            case (state)
                S_IDLE: begin
                    if (start) begin
                        fault <= 3'b0;  // clear on new start
                        if (bypass_p5) begin
                            A_out <= A_in; B_out <= D_in; C_out <= B_in; D_out <= C_in;
                            // A unchanged; B←D, C←B, D←C
                            exp_ap_out <= exp_ap_in; exp_aq_out <= exp_aq_in;
                            exp_bp_out <= exp_dp_in; exp_bq_out <= exp_dq_in;
                            exp_cp_out <= exp_bp_in; exp_cq_out <= exp_bq_in;
                            exp_dp_out <= exp_cp_in; exp_dq_out <= exp_cq_in;
                            state <= S_DONE;
                        end else if (bypass_p5_inv) begin
                            A_out <= A_in; B_out <= C_in; C_out <= D_in; D_out <= B_in;
                            exp_ap_out <= exp_ap_in; exp_aq_out <= exp_aq_in;
                            exp_bp_out <= exp_cp_in; exp_bq_out <= exp_cq_in;
                            exp_cp_out <= exp_dp_in; exp_cq_out <= exp_dq_in;
                            exp_dp_out <= exp_bp_in; exp_dq_out <= exp_bq_in;
                            state <= S_DONE;
                        end else begin
                            case (op)
                                2'b00: state <= S_ROTATE;
                                2'b01: state <= S_ALIGN;
                                2'b10: state <= S_REDUCE;
                                default: begin
                                    A_out <= A_in; B_out <= B_in; C_out <= C_in; D_out <= D_in;
                                    exp_ap_out <= exp_ap_in; exp_aq_out <= exp_aq_in;
                                    exp_bp_out <= exp_bp_in; exp_bq_out <= exp_bq_in;
                                    exp_cp_out <= exp_cp_in; exp_cq_out <= exp_cq_in;
                                    exp_dp_out <= exp_dp_in; exp_dq_out <= exp_dq_in;
                                    state <= S_DONE;
                                end
                            endcase
                        end
                    end
                end

                // ── ROTATE(angle) ─────────────────────────────────────
                S_ROTATE: begin
                    A_out <= A_in;
                    exp_ap_out <= exp_ap_in;
                    exp_aq_out <= exp_aq_in;

                    // Check MISALIGNED: all 6 B/C/D exponents must match
                    if (exp_bp_in != exp_cp_in || exp_bp_in != exp_dp_in ||
                        exp_bq_in != exp_cq_in || exp_bq_in != exp_dq_in ||
                        exp_bp_in != exp_bq_in) begin
                        fault[0] <= 1'b1;  // MISALIGNED
                        B_out <= B_in; C_out <= C_in; D_out <= D_in;
                        exp_bp_out <= exp_bp_in; exp_bq_out <= exp_bq_in;
                        exp_cp_out <= exp_cp_in; exp_cq_out <= exp_cq_in;
                        exp_dp_out <= exp_dp_in; exp_dq_out <= exp_dq_in;
                        state <= S_DONE;
                    end else if (exp_bp_in >= MAX_EXPONENT) begin
                        fault[1] <= 1'b1;  // OVERFLOW
                        B_out <= B_in; C_out <= C_in; D_out <= D_in;
                        exp_bp_out <= exp_bp_in; exp_bq_out <= exp_bq_in;
                        exp_cp_out <= exp_cp_in; exp_cq_out <= exp_cq_in;
                        exp_dp_out <= exp_dp_in; exp_dq_out <= exp_dq_in;
                        state <= S_DONE;
                    end else begin
                        // Apply integer coefficients via circulant matrix.
                        // F, G, H are scalars packed in bits [31:0].
                        B_out[63:32] <=
                            $signed(B_in[63:32]) * $signed(F[31:0]) +
                            $signed(C_in[63:32]) * $signed(H[31:0]) +
                            $signed(D_in[63:32]) * $signed(G[31:0]);
                        B_out[31:0] <=
                            $signed(B_in[31:0]) * $signed(F[31:0]) +
                            $signed(C_in[31:0]) * $signed(H[31:0]) +
                            $signed(D_in[31:0]) * $signed(G[31:0]);

                        C_out[63:32] <=
                            $signed(B_in[63:32]) * $signed(G[31:0]) +
                            $signed(C_in[63:32]) * $signed(F[31:0]) +
                            $signed(D_in[63:32]) * $signed(H[31:0]);
                        C_out[31:0] <=
                            $signed(B_in[31:0]) * $signed(G[31:0]) +
                            $signed(C_in[31:0]) * $signed(F[31:0]) +
                            $signed(D_in[31:0]) * $signed(H[31:0]);

                        D_out[63:32] <=
                            $signed(B_in[63:32]) * $signed(H[31:0]) +
                            $signed(C_in[63:32]) * $signed(G[31:0]) +
                            $signed(D_in[63:32]) * $signed(F[31:0]);
                        D_out[31:0] <=
                            $signed(B_in[31:0]) * $signed(H[31:0]) +
                            $signed(C_in[31:0]) * $signed(G[31:0]) +
                            $signed(D_in[31:0]) * $signed(F[31:0]);

                        // Increment exponents for B, C, D
                        exp_bp_out <= exp_bp_in + 1;
                        exp_bq_out <= exp_bq_in + 1;
                        exp_cp_out <= exp_cp_in + 1;
                        exp_cq_out <= exp_cq_in + 1;
                        exp_dp_out <= exp_dp_in + 1;
                        exp_dq_out <= exp_dq_in + 1;

                        state <= S_DONE;
                    end
                end

                // ── ALIGN(lane, target_exponent) ──────────────────────
                S_ALIGN: begin
                    // Default: preserve all lanes
                    A_out <= A_in; B_out <= B_in; C_out <= C_in; D_out <= D_in;
                    exp_ap_out <= exp_ap_in; exp_aq_out <= exp_aq_in;
                    exp_bp_out <= exp_bp_in; exp_bq_out <= exp_bq_in;
                    exp_cp_out <= exp_cp_in; exp_cq_out <= exp_cq_in;
                    exp_dp_out <= exp_dp_in; exp_dq_out <= exp_dq_in;

                    if (get_exp(align_lane) < align_target) begin
                        // Multiply value by 3^(target - current)
                        case (align_lane)
                            3'd0: begin
                                A_out[63:32] <= mul_pow3(A_in[63:32],
                                    align_target - exp_ap_in);
                                exp_ap_out <= align_target;
                            end
                            3'd1: begin
                                A_out[31:0] <= mul_pow3(A_in[31:0],
                                    align_target - exp_aq_in);
                                exp_aq_out <= align_target;
                            end
                            3'd2: begin
                                B_out[63:32] <= mul_pow3(B_in[63:32],
                                    align_target - exp_bp_in);
                                exp_bp_out <= align_target;
                            end
                            3'd3: begin
                                B_out[31:0] <= mul_pow3(B_in[31:0],
                                    align_target - exp_bq_in);
                                exp_bq_out <= align_target;
                            end
                            3'd4: begin
                                C_out[63:32] <= mul_pow3(C_in[63:32],
                                    align_target - exp_cp_in);
                                exp_cp_out <= align_target;
                            end
                            3'd5: begin
                                C_out[31:0] <= mul_pow3(C_in[31:0],
                                    align_target - exp_cq_in);
                                exp_cq_out <= align_target;
                            end
                            3'd6: begin
                                D_out[63:32] <= mul_pow3(D_in[63:32],
                                    align_target - exp_dp_in);
                                exp_dp_out <= align_target;
                            end
                            3'd7: begin
                                D_out[31:0] <= mul_pow3(D_in[31:0],
                                    align_target - exp_dq_in);
                                exp_dq_out <= align_target;
                            end
                        endcase
                    end
                    state <= S_DONE;
                end

                // ── REDUCE(lane) ──────────────────────────────────────
                S_REDUCE: begin
                    A_out <= A_in; B_out <= B_in; C_out <= C_in; D_out <= D_in;
                    exp_ap_out <= exp_ap_in; exp_aq_out <= exp_aq_in;
                    exp_bp_out <= exp_bp_in; exp_bq_out <= exp_bq_in;
                    exp_cp_out <= exp_cp_in; exp_cq_out <= exp_cq_in;
                    exp_dp_out <= exp_dp_in; exp_dq_out <= exp_dq_in;

                    reduce_exp <= get_exp(reduce_lane);
                    if (get_exp(reduce_lane) == 0) begin
                        state <= S_DONE;
                    end else begin
                        // Load the value to reduce
                        case (reduce_lane)
                            3'd0: reduce_val64 <= {32'd0, A_in[63:32]};
                            3'd1: reduce_val64 <= {32'd0, A_in[31:0]};
                            3'd2: reduce_val64 <= {32'd0, B_in[63:32]};
                            3'd3: reduce_val64 <= {32'd0, B_in[31:0]};
                            3'd4: reduce_val64 <= {32'd0, C_in[63:32]};
                            3'd5: reduce_val64 <= {32'd0, C_in[31:0]};
                            3'd6: reduce_val64 <= {32'd0, D_in[63:32]};
                            3'd7: reduce_val64 <= {32'd0, D_in[31:0]};
                        endcase
                        state <= S_REDUCE_DIV;
                    end
                end

                // ── REDUCE: division and exactness ────────────────────
                S_REDUCE_DIV: begin
                    A_out <= A_in; B_out <= B_in; C_out <= C_in; D_out <= D_in;
                    exp_ap_out <= exp_ap_in; exp_aq_out <= exp_aq_in;
                    exp_bp_out <= exp_bp_in; exp_bq_out <= exp_bq_in;
                    exp_cp_out <= exp_cp_in; exp_cq_out <= exp_cq_in;
                    exp_dp_out <= exp_dp_in; exp_dq_out <= exp_dq_in;

                    if (ENABLE_REDUCE_DIV) begin
                        // Exactness: value must be divisible by 3^exponent
                        if (($signed(reduce_val64) % $signed({1'b0, pow3(reduce_exp)})) == 0) begin
                            case (reduce_lane)
                                3'd0: A_out[63:32] <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd1: A_out[31:0]  <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd2: B_out[63:32] <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd3: B_out[31:0]  <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd4: C_out[63:32] <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd5: C_out[31:0]  <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd6: D_out[63:32] <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                                3'd7: D_out[31:0]  <= $signed(reduce_val64) /
                                    $signed({1'b0, pow3(reduce_exp)});
                            endcase
                            case (reduce_lane)
                                3'd0: exp_ap_out <= 4'd0;
                                3'd1: exp_aq_out <= 4'd0;
                                3'd2: exp_bp_out <= 4'd0;
                                3'd3: exp_bq_out <= 4'd0;
                                3'd4: exp_cp_out <= 4'd0;
                                3'd5: exp_cq_out <= 4'd0;
                                3'd6: exp_dp_out <= 4'd0;
                                3'd7: exp_dq_out <= 4'd0;
                            endcase
                        end else begin
                            fault[2] <= 1'b1;  // INEXACT
                        end
                    end else begin
                        // Stub: skip division for area-constrained synth.
                        // REDUCE is not exercised by the probe self-check FSM,
                        // but if it ever is, fault rather than silently
                        // reporting success on an un-reduced value -- same
                        // "detect, never silently corrupt" idiom as every
                        // other fault in this module.
                        fault[2] <= 1'b1;
                    end
                    state <= S_DONE;
                end

                S_DONE: begin
                    done  <= 1'b1;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase

            debug_state <= state;
        end
    end

endmodule
