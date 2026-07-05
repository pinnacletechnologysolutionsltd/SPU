// spu_hamming_72_64.v — (72,64) SECDED ECC for QR register file
//
// Implements Single-Error Correction, Double-Error Detection on 64-bit
// lanes using 8 check bits: 7 Hamming parity + 1 overall parity.
//
// Copyright 2026 John Curley — CC0 1.0 Universal

module spu_hamming_72_64 (
    input  wire [63:0] data_in,
    output wire [7:0]  parity_out,
    input  wire [63:0] data_check,
    input  wire [7:0]  parity_in,
    output wire [63:0] data_corrected,
    output wire        single_err,
    output wire        double_err
);

    function is_parity_pos;
        input integer pos;
        begin
            is_parity_pos = (pos == 1) || (pos == 2) || (pos == 4) ||
                            (pos == 8) || (pos == 16) || (pos == 32) ||
                            (pos == 64);
        end
    endfunction

    function [6:0] data_code_pos;
        input integer data_idx;
        integer pos;
        integer count;
        begin
            data_code_pos = 7'd0;
            count = 0;
            for (pos = 1; pos <= 71; pos = pos + 1) begin
                if (!is_parity_pos(pos)) begin
                    if (count == data_idx)
                        data_code_pos = pos[6:0];
                    count = count + 1;
                end
            end
        end
    endfunction

    function [6:0] hamming_parity;
        input [63:0] d;
        reg [6:0] acc;
        reg [6:0] pos;
        integer i, j;
        begin
            acc = 7'd0;
            for (i = 0; i < 64; i = i + 1) begin
                pos = data_code_pos(i);
                for (j = 0; j < 7; j = j + 1)
                    if (pos[j])
                        acc[j] = acc[j] ^ d[i];
            end
            hamming_parity = acc;
        end
    endfunction

    wire [6:0] ham_p = hamming_parity(data_in);

    assign parity_out[6:0] = ham_p;
    assign parity_out[7]   = ^data_in ^ ^ham_p;

    wire [6:0] syn = hamming_parity(data_check) ^ parity_in[6:0];
    wire       overall_mismatch = ^data_check ^ ^parity_in[6:0] ^ parity_in[7];

    assign single_err = overall_mismatch;
    assign double_err = (syn != 7'd0) && !overall_mismatch;

    function [63:0] correct_data;
        input [63:0] d;
        input [6:0]  s;
        input        is_single;
        reg [63:0]   r;
        integer      k;
        begin
            r = d;
            if (is_single && s != 7'd0) begin
                for (k = 0; k < 64; k = k + 1) begin
                    if (data_code_pos(k) == s)
                        r[k] = ~d[k];
                end
            end
            correct_data = r;
        end
    endfunction

    assign data_corrected = correct_data(data_check, syn, single_err);

endmodule
