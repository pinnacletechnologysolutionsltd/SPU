// SPU-13 Thomson Rotor Core TDM (v4.0)
// Implementation: Time-Division Multiplexed ALU for Isotropic Rotation.
// Reduces DSP usage from 36 down to 4 by sharing a single surd_multiplier.
// Latency: 11 cycles (1 load + 9 mult + 1 sum).

module spu13_rotor_core_tdm #(
    parameter WIDTH = 32
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
    input  wire        apply_div3,
    
    // Quadray Output Coordinates
    output reg  [63:0] A_out, B_out, C_out, D_out
);

    // --- TDM Controller ---
    reg [3:0] state;
    localparam S_IDLE = 0, S_CALC = 1, S_DONE = 11;

    reg [63:0] sm_op1, sm_op2;
    wire [63:0] sm_res;

    surd_multiplier #(.WIDTH(32), .SHIFT(0)) u_sm (
        .clk(clk), .reset(!rst_n),
        .field_sel(field_sel),
        .a1(sm_op1[31:0]),  .b1(sm_op1[63:32]),
        .a2(sm_op2[31:0]),  .b2(sm_op2[63:32]),
        .res_a(sm_res[31:0]), .res_b(sm_res[63:32])
    );

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

    // Accumulators for B, C, D rows
    reg [63:0] acc_B, acc_C, acc_D;

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
