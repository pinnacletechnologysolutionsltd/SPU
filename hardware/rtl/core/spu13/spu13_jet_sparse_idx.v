`timescale 1ns / 1ps
// Value-blind, order-major window intersection. No coefficient inspection.
module spu13_jet_sparse_idx #(
    parameter N = 2,
    parameter TAG_BITS = $clog2(N+2)
) (
    input wire [TAG_BITS-1:0] j_lo, j_hi, k_lo, k_hi,
    input wire [TAG_BITS-1:0] cursor_order, cursor_i,
    output reg valid,
    output reg [TAG_BITS-1:0] order, i, j
);
    integer row, col;
    always @* begin
        valid = 0; order = 0; i = 0; j = 0;
        for (row = 0; row <= N; row = row + 1)
            for (col = 0; col <= row; col = col + 1)
                if (!valid && (row > cursor_order ||
                    (row == cursor_order && col >= cursor_i)) &&
                    col >= j_lo && col <= j_hi &&
                    row-col >= k_lo && row-col <= k_hi) begin
                    valid = 1;
                    order = row; i = col; j = row-col;
                end
    end
endmodule
