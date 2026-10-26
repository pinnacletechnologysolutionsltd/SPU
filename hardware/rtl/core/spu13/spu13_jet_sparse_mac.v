`timescale 1ns / 1ps
// Standalone tagged Cauchy product over A31[eps]/eps^(N+1).
// Exclusive shared multiplier ownership and reset/drain are issuer obligations.
module spu13_jet_sparse_mac #(
    parameter N = 2,
    parameter TAG_BITS = $clog2(N+2)
) (
    input wire clk, rst_n, start, op_mul,
    input wire [31:0] j_coeff [0:N][0:3], k_coeff [0:N][0:3],
    input wire [TAG_BITS-1:0] j_lo, j_hi, k_lo, k_hi,
    output reg [31:0] r_coeff [0:N][0:3],
    output reg [TAG_BITS-1:0] r_lo, r_hi,
    output reg done,
    output wire busy, err_zero_divisor,
    output reg mult_start,
    output reg [31:0] mult_a0, mult_a1, mult_a2, mult_a3,
    output reg [31:0] mult_b0, mult_b1, mult_b2, mult_b3,
    input wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3,
    input wire mult_done
);
    localparam IDLE=0, ISSUE=1, WAIT=2, RETIRE=3;
    localparam [31:0] P = 32'h7fffffff;
    reg [1:0] state;
    reg [31:0] a [0:N][0:3], b [0:N][0:3], work [0:N][0:3];
    reg [TAG_BITS-1:0] al, ah, bl, bh, next_lo, next_hi;
    reg [TAG_BITS-1:0] cursor_order, cursor_i, pending_order, pending_i;
    wire valid;
    wire [TAG_BITS-1:0] order, idx_i, idx_j;
    wire [TAG_BITS:0] lo_sum = {1'b0,j_lo} + {1'b0,k_lo};
    wire [TAG_BITS:0] hi_sum = {1'b0,j_hi} + {1'b0,k_hi};
    wire j_empty = (j_lo == N+1 && j_hi == 0);
    wire k_empty = (k_lo == N+1 && k_hi == 0);
    wire product_empty = j_empty || k_empty || lo_sum > N;
    assign busy = state != IDLE;
    assign err_zero_divisor = 1'b0;
    spu13_jet_sparse_idx #(.N(N), .TAG_BITS(TAG_BITS)) indices (
        .j_lo(al), .j_hi(ah), .k_lo(bl), .k_hi(bh),
        .cursor_order(cursor_order), .cursor_i(cursor_i),
        .valid(valid), .order(order), .i(idx_i), .j(idx_j)
    );
    function [31:0] add_mod;
        input [31:0] x, y;
        reg [32:0] sum;
        begin
            sum = {1'b0,x} + {1'b0,y};
            add_mod = sum >= P ? sum-P : sum;
        end
    endfunction
    integer row, lane;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE; done <= 0; mult_start <= 0;
            r_lo <= N+1; r_hi <= 0; next_lo <= N+1; next_hi <= 0;
            al <= 0; ah <= 0; bl <= 0; bh <= 0;
            cursor_order <= 0; cursor_i <= 0; pending_order <= 0; pending_i <= 0;
            mult_a0 <= 0; mult_a1 <= 0; mult_a2 <= 0; mult_a3 <= 0;
            mult_b0 <= 0; mult_b1 <= 0; mult_b2 <= 0; mult_b3 <= 0;
            for (row=0; row<=N; row=row+1)
                for (lane=0; lane<4; lane=lane+1) begin
                    a[row][lane] <= 0; b[row][lane] <= 0;
                    work[row][lane] <= 0; r_coeff[row][lane] <= 0;
                end
        end else begin
            done <= 0; mult_start <= 0;
            case (state)
                IDLE: if (start) begin
                    al <= j_lo; ah <= j_hi; bl <= k_lo; bh <= k_hi;
                    cursor_order <= 0; cursor_i <= 0;
                    for (row=0; row<=N; row=row+1)
                        for (lane=0; lane<4; lane=lane+1) begin
                            a[row][lane] <= j_coeff[row][lane];
                            b[row][lane] <= k_coeff[row][lane];
                            work[row][lane] <= op_mul ? 0 : add_mod(j_coeff[row][lane],k_coeff[row][lane]);
                        end
                    if (op_mul) begin
                        next_lo <= product_empty ? N+1 : lo_sum;
                        next_hi <= product_empty ? 0 : (hi_sum > N ? N : hi_sum);
                        state <= product_empty ? RETIRE : ISSUE;
                    end else begin
                        next_lo <= j_empty ? k_lo : (k_empty ? j_lo : (j_lo < k_lo ? j_lo : k_lo));
                        next_hi <= j_empty ? k_hi : (k_empty ? j_hi : (j_hi > k_hi ? j_hi : k_hi));
                        state <= RETIRE;
                    end
                end
                ISSUE: if (valid) begin
                    mult_a0 <= a[idx_i][0]; mult_a1 <= a[idx_i][1];
                    mult_a2 <= a[idx_i][2]; mult_a3 <= a[idx_i][3];
                    mult_b0 <= b[idx_j][0]; mult_b1 <= b[idx_j][1];
                    mult_b2 <= b[idx_j][2]; mult_b3 <= b[idx_j][3];
                    pending_order <= order; pending_i <= idx_i;
                    mult_start <= 1; state <= WAIT;
                end else state <= RETIRE;
                WAIT: if (mult_done) begin
                    work[pending_order][0] <= add_mod(work[pending_order][0],mult_r0);
                    work[pending_order][1] <= add_mod(work[pending_order][1],mult_r1);
                    work[pending_order][2] <= add_mod(work[pending_order][2],mult_r2);
                    work[pending_order][3] <= add_mod(work[pending_order][3],mult_r3);
                    cursor_order <= pending_i == pending_order ? pending_order+1'b1 : pending_order;
                    cursor_i <= pending_i == pending_order ? 0 : pending_i+1'b1;
                    state <= ISSUE;
                end
                RETIRE: begin
                    for (row=0; row<=N; row=row+1)
                        for (lane=0; lane<4; lane=lane+1) r_coeff[row][lane] <= work[row][lane];
                    r_lo <= next_lo; r_hi <= next_hi;
                    done <= 1; state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
