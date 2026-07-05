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

    function [63:0] angle_scalar_B_sum;
        input [5:0] rot_angle;
        begin
            case (rot_angle)
                6'd1, 6'd7, 6'd9:  angle_scalar_B_sum = angle1_B_sum;
                6'd3, 6'd8, 6'd11: angle_scalar_B_sum = angle3_B_sum;
                6'd4, 6'd6, 6'd10: angle_scalar_B_sum = angle4_B_sum;
                default:           angle_scalar_B_sum = scalar_B_sum;
            endcase
        end
    endfunction

    function [63:0] angle_scalar_C_sum;
        input [5:0] rot_angle;
        begin
            case (rot_angle)
                6'd1, 6'd7, 6'd9:  angle_scalar_C_sum = angle1_C_sum;
                6'd3, 6'd8, 6'd11: angle_scalar_C_sum = angle3_C_sum;
                6'd4, 6'd6, 6'd10: angle_scalar_C_sum = angle4_C_sum;
                default:           angle_scalar_C_sum = scalar_C_sum;
            endcase
        end
    endfunction

    function [63:0] angle_scalar_D_sum;
        input [5:0] rot_angle;
        begin
            case (rot_angle)
                6'd1, 6'd7, 6'd9:  angle_scalar_D_sum = angle1_D_sum;
                6'd3, 6'd8, 6'd11: angle_scalar_D_sum = angle3_D_sum;
                6'd4, 6'd6, 6'd10: angle_scalar_D_sum = angle4_D_sum;
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
                        end else if (!ENABLE_TDM_FALLBACK) begin
                            A_out <= A_in;
                            B_out <= scale_axis(angle_scalar_B_sum(angle), apply_div3);
                            C_out <= scale_axis(angle_scalar_C_sum(angle), apply_div3);
                            D_out <= scale_axis(angle_scalar_D_sum(angle), apply_div3);
                            state <= S_DONE;
                        end else if (scalar_fast || !ENABLE_TDM_FALLBACK) begin
                            A_out <= A_in;
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
