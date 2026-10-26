`timescale 1ns / 1ps

// Candidate four-request F_{p^4} inverter controller.
//
// The Fermat chain is bit-identical to spu13_fp4_inverter. The surrounding
// tower uses the structure-specific multiplier operations:
//   Stage A  6 products, Stage B 2, Stage D1 8, final scale 4 = 20 total.
// This module is deliberately separate from the production v1 controller so
// integration can retain a one-parameter rollback path.

module spu13_fp4_inverter_structured (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  z0, z1, z2, z3,
    output reg  [31:0]  inv0, inv1, inv2, inv3,
    output reg          done,
    output reg          busy,
    output reg          flags_v,
    output reg          mult_start,
    output reg  [2:0]   mult_op,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done,
    input  wire         mult_busy,
    output wire [3:0]   debug_state,
    output wire         debug_start_accept
);
    localparam [31:0] P = 32'h7FFFFFFF;
    localparam [30:0] P_MINUS_2 = 31'h7FFFFFFD;

    localparam [2:0] OP_STAGE_A  = 3'd1;
    localparam [2:0] OP_STAGE_B  = 3'd2;
    localparam [2:0] OP_STAGE_D1 = 3'd3;
    localparam [2:0] OP_SCALE    = 3'd4;

    localparam [3:0] S_IDLE        = 4'd0;
    localparam [3:0] S_STAGE_A     = 4'd1;
    localparam [3:0] S_STAGE_B     = 4'd2;
    localparam [3:0] S_FERMAT_INIT = 4'd3;
    localparam [3:0] S_FERMAT_SQ   = 4'd4;
    localparam [3:0] S_FERMAT_MUL  = 4'd5;
    localparam [3:0] S_STAGE_D1    = 4'd6;
    localparam [3:0] S_SCALE       = 4'd7;
    localparam [3:0] S_EXCEPTION   = 4'd8;

    (* keep, fsm_encoding = "none" *) reg [3:0] state;
    reg [31:0] zc0, zc1, zc2, zc3;
    reg [31:0] wc0, wc1;
    reg [31:0] norm_n;
    reg [31:0] ninv;
    reg [31:0] fermat_res;
    reg [4:0] fermat_bit;

    assign debug_state = state;
    assign debug_start_accept = (state == S_IDLE) && start;

    function [31:0] m31_reduce;
        input [63:0] value;
        reg [31:0] lo, hi, sum;
        begin
            lo = value[30:0];
            hi = value[62:31];
            sum = lo + hi;
            if (sum >= P)
                sum = sum - P;
            m31_reduce = sum;
        end
    endfunction

    function [31:0] m31_neg;
        input [31:0] value;
        begin
            m31_neg = (value == 0) ? 32'd0 : P - value;
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            inv0 <= 0; inv1 <= 0; inv2 <= 0; inv3 <= 0;
            done <= 1'b0;
            busy <= 1'b0;
            flags_v <= 1'b0;
            mult_start <= 1'b0;
            mult_op <= 3'd0;
            mult_a0 <= 0; mult_a1 <= 0; mult_a2 <= 0; mult_a3 <= 0;
            mult_b0 <= 0; mult_b1 <= 0; mult_b2 <= 0; mult_b3 <= 0;
            zc0 <= 0; zc1 <= 0; zc2 <= 0; zc3 <= 0;
            wc0 <= 0; wc1 <= 0;
            norm_n <= 0;
            ninv <= 0;
            fermat_res <= 0;
            fermat_bit <= 0;
        end else begin
            done <= 1'b0;
            mult_start <= 1'b0;

            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        busy <= 1'b1;
                        flags_v <= 1'b0;
                        zc0 <= z0;
                        zc1 <= z1;
                        zc2 <= m31_neg(z2);
                        zc3 <= m31_neg(z3);
                        mult_op <= OP_STAGE_A;
                        mult_a0 <= z0;
                        mult_a1 <= z1;
                        mult_a2 <= z2;
                        mult_a3 <= z3;
                        mult_b0 <= 0;
                        mult_b1 <= 0;
                        mult_b2 <= 0;
                        mult_b3 <= 0;
                        mult_start <= 1'b1;
                        state <= S_STAGE_A;
                    end
                end

                S_STAGE_A: begin
                    if (mult_done && !mult_start) begin
                        wc0 <= mult_r0;
                        wc1 <= m31_neg(mult_r1);
                        mult_op <= OP_STAGE_B;
                        mult_a0 <= mult_r0;
                        mult_a1 <= mult_r1;
                        mult_a2 <= 0;
                        mult_a3 <= 0;
                        mult_b0 <= 0;
                        mult_b1 <= 0;
                        mult_b2 <= 0;
                        mult_b3 <= 0;
                        mult_start <= 1'b1;
                        state <= S_STAGE_B;
                    end
                end

                S_STAGE_B: begin
                    if (mult_done && !mult_start) begin
                        norm_n <= mult_r0;
                        if (mult_r0 == 0) begin
                            flags_v <= 1'b1;
                            state <= S_EXCEPTION;
                        end else begin
                            fermat_res <= 32'd1;
                            fermat_bit <= 5'd30;
                            state <= S_FERMAT_INIT;
                        end
                    end
                end

                S_FERMAT_INIT: begin
                    state <= S_FERMAT_SQ;
                end

                S_FERMAT_SQ: begin
                    fermat_res <= m31_reduce(fermat_res * fermat_res);
                    if (P_MINUS_2[fermat_bit])
                        state <= S_FERMAT_MUL;
                    else if (fermat_bit == 0)
                        state <= S_STAGE_D1;
                    else
                        fermat_bit <= fermat_bit - 1'b1;
                end

                S_FERMAT_MUL: begin
                    fermat_res <= m31_reduce(fermat_res * norm_n);
                    if (fermat_bit == 0) begin
                        ninv <= m31_reduce(fermat_res * norm_n);
                        mult_op <= OP_STAGE_D1;
                        mult_a0 <= zc0;
                        mult_a1 <= zc1;
                        mult_a2 <= zc2;
                        mult_a3 <= zc3;
                        mult_b0 <= wc0;
                        mult_b1 <= wc1;
                        mult_b2 <= 0;
                        mult_b3 <= 0;
                        mult_start <= 1'b1;
                        state <= S_STAGE_D1;
                    end else begin
                        fermat_bit <= fermat_bit - 1'b1;
                        state <= S_FERMAT_SQ;
                    end
                end

                S_STAGE_D1: begin
                    if (mult_done && !mult_start) begin
                        mult_op <= OP_SCALE;
                        mult_a0 <= mult_r0;
                        mult_a1 <= mult_r1;
                        mult_a2 <= mult_r2;
                        mult_a3 <= mult_r3;
                        mult_b0 <= ninv;
                        mult_b1 <= 0;
                        mult_b2 <= 0;
                        mult_b3 <= 0;
                        mult_start <= 1'b1;
                        state <= S_SCALE;
                    end
                end

                S_SCALE: begin
                    if (mult_done && !mult_start) begin
                        inv0 <= mult_r0;
                        inv1 <= mult_r1;
                        inv2 <= mult_r2;
                        inv3 <= mult_r3;
                        done <= 1'b1;
                        busy <= 1'b0;
                        state <= S_IDLE;
                    end
                end

                S_EXCEPTION: begin
                    flags_v <= 1'b1;
                    done <= 1'b1;
                    busy <= 1'b0;
                    state <= S_IDLE;
                end

                default: begin
                    busy <= 1'b0;
                    state <= S_IDLE;
                end
            endcase
        end
    end

    // mult_busy is intentionally advisory, matching the v1 shared interface:
    // request acceptance and completion are defined by mult_start/mult_done.
    wire unused_mult_busy = mult_busy;
endmodule
