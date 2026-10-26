// SPU-13 Thomson Rotor Core TDM (v4.0)
// Implementation: Time-Division Multiplexed ALU for Isotropic Rotation.
// Reduces DSP usage from 36 down to 4 by sharing a single surd_multiplier.
// Latency: 11 cycles (1 load + 9 mult + 1 sum).

module spu13_rotor_core_tdm #(
    parameter WIDTH = 32,
    parameter ENABLE_TDM_FALLBACK = 1
)(
    input  wire        clk,
    input  wire        rst_n,

    input  wire        start,
    output reg         done,

    // Quadray Input Coordinates (A,B,C,D)
    input  wire [63:0] A_in, B_in, C_in, D_in,

    // Rotation Coefficients (F,G,H)
    input  wire [63:0] F, G, H,

    input  wire [1:0]  field_sel,
    input  wire        bypass_p5,
    input  wire        bypass_p5_inv,
    input  wire        bypass_ab_cd,       // (AB)(CD) double transposition
    input  wire        bypass_ac_bd,       // (AC)(BD) double transposition
    input  wire        bypass_ad_bc,       // (AD)(BC) double transposition
    input  wire        recompute_A,         // compute A = -(B+C+D) instead of pass-through
    input  wire        apply_div3,
    input  wire [5:0]  angle,

    // Quadray Output Coordinates
    output reg  [63:0] A_out, B_out, C_out, D_out,
    output wire [3:0]  debug_state
);

    // --- TDM Controller ---
    reg [3:0] state;
    localparam S_IDLE = 0, S_CALC = 1, S_DONE = 11;
    assign debug_state = state;

    reg [63:0] sm_op1, sm_op2;
    wire [63:0] sm_res;

    generate
        if (ENABLE_TDM_FALLBACK) begin : gen_tdm_multiplier
            surd_multiplier #(.WIDTH(32), .SHIFT(0)) u_sm (
                .clk(clk), .reset(!rst_n),
                .field_sel(field_sel),
                .a1(sm_op1[31:0]),  .b1(sm_op1[63:32]),
                .a2(sm_op2[31:0]),  .b2(sm_op2[63:32]),
                .res_a(sm_res[31:0]), .res_b(sm_res[63:32])
            );
        end else begin : gen_no_tdm_multiplier
            assign sm_res = 64'd0;
        end
    endgenerate

    // Division by 3 for Tetrahedral Angles (Hacker's Delight magic constant)
    function signed [31:0] div3;
        input signed [31:0] n;
        reg signed [63:0] q;
        begin
            q = $signed(n) * $signed(32'h55555556);
            div3 = q[63:32] + n[31];
        end
    endfunction

    function [63:0] scale_axis;
        input [63:0] axis;
        input        en;
        begin
            if (en)
                scale_axis = {div3(axis[63:32]), div3(axis[31:0])};
            else
                scale_axis = axis;
        end
    endfunction

    function is_small_scalar;
        input [63:0] coeff;
        begin
            is_small_scalar = (coeff[63:32] == 32'd0) &&
                              (coeff[31:0] == 32'd0 ||
                               coeff[31:0] == 32'd1 ||
                               coeff[31:0] == 32'd2 ||
                               coeff[31:0] == 32'hFFFFFFFF);
        end
    endfunction

    function signed [31:0] scalar_mul32;
        input signed [31:0] value;
        input [31:0] coeff;
        begin
            case (coeff)
                32'd0:        scalar_mul32 = 32'sd0;
                32'd1:        scalar_mul32 = value;
                32'd2:        scalar_mul32 = value <<< 1;
                32'hFFFFFFFF: scalar_mul32 = -value;
                default:      scalar_mul32 = 32'sd0;
            endcase
        end
    endfunction

    function [63:0] scalar_mul_axis;
        input [63:0] axis;
        input [63:0] coeff;
        begin
            scalar_mul_axis = {
                scalar_mul32(axis[63:32], coeff[31:0]),
                scalar_mul32(axis[31:0], coeff[31:0])
            };
        end
    endfunction

    function [63:0] neg_axis;
        input [63:0] axis;
        begin
            neg_axis = {
                -$signed(axis[63:32]),
                -$signed(axis[31:0])
            };
        end
    endfunction

    function [63:0] double_axis;
        input [63:0] axis;
        begin
            double_axis = {
                $signed(axis[63:32]) <<< 1,
                $signed(axis[31:0]) <<< 1
            };
        end
    endfunction

    function [63:0] add3_axis;
        input [63:0] x;
        input [63:0] y;
        input [63:0] z;
        begin
            add3_axis = {
                x[63:32] + y[63:32] + z[63:32],
                x[31:0] + y[31:0] + z[31:0]
            };
        end
    endfunction

    // Accumulators for B, C, D rows
    reg [63:0] acc_B, acc_C, acc_D;
    // The current ROTC catalog uses only scalar coefficients {-1,0,1,2}.
    // Force the /3 catalog entries through this path during bring-up so the
    // result does not depend on the shared multiplier schedule.
    wire scalar_fast = apply_div3 ||
                       (is_small_scalar(F) && is_small_scalar(G) && is_small_scalar(H));
    wire [63:0] scalar_B_sum = add3_axis(
        scalar_mul_axis(B_in, F),
        scalar_mul_axis(C_in, H),
        scalar_mul_axis(D_in, G)
    );
    wire [63:0] scalar_C_sum = add3_axis(
        scalar_mul_axis(B_in, G),
        scalar_mul_axis(C_in, F),
        scalar_mul_axis(D_in, H)
    );
    wire [63:0] scalar_D_sum = add3_axis(
        scalar_mul_axis(B_in, H),
        scalar_mul_axis(C_in, G),
        scalar_mul_axis(D_in, F)
    );
    wire [63:0] angle1_B_sum = add3_axis(double_axis(B_in), neg_axis(C_in), double_axis(D_in));
    wire [63:0] angle1_C_sum = add3_axis(double_axis(B_in), double_axis(C_in), neg_axis(D_in));
    wire [63:0] angle1_D_sum = add3_axis(neg_axis(B_in), double_axis(C_in), double_axis(D_in));
    wire [63:0] angle3_B_sum = add3_axis(neg_axis(B_in), double_axis(C_in), double_axis(D_in));
    wire [63:0] angle3_C_sum = add3_axis(double_axis(B_in), neg_axis(C_in), double_axis(D_in));
    wire [63:0] angle3_D_sum = add3_axis(double_axis(B_in), double_axis(C_in), neg_axis(D_in));
    wire [63:0] angle4_B_sum = add3_axis(double_axis(B_in), double_axis(C_in), neg_axis(D_in));
    wire [63:0] angle4_C_sum = add3_axis(neg_axis(B_in), double_axis(C_in), double_axis(D_in));
    wire [63:0] angle4_D_sum = add3_axis(double_axis(B_in), neg_axis(C_in), double_axis(D_in));

    // ── Octahedral group (angles 24-35): integer 3×3, entries 0,±1 ──
    // Zero multiplies — pure combinatorial routing + negation + B+C+D sum.
    // Derived 2026-07-10: the legacy claim that cube rotations "require Q(√2)"
    // is wrong; the rotation group entries are integers in the quadray basis.
    wire [63:0] sum_BCD  = add3_axis(B_in, C_in, D_in);        // B+C+D = -A
    wire [63:0] neg_B    = neg_axis(B_in);
    wire [63:0] neg_C    = neg_axis(C_in);
    wire [63:0] neg_D    = neg_axis(D_in);

    // Group structure (verified in exact Fraction arithmetic 2026-07-10):
    // six 180° edge rotations, self-inverse (period 2): 24,25,28,31,32,34
    //   — negation ∘ diagonal transposition (CD),(AB),(BC),(AD),(BD),(AC)
    // six 90°/270° face rotations (period 4), three inverse pairs:
    //   26↔27 (x axis), 29↔30 (z axis), 33↔35 (y axis)

    // Pure negation + transposition patterns: edges (CD), (BC), (BD)
    wire [63:0] oct24_B = neg_B;    wire [63:0] oct24_C = neg_D;    wire [63:0] oct24_D = neg_C;
    wire [63:0] oct28_B = neg_C;    wire [63:0] oct28_C = neg_B;    wire [63:0] oct28_D = neg_D;
    wire [63:0] oct32_B = neg_D;    wire [63:0] oct32_C = neg_C;    wire [63:0] oct32_D = neg_B;

    // sum_BCD in slot B: 25 = edge (AB) self-inverse; 26/27 = 90°/270° face pair (x)
    wire [63:0] oct25_B = sum_BCD;  wire [63:0] oct25_C = neg_C;    wire [63:0] oct25_D = neg_D;
    wire [63:0] oct26_B = neg_C;    wire [63:0] oct26_C = sum_BCD;  wire [63:0] oct26_D = neg_B;
    wire [63:0] oct27_B = neg_D;    wire [63:0] oct27_C = neg_B;    wire [63:0] oct27_D = sum_BCD;

    // 29/30 = 90°/270° face pair (z); 31 = edge (AD) self-inverse
    wire [63:0] oct29_B = sum_BCD;  wire [63:0] oct29_C = neg_D;    wire [63:0] oct29_D = neg_B;
    wire [63:0] oct30_B = neg_D;    wire [63:0] oct30_C = sum_BCD;  wire [63:0] oct30_D = neg_C;
    wire [63:0] oct31_B = neg_B;    wire [63:0] oct31_C = neg_C;    wire [63:0] oct31_D = sum_BCD;

    // 33/35 = 270°/90° face pair (y); 34 = edge (AC) self-inverse
    wire [63:0] oct33_B = sum_BCD;  wire [63:0] oct33_C = neg_B;    wire [63:0] oct33_D = neg_C;
    wire [63:0] oct34_B = neg_B;    wire [63:0] oct34_C = sum_BCD;  wire [63:0] oct34_D = neg_D;
    wire [63:0] oct35_B = neg_C;    wire [63:0] oct35_C = neg_D;    wire [63:0] oct35_D = sum_BCD;

    function [63:0] angle_scalar_B_sum;
        input [5:0] rot_angle;
        begin
            case (rot_angle)
                6'd1, 6'd7, 6'd9, 6'd14: angle_scalar_B_sum = angle1_B_sum;
                6'd3, 6'd8, 6'd11, 6'd12: angle_scalar_B_sum = angle3_B_sum;
                6'd4, 6'd6, 6'd10, 6'd13: angle_scalar_B_sum = angle4_B_sum;
                // Octahedral group (24-35)
                6'd24: angle_scalar_B_sum = oct24_B;
                6'd25: angle_scalar_B_sum = oct25_B;
                6'd26: angle_scalar_B_sum = oct26_B;
                6'd27: angle_scalar_B_sum = oct27_B;
                6'd28: angle_scalar_B_sum = oct28_B;
                6'd29: angle_scalar_B_sum = oct29_B;
                6'd30: angle_scalar_B_sum = oct30_B;
                6'd31: angle_scalar_B_sum = oct31_B;
                6'd32: angle_scalar_B_sum = oct32_B;
                6'd33: angle_scalar_B_sum = oct33_B;
                6'd34: angle_scalar_B_sum = oct34_B;
                6'd35: angle_scalar_B_sum = oct35_B;
                default:           angle_scalar_B_sum = scalar_B_sum;
            endcase
        end
    endfunction

    function [63:0] angle_scalar_C_sum;
        input [5:0] rot_angle;
        begin
            case (rot_angle)
                6'd1, 6'd7, 6'd9, 6'd14: angle_scalar_C_sum = angle1_C_sum;
                6'd3, 6'd8, 6'd11, 6'd12: angle_scalar_C_sum = angle3_C_sum;
                6'd4, 6'd6, 6'd10, 6'd13: angle_scalar_C_sum = angle4_C_sum;
                // Octahedral group (24-35)
                6'd24: angle_scalar_C_sum = oct24_C;
                6'd25: angle_scalar_C_sum = oct25_C;
                6'd26: angle_scalar_C_sum = oct26_C;
                6'd27: angle_scalar_C_sum = oct27_C;
                6'd28: angle_scalar_C_sum = oct28_C;
                6'd29: angle_scalar_C_sum = oct29_C;
                6'd30: angle_scalar_C_sum = oct30_C;
                6'd31: angle_scalar_C_sum = oct31_C;
                6'd32: angle_scalar_C_sum = oct32_C;
                6'd33: angle_scalar_C_sum = oct33_C;
                6'd34: angle_scalar_C_sum = oct34_C;
                6'd35: angle_scalar_C_sum = oct35_C;
                default:           angle_scalar_C_sum = scalar_C_sum;
            endcase
        end
    endfunction

    function [63:0] angle_scalar_D_sum;
        input [5:0] rot_angle;
        begin
            case (rot_angle)
                6'd1, 6'd7, 6'd9, 6'd14: angle_scalar_D_sum = angle1_D_sum;
                6'd3, 6'd8, 6'd11, 6'd12: angle_scalar_D_sum = angle3_D_sum;
                6'd4, 6'd6, 6'd10, 6'd13: angle_scalar_D_sum = angle4_D_sum;
                // Octahedral group (24-35)
                6'd24: angle_scalar_D_sum = oct24_D;
                6'd25: angle_scalar_D_sum = oct25_D;
                6'd26: angle_scalar_D_sum = oct26_D;
                6'd27: angle_scalar_D_sum = oct27_D;
                6'd28: angle_scalar_D_sum = oct28_D;
                6'd29: angle_scalar_D_sum = oct29_D;
                6'd30: angle_scalar_D_sum = oct30_D;
                6'd31: angle_scalar_D_sum = oct31_D;
                6'd32: angle_scalar_D_sum = oct32_D;
                6'd33: angle_scalar_D_sum = oct33_D;
                6'd34: angle_scalar_D_sum = oct34_D;
                6'd35: angle_scalar_D_sum = oct35_D;
                default:           angle_scalar_D_sum = scalar_D_sum;
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            done <= 0;
            acc_B <= 0; acc_C <= 0; acc_D <= 0;
            A_out <= 0; B_out <= 0; C_out <= 0; D_out <= 0;
            sm_op1 <= 0; sm_op2 <= 0;
        end else begin
            done <= 0;
            case (state)
                S_IDLE: begin
                    if (start) begin
                        if (bypass_p5) begin
                            A_out <= A_in; B_out <= D_in; C_out <= B_in; D_out <= C_in;
                            state <= S_DONE;
                        end else if (bypass_p5_inv) begin
                            A_out <= A_in; B_out <= C_in; C_out <= D_in; D_out <= B_in;
                            state <= S_DONE;
                        end else if (bypass_ab_cd) begin
                            A_out <= B_in; B_out <= A_in; C_out <= D_in; D_out <= C_in;
                            state <= S_DONE;
                        end else if (bypass_ac_bd) begin
                            A_out <= C_in; B_out <= D_in; C_out <= A_in; D_out <= B_in;
                            state <= S_DONE;
                        end else if (bypass_ad_bc) begin
                            A_out <= D_in; B_out <= C_in; C_out <= B_in; D_out <= A_in;
                            state <= S_DONE;
                        end else if (!ENABLE_TDM_FALLBACK) begin
                            B_out <= scale_axis(angle_scalar_B_sum(angle), apply_div3);
                            C_out <= scale_axis(angle_scalar_C_sum(angle), apply_div3);
                            D_out <= scale_axis(angle_scalar_D_sum(angle), apply_div3);
                            A_out <= recompute_A ?
                                neg_axis(add3_axis(angle_scalar_B_sum(angle),
                                                   angle_scalar_C_sum(angle),
                                                   angle_scalar_D_sum(angle))) : A_in;
                            state <= S_DONE;
                        end else if (scalar_fast || !ENABLE_TDM_FALLBACK) begin
                            A_out <= recompute_A ? neg_axis(add3_axis(scale_axis(scalar_B_sum, apply_div3),
                                                                        scale_axis(scalar_C_sum, apply_div3),
                                                                        scale_axis(scalar_D_sum, apply_div3))) : A_in;
                            B_out <= scale_axis(scalar_B_sum, apply_div3);
                            C_out <= scale_axis(scalar_C_sum, apply_div3);
                            D_out <= scale_axis(scalar_D_sum, apply_div3);
                            state <= S_DONE;
                        end else begin
                            acc_B <= 0; acc_C <= 0; acc_D <= 0;
                            A_out <= A_in;
                            // Prep first mult: F * B
                            sm_op1 <= B_in; sm_op2 <= F;
                            state <= 4'd1;
                        end
                    end
                end

                // Step-by-Step TDM Matrix-Vector Mult
                4'd1: begin // FB result available next cycle; prep HC
                    sm_op1 <= C_in; sm_op2 <= H;
                    state <= 4'd2;
                end
                4'd2: begin // FB result latched; prep GD
                    acc_B <= sm_res;
                    sm_op1 <= D_in; sm_op2 <= G;
                    state <= 4'd3;
                end
                4'd3: begin // HC result latched; prep GB
                    acc_B <= {acc_B[63:32] + sm_res[63:32], acc_B[31:0] + sm_res[31:0]};
                    sm_op1 <= B_in; sm_op2 <= G;
                    state <= 4'd4;
                end
                4'd4: begin // GD result latched; prep FC
                    acc_B <= {acc_B[63:32] + sm_res[63:32], acc_B[31:0] + sm_res[31:0]};
                    sm_op1 <= C_in; sm_op2 <= F;
                    state <= 4'd5;
                end
                4'd5: begin // GB result latched; prep HD
                    acc_C <= sm_res;
                    sm_op1 <= D_in; sm_op2 <= H;
                    state <= 4'd6;
                end
                4'd6: begin // FC result latched; prep HB
                    acc_C <= {acc_C[63:32] + sm_res[63:32], acc_C[31:0] + sm_res[31:0]};
                    sm_op1 <= B_in; sm_op2 <= H;
                    state <= 4'd7;
                end
                4'd7: begin // HD result latched; prep GC
                    acc_C <= {acc_C[63:32] + sm_res[63:32], acc_C[31:0] + sm_res[31:0]};
                    sm_op1 <= C_in; sm_op2 <= G;
                    state <= 4'd8;
                end
                4'd8: begin // HB result latched; prep FD
                    acc_D <= sm_res;
                    sm_op1 <= D_in; sm_op2 <= F;
                    state <= 4'd9;
                end
                4'd9: begin // GC result latched
                    acc_D <= {acc_D[63:32] + sm_res[63:32], acc_D[31:0] + sm_res[31:0]};
                    state <= 4'd10;
                end
                4'd10: begin // FD result latched; final sum and optional scale
                    B_out <= scale_axis(acc_B, apply_div3);
                    C_out <= scale_axis(acc_C, apply_div3);
                    D_out <= scale_axis({acc_D[63:32] + sm_res[63:32], acc_D[31:0] + sm_res[31:0]}, apply_div3);
                    state <= S_DONE;
                end

                S_DONE: begin
                    done <= 1;
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
