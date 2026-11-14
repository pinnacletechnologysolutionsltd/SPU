// psurd_decode.v — full-word decoder for the v0.3 programmable-surd ISA (frozen contract §3).
// Combinational. Decodes all 8 opcode bits and every must-be-zero field; any other word is bad.
// Frontend-only classes (SLIK, STST, BR, HALT) are never presented to the shared arithmetic unit:
// psurd_core issues arith_op only for class C_ARITH, so 0x78-0x7B cannot alias SLI/SLD/SRD/SMUL.
module psurd_decode (
    input  wire [63:0] w,
    output reg  [2:0]  cls,        // 0 bad, 1 SLI, 2 SLD, 3 ARITH, 4 SLIK, 5 STST, 6 BR, 7 HALT
    output wire [2:0]  arith_op,   // 3 SMUL, 4 SADD, 5 SSUB, 6 SNORM (shared-unit op codes)
    output wire [2:0]  rd, ra, rb, slice,
    output wire [31:0] payload,    // SLI payload / SLIK immediate, word[39:8]
    output wire [3:0]  cc,
    output wire [15:0] target
);
    localparam C_BAD = 3'd0, C_SLI = 3'd1, C_SLD = 3'd2, C_ARITH = 3'd3,
               C_SLIK = 3'd4, C_STST = 3'd5, C_BR = 3'd6, C_HALT = 3'd7;
    wire [7:0] op = w[63:56], r1 = w[55:48], r2 = w[47:40], sb = w[31:24];
    wire lo40 = w[39:0] == 40'd0, lo24 = w[23:0] == 24'd0, lo8 = w[7:0] == 8'd0, hi8 = w[39:32] == 8'd0;
    assign arith_op = op[2:0];
    assign rd = r1[2:0];
    assign ra = r2[2:0];
    assign rb = sb[2:0];
    assign slice = r2[2:0];
    assign payload = w[39:8];
    assign cc = r1[3:0];
    assign target = w[39:24];
    always @* begin
        cls = C_BAD;
        case (op)
            8'h70: if (r1 < 8 && r2 < 6 && lo8) cls = C_SLI;
            8'h71: if (r1 < 8 && r2 == 0 && lo40) cls = C_SLD;
            8'h73, 8'h74, 8'h75: if (r1 < 8 && r2 < 8 && hi8 && sb < 8 && lo24) cls = C_ARITH;
            8'h76: if (r1 < 8 && r2 < 8 && lo40) cls = C_ARITH;
            8'h78: if (r1 < 8 && r2 == 0 && lo8) cls = C_SLIK;
            8'h79: if (r1 == 0 && r2 < 8 && lo40) cls = C_STST;
            8'h7A: if (r1 <= 9 && r2 == 0 && lo24) cls = C_BR;
            8'h7B: if (w[55:0] == 56'd0) cls = C_HALT;
            default: cls = C_BAD;   // incl. 0x72 SRD (retired), 0x77, 0x7C-0x7F and every other opcode
        endcase
    end
endmodule
